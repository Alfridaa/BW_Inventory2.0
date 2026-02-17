import tkinter as tk
from tkinter import ttk, messagebox

from settings.constants import KLEIDUNG_COLUMNS


class AddKleidungDialog(tk.Toplevel):
    def __init__(self, master, db, on_saved=None):
        super().__init__(master)
        self.title("Kleidung hinzufügen")
        self.db = db
        self.on_saved = on_saved
        self.geometry("520x260")
        self.transient(master)
        self.grab_set()

        self.inputs: dict[str, ttk.Entry] = {}
        form = ttk.Frame(self)
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for row, (col, _type) in enumerate(KLEIDUNG_COLUMNS):
            ttk.Label(form, text=col).grid(row=row, column=0, sticky="w", pady=3)
            entry = ttk.Entry(form)
            entry.grid(row=row, column=1, sticky="we", padx=4)
            self.inputs[col] = entry

        form.grid_columnconfigure(1, weight=1)

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=10)
        ttk.Button(btns, text="Speichern", command=self.save).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT)

    def save(self):
        rec = {c: self.inputs[c].get().strip() for c, _ in KLEIDUNG_COLUMNS}
        if not rec["type"]:
            messagebox.showerror("Fehlende Angaben", "Bitte mindestens 'type' ausfüllen")
            return
        try:
            self.db.insert_kleidung(rec)
            self.db.commit()
        except Exception as ex:
            messagebox.showerror("Fehler", f"Beim Speichern ist ein Fehler aufgetreten: {ex}")
            return
        if self.on_saved:
            self.on_saved()
        self.destroy()


class EditKleidungDialog(tk.Toplevel):
    def __init__(self, master, db, record: dict, on_saved=None):
        super().__init__(master)
        self.title("Kleidung bearbeiten")
        self.db = db
        self.row_id = int(record.get("rowid"))
        self.on_saved = on_saved
        self.geometry("520x260")
        self.transient(master)
        self.grab_set()

        self.inputs: dict[str, ttk.Entry] = {}
        form = ttk.Frame(self)
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for row, (col, _type) in enumerate(KLEIDUNG_COLUMNS):
            ttk.Label(form, text=col).grid(row=row, column=0, sticky="w", pady=3)
            entry = ttk.Entry(form)
            entry.grid(row=row, column=1, sticky="we", padx=4)
            entry.insert(0, str(record.get(col) or ""))
            self.inputs[col] = entry

        form.grid_columnconfigure(1, weight=1)

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=10)
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Löschen", command=self.delete).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Speichern", command=self.save).pack(side=tk.RIGHT, padx=6)

    def save(self):
        rec = {c: self.inputs[c].get().strip() for c, _ in KLEIDUNG_COLUMNS}
        if not rec["type"]:
            messagebox.showerror("Fehlende Angaben", "Bitte mindestens 'type' ausfüllen")
            return
        try:
            self.db.update_kleidung(self.row_id, rec)
            self.db.commit()
        except Exception as ex:
            messagebox.showerror("Fehler", f"Beim Speichern ist ein Fehler aufgetreten: {ex}")
            return
        if self.on_saved:
            self.on_saved()
        self.destroy()

    def delete(self):
        answer = messagebox.askokcancel("Warnung", "Wirklich den Eintrag löschen?")
        if not answer:
            return
        self.db.delete_kleidung(self.row_id)
        self.db.commit()
        if self.on_saved:
            self.on_saved()
        self.destroy()
