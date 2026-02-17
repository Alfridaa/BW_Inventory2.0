import re
import datetime as dt
import tkinter as tk
from tkinter import ttk
from settings.constants import INVENTORY_COLUMNS
from app.core.utils import parse_date, months_until_expiry
from app.ui.components.filter_table import FilterTable


def _safe_get(row, key, default=None):
    """Sicherer Zugriff für sqlite3.Row oder dict."""
    try:
        return row[key]
    except Exception:
        return default


class InventoryTab(ttk.Frame):
    def __init__(self, master, db, settings):
        super().__init__(master)
        self.db = db
        self.settings = settings
        self.columns = [c for c, _ in INVENTORY_COLUMNS]
        self.member_name_by_id: dict[str, str] = {}
        self.table = FilterTable(self, self.columns, bool_columns={"psa_check"})
        self.table.pack(fill=tk.BOTH, expand=True)
        self.table.bind("<<FilterChanged>>", lambda e: self.refresh())
        self.table.tree.bind("<Double-1>", self.on_double_click)

        # Textfarbe immer schwarz (Dark Mode override, u.a. macOS)
        style = ttk.Style(self)
        style.configure("Treeview", foreground="black")
        style.configure("Treeview.Heading", foreground="black")
        style.configure("Treeview", foreground="white")
        style.configure("Treeview.Heading", foreground="white")

        # Regel- und Spezial-Tags
        self.rebuild_color_tags()
        self.table.add_tag_style("depot", background="#F2F3F5", foreground="black")
        self.table.add_tag_style("expiry_violation", background="#a742ff", foreground="black")  # lila

    def rebuild_color_tags(self):
        # gleiche Sortierung wie in compute_row_tag()
        sorted_rules = sorted(self.settings.color_rules, key=lambda r: int(r.get("months", 0)))
        for idx, rule in enumerate(sorted_rules):
            tag = f"rule_{idx}"
            self.table.add_tag_style(tag, background=rule.get("hex", "#FFFFFF"), foreground="black")

    # ----------------- Herstell-Datum & Lebensdauer -----------------
    def _get_mfg_date_str(self, row):
        """
        Versucht, ein Herstell-Datum in verschiedenen (auch vertippten) Feldern zu finden.
        Wichtig: 'manufactury_date' (mit y) ist dabei.
        """
        candidates = (
            "manufactury_date",       # <== dein Feldname
            "manufacture_date",
            "manufactur_date",
            "manufacturing_date",
            "mfg_date",
            "mfg",
            "mfd",
            "herstellungsdatum",
        )
        for k in candidates:
            v = _safe_get(row, k)
            if v not in (None, ""):
                return v
        # Fallback: fuzzy über Keys
        try:
            keys = row.keys()
        except Exception:
            keys = []
        for k in keys:
            lk = str(k).lower()
            if "manufact" in lk or "herstell" in lk:
                v = _safe_get(row, k)
                if v not in (None, ""):
                    return v
        return None

    @staticmethod
    def _add_months(d: dt.date, months: int) -> dt.date:
        """Monate addieren (Monatsende korrekt behandeln)."""
        y = d.year + (d.month - 1 + months) // 12
        m = (d.month - 1 + months) % 12 + 1
        last_day = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
                    31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m-1]
        day = min(d.day, last_day)
        return dt.date(y, m, day)

    def _parse_lifetime(self, row) -> tuple[int, str] | None:
        """
        Lebensdauer aus row auslesen.
        Rückgabe: (wert, einheit) mit einheit in {"days","weeks","months","years"}.
        Regeln:
          - life_time / lifetime als INTEGER → **years**
          - lifetime_years → years
          - lifetime_months / _weeks / _days wie benannt
          - life_time / lifetime als String mit Einheit ("10 Jahre", "10y", "120m", "365d")
          - reine Zahl als String → **years**
          - toleriert Tippfehler: "lifte_time"
        """
        # explizite Felder
        for key, unit in (("lifetime_days", "days"),
                          ("lifetime_weeks", "weeks"),
                          ("lifetime_months", "months"),
                          ("lifetime_years", "years")):
            v = _safe_get(row, key)
            if v not in (None, ""):
                try:
                    return int(str(v).strip()), unit
                except Exception:
                    pass

        # life_time / lifetime (inkl. lifte_time) als INT → Jahre
        for key in ("life_time", "lifetime", "lifte_time"):
            v = _safe_get(row, key)
            if isinstance(v, (int, float)):
                return int(v), "years"
            if isinstance(v, str) and v.strip().isdigit():
                return int(v.strip()), "years"

        # life_time / lifetime als String mit Einheit
        for key in ("life_time", "lifetime", "lifte_time"):
            raw = _safe_get(row, key)
            if raw in (None, ""):
                continue
            s = str(raw).strip().lower()
            m = re.match(r"^\s*(\d+)\s*([a-zäöü]+)\s*$", s)
            if not m:
                continue
            val = int(m.group(1))
            unit = m.group(2)
            if unit in ("y", "yr", "yrs", "year", "years", "jahr", "jahre", "j", "a"):
                return val, "years"
            if unit.startswith("m"):
                return val, "months"
            if unit.startswith("d"):
                return val, "days"
            if unit.startswith("w"):
                return val, "weeks"

        return None

    def _expiry_from_mfg(self, row) -> dt.date | None:
        """Berechnet Herstell-Datum + Lebensdauer als Datum, falls möglich."""
        mfg_str = self._get_mfg_date_str(row)
        if not mfg_str:
            return None
        mfg = parse_date(mfg_str)
        if not mfg:
            return None

        lt = self._parse_lifetime(row)
        if not lt:
            return None

        val, unit = lt
        base = mfg if isinstance(mfg, dt.date) else mfg.date()

        if unit == "days":
            return base + dt.timedelta(days=val)
        if unit == "weeks":
            return base + dt.timedelta(weeks=val)
        if unit == "months":
            return self._add_months(base, val)
        if unit == "years":
            return self._add_months(base, val * 12)
        return None

    def has_mfg_lifetime_violation(self, row) -> bool:
        """True, wenn (manufactury_date + lifetime) <= heute."""
        expiry = self._expiry_from_mfg(row)
        if not expiry:
            return False
        today = dt.date.today()
        return expiry <= today
    # ---------------------------------------------------------------

    def compute_row_tag(self, check_date_str: str) -> str | None:
        if not check_date_str:
            return None
        check_date = parse_date(check_date_str)
        if not check_date:
            return None
        months_to_check = months_until_expiry(check_date)
        sorted_rules = sorted(self.settings.color_rules, key=lambda r: int(r.get("months", 0)))
        for idx, rule in enumerate(sorted_rules):
            try:
                threshold = int(rule.get("months", 0))
            except Exception:
                threshold = 0
            if months_to_check <= threshold:
                return f"rule_{idx}"
        return None

    def refresh(self):
        if not self.db.conn:
            return
        self.member_name_by_id = self._build_member_name_map()
        rows = self.db.fetch_all("inventory")
        filters = self.table.get_filters()
        self.table.clear()

        for r in rows:
            # Filter anwenden
            keep = True
            for col, needle in filters.items():
                val = r[col]
                disp_val = self.format_value(col, val)
                if needle.lower() not in str(disp_val).lower():
                    keep = False
                    break
            if not keep:
                continue

            # 1) höchste Priorität: Herstell-Datum + Lebensdauer überschritten?
            violated = self.has_mfg_lifetime_violation(r)

            # 2) Depot?
            location = str(_safe_get(r, "location", "") or "")
            is_depot = "depot" in location.lower()

            # 3) Checkdate-Regel
            rule_tag = self.compute_row_tag(_safe_get(r, "check_date", "")) or ""

            # Tag-Auswahl (Initial)
            if violated:
                tags = ("expiry_violation",)
            elif is_depot:
                tags = ("depot",)
            else:
                tags = (rule_tag,) if rule_tag else ()

            values = [self.format_value(c, r[c]) for c, _ in INVENTORY_COLUMNS]

            # Einfügen
            iid = self.table.insert_row(values, tags=tags)

            # Falls FilterTable kein iid zurückgibt: letztes Item nehmen
            if not iid:
                children = self.table.tree.get_children("")
                iid = children[-1] if children else None

            # Lila-Prio NACH dem Insert erzwingen (korrekt mit Keyword)
            if violated and iid:
                try:
                    self.table.tree.item(iid, tags=("expiry_violation",))
                except Exception as e:
                    # Optionales Debugging
                    print("Treeview.item set tags failed:", repr(e), "iid=", iid, "type(iid)=", type(iid))

    def on_double_click(self, event):
        item = self.table.tree.focus()
        if not item:
            return
        vals = self.table.tree.item(item, "values")
        if not vals:
            return
        rec_id = vals[0]
        row = self.db.fetch_by_id("inventory", rec_id)
        if not row:
            return
        from app.ui.dialogs.inventory import EditInventoryDialog
        top = self.winfo_toplevel()
        on_saved_cb = getattr(top, "refresh_inventory", None) if hasattr(top, "refresh_inventory") else None
        EditInventoryDialog(self, self.db, dict(row), on_saved=on_saved_cb)

    def _build_member_name_map(self) -> dict[str, str]:
        member_name_by_id: dict[str, str] = {}
        for member in self.db.get_members_basic():
            first_name = (member.get("first_name") or "").strip()
            last_name = (member.get("last_name") or "").strip()
            full_name = f"{first_name} {last_name}".strip()
            if full_name:
                member_name_by_id[str(member["ID"])] = full_name
        return member_name_by_id

    def format_value(self, col: str, v):
        if col in ("psa_check",):
            return "Ja" if str(v) == "1" else "Nein"
        if col == "location" and v not in (None, ""):
            location = str(v).strip()
            if location.startswith("/NR"):
                lookup_id = location[1:]
                member_name = self.member_name_by_id.get(lookup_id)
                if member_name:
                    return member_name
        return v if v is not None else ""
