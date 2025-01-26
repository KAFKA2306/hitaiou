from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import socket
import requests
import os
import subprocess
import sys
import platform

app = FastAPI(title="Hitaiou Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def is_admin():
    """管理者権限で実行されているかチェック"""
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def setup_windows_firewall(port):
    """Windowsファイアウォールの設定を行う"""
    if platform.system() != 'Windows':
        return False, "このコマンドはWindowsでのみ使用できます"

    try:
        # 既存のルールを確認
        rule_check = subprocess.run(
            f'netsh advfirewall firewall show rule name="Hitaiou Dashboard"',
            capture_output=True,
            text=True
        )

        if "規則が見つかりません" in rule_check.stdout or "No rules match" in rule_check.stdout:
            # 新しいルールを作成
            commands = [
                # TCP用のルール
                f'netsh advfirewall firewall add rule name="Hitaiou Dashboard" dir=in action=allow protocol=TCP localport={port}',
                f'netsh advfirewall firewall add rule name="Hitaiou Dashboard" dir=out action=allow protocol=TCP localport={port}',
            ]

            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    return False, f"ファイアウォールの設定に失敗しました: {result.stderr}"

            return True, "ファイアウォールの設定が完了しました"
        else:
            return True, "ファイアウォールのルールは既に存在します"

    except Exception as e:
        return False, f"エラーが発生しました: {str(e)}"

def get_public_ip():
    """パブリックIPアドレスを取得"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()['ip']
    except:
        return None

def get_local_ip():
    """ローカルIPアドレスを取得"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def test_port(port):
    """指定されたポートが利用可能かテスト"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('0.0.0.0', port))
        result = True
    except:
        result = False
    finally:
        sock.close()
    return result

def display_server_info(port):
    """サーバー情報を表示"""
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("\n" + "="*60)
    print("     Hitaiou Dashboard Server - セットアップガイド")
    print("="*60 + "\n")

    # 管理者権限のチェック
    if not is_admin():
        print("【警告】管理者権限がありません")
        print("- 管理者として実行することをお勧めします")
        print("- コマンドプロンプトを管理者として実行し直してください\n")

    # ポートのチェック
    if not test_port(port):
        print(f"【エラー】ポート {port} が既に使用されています")
        print("- 別のポートを使用するか、競合するアプリケーションを終了してください\n")
    
    print("【アクセス情報】")
    print("\n1. ローカルアクセス:")
    print(f"   http://localhost:{port}")
    
    print("\n2. ネットワーク内からのアクセス:")
    print(f"   http://{local_ip}:{port}")
    
    if public_ip:
        print("\n3. インターネットからのアクセス:")
        print(f"   http://{public_ip}:{port}")
    
    print("\n【セットアップ手順】")
    print("1. Windowsファイアウォール:")
    success, msg = setup_windows_firewall(port)
    print(f"   状態: {msg}")
    
    print("\n2. ルーターの設定:")
    print(f"   - ルーター管理画面を開く（通常 http://192.168.0.1 など）")
    print(f"   - ポートフォワーディングの設定で以下を追加:")
    print(f"     * 外部ポート: {port}")
    print(f"     * 内部ポート: {port}")
    print(f"     * 内部IP: {local_ip}")
    print(f"     * プロトコル: TCP")
    
    print("\n3. 動作確認:")
    print("   - まずローカルアクセスで確認")
    print("   - 次にネットワーク内からアクセス")
    print("   - 最後にインターネットからアクセス")
    
    print("\n" + "-"*60)
    print("サーバーを終了するには Ctrl+C を押してください")
    print("-"*60 + "\n")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """メインページを返す"""
    try:
        html_path = Path("static/index.html")
        return html_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="index.html not found in static directory"
        )
    except UnicodeDecodeError:
        try:
            return html_path.read_text(encoding='cp932')
        except:
            raise HTTPException(
                status_code=500,
                detail="Failed to read index.html"
            )

@app.get("/api/demand-metrics")
async def get_demand_metrics():
    """需要メトリクスデータを返す"""
    try:
        dashboard_dir = Path("data/dashboard")
        parquet_files = list(dashboard_dir.glob("demand_metrics_*.parquet"))
        
        if not parquet_files:
            return JSONResponse(
                status_code=404,
                content={"error": "No metrics data found"}
            )
            
        latest_file = max(parquet_files, key=lambda p: p.stat().st_mtime)
        df = pd.read_parquet(latest_file)
        df = df.sort_values('potential_sales', ascending=False)
        
        return JSONResponse(content={
            "data": df.to_dict(orient='records'),
            "timestamp": latest_file.stat().st_mtime,
            "filename": latest_file.name
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

def main():
    """メイン関数"""
    static_dir = Path("static")
    if not static_dir.exists():
        static_dir.mkdir(parents=True)
        print("\n[INFO] static ディレクトリを作成しました")
    
    index_file = static_dir / "index.html"
    if not index_file.exists():
        print("\n[WARNING] static/index.html が見つかりません")
    
    port = 8000
    display_server_info(port)
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )

if __name__ == "__main__":
    main()