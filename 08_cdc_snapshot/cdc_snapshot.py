import pandas as pd
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent.parent


def load_snapshot(prev_path: str, curr_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    df_prev = pd.read_csv(prev_path)
    df_curr = pd.read_csv(curr_path)
    return df_prev, df_curr


def get_change_columns(row, compare_cols):
    return [col for col in compare_cols if row[f"{col}_changed"]]


def get_detail(row, compare_cols):
    changes = []
    numeric_cols = {"price", "stock"}
    for col in compare_cols:
        if row[f"{col}_changed"]:
            old = row[f"{col}_old"]
            new = row[f"{col}_new"]
            if col in numeric_cols:
                old, new = int(old), int(new)
            changes.append(f"{col}:{old}→{new}")
    return ", ".join(changes)


def diff_detection(df_prev: pd.DataFrame, df_curr: pd.DataFrame) -> pd.DataFrame:
    df_merged = pd.merge(
        df_prev,
        df_curr,
        on="product_id",
        how="outer",
        suffixes=("_old", "_new"),
        indicator=True,
    )
    df_insert = df_merged[df_merged["_merge"] == "right_only"].copy()
    df_delete = df_merged[df_merged["_merge"] == "left_only"].copy()
    df_both = df_merged[df_merged["_merge"] == "both"].copy()

    # merge後、_oldと_newを比較する
    compare_cols = [
        "product_name",
        "category",
        "price",
        "stock",
        "status",
        "updated_at",
    ]
    for col in compare_cols:
        df_both[f"{col}_changed"] = df_both[f"{col}_old"] != df_both[f"{col}_new"]

    changed_cols = [f"{col}_changed" for col in compare_cols]
    any_changed = df_both[changed_cols].any(axis=1)

    df_update = df_both[any_changed].copy()
    df_unchanged = df_both[~any_changed].copy()

    # 差分レポート作成
    df_insert["change_type"] = "INSERT"
    df_delete["change_type"] = "DELETE"
    df_update["change_type"] = "UPDATE"
    df_unchanged["change_type"] = "UNCHANGED"

    df_update["changed_columns"] = df_update.apply(
        lambda row: ",".join(get_change_columns(row, compare_cols)), axis=1
    )

    df_insert["details"] = "New record"
    df_delete["details"] = "Deleted record"
    df_update["details"] = df_update.apply(
        lambda row: get_detail(row, compare_cols), axis=1
    )

    df_result = pd.concat(
        [df_insert, df_delete, df_update, df_unchanged], ignore_index=True
    )

    # 　集計
    print("=== CDC Summary ===")
    print(f"前回件数: {len(df_prev)}")
    print(f"今回件数: {len(df_curr)}")
    print(f"INSERT: {len(df_insert)}")
    print(f"UPDATE: {len(df_update)}")
    print(f"DELETE: {len(df_delete)}")
    print(f"UNCHANGED: {len(df_unchanged)}")

    df_result["category"] = df_result["category_new"].fillna(df_result["category_old"])
    print("=== カテゴリ別 変更件数 ===")
    print(pd.crosstab(df_result["category"], df_result["change_type"]))

    all_changed = df_update["changed_columns"].str.split(",").explode()
    print("=== 変更カラム集計 ===")
    print(all_changed.value_counts().to_string())

    return df_result


def load(df_result: pd.DataFrame) -> None:
    df_result[["product_id", "change_type", "changed_columns", "details"]].fillna(
        "-"
    ).to_csv(BASE_DIR / "my_code" / "cdc_report.csv", index=False)


def main():
    start = time.time()
    prev_path = BASE_DIR / "data" / "snapshot_2026-02-14.csv"
    curr_path = BASE_DIR / "data" / "snapshot_2026-02-16.csv"
    df_prev, df_curr = load_snapshot(prev_path, curr_path)
    df_result = diff_detection(df_prev, df_curr)
    load(df_result)
    elapsed = time.time() - start
    print(f"=== CDC処理完了 (処理時間: {elapsed:.2f}秒) ===")


if __name__ == "__main__":
    main()
