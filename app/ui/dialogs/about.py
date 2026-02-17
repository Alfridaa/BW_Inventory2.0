import tkinter as tk
from tkinter import ttk
from settings.constants import APP_TITLE, APP_VERSION

class AboutDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Über diese Anwendung")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        frm = ttk.Frame(self, padding=16)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text=APP_TITLE, font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(frm, text=APP_VERSION, font=("Arial", 10)).grid(row=1, column=1, sticky="w", pady=(4,0))

        ttk.Label(frm, text="© 2025 Rainer Walther / RW Holzdesign & Solutions\nAlle Rechte vorbehalten.",
                  font=("Arial", 9)).grid(row=2, column=1, sticky="w", pady=(6,0))

        ttk.Button(frm, text="OK", command=self.destroy).grid(row=3, column=0, columnspan=2, pady=(16,0))
        self.update_idletasks()
        self.wait_visibility()
        self.focus_force()
