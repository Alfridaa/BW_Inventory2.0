import tkinter as tk
from tkinter import messagebox, ttk


class VehicleManageDialog(tk.Toplevel):
    PREFIX = "set_vehicle_"

    def __init__(self, master, db):
        super().__init__(master)
        self.db = db

        self.title("Fahrzeuge verwalten")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.vehicle_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.database_var = tk.StringVar()

        self.vehicle_combo: ttk.Combobox | None = None
        self.location_combo: ttk.Combobox | None = None
        self.database_combo: ttk.Combobox | None = None

        self.vehicle_rows_by_key: dict[str, dict] = {}

        self._build_ui()
        self._reload_values()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Fahrzeug").grid(row=0, column=0, sticky="w")
        self.vehicle_combo = ttk.Combobox(frame, textvariable=self.vehicle_var, state="normal", width=36)
        self.vehicle_combo.grid(row=0, column=1, pady=(0, 8), sticky="ew")
        self.vehicle_combo.bind("<<ComboboxSelected>>", self._on_vehicle_selected)
        self.vehicle_combo.bind("<FocusOut>", self._on_vehicle_selected)

        ttk.Label(frame, text="Location").grid(row=1, column=0, sticky="w")
        self.location_combo = ttk.Combobox(frame, textvariable=self.location_var, state="normal", width=36)
        self.location_combo.grid(row=1, column=1, pady=(0, 8), sticky="ew")

        ttk.Label(frame, text="PSA Soll-Datenbank").grid(row=2, column=0, sticky="w")
        self.database_combo = ttk.Combobox(frame, textvariable=self.database_var, state="normal", width=36)
        self.database_combo.grid(row=2, column=1, pady=(0, 8), sticky="ew")

        hint = "Leer lassen oder eine PSA Soll-Tabelle auswählen"
        ttk.Label(frame, text=hint).grid(row=3, column=1, sticky="w", pady=(0, 8))

        btns = ttk.Frame(frame)
        btns.grid(row=4, column=0, columnspan=2, sticky="e")
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btns, text="Löschen", command=self._delete).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btns, text="Speichern", command=self._save).pack(side=tk.RIGHT)

        frame.columnconfigure(1, weight=1)

    def _reload_values(self):
        rows = self.db.fetch_vehicle_rows()
        self.vehicle_rows_by_key = {
            row["vehicle"]: {
                "location": row["location"] or "",
                "database_soll": row["database_soll"] or "",
            }
            for row in rows
        }

        if self.vehicle_combo is not None:
            self.vehicle_combo["values"] = sorted(self.vehicle_rows_by_key.keys())
        if self.location_combo is not None:
            locations = sorted({r["location"] for r in self.vehicle_rows_by_key.values() if r["location"]})
            self.location_combo["values"] = locations

        if self.database_combo is not None:
            table_names = self.db.list_vehicle_set_tables()
            display_names = [name[len(self.PREFIX):] for name in table_names if name.startswith(self.PREFIX)]
            self.database_combo["values"] = sorted(display_names)

    def _on_vehicle_selected(self, _event=None):
        key = self.vehicle_var.get().strip()
        row = self.vehicle_rows_by_key.get(key)
        if row is None:
            return
        self.location_var.set(row["location"])
        db_soll = row["database_soll"]
        if db_soll.startswith(self.PREFIX):
            db_soll = db_soll[len(self.PREFIX):]
        self.database_var.set(db_soll)

    def _save(self):
        vehicle = self.vehicle_var.get().strip().lstrip("/")
        location = self.location_var.get().strip()
        db_soll_selection = self.database_var.get().strip()

        if not vehicle:
            messagebox.showwarning("Hinweis", "Bitte ein Fahrzeug angeben.", parent=self)
            return
        if not location:
            messagebox.showwarning("Hinweis", "Bitte eine Location angeben.", parent=self)
            return

        database_soll = ""
        if db_soll_selection:
            database_soll = (
                db_soll_selection
                if db_soll_selection.startswith(self.PREFIX)
                else f"{self.PREFIX}{db_soll_selection}"
            )

        try:
            self.db.upsert_vehicle(vehicle, location, database_soll)
            self._reload_values()
            self.vehicle_var.set(vehicle)
            messagebox.showinfo("Erfolg", "Fahrzeug wurde gespeichert.", parent=self)
        except Exception as ex:
            messagebox.showerror("Fehler", f"Beim Speichern ist ein Fehler aufgetreten: {ex}", parent=self)

    def _delete(self):
        vehicle = self.vehicle_var.get().strip().lstrip("/")
        if not vehicle:
            messagebox.showwarning("Hinweis", "Bitte zuerst ein Fahrzeug auswählen.", parent=self)
            return

        if not messagebox.askyesno("Löschen", f"Fahrzeug '{vehicle}' wirklich löschen?", parent=self):
            return

        try:
            self.db.delete_vehicle(vehicle)
            self.vehicle_var.set("")
            self.location_var.set("")
            self.database_var.set("")
            self._reload_values()
        except Exception as ex:
            messagebox.showerror("Fehler", f"Beim Löschen ist ein Fehler aufgetreten: {ex}", parent=self)
