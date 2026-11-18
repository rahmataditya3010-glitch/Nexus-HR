# -*- coding: utf-8 -*-
"""Widget custom Tkinter: HoverButton, ModernEntry, FormDialog, ScrollFrame, style ttk."""
import tkinter as tk
from tkinter import ttk

from config import *
from helpers import mix, lighten, darken, center_window


class HoverButton(tk.Label):
    """Tombol datar modern dengan efek hover."""

    def __init__(self, parent, text, command=None, bg=PRIMARY, fg="white", hover=None,
                 font=F_BASE_B, padx=16, pady=9, **kw):
        super().__init__(parent, text=text, bg=bg, fg=fg, font=font, padx=padx, pady=pady,
                         cursor="hand2", **kw)
        self._bg = bg
        self._hover = hover or lighten(bg, 0.16)
        self._cmd = command
        self.bind("<Enter>", lambda e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg))
        self.bind("<Button-1>", lambda e: self.config(bg=darken(self._bg, 0.12)))
        self.bind("<ButtonRelease-1>", self._release)

    def _release(self, e):
        self.config(bg=self._hover)
        if self._cmd and 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
            self._cmd()


class ModernEntry(tk.Frame):
    """Input dengan border yang menyala saat fokus, ikon & tombol mata opsional."""

    def __init__(self, parent, textvariable=None, show="", icon="", bg=FIELD,
                 width=20, font=F_BASE, toggle=False):
        super().__init__(parent, bg=BORDER)
        inner = tk.Frame(self, bg=bg)
        inner.pack(fill="x", padx=1, pady=1)
        if icon:
            tk.Label(inner, text=icon, bg=bg, fg=MUTED, font=("Segoe UI Emoji", 11)).pack(
                side="left", padx=(12, 0))
        self.entry = tk.Entry(inner, textvariable=textvariable, show=show, bg=bg, fg=TEXT,
                              insertbackground=TEXT, relief="flat", bd=0, highlightthickness=0,
                              font=font, width=width)
        self.entry.pack(side="left", fill="x", expand=True, padx=10, ipady=9)
        self.entry.bind("<FocusIn>", lambda e: self.config(bg=PRIMARY))
        self.entry.bind("<FocusOut>", lambda e: self.config(bg=BORDER))
        if toggle:
            eye = tk.Label(inner, text="👁", bg=bg, fg=MUTED, cursor="hand2",
                           font=("Segoe UI Emoji", 11))
            eye.pack(side="right", padx=(0, 12))
            eye.bind("<Button-1>", lambda e: self._toggle())
            self._eye = eye

    def _toggle(self):
        if self.entry.cget("show"):
            self.entry.config(show="")
            self._eye.config(fg=PRIMARY)
        else:
            self.entry.config(show="•")
            self._eye.config(fg=MUTED)

    def focus(self):
        self.entry.focus_set()


