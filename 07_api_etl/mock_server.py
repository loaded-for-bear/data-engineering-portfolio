"""
従業員管理API モックサーバー
お題 #7: API連携・Web取得 用
"""

import random
import json
from datetime import date, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- データ生成 ---
DEPARTMENTS = [
    {"id": 101, "name": "Engineering"},
    {"id": 102, "name": "Sales"},
    {"id": 103, "name": "Marketing"},
    {"id": 104, "name": "HR"},
    {"id": 105, "name": "Finance"},
]

random.seed(42)

LAST_NAMES = ["田中", "佐藤", "鈴木", "高橋", "伊藤", "渡辺", "山本", "中村", "小林", "加藤",
              "吉田", "山田", "松本", "井上", "木村", "林", "斎藤", "清水", "山口", "森"]
FIRST_NAMES = ["太郎", "花子", "一郎", "美咲", "健太", "由美", "大輔", "あかり", "翔太", "さくら",
               "雄介", "千尋", "拓也", "麻衣", "直樹", "綾", "裕太", "陽子", "和也", "真由美"]

def generate_employees(n=53):
    employees = []
    for i in range(1, n + 1):
        dept = random.choice(DEPARTMENTS)
        base_salary = {
            101: 6000000, 102: 5000000, 103: 4800000,
            104: 4500000, 105: 5500000
        }[dept["id"]]

        salary = base_salary + random.randint(-1000000, 1500000)
        # 一部の従業員の salary を null にする (約8%)
        if random.random() < 0.08:
            salary = None

        join_year = random.randint(2010, 2024)
        join_month = random.choice([4, 7, 10, 1])
        join_date = f"{join_year}-{join_month:02d}-01"

        status = "active" if random.random() < 0.88 else "inactive"

        employees.append({
            "id": i,
            "name": f"{random.choice(LAST_NAMES)}{random.choice(FIRST_NAMES)}",
            "department_id": dept["id"],
            "salary": salary,
            "join_date": join_date,
            "status": status,
        })
    return employees

EMPLOYEES = generate_employees()

# --- エラーシミュレーション ---
ERROR_RATE = 0.08  # 8%の確率で500エラー

def maybe_error():
    """まれに500エラーを返す"""
    if random.random() < ERROR_RATE:
        return True
    return False

# --- ルーティング ---

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/departments")
def departments():
    if maybe_error():
        return jsonify({"error": "Internal Server Error"}), 500
    return jsonify({"data": DEPARTMENTS})


@app.route("/api/employees")
def employees():
    if maybe_error():
        return jsonify({"error": "Internal Server Error"}), 500

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    per_page = min(per_page, 20)  # 最大20件

    total_count = len(EMPLOYEES)
    total_pages = (total_count + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    page_data = EMPLOYEES[start:end]

    return jsonify({
        "data": page_data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": total_pages,
        }
    })


if __name__ == "__main__":
    print("=== 従業員管理API モックサーバー ===")
    print(f"従業員数: {len(EMPLOYEES)}")
    print(f"部署数: {len(DEPARTMENTS)}")
    print("http://localhost:5050 で起動します")
    app.run(host="0.0.0.0", port=5050, debug=False)
