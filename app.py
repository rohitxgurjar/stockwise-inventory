import tkinter as tk
from tkinter import ttk

import database as db
from screens.dashboard import DashboardTab
from screens.products import ProductsTab
from screens.stock_entry import StockEntryTab
from screens.checkout import CheckoutTab
from screens.reports import ReportsTab


class InventoryApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("StockWise - Smart Inventory")
        self.geometry("1280x780")
        self.minsize(1100, 700)

        db.init_db()

        self.setup_style()
        self.build_layout()
        self.refresh_all()
        self.refresh_all()
    def setup_style(self):

        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TFrame",
            background="#F4F6F8"
        )

        style.configure(
            "Main.TFrame",
            background="#F4F6F8"
        )

        style.configure(
            "Sidebar.TFrame",
            background="#17212B"
        )

        style.configure(
            "Header.TFrame",
            background="#FFFFFF"
        )

        style.configure(
            "Title.TLabel",
            background="#FFFFFF",
            foreground="#17212B",
            font=("Helvetica", 20, "bold")
        )

        style.configure(
            "Subtitle.TLabel",
            background="#FFFFFF",
            foreground="#718096",
            font=("Helvetica", 10)
        )

        style.configure(
            "SidebarTitle.TLabel",
            background="#17212B",
            foreground="#FFFFFF",
            font=("Helvetica", 20, "bold")
        )

        style.configure(
            "SidebarSubtitle.TLabel",
            background="#17212B",
            foreground="#AAB7C4",
            font=("Helvetica", 9)
        )

        style.configure(
            "Nav.TButton",
            background="#17212B",
            foreground="#D9E2EC",
            font=("Helvetica", 11),
            borderwidth=0,
            padding=(18, 12)
        )

        style.map(
            "Nav.TButton",
            background=[("active", "#263746")],
            foreground=[("active", "#FFFFFF")]
        )

        style.configure(
            "Bottom.TLabel",
            background="#17212B",
            foreground="#8293A5",
            font=("Helvetica", 8)
        )
    def build_layout(self):

        self.main_container = ttk.Frame(
            self,
            style="Main.TFrame"
        )
        self.main_container.pack(
            fill="both",
            expand=True
        )

        # Sidebar
        self.sidebar = ttk.Frame(
            self.main_container,
            width=220,
            style="Sidebar.TFrame"
        )
        self.sidebar.pack(
            side="left",
            fill="y"
        )
        self.sidebar.pack_propagate(False)

        # Logo
        ttk.Label(
            self.sidebar,
            text="STOCKWISE",
            style="SidebarTitle.TLabel"
        ).pack(
            anchor="w",
            padx=22,
            pady=(30, 2)
        )

        ttk.Label(
            self.sidebar,
            text="SMART INVENTORY",
            style="SidebarSubtitle.TLabel"
        ).pack(
            anchor="w",
            padx=23,
            pady=(0, 30)
        )

        # Navigation
        self.add_nav_button("Dashboard", 0)
        self.add_nav_button("Products", 1)
        self.add_nav_button("Inventory", 2)
        self.add_nav_button("Checkout", 3)
        self.add_nav_button("Reports", 4)

        # Bottom sidebar area
        ttk.Frame(
            self.sidebar,
            style="Sidebar.TFrame"
        ).pack(
            fill="both",
            expand=True
        )

        ttk.Label(
            self.sidebar,
            text="OFFLINE MODE",
            style="Bottom.TLabel"
        ).pack(
            anchor="w",
            padx=23,
            pady=(0, 4)
        )

        ttk.Label(
            self.sidebar,
            text="Local SQLite Database",
            style="Bottom.TLabel"
        ).pack(
            anchor="w",
            padx=23,
            pady=(0, 20)
        )

        # Content area
        self.content = ttk.Frame(
            self.main_container,
            style="Main.TFrame"
        )
        self.content.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Header
        self.header = ttk.Frame(
            self.content,
            style="Header.TFrame",
            padding=(24, 18)
        )
        self.header.pack(
            fill="x"
        )

        self.header_title = ttk.Label(
            self.header,
            text="Dashboard",
            style="Title.TLabel"
        )
        self.header_title.pack(
            side="left"
        )

        ttk.Label(
            self.header,
            text="Local • Secure • Offline",
            style="Subtitle.TLabel"
        ).pack(
            side="right"
        )

        ttk.Separator(
            self.content,
            orient="horizontal"
        ).pack(
            fill="x"
        )

        # Hidden notebook
        self.notebook = ttk.Notebook(
            self.content
        )
        self.notebook.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # Screens
        self.dashboard = DashboardTab(
            self.notebook,
            self
        )

        self.products = ProductsTab(
            self.notebook,
            self
        )

        self.stock_entry = StockEntryTab(
            self.notebook,
            self
        )

        self.checkout = CheckoutTab(
            self.notebook,
            self
        )

        self.reports = ReportsTab(
            self.notebook,
            self
        )

        self.notebook.add(
            self.dashboard,
            text="Dashboard"
        )

        self.notebook.add(
            self.products,
            text="Products"
        )

        self.notebook.add(
            self.stock_entry,
            text="Inventory"
        )

        self.notebook.add(
            self.checkout,
            text="Checkout"
        )

        self.notebook.add(
            self.reports,
            text="Reports"
        )
    def add_nav_button(self, name, page_index):

        button = ttk.Button(
            self.sidebar,
            text=name,
            style="Nav.TButton",
            command=lambda: self.select_page(page_index)
        )

        button.pack(
            fill="x",
            padx=12,
            pady=3
        )

    def select_page(self, page_index):

        self.notebook.select(page_index)

        names = [
            "Dashboard",
            "Products",
            "Inventory",
            "Checkout",
            "Reports"
        ]

        self.header_title.config(
            text=names[page_index]
        )

    def refresh_all(self):

        self.dashboard.refresh()
        self.products.refresh()
        self.stock_entry.refresh()
        self.checkout.refresh()
        self.reports.refresh()


if __name__ == "__main__":

    app = InventoryApp()
    app.mainloop()
