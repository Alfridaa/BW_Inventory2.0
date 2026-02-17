#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import datetime as dt
import sqlite3
import sys
from typing import Optional

DEFAULT_LOCATION = "/Depot/"

INVENTORY_COLUMNS = [
    ("ID", "TEXT PRIMARY KEY"),
    ("product_type", "TEXT"),
    ("property_1", "TEXT"),
    ("property_2", "TEXT"),
    ("producer", "TEXT"),
    ("product_name", "TEXT"),
    ("serial_number", "TEXT"),
    ("location", "TEXT"),
    ("manufactury_date", "TEXT"),  # store YYYY-MM-DD
    ("check_date", "TEXT"),        # store YYYY-MM-DD
    ("life_time", "INTEGER"),
    ("psa_check", "INTEGER")       # 0/1
]

MEMBER_COLUMNS = [
    ("ID", "TEXT PRIMARY KEY"),
    ("first_name", "TEXT"),
    ("last_name", "TEXT"),
    ("AEK", "INTEGER"),
    ("ET_SO", "INTEGER"),
    ("ET_WI", "INTEGER"),
    ("PR_SO", "INTEGER"),
    ("PR_WI", "INTEGER"),
    ("NFM", "INTEGER"),
    ("LR", "INTEGER"),
    ("EL", "INTEGER"),
]

def parse_args():
    p = argparse.ArgumentParser(description="Migriert Tabellen 'inventory' und 'members' ins neue Schema.")
    p.add_argument("old_db", help="Pfad zur alten SQLite-DB")
    p.add_argument("new_db", help="Pfad zur neuen SQLite-DB (wird erstellt/ergänzt)")
    p.add_argument("--dry-run", action="store_true", help="Nur prüfen, nichts schreiben")
    p.add_argument("--replace", action="store_true", help="Zieltabellen löschen, falls vorhanden")
    return p.parse_args()

