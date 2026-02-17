import re
import tkinter as tk
from tkinter import messagebox, ttk


class PlaceholderAbortDialog(tk.Toplevel):
    def __init__(self, master, title: str, text: str):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text=text).grid(row=0, column=0, padx=4, pady=(0, 12))
        ttk.Button(frame, text="Abbrechen", command=self.destroy).grid(row=1, column=0)


class VehicleCheckDialog(tk.Toplevel):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db

        self.title("PSA Bedarf Berechnung")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.vehicle_var = tk.StringVar()

        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Welches Fahrzeug soll geprüft werden?").grid(row=0, column=0, columnspan=2, sticky="w")

        self.vehicle_combo = ttk.Combobox(frame, textvariable=self.vehicle_var, state="readonly", width=30)
        self.vehicle_combo.grid(row=1, column=0, columnspan=2, pady=(6, 12), sticky="w")

        ttk.Button(frame, text="Prüfen", command=self.open_placeholder_result).grid(row=2, column=0, sticky="w")
        ttk.Button(frame, text="Abbrechen", command=self.destroy).grid(row=2, column=1, sticky="e")

        self.refresh_vehicle_list()

    def refresh_vehicle_list(self):
        vehicles = self.db.get_vehicle_locations()
        self.vehicle_combo["values"] = vehicles
        if vehicles:
            self.vehicle_var.set(vehicles[0])
        else:
            self.vehicle_var.set("")

    def open_placeholder_result(self):
        vehicle = self.vehicle_var.get().strip()
        if not vehicle:
            messagebox.showinfo("Hinweis", "Es wurde kein Fahrzeug gefunden oder ausgewählt.")
            return
        PlaceholderAbortDialog(self, f"Fahrzeug prüfen: {vehicle}", "Wird später implementiert.")


class PSASollListDialog(tk.Toplevel):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db

        self.title("PSA Soll-Liste")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="PSA Soll-Liste anpassen für:").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        ttk.Button(frame, text="Fahrzeuge", command=self.open_vehicle_dialog).grid(row=1, column=0, padx=(0, 6))
        ttk.Button(frame, text="Einsatzkräfte", command=self.open_member_dialog).grid(row=1, column=1, padx=(0, 6))
        ttk.Button(frame, text="Abbrechen", command=self.destroy).grid(row=1, column=2)

    def open_member_dialog(self):
        PlaceholderAbortDialog(self, "PSA Soll-Liste Einsatzkräfte", "Wird später implementiert.")

    def open_vehicle_dialog(self):
        if not self.db.conn:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Datenbank öffnen.")
            return
        VehicleSetDialog(self, self.db)


class VehicleSetDialog(tk.Toplevel):
    PREFIX = "set_vehicle_"

    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.title("PSA Soll-Liste Fahrzeuge")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.set_var = tk.StringVar()
        self.new_set_var = tk.StringVar()

        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Vorhandenes Set auswählen:").grid(row=0, column=0, sticky="w")
        self.combo = ttk.Combobox(frame, textvariable=self.set_var, state="readonly", width=30)
        self.combo.grid(row=1, column=0, padx=(0, 8), pady=(4, 10), sticky="w")
        ttk.Button(frame, text="Bearbeiten", command=self.edit_selected_set).grid(row=1, column=1, pady=(4, 10), sticky="w")

        ttk.Label(frame, text="Neues Set hinzufügen:").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.new_set_var, width=33).grid(row=3, column=0, padx=(0, 8), pady=(4, 10), sticky="w")
        ttk.Button(frame, text="Anlegen", command=self.create_new_set).grid(row=3, column=1, pady=(4, 10), sticky="w")

        ttk.Button(frame, text="Abbrechen", command=self.destroy).grid(row=4, column=1, sticky="e")

        self.refresh_sets()

    def refresh_sets(self):
        set_names = self.db.list_vehicle_sets()
        self.combo["values"] = set_names
        if set_names:
            self.set_var.set(set_names[0])
        else:
            self.set_var.set("")

    def edit_selected_set(self):
        selected = self.set_var.get().strip()
        if not selected:
            messagebox.showinfo("Hinweis", "Bitte zuerst ein Set aus der Liste auswählen.")
            return
        VehicleSetEditDialog(self, self.db, selected)

    def create_new_set(self):
        new_name = self.new_set_var.get().strip()
        if not new_name:
            messagebox.showinfo("Hinweis", "Bitte einen Namen für das neue Set eingeben.")
            return
        if not re.fullmatch(r"\w+", new_name):
            messagebox.showerror("Ungültiger Name", "Nur Buchstaben, Zahlen und Unterstriche sind erlaubt.")
            return

        full_table_name = f"{self.PREFIX}{new_name}"
        try:
            self.db.create_vehicle_set_table(full_table_name)
        except Exception as ex:
            messagebox.showerror("Fehler", f"Set konnte nicht angelegt werden: {ex}")
            return

        self.new_set_var.set("")
        self.refresh_sets()
        self.set_var.set(new_name)
        VehicleSetEditDialog(self, self.db, new_name)


