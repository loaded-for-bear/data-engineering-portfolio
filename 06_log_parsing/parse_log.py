import pandas as pd
import re
from pathlib import Path

BASE_PATH = Path(__file__).parent
# 正規表現パターン（定数）
LOG_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    r" \[(?P<level>\w+)\]"
    r" server=(?P<server>\w+)"
    r" endpoint=(?P<endpoint>\S+)"
    r" method=(?P<method>\w+)"
    r" status=(?P<status>\d+)"
    r" response_time=(?P<response_time>\d+)ms"
)

# def server_metrics(df:pd.DataFrame) -> pd.DataFrame:


def extract(file_path: str) -> list:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    return lines


def server_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df_server_metrics = df.copy()
    df_server_metrics = df_server_metrics.groupby("server").agg(
        total_requests=("status", "count"),
        error_count=("status", lambda x: (x >= 400).sum()),
        error_rate=("status", lambda x: round((x >= 400).sum() / len(x) * 100, 1)),
        avg_response_time=("response_time", lambda x: round(x.mean(), 1)),
    )
    return df_server_metrics


def endpoint_report(df: pd.DataFrame) -> pd.DataFrame:
    df_endpoint_report = df.copy()
    df_endpoint_report = (
        df_endpoint_report.groupby("endpoint")
        .agg(
            total_request=("status", "count"),
            error_count=("status", lambda x: (x >= 400).sum()),
            avg_response_time=("response_time", lambda x: round(x.mean(), 1)),
        )
        .reset_index()
        .sort_values("error_count", ascending=False)
    )
    return df_endpoint_report


def anomaly_minutes(df: pd.DataFrame) -> pd.DataFrame:
    df_anomaly_minutes = df.copy()
    df_anomaly_minutes = df_anomaly_minutes.groupby("minute").agg(
        request_count=("status", "count"),
        error_count=("status", lambda x: (x >= 400).sum()),
        error_rate=("status", lambda x: round((x >= 400).sum() / len(x) * 100, 1)),
    )
    df_anomaly_minutes = df_anomaly_minutes[df_anomaly_minutes["error_rate"] > 50]
    return df_anomaly_minutes


def transform(lines: list) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    records = []
    skip_count = 0

    # 各行を正規表現でパースし、フィールドを抽出する
    for line in lines:
        m = LOG_PATTERN.match(line)
        if m:
            records.append(m.groupdict())
        else:
            skip_count += 1

    print(f"スキップした不正行: {skip_count}件")
    print(f"パース成功: {len(records)}件")
    df = pd.DataFrame(records)

    # データ型調整
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["status"] = df["status"].astype(int)
    df["response_time"] = df["response_time"].astype(int)
    df["minute"] = df["timestamp"].dt.strftime("%H:%M")

    df_server_metrics = server_metrics(df)
    df_endpoint_report = endpoint_report(df)
    df_anomaly_minutes = anomaly_minutes(df)

    return df_server_metrics, df_endpoint_report, df_anomaly_minutes


def load(
    server_metrics: pd.DataFrame,
    endpoint_report: pd.DataFrame,
    anomaly_minutes: pd.DataFrame,
) -> None:
    server_metrics.to_csv(BASE_PATH / "server_metrics.csv")
    endpoint_report.to_csv(BASE_PATH / "endpoint_report.csv")
    anomaly_minutes.to_csv(BASE_PATH / "anomaly_minutes.csv")


def main():
    lines = extract(BASE_PATH / "data" / "app_server.log")
    server_metrics, endpoint_report, anomaly_minutes = transform(lines)
    load(server_metrics, endpoint_report, anomaly_minutes)


if __name__ == "__main__":
    main()
