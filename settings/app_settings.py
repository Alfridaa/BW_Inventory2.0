import os
import json
import configparser
from .constants import SETTINGS_FILE

class AppSettings:
    def __init__(self, path: str = SETTINGS_FILE):
        self.path = path
        self.config = configparser.ConfigParser()
        self.last_db_path: str | None = None
        # list of dicts: {"description": str, "hex": str, "months": int}
        self.color_rules: list[dict] = []
        self.load()

    def load(self):
        if os.path.exists(self.path):
            self.config.read(self.path, encoding="utf-8")
            self.last_db_path = self.config.get("app", "last_db_path", fallback=None)
            rules_json = self.config.get("colors", "rules", fallback="")
            if rules_json:
                try:
                    self.color_rules = json.loads(rules_json)
                except Exception:
                    self.color_rules = []
        if not self.color_rules:
            # sensible defaults
            self.color_rules = [
                {"description": "Überfällig", "hex": "#FD3A3A", "months": -1},
                {"description": "Bald Überfällig", "hex": "#FFCCCC", "months": 0},
                {"description": "Bald fällig", "hex": "#FFEA8D", "months": 1},
                {"description": "Normal", "hex": "#FFFFFF", "months": 11},
                {"description": "Neu/Geprüft", "hex": "#B8E7A7", "months": 12},
            ]

    def save(self):
        if not self.config.has_section("app"):
            self.config.add_section("app")
        if not self.config.has_section("colors"):
            self.config.add_section("colors")
        if self.last_db_path:
            self.config.set("app", "last_db_path", self.last_db_path)
        self.config.set("colors", "rules", json.dumps(self.color_rules, ensure_ascii=False))
        with open(self.path, "w", encoding="utf-8") as f:
            self.config.write(f)
