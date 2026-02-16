import pandas as pd
from pathlib import Path


def etl_pipeline(input_file: str) -> None:
    """
    アクセスログ（CSV）を読み込み、データのクレンジング・変換・集計を行い、レポート用のCSVを出力するETLパイプライン
    :param input_file: アクセスログのCSVファイル
    :return: None
    """
    # Extract（抽出）
    df = Extract(input_file)
    df = Transform(df)
    Load(df)


def Extract(input_file: str) -> pd.DataFrame:
    # Extract（抽出）
    df = pd.read_csv(input_file)
    return df


def Transform(df: pd.DataFrame) -> pd.DataFrame:
    # Transform (変換・クレンジング）
    # 1.不正データの除外: timestamp が空、または duration_sec が負の値のレコードを除外する
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df = df[(df["duration_sec"] >= 0) | (df["duration_sec"].isna())]

    # 2.欠損値の補完: duration_sec が空の場合、同じ action の中央値で補完する
    df["duration_sec"] = df["duration_sec"].fillna(
        df.groupby("action")["duration_sec"].transform("median")
    )

    # 3.エラーの除外: status_code が 400以上のレコードを除外する
    df = df[df["status_code"] < 400]

    # 4.timestampからhourカラム追加
    df["hour"] = df["timestamp"].dt.hour

    # 5.pageパスからpage_categoryカラムを追加
    df["page_category"] = (
        df["page"].str.split("/").str[1].replace("products", "product")
    )
    return df


def Load(df: pd.DataFrame) -> None:
    # Load- 2つの集計CSVを出力する
    # 1.ユーザー別サマリー
    df_user_summary = df.groupby("user_id", as_index=False).agg(
        total_views=("action", lambda x: (x == "view").sum()),
        total_duration=("duration_sec", "sum"),
        has_purchased=("action", lambda x: (x == "purchase").any()),
    )
    df_user_summary.to_csv(Path(__file__).parent / "user_summary.csv", index=False)

    # 2.時間別レポート
    df_hourly_report = df.groupby("hour", as_index=False).agg(
        access_count=("page", "count"),
        unique_users=("user_id", "nunique"),
        avg_duration=("duration_sec", lambda x: round(x.mean(), 1)),
    )

    df_hourly_report.to_csv(Path(__file__).parent / "hourly_report.csv", index=False)


if __name__ == "__main__":
    csv_path = Path(__file__).parent / "data" / "access_log.csv"
    etl_pipeline(csv_path)
