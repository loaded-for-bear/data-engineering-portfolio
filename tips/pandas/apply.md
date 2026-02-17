# df.apply()

DataFrame の各行（または各列）に関数を適用して結果を返すメソッド。

## 基本構文

```python
df.apply(func, axis=0)  # axis=0: 列ごと（デフォルト）
df.apply(func, axis=1)  # axis=1: 行ごと
```

## axis の違い

```python
df = pd.DataFrame({"a": [1, 2, 3], "b": [10, 20, 30]})

# axis=0（列ごと）→ 各列の Series が func に渡る
df.apply(sum, axis=0)    # → a: 6, b: 60

# axis=1（行ごと）→ 各行の Series が func に渡る
df.apply(sum, axis=1)    # → 0: 11, 1: 22, 2: 33
```

## よくある使い方

```python
# 1. lambda で簡単な処理
df["total"] = df.apply(lambda row: row["a"] + row["b"], axis=1)

# 2. 名前付き関数で複雑な処理
def classify(row):
    if row["price"] > 10000:
        return "高額"
    return "通常"
df["class"] = df.apply(classify, axis=1)

# 3. 複数カラムを参照して文字列生成
df["summary"] = df.apply(
    lambda row: f"{row['name']}({row['price']}円)", axis=1
)
```

## apply vs ベクトル演算

| 場面 | 推奨 |
|------|------|
| 単純な比較・四則演算 | ベクトル演算（`df["a"] + df["b"]`） |
| 条件分岐が1つ | `np.where()` |
| 複数カラムを組み合わせて文字列生成 | `apply` |
| 行ごとにリストや辞書を作る | `apply` |

**原則**: ベクトル演算で書けるなら apply は使わない。apply は行ループなので遅い。
ただし文字列の組み立てなど、ベクトル演算に馴染まない処理には apply が適切。

## パフォーマンス目安（5万行）

- ベクトル演算: 数ミリ秒
- apply: 数百ミリ秒〜数秒
- iterrows: 数秒〜十数秒

apply は iterrows よりは速いが、ベクトル演算の 100倍程度遅い。
対象行数が少ない場合（UPDATE行のみ等）は問題にならない。
