import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

class FilterTable(ttk.Frame):
    def __init__(self, master, columns: list[str], *, bool_columns: set[str] | None = None):
        super().__init__(master)
        self.columns = columns
        self.bool_columns = bool_columns or set()
        self.filter_vars: dict[str, tk.StringVar] = {}
        self._filter_entries: dict[str, ttk.Entry] = {}

        style = ttk.Style(self)
        self._filter_label_font = tkfont.nametofont("TkDefaultFont").copy()
        self._filter_label_font.configure(size=8, weight="bold")
        self._filter_entry_font = tkfont.nametofont("TkDefaultFont").copy()
        self._filter_entry_font.configure(size=8)
        style.configure("FilterTable.TEntry", font=self._filter_entry_font)
        style.configure("FilterTable.TButton", padding=(1, 0))

        self.filt_frame = ttk.Frame(self)
        self.filt_frame.pack(fill=tk.X)

        # Header + Filter-Entries
        for j, col in enumerate(self.columns):
            lbl = ttk.Label(self.filt_frame, text=col, font=self._filter_label_font)
            lbl.grid(row=0, column=j, sticky="we", pady=(2, 0))

            entry_wrap = ttk.Frame(self.filt_frame)
            entry_wrap.grid(row=1, column=j, sticky="we", pady=(0, 2))
            entry_wrap.grid_columnconfigure(0, weight=1)

            var = tk.StringVar()
            ent = ttk.Entry(entry_wrap, textvariable=var, style="FilterTable.TEntry")
            ent.grid(row=0, column=0, sticky="we")
            ent.bind("<KeyRelease>", lambda e: self.event_generate("<<FilterChanged>>"))

            clear_btn = ttk.Button(
                entry_wrap,
                text="✕",
                width=1,
                style="FilterTable.TButton",
                command=lambda v=var, e=ent: self._clear_filter(v, e),
            )
            clear_btn.grid(row=0, column=1, padx=(1, 0))
            clear_btn.state(["disabled"])

            var.trace_add("write", lambda *_args, v=var, b=clear_btn: self._on_filter_change(v, b))
            self.filter_vars[col] = var
            self._filter_entries[col] = ent
            self.filt_frame.grid_columnconfigure(j, weight=0, minsize=120)

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

        self.tree.bind("<Configure>", self._sync_filter_widths, add="+")
        self.tree.bind("<B1-Motion>", self._sync_filter_widths, add="+")
        self.tree.bind("<ButtonRelease-1>", self._sync_filter_widths, add="+")
        self.after(0, self._sync_filter_widths)

    def autosize_columns(self, *, min_width: int = 80, max_width: int = 500, padding: int = 24):
        """Passe Spaltenbreiten an Inhalt + Header an.

        Wird von mehreren Tabs beim Laden der Daten aufgerufen.
        """
        if not self.columns:
            return

        measure_font = tkfont.nametofont("TkDefaultFont")
        heading_font_name = ttk.Style(self).lookup("Treeview.Heading", "font")
        heading_font = tkfont.nametofont(heading_font_name) if heading_font_name else measure_font

        for col in self.columns:
            width = heading_font.measure(str(col)) + padding
            for item in self.tree.get_children():
                value = self.tree.set(item, col)
                width = max(width, measure_font.measure(str(value)) + padding)

            width = max(min_width, min(width, max_width))
            self.tree.column(col, width=width)

        self._sync_filter_widths()

    def _on_filter_change(self, var: tk.StringVar, clear_btn: ttk.Button):
        if var.get().strip():
            clear_btn.state(["!disabled"])
        else:
            clear_btn.state(["disabled"])

    def _clear_filter(self, var: tk.StringVar, entry: ttk.Entry):
        if not var.get():
            return
        var.set("")
        entry.focus_set()
        self.event_generate("<<FilterChanged>>")

    def _sync_filter_widths(self, _event=None):
        for j, col in enumerate(self.columns):
            width = int(self.tree.column(col, option="width"))
            self.filt_frame.grid_columnconfigure(j, minsize=max(width, 40))

    def get_filters(self) -> dict:
        return {k: v.get().strip() for k, v in self.filter_vars.items() if v.get().strip()}

    def clear(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

    def insert_row(self, values: list, *, tags=()):
        return self.tree.insert("", tk.END, values=values, tags=tags)

    def add_tag_style(self, tag: str, **kw):
        self.tree.tag_configure(tag, **kw)
