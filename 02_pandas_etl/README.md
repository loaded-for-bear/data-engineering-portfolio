# 02. CSV ETL（pandas基礎）

## 概要

売上データのCSVを読み込み、不正データの除外・売上金額の計算・商品別集計を行うETLパイプライン。
pandasの基本操作（読み込み、フィルタリング、groupby）を活用する。

## 使用技術

- pandas: `read_csv`, `to_numeric`, `to_datetime`, `groupby`, `agg`
- データクレンジング（不正値の除外）

## 入力データ

- `data/sales_raw.csv` — 売上生データ（一部に不正データを含む）

## 出力

- `sales_cleaned.csv` — クレンジング後のデータ
- `sales_summary.csv` — 商品別売上集計

## 実行方法

```bash
python etl_sales.py
```

## 処理内容

1. **Extract**: CSVファイルを pandas で読み込み
2. **Transform**: 不正データ除外（負数quantity、不正日付、空の商品名）、売上金額計算
3. **Load**: クレンジング済みデータと商品別集計をCSV出力
