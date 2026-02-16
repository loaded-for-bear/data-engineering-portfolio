import requests
import pandas as pd
from pathlib import Path
import time
import logging

BASE_PATH = Path(__file__).parent
BASE_URL = "http://localhost:5050"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


def fetch_api(endpoint: str, param: dict | None = None) -> dict:
    for attempt in range(3):
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", params=param)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            if attempt < 2:
                logger.error("API呼び出しに失敗しました")
                time.sleep(1)
    raise Exception(f"API call failed: {endpoint}")


def fetch_all_employees() -> pd.DataFrame:
    employees = []
    departments = []
    # 1ページ目の従業員データ並びにページデータを取得する
    endpoint = "/api/employees"
    param = {"page": 1, "per_page": 20}
    results = fetch_api(endpoint, param)

    for employee in results["data"]:
        employees.append(employee)
    pagination = results["pagination"]
    total_pages = pagination["total_pages"]

    # 2ページ以降の従業員データを取得する
    for page in range(2, total_pages + 1):
        param = {"page": page, "per_page": 20}
        results = fetch_api(endpoint, param)
        for employee in results["data"]:
            employees.append(employee)

    logger.info(f"取得件数：{len(employees)}件")

    # 部署名を付与する
    endpoint = "/api/departments"
    results = fetch_api(endpoint)
    for department in results["data"]:
        departments.append(department)

    df_employees = pd.DataFrame(employees)
    df_departments = pd.DataFrame(departments)
    df_departments = df_departments.rename(
        columns={"id": "department_id", "name": "department_name"}
    )
    return pd.merge(
        df_employees,
        df_departments,
        on="department_id",
        how="left",
    )


def transform() -> tuple[pd.DataFrame, pd.DataFrame]:
    df_all_employees = fetch_all_employees()

    # salaryがNullであるものの件数確認
    null_count = df_all_employees["salary"].isnull().sum()
    if null_count > 0:
        logger.warning(f"salaryがNullのレコード {null_count}件")

    # 2.欠損値の補完: salary が空の場合、同じ部署の平均給与で補完する
    df_all_employees["salary"] = df_all_employees["salary"].fillna(
        df_all_employees.groupby("department_id")["salary"].transform("mean")
    )

    # 　平均勤続年数を出すための処理
    df_all_employees["join_date"] = pd.to_datetime(df_all_employees["join_date"])
    df_department_report = df_all_employees.groupby(
        "department_name", as_index=False
    ).agg(
        active_count=("status", lambda x: (x == "active").sum()),
        avg_salary=("salary", "mean"),
        max_salary=("salary", "max"),
        min_salary=("salary", "min"),
        avg_years_of_service=(
            "join_date",
            lambda x: ((pd.Timestamp.now() - x).dt.days / 365.25).mean(),
        ),
    )
    df_department_report["avg_years_of_service"] = df_department_report[
        "avg_years_of_service"
    ].round(1)

    return df_all_employees, df_department_report


def load(df_all_employees: pd.DataFrame, df_department_report: pd.DataFrame) -> None:
    df_all_employees.to_csv(BASE_PATH / "employees_enriched.csv", index=False)
    df_department_report.to_csv(BASE_PATH / "department_report.csv", index=False)


def main():
    logger.info("処理を開始します")
    df_all_employees, df_department_report = transform()
    load(df_all_employees, df_department_report)
    logger.info("処理を終了します")


if __name__ == "__main__":
    main()
