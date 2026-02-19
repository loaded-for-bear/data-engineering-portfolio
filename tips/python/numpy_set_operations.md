# NumPy 集合演算（setdiff1d / intersect1d / union1d）

## 概要

NumPy の集合演算関数は、配列（インデックスや ID の集合）に対して
「差集合・積集合・和集合」を高速に求める。
テストデータ生成やフィルタリングで頻出する。

## setdiff1d — 差集合（aにあってbにないもの）

```python
import numpy as np

a = np.array([1, 2, 3, 4, 5])
b = np.array([2, 4])

np.setdiff1d(a, b)  # → [1, 3, 5]
```

**名前の読み方**: `set`(集合) + `diff`(difference, 差) + `1d`(1次元配列)

### 典型的な使い方: 「使用済みインデックスを除外して選ぶ」

```python
n = 1000
used_idx = np.array([3, 17, 42, 99])   # すでに使ったインデックス

remaining = np.setdiff1d(np.arange(n), used_idx)  # 残りのインデックス
new_idx = np.random.choice(remaining, size=50, replace=False)
```

テストデータ生成で「個別不正と全不正が同じ行に重複しないようにする」場面などで使う:

```python
# 個別不正に使ったインデックスを除外してから全不正用を選ぶ
remaining = np.setdiff1d(np.arange(output_count), invalid_idx)
all_invalid_idx = np.random.choice(remaining, size=n_all_invalid, replace=False)
```

## 関連関数の比較

| 関数 | 意味 | 例（a=[1,2,3], b=[2,4]） |
|------|------|--------------------------|
| `np.setdiff1d(a, b)` | aにあってbにないもの | `[1, 3]` |
| `np.intersect1d(a, b)` | aとbの両方にあるもの | `[2]` |
| `np.union1d(a, b)` | aまたはbにあるもの（重複なし） | `[1, 2, 3, 4]` |
| `np.isin(a, b)` | aの各要素がbに含まれるか（bool配列） | `[False, True, False]` |

```python
a = np.array([1, 2, 3])
b = np.array([2, 4])

np.setdiff1d(a, b)   # → [1, 3]
np.intersect1d(a, b) # → [2]
np.union1d(a, b)     # → [1, 2, 3, 4]
np.isin(a, b)        # → [False, True, False]
```

## isin との使い分け

```python
# setdiff1d: 差集合の配列が欲しいとき
remaining = np.setdiff1d(np.arange(n), used_idx)

# isin: フィルタリング条件として使いたいとき（bool mask）
mask = ~np.isin(np.arange(n), used_idx)  # setdiff1d と同じ意味
remaining = np.arange(n)[mask]
```

大規模配列では `isin` のほうがメモリ効率が良い場合がある。
小〜中規模（数十万件以下）なら `setdiff1d` で十分。
