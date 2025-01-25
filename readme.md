# Hitaiou Dashboard

非対応改変の需要を可視化するダッシュボードアプリケーションです。Googleフォームから収集したデータを基に、BOOTHのアバターと衣装の組み合わせごとの需要をランキング形式で表示します。

## データの流れ

1. ユーザー入力（Googleフォーム: https://forms.gle/JWDXcChpWzsqpmY97）
https://docs.google.com/forms/d/1xzy5yyXuzG-LZD-TX-bU_l8UVZd5REguUh0Kr7NYdjw/edit#response=ACYDBNgcsdZsQlAF1c19vri3uuRaJNoNQI1-psSG07z_FfrIq_gAvATd-EQbUiel5ROQoRA

- アバターURLの例：`https://mukumi.booth.pm/items/5813187`
- 衣装URLの例：`https://vagrant.booth.pm/items/6082952`
- Twitter ID（必須）
- 希望価格（任意）
- 希望作業者名（任意）

2. データ処理（スプレッドシート: https://docs.google.com/spreadsheets/d/1k133iin4Fu4SHqSY7qSs9CVWFPAF0PW_F30GBFWIqRg/）

具体例：
- アバター「mukumi/5813187」と衣装「vagrant/6082952」の組み合わせ
- リクエスト数：8件
- 中央値価格：1,500円
- 潜在市場規模：12,000円（8件 × 1,500円）

## セットアップ

1. パッケージのインストール:
```bash
pip install fastapi uvicorn pandas pyarrow requests beautifulsoup4
```

2. 設定ファイル`config.json`を作成:
```json
{
    "api_key": "YOUR-GOOGLE-SHEETS-API-KEY",
    "spreadsheet_id": "1k133iin4Fu4SHqSY7qSs9CVWFPAF0PW_F30GBFWIqRg"
}
```

3. データ更新（定期実行推奨）:
```bash
python process.py
```

4. サーバー起動:
```bash
python server.py
```

## アクセス方法の例

実際のアクセスURLは、サーバー起動時にコンソールに表示されます：

- ローカル環境: `http://localhost:8000`
- 同じネットワーク内: `http://192.168.11.22:8000`
- インターネット: `http://219.75.138.126:8000`

## データ構造

処理済みデータは以下の形式で保存されます：

demand_metrics_[timestamp].parquet
```
avatar_id | item_id | request_count | median_price | potential_sales
5813187  | 6082952 | 8            | 1500         | 12000
```

## 現在対応している商品例

アバター:
- mukumi: https://mukumi.booth.pm/items/5813187

衣装:
- vagrant: https://vagrant.booth.pm/items/6082952
- ornamentcorpse: https://ornamentcorpse.booth.pm/items/6082952



---


需要収集
https://docs.google.com/forms/d/1xzy5yyXuzG-LZD-TX-bU_l8UVZd5REguUh0Kr7NYdjw/edit#response=ACYDBNgcsdZsQlAF1c19vri3uuRaJNoNQI1-psSG07z_FfrIq_gAvATd-EQbUiel5ROQoRA


https://docs.google.com/spreadsheets/d/1k133iin4Fu4SHqSY7qSs9CVWFPAF0PW_F30GBFWIqRg/edit?gid=1261115119#gid=1261115119

ダッシュボード
http://192.168.11.22:8000


---

