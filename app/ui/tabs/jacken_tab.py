import tkinter as tk
from tkinter import ttk

from settings.constants import KLEIDUNG_COLUMNS
from app.ui.components.filter_table import FilterTable


class KleidungTab(ttk.Frame):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.columns = [c for c, _ in KLEIDUNG_COLUMNS]
        self.member_name_by_id: dict[str, str] = {}
        self.table = FilterTable(self, self.columns)
        self.table.pack(fill=tk.BOTH, expand=True)
        self.table.bind("<<FilterChanged>>", lambda e: self.refresh())
        self.table.tree.bind("<Double-1>", self.on_double_click)
        self._rowid_by_item: dict[str, int] = {}
        self._row_by_item: dict[str, dict] = {}

    def refresh(self):
        if not self.db.conn:
            return
        self.member_name_by_id = self._build_member_name_map()
        rows = self.db.fetch_all_kleidung()
        filters = self.table.get_filters()
        self.table.clear()
        self._rowid_by_item.clear()
        self._row_by_item.clear()
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
            self._row_by_item[item] = dict(r)

    def on_double_click(self, event):
        item = self.table.tree.focus()
        if not item:
            return
        row_id = self._rowid_by_item.get(item)
        if row_id is None:
            return
        row = self._row_by_item.get(item)
        if not row:
            return
        record = {col: row.get(col) for col, _ in KLEIDUNG_COLUMNS}
        record["rowid"] = row_id

        from app.ui.dialogs.kleidung import EditKleidungDialog

        top = self.winfo_toplevel()
        on_saved_cb = None
        if hasattr(top, "refresh_kleidung"):
            on_saved_cb = top.refresh_kleidung
        EditKleidungDialog(self, self.db, record, on_saved=on_saved_cb)

    def _build_member_name_map(self) -> dict[str, str]:
        member_name_by_id: dict[str, str] = {}
        for member in self.db.get_members_basic():
            first_name = (member.get("first_name") or "").strip()
            last_name = (member.get("last_name") or "").strip()
            full_name = f"{first_name} {last_name}".strip()
            if full_name:
                member_id = str(member["ID"]).strip()
                member_name_by_id[member_id] = full_name
                if member_id.startswith("/"):
                    member_name_by_id[member_id[1:]] = full_name
                else:
                    member_name_by_id[f"/{member_id}"] = full_name
        return member_name_by_id

    def format_value(self, col: str, v):
        if col == "location" and v not in (None, ""):
            location = str(v).strip()
            if location.startswith("/NR"):
                member_name = self.member_name_by_id.get(location)
                if not member_name:
                    member_name = self.member_name_by_id.get(location[1:])
                if member_name:
                    return f"{location} ({member_name})"
        return v if v is not None else ""
