# DataFrame のカラム選択

## 1. 単一カラム（Series が返る）

```python
df["price"]          # → Series
df.price             # → 同じだが、カラム名にスペースや予約語があると使えない
```

## 2. 複数カラム（DataFrame が返る）

```python
# リストで指定
df[["product_id", "change_type", "details"]]

# 変数でカラム名リストを渡す
cols = ["product_id", "change_type", "details"]
df[cols]
```

## 3. パターンで選択

```python
# 特定の文字列を含むカラム
df.filter(like="_changed")        # カラム名に "_changed" を含む

# 正規表現でマッチ
df.filter(regex="^price")         # "price" で始まるカラム

# 特定の接尾辞
df[[c for c in df.columns if c.endswith("_old")]]  # リスト内包表記
```

## 4. 位置で選択（iloc）

```python
df.iloc[:, 0:3]      # 0〜2列目
df.iloc[:, [0, 3, 5]] # 0, 3, 5列目
```

## 5. 型で選択

```python
df.select_dtypes(include=["int64", "float64"])   # 数値カラムのみ
df.select_dtypes(exclude=["object"])              # 文字列以外
```

## 6. カラムの除外

```python
df.drop(columns=["_merge", "updated_at_changed"])  # 指定カラムを除外
```

## よくある使い方

```python
# CSV出力時に必要なカラムだけ選ぶ
output_cols = ["product_id", "change_type", "changed_columns", "details"]
df[output_cols].to_csv("report.csv", index=False)

# 一時的な作業カラムを除外して出力
work_cols = [c for c in df.columns if c.endswith("_changed")]
df.drop(columns=work_cols).to_csv("clean.csv", index=False)
```

## 注意点

- `df["col"]` は Series、`df[["col"]]` は DataFrame（1列でもDFが返る）
- 存在しないカラムを指定すると KeyError になる
- カラムの存在確認: `"col_name" in df.columns`
