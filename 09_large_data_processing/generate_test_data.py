import uuid
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def generate(
    output_count: int, invalid_rate: float, all_invalid_rate: float, dup_rate: float
) -> pd.DataFrame:
    """データ生成"""
    # 注文日時作成
    base_date = pd.Timestamp("2026-02-20")
    random_seconds = np.random.randint(0, 86400, size=output_count)
    order_dates = (base_date + pd.to_timedelta(random_seconds, unit="s")).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )

    # ベースのデータ作成
    df = pd.DataFrame(
        {
            "order_id": [str(uuid.uuid4()) for _ in range(output_count)],
            "customer_id": [
                f"C{i:06d}" for i in np.random.randint(1, 999999, size=output_count)
            ],
            "order_date": order_dates,
            "product_id": [
                f"P{i:05d}" for i in np.random.randint(1, 999999, size=output_count)
            ],
            "category": np.random.choice(
                ["electronics", "clothing", "food", "books", "home"], size=output_count
            ),
            "quantity": np.random.randint(1, 101, size=output_count),
            "unit_price": np.round(
                np.random.uniform(1.0, 99999.99, size=output_count), 2
            ),
            "region": np.random.choice(
                ["tokyo", "osaka", "nagoya", "fukuoka", "sapporo"], size=output_count
            ),
            "payment_method": np.random.choice(
                ["credit", "debit", "cash", "points"], size=output_count
            ),
            "status": np.random.choice(
                ["completed", "cancelled", "returned"], size=output_count
            ),
        }
    )

    """ 不正データ混入 """
    # 個別不正
    output_invalid = int(output_count * invalid_rate)  # 本番想定15%
    output_each = output_invalid // 4
    invalid_idx = np.random.choice(output_count, size=output_invalid, replace=False)
    df.loc[invalid_idx[:output_each], "quantity"] = -1
    df.loc[invalid_idx[output_each : 2 * output_each], "unit_price"] = -99.9
    df.loc[invalid_idx[2 * output_each : 3 * output_each], "order_date"] = "INVALID"

    ## customer_id, product_id対応
    third_idx = invalid_idx[3 * output_each : 4 * output_each]
    mid = len(third_idx) // 2
    df.loc[third_idx[:mid], "customer_id"] = ""
    df.loc[third_idx[mid:], "product_id"] = ""

    # 全不正
    output_all_invalid = int(output_count * all_invalid_rate)
    all_invalid_idx = np.random.choice(
        np.setdiff1d(np.arange(output_count), invalid_idx),
        size=output_all_invalid,
        replace=False,
    )
    df.loc[all_invalid_idx, "quantity"] = -1
    df.loc[all_invalid_idx, "unit_price"] = -99.9
    df.loc[all_invalid_idx, "order_date"] = "INVALID"
    df.loc[all_invalid_idx, "customer_id"] = ""
    df.loc[all_invalid_idx, "product_id"] = ""

    # 重複行の追加
    output_dup = int(output_count * dup_rate)
    dup_idx = np.random.choice(output_count, size=output_dup, replace=False)
    df_with_dups = pd.concat([df, df.iloc[dup_idx]], ignore_index=True)

    return df_with_dups


def load(df_small: pd.DataFrame, df_large: pd.DataFrame) -> None:
    out_dir = BASE_DIR / "data"
    out_dir.mkdir(exist_ok=True)
    df_small.to_csv(out_dir / "orders_small.csv", index=False)
    df_large.to_csv(out_dir / "orders_large.csv", index=False)
    print(f"small: {len(df_small):,}件 → orders_small.csv")
    print(f"large: {len(df_large):,}件 → orders_large.csv")


def main():
    df_small = generate(
        output_count=1000, invalid_rate=0.15, all_invalid_rate=0.05, dup_rate=0.10
    )
    df_large = generate(
        output_count=500000, invalid_rate=0.02, all_invalid_rate=0.01, dup_rate=0.02
    )
    load(df_small, df_large)


if __name__ == "__main__":
    main()
