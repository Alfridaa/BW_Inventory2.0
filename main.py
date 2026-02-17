import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from settings.constants import APP_TITLE
from settings.app_settings import AppSettings
from app.db.database import Database
from app.ui.tabs.inventory_tab import InventoryTab
from app.ui.tabs.member_tab import MemberTab
from app.ui.tabs.jacken_tab import KleidungTab
from app.ui.dialogs.color_rules import ColorRulesDialog
from app.ui.dialogs.about import AboutDialog
from app.ui.dialogs.print_member import PrintExportDialog
from app.ui.dialogs.vehicle import VehicleManageDialog
from app.core.utils import create_folder

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1450x700")

        self.settings = AppSettings()
        self.db = Database()

        self.create_menu()
        self.build_statusbar()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.inventory_tab = InventoryTab(self.notebook, self.db, self.settings)
        self.member_tab = MemberTab(self.notebook, self.db)
        self.kleidung_tab = KleidungTab(self.notebook, self.db)

        self.notebook.add(self.inventory_tab, text="Material")
        self.notebook.add(self.member_tab, text="Einsatzkräfte")
        self.notebook.add(self.kleidung_tab, text="Kleidung")
        

        if self.settings.last_db_path:
            try:
                self.open_db(self.settings.last_db_path)
                self.status_var.set(f"Zuletzt verwendete Datenbank geöffnet:{self.settings.last_db_path}")
            except Exception as ex:
                messagebox.showwarning("Hinweis", f"Konnte letzte DB nicht öffnen: {ex}")
                self.status_var.set("Zuletzt verwendete DB wurde nicht gefunden. Datei → Öffnen…")

    # -------------------------
    # Menu
    # -------------------------
    def create_menu(self):
        menubar = tk.Menu(self)

        m_datei = tk.Menu(menubar, tearoff=0)
        m_datei.add_command(label="Öffnen", command=self.menu_open)
        m_datei.add_separator()
        m_datei.add_command(label="Beenden", command=self.quit)
        menubar.add_cascade(label="Datei", menu=m_datei)

        m_entries = tk.Menu(menubar, tearoff=0)
        m_entries.add_command(label="Material hinzufügen", command=self.menu_add_inventory)
        m_entries.add_command(label="Einsatzkräfte hinzufügen", command=self.menu_add_member)
        m_entries.add_command(label="Kleidung hinzufügen", command=self.menu_add_kleidung)
        m_entries.add_command(label="Fahrzeuge verwalten", command=self.menu_manage_vehicles)
        menubar.add_cascade(label="Einträge", menu=m_entries)

        m_vehicle = tk.Menu(menubar, tearoff=0)
        m_vehicle.add_command(label="Fahrzeuge verwalten", command=self.menu_manage_vehicles)
        menubar.add_cascade(label="Fahrzeuge", menu=m_vehicle)

        m_psacheck = tk.Menu(menubar, tearoff=0)
        m_psacheck.add_command(label="Fahrzeuge", command=lambda: self.placeholder_dialog("PSA Check Fahrzeuge"))
        m_psacheck.add_command(label="Einsatzkräfte", command=lambda: self.placeholder_dialog("PSA Check Einsatzkräfte"))
        menubar.add_cascade(label="PSA-Check", menu=m_psacheck)

        m_psa_soll_liste = tk.Menu(m_psacheck, tearoff=0)
        m_psa_soll_liste.add_command(label="Check Fahrzeuge", command=lambda: self.placeholder_dialog("PSA Bedarf Berechnung"))
        m_psa_soll_liste.add_command(label="Check Einsatzkräfte", command=lambda: self.placeholder_dialog("PSA Bedarf Berechnung"))
        m_psa_soll_liste.add_separator()
        m_psa_soll_liste.add_command(label="Fahrzeuge anpassen", command=self.menu_psa_soll_liste_fahrzeuge)
        m_psa_soll_liste.add_command(label="Einsatzkräfte anpassen", command=self.menu_psa_soll_liste_einsatzkraefte)
        menubar.add_cascade(label="PSA Soll-Liste", menu=m_psa_soll_liste)

        m_print = tk.Menu(menubar, tearoff=0)
        m_print.add_command(label="Listen Fahrzeuge", command=lambda: self.placeholder_dialog("Drucken Fahrzeuge"))
        m_print.add_separator()
        m_print.add_command(label="Ausgabe Einsatzkräfte", command=self.open_print_dialog)
        m_print.add_command(label="Rückgabe Einsatzkräfte", command=lambda: self.placeholder_dialog("Drucken Fahrzeuge"))
        menubar.add_cascade(label="Drucken", menu=m_print)

        m_settings = tk.Menu(menubar, tearoff=0)
        m_settings.add_command(label="Farben PSA-Check", command=self.menu_settings)
        m_settings.add_separator()
        m_settings.add_command(label="Info", command=self.menu_help)
        menubar.add_cascade(label="Einstellung", menu=m_settings)

        self.config(menu=menubar)

    def placeholder_dialog(self, title: str):
        top = tk.Toplevel(self)
        top.title(title)
        ttk.Label(top, text="Wird später implementiert.").pack(padx=20, pady=20)
        ttk.Button(top, text="OK", command=top.destroy).pack(pady=(0, 20))

    def build_statusbar(self):
        self.status_var = tk.StringVar(value="Keine Datenbank geöffnet. Datei → Öffnen…")
        bar = ttk.Label(self, textvariable=self.status_var, anchor=tk.W)
        bar.pack(side=tk.BOTTOM, fill=tk.X)

    # -------------------------
    # Actions
    # -------------------------
    def menu_open(self):
        path = filedialog.asksaveasfilename(
            title="Datenbank öffnen/neu anlegen",
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db"), ("Alle Dateien", "*.*")],
            initialfile=(os.path.basename(self.settings.last_db_path) if self.settings.last_db_path else "inventory.db"),
        )
        if not path:
            return
        try:
            self.open_db(path)
            self.settings.last_db_path = path
            self.settings.save()
        except Exception as ex:
            messagebox.showerror("Fehler", f"DB konnte nicht geöffnet/angelegt werden: {ex}")

    def open_db(self, path: str):
        self.db.connect(path)
        self.refresh_all()
        from settings.constants import APP_TITLE as TITLE  # avoid import cycle
        self.title(f"{TITLE} — {os.path.abspath(path)}")

    def menu_add_inventory(self):
        from app.ui.dialogs.inventory import AddInventoryDialog
        if not self.db.conn:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Datenbank öffnen.")
            return
        AddInventoryDialog(self, self.db, on_saved=self.refresh_inventory)

    def menu_add_member(self):
        from app.ui.dialogs.member import AddMemberDialog
        if not self.db.conn:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Datenbank öffnen.")
            return
        AddMemberDialog(self, self.db, on_saved=self.refresh_member)

    def menu_add_kleidung(self):
        from app.ui.dialogs.kleidung import AddKleidungDialog
        if not self.db.conn:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Datenbank öffnen.")
            return
        AddKleidungDialog(self, self.db, on_saved=self.refresh_kleidung)

    def menu_manage_vehicles(self):
        if not self.db.conn:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Datenbank öffnen.")
            return
        VehicleManageDialog(self, self.db)

    def menu_psa_soll_liste_fahrzeuge(self):
        from app.ui.dialogs.psa_soll_liste import VehicleSetDialog
        if not self.db.conn:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Datenbank öffnen.")
            return
        VehicleSetDialog(self, self.db)

    def menu_psa_soll_liste_einsatzkraefte(self):
        from app.ui.dialogs.psa_soll_liste import PlaceholderAbortDialog
        PlaceholderAbortDialog(self, "PSA Soll-Liste Einsatzkräfte", "Wird später implementiert.")

    def open_print_dialog(self):
        PrintExportDialog(self, self.db)

    def menu_settings(self):
        ColorRulesDialog(self, self.settings, on_save=self.refresh_inventory)

    def menu_help(self):
        AboutDialog(self)

    def refresh_inventory(self):
        self.inventory_tab.rebuild_color_tags()
        self.inventory_tab.refresh()

    def refresh_member(self):
        self.member_tab.refresh()

    def refresh_kleidung(self):
        self.kleidung_tab.refresh()

    def refresh_all(self):
        self.refresh_inventory()
        self.refresh_member()
        self.refresh_kleidung()

if __name__ == "__main__":
    from app.core.utils import create_folder
    create_folder("./output")
    app = App()
    app.mainloop()
