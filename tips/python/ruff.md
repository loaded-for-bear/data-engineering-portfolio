# ruff — Python リンター（コード品質チェックツール）

## 概要

Python コードの品質を自動チェックするツール。Rust 製で非常に高速。
従来の flake8, isort, pycodestyle 等を1つに統合した位置づけ。

## インストール

```bash
pip install ruff
```

## 基本コマンド

```bash
# コードをチェック
ruff check ファイル名.py

# フォルダ内を一括チェック
ruff check .

# 自動修正できるものは修正（--fix）
ruff check --fix .

# フォーマット（コード整形）
ruff format .
```

## 検出する主な問題

### PEP 8 スタイル違反

```python
# E225: 演算子の前後にスペースがない
x=1+2        # NG
x = 1 + 2    # OK

# E501: 1行が長すぎる（デフォルト88文字）
very_long_variable_name = some_function(argument1, argument2, argument3, argument4)  # NG
```

### 命名規則違反

```python
# N802: 関数名は snake_case にすべき
def Process():     # NG
def process():     # OK

# N806: 変数名は小文字にすべき
MyVar = 10         # NG
my_var = 10        # OK
```

### 未使用コード

```python
# F401: import したが使っていない
import os          # NG（どこにも os を使っていない場合）

# F841: 変数に代入したが使っていない
result = calculate()  # NG（result をどこにも使っていない場合）
```

### デバッグコードの消し忘れ

```python
# T201: print() が残っている
print("debug:", df.head())  # NG（本番コードに print は不要）

# T203: pprint() が残っている
pprint(data)                # NG
```

## 設定ファイル（pyproject.toml）

プロジェクトルートに置くと、ルールをカスタマイズできる。

```toml
# pyproject.toml
[tool.ruff]
line-length = 88           # 1行の最大文字数

[tool.ruff.lint]
select = [
    "E",    # pycodestyle エラー
    "F",    # pyflakes（未使用import等）
    "N",    # pep8-naming（命名規則）
    "T20",  # flake8-print（print検出）
]
ignore = [
    "E501",  # 行の長さは無視（場合による）
]
```

## よく使うルールコード一覧

| コード | 意味 | 例 |
|--------|------|-----|
| F401 | 未使用 import | `import os`（未使用） |
| F841 | 未使用変数 | `x = 1`（未使用） |
| E225 | 演算子前後のスペース不足 | `x=1+2` |
| E501 | 行が長すぎる | 88文字超 |
| N802 | 関数名が snake_case でない | `def Process():` |
| N806 | 変数名が小文字でない | `MyVar = 10` |
| T201 | print() の残存 | `print("debug")` |

## CI での使い方（GitHub Actions）

```yaml
# .github/workflows/lint.yml
name: Lint
on: [push, pull_request]
jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/ruff-action@v3
```

## 他のリンターとの比較

| | ruff | flake8 | pylint |
|--|------|--------|--------|
| 速度 | **非常に速い**（Rust製） | 普通 | 遅い |
| 設定 | `pyproject.toml` 1ファイル | `.flake8` + 別途 isort 等 | `.pylintrc` |
| ルール数 | 700+ | 100+（プラグイン依存） | 200+ |
| 自動修正 | `--fix` で対応 | なし | なし |
| 現在の主流 | **2024年以降のデファクト** | 従来の主流 | 厳格なプロジェクト向け |

新規プロジェクトなら ruff 一択。flake8 + isort + pycodestyle を個別に入れる必要がない。
