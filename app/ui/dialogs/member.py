import tkinter as tk
from tkinter import ttk, messagebox
from settings.constants import MEMBER_COLUMNS
from app.core.utils import generate_next_valid_id_member

class AddMemberDialog(tk.Toplevel):
    BOOL_COLS = {"ET_SO", "ET_WI", "PR_SO", "PR_WI", "NFM", "LR", "EL"}

    def __init__(self, master, db, on_saved=None):
        super().__init__(master)
        self.title("Einsatzkräfte hinzufügen")
        self.db = db
        self.on_saved = on_saved
        self.geometry("520x420")
        self.transient(master)
        self.grab_set()

        form = ttk.Frame(self)
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(form, text="first_name").grid(row=0, column=0, sticky="w", pady=3)
        self.e_first = ttk.Entry(form)
        self.e_first.grid(row=0, column=1, sticky="we", padx=4)

        ttk.Label(form, text="last_name").grid(row=1, column=0, sticky="w", pady=3)
        self.e_last = ttk.Entry(form)
        self.e_last.grid(row=1, column=1, sticky="we", padx=4)

        self.bool_vars: dict[str, tk.IntVar] = {}
        r = 2
        for col in self.BOOL_COLS:
            var = tk.IntVar(value=0)
            cb = ttk.Checkbutton(form, text=col, variable=var)
            cb.grid(row=r, column=0, columnspan=2, sticky="w")
            self.bool_vars[col] = var
            r += 1

        for i in range(2):
            form.grid_columnconfigure(i, weight=1)

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=10)
        ttk.Button(btns, text="Speichern", command=self.save).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT)

    def save(self):
        first = self.e_first.get().strip()
        last = self.e_last.get().strip()
        if not first or not last:
            messagebox.showerror("Fehlende Angaben", "Bitte Vor- und Nachname ausfüllen")
            return
        try:
            rec = {c: None for c, _ in MEMBER_COLUMNS}
            old_list = self.db.get_member_ids()
            rec["ID"] = generate_next_valid_id_member(old_list)  # Bugfix: eigene Member-ID
            rec["first_name"] = first
            rec["last_name"] = last
            for c in self.BOOL_COLS:
                rec[c] = 1 if self.bool_vars[c].get() else 0
            self.db.insert_member(rec)
            self.db.commit()
        except Exception as ex:
            messagebox.showerror("Fehler", f"Beim Speichern ist ein Fehler aufgetreten: {ex}")
            return
        if self.on_saved:
            self.on_saved()
            if hasattr(self.master, "status_var"):
                self.master.status_var.set(f"Neues Mitglied ({first} {last}) hinzugefügt")
        self.destroy()

class EditMemberDialog(tk.Toplevel):
    BOOL_COLS = {"ET_SO", "ET_WI", "PR_SO", "PR_WI", "NFM", "LR", "EL"}

    def __init__(self, master, db, record: dict, on_saved=None):
        super().__init__(master)
        self.title(f"Einsatzkraft bearbeiten — ID {record.get('ID')}")
        self.db = db
        self.rec_id = record.get("ID")
        self.on_saved = on_saved
        self.geometry("520x420")
        self.transient(master)
        self.grab_set()
        
        form = ttk.Frame(self)
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(form, text="first_name").grid(row=0, column=0, sticky="w", pady=3)
        self.e_first = ttk.Entry(form)
        self.e_first.grid(row=0, column=1, sticky="we", padx=4)
        self.e_first.insert(0, str(record.get("first_name") or ""))

        ttk.Label(form, text="last_name").grid(row=1, column=0, sticky="w", pady=3)
        self.e_last = ttk.Entry(form)
        self.e_last.grid(row=1, column=1, sticky="we", padx=4)
        self.e_last.insert(0, str(record.get("last_name") or ""))

        self.bool_vars: dict[str, tk.IntVar] = {}
        r = 2
        for col in self.BOOL_COLS:
            var = tk.IntVar(value=1 if str(record.get(col)) == "1" else 0)
            cb = ttk.Checkbutton(form, text=col, variable=var)
            cb.grid(row=r, column=0, columnspan=2, sticky="w")
            self.bool_vars[col] = var
            r += 1

        for i in range(2):
            form.grid_columnconfigure(i, weight=1)

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=10)
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Löschen", command=self.delete).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Speichern", command=self.save).pack(side=tk.RIGHT, padx=6)

    def save(self):
        first = self.e_first.get().strip()
        last = self.e_last.get().strip()
        if not first or not last:
            messagebox.showerror("Fehlende Angaben", "Bitte Vor- und Nachname ausfüllen")
            return
        try:
            rec = {c: None for c, _ in MEMBER_COLUMNS if c != "ID"}
            rec["first_name"] = first
            rec["last_name"] = last
            for c in self.BOOL_COLS:
                rec[c] = 1 if self.bool_vars[c].get() else 0
            self.db.update_member(self.rec_id, rec)
            self.db.commit()
        except Exception as ex:
            messagebox.showerror("Fehler", f"Beim Speichern ist ein Fehler aufgetreten: {ex}")
            return
        if self.on_saved:
            self.on_saved()
            if hasattr(self.master.master.master, "status_var"):
                self.master.master.master.status_var.set(f"Mitglied ({first} {last}) bearbeitet")
        self.destroy()

    def delete(self):
        answer = messagebox.askokcancel("Warnung", "Wirklich den Eintrag löschen?")
        if answer:
            first = self.e_first.get().strip()
            last = self.e_last.get().strip()
            self.db.delete_member(self.rec_id)
            self.db.commit()
            if self.on_saved:
                self.on_saved()
            if hasattr(self.master.master.master, "status_var"):
                self.master.master.master.status_var.set(f"Mitglied ({first} {last}) gelöscht")
        self.destroy()
