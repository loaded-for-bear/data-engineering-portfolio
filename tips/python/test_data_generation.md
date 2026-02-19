# テストデータ生成 — pandas + numpy + uuid

## 概要

ETL のテスト・パフォーマンス計測用のダミー CSV を生成する方法。
大量データ（数十万〜数百万件）を高速に作るには、numpy のベクトル演算を中心に組み立てる。

## 基本パターン

```python
import uuid
import numpy as np
import pandas as pd

n = 500000

df = pd.DataFrame({
    "order_id": [str(uuid.uuid4()) for _ in range(n)],
    "category": np.random.choice(["A", "B", "C"], size=n),
    "quantity": np.random.randint(1, 101, size=n),
    "price": np.round(np.random.uniform(1.0, 999.99, size=n), 2),
})
df.to_csv("output.csv", index=False)
```

## カラム種類別の生成方法

| データ型 | 生成方法 | 例 |
|---------|---------|-----|
| UUID | `uuid.uuid4()` | `[str(uuid.uuid4()) for _ in range(n)]` |
| 固定リスト選択 | `np.random.choice()` | `np.random.choice(["A", "B"], size=n)` |
| 整数範囲 | `np.random.randint()` | `np.random.randint(1, 101, size=n)` |
| 小数範囲 | `np.random.uniform()` + `np.round()` | `np.round(np.random.uniform(1.0, 999.99, size=n), 2)` |
| 日時 | `pd.date_range()` + `np.random.choice()` | 下記参照 |
| パターン付きID | f-string + `np.random.randint()` | `[f"C{i:06d}" for i in np.random.randint(1, 999999, size=n)]` |

### 日時の生成

```python
# 特定日の24時間内でランダムな日時を生成
base_date = pd.Timestamp("2026-02-18")
random_seconds = np.random.randint(0, 86400, size=n)  # 0〜86399秒
timestamps = base_date + pd.to_timedelta(random_seconds, unit="s")
df["order_date"] = timestamps.strftime("%Y-%m-%dT%H:%M:%S")
```

#### 基準日を実行日にする

```python
base_date = pd.Timestamp("today").normalize()  # 今日の 00:00:00
```

`.normalize()` で時刻部分を `00:00:00` にリセットする。固定日付にしたい場合は文字列指定で十分。

| 書き方 | 結果 |
|--------|------|
| `pd.Timestamp("2026-02-18")` | 固定日付の 00:00:00 |
| `pd.Timestamp("today").normalize()` | 実行日の 00:00:00 |
| `pd.Timestamp.now().normalize()` | 同上（別記法） |

### パターン付きIDの生成

```python
# C + 6桁数字（例: C001234）
df["customer_id"] = [f"C{i:06d}" for i in np.random.randint(1, 999999, size=n)]

# P + 5桁数字（例: P01234）
df["product_id"] = [f"P{i:05d}" for i in np.random.randint(1, 99999, size=n)]
```

### フォーマット指定子 `:06d` の読み方

`f"{i:06d}"` の `:06d` は3要素で構成される:

| 位置 | 文字 | 意味 |
|------|------|------|
| 1文字目 | `0` | 埋め文字（ゼロ埋め） |
| 2文字目 | `6` | 最小幅（6文字） |
| 3文字目 | `d` | 型（整数 = decimal） |

```python
i = 42
f"{i:06d}"  # → "000042"  （ゼロ埋め・6桁）
f"{i:6d}"   # → "    42"  （スペース埋め・6桁）
f"{i:d}"    # → "42"      （埋めなし）
```

## 不正データの混入

テスト用データには意図的に不正データを混ぜる。

### 混入率の目安

| データセット | 正常 | 個別不正 | 全不正 | 重複行 |
|-------------|------|---------|--------|--------|
| 小規模（テスト用） | 70% | 15% | 5% | 10% |
| 本番想定（計測用） | 95% | 2% | 1% | 2% |

### 混入方法

```python
n = 1000
n_invalid = int(n * 0.15)  # 個別不正: 15%

# 方法1: インデックス指定で上書き
invalid_idx = np.random.choice(n, size=n_invalid, replace=False)
df.loc[invalid_idx[:50], "quantity"] = -1          # 負の値
df.loc[invalid_idx[50:100], "unit_price"] = -99.9  # 負の値
df.loc[invalid_idx[100:], "order_date"] = "INVALID" # パース不可

# 方法2: 重複行の追加（既存行をコピーして末尾に追加）
n_dup = int(n * 0.10)  # 重複: 10%
dup_idx = np.random.choice(n, size=n_dup, replace=False)
df_with_dups = pd.concat([df, df.iloc[dup_idx]], ignore_index=True)
```

## シード固定（再現性）

```python
np.random.seed(42)
# 以降の np.random 呼び出しが再現可能になる
```

テストの再現性を確保するため、生成スクリプトには必ずシードを固定する。
ただし `uuid.uuid4()` はシード固定できない。再現性が必要な場合は代替手段を使う:

```python
import random
random.seed(42)
order_ids = [f"{random.getrandbits(128):032x}" for _ in range(n)]
```

## 生成速度の目安

50万件（10カラム）の場合:

| 処理 | 時間 |
|------|------|
| UUID生成（uuid.uuid4） | 約1秒 |
| numpy 数値・リスト生成 | 約0.1秒 |
| pandas DataFrame 構築 | 約0.5秒 |
| CSV 書き出し | 約2〜3秒 |
| **合計** | **約4〜5秒** |

ボトルネックは CSV 書き出し。生成自体は高速。

## 2種類のデータセット運用

ETL 課題では以下の2種類を用意する:

| 用途 | 件数 | 不正率 | 使い方 |
|------|------|--------|--------|
| テスト実行用 | 1,000件 | 高め（30%） | pytest で正確性を検証 |
| 本番想定用 | 50万件 | 低め（5%） | SLO 計測・パフォーマンス検証 |
