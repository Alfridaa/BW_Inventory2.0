# utils/pdf_export.py
# -*- coding: utf-8 -*-
import os
from typing import List, Dict, Iterable, Sequence, Tuple, Optional
from fpdf import FPDF
from settings.constants import MEMBER_COLUMNS
from settings.constants import INVENTORY_COLUMNS

# -----------------------------
# Column definitions (importiere bei dir aus settings.constants)
# -----------------------------
# from settings.constants import INVENTORY_COLUMNS, MEMBER_COLUMNS

# Hilfstypen
ColumnDef = Sequence[Tuple[str, str]]  # z.B. INVENTORY_COLUMNS
RowType = Dict[str, str]               # keys = Spaltennamen (erste Elemente aus ColumnDef)


class _PDF(FPDF):
    def __init__(self, title: str, logo_path: Optional[str] = None):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.title_text = title
        self.logo_path = logo_path

    def header(self):
        # Logo (optional)
        if self.logo_path and os.path.exists(self.logo_path):
            # x=250 passt für Querformat A4; zur Not anpassen
            self.image(self.logo_path, x=250, y=8, w=33)
        # Titel
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "", 0, 1)  # Leerzeile
        self.cell(200, 10, self.title_text, 1, 0, "C")
        self.ln(30)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Seite {self.page_no()}/{{nb}}", 0, 0, "C")


def _normalize_columns(columns: ColumnDef) -> List[str]:
    """
    Nimmt INVENTORY_COLUMNS/MEMBER_COLUMNS und gibt nur die sichtbaren
    Spaltennamen (erste Elemente) zurück.
    """
    return [col[0] for col in columns]


def _ensure_output_dir(path: str):
    out_dir = os.path.dirname(os.path.abspath(path))
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)


def _calc_col_widths(pdf: FPDF, headers: List[str], rows: Iterable[RowType],
                     key_order: List[str], base_width: float) -> List[float]:
    """
    Ermittelt einfache Spaltenbreiten:
    - Start mit gleicher Breite (base_width)
    - Erweitert minimal anhand längster Zelle (Textbreite)
    - Begrenzung per min/max, damit es hübsch bleibt
    """
    pdf.set_font("Arial", "B", 10)
    # Textbreiten messen
    max_text_mm = [pdf.get_string_width(h) for h in headers]

    pdf.set_font("Arial", "", 8)
    for row in rows:
        for i, key in enumerate(key_order):
            txt = str(row.get(key, "") if row.get(key, "") is not None else "")
            w = pdf.get_string_width(txt)
            if w > max_text_mm[i]:
                max_text_mm[i] = w

    # Polster addieren
    paddings = [8.0] * len(headers)
    widths = [max(base_width, max_text_mm[i] + paddings[i]) for i in range(len(headers))]

    # sanfte Min/Max-Grenzen
    widths = [min(max(12.0, w), 55.0) for w in widths]
    return widths


def _apply_width_overrides(headers: List[str], widths: List[float],
                           overrides: Optional[Dict[str, float]]) -> List[float]:
    """
    Erlaubt fixe Spaltenbreiten per Name-Override, z. B. {"ID": 12, "serial_number": 30}
    """
    if not overrides:
        return widths
    name_to_idx = {h: i for i, h in enumerate(headers)}
    for name, w in overrides.items():
        if name in name_to_idx:
            widths[name_to_idx[name]] = w
    return widths


