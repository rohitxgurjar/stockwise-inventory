import tkinter as tk
from tkinter import ttk, messagebox
import os
import database as db


class CheckoutTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=16)
        self.app = app
        self.cart = []
        self._products = []
        self._build()

    def _build(self):
        ttk.Label(self, text="Checkout", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        add_frame = ttk.LabelFrame(self, text="Add Item", padding=10)
        add_frame.grid(row=1, column=0, sticky="new", padx=(0, 12))
        ttk.Label(add_frame, text="Product").grid(row=0, column=0, sticky="w", pady=4)
        self.product_combo = ttk.Combobox(add_frame, state="readonly", width=28)
        self.product_combo.grid(row=0, column=1, pady=4)
        ttk.Label(add_frame, text="Quantity").grid(row=1, column=0, sticky="w", pady=4)
        self.qty_entry = ttk.Entry(add_frame)
        self.qty_entry.insert(0, "1")
        self.qty_entry.grid(row=1, column=1, pady=4, sticky="ew")
        ttk.Button(add_frame, text="Add to Cart", command=self._add_to_cart).grid(row=2, column=0, columnspan=2, pady=(8, 0))

        cart_frame = ttk.LabelFrame(self, text="Cart", padding=10)
        cart_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        columns = ("name", "quantity", "unit_price", "line_total")
        self.cart_tree = ttk.Treeview(cart_frame, columns=columns, show="headings", height=10)
        for col, label in zip(columns, ["Product", "Qty", "Unit Price", "Line Total"]):
            self.cart_tree.heading(col, text=label)
            self.cart_tree.column(col, width=140, anchor="center")
        self.cart_tree.pack(fill="both", expand=True, side="left")
        ttk.Button(cart_frame, text="Remove Selected", command=self._remove_selected).pack(side="bottom", pady=6)

        totals_frame = ttk.LabelFrame(self, text="Totals", padding=10)
        totals_frame.grid(row=1, column=1, sticky="new")
        totals_frame.columnconfigure(1, weight=1)

        ttk.Label(totals_frame, text="Discount %").grid(row=0, column=0, sticky="w", pady=4)
        self.discount_entry = ttk.Entry(totals_frame)
        self.discount_entry.insert(0, "0")
        self.discount_entry.grid(row=0, column=1, pady=4, sticky="ew")

        ttk.Label(totals_frame, text="Tax %").grid(row=1, column=0, sticky="w", pady=4)
        self.tax_entry = ttk.Entry(totals_frame)
        self.tax_entry.insert(0, "0")
        self.tax_entry.grid(row=1, column=1, pady=4, sticky="ew")

        self.subtotal_lbl = ttk.Label(totals_frame, text="Subtotal: $0.00")
        self.subtotal_lbl.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self.total_lbl = ttk.Label(totals_frame, text="Total: $0.00", font=("Segoe UI", 13, "bold"))
        self.total_lbl.grid(row=3, column=0, columnspan=2, sticky="w")

        ttk.Button(totals_frame, text="Recalculate", command=self._recalc).grid(row=4, column=0, columnspan=2, pady=(10, 4))
        ttk.Button(totals_frame, text="Complete Sale & Print Receipt", command=self._checkout).grid(
            row=5, column=0, columnspan=2, pady=4)

    def _add_to_cart(self):
        idx = self.product_combo.current()
        if idx < 0:
            messagebox.showwarning("No product", "Choose a product first.")
            return
        try:
            qty = int(self.qty_entry.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Quantity must be a positive whole number.")
            return

        product = self._products[idx]
        if qty > product["stock_qty"]:
            messagebox.showerror("Not enough stock", f"Only {product['stock_qty']} in stock for {product['name']}.")
            return

        for item in self.cart:
            if item["product_id"] == product["id"]:
                item["quantity"] += qty
                break
        else:
            self.cart.append({"product_id": product["id"], "name": product["name"],
                               "unit_price": product["unit_price"], "quantity": qty})
        self._render_cart()

    def _remove_selected(self):
        selected = self.cart_tree.selection()
        if not selected:
            return
        idx = self.cart_tree.index(selected[0])
        del self.cart[idx]
        self._render_cart()

    def _render_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        for item in self.cart:
            line_total = item["quantity"] * item["unit_price"]
            self.cart_tree.insert("", "end", values=(item["name"], item["quantity"],
                                                       f"{item['unit_price']:.2f}", f"{line_total:.2f}"))
        self._recalc()

    def _recalc(self):
        subtotal = sum(i["quantity"] * i["unit_price"] for i in self.cart)
        try:
            discount_pct = float(self.discount_entry.get() or 0)
            tax_pct = float(self.tax_entry.get() or 0)
        except ValueError:
            discount_pct = tax_pct = 0
        total = (subtotal - subtotal * discount_pct / 100) * (1 + tax_pct / 100)
        self.subtotal_lbl.config(text=f"Subtotal: ${subtotal:,.2f}")
        self.total_lbl.config(text=f"Total: ${total:,.2f}")

    def _checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty cart", "Add at least one item first.")
            return
        try:
            discount_pct = float(self.discount_entry.get() or 0)
            tax_pct = float(self.tax_entry.get() or 0)
        except ValueError:
            messagebox.showerror("Invalid input", "Discount and Tax must be numbers.")
            return

        try:
            result = db.record_sale(self.cart, discount_pct, tax_pct)
        except ValueError as e:
            messagebox.showerror("Checkout failed", str(e))
            return

        receipt_path = self._generate_receipt(result)
        self.cart = []
        self._render_cart()
        self.app.refresh_all()
        messagebox.showinfo("Sale complete", f"Sale #{result['sale_id']} recorded.\nReceipt saved to:\n{receipt_path}")

    def _generate_receipt(self, result):
        receipts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "receipts")
        os.makedirs(receipts_dir, exist_ok=True)
        path = os.path.join(receipts_dir, f"receipt_{result['sale_id']}.txt")

        items = db.get_sale_items(result["sale_id"])
        lines = ["=" * 40, "        SHOP RECEIPT", "=" * 40,
                 f"Sale ID: {result['sale_id']}", f"Date:    {result['timestamp']}", "-" * 40]
        for it in items:import tkinter as tk
from tkinter import ttk, messagebox
import os
import database as db


class CheckoutTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=16)
        self.app = app
        self.cart = []
        self._products = []
        self._build()

    def _build(self):
        ttk.Label(self, text="Checkout", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        add_frame = ttk.LabelFrame(self, text="Add Item", padding=10)
        add_frame.grid(row=1, column=0, sticky="new", padx=(0, 12))
        ttk.Label(add_frame, text="Product").grid(row=0, column=0, sticky="w", pady=4)
        self.product_combo = ttk.Combobox(add_frame, state="readonly", width=28)
        self.product_combo.grid(row=0, column=1, pady=4)
        ttk.Label(add_frame, text="Quantity").grid(row=1, column=0, sticky="w", pady=4)
        self.qty_entry = ttk.Entry(add_frame)
        self.qty_entry.insert(0, "1")
        self.qty_entry.grid(row=1, column=1, pady=4, sticky="ew")
        ttk.Button(add_frame, text="Add to Cart", command=self._add_to_cart).grid(row=2, column=0, columnspan=2, pady=(8, 0))

        cart_frame = ttk.LabelFrame(self, text="Cart", padding=10)
        cart_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        columns = ("name", "quantity", "unit_price", "line_total")
        self.cart_tree = ttk.Treeview(cart_frame, columns=columns, show="headings", height=10)
        for col, label in zip(columns, ["Product", "Qty", "Unit Price", "Line Total"]):
            self.cart_tree.heading(col, text=label)
            self.cart_tree.column(col, width=140, anchor="center")
        self.cart_tree.pack(fill="both", expand=True, side="left")
        ttk.Button(cart_frame, text="Remove Selected", command=self._remove_selected).pack(side="bottom", pady=6)

        totals_frame = ttk.LabelFrame(self, text="Totals", padding=10)
        totals_frame.grid(row=1, column=1, sticky="new")
        totals_frame.columnconfigure(1, weight=1)

        ttk.Label(totals_frame, text="Discount %").grid(row=0, column=0, sticky="w", pady=4)
        self.discount_entry = ttk.Entry(totals_frame)
        self.discount_entry.insert(0, "0")
        self.discount_entry.grid(row=0, column=1, pady=4, sticky="ew")

        ttk.Label(totals_frame, text="Tax %").grid(row=1, column=0, sticky="w", pady=4)
        self.tax_entry = ttk.Entry(totals_frame)
        self.tax_entry.insert(0, "0")
        self.tax_entry.grid(row=1, column=1, pady=4, sticky="ew")

        self.subtotal_lbl = ttk.Label(totals_frame, text="Subtotal: $0.00")
        self.subtotal_lbl.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self.total_lbl = ttk.Label(totals_frame, text="Total: $0.00", font=("Segoe UI", 13, "bold"))
        self.total_lbl.grid(row=3, column=0, columnspan=2, sticky="w")

        ttk.Button(totals_frame, text="Recalculate", command=self._recalc).grid(row=4, column=0, columnspan=2, pady=(10, 4))
        ttk.Button(totals_frame, text="Complete Sale & Print Receipt", command=self._checkout).grid(
            row=5, column=0, columnspan=2, pady=4)

    def _add_to_cart(self):
        idx = self.product_combo.current()
        if idx < 0:
            messagebox.showwarning("No product", "Choose a product first.")
            return
        try:
            qty = int(self.qty_entry.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Quantity must be a positive whole number.")
            return

        product = self._products[idx]
        if qty > product["stock_qty"]:
            messagebox.showerror("Not enough stock", f"Only {product['stock_qty']} in stock for {product['name']}.")
            return

        for item in self.cart:
            if item["product_id"] == product["id"]:
                item["quantity"] += qty
                break
        else:
            self.cart.append({"product_id": product["id"], "name": product["name"],
                               "unit_price": product["unit_price"], "quantity": qty})
        self._render_cart()

    def _remove_selected(self):
        selected = self.cart_tree.selection()
        if not selected:
            return
        idx = self.cart_tree.index(selected[0])
        del self.cart[idx]
        self._render_cart()

    def _render_cart(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)
        for item in self.cart:
            line_total = item["quantity"] * item["unit_price"]
            self.cart_tree.insert("", "end", values=(item["name"], item["quantity"],
                                                       f"{item['unit_price']:.2f}", f"{line_total:.2f}"))
        self._recalc()

    def _recalc(self):
        subtotal = sum(i["quantity"] * i["unit_price"] for i in self.cart)
        try:
            discount_pct = float(self.discount_entry.get() or 0)
            tax_pct = float(self.tax_entry.get() or 0)
        except ValueError:
            discount_pct = tax_pct = 0
        total = (subtotal - subtotal * discount_pct / 100) * (1 + tax_pct / 100)
        self.subtotal_lbl.config(text=f"Subtotal: ${subtotal:,.2f}")
        self.total_lbl.config(text=f"Total: ${total:,.2f}")

    def _checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty cart", "Add at least one item first.")
            return
        try:
            discount_pct = float(self.discount_entry.get() or 0)
            tax_pct = float(self.tax_entry.get() or 0)
        except ValueError:
            messagebox.showerror("Invalid input", "Discount and Tax must be numbers.")
            return

        try:
            result = db.record_sale(self.cart, discount_pct, tax_pct)
        except ValueError as e:
            messagebox.showerror("Checkout failed", str(e))
            return

        receipt_path = self._generate_receipt(result)
        self.cart = []
        self._render_cart()
        self.app.refresh_all()
        messagebox.showinfo("Sale complete", f"Sale #{result['sale_id']} recorded.\nReceipt saved to:\n{receipt_path}")

    def _generate_receipt(self, result):
        receipts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "receipts")
        os.makedirs(receipts_dir, exist_ok=True)
        path = os.path.join(receipts_dir, f"receipt_{result['sale_id']}.txt")

        items = db.get_sale_items(result["sale_id"])
        lines = ["=" * 40, "        SHOP RECEIPT", "=" * 40,
                 f"Sale ID: {result['sale_id']}", f"Date:    {result['timestamp']}", "-" * 40]
        for it in items:
            lines.append(f"{it['product_name'][:20]:<20} x{it['quantity']:<3} ${it['line_total']:.2f}")
        lines += ["-" * 40, f"Subtotal:  ${result['subtotal']:.2f}",
                  f"Discount:  -${result['discount_amt']:.2f}", f"Tax:       +${result['tax_amt']:.2f}",
                  f"TOTAL:     ${result['total']:.2f}", "=" * 40, "   Thank you for your purchase!"]

        with open(path, "w") as f:
            f.write("\n".join(lines))
        return path

    def refresh(self):
        self._products = db.get_products()
        self.product_combo["values"] = [f"{p['item_id']} - {p['name']} (${p['unit_price']:.2f}, stock: {p['stock_qty']})"
                                         for p in self._products]
