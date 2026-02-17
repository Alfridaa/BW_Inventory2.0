# -----------------------------
# App metadata
# -----------------------------
APP_TITLE = "Bergwacht Material Manager"
APP_VERSION = "Version 0.0.2"  # +psa/kleidung

SETTINGS_FILE = "settings.cfg"
ID_LIST_FILE = "./output/id_list.csv"

# -----------------------------
# Database column definitions
# -----------------------------

# inventory
INVENTORY_COLUMNS = [
    ("ID", "TEXT PRIMARY KEY"),
    ("product_type", "TEXT"),
    ("property_1", "TEXT"),
    ("property_2", "TEXT"),
    ("producer", "TEXT"),
    ("product_name", "TEXT"),
    ("serial_number", "TEXT"),
    ("location", "TEXT"),
    ("manufactury_date", "TEXT"),  # YYYY-MM-DD
    ("check_date", "TEXT"),        # YYYY-MM-DD
    ("life_time", "INTEGER"),
    ("psa_check", "INTEGER")       # 0/1
]

# member
MEMBER_COLUMNS = [
    ("ID", "TEXT PRIMARY KEY"),
    ("first_name", "TEXT"),
    ("last_name", "TEXT"),
    ("ET_SO", "INTEGER"),
    ("ET_WI", "INTEGER"),
    ("PR_SO", "INTEGER"),
    ("PR_WI", "INTEGER"),
    ("NFM", "INTEGER"),
    ("LR", "INTEGER"),
    ("EL", "INTEGER")
]

# psa (Persönliche Schutzausrüstung)
PSA_COLUMNS = [
    ("count", "INTEGER"),
    ("type", "TEXT"),          # varchar(20) -> TEXT
    ("property_1", "TEXT"),    # varchar(20) -> TEXT
    ("property_2", "TEXT"),    # varchar(20) -> TEXT
    ("state", "TEXT"),         # varchar(5)  -> TEXT
    ("ET_SO", "INTEGER"),
    ("ET_WI", "INTEGER"),
    ("PR_SO", "INTEGER"),
    ("PR_WI", "INTEGER"),
    ("NFM", "INTEGER"),
    ("LR", "INTEGER"),
    ("EL", "INTEGER")
]

# kleidung
KLEIDUNG_COLUMNS = [
    ("type", "TEXT"),
    ("gender", "TEXT"),
    ("size", "TEXT"),
    ("location", "TEXT"),
]

# -----------------------------
# Helper: reine Spaltennamen (optional)
# -----------------------------
INVENTORY_COLNAMES = [c for c, _ in INVENTORY_COLUMNS]
MEMBER_COLNAMES    = [c for c, _ in MEMBER_COLUMNS]
PSA_COLNAMES       = [c for c, _ in PSA_COLUMNS]
KLEIDUNG_COLNAMES  = [c for c, _ in KLEIDUNG_COLUMNS]
