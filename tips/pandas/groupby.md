# pandas groupby の使い方

## 基本構文

```python
df.groupby("グループ化するカラム")["集計対象カラム"].集計関数()
```

## よく使う集計関数

| 関数 | 説明 |
|------|------|
| `mean()` | 平均値 |
| `median()` | 中央値 |
| `sum()` | 合計 |
| `count()` | 件数 |
| `min()` / `max()` | 最小値 / 最大値 |
| `std()` | 標準偏差 |
| `nunique()` | ユニーク件数 |
| `first()` / `last()` | 最初 / 最後の値 |

## 使用例

```python
import pandas as pd

df = pd.DataFrame({
    "action": ["view", "view", "purchase", "view", "purchase"],
    "duration": [10, 20, 30, None, 50],
    "user": ["A", "B", "A", "A", "B"]
})
```

### 1. 基本の集計（結果はグループごとに1行）

```python
df.groupby("action")["duration"].mean()
# action
# purchase    40.0
# view        15.0
```

### 2. 複数カラムの集計

```python
df.groupby("action")["duration"].agg(["mean", "median", "count"])
```

### 3. 複数カラムでグループ化

```python
df.groupby(["action", "user"])["duration"].sum()
```

### 4. transform - 元の行数を保ったまま集計値を返す

```python
# 各行に、同じactionグループの中央値を返す
df.groupby("action")["duration"].transform("median")
# 0    15.0  (viewの中央値)
# 1    15.0  (viewの中央値)
# 2    40.0  (purchaseの中央値)
# 3    15.0  (viewの中央値)
# 4    40.0  (purchaseの中央値)
```

`transform`は元のDataFrameと同じ行数を返すため、`fillna`と組み合わせて欠損値補完に使える。

```python
# duration が NaN の行だけグループの中央値で埋める
df["duration"] = df["duration"].fillna(
    df.groupby("action")["duration"].transform("median")
)
```

### 5. agg - カラムごとに異なる集計

```python
df.groupby("action").agg(
    avg_duration=("duration", "mean"),
    user_count=("user", "nunique")
)
```

### 6. filter - 条件を満たすグループだけ残す

```python
# レコードが2件以上あるグループだけ残す
df.groupby("action").filter(lambda x: len(x) >= 2)
```

### 7. sort_values - 集計結果のソート

```python
# error_count の降順でソート
df.groupby("endpoint").agg(
    total_requests=("status", "count"),
    error_count=("status", lambda x: (x >= 400).sum()),
).reset_index().sort_values("error_count", ascending=False)
```

| 引数 | 説明 |
|------|------|
| `by` | ソート対象のカラム名（文字列 or リスト） |
| `ascending` | `True`=昇順（デフォルト）、`False`=降順 |

```python
# 複数カラムでソート（error_count降順 → total_requests降順）
.sort_values(["error_count", "total_requests"], ascending=[False, False])
```

**注意**: `groupby().agg()` の結果はグループキーがインデックスになるため、`.reset_index()` してから `.sort_values()` するのが扱いやすい。

### 8. 多軸クロス集計後に最大カテゴリを取得する

2軸でグループ化した結果を「行 × 列」の表に変換し、各行の最大列名を取得するパターン。

```python
# region × category の売上表を作る
cat_rev = df.groupby(["region", "category"])["revenue"].sum().unstack()
#          Electronics  Fashion  Food
# region
# North         5000     3000    1200
# South         2000     8000     900

# 各 region で売上1位の category 名を取得
top_category = cat_rev.idxmax(axis=1)
# region
# North    Electronics
# South        Fashion
```

`idxmax(axis=1)` = 各行で最大値の **列名** を返す（`axis=0` は列ごとの最大行名）。

## groupby().unstack() vs pivot_table() の使い分け

どちらも「2軸クロス集計表」を作る。結果は同じ。

```python
# groupby().unstack()
cat_rev = df.groupby(["region", "category"])["revenue"].sum().unstack()

# pivot_table()（同じ結果）
cat_rev = df.pivot_table(
    values="revenue",
    index="region",
    columns="category",
    aggfunc="sum"
)
```

| | `groupby().unstack()` | `pivot_table()` |
|---|---|---|
| 向いている場面 | groupby の流れで書いている時 | 「クロス集計したい」と直感的に書く時 |
| 欠損値の扱い | `NaN`（デフォルト） | `fill_value=0` で0埋めしやすい |
| 複数集計関数 | 別途 `agg()` が必要 | `aggfunc=["sum", "count"]` で一括可能 |
| 可読性 | groupby の続きとして読める | 引数が明示的で意図が伝わりやすい |

```python
# pivot_table の fill_value と複数 aggfunc の例
df.pivot_table(
    values="revenue",
    index="region",
    columns="category",
    aggfunc=["sum", "count"],
    fill_value=0          # NaN を 0 に置換
)
```

**ETL での典型パターン**: groupby で集計 → `unstack()` で表に変換 → `idxmax(axis=1)` で最大カテゴリ取得。

## groupby vs transform の違い

| | `groupby().mean()` | `groupby().transform("mean")` |
|---|---|---|
| 戻り値の行数 | グループ数分 | 元のDF と同じ |
| 用途 | 集計レポート | 元DFへの値埋め・カラム追加 |
