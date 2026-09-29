import tkinter as tk
from tkinter import ttk, messagebox
import database as db


class StockEntryTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=16)
        self.app = app
        self._combo_ids = []
        self._build()

    def _build(self):
        ttk.Label(self, text="Stock Entry", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        form = ttk.LabelFrame(self, text="Log Restock / Adjustment", padding=12)
        form.grid(row=1, column=0, sticky="new", padx=(0, 12))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Product").grid(row=0, column=0, sticky="w", pady=4)
        self.product_combo = ttk.Combobox(form, state="readonly", width=30)
        self.product_combo.grid(row=0, column=1, pady=4, sticky="ew")

        self.type_var = tk.StringVar(value="restock")
        type_frame = ttk.Frame(form)
        type_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Radiobutton(type_frame, text="Restock (add quantity)", variable=self.type_var, value="restock").pack(anchor="w")
        ttk.Radiobutton(type_frame, text="Adjustment (set exact count)", variable=self.type_var, value="adjustment").pack(anchor="w")

        ttk.Label(form, text="Quantity").grid(row=2, column=0, sticky="w", pady=4)
        self.qty_entry = ttk.Entry(form)
        self.qty_entry.grid(row=2, column=1, pady=4, sticky="ew")

        ttk.Label(form, text="Note").grid(row=3, column=0, sticky="w", pady=4)
        self.note_entry = ttk.Entry(form)
        self.note_entry.grid(row=3, column=1, pady=4, sticky="ew")

        ttk.Button(form, text="Submit", command=self._submit).grid(row=4, column=0, columnspan=2, pady=(12, 0))

        hist_box = ttk.LabelFrame(self, text="Recent Stock Movements", padding=10)
        hist_box.grid(row=1, column=1, sticky="nsew")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)

        columns = ("timestamp", "item_id", "product_name", "type", "quantity", "note")
        self.hist_tree = ttk.Treeview(hist_box, columns=columns, show="headings", height=16)
        for col, label in zip(columns, ["When", "Item ID", "Product", "Type", "Qty Change", "Note"]):
            self.hist_tree.heading(col, text=label)
            self.hist_tree.column(col, width=110, anchor="center")
        self.hist_tree.pack(fill="both", expand=True)

    def _submit(self):
        idx = self.product_combo.current()
        if idx < 0:
            messagebox.showwarning("No product", "Choose a product first.")
            return
        try:
            qty = int(self.qty_entry.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Quantity must be a whole number.")
            return

        product_id = self._combo_ids[idx]
        note = self.note_entry.get().strip()
        if self.type_var.get() == "restock":
            if qty <= 0:
                messagebox.showerror("Invalid input", "Restock quantity must be positive.")
                return
            db.record_restock(product_id, qty, note or "Restock")
        else:
            if qty < 0:
                messagebox.showerror("Invalid input", "Stock count cannot be negative.")
                return
            db.record_adjustment(product_id, qty, note or "Manual adjustment")

        self.qty_entry.delete(0, tk.END)
        self.note_entry.delete(0, tk.END)
        self.app.refresh_all()

    def refresh(self):
        products = db.get_products()
        self._combo_ids = [p["id"] for p in products]
        self.product_combo["values"] = [f"{p['item_id']} - {p['name']} (in stock: {p['stock_qty']})" for p in products]
        for row in self.hist_tree.get_children():
            self.hist_tree.delete(row)
        for h in db.get_stock_history(100):
            sign = "+" if h["quantity"] >= 0 else ""
            self.hist_tree.insert("", "end", values=(
                h["timestamp"], h["item_id"], h["product_name"], h["type"], f"{sign}{h['quantity']}", h["note"]))
