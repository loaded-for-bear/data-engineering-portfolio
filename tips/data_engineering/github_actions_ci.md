# GitHub Actions CI — 継続的インテグレーションの基礎

## CI とは

**Continuous Integration（継続的インテグレーション）**の略。
「コードをプッシュするたびに、自動でテスト・チェックを実行する仕組み」。

### CI がない世界（問題）

```
開発者: コード修正 → git push
  → 手動でpytest実行（忘れることがある）
  → 手動でlint実行（忘れることがある）
  → バグが本番に入ってから発覚
```

### CI がある世界（解決）

```
開発者: コード修正 → git push
  → GitHub Actions が自動起動
  → lint → テスト → カバレッジ を自動実行
  → ✅ 全通過 → マージOK
  → ❌ 失敗  → 通知・マージブロック
```

チェックが**自動・強制**になるため、「確認を忘れたまま本番反映」を構造的に防げる。

---

## ci.yml の基本構造

GitHub Actions の設定ファイルは `.github/workflows/ci.yml` に置く。

```yaml
name: CI                          # ワークフローの名前（GitHub上に表示される）

on:                               # いつ動かすか
  push:
    branches: [main]              # main への push 時
  pull_request:
    branches: [main]              # main への PR 時

jobs:
  test:                           # ジョブ名（任意）
    runs-on: ubuntu-latest        # どの環境で動かすか

    steps:
      - uses: actions/checkout@v4             # コードを取得
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"             # Pythonバージョン固定

      - name: Install dependencies
        run: pip install -r requirements.txt  # 依存関係インストール

      - name: Lint
        run: ruff check pipeline.py           # リント

      - name: Test
        run: pytest test_pipeline.py -v       # テスト

      - name: Coverage
        run: |
          pytest test_pipeline.py \
            --cov=pipeline \
            --cov-report=term-missing \
            --cov-fail-under=80               # 80%未満でCI失敗
```

---

## 各ステップの意図

| ステップ | コマンド | 目的 |
|---------|---------|------|
| checkout | `actions/checkout@v4` | サーバー上にコードを取得（必須） |
| Python セットアップ | `actions/setup-python@v5` | バージョン固定で再現性を保証 |
| pip install | `pip install -r requirements.txt` | `requirements.txt` が「再現性の鍵」 |
| ruff check | `ruff check *.py` | 未使用import・スタイル問題を検出 |
| pytest | `pytest -v` | テスト失敗でCIブロック |
| coverage | `--cov-fail-under=80` | カバレッジ80%未満でCIブロック |

**速いチェック（lint）を先に置くのが定石**。lint で失敗したら後続ステップは実行されず、時間を節約できる。

---

## runs-on の意味

```yaml
runs-on: ubuntu-latest
```

GitHub が管理する**クリーンなUbuntuサーバーを毎回新規で用意**して実行する。
「自分のPCでは動いた（でもサーバーでは失敗した）」問題を防ぐ。

---

## `--cov-fail-under=80` の重要性

カバレッジの閾値を CI に組み込む意義:

```yaml
# カバレッジ80%未満 → CI が ❌ → マージできない
--cov-fail-under=80
```

これにより「テストを書かないままマージ」を**構造的に防げる**。
閾値は段階的に引き上げていくのが現実的（60% → 80% → 90%）。

---

## トリガーの使い分け

```yaml
on:
  push:
    branches: [main]        # main に直接 push したとき
  pull_request:
    branches: [main]        # main への PR を作ったとき・更新したとき
```

| トリガー | いつ発火 | 用途 |
|---------|---------|------|
| `push` | git push 直後 | 一人開発・直接コミット |
| `pull_request` | PR 作成・更新時 | チーム開発・マージ前チェック |

チーム開発では `pull_request` トリガーが特に重要。PR の段階でバグを検出できる。

---

## ディレクトリ構成パターン

### 課題単位の場合（ポートフォリオ）

```
data-engineering-portfolio/
├── .github/
│   └── workflows/
│       └── ci.yml          ← リポジトリルートに1つ
├── 09_large_data_processing/
│   ├── pipeline.py
│   └── test_pipeline.py
└── 16_testing_quality_assurance/
    ├── pipeline.py
    └── test_pipeline.py
```

ci.yml 内でパスを指定して複数課題をまとめてテストする:

```yaml
- name: Test
  run: pytest 16_testing_quality_assurance/test_pipeline.py -v
```

### プロジェクト単位の場合（本番）

```
my-project/
├── .github/workflows/ci.yml
├── src/
│   └── pipeline.py
└── tests/
    └── test_pipeline.py
```

---

## よくあるエラーと対処

| エラー | 原因 | 対処 |
|-------|------|------|
| `ModuleNotFoundError` | requirements.txt にライブラリが漏れている | requirements.txt に追記 |
| `ruff: command not found` | ruff が requirements.txt にない | `ruff` を requirements.txt に追加 |
| カバレッジ計測でパスエラー | `--cov=` のパス指定が間違い | `--cov=モジュール名`（拡張子なし）を確認 |
| `No tests ran` | pytest のパス指定ミス | `pytest tests/` のようにディレクトリ指定を確認 |

---

## requirements.txt が「再現性の鍵」である理由

```
開発PC:   Python 3.12 + pandas 3.0.1 + pytest 9.0.2 → テスト PASS
CI サーバー: Python 3.11 + pandas 2.x + pytest 8.x → テスト FAIL ← バージョン差で壊れる
```

`requirements.txt` にバージョンを固定することで CI でも同じ環境を再現できる:

```
pandas==3.0.1
pytest==9.0.2
pytest-cov==7.0.0
ruff==0.15.5
```
