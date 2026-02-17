import os
import random
from pathlib import Path
from datetime import datetime, date
from tkinter import messagebox
from typing import Optional

def today_str() -> str:
    return date.today().strftime("%Y-%m-%d")

def parse_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

def months_until_expiry(check_date: date) -> int:
    today = date.today()
    months = (today.year - check_date.year) * 12 + (today.month - check_date.month)
    return 12 - months

def random_hex_color():
    r = random.randint(96, 224)
    g = random.randint(96, 224)
    b = random.randint(96, 224)
    return f"#{r:02x}{g:02x}{b:02x}"

def create_folder(path: str) -> Path:
    folder = Path(path)
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)
    return folder

def append_line(filepath: str, text: str):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def delete_file(filepath: str):
    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass
    except PermissionError:
        messagebox.showerror("Fehler", f"Keine Berechtigung zum Löschen: : {filepath}")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Löschen von {filepath}: {e}")

# ---------- ID-Generatoren ----------

def generate_next_valid_id_item(old_list_id):
    list_digit_item = ['0','1','2','3','4','5','6','7','8','9',
                       'A','B','C','D','E','F','G','H','I','J',
                       'K','L','M','N','P','Q','R','S','T','U',
                       'V','W','X','Y','Z']
    generate = 1
    digit_0 = 1
    digit_1 = 0
    digit_2 = 0

    list_id = []
    old_id = ""
    for idv in old_list_id:
        if len(idv) > 3:
            idv = idv[:3]
            if idv != old_id:
                list_id.append(idv)
                old_id = idv
        else:
            list_id.append(idv)

    while generate:
        bool_id_founded = 0
        new_id = list_digit_item[digit_2] + list_digit_item[digit_1] + list_digit_item[digit_0]
        for idv in list_id:
            if idv == new_id:
                bool_id_founded = 1
                break
        if bool_id_founded == 1:
            digit_0 += 1
            if digit_0 > len(list_digit_item)-1:
                digit_0 = 0
                digit_1 += 1
                if digit_1 > len(list_digit_item)-1:
                    digit_1 = 0
                    digit_2 += 1
                    if digit_2 > len(list_digit_item)-1:
                        digit_0 = digit_1 = digit_2 = 0
                        generate = 0
                        return -1
        else:
            generate = 0
            break
    return new_id

def generate_next_valid_id_member(old_list_id):
    list_digit_member = ['0','1','2','3','4','5','6','7','8','9']
    generate = 1
    digit_0 = 1
    digit_1 = 0

    list_id = []
    old_id = ""
    for idv in old_list_id:
        if len(idv) > 4:
            idv = idv[:4]
            if idv != old_id:
                list_id.append(idv)
                old_id = idv
        else:
            list_id.append(idv)

    while generate:
        bool_id_founded = 0
        new_id = "NR" + list_digit_member[digit_1] + list_digit_member[digit_0]
        for idv in list_id:
            if idv == new_id:
                bool_id_founded = 1
                break
        if bool_id_founded == 1:
            digit_0 += 1
            if digit_0 > len(list_digit_member)-1:
                digit_0 = 0
                digit_1 += 1
                if digit_1 > len(list_digit_member)-1:
                    digit_0 = digit_1 = 0
                    generate = 0
                    return -1
        else:
            generate = 0
            break
    return new_id
