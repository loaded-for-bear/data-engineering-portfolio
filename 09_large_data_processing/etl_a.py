import pandas as pd
import logging
import tracemalloc, time
from pathlib import Path

BASE_DIR = Path(__file__).parent
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(levelname)s] %(message)s"  
)
logger = logging.getLogger(__name__)

def extract(file_path:str)->pd.DataFrame:
  df = pd.read_csv(file_path)
  return df

def transform(df:pd.DataFrame)-> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
  #1. バリデーション（不正行を除外）
  n_before_validation = len(df)
  df = df[df["quantity"] > 0]
  df = df[~(df["unit_price"] < 0)]
  df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
  invalid_mask = df["order_date"].isna()
  df = df[~invalid_mask]
  for col in ["customer_id", "product_id"]:
    invalid_mask = df[col].isna() | (df[col].str.strip()=="")
    df = df[~invalid_mask]
  n_invalid = n_before_validation - len(df)

  #2.重複削除
  n_before_dedup = len(df)
  df = df.drop_duplicates(subset=["order_id"], keep="first")
  n_dup = n_before_dedup - len(df)

  #3.集計
  ## 集計前に必要な数値とカラムを追加する
  region_counts = df.groupby("region").agg (
    total_all = ("order_id", "count"),
    cancelled = ("status", lambda x: (x == "cancelled").sum())
  )
  df["revenue"] = df["quantity"] * df["unit_price"]
  df["hour"] = df["order_date"].dt.hour

  df = df[df["status"] == "completed"]

  ## category
  df_category = df.groupby("category").agg (
    total_orders = ("order_id", "count"),
    total_quantity = ("quantity", "sum"),
    total_revenue = ("revenue", "sum"),
  )
  
  df_category["avg_order_value"] = df_category["total_revenue"] / df_category["total_orders"]

  ## region
  df_region = df.groupby("region").agg (
    total_orders = ("order_id", "count"),
    total_revenue = ("revenue", "sum")
  )
  cat_rev = df.groupby(["region", "category"])["revenue"].sum().unstack()
  df_region["top_category"] = cat_rev.idxmax(axis=1)
  df_region["total_all"] = region_counts["total_all"] 
  df_region["cancelled"] = region_counts["cancelled"]
  df_region["cancelled_rate"] = (
    df_region["cancelled"] / df_region["total_all"]
  ).round(4)

  ## hourly
  df_hourly = df.groupby("hour").agg(
    total_orders = ("order_id", "count"),
    total_revenue = ("revenue", "sum"),
  )
  max_order = df_hourly["total_orders"].max()
  df_hourly["peak_flag"] = df_hourly["total_orders"].apply(lambda x : 1 if x == max_order else 0)

  stats = {"n_invalid": n_invalid, "n_dup": n_dup}
  return df_category.reset_index(), df_region.reset_index(), df_hourly.reset_index(), stats

def load(df_category:pd.DataFrame, df_region:pd.DataFrame, df_hourly:pd.DataFrame) -> None:
  df_category.to_csv(BASE_DIR / "summary_by_category.csv", index=False)
  df_region.to_csv(BASE_DIR / "summary_by_region.csv", index=False)
  df_hourly.to_csv(BASE_DIR / "summary_hourly.csv", index=False)

def main():
  tracemalloc.start()
  start = time.perf_counter()

  file_name = "orders_large.csv"
  file_path = BASE_DIR/ "data" / file_name
  df = extract(file_path)
  n_input = len(df)
  df_category, df_region, df_hourly, stats = transform(df)
  load(df_category, df_region, df_hourly)

  elapsed = time.perf_counter() - start
  _, peak = tracemalloc.get_traced_memory()
  tracemalloc.stop()

  logger.info(f"処理時間: {elapsed:.2f}s")
  logger.info(f"ピークメモリ: {peak / 1024 / 1024:.1f} MB")
  logger.info(f"入力件数: {n_input}")
  logger.info(f"不正データ除外: {stats['n_invalid']}件")
  logger.info(f"重複排除: {stats['n_dup']}件")
  logger.info(f"出力件数: category={len(df_category)} / region={len(df_region)} / hourly={len(df_hourly)}")

if __name__ == '__main__':
  main()