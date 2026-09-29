import tkinter as tk
from tkinter import ttk
import datetime
import database as db


class ReportsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=16)
        self.app = app
        self.range_var = tk.StringVar(value="all")
        self._build()

    def _build(self):
        ttk.Label(self, text="Sales Reports", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))
        for label, val in [("All time", "all"), ("Today", "today"), ("Last 7 days", "7d"), ("Last 30 days", "30d")]:
            ttk.Radiobutton(filter_frame, text=label, variable=self.range_var, value=val,
                             command=self.refresh).pack(side="left", padx=4)

        self.summary_labels = {}
        summary_frame = ttk.Frame(self)
        summary_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        for i, (key, label) in enumerate([("count", "Sales Count"), ("revenue", "Total Revenue"),
                                            ("inv_value", "Current Inventory Value")]):
            box = ttk.LabelFrame(summary_frame, text=label, padding=10)
            box.grid(row=0, column=i, padx=6, sticky="nsew")
            summary_frame.columnconfigure(i, weight=1)
            lbl = ttk.Label(box, text="-", font=("Segoe UI", 14, "bold"))
            lbl.pack()
            self.summary_labels[key] = lbl

        best_frame = ttk.LabelFrame(self, text="Best-Selling Items", padding=10)
        best_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=(0, 6))
        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)

        columns = ("product_name", "total_qty", "total_revenue")
        self.best_tree = ttk.Treeview(best_frame, columns=columns, show="headings", height=12)
        for col, label in zip(columns, ["Product", "Units Sold", "Revenue"]):
            self.best_tree.heading(col, text=label)
            self.best_tree.column(col, width=130, anchor="center")
        self.best_tree.pack(fill="both", expand=True)

        recent_frame = ttk.LabelFrame(self, text="Recent Sales", padding=10)
        recent_frame.grid(row=3, column=2, sticky="nsew")
        columns2 = ("id", "timestamp", "total")
        self.recent_tree = ttk.Treeview(recent_frame, columns=columns2, show="headings", height=12)
        for col, label in zip(columns2, ["Sale #", "When", "Total"]):
            self.recent_tree.heading(col, text=label)
            self.recent_tree.column(col, width=90, anchor="center")
        self.recent_tree.pack(fill="both", expand=True)

    def refresh(self):
        start = end = None
        today = datetime.date.today()
        rng = self.range_var.get()
        if rng == "today":
            start = end = str(today)
        elif rng == "7d":
            start, end = str(today - datetime.timedelta(days=7)), str(today)
        elif rng == "30d":
            start, end = str(today - datetime.timedelta(days=30)), str(today)

        summary = db.get_sales_summary(start, end)
        self.summary_labels["count"].config(text=str(summary["count"]))
        self.summary_labels["revenue"].config(text=f"${summary['total_revenue']:,.2f}")
        self.summary_labels["inv_value"].config(text=f"${db.get_inventory_value():,.2f}")

        for row in self.best_tree.get_children():
            self.best_tree.delete(row)
        for b in db.get_best_sellers(10):
            self.best_tree.insert("", "end", values=(b["product_name"], b["total_qty"], f"${b['total_revenue']:.2f}"))

        for row in self.recent_tree.get_children():
            self.recent_tree.delete(row)
        for s in db.get_recent_sales(30):
            self.recent_tree.insert("", "end", values=(s["id"], s["timestamp"], f"${s['total']:.2f}"))