def normalize_date(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, (int, float)):
        try:
            return dt.datetime.utcfromtimestamp(int(value)).date().isoformat()
        except Exception:
            return None
    s = str(value).strip()
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s).isoformat()
    except Exception:
        pass
    for fmt in ("%d.%m.%Y", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y", "%Y.%m.%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            continue
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
    except Exception:
        return None
# NEU: Helper – state -> AEK (int)
def state_to_aek(value) -> int:
    if value is None:
        return 0
    s = str(value).strip().upper()
    if s == "AEK":
        return 1
    if s == "ANW":
        return 0
    # Unbekannt -> konservativ 0
    return 0

def bool_to_int(val) -> int:
    if val is None:
        return 0
    if isinstance(val, (int, bool)):
        return 1 if int(val) != 0 else 0
    return 1 if str(val).strip().lower() in {"1", "true", "yes", "y", "t"} else 0

def table_exists(cur, name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return cur.fetchone() is not None

def ensure_clean_table(cur, name: str, columns, replace: bool):
    if table_exists(cur, name):
        if not replace:
            raise RuntimeError(f"Zieltabelle '{name}' existiert bereits. Mit --replace überschreiben.")
        cur.execute(f"DROP TABLE {name};")
    cols_sql = ", ".join([f"{n} {t}" for n, t in columns])
    cur.execute(f"CREATE TABLE {name} ( {cols_sql} );")

def fetch_all(cur, sql: str):
    cur.execute(sql)
    colnames = [d[0] for d in cur.description]
    return colnames, cur.fetchall()

def migrate_inventory(cur_src, cur_dst, dry_run=False):
    if not table_exists(cur_src, "inventory"):
        print("Hinweis: 'inventory' in alter DB nicht gefunden – übersprungen.")
        return 0
    ensure_clean_table(cur_dst, "inventory", INVENTORY_COLUMNS, replace=args.replace)

    sql = """
        SELECT
            ID,
            "type",
            property_1,
            property_2,
            product,
            producer,
            serial_number,
            rfid,
            storage_location,
            manufacturing_date,
            expiry_date,
            lifetime,
            check_date,
            next_check,
            state
        FROM inventory;
    """
    colnames, rows = fetch_all(cur_src, sql)
    idx = {n: i for i, n in enumerate(colnames)}

    ins_cols = ", ".join([n for n, _ in INVENTORY_COLUMNS])
    placeholders = ", ".join(["?"] * len(INVENTORY_COLUMNS))
    inserted = 0

    for r in rows:
        def get(name): return r[idx[name]] if name in idx else None
        row = {
            "ID":               get("ID"),
            "product_type":     get("type"),
            "property_1":       get("property_1"),
            "property_2":       get("property_2"),
            "producer":         get("producer"),
            "product_name":     get("product"),
            "serial_number":    get("serial_number"),
            "location":         (get("storage_location") or DEFAULT_LOCATION),
            "manufactury_date": normalize_date(get("manufacturing_date")),
            "check_date":       normalize_date(get("check_date")),
            "life_time":        get("lifetime"),
            "psa_check":        bool_to_int(get("state")),
        }
        if not dry_run:
            cur_dst.execute(f"INSERT INTO inventory ({ins_cols}) VALUES ({placeholders});",
                            [row[k] for k, _ in INVENTORY_COLUMNS])
        inserted += 1

    return inserted

def migrate_members(cur_src, cur_dst, dry_run=False):
    if not table_exists(cur_src, "members"):
        print("Hinweis: 'members' in alter DB nicht gefunden – übersprungen.")
        return 0
    # Zieltabelle heißt 'member'
    ensure_clean_table(cur_dst, "member", MEMBER_COLUMNS, replace=args.replace)

    sql = """
        SELECT
            first_name,
            last_name,
            member_id,
            state,
            ET_SO,
            ET_WI,
            NFM,
            PR_SO,
            PR_WI,
            EL,
            LR,
            Arzt,
            availability
        FROM members;
    """
    colnames, rows = fetch_all(cur_src, sql)
    idx = {n: i for i, n in enumerate(colnames)}

    ins_cols = ", ".join([n for n, _ in MEMBER_COLUMNS])
    placeholders = ", ".join(["?"] * len(MEMBER_COLUMNS))
    inserted = 0

    for r in rows:
        def get(name): return r[idx[name]] if name in idx else None

        row = {
            "ID":         get("member_id"),
            "first_name": get("first_name"),
            "last_name":  get("last_name"),
            # NEU: AEK aus 'state' ableiten
            "AEK":        state_to_aek(get("state")),
            "ET_SO":      bool_to_int(get("ET_SO")),
            "ET_WI":      bool_to_int(get("ET_WI")),
            "PR_SO":      bool_to_int(get("PR_SO")),
            "PR_WI":      bool_to_int(get("PR_WI")),
            "NFM":        bool_to_int(get("NFM")),
            "LR":         bool_to_int(get("LR")),
            "EL":         bool_to_int(get("EL")),
        }

        if not dry_run:
            cur_dst.execute(
                f"INSERT INTO member ({ins_cols}) VALUES ({placeholders});",
                [row[k] for k, _ in MEMBER_COLUMNS]
            )
        inserted += 1

    return inserted


def main():
    global args
    args = parse_args()

    conn_src = sqlite3.connect(args.old_db)
    conn_dst = sqlite3.connect(args.new_db)

    try:
        cur_src = conn_src.cursor()
        cur_dst = conn_dst.cursor()

        inv_count = migrate_inventory(cur_src, cur_dst, dry_run=args.dry_run)
        mem_count = migrate_members(cur_src, cur_dst, dry_run=args.dry_run)

        if args.dry_run:
            conn_dst.rollback()
            print(f"[Dry-Run] inventory: würde {inv_count} Zeilen migrieren.")
            print(f"[Dry-Run] member:    würde {mem_count} Zeilen migrieren.")
        else:
            conn_dst.commit()
            print(f"inventory: {inv_count} Zeilen migriert.")
            print(f"member:    {mem_count} Zeilen migriert.")

    except Exception as e:
        conn_dst.rollback()
        print(f"FEHLER: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn_src.close()
        conn_dst.close()

if __name__ == "__main__":
    main()