class VehicleSetEditDialog(tk.Toplevel):
    PREFIX = "set_vehicle_"

    def __init__(self, master, db, set_name: str):
        super().__init__(master)
        self.db = db
        self.set_name = set_name
        self.table_name = f"{self.PREFIX}{set_name}"

        self.title(f"Set bearbeiten: {set_name}")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.rows_by_iid: dict[str, dict] = {}
        self.selected_iid: str | None = None

        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Set-Inhalte (Text nicht bearbeitbar, nur Anzahl):").grid(row=0, column=0, columnspan=4, sticky="w")

        self.tree = ttk.Treeview(
            frame,
            columns=("product_type", "property_1", "property_2", "count"),
            show="headings",
            height=10,
        )
        self.tree.heading("product_type", text="Typ")
        self.tree.heading("property_1", text="Property 1")
        self.tree.heading("property_2", text="Property 2")
        self.tree.heading("count", text="Anzahl")
        self.tree.column("product_type", width=150)
        self.tree.column("property_1", width=140)
        self.tree.column("property_2", width=140)
        self.tree.column("count", width=80, anchor="e")
        self.tree.grid(row=1, column=0, columnspan=4, pady=(6, 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_select_row)

        ttk.Label(frame, text="Anzahl bearbeiten:").grid(row=2, column=0, sticky="w")
        self.count_var = tk.StringVar(value="1")
        self.count_spin = tk.Spinbox(frame, from_=0, to=9999, textvariable=self.count_var, width=8)
        self.count_spin.grid(row=2, column=1, sticky="w")
        ttk.Button(frame, text="Speichern", command=self.save_count).grid(row=2, column=2, padx=(8, 0), sticky="w")

        ttk.Button(frame, text="Hinzufügen", command=self.open_add_dialog).grid(row=3, column=0, pady=(10, 0), sticky="w")
        ttk.Button(frame, text="Schließen", command=self.destroy).grid(row=3, column=3, pady=(10, 0), sticky="e")

        self.refresh_rows()

    def refresh_rows(self):
        self.rows_by_iid.clear()
        self.selected_iid = None
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        rows = self.db.fetch_vehicle_set_rows(self.table_name)
        for row in rows:
            iid = str(row["rowid"])
            self.rows_by_iid[iid] = {
                "rowid": row["rowid"],
                "product_type": row["product_type"],
                "property_1": row["property_1"],
                "property_2": row["property_2"],
                "count": row["count"] if row["count"] is not None else 0,
            }
            self.tree.insert(
                "",
                "end",
                iid=iid,
                values=(row["product_type"], row["property_1"], row["property_2"], row["count"] if row["count"] is not None else 0),
            )

    def on_select_row(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            self.selected_iid = None
            return
        self.selected_iid = sel[0]
        row = self.rows_by_iid.get(self.selected_iid)
        if row:
            self.count_var.set(str(row["count"]))

    def save_count(self):
        if not self.selected_iid:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Zeile auswählen.")
            return
        try:
            new_count = int(self.count_var.get())
        except ValueError:
            messagebox.showerror("Ungültige Anzahl", "Bitte eine ganze Zahl eingeben.")
            return
        if new_count < 0:
            messagebox.showerror("Ungültige Anzahl", "Die Anzahl muss mindestens 0 sein.")
            return

        row = self.rows_by_iid[self.selected_iid]
        self.db.update_vehicle_set_row_count(self.table_name, row["rowid"], new_count)
        self.refresh_rows()

    def open_add_dialog(self):
        AddVehicleSetEntryDialog(self, self.db, on_add=self.add_entry)

    def add_entry(self, product_type: str, property_1: str, property_2: str, count: int):
        self.db.insert_vehicle_set_row(self.table_name, product_type, property_1, property_2, count)
        self.refresh_rows()


class AddVehicleSetEntryDialog(tk.Toplevel):
    def __init__(self, master, db, on_add):
        super().__init__(master)
        self.db = db
        self.on_add = on_add

        self.title("Eintrag hinzufügen")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.product_type_var = tk.StringVar()
        self.property_1_var = tk.StringVar()
        self.property_2_var = tk.StringVar()
        self.count_var = tk.StringVar(value="1")

        frame = ttk.Frame(self, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="Product Type:").grid(row=0, column=0, sticky="w")
        self.product_type_combo = ttk.Combobox(frame, textvariable=self.product_type_var, state="readonly", width=30)
        self.product_type_combo.grid(row=1, column=0, sticky="w", pady=(2, 8))
        self.product_type_combo.bind("<<ComboboxSelected>>", self.on_product_type_selected)

        ttk.Label(frame, text="Property 1:").grid(row=2, column=0, sticky="w")
        self.property_1_combo = ttk.Combobox(frame, textvariable=self.property_1_var, state="disabled", width=30)
        self.property_1_combo.grid(row=3, column=0, sticky="w", pady=(2, 8))
        self.property_1_combo.bind("<<ComboboxSelected>>", self.on_property_1_selected)

        ttk.Label(frame, text="Property 2:").grid(row=4, column=0, sticky="w")
        self.property_2_combo = ttk.Combobox(frame, textvariable=self.property_2_var, state="disabled", width=30)
        self.property_2_combo.grid(row=5, column=0, sticky="w", pady=(2, 8))

        ttk.Label(frame, text="Anzahl:").grid(row=6, column=0, sticky="w")
        tk.Spinbox(frame, from_=0, to=9999, textvariable=self.count_var, width=8).grid(row=7, column=0, sticky="w", pady=(2, 10))

        btns = ttk.Frame(frame)
        btns.grid(row=8, column=0, sticky="e")
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Hinzufügen", command=self.save).pack(side="left")

        self.load_product_types()

    def load_product_types(self):
        values = self.db.get_inventory_product_types()
        self.product_type_combo["values"] = values

    def on_product_type_selected(self, _event=None):
        self.property_1_var.set("")
        self.property_2_var.set("")
        self.property_2_combo["values"] = []
        self.property_2_combo.configure(state="disabled")

        values = self.db.get_inventory_property1_for_type(self.product_type_var.get())
        self.property_1_combo["values"] = values
        self.property_1_combo.configure(state="readonly")

    def on_property_1_selected(self, _event=None):
        values = self.db.get_inventory_property2_for_type_and_property1(
            self.product_type_var.get(),
            self.property_1_var.get(),
        )
        self.property_2_var.set("")
        self.property_2_combo["values"] = values
        self.property_2_combo.configure(state="readonly")

    def save(self):
        product_type = self.product_type_var.get().strip()
        property_1 = self.property_1_var.get().strip()
        property_2 = self.property_2_var.get().strip()

        if not product_type:
            messagebox.showinfo("Hinweis", "Bitte zuerst Product Type auswählen.")
            return
        if not property_1:
            messagebox.showinfo("Hinweis", "Bitte danach Property 1 auswählen.")
            return
        if not property_2:
            messagebox.showinfo("Hinweis", "Bitte danach Property 2 auswählen.")
            return
        try:
            count = int(self.count_var.get())
        except ValueError:
            messagebox.showerror("Ungültige Anzahl", "Bitte eine ganze Zahl eingeben.")
            return
        if count < 0:
            messagebox.showerror("Ungültige Anzahl", "Die Anzahl muss mindestens 0 sein.")
            return

        self.on_add(product_type, property_1, property_2, count)
        self.destroy()
