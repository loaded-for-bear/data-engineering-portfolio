# pandas: drop_duplicates の使い方

## 基本構文

```python
df.drop_duplicates(subset=None, keep="first", inplace=False, ignore_index=False)
```

| パラメータ | デフォルト | 意味 |
|-----------|-----------|------|
| `subset` | `None`（全カラム） | 重複判定に使うカラムを指定 |
| `keep` | `"first"` | どの行を残すか（後述） |
| `inplace` | `False` | `True` にすると元の df を書き換える |
| `ignore_index` | `False` | `True` にすると 0 始まりで index を振り直す |

---

## keep の使い分け

| 値 | 動作 |
|----|------|
| `"first"` | 最初の1件を残す（残りを除外） |
| `"last"` | 最後の1件を残す（残りを除外） |
| `False` | 重複しているものを**全件**除外 |

```python
df = pd.DataFrame({
    "order_id": ["A", "B", "A", "C", "B"],
    "amount":   [100, 200, 100, 300, 200],
})

df.drop_duplicates(subset=["order_id"], keep="first")
# → A(1行目), B(2行目), C(4行目) の3件

df.drop_duplicates(subset=["order_id"], keep="last")
# → A(3行目), C(4行目), B(5行目) の3件

df.drop_duplicates(subset=["order_id"], keep=False)
# → C(4行目) の1件のみ（A, B は全件除外）
```

---

## ETL での典型的な使い方

### パターン1: 配信システムの再送による重複排除

```python
# 最初の到着を正とし、再送分を除外する
df = df.drop_duplicates(subset=["order_id"], keep="first")
```

- `keep="first"` を使う理由: 再送は元データの完全コピーなので、どれを残しても値は同じ
- ソート不要: 同一内容なので順序は結果に影響しない

### パターン2: 全カラムで完全一致の重複を排除

```python
# subset を省略すると全カラムが対象
df = df.drop_duplicates()
```

---

## チャンク処理との組み合わせ（注意点）

`drop_duplicates` は **DataFrame 全体** に対してしか使えない。
チャンク処理（`pd.read_csv(chunksize=N)`）では、チャンクをまたいだ重複を検知できない。

```python
# NG: チャンク内の重複しか除外できない
for chunk in pd.read_csv("data.csv", chunksize=10000):
    chunk = chunk.drop_duplicates(subset=["order_id"])  # チャンク内のみ有効

# OK: seen_ids で全チャンクにわたって管理する
seen_ids = set()
for chunk in pd.read_csv("data.csv", chunksize=10000):
    mask = ~chunk["order_id"].isin(seen_ids)
    chunk = chunk[mask]
    seen_ids.update(chunk["order_id"].tolist())
```

| 手法 | メモリ | チャンク対応 | 用途 |
|------|--------|------------|------|
| `drop_duplicates` | データ全体分 | 不可 | 全件一括読み込み時 |
| `seen_ids`（set） | order_id 数 × 数十バイト | 可 | チャンク処理時 |

50万件・UUID（36文字）の場合: `500,000 × ~100byte ≒ 50MB`（許容範囲内）

---

## 類似手法との比較

| 手法 | 速度 | 使い分け |
|------|------|---------|
| `drop_duplicates` | 速い（C拡張） | DataFrame 全体を持てるとき |
| `groupby().first()` | やや遅い | 重複行間で値が異なり「グループ内の集計値」を使いたいとき |
| `sort_values() + drop_duplicates` | 遅い | 「最新日付の1件を残す」など順序に意味があるとき |

---

## パフォーマンスの注意点

- `inplace=True` は読みやすさを下げるだけでほぼ速度メリットがない → 使わない
- `ignore_index=True` はインデックスを振り直すため、大量データでは若干コストがかかる
- 重複排除後に `reset_index(drop=True)` するなら `ignore_index=True` で代替できる
