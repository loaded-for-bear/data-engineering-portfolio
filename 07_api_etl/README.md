# 07. API連携・Web取得

## 概要

ページネーション付きのREST APIから従業員データを全件取得し、部署マスタと結合・欠損値を補完した上で、部署別レポートを生成するETLパイプライン。リトライ処理・ログ出力も実装。

## 使用技術

- `requests`: API呼び出し、ページネーション処理
- `logging`: 実行ログの出力
- pandas: データ結合、欠損値補完（`groupby` + `transform`）、集計
- リトライ処理（最大3回、1秒間隔）

## ファイル構成

- `etl_api.py` — ETLスクリプト本体
- `mock_server.py` — テスト用モックAPIサーバー（Flask）

## 出力

- `department_report.csv` — 部署別集計レポート（人数、平均/最高/最低給与、平均勤続年数）
- `employees_enriched.csv` — 全従業員データ（部署名付き・欠損補完済み）

## 実行方法

```bash
# 1. モックサーバーを起動（別ターミナル）
pip install flask
python mock_server.py

# 2. ETLスクリプトを実行
python etl_api.py
```

## 処理内容

1. **Extract**: ページネーションを辿って全従業員データを取得（リトライ付き）
2. **Transform**: 部署名の結合、欠損給与を部署平均で補完、勤続年数の算出
3. **Load**: 部署別集計レポート + 個人別データをCSV出力
