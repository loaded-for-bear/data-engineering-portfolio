# tracemalloc — メモリ使用量の計測

## 概要

`tracemalloc` は Python 標準ライブラリのメモリプロファイラ。
コードブロックのピークメモリ使用量を計測できる。
`pip install` 不要で使える。

---

## 基本構文

```python
import tracemalloc

tracemalloc.start()          # 計測開始

# ... 計測したい処理 ...

current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()           # 計測終了

print(f"現在: {current / 1024 / 1024:.1f} MB")
print(f"ピーク: {peak / 1024 / 1024:.1f} MB")
```

- `current`: 計測終了時点のメモリ使用量（バイト）
- `peak`: 計測開始〜終了の間のピーク使用量（バイト）
- **ETLのメモリ評価には `peak` を使う**（処理中の最大値が重要）

---

## 処理時間との組み合わせ（ETL計測の定番パターン）

```python
import tracemalloc
import time

tracemalloc.start()
start = time.perf_counter()

# --- 計測したい処理 ---
df = pd.read_csv("orders_large.csv")
# ...

elapsed = time.perf_counter() - start
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"処理時間: {elapsed:.2f}s")
print(f"ピークメモリ: {peak / 1024 / 1024:.1f} MB")
```

---

## よく使う操作

```python
# スナップショット（どこでメモリを使っているか詳細に見る）
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics("lineno")
for stat in top_stats[:5]:
    print(stat)
# 出力例:
# my_etl.py:42: size=120 MiB, count=1, average=120 MiB
```

---

## 注意点

- **tracemalloc 自体のオーバーヘッド**: 計測中は数〜数十MB余分に消費する。
  本番のメモリ制限チェックには参考値として扱う。
- **マルチスレッド**: スレッドをまたいだ計測は正確でない場合がある。
- **C拡張のメモリ**: numpy/pandas の C レイヤーのメモリは計測対象外になることがある。
  実際の使用量は `psutil` の方が正確だが、tracemalloc は標準ライブラリで手軽。

---

## psutil との比較（使い分け）

| | tracemalloc | psutil |
|--|------------|--------|
| インストール | 不要（標準） | 要 `pip install` |
| 計測対象 | Python オブジェクトのみ | プロセス全体のRSS |
| 精度 | 中（C拡張は漏れる） | 高（OS レベル） |
| 用途 | ポートフォリオ・手軽な計測 | 本番監視・正確なメモリ管理 |

```python
# psutil を使う場合
import psutil, os
process = psutil.Process(os.getpid())
peak_mb = process.memory_info().rss / 1024 / 1024
print(f"RSS: {peak_mb:.1f} MB")
```

---

## ETL ポートフォリオでの使い方

メモリ制約（512MB）の証明として README に貼る：

```
案A（全件一括）:
  処理時間: 12.3s
  ピークメモリ: 487.2 MB  ← 制限 512MB に対して余裕なし

案B（チャンク処理）:
  処理時間: 8.7s
  ピークメモリ: 42.1 MB   ← 91% 削減
```
