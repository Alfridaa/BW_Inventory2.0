# dialogs/print_export_dialog.py
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from settings.constants import MEMBER_COLUMNS, INVENTORY_COLUMNS
from app.core.pdf_export import export_table_to_pdf  # generischer Exporter
from app.db.database import Database

INVENTORY_EXPORT_COLUMNS = [
    ("ID", "TEXT PRIMARY KEY"),
    ("product_type", "TEXT"),
    ("property_1", "TEXT"),
    ("property_2", "TEXT"),
    ("producer", "TEXT"),
    ("product_name", "TEXT"),
    ("serial_number", "TEXT"),
]
INVENTORY_EXPORT_COLNAMES = [c for c, _ in INVENTORY_EXPORT_COLUMNS]

class PrintExportDialog(tk.Toplevel):
    """
    Dialog: Inventarliste für ein ausgewähltes Mitglied als PDF drucken.
    - Dropdown zeigt 'first_name last_name', intern wird member.ID gemerkt.
    - Druckt alle Inventory-Einträge mit location = member.ID.
    - PDF enthält nur INVENTORY_EXPORT_COLUMNS.
    """

    def __init__(self, master, db, on_saved=None):
        super().__init__(master)
        self.title("Inventarliste pro Mitglied drucken")
        self.db = db
        self.on_saved = on_saved

        self.geometry("560x240")
        self.transient(master)
        self.grab_set()

        # Member-Map: display -> member_id
        self._member_display_to_id = {}
        self._member_list = []  # Liste der Anzeigenamen (für Combobox)

        # ---------- Form ----------
        form = ttk.Frame(self)
        form.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Mitgliedsauswahl
        ttk.Label(form, text="Mitglied:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.member_var = tk.StringVar()
        self.member_combo = ttk.Combobox(
            form,
            textvariable=self.member_var,
            values=[],
            state="readonly",
            width=32,
        )
        self.member_combo.grid(row=0, column=1, sticky="we", pady=(0, 6), columnspan=2)

        # Pfad/Dateiname
        ttk.Label(form, text="Datei speichern unter:").grid(row=1, column=0, sticky="w")
        self.path_var = tk.StringVar(value=self._default_filename("mitglied"))
        path_entry = ttk.Entry(form, textvariable=self.path_var, width=48)
        path_entry.grid(row=1, column=1, sticky="we", padx=(0, 6))
        browse_btn = ttk.Button(form, text="Durchsuchen…", command=self._browse)
        browse_btn.grid(row=1, column=2, sticky="we")

        # Hinweis
        hint = ttk.Label(
            form,
            text="Es werden alle Inventar-Einträge mit location = Mitglieds-ID gedruckt. Logo-Pfad in utils/pdf_export.py anpassen.",
        )
        hint.grid(row=2, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # ---------- Buttons ----------
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, padx=12, pady=(6, 12))
        ttk.Button(btns, text="Abbrechen", command=self.destroy).pack(side=tk.RIGHT)
        ttk.Button(btns, text="Speichern", command=self._save_pdf).pack(side=tk.RIGHT, padx=(0, 8))

        # Layout-Feinschliff
        form.columnconfigure(1, weight=1)

        # Daten laden & UI aktivieren
        self._load_members()
        self.update_idletasks()
        self.lift()
        self.focus_force()
        self.wait_visibility()
        self.grab_set()

    # ---------- Helpers ----------
    def _default_filename(self, name_hint: str) -> str:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        os.makedirs("./output", exist_ok=True)
        safe_hint = name_hint.replace(" ", "_") if name_hint else "export"
        return os.path.abspath(os.path.join("./output", f"{safe_hint}_{ts}.pdf"))

    def _browse(self):
        # Default-Filename ggf. mit Mitgliedsnamen aktualisieren
        display = self.member_var.get().strip()
        if display:
            self.path_var.set(self._default_filename(display))

        initial = self.path_var.get() or self._default_filename("mitglied")
        path = filedialog.asksaveasfilename(
            parent=self,
            title="PDF speichern unter",
            initialfile=os.path.basename(initial),
            initialdir=os.path.dirname(initial) if os.path.dirname(initial) else os.getcwd(),
            defaultextension=".pdf",
            filetypes=[("PDF-Datei", "*.pdf")],
        )
        if path:
            if not path.lower().endswith(".pdf"):
                path += ".pdf"
            self.path_var.set(path)

    def _load_members(self):
        members = self.db.get_members_basic()  # nutzt jetzt den Wrapper
        self._member_display_to_id = {}
        self._member_list = []

        for m in members:
            mid = m["ID"]
            fn = m.get("first_name") or ""
            ln = m.get("last_name") or ""
            display = f"{fn} {ln}".strip() or str(mid)
            self._member_display_to_id[display] = mid
            self._member_list.append(display)

        self.member_combo["values"] = self._member_list
        if self._member_list:
            self.member_combo.current(0)
            self.path_var.set(self._default_filename(self._member_list[0]))


    def _save_pdf(self):
        display = self.member_var.get().strip()
        if not display:
            messagebox.showwarning("Auswahl fehlt", "Bitte zuerst ein Mitglied auswählen.")
            return

        member_id = self._member_display_to_id.get(display)
        if not member_id:
            messagebox.showwarning("Ungültige Auswahl", "Das ausgewählte Mitglied konnte nicht aufgelöst werden.")
            return

        out_path = self.path_var.get().strip()
        if not out_path:
            messagebox.showwarning("Fehlender Dateiname", "Bitte einen Zielspeicherort auswählen.")
            return

        try:
            # Inventar für dieses Mitglied holen: location = member.ID
            rows = self._fetch_inventory_for_member(member_id)
            if not rows:
                if not messagebox.askyesno("Keine Daten", "Für dieses Mitglied wurden keine Gegenstände gefunden.\nLeeres PDF trotzdem erzeugen?"):
                    return

            # Nur die gewünschten Spalten in die PDF bringen
            title = f"Inventarliste für {display}"
            export_table_to_pdf(
                pdf_title=title,
                columns=INVENTORY_EXPORT_COLUMNS,   # nur die 7 gewünschten Spalten
                rows=rows,                          # Liste[dict] mit genau diesen Keys
                out_path=out_path,
                logo_path="settings/BW_LOGO_mit_NBG_bunt.svg",
                footer_lines=["Erstellt am:", "Ort/Datum              Unterschrift"],
                width_overrides={
                    "ID": 18,
                    "product_type": 28,
                    "property_1": 26,
                    "property_2": 26,
                    "producer": 28,
                    "product_name": 36,
                    "serial_number": 32,
                },
            )

            messagebox.showinfo("PDF erstellt", f"Export erfolgreich:\n{out_path}")
            if self.on_saved:
                self.on_saved()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Fehler beim PDF-Export", str(e))

    def _fetch_inventory_for_member(self, member_id: str) -> list[dict]:
        # holt nur die Spalten, die ins PDF sollen
        return self.db.get_inventory_for_member(member_id, INVENTORY_EXPORT_COLNAMES)