def export_table_to_pdf(
    pdf_title: str,
    columns: ColumnDef,
    rows: Iterable[RowType],
    out_path: str,
    *,
    logo_path: Optional[str] = "bw_logo_large.png",
    footer_lines: Optional[List[str]] = None,
    width_overrides: Optional[Dict[str, float]] = None,
) -> str:
    """
    Generischer PDF-Export für tabellarische Daten.
    - columns: z. B. INVENTORY_COLUMNS (nur die Namen werden verwendet)
    - rows: Iterable von Dicts mit Keys passend zu den Spaltennamen
    - out_path: z. B. './output/inventar_export.pdf'
    - width_overrides: optionale fixe Breiten pro Spaltenname in mm
    - footer_lines: optionale Zusatzzeilen am Ende (zentriert + Unterschriftzeilen)
    """
    headers = _normalize_columns(columns)
    key_order = headers[:]  # gleiche Reihenfolge

    # PDF
    pdf = _PDF(pdf_title, logo_path=logo_path)
    pdf.alias_nb_pages()
    pdf.add_page("L")
    pdf.set_auto_page_break(auto=True, margin=15)

    # Layout-Basics
    pdf.set_font("Arial", "B", 10)
    epw = pdf.w - 2 * pdf.l_margin  # Effective page width
    base_col_width = epw / max(1, len(headers))
    row_height = pdf.font_size * 1.5
    spacing = 1.3

    # rows als Liste materialisieren, weil wir sie mehrfach brauchen
    rows_list = list(rows)

    # Spaltenbreiten berechnen + Overrides anwenden
    widths = _calc_col_widths(pdf, headers, rows_list, key_order, base_col_width)
    widths = _apply_width_overrides(headers, widths, width_overrides)

    # Tabellenkopf
    for hdr, w in zip(headers, widths):
        pdf.cell(w, row_height * spacing, txt=hdr, border=1)
    pdf.ln(row_height * spacing)

    # Tabellendaten
    pdf.set_font("Arial", "", 8)
    for row in rows_list:
        for key, w in zip(key_order, widths):
            val = row.get(key, "")
            txt = "" if val is None else str(val)
            pdf.cell(w, row_height * spacing, txt=txt, border=1)
        pdf.ln(row_height * spacing)

    # Optionale Footer-Zeilen (z. B. Prüfdokumente / Übergabeprotokoll)
    if footer_lines:
        pdf.cell(0, 10, "", 0, 1)  # Abstand
        pdf.set_font("Arial", "", 10)
        for line in footer_lines:
            align = "C"  # Standard zentriert
            border = 0
            # einfache Heuristik für Unterschrift-Zeilen
            if "Unterschrift" in line or "Ort/Datum" in line:
                align = "R"
                border = "T"
            pdf.cell(0, 10, line, border, 1, align)

    # Schreiben
    _ensure_output_dir(out_path)
    pdf.output(out_path, "F")
    return out_path


# --------------------------------
# Komfort-Wrapper für deine Tabellen
# --------------------------------
def export_inventory_pdf(
    rows: Iterable[RowType],
    filename: str,
    *,
    title: str = "Inventarübersicht",
    logo_path: Optional[str] = "bw_logo_large.png",
) -> str:
    # Beispielhafte Fixbreiten, falls du einzelne Spalten ähnlich wie früher
    # strenger layouten möchtest:
    width_overrides = {
        "ID": 14,
        "serial_number": 30,
        "location": 30,
        "producer": 28,
        "product_type": 26,
        "product_name": 32,
        "manufactury_date": 26,
        "check_date": 26,
    }
    footer = [
        "Geprüft am:",
        "Ort/Datum              Unterschrift",
    ]
    return export_table_to_pdf(
        pdf_title=title,
        columns=INVENTORY_COLUMNS,  # aus settings.constants importieren
        rows=rows,
        out_path=filename,
        logo_path=logo_path,
        footer_lines=footer,
        width_overrides=width_overrides,
    )


def export_members_pdf(
    rows: Iterable[RowType],
    filename: str,
    *,
    title: str = "Mitgliederübersicht",
    logo_path: Optional[str] = "bw_logo_large.png",
) -> str:
    width_overrides = {
        "ID": 18,
        "first_name": 28,
        "last_name": 28,
    }
    footer = [
        "Erstellt am:",
        "Ort/Datum              Unterschrift",
    ]
    return export_table_to_pdf(
        pdf_title=title,
        columns=MEMBER_COLUMNS,     # aus settings.constants importieren
        rows=rows,
        out_path=filename,
        logo_path=logo_path,
        footer_lines=footer,
        width_overrides=width_overrides,
    )
