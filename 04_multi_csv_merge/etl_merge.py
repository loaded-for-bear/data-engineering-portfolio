import pandas as pd
from pathlib import Path

BASE_PATH = Path(__file__).parent


def extract(
    dept_path: Path, emp_path: Path, att_path: Path
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """CSVファイルからデータを抽出してDataFrameとして返す。"""
    dept_df = pd.read_csv(dept_path)
    emp_df = pd.read_csv(emp_path)
    att_df = pd.read_csv(att_path)
    return dept_df, emp_df, att_df


def transform(
    dept_df: pd.DataFrame, emp_df: pd.DataFrame, att_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """1.不整合検出"""
    issues = []
    # invalid_dept: 社員マスタに存在しないdept_idを持つ社員
    invalid_dept = emp_df[~emp_df["dept_id"].isin(dept_df["dept_id"])]
    for _, row in invalid_dept.iterrows():
        issues.append(
            {
                "issue_type": "invalid_dept",
                "record_id": row["emp_id"],
                "detail": "id=" + str(row["dept_id"]) + "は部門マスタに存在しない",
            }
        )
    # invalid_emp: 勤怠記録に存在しない emp_id のレコード（社員マスタにないもの）
    invalid_emp = att_df[~att_df["emp_id"].isin(emp_df["emp_id"])]
    for _, row in invalid_emp.iterrows():
        issues.append(
            {
                "issue_type": "invalid_emp",
                "record_id": row["emp_id"],
                "detail": "社員マスタに存在しない社員の勤怠レコード",
            }
        )
    # missing_clock_in: clock_in が空（欠損）の勤怠レコード
    missing_clock_in = att_df[att_df["clock_in"].isna()]
    for _, row in missing_clock_in.iterrows():
        issues.append(
            {
                "issue_type": "missing_clock_in",
                "record_id": row["emp_id"],
                "detail": "date=" + str(row["date"]) + "の clock_in が欠損",
            }
        )

    """ 2.データ結合 """
    merge_df = pd.merge(emp_df, dept_df, on="dept_id", how="left")

    """ 3.勤務時間の計算 """
    att_df = att_df.dropna(subset="clock_in")
    att_df = att_df[att_df["emp_id"].isin(emp_df["emp_id"])]
    att_df["hours"] = round(
        (
            pd.to_datetime(att_df["clock_out"], format="%H:%M")
            - pd.to_datetime(att_df["clock_in"], format="%H:%M")
        ).dt.total_seconds()
        / 3600,
        1,
    )
    att_hour_df = att_df.groupby("emp_id").agg(hours=("hours", "sum"))

    """ 4.残業カウント"""
    att_count_df = (
        att_df[att_df["status"] == "overtime"]
        .groupby("emp_id")
        .agg(overtime_count=("status", "size"))
    )

    """ 集計まとめ """
    merge_df = pd.merge(merge_df, att_hour_df, on="emp_id", how="left")
    merge_df = pd.merge(merge_df, att_count_df, on="emp_id", how="left")

    """ dept_summary """
    dept_summary = merge_df.groupby(["dept_id", "dept_name"]).agg(
        employee_count=("emp_id", "count"),
        total_work_hours=("hours", "sum"),
        overtime_count=("overtime_count", "count"),
    )

    """employee_work"""
    employee_work = merge_df.groupby(["emp_id", "name", "dept_name"]).agg(
        total_hours=("hours", "sum"), overtime_count=("overtime_count", "sum")
    )

    return pd.DataFrame(issues), dept_summary, employee_work


def load(
    issues: pd.DataFrame, dept_summary: pd.DataFrame, employee_work: pd.DataFrame
) -> None:
    issues.to_csv(BASE_PATH / "data_issues.csv", index=False)
    dept_summary.to_csv(BASE_PATH / "dept_summary.csv", index=True)
    employee_work.to_csv(BASE_PATH / "employee_work.csv", index=True)


def main():
    dept_df, emp_df, att_df = extract(
        BASE_PATH / "departments.csv",
        BASE_PATH / "employees.csv",
        BASE_PATH / "attendance.csv",
    )
    issues, dept_summary, employee_work = transform(dept_df, emp_df, att_df)
    load(issues, dept_summary, employee_work)


if __name__ == "__main__":
    main()
