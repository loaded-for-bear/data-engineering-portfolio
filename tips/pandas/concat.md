# DataFrame をまとめる方法

複数の DataFrame を1つにまとめる主要な2つの手法。

## 方法1: pd.concat()（分割→加工→再結合）

複数の DataFrame を縦方向に結合する。カラムが異なる場合は NaN で埋められる。

```python
df_insert["change_type"] = "INSERT"
df_delete["change_type"] = "DELETE"
df_update["change_type"] = "UPDATE"
df_unchanged["change_type"] = "UNCHANGED"

df_result = pd.concat(
    [df_insert, df_delete, df_update, df_unchanged],
    ignore_index=True
)
```

### 注意点
- 第1引数は **リスト** で渡す（`[]` で囲む）
- `ignore_index=True` で連番インデックスを振り直す
- カラムが異なっても OK（存在しないカラムは NaN）
- 出力時に必要なカラムだけ選べばよい

```python
output_cols = ["product_id", "change_type", "changed_columns", "details"]
df_result[output_cols].fillna("-").to_csv("report.csv", index=False)
```

### 向いている場面
- グループごとに **異なる加工処理** が必要な場合
- 例: UPDATE だけ changed_columns を特定する、INSERT/DELETE は固定テキスト

## 方法2: 元の DataFrame に直接ラベル付け

分割せず、条件ごとにカラム値を設定する。

```python
df_merged["change_type"] = "UNCHANGED"  # デフォルト
df_merged.loc[df_merged["_merge"] == "right_only", "change_type"] = "INSERT"
df_merged.loc[df_merged["_merge"] == "left_only", "change_type"] = "DELETE"
df_merged.loc[update_mask, "change_type"] = "UPDATE"
```

### 向いている場面
- 全グループで **同じカラム構成** のまま進められる場合
- 追加の加工が少なく、ラベル付けだけで済む場合
- concat のオーバーヘッドを避けたい場合（大量データ時）

## 比較

| 観点 | concat | 直接ラベル付け |
|------|--------|--------------|
| 可読性 | グループごとの処理が明確 | 1つのDFで完結 |
| 柔軟性 | グループ別に異なる加工が容易 | 共通処理向き |
| パフォーマンス | concat のコピーコストあり | コピー不要で高速 |
| メモリ | 一時的に2倍使う | 追加メモリ少 |

**判断基準**: グループごとに異なる加工が必要なら concat、ラベル付けだけなら直接ラベル。
