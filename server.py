from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import platform
import re
import socket
import subprocess

import pandas as pd


SNAPSHOT_NAME_RE = re.compile(r"^demand_metrics_(\d{8}_\d{6})\.parquet$")


def snapshot_identity(path):
    match = SNAPSHOT_NAME_RE.fullmatch(path.name)
    if match is None:
        raise ValueError(f"Invalid demand metrics snapshot name: {path.name}")
    identity = match.group(1)
    observed_at = datetime.strptime(identity, "%Y%m%d_%H%M%S").replace(
        tzinfo=timezone.utc
    )
    return identity, observed_at


def select_latest_snapshot(dashboard_dir):
    snapshots = list(Path(dashboard_dir).glob("demand_metrics_*.parquet"))
    if not snapshots:
        raise FileNotFoundError("No metrics data found")

    parsed = []
    identities = set()
    for path in snapshots:
        identity, observed_at = snapshot_identity(path)
        if identity in identities:
            raise ValueError(f"Ambiguous demand metrics snapshot identity: {identity}")
        identities.add(identity)
        parsed.append((observed_at, identity, path))

    observed_at, identity, path = max(parsed, key=lambda item: item[0])
    return path, identity, observed_at


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == "/":
                self.handle_root()
            elif self.path == "/api/demand-metrics":
                self.handle_metrics()
            else:
                self.handle_not_found()
        except Exception as exc:
            self.handle_server_error(str(exc))

    def handle_root(self):
        self.send_json_response(
            200,
            {
                "status": "running",
                "message": "Hitaiou Dashboard API Server",
                "endpoints": [
                    {
                        "path": "/api/demand-metrics",
                        "method": "GET",
                        "description": "需要メトリクスデータを取得",
                    }
                ],
            },
        )

    def handle_metrics(self):
        try:
            latest_file, snapshot_id, observed_at = select_latest_snapshot(
                Path("data/dashboard")
            )
            df = pd.read_parquet(latest_file).sort_values(
                "potential_sales", ascending=False
            )
            self.send_json_response(
                200,
                {
                    "data": df.to_dict(orient="records"),
                    "timestamp": observed_at.timestamp(),
                    "snapshot_id": snapshot_id,
                    "filename": latest_file.name,
                },
            )
        except FileNotFoundError:
            self.handle_not_found("No metrics data found")
        except Exception as exc:
            self.handle_server_error(str(exc))

    def send_json_response(self, status_code, data):
        response_body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def handle_not_found(self, message="Resource not found"):
        self.send_json_response(
            404, {"error": True, "message": message, "status": 404}
        )

    def handle_server_error(self, message="Internal server error"):
        self.send_json_response(
            500, {"error": True, "message": message, "status": 500}
        )

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def get_local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
        sock.close()
        return local_ip
    except OSError:
        return "127.0.0.1"


def setup_windows_firewall(port):
    if platform.system() != "Windows":
        return False, "このコマンドはWindowsでのみ使用できます"

    try:
        rule_check = subprocess.run(
            'netsh advfirewall firewall show rule name="Hitaiou Dashboard"',
            capture_output=True,
            text=True,
            check=False,
        )
        if (
            "規則が見つかりません" in rule_check.stdout
            or "No rules match" in rule_check.stdout
        ):
            commands = [
                f'netsh advfirewall firewall add rule name="Hitaiou Dashboard" dir=in action=allow protocol=TCP localport={port}',
                f'netsh advfirewall firewall add rule name="Hitaiou Dashboard" dir=out action=allow protocol=TCP localport={port}',
            ]
            for command in commands:
                result = subprocess.run(
                    command, capture_output=True, text=True, check=False
                )
                if result.returncode != 0:
                    return False, f"ファイアウォールの設定に失敗しました: {result.stderr}"
            return True, "ファイアウォールの設定が完了しました"
        return True, "ファイアウォールのルールは既に存在します"
    except OSError as exc:
        return False, f"エラーが発生しました: {exc}"


def main():
    api_port = 8001
    print("\n" + "=" * 60)
    print("     Hitaiou Dashboard API Server")
    print("=" * 60 + "\n")

    _, message = setup_windows_firewall(api_port)
    print(f"ファイアウォール設定: {message}\n")
    print(f"APIサーバー起動: http://{get_local_ip()}:{api_port}")
    print("\nCtrl+C で終了")
    print("-" * 60 + "\n")

    server = HTTPServer(("0.0.0.0", api_port), DashboardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを終了します")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
