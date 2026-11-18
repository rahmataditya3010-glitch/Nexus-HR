# -*- coding: utf-8 -*-
"""Kerangka utama: helper umum, sidebar/topbar, navigasi, kartu & grafik dasar."""
import calendar
import csv
import hashlib
import json
import math
import os
import re
import tempfile
import tkinter as tk
import webbrowser
from datetime import date, datetime, time as dtime, timedelta
from html import escape as html_escape
from tkinter import filedialog, messagebox, ttk

from config import *
from helpers import *
from database import DB
from widgets import *


class CoreMixin:
    @property
    def is_admin(self):
        return (self.user or {}).get("role", "").lower() == "admin"

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def stop_clock(self):
        if self.clock_job:
            try:
                self.root.after_cancel(self.clock_job)
            except tk.TclError:
                pass
            self.clock_job = None

    def log(self, aksi, detail=""):
        DB.run("INSERT INTO aktivitas (pengguna, aksi, detail) VALUES (%s,%s,%s)",
               ((self.user or {}).get("nama_lengkap") or "-", aksi, detail[:250]), silent=True)

    def toast(self, msg, kind="success"):
        color = {"success": SUCCESS, "error": DANGER, "info": PRIMARY}.get(kind, SUCCESS)
        icon = {"success": "✔", "error": "✖", "info": "ℹ"}.get(kind, "✔")
        t = tk.Label(self.root, text=f"  {icon}  {msg}  ", bg=color, fg="white",
                     font=F_BASE_B, padx=14, pady=10)
        t.place(relx=1.0, rely=1.0, x=-26, y=-26, anchor="se")
        t.lift()
        self.root.after(2400, lambda: t.destroy() if t.winfo_exists() else None)

    def require_admin(self, aksi="melakukan aksi ini"):
        if not self.is_admin:
            messagebox.showerror("Akses Ditolak", f"Hanya Admin yang dapat {aksi}.")
            return False
        return True

    def make_tree(self, parent, cols):
        frame = tk.Frame(parent, bg=CARD)
        ysb = ttk.Scrollbar(frame, orient="vertical")
        xsb = ttk.Scrollbar(frame, orient="horizontal")
        tree = ttk.Treeview(frame, columns=[c[0] for c in cols], show="headings",
                            yscrollcommand=ysb.set, xscrollcommand=xsb.set, selectmode="browse")
        ysb.config(command=tree.yview)
        xsb.config(command=tree.xview)
        ysb.pack(side="right", fill="y")
        xsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)
        for key, head, w, anchor in cols:
            tree.heading(key, text=head)
            tree.column(key, width=w, anchor=anchor, minwidth=50)
        tree.tag_configure("odd", background=CARD)
        tree.tag_configure("even", background="#17233B")
        tree.tag_configure("cuti", foreground=WARN)
        tree.tag_configure("nonaktif", foreground="#F87171")
        return frame, tree

    # ============================================================
    #  KERANGKA UTAMA (SIDEBAR + TOPBAR)
    # ============================================================
    def show_main(self):
        self.clear()
        self.bind_shortcuts()

        side = tk.Frame(self.root, bg=SURFACE, width=252)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        brand = tk.Frame(side, bg=SURFACE)
        brand.pack(fill="x", padx=20, pady=(26, 22))
        tk.Label(brand, text="⚡", bg=PRIMARY, fg="white", font=("Segoe UI Emoji", 14),
                 padx=8, pady=3).pack(side="left")
        tk.Label(brand, text="NEXUS HR", bg=SURFACE, fg=TEXT,
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=12)

        tk.Label(side, text="MENU UTAMA", bg=SURFACE, fg="#52617D",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=24, pady=(0, 8))

        self.nav_items = {}
        for key, icon, text, admin_only in self.NAV:
            if admin_only and not self.is_admin:
                continue
            row = tk.Frame(side, bg=SURFACE, cursor="hand2")
            row.pack(fill="x", padx=14, pady=2)
            strip = tk.Frame(row, bg=SURFACE, width=4)
            strip.pack(side="left", fill="y")
            lbl = tk.Label(row, text=f"  {icon}   {text}", font=F_BASE_B, bg=SURFACE, fg=MUTED,
                           anchor="w", padx=10, pady=8)
            lbl.pack(side="left", fill="x", expand=True)
            for w in (row, lbl):
                w.bind("<Button-1>", lambda e, k=key: self.navigate(k))
                w.bind("<Enter>", lambda e, k=key: self.nav_hover(k, True))
                w.bind("<Leave>", lambda e, k=key: self.nav_hover(k, False))
            self.nav_items[key] = (row, strip, lbl)

        # kartu user di bawah
        bottom = tk.Frame(side, bg=SURFACE)
        bottom.pack(side="bottom", fill="x", padx=16, pady=18)
        HoverButton(bottom, "⎋   Keluar", self.logout, bg="#3B1D26", fg="#FCA5A5",
                    hover="#4C2430", pady=10).pack(fill="x", side="bottom", pady=(12, 0))
        ucard = tk.Frame(bottom, bg=CARD2)
        ucard.pack(fill="x", side="bottom")
        nm = self.user["nama_lengkap"]
        tk.Label(ucard, text=nm[:1].upper(), bg=PRIMARY, fg="white", font=("Segoe UI", 12, "bold"),
                 width=3, pady=6).pack(side="left", padx=10, pady=10)
        info = tk.Frame(ucard, bg=CARD2)
        info.pack(side="left", pady=8)
        tk.Label(info, text=nm if len(nm) < 17 else nm[:15] + "…", bg=CARD2, fg=TEXT,
                 font=F_BASE_B).pack(anchor="w")
        tk.Label(info, text="● " + self.user["role"].upper(), bg=CARD2,
                 fg=SUCCESS if self.is_admin else ACCENT, font=("Segoe UI", 8, "bold")).pack(anchor="w")

        # area kanan
        main = tk.Frame(self.root, bg=BG)
        main.pack(side="left", fill="both", expand=True)

        top = tk.Frame(main, bg=BG)
        top.pack(fill="x", padx=28, pady=(22, 8))
        tl = tk.Frame(top, bg=BG)
        tl.pack(side="left")
        self.title_lbl = tk.Label(tl, font=("Segoe UI", 22, "bold"), bg=BG, fg=TEXT)
        self.title_lbl.pack(anchor="w")
        self.sub_lbl = tk.Label(tl, font=("Segoe UI", 10), bg=BG, fg=MUTED)
        self.sub_lbl.pack(anchor="w")
        tr = tk.Frame(top, bg=BG)
        tr.pack(side="right")
        HoverButton(top, "🔍   Cari cepat      Ctrl+K", self.open_palette, bg=CARD, fg=MUTED, hover=CARD2,
                    font=F_SMALL, pady=9, padx=18).pack(side="right", padx=(0, 28))
        self.time_lbl = tk.Label(tr, font=("Segoe UI", 18, "bold"), bg=BG, fg=TEXT)
        self.time_lbl.pack(anchor="e")
        self.date_lbl = tk.Label(tr, font=F_SMALL, bg=BG, fg=MUTED)
        self.date_lbl.pack(anchor="e")

        self.content = tk.Frame(main, bg=BG)
        self.content.pack(fill="both", expand=True, padx=28, pady=(8, 22))

        self.tick()
        self.navigate("dashboard")

    def tick(self):
        try:
            now = datetime.now()
            self.time_lbl.config(text=now.strftime("%H:%M:%S"))
            self.date_lbl.config(text=f"{HARI[now.weekday()]}, {now.day} {BULAN[now.month - 1]} {now.year}")
            self.clock_job = self.root.after(1000, self.tick)
        except tk.TclError:
            self.clock_job = None

    def nav_hover(self, key, inside):
        if key == self.page:
            return
        row, strip, lbl = self.nav_items[key]
        bg = CARD if inside else SURFACE
        for w in (row, lbl, strip):
            w.config(bg=bg)
        lbl.config(fg=TEXT if inside else MUTED)

    def set_active(self, key):
        for k, (row, strip, lbl) in self.nav_items.items():
            if k == key:
                row.config(bg=CARD2)
                lbl.config(bg=CARD2, fg=TEXT)
                strip.config(bg=PRIMARY)
            else:
                row.config(bg=SURFACE)
                lbl.config(bg=SURFACE, fg=MUTED)
                strip.config(bg=SURFACE)

    def navigate(self, key):
        if key in ("user", "log", "pengaturan", "slip") and not self.is_admin:
            return
        self.page = key
        for w in self.content.winfo_children():
            w.destroy()
        title, sub = self.TITLES[key]
        self.title_lbl.config(text=title)
        self.sub_lbl.config(text=sub)
        self.set_active(key)
        getattr(self, f"build_{key}")(self.content)

    def logout(self):
        if messagebox.askyesno("Keluar", "Yakin ingin keluar dari aplikasi?"):
            self.log("LOGIN", f"{self.user['nama_lengkap']} keluar dari sistem")
            self.show_login()

    # ---------- shortcut ----------
    def bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.page == "karyawan" and self.is_admin and self.add_employee())
        self.root.bind("<Control-f>", lambda e: self.page == "karyawan" and self.search_box.focus())
        self.root.bind("<F5>", lambda e: self.navigate(self.page) if self.page else None)
        self.root.bind("<Control-k>", lambda e: self.open_palette())

    def unbind_shortcuts(self):
        for seq in ("<Control-n>", "<Control-f>", "<F5>", "<Control-k>"):
            self.root.unbind(seq)

    def salam(self):
        h = datetime.now().hour
        return "Selamat pagi" if h < 11 else "Selamat siang" if h < 15 else "Selamat sore" if h < 18 else "Selamat malam"

    def rcard(self, parent, title=None, subtitle=None, accent=None):
        """Kartu dengan sudut membulat. Mengembalikan (container, body)."""
        box = tk.Frame(parent, bg=BG)
        bgc = tk.Canvas(box, bg=BG, highlightthickness=0)
        bgc.place(x=0, y=0, relwidth=1, relheight=1)

        def redraw(e):
            bgc.delete("all")
            round_rect(bgc, 1, 1, e.width - 2, e.height - 2, 12, fill=CARD, outline=BORDER)

        bgc.bind("<Configure>", redraw)
        inner = tk.Frame(box, bg=CARD)
        inner.pack(fill="both", expand=True, padx=6, pady=6)
        if accent:
            tk.Frame(inner, bg=accent, height=3).pack(fill="x")
        if title:
            h = tk.Frame(inner, bg=CARD)
            h.pack(fill="x", padx=13, pady=(10, 2))
            tk.Label(h, text=title, font=("Segoe UI", 11, "bold"), bg=CARD, fg=TEXT).pack(anchor="w")
            if subtitle:
                tk.Label(h, text=subtitle, font=F_SMALL, bg=CARD, fg=MUTED).pack(anchor="w")
        body = tk.Frame(inner, bg=CARD)
        body.pack(fill="both", expand=True, padx=13, pady=(4, 9))
        return box, body

    def make_card(self, parent, title=None, subtitle=None):
        return self.rcard(parent, title, subtitle)

    def gridcard(self, w, row, col, span, pady=(0, 16)):
        w.grid(row=row, column=col, columnspan=span, sticky="nsew",
               padx=(0 if col == 0 else 8, 0 if col + span >= 12 else 8), pady=pady)

    def animate(self, c, draw, done=None, steps=22, i=0):
        try:
            if not c.winfo_exists():
                return
            t = i / steps
            draw(c, 1 - (1 - t) ** 3)
            if i < steps:
                self.root.after(16, lambda: self.animate(c, draw, done, steps, i + 1))
            elif done:
                done()
        except tk.TclError:
            pass

    def chart_canvas(self, body, draw, height=230):
        """Canvas grafik: animasi saat pertama tampil + tooltip saat hover."""
        c = tk.Canvas(body, bg=CARD, highlightthickness=0, height=height)
        c.pack(fill="both", expand=True)
        c._hits = []
        state = {"first": True, "busy": False}

        def finish():
            state["busy"] = False

        def on_cfg(e):
            if e.width < 60 or state["busy"]:
                return
            if state["first"]:
                state["first"] = False
                state["busy"] = True
                self.animate(c, draw, finish)
            else:
                draw(c, 1.0)

        def motion(e):
            c.delete("tip")
            for x1, y1, x2, y2, txt in c._hits:
                if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                    t = c.create_text(e.x + 14, e.y + 14, text=txt, anchor="nw", fill=TEXT,
                                      font=F_SMALL_B, justify="left", tags="tip")
                    bx1, by1, bx2, by2 = c.bbox(t)
                    if bx2 + 14 > c.winfo_width():
                        c.move(t, -(bx2 - bx1) - 30, 0)
                    if by2 + 14 > c.winfo_height():
                        c.move(t, 0, -(by2 - by1) - 30)
                    bx1, by1, bx2, by2 = c.bbox(t)
                    r = round_rect(c, bx1 - 9, by1 - 6, bx2 + 9, by2 + 6, 8, fill=CARD2,
                                   outline=PRIMARY, tags="tip")
                    c.tag_lower(r, t)
                    return

        c.bind("<Configure>", on_cfg)
        c.bind("<Motion>", motion)
        c.bind("<Leave>", lambda e: c.delete("tip"))
        return c

    def count_up(self, lbl, target, fmt, step=0, steps=22):
        try:
            if not lbl.winfo_exists():
                return
            t = step / steps
            lbl.config(text=fmt(target * (1 - (1 - t) ** 3)))
            if step < steps:
                self.root.after(24, lambda: self.count_up(lbl, target, fmt, step + 1, steps))
        except tk.TclError:
            pass
