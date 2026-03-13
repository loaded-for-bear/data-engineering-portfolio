import pandas as pd
import pytest
from pipeline import run
from pathlib import Path
from pipeline import validate, clean, transform, run, REQUIRED_COLS, VALID_CATEGORIES
from unittest.mock import patch

# run()のエンドツーエンドテスト
def test_run_pipeline(tmp_output_dir):
    # 入力CSVのパス（実際のサンプルデータを利用する）
    input_path = Path(__file__).resolve().parent / "data" / "sales_raw.csv"

    # 出力先は一時フォルダ
    output_path = tmp_output_dir / "sales_summary.csv"

    # 実行
    run(input_path, output_path)

    # 出力ファイルが作られたか確認
    assert output_path.exists()

    result = pd.read_csv(output_path)
    assert len(result) == 14  # 4カテゴリ × 5日 = 14組み合わせ
    assert set(result["category"].unique()) == {"Books", "Clothing", "Electronics", "Food"}
    assert result["total_amount"].sum() == pytest.approx(345900.0)
    assert list(result.columns) == ["category", "order_date", "total_quantity", "total_amount"]

# 正常系
def test_validate_normal(sample_df):
    result = validate(sample_df)
    assert len(result) == 1
    assert result["order_id"].iloc[0] == "ORD-00000001"
    assert result["category"].iloc[0] == "Electronics"
    assert result["quantity"].iloc[0] == 2

def test_transform_sales_amount(sample_df):
    df = clean(sample_df)
    result = transform(df)
    assert result["total_amount"].iloc[0] == pytest.approx(59600.0)

# 異常系
def test_validate_missing_column(sample_df):
    # 必須カラムを一つ削除
    df = sample_df.drop(columns=["order_id"])
    with pytest.raises(ValueError, match="必須カラムが不足"):
        validate(df)

def test_validate_invalid_category(sample_df):
    df = sample_df.copy()
    df["category"] = "InvalideCat"
    with pytest.raises(ValueError):
        validate(df)

def test_validate_invalid_order_id(sample_df):
    df = sample_df.copy()
    df["order_id"] = "INVALID-123"
    with pytest.raises(ValueError):
        validate(df)

def test_clean_removes_duplicate_order_id(sample_df):
    # 同じ order_id のレコードを2行にする
    df = pd.concat([sample_df, sample_df], ignore_index=True)
    result = clean(df)
    assert len(result) == 1

def test_clean_removes_invalid_quantity(sample_df):
    df = sample_df.copy()
    df["quantity"] = "abc"  # 文字列を入れる
    result = clean(df)
    assert len(result) == 0

# 境界値
@pytest.mark.parametrize("qty,expected_len", [
    (1, 1),       # 最小値
    (9999, 1),    # 最大値
    (0, 0),       # 下限外
])
def test_clean_quantity_bound(sample_df, qty, expected_len):
    df = sample_df.copy()
    df["quantity"] = qty
    result = clean(df)
    assert len(result) == expected_len

@pytest.mark.parametrize("price,expected_len", [
    (0.01, 1),      # 最小値
    (99999.99, 1),  # 最大値
    (0, 0),         # 下限外
])
def test_clean_price_boundary(sample_df, price, expected_len):
    df = sample_df.copy()
    df["unit_price"] = price
    result = clean(df)
    assert len(result) == expected_len

def test_clean_empty_input(empty_df):
    # 0件入力 → 0件出力（エラーなし）
    result = clean(empty_df)
    assert len(result) == 0

def test_run_empty_input(empty_df, tmp_output_dir):
    # 0件入力でも出力CSVが生成され、空の集計結果になる
    output_path = tmp_output_dir / "empty_output.csv"
    with patch("pipeline.pd.read_csv", return_value=empty_df):
        run("dummy.csv", output_path)
    result = pd.read_csv(output_path)
    assert len(result) == 0

# 冪等性
def test_idempotency(tmp_output_dir):
    input_path = Path(__file__).resolve().parent / "data" / "sales_raw.csv"
    output_path = tmp_output_dir / "sales_summary.csv"

    run(input_path, output_path)
    content1 = output_path.read_text()

    run(input_path, output_path)
    content2 = output_path.read_text()

    assert content1 == content2

# モック
def test_transform_with_mock(sample_df):
    df = clean(sample_df)

    # "pipeline.clean" を呼び出したとき、dfをそのまま返す偽物に差し替える
    with patch("pipeline.clean", return_value=df):
        result = transform(df)
        assert "total_amount" in result.columns

def test_run_without_file(sample_df, tmp_output_dir):
    output_path = tmp_output_dir / "out.csv"

    # pd.read_csv をモック → 実際のファイルが不要になる
    with patch("pipeline.pd.read_csv", return_value=sample_df):
        run("dummy_path.csv", output_path)

    assert output_path.exists()
    result = pd.read_csv(output_path)
    assert "total_amount" in result.columns
