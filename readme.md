# Hitaiou Dashboard

BOOTHのアバター×衣装の需要データを処理し、集計結果をHTTP APIで参照するための小さなPythonアプリです。

## 現在の実行経路

1. `process.py` がGoogle Sheets APIから入力を取得し、BOOTH URLを正規化して `data/` 配下へ保存します。
2. `server.py` が `data/dashboard/demand_metrics_*.parquet` の最新ファイルを読み込みます。
3. HTTP APIはポート`8001`で起動します。

```bash
python -m pip install -r requirements.txt
python server.py
```

API:

- `GET /` — server statusと利用可能endpoint
- `GET /api/demand-metrics` — 最新の需要集計を`potential_sales`降順で返す

## データ取得

`process.py` のGoogle Sheets取得には `config.json` の `api_key` と `spreadsheet_id` が必要です。`config_handler.py` は設定ファイルが存在しない場合にtemplateを生成します。実credentialはrepositoryへcommitしないでください。

## 検証

```bash
python -m unittest discover -s tests -v
```

CIではdependency install、Python compile、unit tests、`server.py`起動後の`GET /` HTTP smoke test、clean checkoutを実行します。

## 未検証

外部公開URL、ルーター設定、外部frontend、Google Form/Sheetの現在の公開状態は、このrepositoryのCIでは検証していません。
