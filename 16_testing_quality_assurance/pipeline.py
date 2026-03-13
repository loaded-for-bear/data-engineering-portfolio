import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REQUIRED_COLS = ["order_id", "product_id", "category", "quantity", "unit_price", "order_date", "customer_id"]
VALID_CATEGORIES = {"Electronics","Clothing","Food","Books"}

def validate(df:pd.DataFrame)->pd.DataFrame:
    # 必須カラム存在チェック
    missing = set(REQUIRED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"必須カラムが不足しています：{missing}")
    
    # categoryチェック
    invalid_rows = ~df["category"].isin(VALID_CATEGORIES)
    if invalid_rows.any():
        raise ValueError(f"不正なcategoryが含まれています:{df.loc[invalid_rows, 'category'].unique()}")
    
    #order_id 形式チェック
    invalid_order_ids = ~df["order_id"].str.match(r"^ORD-\d{8}$")
    if invalid_order_ids.any():
        raise ValueError(f"不正なorder_idが含まれています:{df.loc[invalid_order_ids, 'order_id'].unique()}")
    
    return df

def clean(df:pd.DataFrame)->pd.DataFrame:
    # 重複排除
    df = df.drop_duplicates(subset=["order_id"])
    # quantity / unit_price の不正値除去
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df = df[df["quantity"].notna() & (df["quantity"] >= 1)]
    df["quantity"] = df["quantity"].astype(int)

    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df = df[df["unit_price"].notna() & (df["unit_price"] > 0)]
    df["unit_price"] = df["unit_price"].astype(float)
    
    # order_dateの不整地除去
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    invalid_mask = df["order_date"].isna()
    df = df[~invalid_mask]

    # 欠損値
    for col in ["order_id", "product_id", "customer_id"]:
        invalid_mask = df[col].isna() | (df[col].str.strip()=="")
        df = df[~invalid_mask]

    return df

def transform(df:pd.DataFrame)->pd.DataFrame:
    df = df.copy()
    df["sales_amount"] = df["quantity"] * df["unit_price"]
    summary = df.groupby(["category", "order_date"]).agg(
        total_quantity = ("quantity", "sum"),
        total_amount = ("sales_amount", "sum")
    ).reset_index()

    return summary
 
def run(input_path, output_path):
    df = pd.read_csv(input_path)
    df = validate(df)
    df = clean(df)
    summary = transform(df)
    summary.to_csv(output_path, index=False)

def main():
    run(BASE_DIR / "data" / "sales_raw.csv", BASE_DIR / "data" / "sales_summary.csv")

if __name__ == '__main__':
    main()