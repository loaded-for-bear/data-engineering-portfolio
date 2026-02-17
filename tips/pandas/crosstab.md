# pd.crosstab()

2つのカテゴリ変数のクロス集計表（頻度表）を作成する関数。

## 基本構文

```python
pd.crosstab(index, columns)
# index: 行になるSeries
# columns: 列になるSeries
```

## 基本例

```python
pd.crosstab(df["category"], df["change_type"])
```

出力:
```
change_type  DELETE  INSERT  UNCHANGED  UPDATE
category
Electronics       0       0          2       4
Furniture         1       1          1       3
Stationery        0       1          2       2
```

## よく使うオプション

```python
# margins: 合計行・列を追加
pd.crosstab(df["category"], df["change_type"], margins=True)

# normalize: 割合表示（"index"=行ごと, "columns"=列ごと, "all"=全体）
pd.crosstab(df["category"], df["change_type"], normalize="index")

# values + aggfunc: 頻度以外の集計（合計、平均など）
pd.crosstab(df["category"], df["change_type"], values=df["price"], aggfunc="mean")
```

## crosstab vs groupby vs pivot_table

| 手法 | 用途 |
|------|------|
| `crosstab` | 2変数の頻度集計（カウント）がメイン |
| `groupby().size().unstack()` | crosstab と同等だが既存DFから |
| `pivot_table` | 任意の集計関数（mean, sum等）を使いたい場合 |

```python
# これらは同じ結果
pd.crosstab(df["category"], df["change_type"])
df.groupby(["category", "change_type"]).size().unstack(fill_value=0)
df.pivot_table(index="category", columns="change_type", aggfunc="size", fill_value=0)
```

crosstab は最もシンプルで、頻度のクロス集計には最適。
集計関数をカスタマイズしたい場合は pivot_table を使う。
