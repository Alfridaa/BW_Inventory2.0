import tkinter as tk
from tkinter import ttk

from settings.constants import KLEIDUNG_COLUMNS
from app.ui.components.filter_table import FilterTable


class KleidungTab(ttk.Frame):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.columns = [c for c, _ in KLEIDUNG_COLUMNS]
        self.table = FilterTable(self, self.columns)
        self.table.pack(fill=tk.BOTH, expand=True)
        self.table.bind("<<FilterChanged>>", lambda e: self.refresh())
        self.table.tree.bind("<Double-1>", self.on_double_click)
        self._rowid_by_item: dict[str, int] = {}

    def refresh(self):
        if not self.db.conn:
            return
        rows = self.db.fetch_all_kleidung()
        filters = self.table.get_filters()
        self.table.clear()
        self._rowid_by_item.clear()
        for r in rows:
            values = [self.format_value(c, r[c]) for c, _ in KLEIDUNG_COLUMNS]
            keep = True
            for col, needle in filters.items():
                idx = self.columns.index(col)
                if needle.lower() not in str(values[idx]).lower():
                    keep = False
                    break
            if not keep:
                continue
            item = self.table.tree.insert("", tk.END, values=values)
            self._rowid_by_item[item] = r["rowid"]

    def on_double_click(self, event):
        item = self.table.tree.focus()
        if not item:
            return
        row_id = self._rowid_by_item.get(item)
        if row_id is None:
            return
        vals = self.table.tree.item(item, "values")
        if not vals:
            return
        record = {col: vals[idx] for idx, (col, _) in enumerate(KLEIDUNG_COLUMNS)}
        record["rowid"] = row_id

        from app.ui.dialogs.kleidung import EditKleidungDialog

        top = self.winfo_toplevel()
        on_saved_cb = None
        if hasattr(top, "refresh_kleidung"):
            on_saved_cb = top.refresh_kleidung
        EditKleidungDialog(self, self.db, record, on_saved=on_saved_cb)

    @staticmethod
    def format_value(col: str, v):
        return v if v is not None else ""
