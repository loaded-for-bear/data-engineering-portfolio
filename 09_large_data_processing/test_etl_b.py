"""
test_etl_b.py - etl_b.py のユニットテスト

正常系 (2): test_normal_output_counts, test_revenue_calculation
異常系 (3): test_all_invalid_data, test_empty_dataframe, test_missing_required_column
境界値 (3): test_all_cancelled, test_single_category, test_all_hours_present
冪等性 (1): test_idempotency
"""
import pytest
import pandas as pd
from collections import defaultdict
from etl_b import process_chunk, accumulate, build_outputs, _region_default

COLUMNS = [
    "order_id", "customer_id", "product_id", "quantity",
    "unit_price", "order_date", "status", "category", "region",
]


def make_df(n=1, **overrides):
    """テスト用 DataFrame ファクトリ。overrides で任意のカラムを上書き可能"""
    base = {
        "order_id":    [f"ORD{i:04d}" for i in range(n)],
        "customer_id": [f"C{i:06d}" for i in range(n)],
        "product_id":  [f"P{i:06d}" for i in range(n)],
        "quantity":    [1] * n,
        "unit_price":  [100.0] * n,
        "order_date":  ["2024-01-01 10:00:00"] * n,
        "status":      ["completed"] * n,
        "category":    ["Electronics"] * n,
        "region":      ["East"] * n,
    }
    base.update(overrides)
    return pd.DataFrame(base)


def run_pipeline(df):
    """process_chunk → accumulate → build_outputs を一括実行するヘルパー"""
    seen_ids = set()
    cat_stats    = defaultdict(lambda: {"orders": 0, "qty": 0, "revenue": 0.0})
    reg_stats    = defaultdict(_region_default)
    hourly_stats = defaultdict(lambda: {"orders": 0, "revenue": 0.0})

    chunk, _, _ = process_chunk(df.copy(), seen_ids)
    accumulate(chunk, cat_stats, reg_stats, hourly_stats)
    return build_outputs(cat_stats, reg_stats, hourly_stats)


# ── 正常系 ────────────────────────────────────────────────────────────────────

def test_normal_output_counts():
    """正常系1: 出力件数が期待通りか（category=2, region=2, hourly=2）"""
    df = make_df(
        n=4,
        order_id=["A", "B", "C", "D"],
        category=["Electronics", "Electronics", "Clothing", "Clothing"],
        region=["East", "West", "East", "West"],
        order_date=[
            "2024-01-01 08:00:00",
            "2024-01-01 09:00:00",
            "2024-01-01 08:00:00",
            "2024-01-01 09:00:00",
        ],
    )
    df_cat, df_reg, df_hourly = run_pipeline(df)
    assert len(df_cat) == 2
    assert len(df_reg) == 2
    assert len(df_hourly) == 2


def test_revenue_calculation():
    """正常系2: total_revenue = sum(quantity × unit_price) と一致するか"""
    df = make_df(
        n=3,
        order_id=["A", "B", "C"],
        quantity=[2, 3, 5],
        unit_price=[100.0, 200.0, 50.0],
    )
    df_cat, _, _ = run_pipeline(df)
    expected = 2 * 100.0 + 3 * 200.0 + 5 * 50.0  # 1050.0
    assert abs(df_cat.loc[0, "total_revenue"] - expected) < 0.01


# ── 異常系 ────────────────────────────────────────────────────────────────────

def test_all_invalid_data():
    """異常系3: 不正データのみ（quantity<=0）→ 出力が空でエラーにならない"""
    df = make_df(n=3, order_id=["A", "B", "C"], quantity=[-1, -2, 0])
    df_cat, df_reg, df_hourly = run_pipeline(df)
    assert len(df_cat) == 0
    assert len(df_hourly) == 0


def test_empty_dataframe():
    """異常系4: 空DataFrame（ヘッダーのみ）→ 正常終了・全出力が0行"""
    df = pd.DataFrame(columns=COLUMNS)
    df_cat, df_reg, df_hourly = run_pipeline(df)
    assert len(df_cat) == 0
    assert len(df_reg) == 0
    assert len(df_hourly) == 0


def test_missing_required_column():
    """異常系5: 必須カラム（category）欠損 → KeyError が発生する"""
    df = make_df(n=2, order_id=["A", "B"]).drop(columns=["category"])
    with pytest.raises(KeyError):
        run_pipeline(df)


# ── 境界値 ────────────────────────────────────────────────────────────────────

def test_all_cancelled():
    """境界値6: 全件cancelled → category/hourly が空、0除算が起きない"""
    df = make_df(n=3, order_id=["A", "B", "C"], status=["cancelled"] * 3)
    df_cat, df_reg, df_hourly = run_pipeline(df)
    assert len(df_cat) == 0
    assert len(df_hourly) == 0
    assert df_reg.loc[0, "cancelled"] == 3


def test_single_category():
    """境界値7: 全件同一カテゴリ → category出力が1行、total_orders = 全件数"""
    n = 5
    df = make_df(n=n, order_id=[f"X{i}" for i in range(n)], category=["Electronics"] * n)
    df_cat, _, _ = run_pipeline(df)
    assert len(df_cat) == 1
    assert df_cat.loc[0, "total_orders"] == n


def test_all_hours_present():
    """境界値8: 全24時間帯に注文あり → hourly=24行、peak_flag の合計=1
    hour=12 のみ2件、他は1件 → max が hour=12 の1時間帯だけになることを確認
    """
    hours = list(range(24)) + [12]  # hour=12 を2件にして唯一の最大値を作る
    df = make_df(
        n=25,
        order_id=[f"H{i}" for i in range(25)],
        order_date=[f"2024-01-01 {h:02d}:00:00" for h in hours],
    )
    _, _, df_hourly = run_pipeline(df)
    assert len(df_hourly) == 24
    assert df_hourly["peak_flag"].sum() == 1


# ── 冪等性 ────────────────────────────────────────────────────────────────────

def test_idempotency():
    """冪等性9: 同じ入力で2回実行しても出力が同一"""
    df = make_df(
        n=5,
        order_id=[f"I{i}" for i in range(5)],
        category=["Electronics", "Clothing", "Electronics", "Clothing", "Food"],
        region=["East", "West", "East", "East", "West"],
    )
    df_cat1, df_reg1, df_hourly1 = run_pipeline(df)
    df_cat2, df_reg2, df_hourly2 = run_pipeline(df)

    pd.testing.assert_frame_equal(
        df_cat1.sort_values("category").reset_index(drop=True),
        df_cat2.sort_values("category").reset_index(drop=True),
    )
    pd.testing.assert_frame_equal(
        df_reg1.sort_values("region").reset_index(drop=True),
        df_reg2.sort_values("region").reset_index(drop=True),
    )
    pd.testing.assert_frame_equal(df_hourly1, df_hourly2)
