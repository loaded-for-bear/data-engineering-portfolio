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

## groupby vs transform の違い

| | `groupby().mean()` | `groupby().transform("mean")` |
|---|---|---|
| 戻り値の行数 | グループ数分 | 元のDF と同じ |
| 用途 | 集計レポート | 元DFへの値埋め・カラム追加 |
