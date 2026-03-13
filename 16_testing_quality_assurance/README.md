# 16. テスト・品質保証

## 想定シナリオ

ECサイトの売上データを日次処理するパイプライン（#08 CDC差分更新・#09 大容量チャンク処理）は本番稼働中だが、テストコードが不十分なため以下の問題が発生している:
- コード修正のたびに手動で動作確認が必要（開発速度低下）
- 境界値・異常系が未検証のまま本番デプロイされ、過去に障害が発生した
- 新メンバーが「どこまで動作保証されているか」を把握できない

チームから「本格的なテスト基盤を整備し、次の課題から全課題に横展開できる形にしてほしい」という依頼を受けた。バリデーション・クレンジング・集計の3ステップを持つ `pipeline.py` を対象に、テストスイートを構築する。

## 制約条件

| 項目 | 値 | 根拠 |
|------|-----|------|
| 想定データ件数 | 日次 1万件（将来 10万件） | EC標準規模 |
| SLO（テスト実行時間） | 全テスト30秒以内 | CIでのフィードバックループ |
| エラーバジェット | テスト失敗率 0%（CIでブロック） | 品質ゲートとして機能させる |
| 予算制約 | 0円（ローカル・GitHub Actions 無料枠） | OSS構成 |
| チーム規模 | エンジニア 3名 | 新メンバー1名含む |

## 使用技術

| 技術 | バージョン | 用途 |
|------|-----------|------|
| Python | 3.12.3 | 実行環境 |
| pandas | 3.0.1 | データ処理 |
| pytest | 9.0.2 | テストフレームワーク |
| pytest-cov | 7.0.0 | カバレッジ計測 |
| ruff | 0.15.5 | リンター |
| GitHub Actions | - | CI/CD |

## テスト設計方針

### テストカテゴリ

| カテゴリ | 件数 | 対象関数 | 目的 |
|---------|------|---------|------|
| 正常系 | 3件 | validate / transform / run | 期待出力との一致確認（件数・値・カラム名） |
| 異常系 | 5件 | validate / clean | 不正入力のエラーハンドリング確認 |
| 境界値 | 8件（parametrize + 0件入力） | clean / run | quantity/unit_price の上下限・0件入力 |
| 冪等性 | 1件 | run | 2回実行で出力差分 = 0行 |
| モック | 2件 | transform / run | I/O不要でロジックを単独検証 |
| **合計** | **19件** | - | - |

### フィクスチャ設計（conftest.py）

- `sample_df`: 正常な1レコードのDataFrame。各テストが独立して変更できるよう `.copy()` 前提の設計
- `empty_df`: カラムのみ・0行のDataFrame。0件入力を簡単に再現するため分離
- `tmp_output_dir`: pytest組み込みの `tmp_path` をラップ。テスト後自動削除されファイルI/Oのテストが汚染しない

### カバレッジ目標

目標 80% 以上 → 実測 **96%** 達成（未カバー: `main()` の `if __name__ == '__main__':` ブロック 2行のみ）

## 設計選定理由（Why this design?）

**pytest を選択した理由**: unittest より記述が短く、フィクスチャの自動注入・parametrize・tmp_path など「テストを書く速度を上げる」機能が揃っている。新メンバーへの説明コストも低い。

**conftest.py でフィクスチャを集中管理した理由**: 各テストファイルが独立してフィクスチャを定義すると、データ仕様変更時に複数箇所を修正する必要が生じる。conftest.py に集約することでDRYを保てる。

**parametrize で境界値テストを書いた理由**: quantity（1/9999/0）と unit_price（0.01/99999.99/0）の各境界を個別の関数で書くと6関数必要。parametrize により2関数 × 3ケース = 6テストに圧縮し、境界仕様の変更も1箇所で済む。

## 代替案（Alternatives considered）

| 案 | 概要 | 却下理由 |
|----|------|---------|
| unittest | Python標準。setUpでフィクスチャ管理 | 記述量が多く、parametrize相当がddt等の外部ライブラリ依存 |
| hypothesis | プロパティベーステスト（自動値生成） | 境界値の意図が隠れる。今回は明示的な境界値テストを優先 |
| テストなし手動確認 | 現状維持 | 開発速度低下・障害再発リスクが継続するため却下 |

## トレードオフ（Trade-offs）

| 選択 | メリット | デメリット |
|------|---------|-----------|
| 関数単位テスト（validate/clean/transform を分離） | 失敗箇所が即特定できる | run() のE2Eテストと重複する部分がある |
| conftest.py の sample_df を1レコードに絞る | 各テストが最小限のデータで意図が明確 | 複数レコードの集計テストは別途E2Eテストに依存 |
| カバレッジ 80% 目標 | `main()` の手動実行ブロックは除外可能 | 96% 達成したが、68・71行目（`if __name__`）は実行不可 |

## CI設計

```
トリガー: push / pull_request（main ブランチ）
ステップ:
  1. Python 3.11 セットアップ
  2. pip install -r requirements.txt
  3. ruff check（リント: コードスタイル・未使用import検出）
  4. pytest --tb=short -v（全テスト実行）
  5. pytest --cov --cov-fail-under=80（カバレッジ 80% 未満でCI失敗）
```

カバレッジ閾値を CI に組み込むことで「テストを書かないままマージ」を構造的に防ぐ。

## 運用設計

### 障害時の再実行方法

`run()` は「読み込み → 変換 → 上書き保存」の冪等な構造。同一入力で何度実行しても出力は一致する（冪等性テスト `test_idempotency` で証明済み）。障害後は入力CSVを差し替えずに再実行するだけでよい。

### スキーマ変更時の対応

