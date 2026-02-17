import tkinter as tk
from tkinter import ttk, messagebox
from settings.constants import INVENTORY_COLUMNS, ID_LIST_FILE
from app.core.utils import today_str, parse_date, delete_file, append_line, generate_next_valid_id_item


def _build_member_name_map(db) -> dict[str, str]:
    member_name_by_id: dict[str, str] = {}
    for member in db.get_members_basic():
        first_name = (member.get("first_name") or "").strip()
        last_name = (member.get("last_name") or "").strip()
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            continue

        member_id = str(member.get("ID") or "").strip()
        if not member_id:
            continue

        member_name_by_id[member_id] = full_name
        if member_id.startswith("/"):
            member_name_by_id[member_id[1:]] = full_name
        else:
            member_name_by_id[f"/{member_id}"] = full_name
    return member_name_by_id


def _format_location_option(location: str, member_name_by_id: dict[str, str]) -> str:
    location_str = str(location).strip()
    if location_str.startswith("/NR"):
        member_name = member_name_by_id.get(location_str) or member_name_by_id.get(location_str[1:])
        if member_name:
            return f"{location_str} ({member_name})"
    return location_str


def _location_value_from_display(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("/NR") and " (" in cleaned and cleaned.endswith(")"):
        return cleaned.split(" (", 1)[0].strip()
    return cleaned

class AddInventoryDialog(tk.Toplevel):
    def __init__(self, master, db, on_saved=None):
        super().__init__(master)
        self.title("Material hinzufügen")
        self.db = db
        self.on_saved = on_saved
        self.member_name_by_id = _build_member_name_map(db)
        self.geometry("720x520")
        self.transient(master)
        self.grab_set()

        self.inputs = {}
        form = ttk.Frame(self)
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        row = 0
        for col, _type in INVENTORY_COLUMNS:
            if col == "ID":
                continue
            ttk.Label(form, text=f"{col}").grid(row=row, column=0, sticky="w", pady=3)
            dd = ttk.Combobox(form, state="readonly")
            try:
                dd_values = self.db.get_distinct_values("inventory", col)
                if col == "location":
                    dd_values = [_format_location_option(v, self.member_name_by_id) for v in dd_values]
                dd["values"] = [""] + dd_values
            except Exception:
                dd["values"] = [""]
            dd.grid(row=row, column=1, sticky="we", padx=4)

            new_e = ttk.Entry(form)
            new_e.grid(row=row, column=2, sticky="we", padx=4)

            self.inputs[col] = {"combo": dd, "new": new_e}

            if col in ("manufactury_date", "check_date"):
                btn = ttk.Button(form, text="Heute", command=lambda e=new_e: e.delete(0, tk.END) or e.insert(0, today_str()))
                btn.grid(row=row, column=3, padx=4)

            row += 1

        self.inputs["check_date"]["new"].insert(0, today_str())

        psa_widgets = self.inputs["psa_check"]
        for w in psa_widgets.values():
            try: w.grid_forget()
            except Exception: pass
        var_psa = tk.IntVar(value=0)
        cb = ttk.Checkbutton(form, text="psa_check", variable=var_psa)
        cb.grid(row=row - 1, column=1, sticky="w")
        self.inputs["psa_check"] = {"var": var_psa}

        ttk.Separator(self).pack(fill=tk.X, pady=6)
        cnt_frame = ttk.Frame(self)
        cnt_frame.pack(fill=tk.X, padx=10)
        ttk.Label(cnt_frame, text="Anzahl").pack(side=tk.LEFT)
        self.e_count = ttk.Spinbox(cnt_frame, from_=1, to=999, width=6)
        self.e_count.set("1")
        self.e_count.pack(side=tk.LEFT, padx=6)

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=10)
        ttk.Button(btns, text="Speichern", command=self.save).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT)

        for i in range(4):
            form.grid_columnconfigure(i, weight=1)

    def resolve_value(self, col: str):
        if col == "psa_check":
            return 1 if self.inputs[col]["var"].get() else 0
        pair = self.inputs[col]
        newv = pair["new"].get().strip()
        if newv:
            return newv
        selected = pair["combo"].get().strip()
        if col == "location":
            return _location_value_from_display(selected)
        return selected

    def save(self):
        for col in ("manufactury_date", "check_date"):
            val = self.resolve_value(col)
            if val and not parse_date(val):
                messagebox.showerror("Ungültiges Datum", f"{col}: Bitte YYYY-MM-DD eingeben")
                return
        lt = self.resolve_value("life_time")
        if lt:
            try: int(lt)
            except Exception:
                messagebox.showerror("Ungültiger Wert", "life_time muss eine Ganzzahl sein")
                return

        try:
            count = max(1, int(self.e_count.get()))
        except Exception:
            count = 1

        try:
            delete_file(ID_LIST_FILE)
            for _ in range(count):
                rec = {}
                for col, _ in INVENTORY_COLUMNS:
                    if col == "ID":
                        old_list = self.db.get_inventory_ids()
                        rec[col] = generate_next_valid_id_item(old_list)
                        append_line(ID_LIST_FILE, rec[col])
                    elif col == "psa_check":
                        rec[col] = 1 if self.inputs[col]["var"].get() else 0
                    else:
                        rec[col] = self.resolve_value(col)
                self.db.insert_inventory(rec)
            self.db.commit()
        except Exception as ex:
            messagebox.showerror("Fehler", f"Beim Speichern ist ein Fehler aufgetreten: {ex}")
            return

        if self.on_saved:
            self.on_saved()
        self.destroy()

