import tkinter as tk
from tkinter import ttk
from settings.constants import MEMBER_COLUMNS
from app.ui.components.filter_table import FilterTable

class PSACalcTab(ttk.Frame):
    BOOL_COLS = {"ET_SO", "ET_WI", "PR_SO", "PR_WI", "NFM", "LR", "EL"}

    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.columns = [c for c, _ in MEMBER_COLUMNS]
        self.table = FilterTable(self, self.columns, bool_columns=self.BOOL_COLS)
        self.table.pack(fill=tk.BOTH, expand=True)
        self.table.bind("<<FilterChanged>>", lambda e: self.refresh())
        self.table.tree.bind("<Double-1>", self.on_double_click)

    def refresh(self):
        if not self.db.conn:
            return
        rows = self.db.fetch_all("member")
        filters = self.table.get_filters()
        self.table.clear()
        for r in rows:
            keep = True
            for col, needle in filters.items():
                val = r[col]
                disp_val = self.format_value(col, val)
                if needle.lower() not in str(disp_val).lower():
                    keep = False
                    break
            if not keep:
                continue
            values = [self.format_value(c, r[c]) for c, _ in MEMBER_COLUMNS]
            self.table.insert_row(values)

    def on_double_click(self, event):
        item = self.table.tree.focus()
        if not item:
            return
        vals = self.table.tree.item(item, "values")
        if not vals:
            return
        rec_id = vals[0]
        row = self.db.fetch_by_id("member", rec_id)
        if not row:
            return
        from app.ui.dialogs.member import EditMemberDialog
        top = self.winfo_toplevel()
        on_saved_cb = None
        if hasattr(top, "refresh_member"):
            on_saved_cb = top.refresh_member
        EditMemberDialog(self, self.db, dict(row), on_saved=on_saved_cb)

    @staticmethod
    def format_value(col: str, v):
        if col in PSACalcTab.BOOL_COLS:
            return "Ja" if str(v) == "1" else "Nein"
        return v if v is not None else ""
