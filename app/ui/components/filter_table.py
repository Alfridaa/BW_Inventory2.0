import tkinter as tk
from tkinter import ttk

class FilterTable(ttk.Frame):
    def __init__(self, master, columns: list[str], *, bool_columns: set[str] | None = None):
        super().__init__(master)
        self.columns = columns
        self.bool_columns = bool_columns or set()
        self.filter_vars: dict[str, tk.StringVar] = {}

        filt_frame = ttk.Frame(self)
        filt_frame.pack(fill=tk.X)

        # Header + Filter-Entries
        for j, col in enumerate(self.columns):
            lbl = ttk.Label(filt_frame, text=col, font=("TkDefaultFont", 9, "bold"))
            lbl.grid(row=0, column=j, sticky="we", padx=2, pady=(4, 0))
            var = tk.StringVar()
            ent = ttk.Entry(filt_frame, textvariable=var)
            ent.grid(row=1, column=j, sticky="we", padx=2, pady=(0, 4))
            ent.bind("<KeyRelease>", lambda e: self.event_generate("<<FilterChanged>>"))
            self.filter_vars[col] = var
            filt_frame.grid_columnconfigure(j, weight=1, uniform="col")

        # Treeview
        self.tree = ttk.Treeview(self, columns=self.columns, show="headings")
        for c in self.columns:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, anchor=tk.W)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        vsb.pack(fill=tk.Y, side=tk.LEFT)
        hsb.pack(fill=tk.X)

    def get_filters(self) -> dict:
        return {k: v.get().strip() for k, v in self.filter_vars.items() if v.get().strip()}

    def clear(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

    def insert_row(self, values: list, *, tags=()):
        self.tree.insert("", tk.END, values=values, tags=tags)

    def add_tag_style(self, tag: str, **kw):
        self.tree.tag_configure(tag, **kw)
