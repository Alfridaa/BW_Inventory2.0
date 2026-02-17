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
        PlaceholderAbortDialog(self, f"Set bearbeiten: {selected}", "Wird später implementiert.")

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
        PlaceholderAbortDialog(self, f"Set angelegt: {new_name}", "SQL-Tabelle wurde angelegt. Bearbeiten wird später implementiert.")
