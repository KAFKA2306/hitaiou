
M:
cd M:\DB\hitaiou\
conda activate hitaiou

# 管理者権限のコマンドプロンプトで実行
netsh advfirewall firewall add rule name="Hitaiou Dashboard External" dir=in action=allow protocol=TCP localport=8001 remoteip=any

python server.py

curl http://219.75.138.126:8001/