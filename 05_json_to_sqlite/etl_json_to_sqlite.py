import sqlite3
import json
from pathlib import Path

BASE_PATH = Path(__file__).parent


def extract(file_path: str) -> list:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def transform(data: list) -> list:
    customers = {}
    orders = []
    order_items = []

    for order in data["orders"]:
        # Transform customer data
        customers[order["customer"]["id"]] = {
            "customer_id": order["customer"]["id"],
            "name": order["customer"]["name"],
            "email": order["customer"]["email"],
        }
        # Transform order data
        orders.append(
            {
                "order_id": order["order_id"],
                "customer_id": order["customer"]["id"],
                "order_date": order["order_date"],
                "status": order["status"],
            }
        )
        # Transform order items data
        for item in order["items"]:
            order_items.append(
                {
                    "order_id": order["order_id"],
                    "product_id": item["product_id"],
                    "product_name": item["name"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                }
            )
    return customers, orders, order_items


def Load(customers: dict, orders: list, order_items: list) -> None:
    conn = sqlite3.connect(BASE_PATH / "ecommerce.db")
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS order_items")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS customers")

    # Create tables if they don't exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT,
            order_date TEXT,
            status TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            product_id TEXT,
            product_name TEXT,
            quantity INTEGER,
            price INTEGER
        )
    """
    )

    # Insert customers data
    for customer_id, customer in customers.items():
        cursor.execute(
            "INSERT OR REPLACE INTO customers (customer_id, name, email) VALUES (?, ?, ?)",
            (customer["customer_id"], customer["name"], customer["email"]),
        )

    # Insert orders data
    for order in orders:
        cursor.execute(
            "INSERT OR REPLACE INTO orders (order_id, customer_id, order_date, status) VALUES (?, ?, ?, ?)",
            (
                order["order_id"],
                order["customer_id"],
                order["order_date"],
                order["status"],
            ),
        )

    # Insert order items data
    for item in order_items:
        cursor.execute(
            "INSERT OR REPLACE INTO order_items (order_id, product_id, product_name, quantity, price) VALUES (?, ?, ?, ?, ?)",
            (
                item["order_id"],
                item["product_id"],
                item["product_name"],
                item["quantity"],
                item["price"],
            ),
        )

    conn.commit()
    conn.close()


def Verify():
    conn = sqlite3.connect(BASE_PATH / "ecommerce.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 
            c.customer_id,
            c.name,
            -- oi.quantity,
            -- oi.price,
            SUM(oi.quantity * oi.price) AS total_amount
        FROM order_items oi
        LEFT JOIN orders o ON oi.order_id = o.order_id
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.status = 'completed'
        GROUP BY c.customer_id, c.name
    """
    )
    verify1 = cursor.fetchall()
    print(verify1)

    cursor.execute(
        """
        SELECT 
            oi.product_id,
            oi.product_name,
            SUM(oi.quantity) AS total_quantity
        FROM order_items oi
        LEFT JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status = 'completed'
        GROUP BY oi.product_id, oi.product_name
        ORDER BY total_quantity DESC
    """
    )
    verify2 = cursor.fetchall()
    print(verify2)

    conn.close()


def main():
    data = extract(BASE_PATH / "data" / "orders.json")
    customers, orders, order_items = transform(data)
    Load(customers, orders, order_items)
    Verify()


if __name__ == "__main__":
    main()
