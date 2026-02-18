import os
import re
import sqlite3
from settings.constants import INVENTORY_COLUMNS, MEMBER_COLUMNS, KLEIDUNG_COLUMNS

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
        # ➕ kleidung
        cur.execute("""CREATE TABLE IF NOT EXISTS kleidung (
            type TEXT,
            gender TEXT,
            size TEXT,
            location TEXT
        );""")

        # ➕ location
        cur.execute("""CREATE TABLE IF NOT EXISTS location (
            location TEXT PRIMARY KEY,
            set_name TEXT,
            database_soll TEXT
        );""")


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


    def list_tables_with_prefix(self, prefix: str) -> list[str]:
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE ? ORDER BY name", (f"{prefix}%",))
        rows = cur.fetchall()
        return [row[0] for row in rows]

    def list_vehicle_sets(self) -> list[str]:
        prefix = "set_vehicle_"
        table_names = self.list_tables_with_prefix(prefix)
        return [name[len(prefix):] for name in table_names]

    def list_location_set_tables(self) -> list[str]:
        return self.list_tables_with_prefix("set_vehicle_")

    def fetch_location_rows(self) -> list[sqlite3.Row]:
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute("SELECT location, set_name, database_soll FROM location ORDER BY location")
        return cur.fetchall()

    def fetch_location_names(self) -> list[str]:
        """Liefert alle vorhandenen Lagerorte aus der Spalte `location`."""
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute(
            "SELECT DISTINCT location FROM location "
            "WHERE location IS NOT NULL AND TRIM(location) <> '' "
            "ORDER BY location"
        )
        return [row[0] for row in cur.fetchall()]

    def fetch_location_set_names(self) -> list[str]:
        """Liefert alle vorhandenen Setnamen aus der Spalte `set_name`."""
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute(
            "SELECT DISTINCT set_name FROM location "
            "WHERE set_name IS NOT NULL AND TRIM(set_name) <> '' "
            "ORDER BY set_name"
        )
        return [row[0] for row in cur.fetchall()]

    def upsert_location(self, location: str, set_name: str, database_soll: str | None):
        assert self.conn is not None
        self.conn.execute(
            """
            INSERT INTO location (location, set_name, database_soll)
            VALUES (?, ?, ?)
            ON CONFLICT(location) DO UPDATE SET
                set_name = excluded.set_name,
                database_soll = excluded.database_soll
            """,
            (location, set_name or None, database_soll or None),
        )
        self.conn.commit()

    def delete_location(self, location: str):
        assert self.conn is not None
        self.conn.execute("DELETE FROM location WHERE location = ?", (location,))
        self.conn.commit()

    def create_vehicle_set_table(self, table_name: str):
        assert self.conn is not None
        if not re.fullmatch(r"\w+", table_name):
            raise ValueError("Ungültiger Tabellenname")
        self.conn.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
            product_type TEXT,
            property_1 TEXT,
            property_2 TEXT,
            count INTEGER
        );""")
        self.conn.commit()

    def _validate_table_name(self, table_name: str):
        if not re.fullmatch(r"\w+", table_name):
            raise ValueError("Ungültiger Tabellenname")

    def fetch_vehicle_set_rows(self, table_name: str) -> list[sqlite3.Row]:
        assert self.conn is not None
        self._validate_table_name(table_name)
        cur = self.conn.cursor()
        cur.execute(
            f"SELECT rowid, product_type, property_1, property_2, count FROM {table_name} "
            "ORDER BY product_type, property_1, property_2"
        )
        return cur.fetchall()

    def insert_vehicle_set_row(self, table_name: str, product_type: str, property_1: str, property_2: str, count: int):
        assert self.conn is not None
        self._validate_table_name(table_name)
        self.conn.execute(
            f"INSERT INTO {table_name} (product_type, property_1, property_2, count) VALUES (?, ?, ?, ?)",
            (product_type, property_1, property_2, count),
        )
        self.conn.commit()

    def update_vehicle_set_row_count(self, table_name: str, row_id: int, count: int):
        assert self.conn is not None
        self._validate_table_name(table_name)
        self.conn.execute(f"UPDATE {table_name} SET count = ? WHERE rowid = ?", (count, row_id))
        self.conn.commit()

    def get_inventory_product_types(self) -> list[str]:
        return self.get_distinct_values("inventory", "product_type")

    def get_inventory_property1_for_type(self, product_type: str) -> list[str]:
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT property_1
            FROM inventory
            WHERE product_type = ? AND property_1 IS NOT NULL AND property_1 <> ''
            ORDER BY property_1
            """,
            (product_type,),
        )
        return [row[0] for row in cur.fetchall()]

    def get_inventory_property2_for_type_and_property1(self, product_type: str, property_1: str) -> list[str]:
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT property_2
            FROM inventory
            WHERE product_type = ?
              AND property_1 = ?
              AND property_2 IS NOT NULL
              AND property_2 <> ''
            ORDER BY property_2
            """,
            (product_type, property_1),
        )
        return [row[0] for row in cur.fetchall()]

    def get_inventory_distinct_by_filters(
        self,
        column: str,
        location: str | None = None,
        product_type: str | None = None,
        property_1: str | None = None,
    ) -> list[str]:
        assert self.conn is not None
        allowed_columns = {"location", "product_type", "property_1", "property_2"}
        if column not in allowed_columns:
            raise ValueError("Ungültige Spalte")

        query = [
            f"SELECT DISTINCT {column} FROM inventory",
            f"WHERE {column} IS NOT NULL AND TRIM({column}) <> ''",
        ]
        params: list[str] = []

        if location:
            query.append("AND location = ?")
            params.append(location)
        if product_type:
            query.append("AND product_type = ?")
            params.append(product_type)
        if property_1:
            query.append("AND property_1 = ?")
            params.append(property_1)

        query.append(f"ORDER BY {column}")
        cur = self.conn.cursor()
        cur.execute(" ".join(query), tuple(params))
        return [row[0] for row in cur.fetchall()]

    def fetch_inventory_for_psa_check(
        self,
        location: str,
        product_type: str | None = None,
        property_1: str | None = None,
        property_2: str | None = None,
    ) -> list[sqlite3.Row]:
        assert self.conn is not None
        query = [
            """
            SELECT ID, product_type, property_1, property_2, serial_number, check_date, psa_check
            FROM inventory
            WHERE location = ?
            """
        ]
        params: list[str] = [location]

        if product_type:
            query.append("AND product_type = ?")
            params.append(product_type)
        if property_1:
            query.append("AND property_1 = ?")
            params.append(property_1)
        if property_2:
            query.append("AND property_2 = ?")
            params.append(property_2)

        query.append("ORDER BY ID")

        cur = self.conn.cursor()
        cur.execute(" ".join(query), tuple(params))
        return cur.fetchall()

    def update_inventory_psa_check_dates(self, ids: list[str], check_date: str):
        assert self.conn is not None
        if not ids:
            return
        self.conn.executemany(
            "UPDATE inventory SET check_date = ?, psa_check = 1 WHERE ID = ?",
            [(check_date, item_id) for item_id in ids],
        )
        self.conn.commit()

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

    # ---- Kleidung ----
    def fetch_all_kleidung(self) -> list[sqlite3.Row]:
        assert self.conn is not None
        cur = self.conn.cursor()
        cur.execute("SELECT rowid, type, gender, size, location FROM kleidung ORDER BY type, gender, size, location")
        return cur.fetchall()

    def insert_kleidung(self, record: dict):
        assert self.conn is not None
        cols = [c for c, _ in KLEIDUNG_COLUMNS]
        placeholders = ",".join(["?"] * len(cols))
        values = [record.get(c) for c in cols]
        self.conn.execute(f"INSERT INTO kleidung ({','.join(cols)}) VALUES ({placeholders})", values)

    def update_kleidung(self, row_id: int, record: dict):
        assert self.conn is not None
        cols = [c for c, _ in KLEIDUNG_COLUMNS]
        set_clause = ",".join([f"{c}=?" for c in cols])
        values = [record.get(c) for c in cols] + [row_id]
        self.conn.execute(f"UPDATE kleidung SET {set_clause} WHERE rowid = ?", values)

    def delete_kleidung(self, row_id: int):
        assert self.conn is not None
        self.conn.execute("DELETE FROM kleidung WHERE rowid = ?", (row_id,))
        self.conn.commit()
