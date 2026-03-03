import pandas as pd
import logging
import tracemalloc, time
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

CHUNK_SIZE = 50_000


def _region_default():
    return {"orders": 0, "revenue": 0.0, "cat_revenue": defaultdict(float), "total_all": 0, "cancelled": 0}


def process_chunk(chunk: pd.DataFrame, seen_ids: set) -> tuple[pd.DataFrame, int, int]:
    """バリデーション + 重複排除を実行して処理済みチャンクを返す"""
    # 1. バリデーション
    n_before = len(chunk)
    chunk = chunk[chunk["quantity"] > 0]
    chunk = chunk[~(chunk["unit_price"] < 0)]
    chunk["order_date"] = pd.to_datetime(chunk["order_date"], errors="coerce")
    chunk = chunk[~chunk["order_date"].isna()]
    for col in ["customer_id", "product_id"]:
        mask = chunk[col].isna() | (chunk[col].str.strip() == "")
        chunk = chunk[~mask]
    n_invalid = n_before - len(chunk)

    # 2. 重複排除（チャンク内 + チャンク間）
    n_before_dedup = len(chunk)
    chunk = chunk.drop_duplicates(subset=["order_id"], keep="first")
    chunk = chunk[~chunk["order_id"].isin(seen_ids)]
    seen_ids.update(chunk["order_id"].tolist())
    n_dup = n_before_dedup - len(chunk)

    return chunk, n_invalid, n_dup


def accumulate(chunk: pd.DataFrame, category_stats: dict, region_stats: dict, hourly_stats: dict) -> None:
    """処理済みチャンクを集計辞書に累積する"""
    if chunk.empty:
        return

    # 3. region の total_all, cancelled をカウント（全ステータス・completedフィルタ前）
    for region, cnt in chunk.groupby("region").size().items():
        region_stats[region]["total_all"] += int(cnt)
    for region, cnt in chunk[chunk["status"] == "cancelled"].groupby("region").size().items():
        region_stats[region]["cancelled"] += int(cnt)

    # 4. 派生カラム追加
    chunk = chunk.copy()
    chunk["revenue"] = chunk["quantity"] * chunk["unit_price"]
    chunk["hour"] = chunk["order_date"].dt.hour

    # 5. completed フィルタ
    chunk = chunk[chunk["status"] == "completed"]
    if chunk.empty:
        return

    # 6. category 累積
    for cat, grp in chunk.groupby("category"):
        category_stats[cat]["orders"] += len(grp)
        category_stats[cat]["qty"] += int(grp["quantity"].sum())
        category_stats[cat]["revenue"] += float(grp["revenue"].sum())

    # 7. region 累積（completed のみ）
    for region, grp in chunk.groupby("region"):
        region_stats[region]["orders"] += len(grp)
        region_stats[region]["revenue"] += float(grp["revenue"].sum())
        for cat, rev in grp.groupby("category")["revenue"].sum().items():
            region_stats[region]["cat_revenue"][cat] += float(rev)

    # 8. hourly 累積
    for hour, grp in chunk.groupby("hour"):
        hourly_stats[int(hour)]["orders"] += len(grp)
        hourly_stats[int(hour)]["revenue"] += float(grp["revenue"].sum())


def build_outputs(category_stats: dict, region_stats: dict, hourly_stats: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """集計辞書から出力用 DataFrame を生成する"""
    # category
    df_category = pd.DataFrame([
        {
            "category": cat,
            "total_orders": s["orders"],
            "total_quantity": s["qty"],
            "total_revenue": s["revenue"],
            "avg_order_value": s["revenue"] / s["orders"] if s["orders"] > 0 else 0.0,
        }
        for cat, s in category_stats.items()
    ])

    # region
    df_region = pd.DataFrame([
        {
            "region": region,
            "total_orders": s["orders"],
            "total_revenue": s["revenue"],
            "top_category": max(s["cat_revenue"], key=s["cat_revenue"].get) if s["cat_revenue"] else None,
            "total_all": s["total_all"],
            "cancelled": s["cancelled"],
            "cancelled_rate": round(s["cancelled"] / s["total_all"], 4) if s["total_all"] > 0 else 0.0,
        }
        for region, s in region_stats.items()
    ])

    # hourly
    max_orders = max((s["orders"] for s in hourly_stats.values()), default=0)
    df_hourly = pd.DataFrame([
        {
            "hour": hour,
            "total_orders": s["orders"],
            "total_revenue": s["revenue"],
            "peak_flag": 1 if s["orders"] == max_orders else 0,
        }
        for hour, s in hourly_stats.items()
    ])
    if not df_hourly.empty:
        df_hourly = df_hourly.sort_values("hour").reset_index(drop=True)

    return df_category, df_region, df_hourly


def load(df_category: pd.DataFrame, df_region: pd.DataFrame, df_hourly: pd.DataFrame) -> None:
    df_category.to_csv(BASE_DIR / "summary_by_category.csv", index=False)
    df_region.to_csv(BASE_DIR / "summary_by_region.csv", index=False)
    df_hourly.to_csv(BASE_DIR / "summary_hourly.csv", index=False)


def main():
    tracemalloc.start()
    start = time.perf_counter()

    file_path = BASE_DIR / "data" / "orders_large.csv"

    seen_ids: set = set()
    category_stats: dict = defaultdict(lambda: {"orders": 0, "qty": 0, "revenue": 0.0})
    region_stats: dict = defaultdict(_region_default)
    hourly_stats: dict = defaultdict(lambda: {"orders": 0, "revenue": 0.0})

    n_input = 0
    n_invalid_total = 0
    n_dup_total = 0

    for chunk in pd.read_csv(file_path, chunksize=CHUNK_SIZE):
        n_input += len(chunk)
        chunk, n_invalid, n_dup = process_chunk(chunk, seen_ids)
        n_invalid_total += n_invalid
        n_dup_total += n_dup
        accumulate(chunk, category_stats, region_stats, hourly_stats)

    df_category, df_region, df_hourly = build_outputs(category_stats, region_stats, hourly_stats)
    load(df_category, df_region, df_hourly)

    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    logger.info(f"処理時間: {elapsed:.2f}s")
    logger.info(f"ピークメモリ: {peak / 1024 / 1024:.1f} MB")
    logger.info(f"入力件数: {n_input}")
    logger.info(f"不正データ除外: {n_invalid_total}件")
    logger.info(f"重複排除: {n_dup_total}件")
    logger.info(f"出力件数: category={len(df_category)} / region={len(df_region)} / hourly={len(df_hourly)}")


if __name__ == "__main__":
    main()
