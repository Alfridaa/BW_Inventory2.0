import tkinter as tk
from tkinter import ttk, messagebox

from app.core.utils import parse_date, today_str


class DepotPsaCheckDialog(tk.Toplevel):
    EMPTY_FILTER_VALUE = ""

    def __init__(self, master, db, on_saved=None):
        super().__init__(master)
        self.title("PSA Check Lagerort")
        self.geometry("980x620")
        self.transient(master)
        self.grab_set()

        self.db = db
        self.on_saved = on_saved

        self.var_location = tk.StringVar()
        self.var_product_type = tk.StringVar()
        self.var_property_1 = tk.StringVar()
        self.var_property_2 = tk.StringVar()
        self.var_check_date = tk.StringVar(value=today_str())

        self.row_selected: dict[str, bool] = {}

        self._build_ui()
        self._load_locations()

    def _build_ui(self):
        filters = ttk.LabelFrame(self, text="Filter")
        filters.pack(fill=tk.X, padx=10, pady=(10, 6))

        ttk.Label(filters, text="location").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.cb_location = ttk.Combobox(filters, textvariable=self.var_location, state="readonly")
        self.cb_location.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(filters, text="product_type").grid(row=0, column=2, sticky="w", padx=6, pady=6)
        self.cb_product_type = ttk.Combobox(filters, textvariable=self.var_product_type, state="readonly")
        self.cb_product_type.grid(row=0, column=3, sticky="ew", padx=6, pady=6)

        ttk.Label(filters, text="property_1").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.cb_property_1 = ttk.Combobox(filters, textvariable=self.var_property_1, state="readonly")
        self.cb_property_1.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        ttk.Label(filters, text="property_2").grid(row=1, column=2, sticky="w", padx=6, pady=6)
        self.cb_property_2 = ttk.Combobox(filters, textvariable=self.var_property_2, state="readonly")
        self.cb_property_2.grid(row=1, column=3, sticky="ew", padx=6, pady=6)

        for col in range(4):
            filters.grid_columnconfigure(col, weight=1)

        self.cb_location.bind("<<ComboboxSelected>>", lambda _e: self._on_location_changed())
        self.cb_product_type.bind("<<ComboboxSelected>>", lambda _e: self._on_product_type_changed())
        self.cb_property_1.bind("<<ComboboxSelected>>", lambda _e: self._on_property_1_changed())
        self.cb_property_2.bind("<<ComboboxSelected>>", lambda _e: self._refresh_table())

        date_frame = ttk.Frame(self)
        date_frame.pack(fill=tk.X, padx=10, pady=6)
        ttk.Label(date_frame, text="check_date").pack(side=tk.LEFT)
        self.entry_date = ttk.Entry(date_frame, textvariable=self.var_check_date, width=14)
        self.entry_date.pack(side=tk.LEFT, padx=6)
        ttk.Button(date_frame, text="Heute", command=lambda: self.var_check_date.set(today_str())).pack(side=tk.LEFT)

        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        columns = ("psa", "ID", "product_type", "property_1", "property_2", "serial_number", "check_date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        headings = {
            "psa": "checkbox psa",
            "ID": "ID",
            "product_type": "product_type",
            "property_1": "property_1",
            "property_2": "property_2",
            "serial_number": "serial_number",
            "check_date": "check_date",
        }
        widths = {"psa": 100, "ID": 90, "product_type": 160, "property_1": 140, "property_2": 140, "serial_number": 160, "check_date": 120}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Button-1>", self._handle_tree_click)

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(btns, text="Check abschließen", command=self._finish_check).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Schließen", command=self.destroy).pack(side=tk.RIGHT)

    def _load_locations(self):
        locations = self.db.get_inventory_distinct_by_filters("location")
        self.cb_location["values"] = locations
        self.var_location.set(locations[0] if locations else "")
        self._on_location_changed()

    def _on_location_changed(self):
        self.var_product_type.set("")
        self.var_property_1.set("")
        self.var_property_2.set("")

        if not self.var_location.get():
            self.cb_product_type["values"] = []
            self.cb_property_1["values"] = []
            self.cb_property_2["values"] = []
            self._refresh_table()
            return

        products = self.db.get_inventory_distinct_by_filters(
            "product_type",
            location=self.var_location.get(),
        )
        self.cb_product_type["values"] = [self.EMPTY_FILTER_VALUE, *products]
        self.var_product_type.set(self.EMPTY_FILTER_VALUE)
        self._on_product_type_changed()

    def _on_product_type_changed(self):
        self.var_property_1.set("")
        self.var_property_2.set("")

        prop1_values = self.db.get_inventory_distinct_by_filters(
            "property_1",
            location=self.var_location.get(),
            product_type=self.var_product_type.get() or None,
        )
        self.cb_property_1["values"] = [self.EMPTY_FILTER_VALUE, *prop1_values]
        self.var_property_1.set(self.EMPTY_FILTER_VALUE)
        self._on_property_1_changed()

    def _on_property_1_changed(self):
        self.var_property_2.set("")

        prop2_values = self.db.get_inventory_distinct_by_filters(
            "property_2",
            location=self.var_location.get(),
            product_type=self.var_product_type.get() or None,
            property_1=self.var_property_1.get() or None,
        )
        self.cb_property_2["values"] = [self.EMPTY_FILTER_VALUE, *prop2_values]
        self.var_property_2.set(self.EMPTY_FILTER_VALUE)

        self._refresh_table()

    def _refresh_table(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.row_selected.clear()

        if not self.var_location.get():
            return

        rows = self.db.fetch_inventory_for_psa_check(
            location=self.var_location.get(),
            product_type=self.var_product_type.get() or None,
            property_1=self.var_property_1.get() or None,
            property_2=self.var_property_2.get() or None,
        )

        for row in rows:
            item_id = row["ID"]
            default_checked = str(row["psa_check"] or "0") == "1"
            self.row_selected[item_id] = default_checked
            self.tree.insert(
                "",
                tk.END,
                iid=item_id,
                values=(
                    "☑" if default_checked else "☐",
                    row["ID"],
                    row["product_type"],
                    row["property_1"],
                    row["property_2"],
                    row["serial_number"],
                    row["check_date"] or "",
                ),
            )

    def _handle_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify_column(event.x)
        if column != "#1":
            return
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        self.row_selected[item_id] = not self.row_selected.get(item_id, False)
        values = list(self.tree.item(item_id, "values"))
        values[0] = "☑" if self.row_selected[item_id] else "☐"
        self.tree.item(item_id, values=values)

    def _finish_check(self):
        check_date = self.var_check_date.get().strip()
        if not parse_date(check_date):
            messagebox.showerror("Ungültiges Datum", "Bitte Datum im Format YYYY-MM-DD eingeben.")
            return

        selected_ids = [item_id for item_id, selected in self.row_selected.items() if selected]
        if not selected_ids:
            messagebox.showinfo("Hinweis", "Keine Einträge für PSA-Check ausgewählt.")
            return

        try:
            self.db.update_inventory_psa_check_dates(selected_ids, check_date)
        except Exception as ex:
            messagebox.showerror("Fehler", f"PSA-Check konnte nicht gespeichert werden: {ex}")
            return

        messagebox.showinfo("Erfolg", f"PSA-Check gespeichert: {len(selected_ids)} Einträge aktualisiert.")
        self._refresh_table()
        if self.on_saved:
            self.on_saved()
