import csv
import io
from pathlib import Path

def analyze_logs(csv_text: str) -> dict:
    reader = csv.DictReader(io.StringIO(csv_text))
    stats = {}
    slow_requests = []
    for row in reader:
        ep = row["endpoint"]
        if ep not in stats:
            stats[ep] = {"count": 0, "total_time": 0, "error_count": 0}
        # エンドポイント別の集計: 各endpointごとに、リクエスト数・平均レスポンスタイム(ms)・エラー率(status_code >= 400の割合)を算出
        stats[ep]["count"] += 1
        stats[ep]["total_time"] += int(row["response_time_ms"])
        if int(row["status_code"]) >= 400:
            stats[ep]["error_count"] += 1

        if int(row["response_time_ms"]) > 1000:
            slow_requests.append(
                {
                    "timestamp": row["timestamp"],
                    "user_id": row["user_id"],
                    "endpoint": row["endpoint"],
                    "response_time_ms": int(row["response_time_ms"]),
                }
            )

    endpoint_stats = {}
    for ep, data in stats.items():
        endpoint_stats[ep] = {
            "count": data["count"],
            "avg_response_time": round(data["total_time"] / data["count"], 2),
            "error_rate": (
                round(data["error_count"] / data["count"], 2)
                if data["count"] > 0
                else 0
            ),
        }

    return {"endpoint_stats": endpoint_stats, "slow_requests": slow_requests}


if __name__ == "__main__":
    csv_path = Path(__file__).parent / "sample.csv"
    with open(csv_path, "r") as f:
        csv_text = f.read()
    print(analyze_logs(csv_text))
