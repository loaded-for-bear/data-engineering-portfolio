# 04. 複数CSVマージ・整合性検証

## 概要

部門マスタ・社員マスタ・勤怠記録の3つのCSVを結合し、データの整合性を検証した上で、部門別勤怠サマリーを出力するETLパイプライン。

## 使用技術

- pandas: `merge`（LEFT JOIN）, `groupby`, `agg`
- データ整合性検証（存在しない外部キーの検出）
- NaN補完

## 入力データ

- `data/departments.csv` — 部門マスタ（4部門）
- `data/employees.csv` — 社員マスタ（10名、うち1名は無効な部署ID）
- `data/attendance.csv` — 勤怠記録（15件、一部に品質問題あり）

## 出力

- `data_issues.csv` — 検出された不整合データ（無効な部署ID、無効な社員ID、打刻欠損）
- `dept_summary.csv` — 部門別勤怠サマリー（勤務時間、残業回数）
- `employee_work.csv` — 社員別勤務メトリクス

## 実行方法

```bash
python etl_merge.py
```

## 処理内容

1. **Extract**: 3つのCSVを読み込み
2. **Validate**: 3種類の不整合を検出（無効な部署ID、無効な社員ID、打刻欠損）
3. **Transform**: LEFT JOINで結合、勤務時間の計算、残業回数の集計
4. **Load**: 不整合レポート + 部門別/社員別サマリーをCSV出力
