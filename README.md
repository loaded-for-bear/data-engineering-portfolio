# Data Engineering ETL Portfolio

Python によるデータエンジニアリング（ETL）の実践課題集です。
CSV・JSON・ログ・API など多様なデータソースに対して、抽出・変換・ロードのパイプラインを実装しています。

## 技術スタック

- **言語**: Python 3.12
- **主要ライブラリ**: pandas, requests, Flask（モックサーバー）, logging
- **標準ライブラリ**: csv, json, sqlite3, re, logging, pathlib
- **データストア**: CSV, SQLite

## 課題一覧

| # | タイトル | 主なスキル | フォルダ |
|---|---------|-----------|---------|
| 1 | CSV基礎（標準ライブラリ） | csv.DictReader, 辞書集計 | `01_csv_basics/` |
| 2 | CSV ETL（pandas基礎） | pandas, クレンジング, groupby | `02_pandas_etl/` |
| 3 | CSV ETL（欠損値・分類） | fillna, transform, カテゴリ分類 | `03_csv_missing_values/` |
| 4 | 複数CSVマージ・整合性検証 | merge(JOIN), 不整合検出 | `04_multi_csv_merge/` |
| 5 | JSON正規化 → SQLite | json, sqlite3, DB正規化, SQL集計 | `05_json_to_sqlite/` |
| 6 | テキストログパース・異常検知 | re(正規表現), 時間帯集計, 異常検知 | `06_log_parsing/` |
| 7 | API連携・Web取得 | requests, ページネーション, リトライ | `07_api_etl/` |
| 8 | CDC（スナップショット差分検出） | pd.merge(outer), ベクトル演算, CDC設計 | `08_cdc_snapshot/` |

## セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/<your-username>/data-engineering-portfolio.git
cd data-engineering-portfolio

# 依存ライブラリをインストール
pip install pandas requests flask
```

## 実行方法

各フォルダに移動して Python スクリプトを実行します。

```bash
# 例: 02番の課題を実行
cd 02_pandas_etl
python etl_sales.py
```

詳細は各フォルダの `README.md` を参照してください。

## フォルダ構成

```
data-engineering-portfolio/
├── README.md
├── 01_csv_basics/
│   ├── README.md
│   ├── analyze_logs.py
│   └── data/
├── 02_pandas_etl/
│   ├── README.md
│   ├── etl_sales.py
│   └── data/
├── 03_csv_missing_values/
│   ├── README.md
│   ├── etl_pipeline.py
│   └── data/
├── 04_multi_csv_merge/
│   ├── README.md
│   ├── etl_merge.py
│   └── data/
├── 05_json_to_sqlite/
│   ├── README.md
│   ├── etl_json_to_sqlite.py
│   └── data/
├── 06_log_parsing/
│   ├── README.md
│   ├── parse_log.py
│   └── data/
├── 07_api_etl/
│   ├── README.md
│   ├── etl_api.py
│   └── mock_server.py
├── 08_cdc_snapshot/
│   ├── README.md
│   ├── cdc_snapshot.py
│   └── data/
└── tips/
    ├── data_engineering/
    ├── pandas/
    └── python/
```