`REQUIRED_COLS` 定数でカラムリストを管理。新カラムの追加は `REQUIRED_COLS` に追記し、追加カラムを使うロジックを実装する。カラム削除は `validate()` で即座に `ValueError` を発生させて検知できる。

### ログ設計・監視閾値

- 現状: `ValueError` を例外として上位に伝播（CI/ジョブエラーとして検知）
- 将来: `logging` モジュールで WARNING / ERROR レベルの構造化ログを追加し、異常行の件数・カラム名をログに残す
- 監視閾値: テスト実行時間が30秒を超えたらCIでタイムアウトさせる（SLO: 全テスト30秒以内）

## 意思決定ログ（Decision Log）

### 判断1: モックのターゲット指定

**最初の実装**: `transform()` のテストで `pipeline.clean` をモックしようとした

```python
with patch("pipeline.clean", return_value=df):
    result = transform(df)  # transform() は clean() を呼ばないので無意味
```

**失敗**: モックが機能せず、clean() を差し替えても transform() の挙動が変わらないことに気づいた

**原因分析**: `transform()` は `clean()` を呼ばない。モックは「差し替えたい関数が実際に呼ばれる場所」を正確に指定する必要がある

**改善**: `run()` 内で呼ばれる `pd.read_csv` をモックするテストに変更

```python
with patch("pipeline.pd.read_csv", return_value=sample_df):
    run("dummy_path.csv", output_path)
```

**結果**: 実ファイルなしで `run()` の変換フロー全体をテストできるようになった

---

### 判断2: 型不正の除去方針

**最初の実装**: `quantity` に文字列が入った場合、try/except で行ごとに変換しようとした

**問題**: iterrows での行ループは遅い（将来10万件でボトルネック）

**改善**: `pd.to_numeric(errors="coerce")` で一括 NaN 変換 → `notna() & (quantity >= 1)` でフィルタ

**結果**: ベクトル演算で処理でき、かつテスト `test_clean_removes_invalid_quantity` で「文字列 quantity → 0行」を確認済み

## 将来拡張案（Scale plan）

| 想定変化 | 対応方針 |
|---------|---------|
| テストケース増加（50件以上） | `test_validation.py` / `test_transform.py` にファイル分割。conftest.py は共有 |
| データ件数 10万件 | pipeline.py にチャンク処理を追加（#09 の実装を流用）。テスト用サンプルは小さいままで良い |
| 外部DB連接 | `unittest.mock.patch` でDB接続をモックするテストを追加 |
| カバレッジ目標引き上げ | `if __name__ == '__main__':` は `pytest-subprocess` 等でCLI経由テストに対応 |

## 実行方法

```bash
# 依存関係インストール
pip install -r requirements.txt

# テスト実行（詳細ログ）
pytest test_pipeline.py -v

# カバレッジ計測
pytest test_pipeline.py --cov=pipeline --cov-report=term-missing

# リント
ruff check pipeline.py
```

## テスト

```
$ pytest test_pipeline.py -v --cov=pipeline --cov-report=term-missing
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
collected 19 items

test_pipeline.py::test_run_pipeline                      PASSED  [  5%]
test_pipeline.py::test_validate_normal                   PASSED  [ 10%]
test_pipeline.py::test_transform_sales_amount            PASSED  [ 15%]
test_pipeline.py::test_validate_missing_column           PASSED  [ 21%]
test_pipeline.py::test_validate_invalid_category         PASSED  [ 26%]
test_pipeline.py::test_validate_invalid_order_id         PASSED  [ 31%]
test_pipeline.py::test_clean_removes_duplicate_order_id  PASSED  [ 36%]
test_pipeline.py::test_clean_removes_invalid_quantity    PASSED  [ 42%]
test_pipeline.py::test_clean_quantity_bound[1-1]         PASSED  [ 47%]
test_pipeline.py::test_clean_quantity_bound[9999-1]      PASSED  [ 52%]
test_pipeline.py::test_clean_quantity_bound[0-0]         PASSED  [ 57%]
test_pipeline.py::test_clean_price_boundary[0.01-1]      PASSED  [ 63%]
test_pipeline.py::test_clean_price_boundary[99999.99-1]  PASSED  [ 68%]
test_pipeline.py::test_clean_price_boundary[0-0]         PASSED  [ 73%]
test_pipeline.py::test_clean_empty_input                 PASSED  [ 78%]
test_pipeline.py::test_run_empty_input                   PASSED  [ 84%]
test_pipeline.py::test_idempotency                       PASSED  [ 89%]
test_pipeline.py::test_transform_with_mock               PASSED  [ 94%]
test_pipeline.py::test_run_without_file                  PASSED  [100%]

Name          Stmts   Miss  Cover   Missing
-------------------------------------------
pipeline.py      46      2    96%   68, 71
-------------------------------------------
TOTAL            46      2    96%
============================== 19 passed in 0.21s ==============================
```

## 実測ログ

| 項目 | 値 |
|------|-----|
| テスト実行時間（min/avg/max） | min: 0.19s / avg: 0.20s / max: 0.21s（3回計測）|
| テスト件数（pass/fail/skip） | 19 passed / 0 failed / 0 skipped |
| カバレッジ | 96%（未カバー: pipeline.py 68, 71行目 = `if __name__ == '__main__':` ブロック） |
| 冪等性確認 | 2回実行の出力ファイル diff = 0行（test_idempotency で自動確認） |
| SLO達成 | ✅ 目標30秒以内 → 実測 max 0.23s（余裕 129倍） |

## 環境

- Python: 3.12.3
- 主要ライブラリ（バージョン付き）:
  - pandas==3.0.1
  - pytest==9.0.2
  - pytest-cov==7.0.0
  - ruff==0.15.5
