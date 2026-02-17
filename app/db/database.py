import os
import sqlite3
from settings.constants import INVENTORY_COLUMNS, MEMBER_COLUMNS

class Database:
    def __init__(self):
        self.conn: sqlite3.Connection | None = None
        self.path: str | None = None

    def connect(self, path: str):
        need_create = not os.path.exists(path)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.path = path
        self.ensure_schema()

    def ensure_schema(self):
        assert self.conn is not None
        cur = self.conn.cursor()
        # inventory
        cur.execute("""CREATE TABLE IF NOT EXISTS inventory (
            ID TEXT PRIMARY KEY,
            product_type TEXT,
            property_1 TEXT,
            property_2 TEXT,
            producer TEXT,
            product_name TEXT,
            serial_number TEXT,
            location TEXT,
            manufactury_date TEXT,
            check_date TEXT,
            life_time INTEGER,
            psa_check INTEGER
        );""")
        # member
        cur.execute("""CREATE TABLE IF NOT EXISTS member (
            ID TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            ET_SO INTEGER,
            ET_WI INTEGER,
            PR_SO INTEGER,
            PR_WI INTEGER,
            NFM INTEGER,
            LR INTEGER,
            EL INTEGER
        );""")
        # ➕ psa
        cur.execute("""CREATE TABLE IF NOT EXISTS psa (
            count INTEGER,
            type TEXT,
            property_1 TEXT,
            property_2 TEXT,
            state TEXT,
            ET_SO INTEGER,
            ET_WI INTEGER,
            PR_SO INTEGER,
            PR_WI INTEGER,
            NFM INTEGER,
            LR INTEGER,
            EL INTEGER
        );""")
        # ➕ jacken
        cur.execute("""CREATE TABLE IF NOT EXISTS jacken (
            type TEXT,
            gender TEXT,
            size TEXT,
            location TEXT
        );""")
        self.conn.commit()


    def fetch_all(self, table: str) -> list[sqlite3.Row]:
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM {table}")
        return cur.fetchall()

    def fetch_by_id(self, table: str, id_val: str):
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM {table} WHERE ID = ?", (id_val,))
        return cur.fetchone()

    def get_distinct_values(self, table: str, column: str) -> list[str]:
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL AND {column} <> ''")
        vals = [row[0] for row in cur.fetchall() if row[0] is not None]
        return sorted({str(v) for v in vals})

    def id_exists(self, table: str, id_val: str) -> bool:
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute(f"SELECT 1 FROM {table} WHERE ID = ?", (id_val,))
        return cur.fetchone() is not None

    def insert_inventory(self, record: dict):
        assert self.conn is not None
        cols = [c for c, _ in INVENTORY_COLUMNS]
        placeholders = ",".join(["?"] * len(cols))
        values = [record.get(c) for c in cols]
        self.conn.execute(f"INSERT INTO inventory ({','.join(cols)}) VALUES ({placeholders})", values)

    def update_inventory(self, id_val: str, record: dict):
        assert self.conn is not None
        cols = [c for c, _ in INVENTORY_COLUMNS if c != "ID"]
        set_clause = ",".join([f"{c}=?" for c in cols])
        values = [record.get(c) for c in cols] + [id_val]
        self.conn.execute(f"UPDATE inventory SET {set_clause} WHERE ID = ?", values)

    def delete_inventory(self, id_val: str):
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute("DELETE FROM inventory WHERE ID = ?", (id_val,))
        self.conn.commit()

    def get_inventory_ids(self):
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute("SELECT ID FROM inventory ORDER BY ID")
        rows = cur.fetchall()
        return [row[0] for row in rows]

    def insert_member(self, record: dict):
        assert self.conn is not None
        cols = [c for c, _ in MEMBER_COLUMNS]
        placeholders = ",".join(["?"] * len(cols))
        values = [record.get(c) for c in cols]
        self.conn.execute(f"INSERT INTO member ({','.join(cols)}) VALUES ({placeholders})", values)

    def update_member(self, id_val: str, record: dict):
        assert self.conn is not None
        cols = [c for c, _ in MEMBER_COLUMNS if c != "ID"]
        set_clause = ",".join([f"{c}=?" for c in cols])
        values = [record.get(c) for c in cols] + [id_val]
        self.conn.execute(f"UPDATE member SET {set_clause} WHERE ID = ?", values)

    def delete_member(self, id_val: str):
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute("DELETE FROM member WHERE ID = ?", (id_val,))
        self.conn.commit()

    def get_member_ids(self):
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute("SELECT ID FROM member ORDER BY ID")
        rows = cur.fetchall()
        return [row[0] for row in rows]

    def commit(self):
        assert self.conn is not None
        self.conn.commit()
        
    def get_members_basic(self) -> list[dict]:
        """
        Gibt eine Liste von Mitgliedern zurück, jeweils als Dict mit:
        {"ID": str, "first_name": str | None, "last_name": str | None}
        Sortiert nach last_name, first_name.
        """
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute("SELECT ID, first_name, last_name FROM member ORDER BY last_name, first_name;")
        rows = cur.fetchall()
        # row_factory = sqlite3.Row -> Zugriff per Spaltennamen möglich
        return [{"ID": r["ID"], "first_name": r["first_name"], "last_name": r["last_name"]} for r in rows]

    def get_inventory_for_member(self, member_id: str, columns: list[str]) -> list[dict]:
        """
        Holt Inventarzeilen für location = member_id und gibt nur die gewünschten Spalten zurück.
        columns: Liste der Spaltennamen, z.B. ["ID","product_type","property_1",...]
        """
        assert self.conn is not None
        if not columns:
            columns = [c for c, _ in INVENTORY_COLUMNS]
        cols_sql = ", ".join(columns)
        cur = self.conn.cursor()
        cur.execute(f"SELECT {cols_sql} FROM inventory WHERE location = ? ORDER BY product_type, product_name, ID;", (member_id,))
        rows = cur.fetchall()
        # In Dicts mappen (dank row_factory geht Name-basiert)
        return [{col: row[col] for col in columns} for row in rows]
    
        # ---- PSA ----
    def fetch_all_psa(self) -> list[sqlite3.Row]:
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM psa")
        return cur.fetchall()

    def insert_psa(self, record: dict):
        assert self.conn is not None
        cols = ["count","type","property_1","property_2","state",
                "ET_SO","ET_WI","PR_SO","PR_WI","NFM","LR","EL"]
        placeholders = ",".join(["?"] * len(cols))
        values = [record.get(c) for c in cols]
        self.conn.execute(f"INSERT INTO psa ({','.join(cols)}) VALUES ({placeholders})", values)

    def delete_psa(self, type_val: str):
        """Beispiel: löscht alle Zeilen eines bestimmten Typs"""
        assert self.conn is not None
        self.conn.execute("DELETE FROM psa WHERE type = ?", (type_val,))
        self.conn.commit()

    # ---- Jacken ----
    def fetch_all_jacken(self) -> list[sqlite3.Row]:
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM jacken")
        return cur.fetchall()

    def insert_jacke(self, record: dict):
        assert self.conn is not None
        cols = ["type","gender","size","location"]
        placeholders = ",".join(["?"] * len(cols))
        values = [record.get(c) for c in cols]
        self.conn.execute(f"INSERT INTO jacken ({','.join(cols)}) VALUES ({placeholders})", values)

    def delete_jacken_by_type(self, type_val: str):
        assert self.conn is not None
        self.conn.execute("DELETE FROM jacken WHERE type = ?", (type_val,))
        self.conn.commit()
