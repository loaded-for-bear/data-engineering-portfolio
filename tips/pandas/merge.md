# pandas merge の使い方

## 基本構文

```python
pd.merge(left_df, right_df, on="共通カラム名", how="結合方法")
```

## 結合方法（how）

| how | 説明 | SQLでの対応 |
|-----|------|-------------|
| `inner` | 両方に存在するもののみ（デフォルト） | INNER JOIN |
| `left` | 左のDFを全て残す。右に一致がなければNaN | LEFT JOIN |
| `right` | 右のDFを全て残す | RIGHT JOIN |
| `outer` | 両方の全レコードを残す | FULL OUTER JOIN |

## 使用例

```python
import pandas as pd

employees = pd.DataFrame({
    "emp_id": ["E001", "E002", "E003"],
    "name": ["田中", "鈴木", "佐藤"],
    "dept_id": ["D001", "D002", "D999"]
})

departments = pd.DataFrame({
    "dept_id": ["D001", "D002", "D003"],
    "dept_name": ["営業部", "開発部", "人事部"]
})
```

### 1. inner（両方に存在するもののみ）

```python
pd.merge(employees, departments, on="dept_id", how="inner")
#   emp_id  name dept_id dept_name
# 0  E001   田中   D001    営業部
# 1  E002   鈴木   D002    開発部
# ※ E003(D999) と D003(人事部) は消える
```

### 2. left（左を全て残す）

```python
pd.merge(employees, departments, on="dept_id", how="left")
#   emp_id  name dept_id dept_name
# 0  E001   田中   D001    営業部
# 1  E002   鈴木   D002    開発部
# 2  E003   佐藤   D999      NaN    ← 一致なしはNaN
```

### 3. outer（両方の全レコード）

```python
pd.merge(employees, departments, on="dept_id", how="outer")
#   emp_id  name dept_id dept_name
# 0  E001   田中   D001    営業部
# 1  E002   鈴木   D002    開発部
# 2  E003   佐藤   D999      NaN
# 3   NaN   NaN   D003    人事部    ← 右のみのレコードも残る
```

## 左右でカラム名が異なる場合

```python
pd.merge(left_df, right_df, left_on="employee_id", right_on="emp_id", how="left")
```

## 複数キーで結合

```python
pd.merge(df1, df2, on=["dept_id", "year"], how="inner")
```

## 結合後のNaN確認

```python
merged = pd.merge(employees, departments, on="dept_id", how="left")

# NaNがある行 = 結合相手がなかった = 不整合データ
unmatched = merged[merged["dept_name"].isna()]
```

## merge vs join の違い

| | `pd.merge()` | `df.join()` |
|---|---|---|
| 結合キー | 任意のカラム（`on`で指定） | インデックス（デフォルト） |
| 柔軟性 | 高い | インデックス結合に特化 |
| 使いやすさ | 一般的にこちらを使う | `set_index` が必要な場合が多い |

基本的には `pd.merge()` を使えばOK。

## indicator オプション（差分検出に便利）

`indicator=True` を指定すると、各行がどちら由来かを示す `_merge` カラムが追加される。
**outer join と組み合わせることで、CDC（差分検出）に活用できる。**

### `_merge` の値

| 値 | 意味 |
|----|------|
| `left_only` | 左のDFにのみ存在 |
| `right_only` | 右のDFにのみ存在 |
| `both` | 両方に存在 |

### 基本例

```python
df_prev = pd.DataFrame({
    "product_id": ["P001", "P002", "P003"],
    "price": [100, 200, 300]
})

df_curr = pd.DataFrame({
    "product_id": ["P002", "P003", "P004"],
    "price": [250, 300, 400]
})

merged = pd.merge(df_prev, df_curr, on="product_id", how="outer", indicator=True)
#   product_id  price_x  price_y      _merge
# 0       P001    100.0      NaN   left_only   ← 削除された
# 1       P002    200.0    250.0        both   ← 両方にある（価格変更あり）
# 2       P003    300.0    300.0        both   ← 両方にある（変更なし）
# 3       P004      NaN    400.0  right_only   ← 新規追加
```

### CDC（差分検出）での活用パターン

```python
merged = pd.merge(df_prev, df_curr, on="product_id", how="outer",
                  suffixes=("_old", "_new"), indicator=True)

# 新規（INSERT）
inserted = merged[merged["_merge"] == "right_only"]

# 削除（DELETE）
deleted = merged[merged["_merge"] == "left_only"]

# 両方に存在するレコード → さらにUPDATED / UNCHANGEDに分類
both = merged[merged["_merge"] == "both"]
```

### カスタム名をつける

```python
pd.merge(df1, df2, on="id", how="outer", indicator="source")
# "_merge" の代わりに "source" というカラム名になる
```

---

## よくあるミス

1. **`on` のカラム名が一致しない** → `left_on` / `right_on` を使う
2. **重複行が増える** → 結合キーに重複がある場合、組み合わせ分だけ行が増える（1対多の結合）
3. **カラム名の衝突** → 両方のDFに同名カラムがあると `_x`, `_y` が付く。`suffixes` パラメータで制御可能

```python
pd.merge(df1, df2, on="id", suffixes=("_left", "_right"))
```
