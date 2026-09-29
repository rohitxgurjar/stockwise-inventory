import tkinter as tk
from tkinter import ttk
import database as db
import datetime


class DashboardTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=16)
        self.app = app
        self._build()

    def _build(self):
        ttk.Label(self, text="Dashboard", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 12))

        self.card_labels = {}
        cards = [("total_products", "Total Products"), ("inventory_value", "Inventory Value"),
                 ("low_stock", "Low-Stock Items"), ("sales_today", "Sales Today")]
        for i, (key, label) in enumerate(cards):
            box = ttk.LabelFrame(self, text=label, padding=12)
            box.grid(row=1, column=i, padx=6, pady=6, sticky="nsew")
            self.columnconfigure(i, weight=1)
            lbl = ttk.Label(box, text="-", font=("Segoe UI", 18, "bold"))
            lbl.pack()
            self.card_labels[key] = lbl

        alert_box = ttk.LabelFrame(self, text="Low Stock Alerts", padding=10)
        alert_box.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=(16, 0))
        self.rowconfigure(2, weight=1)

        columns = ("item_id", "name", "stock_qty", "reorder_point")
        self.alert_tree = ttk.Treeview(alert_box, columns=columns, show="headings", height=8)
        for col, label in zip(columns, ["Item ID", "Product", "Current Stock", "Reorder Point"]):
            self.alert_tree.heading(col, text=label)
            self.alert_tree.column(col, anchor="center")
        self.alert_tree.pack(fill="both", expand=True)

    def refresh(self):
        products = db.get_products()
        low_stock = db.get_low_stock_products()
        self.card_labels["total_products"].config(text=str(len(products)))
        self.card_labels["inventory_value"].config(text=f"${db.get_inventory_value():,.2f}")
        self.card_labels["low_stock"].config(text=str(len(low_stock)))
        today = str(datetime.date.today())
        today_summary = db.get_sales_summary(today, today)
        self.card_labels["sales_today"].config(text=f"${today_summary['total_revenue']:,.2f}")
        for row in self.alert_tree.get_children():
            self.alert_tree.delete(row)
        for p in low_stock:
            self.alert_tree.insert("", "end", values=(p["item_id"], p["name"], p["stock_qty"], p["reorder_point"]))
