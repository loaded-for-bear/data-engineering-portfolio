# リスト内包表記（List Comprehension）

## 基本構文

```python
[式 for 変数 in イテラブル]
[式 for 変数 in イテラブル if 条件]
```

### 通常のループとの対比

```python
# ループ版
result = []
for x in [1, 2, 3, 4, 5]:
    result.append(x * 2)

# 内包表記版（同じ意味）
result = [x * 2 for x in [1, 2, 3, 4, 5]]
# → [2, 4, 6, 8, 10]
```

### 条件フィルタ付き

```python
# 偶数だけ取り出す
result = [x for x in [1, 2, 3, 4, 5] if x % 2 == 0]
# → [2, 4]
```

---

## 辞書内包表記

`{}` を使うと辞書が作れる。

```python
prices = {"apple": 100, "banana": 80, "cherry": 200}

# 全品10%引き
sale = {name: price * 0.9 for name, price in prices.items()}
# → {"apple": 90.0, "banana": 72.0, "cherry": 180.0}
```

---

## 三項演算子との組み合わせ

式の部分に `A if 条件 else B` を使うと、条件によって値を変えられる。

```python
# 三項演算子の基本形
値 = A if 条件 else B

# 例: 0除算を避ける
avg = revenue / orders if orders > 0 else 0.0
```

---

## ETL でよく使うパターン：辞書のリスト → DataFrame

`pd.DataFrame()` は「辞書のリスト」を受け取って表に変換する。
内包表記で集計辞書を行データに変換するのが典型的な使い方。

```python
# 集計辞書（チャンク処理で累積した結果）
category_stats = {
    "Electronics": {"orders": 1000, "qty": 2000, "revenue": 500000.0},
    "Clothing":    {"orders":  800, "qty": 1600, "revenue": 320000.0},
}

# 内包表記で辞書のリストに変換 → DataFrame化
df_category = pd.DataFrame([
    {
        "category": cat,
        "total_orders": s["orders"],
        "total_quantity": s["qty"],
        "total_revenue": s["revenue"],
        "avg_order_value": s["revenue"] / s["orders"] if s["orders"] > 0 else 0.0,
    }
    for cat, s in category_stats.items()
])
```

出力される DataFrame：

| category | total_orders | total_quantity | total_revenue | avg_order_value |
|----------|-------------|----------------|---------------|-----------------|
| Electronics | 1000 | 2000 | 500000.0 | 500.0 |
| Clothing | 800 | 1600 | 320000.0 | 400.0 |

### ループ版と対比

```python
# ループ版（同じ意味）
rows = []
for cat, s in category_stats.items():
    rows.append({
        "category": cat,
        "total_orders": s["orders"],
        ...
    })
df_category = pd.DataFrame(rows)
```

---

## パフォーマンス

内包表記はループより高速。理由は Python インタプリタの最適化が効くため。
ただし、**可読性が著しく下がる場合はループの方が望ましい**。

```python
# やりすぎ（読みにくい）
result = [f(x) for x in data if g(x) and h(x) for y in x if y > 0]

# この場合は素直にループで書く
```

---

## 使い分けの判断基準

| 状況 | 選択 |
|------|------|
| 1行で書けて意図が明確 | 内包表記 |
| 処理が複雑・多段階 | ループ |
| デバッグ中（中間値を確認したい） | ループ |
| DataFrame の材料（辞書のリスト）を作る | 内包表記が定番 |
