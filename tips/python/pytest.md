# pytest — Python テストフレームワーク

## 概要

Python のテストを自動実行するフレームワーク。
`test_` で始まるファイル・関数を自動検出し、`assert` 文で期待値と実際の値を比較する。

## インストール

```bash
pip install pytest
```

## 基本構文

```python
# test_example.py

def add(a, b):
    return a + b

# テスト関数: test_ で始める（必須）
def test_add_normal():
    assert add(1, 2) == 3       # True → PASSED

def test_add_negative():
    assert add(-1, 1) == 0      # True → PASSED
```

```bash
$ pytest test_example.py -v
test_example.py::test_add_normal    PASSED
test_example.py::test_add_negative  PASSED
2 passed in 0.01s
```

## 命名規則（pytest が自動検出する条件）

| 対象 | ルール |
|------|--------|
| ファイル名 | `test_*.py` または `*_test.py` |
| 関数名 | `test_` で始まる |
| クラス名 | `Test` で始まる（クラスを使う場合） |

## assert の書き方

```python
# 値の比較
assert result == 42
assert result != 0

# 型チェック
assert isinstance(result, list)

# 含まれるか
assert "error" in message
assert "tokyo" in df["region"].values

# 範囲チェック
assert 0 < result < 100

# 件数チェック
assert len(df) == 5
```

### 失敗時のメッセージ

```python
# カスタムメッセージ付き（失敗時に表示される）
assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
```

## よく使うパターン

### 1. ファイル出力のテスト

```python
import pandas as pd

def test_output_file():
    # 処理実行
    process("input.csv", "output/")

    # 出力ファイルを読んで検証
    df = pd.read_csv("output/result.csv")
    assert len(df) == 5
    assert list(df.columns) == ["category", "total_orders", "total_revenue"]
```

### 2. 数値の近似比較（浮動小数点）

```python
# float は == で比較すると誤差で失敗する場合がある
assert result == pytest.approx(3.14, abs=0.01)

# pandas DataFrame の比較
pd.testing.assert_frame_equal(df1, df2)
```

### 3. 例外が発生することのテスト

```python
import pytest

def test_invalid_input():
    with pytest.raises(ValueError):
        process("invalid_file.csv")

# エラーメッセージも検証
def test_missing_column():
    with pytest.raises(KeyError, match="order_id"):
        process("missing_column.csv")
```

#### `match` パラメータ — エラーメッセージの内容を検証する

`match` を指定すると、例外の種類に加えてメッセージの内容も検証できる。

```python
# match なし → ValueError が出れば何でも PASS
with pytest.raises(ValueError):
    validate(df)

# match あり → ValueError かつメッセージに "必須カラムが不足" が含まれないと FAIL
with pytest.raises(ValueError, match="必須カラムが不足"):
    validate(df)
```

**対応する raise 側のコード例:**

```python
# pipeline.py
raise ValueError(f"必須カラムが不足しています：{missing}")
#                    ↑ "必須カラムが不足" が含まれる → match に一致 → PASS
```

**ポイント:**
- `match` は**正規表現**として扱われる（部分一致でOK）
- `"必須カラムが不足"` と書けば `"必須カラムが不足しています：{'order_id'}"` にも一致する
- `match` を使うと「正しい理由でエラーが出ているか」まで検証できる（より厳密なテスト）

### 4. 冪等性テスト

```python
def test_idempotency():
    process("input.csv", "output/")
    result1 = pd.read_csv("output/result.csv")

    process("input.csv", "output/")
    result2 = pd.read_csv("output/result.csv")

    pd.testing.assert_frame_equal(result1, result2)
```

### 5. 一時ディレクトリの利用（tmp_path）

```python
def test_with_temp_dir(tmp_path):
    """pytest が自動で一時ディレクトリを作成・削除"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    process("input.csv", str(output_dir))

    result = pd.read_csv(output_dir / "result.csv")
    assert len(result) > 0
```

## フィクスチャ（fixture）— テストデータ・前処理の共通化

### 基本構文

```python
# conftest.py
import pytest
import pandas as pd

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "order_id": ["ORD-00000001"],
        "quantity": [2],
        "unit_price": [29800.0],
    })
```

```python
# test_pipeline.py（import 不要）
def test_validate_normal(sample_df):   # 引数名 = フィクスチャ名
    result = validate(sample_df)
    assert len(result) == 1
```

### 自動注入の仕組み

pytest はテスト関数の**引数名**を見て、`conftest.py` に定義された同名フィクスチャを自動で探し、値を渡す（= 依存性注入）。**`import` は不要**。

