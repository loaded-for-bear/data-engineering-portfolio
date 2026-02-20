# pd.to_datetime() の errors パラメータ

## 概要

`pd.to_datetime()` は文字列や数値を datetime 型に変換する関数。
`errors` パラメータで、**変換できない値（不正な日付文字列など）の扱い**を制御できる。

---

## errors の挙動比較

```python
import pandas as pd

s = pd.Series(["2026-01-01", "INVALID", "2026-03-15"])

# errors='raise'（デフォルト）
pd.to_datetime(s)
# → ValueError: Unknown string format: INVALID  ← 処理が止まる

# errors='coerce'
pd.to_datetime(s, errors="coerce")
# → DatetimeIndex(['2026-01-01', 'NaT', '2026-03-15'])  ← NaT に変換

# errors='ignore'
pd.to_datetime(s, errors="ignore")
# → Index(['2026-01-01', 'INVALID', '2026-03-15'])  ← 元の文字列のまま（非推奨）
```

| errors= | 変換不可の値 | 用途 |
|---------|------------|------|
| `'raise'`（デフォルト） | ValueError で処理停止 | 入力が完全に信頼できる場合 |
| `'coerce'` | `NaT` に変換 | **ETLのバリデーション（推奨）** |
| `'ignore'` | 元の値のまま残す | ほぼ使わない（型が混在して危険） |

---

## ETL バリデーションでの使い方（推奨パターン）

```python
# 1. coerce で変換 → 不正値は NaT に
df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

# 2. NaT を不正行としてマスク
invalid_mask = df["order_date"].isna()
n_invalid = invalid_mask.sum()

# 3. ログ出力（理由別件数）
if n_invalid > 0:
    logging.warning(f"order_date 不正: {n_invalid}件を除外")

# 4. 除外
df = df[~invalid_mask]
```

---

## NaT とは

`NaT`（Not a Time）は pandas の日時型における欠損値。
数値の `NaN` に相当する。

```python
import pandas as pd

nat = pd.NaT
print(pd.isna(nat))   # True
print(nat is pd.NaT)  # True
```

- `isna()` / `isnull()` で検出できる
- datetime 列の `isna()` は NaT も検出する（NaN と同じ扱い）

---

## 注意: errors='ignore' を使ってはいけない理由

```python
s = pd.Series(["2026-01-01", "INVALID"])
result = pd.to_datetime(s, errors="ignore")
# → dtype: object（文字列のまま）

# 後続処理で dt アクセサが使えない
result.dt.hour  # → AttributeError または意図しない動作
```

`errors='ignore'` は型が混在した列を返すため、後続の `.dt.hour` などの操作が壊れる。**使用禁止**。