class EditInventoryDialog(tk.Toplevel):
    def __init__(self, master, db, record: dict, on_saved=None):
        super().__init__(master)
        self.title(f"Material bearbeiten — ID {record.get('ID')}")
        self.db = db
        self.rec_id = record.get("ID")
        self.on_saved = on_saved
        self.member_name_by_id = _build_member_name_map(db)
        self.geometry("720x520")
        self.transient(master)
        self.grab_set()
        self.inputs = {}
        form = ttk.Frame(self)
        form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        row = 0
        for col, _type in INVENTORY_COLUMNS:
            if col == "ID":
                ttk.Label(form, text=f"ID: {self.rec_id}").grid(row=row, column=0, columnspan=3, sticky="w", pady=3)
                row += 1
                continue
            ttk.Label(form, text=f"{col}").grid(row=row, column=0, sticky="w", pady=3)
            dd = ttk.Combobox(form, state="readonly")
            try:
                dd_values = self.db.get_distinct_values("inventory", col)
                if col == "location":
                    dd_values = [_format_location_option(v, self.member_name_by_id) for v in dd_values]
                dd["values"] = [""] + dd_values
            except Exception:
                dd["values"] = [""]
            dd.grid(row=row, column=1, sticky="we", padx=4)

            new_e = ttk.Entry(form)
            new_e.grid(row=row, column=2, sticky="we", padx=4)
            current_val = record.get(col) if record.get(col) is not None else ""
            new_e.insert(0, str(current_val))

            self.inputs[col] = {"combo": dd, "new": new_e}

            if col in ("manufactury_date", "check_date"):
                ttk.Button(form, text="Heute", command=lambda e=new_e: e.delete(0, tk.END) or e.insert(0, today_str())).grid(row=row, column=3, padx=4)

            row += 1

        psa_widgets = self.inputs["psa_check"]
        for w in psa_widgets.values():
            try: w.grid_forget()
            except Exception: pass
        var_psa = tk.IntVar(value=1 if str(record.get("psa_check")) == "1" else 0)
        cb = ttk.Checkbutton(form, text="psa_check", variable=var_psa)
        cb.grid(row=row - 1, column=1, sticky="w")
        self.inputs["psa_check"] = {"var": var_psa}

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=10)
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Löschen", command=self.delete).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Speichern", command=self.save).pack(side=tk.RIGHT, padx=6)

        for i in range(4):
            form.grid_columnconfigure(i, weight=1)

    def resolve_value(self, col: str):
        if col == "psa_check":
            return 1 if self.inputs[col]["var"].get() else 0
        pair = self.inputs[col]
        newv = pair["new"].get().strip()
        if newv:
            return newv
        selected = pair["combo"].get().strip()
        if col == "location":
            return _location_value_from_display(selected)
        return selected

    def save(self):
        for col in ("manufactury_date", "check_date"):
            val = self.resolve_value(col)
            if val and not parse_date(val):
                messagebox.showerror("Ungültiges Datum", f"{col}: Bitte YYYY-MM-DD eingeben")
                return
        lt = self.resolve_value("life_time")
        if lt:
            try: int(lt)
            except Exception:
                messagebox.showerror("Ungültiger Wert", "life_time muss eine Ganzzahl sein")
                return
        try:
            rec = {}
            for col, _ in INVENTORY_COLUMNS:
                if col == "ID":
                    continue
                elif col == "psa_check":
                    rec[col] = 1 if self.inputs[col]["var"].get() else 0
                else:
                    rec[col] = self.resolve_value(col)
            self.db.update_inventory(self.rec_id, rec)
            self.db.commit()
        except Exception as ex:
            messagebox.showerror("Fehler", f"Beim Speichern ist ein Fehler aufgetreten: {ex}")
            return
        if self.on_saved:
            self.on_saved()
            if hasattr(self.master.master.master, "status_var"):
                self.master.master.master.status_var.set(f"Material (ID: {self.rec_id}) bearbeitet")
        self.destroy()

    def delete(self):
        answer = messagebox.askokcancel("Warnung", "Wirklich den Eintrag löschen?")
        if answer:
            self.db.delete_inventory(self.rec_id)
            self.db.commit()
            if self.on_saved:
                self.on_saved()
            if hasattr(self.master.master.master, "status_var"):
                self.master.master.master.status_var.set(f"Material (ID: {self.rec_id}) gelöscht")
        self.destroy()
