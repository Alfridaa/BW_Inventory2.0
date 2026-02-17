import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from app.core.utils import random_hex_color

class ColorRulesDialog(tk.Toplevel):
    def __init__(self, master, settings, on_save=None):
        super().__init__(master)
        self.title("Farbregeln einstellen")
        self.settings = settings
        self.on_save = on_save
        self.geometry("600x400")
        self.transient(master)
        self.grab_set()

        cols = ("Beschreibung", "HEX", "Monate")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=6)
        ttk.Button(btn_frame, text="Hinzufügen", command=self.add_rule).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Bearbeiten", command=self.edit_rule).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Löschen", command=self.delete_rule).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Speichern", command=self.save).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_frame, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT, padx=4)

        self.load_rules()

    def load_rules(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in self.settings.color_rules:
            self.tree.insert("", tk.END, values=(r.get("description", ""), r.get("hex", ""), r.get("months", 0)))

    def add_rule(self):
        RuleEditor(self, on_done=self._add_done)

    def _add_done(self, desc, hexv, months):
        try:
            months = int(months)
        except Exception:
            messagebox.showerror("Fehler", "'Monate' muss eine Zahl sein")
            return
        self.settings.color_rules.append({"description": desc, "hex": hexv, "months": months})
        self.load_rules()

    def edit_rule(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = self.tree.item(item, "values")
        idx = self.tree.index(item)
        RuleEditor(self, default=vals, on_done=lambda d, h, m: self._edit_done(idx, d, h, m))

    def _edit_done(self, idx, desc, hexv, months):
        try:
            months = int(months)
        except Exception:
            messagebox.showerror("Fehler", "'Monate' muss eine Zahl sein")
            return
        self.settings.color_rules[idx] = {"description": desc, "hex": hexv, "months": months}
        self.load_rules()

    def delete_rule(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        del self.settings.color_rules[idx]
        self.load_rules()

    def save(self):
        self.settings.save()
        if self.on_save:
            self.on_save()
            if hasattr(self.master, "status_var"):
                self.master.status_var.set("Einstellung bearbeitet")
        self.destroy()

class RuleEditor(tk.Toplevel):
    def __init__(self, master, default=None, on_done=None):
        super().__init__(master)
        self.title("Regel bearbeiten")
        self.on_done = on_done
        self.geometry("360x160")
        self.transient(master)
        self.grab_set()

        ttk.Label(self, text="Beschreibung").pack(anchor="w", padx=8, pady=(8, 0))
        self.e_desc = ttk.Entry(self)
        self.e_desc.pack(fill=tk.X, padx=8)

        ttk.Label(self, text="Monate (Schwelle: fällig in ≤ Monate)").pack(anchor="w", padx=8, pady=(8, 0))
        self.e_months = ttk.Entry(self)
        self.e_months.pack(fill=tk.X, padx=8)

        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, pady=8)
        ttk.Button(btns, text="OK", command=self.ok).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT, padx=4)

        if default:
            self.e_desc.insert(0, default[0])
            self.e_months.insert(0, default[2])

    def ok(self):
        if self.on_done:
            _, hex_color = colorchooser.askcolor(color=random_hex_color(), title="Farbe Regel")
            self.on_done(self.e_desc.get().strip(), hex_color, self.e_months.get().strip())
        self.destroy()
