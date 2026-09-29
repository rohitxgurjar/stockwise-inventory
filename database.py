import sqlite3
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "inventory.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            unit_price REAL NOT NULL,
            stock_qty INTEGER NOT NULL DEFAULT 0,
            reorder_point INTEGER NOT NULL DEFAULT 5
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            note TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            subtotal REAL NOT NULL,
            discount_pct REAL NOT NULL DEFAULT 0,
            tax_pct REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY(sale_id) REFERENCES sales(id)
        )
    """)
    conn.commit()
    conn.close()


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def add_product(item_id, name, category, unit_price, stock_qty, reorder_point):
    conn = get_connection()
    conn.execute(
        "INSERT INTO products (item_id, name, category, unit_price, stock_qty, reorder_point) VALUES (?, ?, ?, ?, ?, ?)",
        (item_id, name, category, unit_price, stock_qty, reorder_point),
    )
    conn.commit()
    conn.close()


def get_products():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    conn.close()
    return rows


def get_product(product_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    conn.close()
    return row


def get_low_stock_products():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products WHERE stock_qty <= reorder_point").fetchall()
    conn.close()
    return rows


def update_product(product_id, item_id, name, category, unit_price, reorder_point):
    conn = get_connection()
    conn.execute(
        "UPDATE products SET item_id=?, name=?, category=?, unit_price=?, reorder_point=? WHERE id=?",
        (item_id, name, category, unit_price, reorder_point, product_id),
    )
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_connection()
    conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


def record_restock(product_id, quantity, note=""):
    conn = get_connection()
    conn.execute("UPDATE products SET stock_qty = stock_qty + ? WHERE id=?", (quantity, product_id))
    conn.execute(
        "INSERT INTO stock_transactions (product_id, type, quantity, note, timestamp) VALUES (?, 'restock', ?, ?, ?)",
        (product_id, quantity, note, now()),
    )
    conn.commit()
    conn.close()


def record_adjustment(product_id, new_quantity, note="Manual adjustment"):
    conn = get_connection()
    current = conn.execute("SELECT stock_qty FROM products WHERE id=?", (product_id,)).fetchone()["stock_qty"]
    delta = new_quantity - current
    conn.execute("UPDATE products SET stock_qty = ? WHERE id=?", (new_quantity, product_id))
    conn.execute(
        "INSERT INTO stock_transactions (product_id, type, quantity, note, timestamp) VALUES (?, 'adjustment', ?, ?, ?)",
        (product_id, delta, note, now()),
    )
    conn.commit()
    conn.close()


def get_stock_history(limit=100):
    conn = get_connection()
    rows = conn.execute("""
        SELECT st.*, p.name as product_name, p.item_id as item_id
        FROM stock_transactions st JOIN products p ON st.product_id = p.id
        ORDER BY st.timestamp DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def record_sale(cart_items, discount_pct=0.0, tax_pct=0.0):
    conn = get_connection()
    cur = conn.cursor()
    for item in cart_items:
        row = cur.execute("SELECT stock_qty, name FROM products WHERE id=?", (item["product_id"],)).fetchone()
        if row is None:
            conn.close()
            raise ValueError(f"Product id {item['product_id']} not found.")
        if row["stock_qty"] < item["quantity"]:
            conn.close()
            raise ValueError(f"Not enough stock for '{row['name']}' (have {row['stock_qty']}, need {item['quantity']}).")

    subtotal = sum(i["quantity"] * i["unit_price"] for i in cart_items)
    discount_amt = subtotal * (discount_pct / 100)
    taxable = subtotal - discount_amt
    tax_amt = taxable * (tax_pct / 100)
    total = taxable + tax_amt

    cur.execute(
        "INSERT INTO sales (timestamp, subtotal, discount_pct, tax_pct, total) VALUES (?, ?, ?, ?, ?)",
        (now(), subtotal, discount_pct, tax_pct, total),
    )
    sale_id = cur.lastrowid

    for item in cart_items:
        line_total = item["quantity"] * item["unit_price"]
        cur.execute(
            "INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, line_total) VALUES (?, ?, ?, ?, ?, ?)",
            (sale_id, item["product_id"], item["name"], item["quantity"], item["unit_price"], line_total),
        )
        cur.execute("UPDATE products SET stock_qty = stock_qty - ? WHERE id=?", (item["quantity"], item["product_id"]))

    conn.commit()
    conn.close()
    return {"sale_id": sale_id, "subtotal": subtotal, "discount_amt": discount_amt,
            "tax_amt": tax_amt, "total": total, "timestamp": now()}


def get_sale_items(sale_id):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM sale_items WHERE sale_id=?", (sale_id,)).fetchall()
    conn.close()
    return rows


def get_inventory_value():
    conn = get_connection()
    row = conn.execute("SELECT SUM(stock_qty * unit_price) as total FROM products").fetchone()
    conn.close()
    return row["total"] or 0.0


def get_sales_summary(start_date=None, end_date=None):
    conn = get_connection()
    query = "SELECT * FROM sales"
    params = []
    if start_date and end_date:
        query += " WHERE date(timestamp) BETWEEN ? AND ?"
        params = [start_date, end_date]
    rows = conn.execute(query, params).fetchall()
    conn.close()
    total = sum(r["total"] for r in rows)
    return {"count": len(rows), "total_revenue": total, "sales": rows}


def get_best_sellers(limit=10):
    conn = get_connection()
    rows = conn.execute("""
        SELECT product_name, SUM(quantity) as total_qty, SUM(line_total) as total_revenue
        FROM sale_items GROUP BY product_id ORDER BY total_qty DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def get_recent_sales(limit=30):
    conn = get_connection()
    rows = conn.execute("SELECT * FROM sales ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return rows
