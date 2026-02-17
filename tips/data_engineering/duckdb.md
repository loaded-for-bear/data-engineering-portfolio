# DuckDB

SQLインターフェースを持つ組み込み型の列指向分析データベース。「SQLite の分析版」と呼ばれる。

## 特徴

| 観点 | DuckDB | pandas | SQLite |
|------|--------|--------|--------|
| 処理方式 | 列指向（カラムナー） | 行指向（メモリ内） | 行指向（ディスク） |
| 大規模データ | 強い（ディスクスピル対応） | メモリに依存 | 遅い（分析向きでない） |
| クエリ言語 | SQL | Python API | SQL |
| インストール | `pip install duckdb` | `pip install pandas` | 標準ライブラリ |
| サーバー | 不要（組み込み型） | - | 不要 |

## なぜ DuckDB が強いのか

1. **列指向**: 分析クエリ（集計・フィルタ）で必要なカラムだけ読むため I/O が少ない
2. **メモリ効率**: データがメモリに収まらなくてもディスクにスピルして処理を継続できる
3. **CSV/Parquet直接クエリ**: DBにロードせずファイルを直接SQLで操作可能
4. **ベクトル化実行**: SIMD命令を活用し、バッチ単位で高速処理

## 基本的な使い方

```python
import duckdb

# CSVを直接クエリ（DB不要）
result = duckdb.sql("""
    SELECT * FROM 'data/products.csv'
    WHERE price > 10000
""").fetchdf()  # pandas DataFrame で返る

# 2つのCSVを直接JOIN
result = duckdb.sql("""
    SELECT
        curr.product_id,
        CASE
            WHEN prev.product_id IS NULL THEN 'INSERT'
            WHEN curr.product_id IS NULL THEN 'DELETE'
            WHEN curr.price != prev.price OR curr.stock != prev.stock THEN 'UPDATE'
            ELSE 'UNCHANGED'
        END AS change_type
    FROM 'snapshot_today.csv' curr
    FULL OUTER JOIN 'snapshot_yesterday.csv' prev
        ON curr.product_id = prev.product_id
""").fetchdf()
```

## pandas DataFrame との連携

```python
import pandas as pd
import duckdb

df = pd.read_csv("products.csv")

# pandas DataFrame を直接SQLでクエリ
result = duckdb.sql("""
    SELECT category, COUNT(*) as cnt, AVG(price) as avg_price
    FROM df
    GROUP BY category
""").fetchdf()
```

## CDC でのスケールアップ例

pandas で 50万件が厳しくなった場合の移行:

```python
# pandas版（メモリに全件乗せる）
df_merged = pd.merge(df_prev, df_curr, on="product_id", how="outer", indicator=True)

# DuckDB版（メモリ効率が良い）
result = duckdb.sql("""
    SELECT
        COALESCE(prev.product_id, curr.product_id) AS product_id,
        CASE
            WHEN prev.product_id IS NULL THEN 'INSERT'
            WHEN curr.product_id IS NULL THEN 'DELETE'
            WHEN prev.price != curr.price
              OR prev.stock != curr.stock
              OR prev.status != curr.status THEN 'UPDATE'
            ELSE 'UNCHANGED'
        END AS change_type
    FROM 'snapshot_prev.csv' prev
    FULL OUTER JOIN 'snapshot_curr.csv' curr
        ON prev.product_id = curr.product_id
""").fetchdf()
```

## pandas vs DuckDB の使い分け

| データ量 | 推奨 | 理由 |
|---------|------|------|
| 〜10万件 | pandas | シンプル、デバッグしやすい |
| 10万〜100万件 | DuckDB | メモリ効率、SQL の表現力 |
| 100万件〜 | Spark / BigQuery | 分散処理が必要 |

## インストール

```bash
pip install duckdb
```

サーバー不要、設定ファイル不要。pip install だけで即座に使える。
