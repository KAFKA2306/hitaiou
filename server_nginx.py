# server.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from pathlib import Path
import pandas as pd
import socket
import requests
import platform
import subprocess
import os

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        GETリクエストの処理
        HTTPプロトコルに従って、正しい順序でヘッダーとボディを送信
        """
        try:
            if self.path == '/':
                self.handle_root()
            elif self.path == '/api/demand-metrics':
                self.handle_metrics()
            else:
                self.handle_not_found()
        except Exception as e:
            self.handle_server_error(str(e))

    def handle_root(self):
        """
        ルートパスのハンドラー
        APIの状態と利用可能なエンドポイントを返す
        """
        response_data = {
            "status": "running",
            "message": "Hitaiou Dashboard API Server",
            "endpoints": [
                {
                    "path": "/api/demand-metrics",
                    "method": "GET",
                    "description": "需要メトリクスデータを取得"
                }
            ]
        }
        self.send_json_response(200, response_data)

    def handle_metrics(self):
        """
        メトリクスデータのハンドラー
        Parquetファイルからデータを読み込んで返す
        """
        try:
            dashboard_dir = Path("data/dashboard")
            parquet_files = list(dashboard_dir.glob("demand_metrics_*.parquet"))
            
            if not parquet_files:
                self.handle_not_found("No metrics data found")
                return
                
            latest_file = max(parquet_files, key=lambda p: p.stat().st_mtime)
            df = pd.read_parquet(latest_file)
            df = df.sort_values('potential_sales', ascending=False)
            
            response_data = {
                "data": df.to_dict(orient='records'),
                "timestamp": latest_file.stat().st_mtime,
                "filename": latest_file.name
            }
            self.send_json_response(200, response_data)
            
        except Exception as e:
            self.handle_server_error(str(e))

    def send_json_response(self, status_code, data):
        """
        JSON形式でレスポンスを送信
        ヘッダーの送信順序を厳密に管理
        """
        # 1. まずステータスコードを送信
        self.send_response(status_code)
        
        # 2. 必要なヘッダーをすべて送信
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        # 3. データをJSON形式にエンコード
        response_body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        # 4. Content-Lengthヘッダーを送信
        self.send_header('Content-Length', str(len(response_body)))
        
        # 5. ヘッダーの終了を明示
        self.end_headers()
        
        # 6. レスポンスボディを送信
        self.wfile.write(response_body)

    def handle_not_found(self, message="Resource not found"):
        """
        404エラーハンドラー
        """
        error_data = {
            "error": True,
            "message": message,
            "status": 404
        }
        self.send_json_response(404, error_data)

    def handle_server_error(self, message="Internal server error"):
        """
        500エラーハンドラー
        """
        error_data = {
            "error": True,
            "message": message,
            "status": 500
        }
        self.send_json_response(500, error_data)

    def do_OPTIONS(self):
        """
        OPTIONSリクエストのハンドラー
        CORSプリフライトリクエストに対応
        """
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

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

def setup_windows_firewall(port):
    """Windowsファイアウォールの設定"""
    if platform.system() != 'Windows':
        return False, "このコマンドはWindowsでのみ使用できます"

    try:
        rule_check = subprocess.run(
            f'netsh advfirewall firewall show rule name="Hitaiou Dashboard"',
            capture_output=True,
            text=True
        )

        if "規則が見つかりません" in rule_check.stdout or "No rules match" in rule_check.stdout:
            commands = [
                f'netsh advfirewall firewall add rule name="Hitaiou Dashboard" dir=in action=allow protocol=TCP localport={port}',
                f'netsh advfirewall firewall add rule name="Hitaiou Dashboard" dir=out action=allow protocol=TCP localport={port}'
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

def main():
    """メインサーバー起動処理"""
    API_PORT = 8001
    
    print("\n" + "="*60)
    print("     Hitaiou Dashboard API Server")
    print("="*60 + "\n")
    
    # Windowsファイアウォールの設定
    success, msg = setup_windows_firewall(API_PORT)
    print(f"ファイアウォール設定: {msg}\n")
    
    # サーバー情報の表示
    local_ip = get_local_ip()
    print(f"APIサーバー起動: http://{local_ip}:{API_PORT}")
    print("\nCtrl+C で終了")
    print("-"*60 + "\n")
    
    server = HTTPServer(('0.0.0.0', API_PORT), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを終了します")
        server.server_close()

if __name__ == "__main__":
    main()