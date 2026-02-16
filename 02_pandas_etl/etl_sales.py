import pandas as pd
from pathlib import Path


def etl_sales(input_file) -> None:
    """
    売上データのCSVファイルを読み込み、データクレンジング・変換を行い、集計結果を出力する

    :param input_file: 売上データのCSVファイルパス
    :return : None
    """

    """
    1. **Extract（抽出）**: CSVファイルを読み込む
    """
    df = pd.read_csv(input_file)
    print(df.head())

    """
    2. **Transform（変換）**:
   - 不正データの除外（quantity が負数または数値以外、order_date が不正、product_name が空）
   - 売上金額の計算（quantity × unit_price）
   - 日付を datetime 型に変換
   """
    df_cleaned: pd.DataFrame = df.dropna(subset=["product_name"])
    df_cleaned["order_date"] = pd.to_datetime(df_cleaned["order_date"], errors="coerce")
    df_cleaned = df_cleaned.dropna(subset=["order_date"])
    df_cleaned["quantity"] = pd.to_numeric(df_cleaned["quantity"], errors="coerce")
    df_cleaned = df_cleaned.dropna(subset=["quantity"])
    df_cleaned = df_cleaned[df_cleaned["quantity"] >= 0]
    df_cleaned["sales_amount"] = df_cleaned["quantity"] * df_cleaned["unit_price"]

    df_summary: pd.DataFrame = df_cleaned.copy()
    df_summary = df_summary.groupby("product_name", as_index=False).agg(
        total_quantity=("quantity", "sum"), total_sales_amount=("sales_amount", "sum")
    )

    """
    3. **Load（出力）**:
   - クレンジング後のデータを `sales_cleaned.csv` に出力
   - 商品別売上集計を `sales_summary.csv` に出力
    """
    output_cleaned_path = Path(__file__).parent / "sales_cleaned.csv"
    df_cleaned.to_csv(output_cleaned_path, index=False)
    output_summary_path = Path(__file__).parent / "sales_summary.csv"
    df_summary.to_csv(output_summary_path, index=False)


if __name__ == "__main__":
    csv_path = Path(__file__).parent / "sales_raw.csv"
    etl_sales(csv_path)