```
conftest.py               test_pipeline.py
────────────────────      ──────────────────────────────────
@pytest.fixture           def test_validate_normal(sample_df):
def sample_df():      →       ↑ 引数名を見て自動注入
    return pd.DataFrame(...)
```

### 探索順序

pytest は以下の順で `conftest.py` を探す（見つかった時点で使用）:

```
my_code/
├── conftest.py       ← ① 同ディレクトリを最初に探す
├── test_pipeline.py
└── ...
(親ディレクトリ → さらに上、と階層を上って探す)
```

### フィクスチャがフィクスチャを使う

フィクスチャ同士を組み合わせることもできる。`tmp_path` は pytest 組み込みのフィクスチャで、テスト用の一時ディレクトリを自動生成・自動削除する:

```python
@pytest.fixture
def tmp_output_dir(tmp_path):   # tmp_path は pytest 組み込み
    return tmp_path
```

```python
def test_idempotency(tmp_output_dir):   # conftest 経由で tmp_path を受け取る
    output_path = tmp_output_dir / "result.csv"
    ...
```

### 通常の Python との比較

| | 通常の Python | pytest フィクスチャ |
|--|---|---|
| 使い方 | `import` が必要 | `import` 不要（conftest.py を自動読み込み）|
| インスタンス化 | 呼び出し側が行う | pytest が自動で渡す |
| 引数の意味 | 任意 | 引数名 = フィクスチャ名（命名が重要）|

### conftest.py の配置ルール

- **同ディレクトリの `conftest.py`** にテスト共通のフィクスチャを定義する（`import` 不要）
- 複数テストファイルで共有するフィクスチャは必ず `conftest.py` に置く
- テストファイル固有のフィクスチャは `test_*.py` 内に直接書いてもよい

---

## テストの実行方法

```bash
# 基本実行
pytest test_example.py

# 詳細表示（-v: 各テスト名を表示）
pytest test_example.py -v

# 特定のテストだけ実行（-k: キーワードフィルタ）
pytest test_example.py -k "test_normal"

# 最初の失敗で停止（-x）
pytest test_example.py -x

# print() の出力を表示（-s）
pytest test_example.py -s

# 組み合わせ
pytest test_example.py -v -s -x
```

## テストの構成パターン（ETL向け）

```python
# test_etl.py
import pandas as pd
import pytest

# --- 正常系 ---

def test_normal_output_counts():
    """出力CSVの件数が期待通り"""
    process("data/test_1000.csv", "output/")
    cat = pd.read_csv("output/summary_by_category.csv")
    assert len(cat) == 5

def test_revenue_calculation():
    """revenue = quantity × unit_price の合計が一致"""
    process("data/test_1000.csv", "output/")
    cat = pd.read_csv("output/summary_by_category.csv")
    assert cat["total_revenue"].sum() > 0

# --- 異常系 ---

def test_empty_input():
    """空ファイルでエラーにならない"""
    process("data/test_empty.csv", "output/")
    cat = pd.read_csv("output/summary_by_category.csv")
    assert len(cat) == 0

def test_missing_column():
    """必須カラム欠損で適切なエラー"""
    with pytest.raises(KeyError):
        process("data/test_missing_col.csv", "output/")

# --- 境界値 ---

def test_all_cancelled():
    """全件cancelledでcompleted集計が0件"""
    process("data/test_all_cancelled.csv", "output/")
    cat = pd.read_csv("output/summary_by_category.csv")
    assert len(cat) == 0

# --- 冪等性 ---

def test_idempotency():
    """2回実行で同一結果"""
    process("data/test_1000.csv", "output/")
    r1 = pd.read_csv("output/summary_by_category.csv")
    process("data/test_1000.csv", "output/")
    r2 = pd.read_csv("output/summary_by_category.csv")
    pd.testing.assert_frame_equal(r1, r2)
```

## READMEへの貼り方

テスト実行結果を **そのままコピペ** する:

```bash
$ pytest test_large_data.py -v
test_large_data.py::test_normal_output_counts  PASSED
test_large_data.py::test_empty_input           PASSED
test_large_data.py::test_all_cancelled         PASSED
test_large_data.py::test_idempotency           PASSED
4 passed in 0.45s
```

## unittest との比較

| | pytest | unittest |
|--|--------|---------|
| テスト記法 | `assert` 文（シンプル） | `self.assertEqual()` 等（冗長） |
| クラス必須？ | 不要（関数だけでOK） | 必須（`TestCase` 継承） |
| 自動検出 | `test_` で始まるものを自動発見 | 同様 |
| プラグイン | 豊富（カバレッジ、並列実行等） | 少ない |
| 業界標準 | **現在の主流** | Python 標準だが古い |

pytest を使えば十分。unittest を選ぶ理由はほぼない。
