import tkinter as tk
from tkinter import ttk, messagebox
import database as db


class ProductsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=16)
        self.app = app
        self.selected_product_id = None
        self._row_to_id = {}
        self._build()

    def _build(self):
        ttk.Label(self, text="Product Catalog", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        table_frame = ttk.Frame(self)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)

        columns = ("item_id", "name", "category", "unit_price", "stock_qty", "reorder_point")
        headers = ["Item ID", "Name", "Category", "Unit Price", "Stock", "Reorder At"]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        for col, label in zip(columns, headers):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=110, anchor="center")
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        form = ttk.LabelFrame(self, text="Add / Edit Product", padding=12)
        form.grid(row=1, column=1, sticky="nsew")
        form.columnconfigure(1, weight=1)

        self.fields = {}
        for i, (key, label) in enumerate([("item_id", "Item ID"), ("name", "Name"), ("category", "Category"),
                                            ("unit_price", "Unit Price"), ("stock_qty", "Initial Stock (add only)"),
                                            ("reorder_point", "Reorder Point")]):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", pady=4)
            entry = ttk.Entry(form)
            entry.grid(row=i, column=1, pady=4, sticky="ew")
            self.fields[key] = entry

        btns = ttk.Frame(form)
        btns.grid(row=6, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btns, text="Add New", command=self._add).pack(side="left", padx=4)
        ttk.Button(btns, text="Update", command=self._update).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete", command=self._delete).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear", command=self._clear).pack(side="left", padx=4)

    def _on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        row_id = selected[0]
        self.selected_product_id = self._row_to_id.get(row_id)
        values = self.tree.item(row_id)["values"]
        for key, val in zip(["item_id", "name", "category", "unit_price", "stock_qty", "reorder_point"], values):
            self.fields[key].delete(0, tk.END)
            self.fields[key].insert(0, val)

    def _clear(self):
        for entry in self.fields.values():
            entry.delete(0, tk.END)
        self.selected_product_id = None

    def _add(self):
        try:
            item_id = self.fields["item_id"].get().strip()
            name = self.fields["name"].get().strip()
            if not item_id or not name:
                raise ValueError("Item ID and Name are required.")
            category = self.fields["category"].get().strip()
            unit_price = float(self.fields["unit_price"].get())
            stock_qty = int(self.fields["stock_qty"].get() or 0)
            reorder_point = int(self.fields["reorder_point"].get() or 5)
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e) if "required" in str(e) else "Price/Stock/Reorder must be numbers.")
            return
        try:
            db.add_product(item_id, name, category, unit_price, stock_qty, reorder_point)
        except Exception as e:
            messagebox.showerror("Could not add", f"Item ID may already exist.\n{e}")
            return
        self._clear()
        self.app.refresh_all()

    def _update(self):
        if not self.selected_product_id:
            messagebox.showwarning("No selection", "Select a product first.")
            return
        try:
            item_id = self.fields["item_id"].get().strip()
            name = self.fields["name"].get().strip()
            category = self.fields["category"].get().strip()
            unit_price = float(self.fields["unit_price"].get())
            reorder_point = int(self.fields["reorder_point"].get() or 5)
        except ValueError:
            messagebox.showerror("Invalid input", "Price/Reorder must be numbers.")
            return
        db.update_product(self.selected_product_id, item_id, name, category, unit_price, reorder_point)
        self._clear()
        self.app.refresh_all()

    def _delete(self):
        if not self.selected_product_id:
            messagebox.showwarning("No selection", "Select a product first.")
            return
        if messagebox.askyesno("Confirm", "Delete this product?"):
            db.delete_product(self.selected_product_id)
            self._clear()
            self.app.refresh_all()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        self._row_to_id = {}
        for p in db.get_products():
            row_id = self.tree.insert("", "end", values=(
                p["item_id"], p["name"], p["category"], f"{p['unit_price']:.2f}", p["stock_qty"], p["reorder_point"]))
            self._row_to_id[row_id] = p["id"]
