import tkinter as tk
from tkinter import messagebox, ttk


class LocationManageDialog(tk.Toplevel):
    PREFIX = "set_vehicle_"

    def __init__(self, master, db):
        super().__init__(master)
        self.db = db

        self.title("Lagerorte verwalten")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.location_var = tk.StringVar()
        self.set_name_var = tk.StringVar()
        self.database_var = tk.StringVar()

        self.location_combo: ttk.Combobox | None = None
        self.set_name_combo: ttk.Combobox | None = None
        self.database_combo: ttk.Combobox | None = None

        self.location_rows_by_key: dict[str, dict] = {}

        self._build_ui()
        self._reload_values()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Location").grid(row=0, column=0, sticky="w")
        self.location_combo = ttk.Combobox(frame, textvariable=self.location_var, state="normal", width=36)
        self.location_combo.grid(row=0, column=1, pady=(0, 8), sticky="ew")
        self.location_combo.bind("<<ComboboxSelected>>", self._on_location_selected)
        self.location_combo.bind("<FocusOut>", self._on_location_selected)

        ttk.Label(frame, text="Setname").grid(row=1, column=0, sticky="w")
        self.set_name_combo = ttk.Combobox(frame, textvariable=self.set_name_var, state="normal", width=36)
        self.set_name_combo.grid(row=1, column=1, pady=(0, 8), sticky="ew")

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
        rows = self.db.fetch_location_rows()
        self.location_rows_by_key = {
            row["location"]: {
                "set_name": row["set_name"] or "",
                "database_soll": row["database_soll"] or "",
            }
            for row in rows
        }

        if self.location_combo is not None:
            self.location_combo["values"] = sorted(self.location_rows_by_key.keys())

        if self.set_name_combo is not None:
            set_names = sorted({r["set_name"] for r in self.location_rows_by_key.values() if r["set_name"]})
            self.set_name_combo["values"] = set_names

        if self.database_combo is not None:
            table_names = self.db.list_location_set_tables()
            display_names = [name[len(self.PREFIX):] for name in table_names if name.startswith(self.PREFIX)]
            self.database_combo["values"] = sorted(display_names)

    def _on_location_selected(self, _event=None):
        key = self.location_var.get().strip()
        row = self.location_rows_by_key.get(key)
        if row is None:
            return
        self.set_name_var.set(row["set_name"])
        db_soll = row["database_soll"]
        if db_soll.startswith(self.PREFIX):
            db_soll = db_soll[len(self.PREFIX):]
        self.database_var.set(db_soll)

    def _save(self):
        location = self.location_var.get().strip()
        set_name = self.set_name_var.get().strip().lstrip("/")
        db_soll_selection = self.database_var.get().strip()

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
            self.db.upsert_location(location, set_name, database_soll)
            self._reload_values()
            self.location_var.set(location)
            messagebox.showinfo("Erfolg", "Lagerort wurde gespeichert.", parent=self)
        except Exception as ex:
            messagebox.showerror("Fehler", f"Beim Speichern ist ein Fehler aufgetreten: {ex}", parent=self)

    def _delete(self):
        location = self.location_var.get().strip()
        if not location:
            messagebox.showwarning("Hinweis", "Bitte zuerst eine Location auswählen.", parent=self)
            return

        if not messagebox.askyesno("Löschen", f"Location '{location}' wirklich löschen?", parent=self):
            return

        try:
            self.db.delete_location(location)
            self.location_var.set("")
            self.set_name_var.set("")
            self.database_var.set("")
            self._reload_values()
        except Exception as ex:
            messagebox.showerror("Fehler", f"Beim Löschen ist ein Fehler aufgetreten: {ex}", parent=self)