class FormDialog(tk.Toplevel):
    """Dialog form generik.  on_save(values) -> None jika sukses, atau string pesan error."""

    def __init__(self, app, title, subtitle, fields, on_save, initial=None,
                 width=580, save_text="💾  Simpan"):
        super().__init__(app.root)
        self.configure(bg=SURFACE)
        self.title(title)
        self.resizable(False, False)
        self.transient(app.root)
        self.on_save = on_save
        self.vars = {}
        self.first = None

        head = tk.Frame(self, bg=SURFACE)
        head.pack(fill="x", padx=28, pady=(24, 4))
        tk.Label(head, text=title, font=("Segoe UI", 16, "bold"), bg=SURFACE, fg=TEXT).pack(anchor="w")
        tk.Label(head, text=subtitle, font=F_SMALL, bg=SURFACE, fg=MUTED).pack(anchor="w", pady=(2, 0))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(12, 6))

        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="x", padx=28, pady=4)
        body.columnconfigure(0, weight=1, uniform="c")
        body.columnconfigure(1, weight=1, uniform="c")

        row = col = 0
        for f in fields:
            full = f.get("full", False)
            if full and col == 1:
                row, col = row + 1, 0
            cell = tk.Frame(body, bg=SURFACE)
            padx = (0, 0) if full else ((0, 8) if col == 0 else (8, 0))
            cell.grid(row=row, column=0 if full else col, columnspan=2 if full else 1,
                      sticky="ew", padx=padx, pady=6)
            lab = f["label"] + (" *" if f.get("required", True) else "")
            tk.Label(cell, text=lab.upper(), font=("Segoe UI", 8, "bold"), bg=SURFACE,
                     fg=MUTED).pack(anchor="w", pady=(0, 4))
            init = ""
            if initial and initial.get(f["key"]) is not None:
                init = str(initial.get(f["key"]))
            elif "default" in f:
                init = f["default"]
            var = tk.StringVar(value=init)
            self.vars[f["key"]] = var
            kind = f.get("type", "entry")
            if kind == "combo":
                w = ttk.Combobox(cell, textvariable=var, values=f.get("values", []),
                                 style="Modern.TCombobox", font=F_BASE,
                                 state="readonly" if f.get("readonly") else "normal")
                w.pack(fill="x")
            else:
                w = ModernEntry(cell, textvariable=var, show="•" if kind == "password" else "",
                                toggle=(kind == "password"))
                w.pack(fill="x")
            if self.first is None:
                self.first = w
            if full:
                row, col = row + 1, 0
            else:
                col = (col + 1) % 2
                if col == 0:
                    row += 1

        self.err = tk.Label(self, text="", fg="#FCA5A5", bg=SURFACE, font=F_SMALL,
                            wraplength=width - 60, justify="left")
        self.err.pack(anchor="w", padx=28, pady=(8, 0))

        foot = tk.Frame(self, bg=SURFACE)
        foot.pack(fill="x", padx=28, pady=(10, 24))
        HoverButton(foot, save_text, self.save, bg=PRIMARY, padx=22).pack(side="right")
        HoverButton(foot, "Batal", self.destroy, bg=CARD2, fg=TEXT, padx=22).pack(side="right", padx=10)

        self.bind("<Return>", lambda e: self.save())
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        center_window(self, width, self.winfo_reqheight(), app.root)
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        if self.first is not None:
            try:
                self.first.focus()
            except (AttributeError, tk.TclError):
                self.first.focus_set()

    def save(self):
        vals = {k: v.get().strip() for k, v in self.vars.items()}
        msg = self.on_save(vals)
        if msg:
            self.err.config(text="⚠  " + msg)
        else:
            self.destroy()


class ScrollFrame(tk.Frame):
    """Area yang bisa di-scroll (mouse wheel + scrollbar)."""

    def __init__(self, parent, bg=BG):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, yscrollincrement=30)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.bind_all("<MouseWheel>", self._wheel)
        self.bind("<Destroy>", self._destroyed)

    def _wheel(self, e):
        try:
            w = self.winfo_containing(e.x_root, e.y_root)
        except (KeyError, tk.TclError):
            return
        while w is not None:
            if w is self:
                break
            w = w.master
        else:
            return
        if self.inner.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-e.delta / 120), "units")

    def _destroyed(self, e):
        if e.widget is self:
            try:
                self.unbind_all("<MouseWheel>")
            except tk.TclError:
                pass


def setup_styles(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                rowheight=36, borderwidth=0, font=F_BASE)
    s.configure("Treeview.Heading", background=CARD2, foreground=MUTED,
                font=("Segoe UI", 9, "bold"), relief="flat", borderwidth=0, padding=(10, 9))
    s.map("Treeview", background=[("selected", PRIMARY)], foreground=[("selected", "#FFFFFF")])
    s.map("Treeview.Heading", background=[("active", BORDER)], foreground=[("active", TEXT)])
    for o in ("Vertical", "Horizontal"):
        s.configure(f"{o}.TScrollbar", background=BORDER, troughcolor=CARD, bordercolor=CARD,
                    arrowcolor=MUTED, lightcolor=BORDER, darkcolor=BORDER, relief="flat")
        s.map(f"{o}.TScrollbar", background=[("active", MUTED)])
    s.configure("Modern.TCombobox", fieldbackground=FIELD, background=CARD2, foreground=TEXT,
                arrowcolor=MUTED, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                selectbackground=FIELD, selectforeground=TEXT, padding=8, relief="flat")
    s.map("Modern.TCombobox",
          fieldbackground=[("readonly", FIELD), ("focus", FIELD)],
          foreground=[("readonly", TEXT)],
          selectbackground=[("readonly", FIELD)],
          selectforeground=[("readonly", TEXT)],
          bordercolor=[("focus", PRIMARY)],
          arrowcolor=[("hover", TEXT)])
    root.option_add("*TCombobox*Listbox.background", CARD2)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", PRIMARY)
    root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
    root.option_add("*TCombobox*Listbox.font", F_BASE)
