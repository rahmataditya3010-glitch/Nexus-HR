# -*- coding: utf-8 -*-

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

import mysql.connector
import db_server
db_server.start_server()
# ============================================================
#  KONFIGURASI
# ============================================================
DB_NAME = "karyawan_DB"
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "root",
    "password": "",
    "database": DB_NAME,
}
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(APP_DIR, "nexus_settings.json")

# ---------- Logo / ikon (letakkan file di folder yang sama dengan file .py ini) ----------
LOGO_PNG = os.path.join(APP_DIR, "logo.png")   # logo untuk login & sidebar (persegi, transparan, min. 128x128)
LOGO_ICO = os.path.join(APP_DIR, "nexus.ico")  # ikon jendela / taskbar Windows

# ---------- Warna ----------
BG = "#0B1120"
SURFACE = "#0F172A"
CARD = "#131C31"
CARD2 = "#1B2740"
FIELD = "#0B1220"
BORDER = "#26344F"
TEXT = "#F1F5F9"
MUTED = "#8B9AB5"
PRIMARY = "#6366F1"
ACCENT = "#22D3EE"
SUCCESS = "#10B981"
WARN = "#F59E0B"
DANGER = "#EF4444"
PINK = "#EC4899"
VIOLET = "#A78BFA"
PALETTE = [PRIMARY, ACCENT, SUCCESS, WARN, PINK, VIOLET, "#F87171"]
STATUS_COLOR = {"Aktif": SUCCESS, "Cuti": WARN, "Nonaktif": DANGER}

F_BASE = ("Segoe UI", 10)
F_BASE_B = ("Segoe UI", 10, "bold")
F_SMALL = ("Segoe UI", 9)
F_SMALL_B = ("Segoe UI", 9, "bold")

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
DEPT_DEFAULT = ["Umum", "IT", "HRD", "Keuangan", "Marketing", "Operasional", "Produksi", "Penjualan"]
STATUS_LIST = ["Aktif", "Cuti", "Nonaktif"]


# ============================================================
#  HELPER
# ============================================================
def mix(c1, c2, t):
    """Campur dua warna hex. t=0 -> c1, t=1 -> c2."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def lighten(c, t=0.18):
    return mix(c, "#FFFFFF", t)


def darken(c, t=0.2):
    return mix(c, "#000000", t)


def rp(n):
    try:
        return "Rp " + f"{int(float(n)):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "Rp 0"


def rp_short(n):
    n = float(n or 0)
    if n >= 1e9:
        return ("Rp %.2f M" % (n / 1e9)).replace(".", ",")
    if n >= 1e6:
        return ("Rp %.1f jt" % (n / 1e6)).replace(".", ",")
    return rp(n)


def short_num(v):
    if v == 0:
        return "0"
    if v >= 1e9:
        return ("%.1f M" % (v / 1e9)).replace(".", ",")
    if v >= 1e6:
        return ("%.1f jt" % (v / 1e6)).replace(".", ",")
    if v >= 1e3:
        return "%d rb" % (v / 1e3)
    return str(int(v))


def hash_pw(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


def center_window(win, w, h, parent=None):
    win.update_idletasks()
    if parent is not None:
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    else:
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        w, h = min(w, sw - 60), min(h, sh - 90)
        x, y = (sw - w) // 2, max((sh - h) // 2 - 20, 0)
    win.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass


def make_app_icon(size=128):
    """Buat ikon aplikasi (petir putih di kotak membulat ungu) tanpa file gambar."""
    img = tk.PhotoImage(width=size, height=size)
    bolt = [(0.60, 0.08), (0.24, 0.56), (0.47, 0.56), (0.38, 0.92), (0.78, 0.42), (0.54, 0.42), (0.66, 0.08)]
    r = 0.24

    def in_round(x, y):
        dx = max(r - x, 0, x - (1 - r))
        dy = max(r - y, 0, y - (1 - r))
        return dx * dx + dy * dy <= r * r

    def in_bolt(x, y):
        inside = False
        j = len(bolt) - 1
        for i in range(len(bolt)):
            xi, yi = bolt[i]
            xj, yj = bolt[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
        return inside

    for py in range(size):
        row = []
        for px in range(size):
            x, y = (px + 0.5) / size, (py + 0.5) / size
            if not in_round(x, y):
                row.append("{}")  # transparan
            elif in_bolt(x, y):
                row.append("#FFFFFF")
            else:
                row.append(mix(PRIMARY, "#7C3AED", (x + y) / 2))
        img.put("{" + " ".join(row) + "}", to=(0, py))
    return img


def load_logo(size):
    """Muat logo (logo.png, atau nexus.ico jika Pillow terpasang) dan ubah ke ukuran ~size px.
    Mengembalikan None jika tidak ada / gagal."""
    try:
        from PIL import Image, ImageTk
    except ImportError:
        Image = ImageTk = None

    try:
        if Image is not None:
            for path in (LOGO_PNG, LOGO_ICO):
                if os.path.exists(path):
                    img = Image.open(path)
                    if path.lower().endswith(".ico"):   # ambil ukuran terbesar di dalam .ico
                        sizes = img.ico.sizes() if hasattr(img, "ico") else []
                        if sizes:
                            img.size = max(sizes)
                    img = img.convert("RGBA").resize((size, size), Image.LANCZOS)
                    return ImageTk.PhotoImage(img)
        elif os.path.exists(LOGO_PNG):   # tanpa Pillow: hanya PNG yang bisa dibaca Tk
            img = tk.PhotoImage(file=LOGO_PNG)
            f = max(1, img.width() // size)
            return img.subsample(f, f)
    except (tk.TclError, OSError, ValueError):
        pass
    return None


# ============================================================
#  DATABASE
# ============================================================
class DB:
    failed = False

    @staticmethod
    def run(sql, params=(), fetch=None, many=False, silent=False):
        """fetch: 'all' | 'one' | None (commit). Mengembalikan None jika error."""
        DB.failed = False
        conn = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cur = conn.cursor(dictionary=True)
            if many:
                cur.executemany(sql, params)
            else:
                cur.execute(sql, params)
            if fetch == "all":
                return cur.fetchall()
            if fetch == "one":
                return cur.fetchone()
            conn.commit()
            return cur.lastrowid or True
        except mysql.connector.Error as err:
            DB.failed = True
            if not silent:
                messagebox.showerror("Kesalahan Database", f"{err}")
            return None
        finally:
            if conn is not None:
                try:
                    conn.close()
                except mysql.connector.Error:
                    pass


def init_db():
    """Buat database/tabel jika belum ada & tambahkan kolom baru jika perlu."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"], port=DB_CONFIG["port"], user=DB_CONFIG["user"], password=DB_CONFIG["password"]
        )
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4")
        conn.database = DB_NAME

        cur.execute(
            """CREATE TABLE IF NOT EXISTS users (
                 id INT AUTO_INCREMENT PRIMARY KEY,
                 username VARCHAR(50) NOT NULL UNIQUE,
                 password VARCHAR(255) NOT NULL,
                 nama_lengkap VARCHAR(100) NOT NULL,
                 role VARCHAR(20) NOT NULL DEFAULT 'staff')"""
        )
        try:
            cur.execute("ALTER TABLE users MODIFY password VARCHAR(255) NOT NULL")
        except mysql.connector.Error:
            pass

        cur.execute(
            """CREATE TABLE IF NOT EXISTS karyawan (
                 id INT AUTO_INCREMENT PRIMARY KEY,
                 nama VARCHAR(100) NOT NULL,
                 jabatan VARCHAR(100),
                 email VARCHAR(100),
                 telepon VARCHAR(30),
                 gaji DECIMAL(15,2) DEFAULT 0)"""
        )
        for col, ddl in (
            ("departemen", "VARCHAR(80) DEFAULT 'Umum'"),
            ("tanggal_masuk", "DATE NULL"),
            ("status", "VARCHAR(20) DEFAULT 'Aktif'"),
        ):
            cur.execute(f"SHOW COLUMNS FROM karyawan LIKE '{col}'")
            if cur.fetchone() is None:
                cur.execute(f"ALTER TABLE karyawan ADD COLUMN {col} {ddl}")
        cur.execute("UPDATE karyawan SET departemen='Umum' WHERE departemen IS NULL OR departemen=''")
        cur.execute("UPDATE karyawan SET status='Aktif' WHERE status IS NULL OR status=''")

        cur.execute(
            """CREATE TABLE IF NOT EXISTS aktivitas (
                 id INT AUTO_INCREMENT PRIMARY KEY,
                 waktu DATETIME DEFAULT CURRENT_TIMESTAMP,
                 pengguna VARCHAR(100),
                 aksi VARCHAR(30),
                 detail VARCHAR(255))"""
        )

        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO users (username, password, nama_lengkap, role) VALUES (%s,%s,%s,%s)",
                ("admin", hash_pw("admin123"), "Administrator", "admin"),
            )
        init_modul_tables(cur)
        conn.commit()
        conn.close()
        return True
    except mysql.connector.Error as err:
        messagebox.showerror(
            "Koneksi Gagal",
            f"Tidak dapat terhubung / menyiapkan database:\n{err}\n\n"
            "Pastikan MySQL di Laragon sudah berjalan (Start All).",
        )
        return False


# ============================================================
#  WIDGET CUSTOM
# ============================================================
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


def round_rect(c, x1, y1, x2, y2, r=12, **kw):
    """Persegi panjang dengan sudut membulat di Canvas."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def nice_scale(mx, ticks=4, integer=False):
    """Hitung nilai atas & langkah sumbu yang 'rapi'."""
    mx = max(mx, 1e-9)
    raw = mx / ticks
    mag = 10 ** math.floor(math.log10(raw))
    step = mag * 10
    for m in (1, 2, 2.5, 5, 10):
        if m * mag * ticks >= mx:
            step = m * mag
            break
    if integer and step < 1:
        step = 1
    return step * ticks, step


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


# ============================================================
#  STYLE TTK
# ============================================================
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


# ============================================================
#  KONFIGURASI MODUL
# ============================================================
JAM_MASUK = dtime(8, 0)          # lewat jam ini => Terlambat
JATAH_CUTI = 12                  # hari cuti tahunan per tahun
HARI_KERJA_BULAN = 22            # pembagi potongan alpa
BPJS_PCT = 0.03                  # iuran karyawan (JHT 2% + Kesehatan 1%)
PTKP = 54_000_000                # PTKP TK/0 per tahun
STATUS_ABSEN = ["Hadir", "Terlambat", "Izin", "Sakit", "Cuti", "Alpa"]
JENIS_CUTI = ["Tahunan", "Sakit", "Melahirkan", "Penting", "Lainnya"]


def init_modul_tables(cur):
    """Dipanggil dari init_db() dengan cursor yang sedang terbuka."""
    cur.execute(
        """CREATE TABLE IF NOT EXISTS absensi (
             id INT AUTO_INCREMENT PRIMARY KEY,
             karyawan_id INT NOT NULL,
             tanggal DATE NOT NULL,
             jam_masuk TIME NULL,
             jam_keluar TIME NULL,
             status VARCHAR(20) NOT NULL DEFAULT 'Hadir',
             catatan VARCHAR(150) NULL,
             UNIQUE KEY uq_absen (karyawan_id, tanggal))""")
    cur.execute(
        """CREATE TABLE IF NOT EXISTS cuti (
             id INT AUTO_INCREMENT PRIMARY KEY,
             karyawan_id INT NOT NULL,
             jenis VARCHAR(20) NOT NULL,
             tgl_mulai DATE NOT NULL,
             tgl_selesai DATE NOT NULL,
             jumlah_hari INT NOT NULL DEFAULT 0,
             alasan VARCHAR(255) NULL,
             status VARCHAR(20) NOT NULL DEFAULT 'Menunggu',
             diproses_oleh VARCHAR(100) NULL,
             dibuat DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute(
        """CREATE TABLE IF NOT EXISTS slip_gaji (
             id INT AUTO_INCREMENT PRIMARY KEY,
             karyawan_id INT NOT NULL,
             periode CHAR(7) NOT NULL,
             gaji_pokok DECIMAL(15,2) DEFAULT 0,
             tunjangan DECIMAL(15,2) DEFAULT 0,
             lembur DECIMAL(15,2) DEFAULT 0,
             alpa_hari INT DEFAULT 0,
             potongan_absen DECIMAL(15,2) DEFAULT 0,
             bpjs DECIMAL(15,2) DEFAULT 0,
             pph21 DECIMAL(15,2) DEFAULT 0,
             potongan_lain DECIMAL(15,2) DEFAULT 0,
             gaji_bersih DECIMAL(15,2) DEFAULT 0,
             catatan VARCHAR(200) NULL,
             dibuat DATETIME DEFAULT CURRENT_TIMESTAMP,
             UNIQUE KEY uq_slip (karyawan_id, periode))""")


# ============================================================
#  HELPER
# ============================================================
def _fmt_time(v):
    if v is None:
        return "-"
    if isinstance(v, timedelta):
        s = int(v.total_seconds())
        return f"{s // 3600:02d}:{s % 3600 // 60:02d}"
    return str(v)[:5]


def _parse_time(s):
    """'08:15' -> '08:15:00'; kosong -> None; salah -> ValueError."""
    s = (s or "").strip()
    if not s:
        return None
    return datetime.strptime(s, "%H:%M").strftime("%H:%M:%S")


def _parse_date(s):
    return datetime.strptime((s or "").strip(), "%Y-%m-%d").date()


def _workday_list(d1, d2):
    out, d = [], d1
    while d <= d2:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def _month_range(per):
    y, m = int(per[:4]), int(per[5:7])
    return date(y, m, 1), date(y + m // 12, m % 12 + 1, 1)


def _periods(n=12):
    t = date.today()
    y, m, out = t.year, t.month, []
    for _ in range(n):
        out.append(f"{y}-{m:02d}")
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return out


def _per_label(per):
    return f"{BULAN[int(per[5:7]) - 1]} {per[:4]}"


def _num(s):
    """Angka bulat dari teks; kosong -> 0; tidak valid -> None."""
    s = (s or "").strip()
    if not s:
        return 0
    if not re.fullmatch(r"(?i)(rp)?\s*[\d.,\s]+", s):
        return None
    return int(re.sub(r"\D", "", s) or 0)


def pph21_bulanan(bruto, iuran):
    """Estimasi PPh21 sederhana (TK/0, tarif progresif UU HPP). Bukan pengganti perhitungan pajak resmi."""
    annual = bruto * 12
    biaya = min(annual * 0.05, 6_000_000)
    pkp = max(annual - biaya - iuran * 12 - PTKP, 0)
    pkp = int(pkp // 1000 * 1000)
    tax, sisa = 0.0, pkp
    for lebar, tarif in ((60e6, .05), (190e6, .15), (250e6, .25), (4.5e9, .30), (float("inf"), .35)):
        part = min(sisa, lebar)
        tax += part * tarif
        sisa -= part
        if sisa <= 0:
            break
    return int(round(tax / 12))


def hitung_slip(pokok, tunjangan, lembur, alpa, lain):
    pokok, tunjangan, lembur, alpa, lain = (int(pokok), int(tunjangan), int(lembur), int(alpa), int(lain))
    bruto = pokok + tunjangan + lembur
    pot_absen = int(round(pokok / HARI_KERJA_BULAN * alpa))
    bpjs = int(round(pokok * BPJS_PCT))
    pph = pph21_bulanan(bruto, bpjs)
    bersih = bruto - pot_absen - bpjs - pph - lain
    return {"gaji_pokok": pokok, "tunjangan": tunjangan, "lembur": lembur, "alpa_hari": alpa,
            "potongan_absen": pot_absen, "bpjs": bpjs, "pph21": pph, "potongan_lain": lain,
            "gaji_bersih": bersih}


# ============================================================
#  MIXIN — ditambahkan ke class NexusHR
# ============================================================
class ModulHR:
    # ---------- umum ----------
    def _modul_tabs(self, parent, attr, tabs, builders):
        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        body = tk.Frame(parent, bg=BG)
        body.pack(fill="both", expand=True)

        def show(key):
            setattr(self, attr, key)
            for w in bar.winfo_children():
                w.destroy()
            for k, text in tabs:
                on = k == key
                HoverButton(bar, text, lambda k=k: show(k), bg=PRIMARY if on else CARD,
                            fg="white" if on else MUTED, hover=PRIMARY if on else CARD2,
                            pady=8).pack(side="left", padx=(0, 8))
            for w in body.winfo_children():
                w.destroy()
            builders[key](body)

        show(getattr(self, attr, tabs[0][0]))

    def _card_tree(self, parent, cols):
        outer, inner = self.make_card(parent)
        outer.pack(fill="both", expand=True)
        inner.pack_configure(padx=0, pady=0)
        tf, tree = self.make_tree(inner, cols)
        tf.pack(fill="both", expand=True)
        return tree

    def _selected_row(self, tree, rows, key="id"):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih satu baris dari tabel terlebih dahulu.")
            return None
        return next((r for r in rows if str(r[key]) == sel[0]), None)

    # ============================================================
    #  ABSENSI
    # ============================================================
    def build_absensi(self, parent):
        self._modul_tabs(parent, "abs_tab",
                         [("harian", "🗓️  Harian"), ("rekap", "📈  Rekap Bulanan")],
                         {"harian": self._abs_harian, "rekap": self._abs_rekap})

    def _abs_harian(self, parent):
        self.abs_date = tk.StringVar(value=date.today().isoformat())
        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        HoverButton(bar, "◀", lambda: self._abs_shift(-1), bg=CARD2, fg=TEXT, padx=12).pack(side="left")
        ent = ModernEntry(bar, textvariable=self.abs_date, icon="📅", bg=CARD, width=12)
        ent.pack(side="left", padx=8)
        ent.entry.bind("<Return>", lambda e: self._abs_load())
        HoverButton(bar, "▶", lambda: self._abs_shift(1), bg=CARD2, fg=TEXT, padx=12).pack(side="left")
        HoverButton(bar, "Hari ini", self._abs_today, bg=CARD2, fg=TEXT).pack(side="left", padx=8)
        if self.is_admin:
            HoverButton(bar, "✔  Semua Hadir", self._abs_all_present, bg=CARD2, fg=TEXT).pack(side="right")
            HoverButton(bar, "✏️  Catat Manual", self._abs_manual, bg=WARN, fg="#1F2937").pack(side="right", padx=8)
            HoverButton(bar, "🏁  Check-out", self._abs_checkout, bg=PRIMARY).pack(side="right")
            HoverButton(bar, "✅  Check-in", self._abs_checkin, bg=SUCCESS).pack(side="right", padx=8)

        cols = [("nama", "Nama Karyawan", 230, "w"), ("departemen", "Departemen", 140, "w"),
                ("masuk", "Jam Masuk", 100, "center"), ("keluar", "Jam Keluar", 100, "center"),
                ("status", "Status", 120, "center"), ("catatan", "Catatan", 260, "w")]
        self.abs_tree = self._card_tree(parent, cols)
        self.abs_tree.tag_configure("terlambat", foreground=WARN)
        self.abs_tree.tag_configure("izin", foreground=ACCENT)
        self.abs_tree.tag_configure("alpa", foreground="#F87171")
        self.abs_tree.tag_configure("belum", foreground=MUTED)
        self.abs_info = tk.Label(parent, text="", bg=BG, fg=MUTED, font=F_SMALL)
        self.abs_info.pack(anchor="w", pady=(12, 0))
        self._abs_load()

    def _abs_cur(self):
        try:
            return _parse_date(self.abs_date.get())
        except ValueError:
            messagebox.showwarning("Tanggal", "Format tanggal harus YYYY-MM-DD (contoh: 2026-11-14).")
            return None

    def _abs_shift(self, n):
        d = self._abs_cur()
        if d:
            self.abs_date.set((d + timedelta(days=n)).isoformat())
            self._abs_load()

    def _abs_today(self):
        self.abs_date.set(date.today().isoformat())
        self._abs_load()

    def _abs_load(self):
        d = self._abs_cur()
        if d is None:
            return
        rows = DB.run(
            "SELECT k.id, k.nama, k.departemen, a.jam_masuk, a.jam_keluar, a.status, a.catatan "
            "FROM karyawan k LEFT JOIN absensi a ON a.karyawan_id=k.id AND a.tanggal=%s "
            "WHERE k.status<>'Nonaktif' ORDER BY k.nama", (d.isoformat(),), "all") or []
        self.abs_rows = rows
        self.abs_tree.delete(*self.abs_tree.get_children())
        cnt = {}
        for i, r in enumerate(rows):
            st = r["status"] or "Belum Absen"
            cnt[st] = cnt.get(st, 0) + 1
            tags = ["even" if i % 2 else "odd"]
            if st == "Terlambat":
                tags.append("terlambat")
            elif st in ("Izin", "Sakit", "Cuti"):
                tags.append("izin")
            elif st == "Alpa":
                tags.append("alpa")
            elif st == "Belum Absen":
                tags.append("belum")
            self.abs_tree.insert("", "end", iid=str(r["id"]), tags=tags, values=(
                r["nama"], r["departemen"] or "Umum", _fmt_time(r["jam_masuk"]),
                _fmt_time(r["jam_keluar"]), st, r["catatan"] or ""))
        order = STATUS_ABSEN + ["Belum Absen"]
        ringkas = "   •   ".join(f"{k} {cnt[k]}" for k in order if cnt.get(k))
        hari = f"{HARI[d.weekday()]}, {d.day} {BULAN[d.month - 1]} {d.year}"
        akhir = "  (akhir pekan)" if d.weekday() >= 5 else ""
        self.abs_info.config(text=f"{hari}{akhir}   —   {ringkas or 'Belum ada karyawan aktif'}"
                                  f"   •   Batas masuk {JAM_MASUK:%H:%M}")

    def _abs_selected(self):
        return self._selected_row(self.abs_tree, getattr(self, "abs_rows", []))

    def _abs_upsert(self, kid, tgl, status, jm, jk, catatan):
        return DB.run(
            "INSERT INTO absensi (karyawan_id, tanggal, jam_masuk, jam_keluar, status, catatan) "
            "VALUES (%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE jam_masuk=VALUES(jam_masuk), "
            "jam_keluar=VALUES(jam_keluar), status=VALUES(status), catatan=VALUES(catatan)",
            (kid, tgl, jm, jk, status, catatan))

    def _abs_checkin(self):
        if not self.require_admin("mencatat absensi"):
            return
        r = self._abs_selected()
        d = self._abs_cur()
        if not r or d is None:
            return
        if d != date.today():
            messagebox.showinfo("Check-in", "Check-in cepat hanya untuk hari ini.\nGunakan 'Catat Manual' untuk tanggal lain.")
            return
        if r["status"] in ("Izin", "Sakit", "Cuti"):
            messagebox.showinfo("Check-in", f"{r['nama']} berstatus {r['status']} hari ini.")
            return
        if r["jam_masuk"] is not None:
            messagebox.showinfo("Check-in", f"{r['nama']} sudah check-in pukul {_fmt_time(r['jam_masuk'])}.")
            return
        now = datetime.now()
        st = "Terlambat" if now.time() > JAM_MASUK else "Hadir"
        if self._abs_upsert(r["id"], d.isoformat(), st, now.strftime("%H:%M:%S"), None, r["catatan"]) is not None:
            self.log("ABSEN", f"Check-in {r['nama']} {now:%H:%M} ({st})")
            self._abs_load()
            self.toast(f"{r['nama']} check-in {now:%H:%M} — {st}", "success" if st == "Hadir" else "info")

    def _abs_checkout(self):
        if not self.require_admin("mencatat absensi"):
            return
        r = self._abs_selected()
        d = self._abs_cur()
        if not r or d is None:
            return
        if r["jam_masuk"] is None:
            messagebox.showinfo("Check-out", f"{r['nama']} belum check-in pada tanggal ini.")
            return
        now = datetime.now()
        if DB.run("UPDATE absensi SET jam_keluar=%s WHERE karyawan_id=%s AND tanggal=%s",
                  (now.strftime("%H:%M:%S"), r["id"], d.isoformat())) is not None:
            self.log("ABSEN", f"Check-out {r['nama']} {now:%H:%M}")
            self._abs_load()
            self.toast(f"{r['nama']} check-out {now:%H:%M}", "info")

    def _abs_manual(self):
        if not self.require_admin("mencatat absensi"):
            return
        r = self._abs_selected()
        d = self._abs_cur()
        if not r or d is None:
            return
        fields = [
            {"key": "status", "label": "Status", "type": "combo", "values": STATUS_ABSEN, "readonly": True,
             "full": True},
            {"key": "jam_masuk", "label": "Jam Masuk (HH:MM)", "required": False},
            {"key": "jam_keluar", "label": "Jam Keluar (HH:MM)", "required": False},
            {"key": "catatan", "label": "Catatan", "required": False, "full": True},
        ]
        init = {"status": r["status"] or "Hadir",
                "jam_masuk": "" if r["jam_masuk"] is None else _fmt_time(r["jam_masuk"]),
                "jam_keluar": "" if r["jam_keluar"] is None else _fmt_time(r["jam_keluar"]),
                "catatan": r["catatan"] or ""}

        def save(v, kid=r["id"], nama=r["nama"], tgl=d.isoformat()):
            st = v["status"]
            if st not in STATUS_ABSEN:
                return "Status tidak valid."
            try:
                jm, jk = _parse_time(v["jam_masuk"]), _parse_time(v["jam_keluar"])
            except ValueError:
                return "Format jam harus HH:MM (contoh: 08:15)."
            if st in ("Hadir", "Terlambat") and not jm:
                return "Jam masuk wajib diisi untuk status Hadir / Terlambat."
            if jm and jk and jk <= jm:
                return "Jam keluar harus setelah jam masuk."
            if st in ("Izin", "Sakit", "Cuti", "Alpa"):
                jm = jk = None
            if self._abs_upsert(kid, tgl, st, jm, jk, v["catatan"][:150] or None) is None:
                return "Gagal menyimpan absensi."
            self.log("ABSEN", f"Catat manual {nama} {tgl}: {st}")
            self._abs_load()
            self.toast("Absensi disimpan")
            return None

        FormDialog(self, "Catat Absensi", f"{r['nama']} — {d.day} {BULAN[d.month - 1]} {d.year}", fields,
                   save, initial=init, width=520)

    def _abs_all_present(self):
        if not self.require_admin("mencatat absensi"):
            return
        d = self._abs_cur()
        if d is None:
            return
        kosong = [r for r in getattr(self, "abs_rows", []) if not r["status"]]
        if not kosong:
            messagebox.showinfo("Semua Hadir", "Semua karyawan sudah memiliki catatan pada tanggal ini.")
            return
        if not messagebox.askyesno("Semua Hadir",
                                   f"Tandai {len(kosong)} karyawan yang belum absen sebagai HADIR "
                                   f"(masuk {JAM_MASUK:%H:%M}) pada {d.isoformat()}?"):
            return
        data = [(r["id"], d.isoformat(), JAM_MASUK.strftime("%H:%M:%S"), "Hadir") for r in kosong]
        if DB.run("INSERT IGNORE INTO absensi (karyawan_id, tanggal, jam_masuk, status) VALUES (%s,%s,%s,%s)",
                  data, many=True) is not None:
            self.log("ABSEN", f"Menandai {len(data)} karyawan hadir ({d.isoformat()})")
            self._abs_load()
            self.toast(f"{len(data)} karyawan ditandai hadir")

    # ---------- rekap bulanan ----------
    def _abs_rekap(self, parent):
        self.rk_per = tk.StringVar(value=_periods()[0])
        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        tk.Label(bar, text="Periode:", bg=BG, fg=MUTED, font=F_BASE).pack(side="left", padx=(0, 8))
        cb = ttk.Combobox(bar, textvariable=self.rk_per, values=_periods(), state="readonly", width=12,
                          style="Modern.TCombobox", font=F_BASE)
        cb.pack(side="left", ipady=3)
        cb.bind("<<ComboboxSelected>>", lambda e: self._abs_rekap_load())
        cols = [("nama", "Nama Karyawan", 230, "w"), ("departemen", "Departemen", 140, "w"),
                ("hadir", "Hadir", 80, "center"), ("terlambat", "Terlambat", 90, "center"),
                ("izin", "Izin", 70, "center"), ("sakit", "Sakit", 70, "center"),
                ("cuti", "Cuti", 70, "center"), ("alpa", "Alpa", 70, "center")]
        self.rk_tree = self._card_tree(parent, cols)
        self.rk_tree.tag_configure("alpa", foreground="#F87171")
        self._abs_rekap_load()

    def _abs_rekap_load(self):
        start, nxt = _month_range(self.rk_per.get())
        rows = DB.run(
            "SELECT k.id, k.nama, k.departemen, "
            "SUM(a.status='Hadir') AS hadir, SUM(a.status='Terlambat') AS terlambat, "
            "SUM(a.status='Izin') AS izin, SUM(a.status='Sakit') AS sakit, "
            "SUM(a.status='Cuti') AS cuti, SUM(a.status='Alpa') AS alpa "
            "FROM karyawan k LEFT JOIN absensi a ON a.karyawan_id=k.id AND a.tanggal>=%s AND a.tanggal<%s "
            "WHERE k.status<>'Nonaktif' GROUP BY k.id, k.nama, k.departemen ORDER BY k.nama",
            (start.isoformat(), nxt.isoformat()), "all") or []
        self.rk_tree.delete(*self.rk_tree.get_children())
        for i, r in enumerate(rows):
            v = [int(r[k] or 0) for k in ("hadir", "terlambat", "izin", "sakit", "cuti", "alpa")]
            tags = ["even" if i % 2 else "odd"] + (["alpa"] if v[5] else [])
            self.rk_tree.insert("", "end", tags=tags, values=(r["nama"], r["departemen"] or "Umum", *v))

    # ============================================================
    #  CUTI
    # ============================================================
    def build_cuti(self, parent):
        self._modul_tabs(parent, "cuti_tab",
                         [("ajuan", "📝  Pengajuan"), ("saldo", "🧮  Saldo Cuti")],
                         {"ajuan": self._cuti_ajuan, "saldo": self._cuti_saldo})

    def _cuti_ajuan(self, parent):
        self.cuti_filter = tk.StringVar(value="Semua Status")
        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        cb = ttk.Combobox(bar, textvariable=self.cuti_filter, state="readonly", width=16,
                          style="Modern.TCombobox", font=F_BASE,
                          values=["Semua Status", "Menunggu", "Disetujui", "Ditolak"])
        cb.pack(side="left", ipady=3)
        cb.bind("<<ComboboxSelected>>", lambda e: self._cuti_load())
        if self.is_admin:
            HoverButton(bar, "➕  Ajukan Cuti", self._cuti_add, bg=SUCCESS).pack(side="right")
        cols = [("id", "ID", 50, "center"), ("nama", "Karyawan", 190, "w"), ("jenis", "Jenis", 100, "center"),
                ("mulai", "Mulai", 100, "center"), ("selesai", "Selesai", 100, "center"),
                ("hari", "Hari Kerja", 80, "center"), ("alasan", "Alasan", 230, "w"),
                ("status", "Status", 100, "center"), ("oleh", "Diproses Oleh", 140, "w")]
        self.cuti_tree = self._card_tree(parent, cols)
        self.cuti_tree.tag_configure("menunggu", foreground=WARN)
        self.cuti_tree.tag_configure("disetujui", foreground=SUCCESS)
        self.cuti_tree.tag_configure("ditolak", foreground="#F87171")
        foot = tk.Frame(parent, bg=BG)
        foot.pack(fill="x", pady=(12, 0))
        self.cuti_info = tk.Label(foot, text="", bg=BG, fg=MUTED, font=F_SMALL)
        self.cuti_info.pack(side="left")
        if self.is_admin:
            HoverButton(foot, "🗑️  Hapus", self._cuti_delete, bg="#3B1D26", fg="#FCA5A5", hover="#4C2430",
                        pady=7).pack(side="right")
            HoverButton(foot, "❌  Tolak", lambda: self._cuti_proses("Ditolak"), bg=CARD2, fg="#FCA5A5",
                        pady=7).pack(side="right", padx=8)
            HoverButton(foot, "✅  Setujui", lambda: self._cuti_proses("Disetujui"), bg=SUCCESS,
                        pady=7).pack(side="right")
        self._cuti_load()

    def _cuti_load(self):
        f = self.cuti_filter.get()
        sql = ("SELECT c.id, c.karyawan_id, k.nama, c.jenis, c.tgl_mulai, c.tgl_selesai, c.jumlah_hari, "
               "c.alasan, c.status, c.diproses_oleh FROM cuti c JOIN karyawan k ON k.id=c.karyawan_id ")
        if f != "Semua Status":
            rows = DB.run(sql + "WHERE c.status=%s ORDER BY c.id DESC", (f,), "all")
        else:
            rows = DB.run(sql + "ORDER BY c.id DESC", fetch="all")
        self.cuti_rows = rows or []
        self.cuti_tree.delete(*self.cuti_tree.get_children())
        for i, r in enumerate(self.cuti_rows):
            self.cuti_tree.insert("", "end", iid=str(r["id"]), tags=["even" if i % 2 else "odd", r["status"].lower()],
                                  values=(r["id"], r["nama"], r["jenis"], r["tgl_mulai"].strftime("%d-%m-%Y"),
                                          r["tgl_selesai"].strftime("%d-%m-%Y"), r["jumlah_hari"],
                                          r["alasan"] or "-", r["status"], r["diproses_oleh"] or "-"))
        menunggu = sum(1 for r in self.cuti_rows if r["status"] == "Menunggu")
        self.cuti_info.config(text=f"{len(self.cuti_rows)} pengajuan   •   {menunggu} menunggu persetujuan   •   "
                                   f"Jatah cuti tahunan {JATAH_CUTI} hari kerja")

    def _sisa_cuti(self, kid, tahun, exclude_id=0):
        r = DB.run("SELECT COALESCE(SUM(jumlah_hari),0) AS n FROM cuti WHERE karyawan_id=%s AND jenis='Tahunan' "
                   "AND status IN ('Disetujui','Menunggu') AND YEAR(tgl_mulai)=%s AND id<>%s",
                   (kid, tahun, exclude_id), "one", silent=True)
        return JATAH_CUTI - int((r or {}).get("n") or 0)

    def _cuti_add(self):
        if not self.require_admin("mengajukan cuti"):
            return
        emps = DB.run("SELECT id, nama FROM karyawan WHERE status<>'Nonaktif' ORDER BY nama", fetch="all") or []
        if not emps:
            messagebox.showinfo("Cuti", "Belum ada karyawan aktif.")
            return
        today = date.today().isoformat()
        fields = [
            {"key": "karyawan", "label": "Karyawan", "type": "combo", "readonly": True, "full": True,
             "values": [f"{e['id']} - {e['nama']}" for e in emps]},
            {"key": "jenis", "label": "Jenis Cuti", "type": "combo", "values": JENIS_CUTI, "readonly": True,
             "default": "Tahunan", "full": True},
            {"key": "mulai", "label": "Tanggal Mulai (YYYY-MM-DD)", "default": today},
            {"key": "selesai", "label": "Tanggal Selesai (YYYY-MM-DD)", "default": today},
            {"key": "alasan", "label": "Alasan", "required": False, "full": True},
        ]
        FormDialog(self, "Ajukan Cuti", "Hari kerja dihitung Senin–Jumat.", fields, self._cuti_save, width=560)

    def _cuti_save(self, v):
        try:
            kid = int(v["karyawan"].split(" - ")[0])
        except (ValueError, IndexError):
            return "Pilih karyawan terlebih dahulu."
        try:
            d1, d2 = _parse_date(v["mulai"]), _parse_date(v["selesai"])
        except ValueError:
            return "Format tanggal harus YYYY-MM-DD."
        if d2 < d1:
            return "Tanggal selesai tidak boleh sebelum tanggal mulai."
        hari = len(_workday_list(d1, d2))
        if hari == 0:
            return "Rentang tanggal hanya berisi akhir pekan."
        if DB.run("SELECT id FROM cuti WHERE karyawan_id=%s AND status<>'Ditolak' AND tgl_mulai<=%s "
                  "AND tgl_selesai>=%s", (kid, d2.isoformat(), d1.isoformat()), "one", silent=True):
            return "Tanggal bentrok dengan pengajuan cuti lain milik karyawan ini."
        if v["jenis"] == "Tahunan":
            sisa = self._sisa_cuti(kid, d1.year)
            if hari > sisa:
                return f"Sisa cuti tahunan {d1.year} hanya {max(sisa, 0)} hari (diajukan {hari} hari)."
        if DB.run("INSERT INTO cuti (karyawan_id, jenis, tgl_mulai, tgl_selesai, jumlah_hari, alasan) "
                  "VALUES (%s,%s,%s,%s,%s,%s)",
                  (kid, v["jenis"], d1.isoformat(), d2.isoformat(), hari, v["alasan"][:255] or None)) is None:
            return "Gagal menyimpan pengajuan."
        self.log("CUTI", f"Pengajuan cuti {v['jenis']} {hari} hari — {v['karyawan'].split(' - ', 1)[-1]}")
        self._cuti_load()
        self.toast("Pengajuan cuti dicatat")
        return None

    def _cuti_proses(self, status):
        if not self.require_admin("memproses cuti"):
            return
        r = self._selected_row(self.cuti_tree, getattr(self, "cuti_rows", []))
        if not r:
            return
        if r["status"] != "Menunggu":
            messagebox.showinfo("Cuti", f"Pengajuan ini sudah {r['status'].lower()}.")
            return
        if status == "Disetujui" and r["jenis"] == "Tahunan":
            sisa = self._sisa_cuti(r["karyawan_id"], r["tgl_mulai"].year, exclude_id=r["id"])
            if r["jumlah_hari"] > sisa:
                messagebox.showerror("Cuti", f"Sisa cuti tahunan tidak cukup ({max(sisa, 0)} hari).")
                return
        if DB.run("UPDATE cuti SET status=%s, diproses_oleh=%s WHERE id=%s",
                  (status, self.user["nama_lengkap"], r["id"])) is None:
            return
        if status == "Disetujui":   # otomatis tercatat di absensi
            st_abs = "Sakit" if r["jenis"] == "Sakit" else "Cuti"
            data = [(r["karyawan_id"], d.isoformat(), st_abs, f"Cuti #{r['id']}")
                    for d in _workday_list(r["tgl_mulai"], r["tgl_selesai"])]
            DB.run("INSERT INTO absensi (karyawan_id, tanggal, status, catatan) VALUES (%s,%s,%s,%s) "
                   "ON DUPLICATE KEY UPDATE status=VALUES(status), catatan=VALUES(catatan), "
                   "jam_masuk=NULL, jam_keluar=NULL", data, many=True)
        self.log("CUTI", f"{status} cuti #{r['id']} — {r['nama']}")
        self._cuti_load()
        self.toast(f"Cuti {status.lower()}", "success" if status == "Disetujui" else "error")

    def _cuti_delete(self):
        if not self.require_admin("menghapus cuti"):
            return
        r = self._selected_row(self.cuti_tree, getattr(self, "cuti_rows", []))
        if not r:
            return
        if not messagebox.askyesno("Konfirmasi", f"Hapus pengajuan cuti #{r['id']} milik {r['nama']}?"):
            return
        if DB.run("DELETE FROM cuti WHERE id=%s", (r["id"],)) is not None:
            DB.run("DELETE FROM absensi WHERE karyawan_id=%s AND catatan=%s",
                   (r["karyawan_id"], f"Cuti #{r['id']}"), silent=True)
            self.log("CUTI", f"Menghapus cuti #{r['id']} — {r['nama']}")
            self._cuti_load()
            self.toast("Pengajuan cuti dihapus", "error")

    def _cuti_saldo(self, parent):
        tahun = date.today().year
        tk.Label(parent, text=f"Saldo cuti tahunan {tahun} (hanya cuti jenis Tahunan yang disetujui)",
                 bg=BG, fg=MUTED, font=F_BASE).pack(anchor="w", pady=(0, 12))
        cols = [("nama", "Karyawan", 230, "w"), ("departemen", "Departemen", 150, "w"),
                ("jatah", "Jatah", 90, "center"), ("pakai", "Terpakai", 90, "center"),
                ("sisa", "Sisa", 90, "center")]
        tree = self._card_tree(parent, cols)
        tree.tag_configure("habis", foreground="#F87171")
        rows = DB.run(
            "SELECT k.id, k.nama, k.departemen, COALESCE(SUM(c.jumlah_hari),0) AS pakai "
            "FROM karyawan k LEFT JOIN cuti c ON c.karyawan_id=k.id AND c.jenis='Tahunan' "
            "AND c.status='Disetujui' AND YEAR(c.tgl_mulai)=%s "
            "WHERE k.status<>'Nonaktif' GROUP BY k.id, k.nama, k.departemen ORDER BY k.nama",
            (tahun,), "all") or []
        for i, r in enumerate(rows):
            pakai = int(r["pakai"] or 0)
            sisa = JATAH_CUTI - pakai
            tags = ["even" if i % 2 else "odd"] + (["habis"] if sisa <= 0 else [])
            tree.insert("", "end", tags=tags, values=(r["nama"], r["departemen"] or "Umum", JATAH_CUTI, pakai, sisa))

    # ============================================================
    #  SLIP GAJI
    # ============================================================
    def build_slip(self, parent):
        if not self.require_admin("melihat slip gaji"):
            return
        self.slip_per = tk.StringVar(value=_periods()[0])
        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        tk.Label(bar, text="Periode:", bg=BG, fg=MUTED, font=F_BASE).pack(side="left", padx=(0, 8))
        cb = ttk.Combobox(bar, textvariable=self.slip_per, values=_periods(), state="readonly", width=12,
                          style="Modern.TCombobox", font=F_BASE)
        cb.pack(side="left", ipady=3)
        cb.bind("<<ComboboxSelected>>", lambda e: self._slip_load())
        HoverButton(bar, "🖨️  Cetak Semua", lambda: self._slip_print(False), bg=CARD2, fg=TEXT).pack(side="right")
        HoverButton(bar, "🖨️  Cetak Slip", lambda: self._slip_print(True), bg=PRIMARY).pack(side="right", padx=8)
        HoverButton(bar, "⚙️  Generate Periode", self._slip_generate, bg=SUCCESS).pack(side="right")

        cols = [("nama", "Karyawan", 190, "w"), ("pokok", "Gaji Pokok", 115, "e"), ("tunj", "Tunjangan", 105, "e"),
                ("lembur", "Lembur", 100, "e"), ("absen", "Pot. Alpa", 100, "e"), ("bpjs", "BPJS", 100, "e"),
                ("pph", "PPh21", 100, "e"), ("lain", "Pot. Lain", 100, "e"), ("bersih", "Gaji Bersih", 125, "e")]
        self.slip_tree = self._card_tree(parent, cols)
        foot = tk.Frame(parent, bg=BG)
        foot.pack(fill="x", pady=(12, 0))
        self.slip_info = tk.Label(foot, text="", bg=BG, fg=MUTED, font=F_SMALL)
        self.slip_info.pack(side="left")
        HoverButton(foot, "🗑️  Hapus", self._slip_delete, bg="#3B1D26", fg="#FCA5A5", hover="#4C2430",
                    pady=7).pack(side="right")
        HoverButton(foot, "✏️  Ubah Komponen", self._slip_edit, bg=WARN, fg="#1F2937", pady=7).pack(
            side="right", padx=8)
        self._slip_load()

    def _slip_load(self):
        per = self.slip_per.get()
        self.slip_rows = DB.run(
            "SELECT s.*, k.nama FROM slip_gaji s JOIN karyawan k ON k.id=s.karyawan_id "
            "WHERE s.periode=%s ORDER BY k.nama", (per,), "all") or []
        self.slip_tree.delete(*self.slip_tree.get_children())
        total = 0
        for i, s in enumerate(self.slip_rows):
            g = lambda k: int(float(s[k] or 0))
            total += g("gaji_bersih")
            self.slip_tree.insert("", "end", iid=str(s["id"]), tags=["even" if i % 2 else "odd"], values=(
                s["nama"], rp(g("gaji_pokok")), rp(g("tunjangan")), rp(g("lembur")), rp(g("potongan_absen")),
                rp(g("bpjs")), rp(g("pph21")), rp(g("potongan_lain")), rp(g("gaji_bersih"))))
        if self.slip_rows:
            self.slip_info.config(text=f"{_per_label(per)}   •   {len(self.slip_rows)} slip   •   "
                                       f"Total gaji bersih: {rp(total)}   •   PPh21 = estimasi sederhana")
        else:
            self.slip_info.config(text=f"Belum ada slip untuk {_per_label(per)} — klik 'Generate Periode'.")

    def _slip_generate(self):
        if not self.require_admin("membuat slip gaji"):
            return
        per = self.slip_per.get()
        start, nxt = _month_range(per)
        emps = DB.run("SELECT id, gaji FROM karyawan WHERE status<>'Nonaktif'", fetch="all") or []
        have = {r["karyawan_id"] for r in (DB.run("SELECT karyawan_id FROM slip_gaji WHERE periode=%s",
                                                  (per,), "all") or [])}
        baru = [e for e in emps if e["id"] not in have]
        if not baru:
            messagebox.showinfo("Slip Gaji", f"Semua karyawan aktif sudah punya slip {_per_label(per)}.")
            return
        if not messagebox.askyesno("Generate Slip",
                                   f"Buat {len(baru)} slip gaji untuk {_per_label(per)}?\n\n"
                                   "Potongan alpa diambil dari data absensi. Slip yang sudah ada tidak diubah."):
            return
        alpa = {r["karyawan_id"]: int(r["n"]) for r in (DB.run(
            "SELECT karyawan_id, COUNT(*) AS n FROM absensi WHERE status='Alpa' AND tanggal>=%s AND tanggal<%s "
            "GROUP BY karyawan_id", (start.isoformat(), nxt.isoformat()), "all") or [])}
        data = []
        for e in baru:
            h = hitung_slip(float(e["gaji"] or 0), 0, 0, alpa.get(e["id"], 0), 0)
            data.append((e["id"], per, h["gaji_pokok"], h["tunjangan"], h["lembur"], h["alpa_hari"],
                         h["potongan_absen"], h["bpjs"], h["pph21"], h["potongan_lain"], h["gaji_bersih"]))
        if DB.run("INSERT INTO slip_gaji (karyawan_id, periode, gaji_pokok, tunjangan, lembur, alpa_hari, "
                  "potongan_absen, bpjs, pph21, potongan_lain, gaji_bersih) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", data, many=True) is not None:
            self.log("SLIP", f"Generate {len(data)} slip gaji {per}")
            self._slip_load()
            self.toast(f"{len(data)} slip gaji dibuat")

    def _slip_edit(self):
        if not self.require_admin("mengubah slip gaji"):
            return
        s = self._selected_row(self.slip_tree, getattr(self, "slip_rows", []))
        if not s:
            return
        fields = [
            {"key": "gaji_pokok", "label": "Gaji Pokok (Rp)"},
            {"key": "tunjangan", "label": "Tunjangan (Rp)", "required": False},
            {"key": "lembur", "label": "Lembur (Rp)", "required": False},
            {"key": "alpa_hari", "label": "Hari Alpa", "required": False},
            {"key": "potongan_lain", "label": "Potongan Lain (Rp)", "required": False},
            {"key": "catatan", "label": "Catatan", "required": False, "full": True},
        ]
        init = {k: int(float(s[k] or 0)) for k in ("gaji_pokok", "tunjangan", "lembur", "alpa_hari", "potongan_lain")}
        init["catatan"] = s["catatan"] or ""

        def save(v, sid=s["id"], nama=s["nama"]):
            n = {k: _num(v[k]) for k in ("gaji_pokok", "tunjangan", "lembur", "alpa_hari", "potongan_lain")}
            if any(x is None for x in n.values()):
                return "Semua isian harus berupa angka."
            if n["alpa_hari"] > 31:
                return "Hari alpa maksimal 31."
            h = hitung_slip(n["gaji_pokok"], n["tunjangan"], n["lembur"], n["alpa_hari"], n["potongan_lain"])
            if h["gaji_bersih"] < 0:
                return "Potongan melebihi pendapatan (gaji bersih negatif)."
            if DB.run("UPDATE slip_gaji SET gaji_pokok=%s, tunjangan=%s, lembur=%s, alpa_hari=%s, "
                      "potongan_absen=%s, bpjs=%s, pph21=%s, potongan_lain=%s, gaji_bersih=%s, catatan=%s "
                      "WHERE id=%s",
                      (h["gaji_pokok"], h["tunjangan"], h["lembur"], h["alpa_hari"], h["potongan_absen"],
                       h["bpjs"], h["pph21"], h["potongan_lain"], h["gaji_bersih"], v["catatan"][:200] or None,
                       sid)) is None:
                return "Gagal menyimpan slip."
            self.log("SLIP", f"Mengubah slip {nama} ({self.slip_per.get()})")
            self._slip_load()
            self.toast("Slip gaji diperbarui")
            return None

        FormDialog(self, "Ubah Komponen Slip", f"{s['nama']} — {_per_label(s['periode'])}. BPJS, PPh21 & "
                   "potongan alpa dihitung ulang otomatis.", fields, save, initial=init, width=580)

    def _slip_delete(self):
        if not self.require_admin("menghapus slip gaji"):
            return
        s = self._selected_row(self.slip_tree, getattr(self, "slip_rows", []))
        if not s:
            return
        if messagebox.askyesno("Konfirmasi", f"Hapus slip {s['nama']} periode {_per_label(s['periode'])}?"):
            if DB.run("DELETE FROM slip_gaji WHERE id=%s", (s["id"],)) is not None:
                self.log("SLIP", f"Menghapus slip {s['nama']} ({s['periode']})")
                self._slip_load()
                self.toast("Slip gaji dihapus", "error")

    def _slip_print(self, only_selected):
        per = self.slip_per.get()
        sql = ("SELECT s.*, k.nama, k.jabatan, k.departemen FROM slip_gaji s "
               "JOIN karyawan k ON k.id=s.karyawan_id WHERE s.periode=%s")
        if only_selected:
            sel = self.slip_tree.selection()
            if not sel:
                messagebox.showwarning("Peringatan", "Pilih satu slip dari tabel terlebih dahulu.")
                return
            rows = DB.run(sql + " AND s.id=%s", (per, int(sel[0])), "all")
        else:
            rows = DB.run(sql + " ORDER BY k.nama", (per,), "all")
        if not rows:
            messagebox.showinfo("Slip Gaji", "Tidak ada slip untuk dicetak.")
            return
        try:
            f = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
            f.write(self._slip_html(rows, per))
            f.close()
            webbrowser.open("file:///" + f.name.replace("\\", "/"))
        except OSError as err:
            messagebox.showerror("Slip Gaji", str(err))
            return
        self.log("SLIP", f"Mencetak {len(rows)} slip gaji {per}")
        self.toast("Slip dibuka di browser — pilih 'Save as PDF' untuk menyimpan", "info")

    def _slip_html(self, rows, per):
        esc = html_escape
        css = ("body{font-family:Segoe UI,Arial,sans-serif;margin:0;color:#0f172a}"
               ".page{width:720px;margin:28px auto;border:1px solid #cbd5e1;border-radius:10px;padding:28px;"
               "page-break-after:always}.page:last-child{page-break-after:auto}"
               "h1{margin:0;color:#4338ca;font-size:22px}.per{color:#64748b;margin:2px 0 18px}"
               ".info{display:flex;gap:30px;font-size:13px;margin-bottom:18px;border-top:2px solid #4338ca;"
               "padding-top:12px}.info b{display:block;color:#64748b;font-size:10px;text-transform:uppercase}"
               ".cols{display:flex;gap:22px}.cols>div{flex:1}"
               "table{width:100%;border-collapse:collapse;font-size:13px}"
               "th{background:#4338ca;color:#fff;padding:7px;text-align:left}"
               "td{padding:7px;border-bottom:1px solid #e2e8f0}.r{text-align:right}"
               ".tot td{font-weight:bold;background:#f1f5f9}"
               ".net{margin-top:18px;background:#eef2ff;border-radius:8px;padding:14px 18px;display:flex;"
               "justify-content:space-between;font-size:16px;font-weight:bold;color:#3730a3}"
               ".ttd{margin-top:36px;display:flex;justify-content:space-between;font-size:12px;color:#475569}"
               ".ttd div{width:200px;text-align:center}.ttd span{display:block;margin-top:56px;"
               "border-top:1px solid #94a3b8;padding-top:4px}.note{font-size:11px;color:#64748b;margin-top:14px}"
               "@media print{.page{border:none;margin:0 auto}}")
        pages = []
        for s in rows:
            g = lambda k: int(float(s[k] or 0))
            pend = g("gaji_pokok") + g("tunjangan") + g("lembur")
            pot = g("potongan_absen") + g("bpjs") + g("pph21") + g("potongan_lain")
            pages.append(
                "<div class='page'><h1>SLIP GAJI</h1>"
                f"<div class='per'>Periode {esc(_per_label(per))}</div>"
                f"<div class='info'><div><b>Nama</b>{esc(s['nama'])}</div>"
                f"<div><b>Jabatan</b>{esc(s['jabatan'] or '-')}</div>"
                f"<div><b>Departemen</b>{esc(s['departemen'] or 'Umum')}</div>"
                f"<div><b>ID</b>#{s['karyawan_id']}</div></div>"
                "<div class='cols'><div><table><tr><th colspan='2'>PENDAPATAN</th></tr>"
                f"<tr><td>Gaji Pokok</td><td class='r'>{rp(g('gaji_pokok'))}</td></tr>"
                f"<tr><td>Tunjangan</td><td class='r'>{rp(g('tunjangan'))}</td></tr>"
                f"<tr><td>Lembur</td><td class='r'>{rp(g('lembur'))}</td></tr>"
                f"<tr class='tot'><td>Total Pendapatan</td><td class='r'>{rp(pend)}</td></tr></table></div>"
                "<div><table><tr><th colspan='2'>POTONGAN</th></tr>"
                f"<tr><td>Alpa ({g('alpa_hari')} hari)</td><td class='r'>{rp(g('potongan_absen'))}</td></tr>"
                f"<tr><td>BPJS (JHT + Kesehatan)</td><td class='r'>{rp(g('bpjs'))}</td></tr>"
                f"<tr><td>PPh 21 (estimasi)</td><td class='r'>{rp(g('pph21'))}</td></tr>"
                f"<tr><td>Potongan Lain</td><td class='r'>{rp(g('potongan_lain'))}</td></tr>"
                f"<tr class='tot'><td>Total Potongan</td><td class='r'>{rp(pot)}</td></tr></table></div></div>"
                f"<div class='net'><span>GAJI BERSIH (Take Home Pay)</span><span>{rp(g('gaji_bersih'))}</span></div>"
                + (f"<div class='note'>Catatan: {esc(s['catatan'])}</div>" if s["catatan"] else "")
                + "<div class='ttd'><div>Karyawan<span>" + esc(s["nama"]) + "</span></div>"
                  "<div>HRD / Keuangan<span>&nbsp;</span></div></div>"
                  f"<div class='note'>Dicetak {datetime.now():%d-%m-%Y %H:%M} oleh "
                  f"{esc(self.user['nama_lengkap'])}. Dokumen ini dihasilkan oleh sistem.</div></div>")
        return ("<!doctype html><html><head><meta charset='utf-8'><title>Slip Gaji</title><style>" + css +
                "</style></head><body>" + "".join(pages) +
                "<script>window.onload=function(){setTimeout(function(){window.print()},500)}</script>"
                "</body></html>")


# ============================================================
#  APLIKASI UTAMA
# ============================================================
class NexusHR(ModulHR):
    NAV = [
        ("dashboard", "🏠", "Dashboard", False),
        ("karyawan", "👥", "Data Karyawan", False),
        ("laporan", "📊", "Laporan", False),
        ("user", "🔐", "Manajemen User", True),
        ("log", "📜", "Log Aktivitas", True),
        ("absensi", "🕒", "Absensi", False),
        ("cuti", "🌴", "Cuti", False),
        ("slip", "🧾", "Slip Gaji", True),
        ("profil", "👤", "Profil Saya", False),
        ("pengaturan", "⚙️", "Pengaturan", True),
    ]
    TITLES = {
        "dashboard": ("Dashboard", "Ringkasan data & aktivitas terkini"),
        "karyawan": ("Data Karyawan", "Kelola seluruh data karyawan perusahaan"),
        "laporan": ("Laporan", "Ringkasan penggajian & cetak laporan"),
        "user": ("Manajemen User", "Atur akun & hak akses pengguna aplikasi"),
        "log": ("Log Aktivitas", "Riwayat aktivitas pengguna di sistem"),
        "absensi": ("Absensi", "Kehadiran harian & rekap bulanan"),
        "cuti": ("Cuti", "Pengajuan, persetujuan & saldo cuti"),
        "slip": ("Slip Gaji", "Buat & cetak slip gaji per periode"),
        "profil": ("Profil Saya", "Informasi akun & keamanan"),
        "pengaturan": ("Pengaturan", "Struktur database & penerapan 4 pilar OOP"),
    }
    EMP_COLS = [
        ("id", "ID", 60, "center"),
        ("nama", "Nama Lengkap", 190, "w"),
        ("jabatan", "Jabatan", 150, "w"),
        ("departemen", "Departemen", 120, "w"),
        ("email", "Email", 210, "w"),
        ("telepon", "Telepon", 120, "w"),
        ("gaji", "Gaji (Rp)", 120, "e"),
        ("tanggal_masuk", "Tgl Masuk", 100, "center"),
        ("status", "Status", 90, "center"),
    ]

    def __init__(self, root):
        self.root = root
        root.title("Nexus HR — Sistem Manajemen Karyawan")
        root.configure(bg=BG)
        self._icon = None
        self._logo_login = None
        self._logo_side = None
        self.apply_window_icon()
        root.minsize(1100, 680)
        center_window(root, 1280, 760)
        setup_styles(root)
        self.user = None
        self.page = None
        self.clock_job = None
        self.settings = load_settings()
        self.emp_data = []
        self.sort_col, self.sort_rev = "id", False
        init_db()
        self.show_login()

    def apply_window_icon(self):
        """Pasang ikon jendela + taskbar. Cetak penyebab ke konsol jika gagal."""
        root = self.root
        if os.path.exists(LOGO_ICO):
            try:
                root.iconbitmap(default=LOGO_ICO)     # berlaku juga untuk semua dialog
                return
            except tk.TclError as err:
                print(f"[ikon] iconbitmap gagal: {err}")
            # cadangan: ubah .ico -> PhotoImage lewat Pillow
            try:
                from PIL import Image, ImageTk
                img = Image.open(LOGO_ICO)
                sizes = img.ico.sizes() if hasattr(img, "ico") else []
                if sizes:
                    img.size = max(sizes)
                self._icon = ImageTk.PhotoImage(img.convert("RGBA"))
                root.iconphoto(True, self._icon)
                return
            except Exception as err:
                print(f"[ikon] cadangan Pillow gagal: {err}")
        else:
            print(f"[ikon] file tidak ditemukan: {LOGO_ICO}")
        try:
            if os.path.exists(LOGO_PNG):
                self._icon = tk.PhotoImage(file=LOGO_PNG)
            else:
                self._icon = make_app_icon()
            root.iconphoto(True, self._icon)
        except tk.TclError as err:
            print(f"[ikon] iconphoto gagal: {err}")

    # ---------------- umum ----------------
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
    #  LOGIN
    # ============================================================
    def show_login(self):
        self.stop_clock()
        self.unbind_shortcuts()
        self.clear()
        self.user = None
        self.page = None

        wrap = tk.Frame(self.root, bg=BG)
        wrap.pack(fill="both", expand=True)

        left = tk.Canvas(wrap, bg="#1E1B4B", highlightthickness=0)
        left.place(relx=0, rely=0, relwidth=0.55, relheight=1)
        left.bind("<Configure>", lambda e: self.draw_login_art(left))

        right = tk.Frame(wrap, bg=BG)
        right.place(relx=0.55, rely=0, relwidth=0.45, relheight=1)

        card = tk.Frame(right, bg=BG)
        card.place(relx=0.5, rely=0.5, anchor="center", width=390)
        self.login_card = card

        tk.Label(card, text="Selamat Datang 👋", font=("Segoe UI", 26, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(card, text="Masuk untuk mengelola data karyawan Anda.",
                 font=("Segoe UI", 11), bg=BG, fg=MUTED).pack(anchor="w", pady=(4, 28))

        self.username_var = tk.StringVar(value=self.settings.get("username", ""))
        self.password_var = tk.StringVar()
        self.remember_var = tk.BooleanVar(value=bool(self.settings.get("username")))

        tk.Label(card, text="USERNAME", font=("Segoe UI", 8, "bold"), bg=BG, fg=MUTED).pack(anchor="w")
        e1 = ModernEntry(card, textvariable=self.username_var, icon="👤")
        e1.pack(fill="x", pady=(6, 16))
        tk.Label(card, text="PASSWORD", font=("Segoe UI", 8, "bold"), bg=BG, fg=MUTED).pack(anchor="w")
        e2 = ModernEntry(card, textvariable=self.password_var, icon="🔒", show="•", toggle=True)
        e2.pack(fill="x", pady=(6, 12))

        opt = tk.Frame(card, bg=BG)
        opt.pack(fill="x")
        tk.Checkbutton(opt, text="Ingat username", variable=self.remember_var, bg=BG, fg=MUTED,
                       activebackground=BG, activeforeground=TEXT, selectcolor=FIELD,
                       font=F_SMALL, bd=0, highlightthickness=0, cursor="hand2").pack(side="left")

        self.login_err = tk.Label(card, text="", bg=BG, fg="#FCA5A5", font=F_SMALL, anchor="w")
        self.login_err.pack(fill="x", pady=(10, 0))

        self.login_btn = HoverButton(card, "Masuk ke Dashboard   →", self.do_login,
                                     font=("Segoe UI", 11, "bold"), pady=13)
        self.login_btn.pack(fill="x", pady=(10, 18))

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x")
        tk.Label(card, text="Akun awal:  admin  /  admin123", font=F_SMALL, bg=BG,
                 fg=MUTED).pack(pady=(14, 0))

        for w in (e1.entry, e2.entry):
            w.bind("<Return>", lambda e: self.do_login())
        (e2 if self.username_var.get() else e1).focus()

    def draw_login_art(self, c):
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 50 or h < 50:
            return
        c1, c2, c3 = "#1E1B4B", "#4338CA", "#7C3AED"
        for y in range(0, h, 2):
            t = y / h
            col = mix(c1, c2, t * 2) if t < 0.5 else mix(c2, c3, (t - 0.5) * 2)
            c.create_rectangle(0, y, w, y + 2, fill=col, outline="")
        # dekorasi lingkaran
        c.create_oval(-120, -120, 220, 220, fill=mix(c2, "#FFFFFF", 0.07), outline="")
        for r in (130, 210, 290, 370):
            c.create_oval(w * 0.88 - r, h * 0.92 - r, w * 0.88 + r, h * 0.92 + r,
                          outline=mix(c3, "#FFFFFF", 0.16), width=1)
        c.create_oval(w * 0.72, h * 0.12, w * 0.72 + 90, h * 0.12 + 90,
                      fill=mix(c3, "#FFFFFF", 0.1), outline="")

        px = max(48, w * 0.1)
        # ---- logo + nama aplikasi (memakai logo.png jika ada) ----
        if self._logo_login is None:
            self._logo_login = load_logo(44)
        if self._logo_login:
            c.create_image(px, 70, image=self._logo_login, anchor="w")
            c.create_text(px + 56, 70, text="NEXUS HR", anchor="w", fill="white",
                          font=("Segoe UI", 20, "bold"))
        else:
            c.create_text(px, 70, text="⚡  NEXUS HR", anchor="w", fill="white",
                          font=("Segoe UI", 20, "bold"))
        c.create_text(px, h * 0.34, text="Kelola tim Anda\nlebih cerdas & cepat.", anchor="nw",
                      fill="white", font=("Segoe UI", 34, "bold"))
        c.create_text(px, h * 0.34 + 140, anchor="nw", fill="#C7D2FE", font=("Segoe UI", 12),
                      width=max(w - 2 * px, 200),
                      text="Platform manajemen karyawan terpadu: data terpusat, "
                           "laporan instan, dan akses yang aman.")
        feats = ["Dashboard statistik real-time", "Import & export data CSV",
                 "Hak akses berbasis peran", "Log aktivitas lengkap"]
        y0 = h * 0.34 + 215
        for i, ft in enumerate(feats):
            c.create_oval(px, y0 + i * 36, px + 22, y0 + i * 36 + 22, fill=mix(c3, "#FFFFFF", 0.22), outline="")
            c.create_text(px + 11, y0 + i * 36 + 11, text="✓", fill="white", font=("Segoe UI", 9, "bold"))
            c.create_text(px + 36, y0 + i * 36 + 11, text=ft, anchor="w", fill="#E0E7FF",
                          font=("Segoe UI", 11))
        c.create_text(px, h - 36, text="v2.0  •  Python + MySQL", anchor="w", fill="#A5B4FC",
                      font=F_SMALL)

    def login_error(self, msg):
        self.login_err.config(text="⚠  " + msg)
        self.shake(self.login_card)

    def shake(self, widget, n=0):
        offs = [-12, 12, -9, 9, -5, 5, 0]
        if n >= len(offs) or not widget.winfo_exists():
            return
        widget.place_configure(x=offs[n])
        self.root.after(35, lambda: self.shake(widget, n + 1))

    def do_login(self):
        u = self.username_var.get().strip()
        p = self.password_var.get()
        if not u or not p:
            self.login_error("Username dan password wajib diisi.")
            return
        self.login_btn.config(text="Memeriksa…")
        self.root.update_idletasks()
        row = DB.run("SELECT username, password, nama_lengkap, role FROM users WHERE username=%s",
                     (u,), "one")
        if DB.failed:
            self.login_btn.config(text="Masuk ke Dashboard   →")
            return
        ok = False
        if row:
            stored = row["password"] or ""
            if stored == hash_pw(p):
                ok = True
            elif stored == p:  # kompatibel dengan password lama (plain) -> upgrade ke hash
                ok = True
                DB.run("UPDATE users SET password=%s WHERE username=%s", (hash_pw(p), row["username"]),
                       silent=True)
        if not ok:
            self.login_btn.config(text="Masuk ke Dashboard   →")
            self.login_error("Username atau password salah.")
            return
        self.settings["username"] = u if self.remember_var.get() else ""
        save_settings(self.settings)
        self.user = row
        self.log("LOGIN", f"{row['nama_lengkap']} masuk ke sistem")
        self.show_main()

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
        # ---- logo sidebar (memakai logo.png jika ada) ----
        self._logo_side = load_logo(36)   # simpan di self agar tidak dihapus garbage collector
        if self._logo_side:
            tk.Label(brand, image=self._logo_side, bg=SURFACE).pack(side="left")
        else:
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

    # ============================================================
    #  DASHBOARD
    # ============================================================
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

    def stat_card(self, g, col, icon, title, value, color, fmt, sub, sub_color=MUTED, progress=None):
        box, body = self.rcard(g, accent=color)
        self.gridcard(box, 1, col * 3, 3)
        top = tk.Frame(body, bg=CARD)
        top.pack(fill="x", pady=(6, 0))
        tk.Label(top, text=title.upper(), font=("Segoe UI", 8, "bold"), bg=CARD, fg=MUTED).pack(side="left")
        tk.Label(top, text=icon, font=("Segoe UI Emoji", 12), bg=mix(CARD, color, 0.22), fg=color,
                 padx=7, pady=3).pack(side="right")
        lbl = tk.Label(body, text=fmt(0), font=("Segoe UI", 22, "bold"), bg=CARD, fg=TEXT)
        lbl.pack(anchor="w", pady=(8, 2))
        tk.Label(body, text=sub, font=F_SMALL, bg=CARD, fg=sub_color).pack(anchor="w")
        if progress is not None:
            track = tk.Frame(body, bg=CARD2, height=5)
            track.pack(fill="x", pady=(8, 2))
            tk.Frame(track, bg=color).place(x=0, y=0, relheight=1, relwidth=max(0.02, min(progress, 1)))
        self.count_up(lbl, value, fmt)

    # ---------- penggambar grafik ----------
    def draw_empty(self, c, text, sub=""):
        w, h = c.winfo_width(), c.winfo_height()
        c.create_oval(w / 2 - 28, h / 2 - 58, w / 2 + 28, h / 2 - 2, fill=CARD2, outline="")
        c.create_text(w / 2, h / 2 - 30, text="📊", fill=MUTED, font=("Segoe UI Emoji", 18))
        c.create_text(w / 2, h / 2 + 22, text=text, fill=TEXT, font=F_BASE_B)
        if sub:
            c.create_text(w / 2, h / 2 + 44, text=sub, fill=MUTED, font=F_SMALL)

    def draw_growth(self, c, p, series):
        c.delete("all")
        c._hits = []
        w, h = c.winfo_width(), c.winfo_height()
        if w < 80 or h < 80:
            return
        mx = max(v for _, v, _ in series)
        if mx == 0:
            self.draw_empty(c, "Belum ada data pertumbuhan", "Tambahkan karyawan untuk melihat grafik")
            return
        L, R, T, B = 40, w - 22, 20, h - 30
        top, step = nice_scale(mx, 4, integer=True)
        for i in range(5):
            y = B - (B - T) * i / 4
            opts = {"dash": (2, 4)} if i else {}
            c.create_line(L, y, R, y, fill=BORDER, **opts)
            c.create_text(L - 8, y, text=str(int(step * i)), fill=MUTED, anchor="e", font=("Segoe UI", 8))
        n = len(series)
        xs = [L + (R - L) * i / (n - 1) for i in range(n)]
        pts = [(xs[i], B - (B - T) * (series[i][1] / top) * p) for i in range(n)]
        flat = [v for pt in pts for v in pt]
        c.create_polygon([xs[0], B] + flat + [xs[-1], B], fill=mix(CARD, PRIMARY, 0.2), outline="")
        c.create_line(*flat, fill=PRIMARY, width=3, smooth=True)
        for i, (lab, cum, new) in enumerate(series):
            x, y = pts[i]
            c.create_oval(x - 5, y - 5, x + 5, y + 5, fill=CARD, outline=PRIMARY, width=2)
            c.create_text(x, B + 14, text=lab, fill=MUTED, font=("Segoe UI", 8))
            if p > 0.95:
                c.create_text(x, y - 14, text=str(cum), fill=TEXT, font=("Segoe UI", 8, "bold"))
            c._hits.append((x - 22, T, x + 22, B, f"{lab}: {cum} karyawan\n+{new} bergabung"))

    def draw_bars(self, c, p, data):
        c.delete("all")
        c._hits = []
        w, h = c.winfo_width(), c.winfo_height()
        if w < 80 or h < 80:
            return
        if not data:
            self.draw_empty(c, "Belum ada data gaji", "Data akan muncul setelah ada karyawan")
            return
        L, R, T, B = 58, w - 14, 20, h - 30
        mx = max(v for _, v, _, _ in data) or 1
        top, step = nice_scale(mx, 4)
        for i in range(5):
            y = B - (B - T) * i / 4
            opts = {"dash": (2, 4)} if i else {}
            c.create_line(L, y, R, y, fill=BORDER, **opts)
            c.create_text(L - 8, y, text=short_num(step * i), fill=MUTED, anchor="e", font=("Segoe UI", 8))
        slot = (R - L) / len(data)
        bw = min(54, slot * 0.55)
        for i, (lab, v, col, cnt) in enumerate(data):
            cx = L + slot * (i + 0.5)
            y = B - (B - T) * v / top * p
            c.create_rectangle(cx - bw / 2, y, cx + bw / 2, B, fill=col, outline="")
            c.create_rectangle(cx - bw / 2, y, cx + bw / 2, min(y + 3, B), fill=lighten(col, 0.4), outline="")
            if p > 0.95:
                c.create_text(cx, y - 10, text=short_num(v), fill=TEXT, font=("Segoe UI", 8, "bold"))
            c.create_text(cx, B + 14, text=lab if len(lab) <= 11 else lab[:10] + "…", fill=MUTED,
                          font=("Segoe UI", 8))
            c._hits.append((cx - slot / 2, T, cx + slot / 2, B,
                            f"{lab}\nRata-rata {rp(v)}\n{cnt} karyawan"))

    def draw_donut(self, c, p, data):
        c.delete("all")
        c._hits = []
        w, h = c.winfo_width(), c.winfo_height()
        if w < 80 or h < 60:
            return
        total = sum(v for _, v, _ in data)
        if total == 0:
            self.draw_empty(c, "Belum ada data status")
            return
        size = min(h - 16, w * 0.52)
        cx, cy = size / 2 + 6, h / 2
        bb = (cx - size / 2 + 12, cy - size / 2 + 12, cx + size / 2 - 12, cy + size / 2 - 12)
        c.create_oval(*bb, outline=CARD2, width=24)
        start = 90
        for lab, v, col in data:
            ext = (-359.99 if len(data) == 1 else -360 * v / total) * p
            c.create_arc(*bb, start=start, extent=ext, style="arc", outline=col, width=24)
            start += ext
        c.create_text(cx, cy - 8, text=str(int(total * p)), font=("Segoe UI", 24, "bold"), fill=TEXT)
        c.create_text(cx, cy + 18, text="Karyawan", font=F_SMALL, fill=MUTED)
        lx = cx + size / 2 + 20
        ly = cy - (len(data) - 1) * 18
        for i, (lab, v, col) in enumerate(data):
            y = ly + i * 36
            c.create_rectangle(lx, y - 6, lx + 12, y + 6, fill=col, outline="")
            c.create_text(lx + 20, y - 7, text=lab, anchor="w", fill=TEXT, font=F_BASE_B)
            c.create_text(lx + 20, y + 9, text=f"{v} orang • {v * 100 // total}%", anchor="w", fill=MUTED,
                          font=("Segoe UI", 8))

    def draw_dist(self, c, p, buckets):
        c.delete("all")
        c._hits = []
        w, h = c.winfo_width(), c.winfo_height()
        if w < 80 or h < 60:
            return
        total = sum(n for _, n, _ in buckets)
        if total == 0:
            self.draw_empty(c, "Belum ada data gaji")
            return
        L, R = 80, w - 34
        rh = (h - 10) / len(buckets)
        mx = max(n for _, n, _ in buckets) or 1
        for i, (lab, n, col) in enumerate(buckets):
            y = 5 + rh * (i + 0.5)
            c.create_text(4, y, text=lab, anchor="w", fill=MUTED, font=F_SMALL)
            round_rect(c, L, y - 8, R, y + 8, 8, fill=CARD2, outline="")
            bw = (R - L) * n / mx * p
            if n > 0 and bw > 4:
                round_rect(c, L, y - 8, L + max(bw, 16), y + 8, 8, fill=col, outline="")
            c.create_text(w - 4, y, text=str(n), anchor="e", fill=TEXT, font=F_SMALL_B)
            c._hits.append((0, y - rh / 2, w, y + rh / 2, f"{lab}\n{n} karyawan ({n * 100 // total}%)"))

    def draw_calendar(self, c, p, joins):
        c.delete("all")
        c._hits = []
        w, h = c.winfo_width(), c.winfo_height()
        if w < 100 or h < 100:
            return
        today = date.today()
        weeks = calendar.Calendar(0).monthdayscalendar(today.year, today.month)
        c.create_text(w / 2, 14, text=f"{BULAN[today.month - 1]} {today.year}", fill=TEXT,
                      font=("Segoe UI", 11, "bold"))
        cw = (w - 12) / 7
        top = 52
        for i, dn in enumerate(["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]):
            c.create_text(6 + cw * (i + 0.5), 36, text=dn, fill="#F87171" if i == 6 else MUTED,
                          font=("Segoe UI", 8, "bold"))
        rh = min(30, (h - top - 4) / len(weeks))
        for r, week in enumerate(weeks):
            for i, d in enumerate(week):
                if d == 0:
                    continue
                cx, cy = 6 + cw * (i + 0.5), top + rh * (r + 0.5)
                if d == today.day:
                    c.create_oval(cx - 13, cy - 13, cx + 13, cy + 13, fill=PRIMARY, outline="")
                c.create_text(cx, cy, text=str(d), font=("Segoe UI", 9, "bold" if d == today.day else "normal"),
                              fill="white" if d == today.day else ("#F87171" if i == 6 else TEXT))
                if d in joins:
                    c.create_oval(cx - 2.5, cy + 9, cx + 2.5, cy + 14, fill=ACCENT, outline="")
                    c._hits.append((cx - cw / 2, cy - rh / 2, cx + cw / 2, cy + rh / 2,
                                    f"{d} {BULAN[today.month - 1]}\nBergabung: " + ", ".join(joins[d][:3])))

    # ---------- halaman dashboard ----------
    def build_dashboard(self, parent):
        rows = DB.run("SELECT id, nama, jabatan, departemen, email, gaji, tanggal_masuk, status "
                      "FROM karyawan ORDER BY id", fetch="all") or []
        today = date.today()
        total = len(rows)
        stt = lambda r: r["status"] or "Aktif"
        has_date = lambda r: hasattr(r["tanggal_masuk"], "year")
        aktif = sum(1 for r in rows if stt(r) == "Aktif")
        gajis = [float(r["gaji"] or 0) for r in rows]
        tgaji = sum(gajis)
        rata = tgaji / total if total else 0
        maks = max(gajis) if gajis else 0
        by_dept = {}
        for r in rows:
            by_dept.setdefault(r["departemen"] or "Umum", []).append(float(r["gaji"] or 0))
        baru = sum(1 for r in rows if has_date(r) and
                   (r["tanggal_masuk"].year, r["tanggal_masuk"].month) == (today.year, today.month))

        sf = ScrollFrame(parent)
        sf.pack(fill="both", expand=True)
        g = sf.inner
        for c in range(12):
            g.columnconfigure(c, weight=1, uniform="g")

        # ---------- HERO ----------
        hero = tk.Canvas(g, height=172, bg=BG, highlightthickness=0)
        hero.grid(row=0, column=0, columnspan=12, sticky="ew", pady=(0, 16))
        hero_btns = []

        def hbtn(text, cmd, primary=False):
            if primary:
                b = HoverButton(hero, text, cmd, bg="#FFFFFF", fg="#4338CA", hover="#E0E7FF", pady=8)
            else:
                base = mix("#7C3AED", "#FFFFFF", 0.2)
                b = HoverButton(hero, text, cmd, bg=base, fg="white", hover=mix(base, "#FFFFFF", 0.18), pady=8)
            hero_btns.append(b)

        if self.is_admin:
            hbtn("➕  Tambah Karyawan", self.quick_add, True)
            hbtn("📥  Import CSV", self.quick_import)
            if total == 0:
                hbtn("🧪  Isi Data Contoh", self.seed_demo)
        hbtn("👥  Lihat Semua", lambda: self.navigate("karyawan"), not self.is_admin)
        hbtn("🔄  Segarkan", lambda: self.navigate("dashboard"))

        if total:
            sub = f"Anda mengelola {total} karyawan di {len(by_dept)} departemen — {aktif} sedang aktif."
        else:
            sub = "Belum ada data karyawan. Tambah data, import CSV, atau isi data contoh untuk mencoba semua fitur."

        def draw_hero(e=None):
            w, h = hero.winfo_width(), hero.winfo_height()
            if w < 200:
                return
            hero.delete("all")
            r = 22
            c1, c2, c3 = "#4F46E5", "#7C3AED", "#C026D3"
            for x in range(0, w, 3):
                t = x / w
                col = mix(c1, c2, t * 2) if t < 0.5 else mix(c2, c3, (t - 0.5) * 2)
                if x < r:
                    ins = r - math.sqrt(max(r * r - (r - x) ** 2, 0))
                elif x > w - r:
                    ins = r - math.sqrt(max(r * r - (x - (w - r)) ** 2, 0))
                else:
                    ins = 0
                hero.create_rectangle(x, ins, x + 3, h - ins, fill=col, outline="")
            cx, cy = w - 120, h / 2
            for rad in (80, 58, 38):
                hero.create_oval(cx - rad, cy - rad, cx + rad, cy + rad,
                                 outline=mix(c3, "#FFFFFF", 0.28), width=1)
            hero.create_text(cx, cy - 10, text=str(today.day), fill="white", font=("Segoe UI", 30, "bold"))
            hero.create_text(cx, cy + 20, text=HARI[today.weekday()].upper(), fill="#E9D5FF",
                             font=("Segoe UI", 8, "bold"))
            hero.create_text(cx, cy + 34, text=f"{BULAN[today.month - 1][:3].upper()} {today.year}",
                             fill="#E9D5FF", font=("Segoe UI", 8))
            for dx, dy, rr in ((w * 0.55, 30, 4), (w * 0.62, 130, 6), (w * 0.45, 140, 3), (w * 0.7, 50, 3)):
                hero.create_oval(dx - rr, dy - rr, dx + rr, dy + rr, fill=mix(c2, "#FFFFFF", 0.35), outline="")
            hero.create_text(36, 36, anchor="w", fill="white", font=("Segoe UI", 21, "bold"),
                             text=f"{self.salam()}, {self.user['nama_lengkap']} 👋")
            hero.create_text(36, 70, anchor="w", fill="#E0E7FF", font=("Segoe UI", 11),
                             width=max(w - 380, 300), text=sub)
            x = 36
            for b in hero_btns:
                hero.create_window(x, 104, window=b, anchor="nw")
                x += b.winfo_reqwidth() + 10

        hero.bind("<Configure>", draw_hero)

        # ---------- KARTU STATISTIK ----------
        n_fmt = lambda v: f"{int(round(v)):,}".replace(",", ".")
        pct = aktif / total if total else 0
        self.stat_card(g, 0, "👥", "Total Karyawan", total, PRIMARY, n_fmt,
                       f"+{baru} bergabung bulan ini" if baru else "Belum ada yang baru bulan ini",
                       SUCCESS if baru else MUTED)
        self.stat_card(g, 1, "✅", "Karyawan Aktif", aktif, SUCCESS, n_fmt,
                       f"{int(pct * 100)}% dari total karyawan", MUTED, progress=pct)
        self.stat_card(g, 2, "💰", "Total Gaji / Bulan", tgaji, WARN, rp_short,
                       f"{len(by_dept)} departemen" if total else "Belum ada data")
        self.stat_card(g, 3, "📈", "Rata-rata Gaji", rata, PINK, rp_short,
                       f"Tertinggi {rp_short(maks)}" if total else "Belum ada data")

        # ---------- PERTUMBUHAN ----------
        def add_months(d, k):
            y = d.year + (d.month - 1 + k) // 12
            m = (d.month - 1 + k) % 12 + 1
            return date(y, m, 1)

        series = []
        for k in range(5, -1, -1):
            m0 = add_months(today.replace(day=1), -k)
            nxt = add_months(m0, 1)
            cum = sum(1 for r in rows if not has_date(r) or r["tanggal_masuk"] < nxt)
            new = sum(1 for r in rows if has_date(r) and m0 <= r["tanggal_masuk"] < nxt)
            series.append((BULAN[m0.month - 1][:3], cum, new))
        box, body = self.rcard(g, "Pertumbuhan Karyawan", "Jumlah karyawan 6 bulan terakhir")
        self.gridcard(box, 2, 0, 6)
        self.chart_canvas(body, lambda c, p: self.draw_growth(c, p, series))

        # ---------- GAJI PER DEPARTEMEN ----------
        dept_rows = sorted(by_dept.items(), key=lambda kv: sum(kv[1]) / len(kv[1]), reverse=True)[:7]
        bars = [(d, sum(v) / len(v), PALETTE[i % len(PALETTE)], len(v)) for i, (d, v) in enumerate(dept_rows)]
        box, body = self.rcard(g, "Rata-rata Gaji per Departemen", "Arahkan kursor ke batang untuk detail")
        self.gridcard(box, 2, 6, 6)
        self.chart_canvas(body, lambda c, p: self.draw_bars(c, p, bars))

        # ---------- STATUS / DISTRIBUSI / KALENDER ----------
        counts = {}
        for r in rows:
            counts[stt(r)] = counts.get(stt(r), 0) + 1
        order = STATUS_LIST + [k for k in counts if k not in STATUS_LIST]
        slices = [(k, counts[k], STATUS_COLOR.get(k, VIOLET)) for k in order if counts.get(k)]
        box, body = self.rcard(g, "Status Karyawan", "Komposisi status kepegawaian")
        self.gridcard(box, 3, 0, 4)
        self.chart_canvas(body, lambda c, p: self.draw_donut(c, p, slices), 236)

        edges = [("< 3 jt", 0, 3e6), ("3 – 5 jt", 3e6, 5e6), ("5 – 8 jt", 5e6, 8e6),
                 ("8 – 12 jt", 8e6, 12e6), ("> 12 jt", 12e6, float("inf"))]
        buckets = [(lab, sum(1 for x in gajis if lo <= x < hi), PALETTE[i]) for i, (lab, lo, hi) in enumerate(edges)]
        box, body = self.rcard(g, "Distribusi Gaji", "Sebaran karyawan menurut rentang gaji")
        self.gridcard(box, 3, 4, 4)
        self.chart_canvas(body, lambda c, p: self.draw_dist(c, p, buckets), 236)

        joins = {}
        for r in rows:
            if has_date(r) and (r["tanggal_masuk"].year, r["tanggal_masuk"].month) == (today.year, today.month):
                joins.setdefault(r["tanggal_masuk"].day, []).append(r["nama"])
        box, body = self.rcard(g, "Kalender", "Titik biru = ada karyawan baru bergabung")
        self.gridcard(box, 3, 8, 4)
        self.chart_canvas(body, lambda c, p: self.draw_calendar(c, p, joins), 236)

        # ---------- DAFTAR ----------
        def ago(dt):
            if not dt:
                return ""
            s = int((datetime.now() - dt).total_seconds())
            if s < 60:
                return "baru saja"
            if s < 3600:
                return f"{s // 60} mnt lalu"
            if s < 86400:
                return f"{s // 3600} jam lalu"
            return f"{s // 86400} hari lalu"

        # karyawan terbaru
        box, body = self.rcard(g, "Karyawan Terbaru", "5 data terakhir ditambahkan")
        self.gridcard(box, 4, 0, 4, pady=(0, 8))
        recent = sorted(rows, key=lambda r: r["id"], reverse=True)[:5]
        if not recent:
            tk.Label(body, text="Belum ada data karyawan.", bg=CARD, fg=MUTED, font=F_BASE).pack(pady=24)
        for e in recent:
            row = tk.Frame(body, bg=CARD)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=(e["nama"] or "?")[:1].upper(), bg=PALETTE[e["id"] % len(PALETTE)], fg="white",
                     font=("Segoe UI", 10, "bold"), width=3, pady=4).pack(side="left")
            info = tk.Frame(row, bg=CARD)
            info.pack(side="left", padx=10)
            tk.Label(info, text=e["nama"], bg=CARD, fg=TEXT, font=F_BASE_B).pack(anchor="w")
            tk.Label(info, text=f"{e['jabatan'] or '-'} • {e['departemen'] or 'Umum'}", bg=CARD, fg=MUTED,
                     font=("Segoe UI", 8)).pack(anchor="w")
            tk.Label(row, text=rp_short(e["gaji"]), bg=CARD, fg=SUCCESS, font=F_SMALL_B).pack(side="right")

        # gaji tertinggi
        box, body = self.rcard(g, "Gaji Tertinggi", "Top 5 penghasilan karyawan")
        self.gridcard(box, 4, 4, 4, pady=(0, 8))
        top5 = sorted(rows, key=lambda r: float(r["gaji"] or 0), reverse=True)[:5]
        mxg = float(top5[0]["gaji"] or 1) if top5 else 1
        if not top5:
            tk.Label(body, text="Belum ada data karyawan.", bg=CARD, fg=MUTED, font=F_BASE).pack(pady=24)
        for i, e in enumerate(top5):
            wrap = tk.Frame(body, bg=CARD)
            wrap.pack(fill="x", pady=3)
            row = tk.Frame(wrap, bg=CARD)
            row.pack(fill="x")
            tk.Label(row, text=str(i + 1), bg=PALETTE[i % len(PALETTE)], fg="white",
                     font=("Segoe UI", 9, "bold"), width=2).pack(side="left")
            tk.Label(row, text=e["nama"] if len(e["nama"]) < 20 else e["nama"][:18] + "…", bg=CARD, fg=TEXT,
                     font=F_SMALL_B).pack(side="left", padx=10)
            tk.Label(row, text=rp_short(e["gaji"]), bg=CARD, fg=WARN, font=F_SMALL_B).pack(side="right")
            track = tk.Frame(wrap, bg=CARD2, height=4)
            track.pack(fill="x", pady=(3, 0))
            tk.Frame(track, bg=PALETTE[i % len(PALETTE)]).place(
                x=0, y=0, relheight=1, relwidth=max(0.03, float(e["gaji"] or 0) / mxg))

        # aktivitas
        icons = {"LOGIN": "🔑", "TAMBAH": "➕", "UBAH": "✏️", "HAPUS": "🗑️",
                 "EXPORT": "📤", "IMPORT": "📥", "USER": "👤", "PASSWORD": "🔒",
                 "ABSEN": "🕒", "CUTI": "🌴", "SLIP": "🧾"}
        acts = DB.run("SELECT waktu, pengguna, aksi, detail FROM aktivitas ORDER BY id DESC LIMIT 5",
                      fetch="all") or []
        box, body = self.rcard(g, "Aktivitas Terbaru", "Riwayat tindakan di sistem")
        self.gridcard(box, 4, 8, 4, pady=(0, 8))
        if not acts:
            tk.Label(body, text="Belum ada aktivitas.", bg=CARD, fg=MUTED, font=F_BASE).pack(pady=24)
        for a in acts:
            row = tk.Frame(body, bg=CARD)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=icons.get(a["aksi"], "•"), bg=CARD2, fg=ACCENT, font=("Segoe UI Emoji", 10),
                     width=3, pady=4).pack(side="left")
            info = tk.Frame(row, bg=CARD)
            info.pack(side="left", padx=10)
            det = a["detail"] or ""
            tk.Label(info, text=det if len(det) < 30 else det[:28] + "…", bg=CARD, fg=TEXT,
                     font=F_SMALL).pack(anchor="w")
            tk.Label(info, text=f"{a['pengguna']} • {ago(a['waktu'])}", bg=CARD, fg=MUTED,
                     font=("Segoe UI", 8)).pack(anchor="w")

    def quick_add(self):
        self.navigate("karyawan")
        self.root.after(150, self.add_employee)

    def quick_import(self):
        self.navigate("karyawan")
        self.root.after(150, self.import_csv)

    # ---------- data contoh ----------
    def seed_demo(self):
        if not self.require_admin("mengisi data contoh"):
            return
        if not messagebox.askyesno(
                "Isi Data Contoh",
                "Tambahkan 24 data karyawan contoh agar grafik dan semua fitur bisa dicoba?\n\n"
                "Email memakai domain @contoh.id sehingga mudah dikenali dan dihapus."):
            return
        demo = [
            ("Budi Santoso", "Software Engineer", "IT", 12500000, 11, "Aktif"),
            ("Siti Nurhaliza", "HR Manager", "HRD", 15000000, 14, "Aktif"),
            ("Agus Prasetyo", "Akuntan", "Keuangan", 9500000, 9, "Aktif"),
            ("Dewi Lestari", "Digital Marketer", "Marketing", 8000000, 8, "Aktif"),
            ("Rizky Ramadhan", "Supervisor Operasional", "Operasional", 10500000, 13, "Aktif"),
            ("Putri Anggraini", "UI/UX Designer", "IT", 9800000, 7, "Aktif"),
            ("Eko Wijaya", "Operator Produksi", "Produksi", 5200000, 12, "Aktif"),
            ("Rina Marlina", "Sales Executive", "Penjualan", 6800000, 6, "Aktif"),
            ("Andi Kurniawan", "DevOps Engineer", "IT", 14000000, 5, "Aktif"),
            ("Maya Sari", "Recruiter", "HRD", 7200000, 5, "Cuti"),
            ("Fajar Nugroho", "Staf Keuangan", "Keuangan", 6500000, 4, "Aktif"),
            ("Lia Permata", "Content Creator", "Marketing", 6200000, 4, "Aktif"),
            ("Hendra Gunawan", "Kepala Produksi", "Produksi", 13500000, 10, "Aktif"),
            ("Nurul Hidayah", "Sales Manager", "Penjualan", 14500000, 10, "Aktif"),
            ("Yusuf Maulana", "Staf Gudang", "Operasional", 4800000, 3, "Aktif"),
            ("Tiara Kusuma", "Data Analyst", "IT", 11000000, 3, "Aktif"),
            ("Bagas Saputra", "QC Inspector", "Produksi", 5600000, 2, "Aktif"),
            ("Citra Dewanti", "Brand Manager", "Marketing", 12000000, 2, "Aktif"),
            ("Dimas Aditya", "Customer Service", "Penjualan", 4900000, 1, "Aktif"),
            ("Ayu Wulandari", "Payroll Specialist", "Keuangan", 8500000, 1, "Aktif"),
            ("Galih Pratama", "Staf Logistik", "Operasional", 5500000, 0, "Aktif"),
            ("Wulan Sari", "Admin HR", "HRD", 5300000, 0, "Aktif"),
            ("Irfan Hakim", "Backend Developer", "IT", 13000000, 15, "Nonaktif"),
            ("Mega Putri", "Sales Executive", "Penjualan", 6400000, 0, "Aktif"),
        ]
        have = {(r["email"] or "").lower() for r in (DB.run("SELECT email FROM karyawan", fetch="all", silent=True) or [])}
        today = date.today()
        data = []
        for i, (nama, jab, dep, gaji, bln, status) in enumerate(demo):
            email = re.sub(r"[^a-z0-9]+", ".", nama.lower()).strip(".") + "@contoh.id"
            if email in have:
                continue
            back = bln * 30 + ((i * 7) % 20 if bln else (i * 2) % max(today.day, 1))
            tgl = (today - timedelta(days=back)).isoformat()
            telp = f"08{12 + i % 8}{(i * 7654321 + 1234567) % 10 ** 8:08d}"
            data.append((nama, jab, dep, email, telp, gaji, tgl, status))
        if not data:
            messagebox.showinfo("Data Contoh", "Data contoh sudah ada di database.")
            return
        if DB.run("INSERT INTO karyawan (nama, jabatan, departemen, email, telepon, gaji, tanggal_masuk, status) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", data, many=True) is not None:
            self.log("TAMBAH", f"Menambah {len(data)} data karyawan contoh")
            self.navigate("dashboard")
            self.toast(f"{len(data)} data contoh ditambahkan")

    # ---------- cari cepat (Ctrl+K) ----------
    def palette_commands(self):
        cmds = [("🏠  Buka Dashboard", lambda: self.navigate("dashboard")),
                ("👥  Buka Data Karyawan", lambda: self.navigate("karyawan")),
                ("📊  Buka Laporan", lambda: self.navigate("laporan")),
                ("🕒  Buka Absensi", lambda: self.navigate("absensi")),
                ("🌴  Buka Cuti", lambda: self.navigate("cuti"))]
        if self.is_admin:
            cmds += [("🧾  Buka Slip Gaji", lambda: self.navigate("slip")),
                     ("🔐  Buka Manajemen User", lambda: self.navigate("user")),
                     ("📜  Buka Log Aktivitas", lambda: self.navigate("log")),
                     ("⚙️  Buka Pengaturan", lambda: self.navigate("pengaturan")),
                     ("➕  Tambah Karyawan Baru", self.quick_add),
                     ("📥  Import dari CSV", self.quick_import),
                     ("🧪  Isi Data Contoh", self.seed_demo)]
        cmds += [("👤  Buka Profil Saya", lambda: self.navigate("profil")),
                 ("🔄  Segarkan Halaman", lambda: self.navigate(self.page or "dashboard")),
                 ("⎋  Keluar", self.logout)]
        return cmds

    def goto_employee(self, nama):
        self.navigate("karyawan")
        self.cari_var.set(nama)

    def open_palette(self):
        old = getattr(self, "_pal", None)
        if old is not None and old.winfo_exists():
            old.destroy()
        emps = DB.run("SELECT nama, jabatan, departemen, email FROM karyawan ORDER BY nama",
                      fetch="all", silent=True) or []
        win = tk.Toplevel(self.root)
        self._pal = win
        win.overrideredirect(True)
        win.configure(bg=PRIMARY)
        box = tk.Frame(win, bg=SURFACE)
        box.pack(padx=1, pady=1, fill="both", expand=True)
        var = tk.StringVar()
        ent = ModernEntry(box, textvariable=var, icon="🔍", bg=SURFACE, width=40)
        ent.pack(fill="x", padx=14, pady=(14, 8))
        lb = tk.Listbox(box, bg=SURFACE, fg=TEXT, selectbackground=PRIMARY, selectforeground="white", bd=0,
                        highlightthickness=0, font=("Segoe UI", 11), activestyle="none", height=10)
        lb.pack(fill="both", expand=True, padx=14, pady=(0, 6))
        tk.Label(box, text="Ketik untuk mencari menu / karyawan   •   ↑↓ pilih   •   Enter buka   •   Esc tutup",
                 bg=SURFACE, fg=MUTED, font=("Segoe UI", 8)).pack(pady=(0, 10))
        items = []

        def refresh(*_):
            q = var.get().strip().lower()
            items.clear()
            lb.delete(0, "end")
            for label, fn in self.palette_commands():
                if q in label.lower():
                    items.append((label, fn))
            if q:
                n = 0
                for e in emps:
                    hay = " ".join(str(e[k] or "") for k in ("nama", "jabatan", "departemen", "email")).lower()
                    if q in hay:
                        items.append((f"👤  {e['nama']}  —  {e['jabatan'] or '-'} · {e['departemen'] or 'Umum'}",
                                      lambda nm=e["nama"]: self.goto_employee(nm)))
                        n += 1
                        if n >= 8:
                            break
            for label, _ in items:
                lb.insert("end", "  " + label)
            if items:
                lb.selection_set(0)
                lb.activate(0)

        def run(*_):
            sel = lb.curselection()
            if not sel:
                return "break"
            fn = items[sel[0]][1]
            win.destroy()
            self.root.after(60, fn)
            return "break"

        def move(d):
            sel = lb.curselection()
            i = max(0, min((sel[0] if sel else -1) + d, len(items) - 1))
            lb.selection_clear(0, "end")
            lb.selection_set(i)
            lb.see(i)
            return "break"

        def lost_focus(e):
            def chk():
                if not win.winfo_exists():
                    return
                f = win.focus_get()
                if f is None or not str(f).startswith(str(win)):
                    win.destroy()
            win.after(150, chk)

        ent.entry.bind("<Down>", lambda e: move(1))
        ent.entry.bind("<Up>", lambda e: move(-1))
        ent.entry.bind("<Return>", run)
        win.bind("<Escape>", lambda e: win.destroy())
        ent.entry.bind("<Escape>", lambda e: win.destroy())
        lb.bind("<Double-Button-1>", run)
        lb.bind("<Return>", run)
        win.bind("<FocusOut>", lost_focus)
        var.trace_add("write", refresh)
        refresh()
        w = 600
        win.update_idletasks()
        h = win.winfo_reqheight()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_rooty() + 110
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.lift()
        win.focus_force()
        ent.focus()

    # ---------- kartu detail karyawan ----------
    def show_detail(self):
        r = self.selected_employee()
        if not r:
            return
        today = date.today()
        tm = r["tanggal_masuk"]
        if hasattr(tm, "year"):
            months = max((today.year - tm.year) * 12 + today.month - tm.month - (1 if today.day < tm.day else 0), 0)
            masa = f"{months // 12} tahun {months % 12} bulan"
            tgl = f"{tm.day} {BULAN[tm.month - 1]} {tm.year}"
        else:
            masa, tgl = "-", "-"
        win = tk.Toplevel(self.root)
        win.configure(bg=SURFACE)
        win.title("Detail Karyawan")
        win.resizable(False, False)
        win.transient(self.root)
        W = 480
        hc = tk.Canvas(win, width=W, height=130, bg=SURFACE, highlightthickness=0)
        hc.pack()
        for x in range(0, W, 2):
            hc.create_rectangle(x, 0, x + 2, 130, fill=mix("#4F46E5", "#C026D3", x / W), outline="")
        hc.create_oval(28, 33, 92, 97, fill="white", outline="")
        hc.create_text(60, 65, text=(r["nama"] or "?")[:1].upper(), fill=PRIMARY, font=("Segoe UI", 26, "bold"))
        hc.create_text(110, 52, anchor="w", text=r["nama"], fill="white", font=("Segoe UI", 16, "bold"))
        hc.create_text(110, 78, anchor="w", text=f"{r['jabatan'] or '-'}  •  {r['departemen'] or 'Umum'}",
                       fill="#E0E7FF", font=("Segoe UI", 10))
        stt = r["status"] or "Aktif"
        hc.create_text(W - 28, 24, anchor="e", text=f"●  {stt}", fill=STATUS_COLOR.get(stt, "white"),
                       font=("Segoe UI", 10, "bold"))
        info = tk.Frame(win, bg=SURFACE)
        info.pack(fill="x", padx=30, pady=(16, 6))
        for k, v in (("ID Karyawan", f"#{r['id']}"), ("Email", r["email"] or "-"), ("Telepon", r["telepon"] or "-"),
                     ("Gaji", rp(r["gaji"])), ("Tanggal Masuk", tgl), ("Masa Kerja", masa)):
            row = tk.Frame(info, bg=SURFACE)
            row.pack(fill="x", pady=6)
            tk.Label(row, text=k.upper(), bg=SURFACE, fg=MUTED, font=("Segoe UI", 8, "bold"), width=16,
                     anchor="w").pack(side="left")
            tk.Label(row, text=v, bg=SURFACE, fg=TEXT, font=F_BASE_B, anchor="w").pack(side="left")
            tk.Frame(info, bg=BORDER, height=1).pack(fill="x")
        foot = tk.Frame(win, bg=SURFACE)
        foot.pack(fill="x", padx=30, pady=(12, 22))
        HoverButton(foot, "Tutup", win.destroy, bg=CARD2, fg=TEXT, padx=22).pack(side="right")
        if self.is_admin:
            HoverButton(foot, "✏️  Ubah", lambda: (win.destroy(), self.edit_employee()), bg=WARN, fg="#1F2937",
                        padx=22).pack(side="right", padx=10)
        win.bind("<Escape>", lambda e: win.destroy())
        win.update_idletasks()
        center_window(win, W, win.winfo_reqheight(), self.root)
        try:
            win.wait_visibility()
            win.grab_set()
        except tk.TclError:
            pass

    # ============================================================
    #  LAPORAN
    # ============================================================
    def dept_summary(self, rows):
        d = {}
        for r in rows:
            d.setdefault(r["departemen"] or "Umum", []).append(r)
        out = []
        for name, lst in sorted(d.items()):
            g = [float(x["gaji"] or 0) for x in lst]
            out.append({"dept": name, "n": len(lst),
                        "aktif": sum(1 for x in lst if (x["status"] or "Aktif") == "Aktif"),
                        "total": sum(g), "avg": sum(g) / len(g), "max": max(g), "min": min(g)})
        return out

    def build_laporan(self, parent):
        rows = DB.run("SELECT nama, jabatan, departemen, email, telepon, gaji, tanggal_masuk, status "
                      "FROM karyawan ORDER BY departemen, nama", fetch="all") or []
        self.report_rows = rows
        summ = self.dept_summary(rows)
        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        tk.Label(bar, text="Ringkasan penggajian & komposisi karyawan per departemen", bg=BG, fg=MUTED,
                 font=F_BASE).pack(side="left")
        HoverButton(bar, "🖨️  Cetak / Simpan PDF", self.print_report, bg=PRIMARY).pack(side="right")
        HoverButton(bar, "📤  Export Ringkasan", self.export_summary, bg=CARD2, fg=TEXT).pack(side="right", padx=8)

        outer, inner = self.make_card(parent)
        outer.pack(fill="both", expand=True)
        inner.pack_configure(padx=0, pady=0)
        cols = [("dept", "Departemen", 200, "w"), ("n", "Jumlah", 90, "center"), ("aktif", "Aktif", 90, "center"),
                ("total", "Total Gaji", 170, "e"), ("avg", "Rata-rata", 150, "e"),
                ("max", "Tertinggi", 150, "e"), ("min", "Terendah", 150, "e")]
        tf, tree = self.make_tree(inner, cols)
        tf.pack(fill="both", expand=True)
        tree.tag_configure("total", background=CARD2, foreground=ACCENT)
        for i, s in enumerate(summ):
            tree.insert("", "end", tags=["even" if i % 2 else "odd"],
                        values=(s["dept"], s["n"], s["aktif"], rp(s["total"]), rp(s["avg"]), rp(s["max"]), rp(s["min"])))
        if summ:
            g = [float(r["gaji"] or 0) for r in rows]
            tree.insert("", "end", tags=["total"], values=(
                "TOTAL", len(rows), sum(s["aktif"] for s in summ), rp(sum(g)), rp(sum(g) / len(g)),
                rp(max(g)), rp(min(g))))
        else:
            tk.Label(tf, text="📭   Belum ada data untuk dilaporkan", bg=CARD, fg=MUTED,
                     font=("Segoe UI", 12)).place(relx=0.5, rely=0.5, anchor="center")

    def print_report(self):
        rows = getattr(self, "report_rows", [])
        if not rows:
            messagebox.showinfo("Laporan", "Belum ada data karyawan.")
            return
        esc = html_escape
        summ = self.dept_summary(rows)
        tr1 = "".join(
            f"<tr><td>{esc(s['dept'])}</td><td class='c'>{s['n']}</td><td class='c'>{s['aktif']}</td>"
            f"<td class='r'>{rp(s['total'])}</td><td class='r'>{rp(s['avg'])}</td>"
            f"<td class='r'>{rp(s['max'])}</td><td class='r'>{rp(s['min'])}</td></tr>" for s in summ)
        tr2 = ""
        for i, r in enumerate(rows, 1):
            tgl = r["tanggal_masuk"].strftime("%d-%m-%Y") if hasattr(r["tanggal_masuk"], "strftime") else "-"
            tr2 += (f"<tr><td class='c'>{i}</td><td>{esc(r['nama'] or '')}</td><td>{esc(r['jabatan'] or '')}</td>"
                    f"<td>{esc(r['departemen'] or '')}</td><td>{esc(r['email'] or '')}</td>"
                    f"<td class='r'>{rp(r['gaji'])}</td><td class='c'>{tgl}</td><td class='c'>{esc(r['status'] or '')}</td></tr>")
        total = sum(float(r["gaji"] or 0) for r in rows)
        css = ("body{font-family:Segoe UI,Arial,sans-serif;margin:32px;color:#0f172a}"
               "h1{margin:0;color:#4338ca}.sub{color:#64748b;margin:4px 0 24px}"
               "h2{margin:28px 0 8px;font-size:16px}"
               "table{border-collapse:collapse;width:100%;font-size:12px}"
               "th{background:#4338ca;color:#fff;padding:8px;text-align:left}"
               "td{padding:7px 8px;border-bottom:1px solid #e2e8f0}tr:nth-child(even) td{background:#f8fafc}"
               ".c{text-align:center}.r{text-align:right}"
               ".kpi{display:flex;gap:16px}.kpi div{flex:1;border:1px solid #e2e8f0;border-radius:10px;padding:12px}"
               ".kpi b{display:block;font-size:20px;color:#4338ca}")
        body = (f"<h1>Laporan Karyawan — Nexus HR</h1>"
                f"<div class='sub'>Dicetak {datetime.now():%d-%m-%Y %H:%M} oleh {esc(self.user['nama_lengkap'])}</div>"
                f"<div class='kpi'><div>Total Karyawan<b>{len(rows)}</b></div>"
                f"<div>Departemen<b>{len(summ)}</b></div><div>Total Gaji / Bulan<b>{rp(total)}</b></div>"
                f"<div>Rata-rata Gaji<b>{rp(total / len(rows))}</b></div></div>"
                "<h2>Ringkasan per Departemen</h2><table><tr><th>Departemen</th><th>Jumlah</th><th>Aktif</th>"
                "<th>Total Gaji</th><th>Rata-rata</th><th>Tertinggi</th><th>Terendah</th></tr>" + tr1 + "</table>"
                "<h2>Daftar Karyawan</h2><table><tr><th>No</th><th>Nama</th><th>Jabatan</th><th>Departemen</th>"
                "<th>Email</th><th>Gaji</th><th>Tgl Masuk</th><th>Status</th></tr>" + tr2 + "</table>"
                "<script>window.onload=function(){setTimeout(function(){window.print()},500)}</script>")
        html = "<!doctype html><html><head><meta charset='utf-8'><title>Laporan Karyawan</title><style>" + css + \
               "</style></head><body>" + body + "</body></html>"
        try:
            f = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
            f.write(html)
            f.close()
            webbrowser.open("file:///" + f.name.replace("\\", "/"))
        except OSError as err:
            messagebox.showerror("Laporan", str(err))
            return
        self.log("EXPORT", "Mencetak laporan karyawan")
        self.toast("Laporan dibuka di browser — pilih 'Save as PDF' untuk menyimpan", "info")

    def export_summary(self):
        summ = self.dept_summary(getattr(self, "report_rows", []))
        if not summ:
            messagebox.showinfo("Export", "Belum ada data untuk diexport.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("File CSV", "*.csv")],
                                            initialfile=f"ringkasan_departemen_{datetime.now():%Y%m%d}.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["departemen", "jumlah", "aktif", "total_gaji", "rata_rata", "tertinggi", "terendah"])
                for s in summ:
                    w.writerow([s["dept"], s["n"], s["aktif"], int(s["total"]), int(s["avg"]),
                                int(s["max"]), int(s["min"])])
        except OSError as err:
            messagebox.showerror("Export Gagal", str(err))
            return
        self.log("EXPORT", "Export ringkasan departemen ke CSV")
        self.toast("Ringkasan berhasil diexport")

    # ============================================================
    #  DATA KARYAWAN
    # ============================================================
    def build_karyawan(self, parent):
        self.cari_var = tk.StringVar()
        self.f_dept = tk.StringVar(value="Semua Departemen")
        self.f_status = tk.StringVar(value="Semua Status")
        self.filtered = []

        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        self.search_box = ModernEntry(bar, textvariable=self.cari_var, icon="🔍", bg=CARD, width=26)
        self.search_box.pack(side="left")
        self.cb_dept = ttk.Combobox(bar, textvariable=self.f_dept, state="readonly", width=19,
                                    style="Modern.TCombobox", font=F_BASE, values=["Semua Departemen"])
        self.cb_dept.pack(side="left", padx=(10, 0), ipady=3)
        self.cb_status = ttk.Combobox(bar, textvariable=self.f_status, state="readonly", width=14,
                                      style="Modern.TCombobox", font=F_BASE,
                                      values=["Semua Status"] + STATUS_LIST)
        self.cb_status.pack(side="left", padx=10, ipady=3)

        if self.is_admin:
            HoverButton(bar, "➕  Tambah", self.add_employee, bg=SUCCESS).pack(side="right", padx=(8, 0))
            HoverButton(bar, "📥  Import", self.import_csv, bg=CARD2, fg=TEXT).pack(side="right", padx=(8, 0))
        HoverButton(bar, "📤  Export", self.export_csv, bg=CARD2, fg=TEXT).pack(side="right", padx=(8, 0))
        if self.is_admin:
            HoverButton(bar, "📄  Template", self.save_template, bg=CARD2, fg=TEXT).pack(side="right", padx=(8, 0))

        outer, inner = self.make_card(parent)
        outer.pack(fill="both", expand=True)
        inner.pack_configure(padx=0, pady=0)
        tframe, self.tree = self.make_tree(inner, self.EMP_COLS)
        tframe.pack(fill="both", expand=True)
        for key, head, *_ in self.EMP_COLS:
            self.tree.heading(key, command=lambda k=key: self.sort_by(k))
        self.empty_lbl = tk.Label(tframe, text="📭   Tidak ada data yang cocok", bg=CARD, fg=MUTED,
                                  font=("Segoe UI", 12))

        foot = tk.Frame(parent, bg=BG)
        foot.pack(fill="x", pady=(12, 0))
        self.info_lbl = tk.Label(foot, text="", bg=BG, fg=MUTED, font=F_SMALL)
        self.info_lbl.pack(side="left")
        if self.is_admin:
            HoverButton(foot, "🗑️  Hapus", self.delete_employee, bg="#3B1D26", fg="#FCA5A5",
                        hover="#4C2430", pady=7).pack(side="right")
            HoverButton(foot, "✏️  Ubah", self.edit_employee, bg=WARN, fg="#1F2937", pady=7).pack(
                side="right", padx=8)
        tk.Label(foot, text="Klik 2× baris untuk ubah  •  Klik kanan untuk menu  •  Ctrl+N tambah, Ctrl+F cari",
                 bg=BG, fg="#52617D", font=("Segoe UI", 8)).pack(side="right", padx=14)

        # menu klik kanan
        self.menu = tk.Menu(self.tree, tearoff=0, bg=CARD2, fg=TEXT, activebackground=PRIMARY,
                            activeforeground="white", bd=0, font=F_BASE)
        self.menu.add_command(label="🔎  Lihat Detail", command=self.show_detail)
        if self.is_admin:
            self.menu.add_command(label="✏️  Ubah", command=self.edit_employee)
            self.menu.add_command(label="🗑️  Hapus", command=self.delete_employee)
        self.menu.add_separator()
        self.menu.add_command(label="📋  Salin Email", command=self.copy_email)
        self.tree.bind("<Button-3>", self.popup_menu)
        self.tree.bind("<Double-1>", lambda e: self.edit_employee() if self.is_admin else self.show_detail())
        self.tree.bind("<Delete>", lambda e: self.delete_employee() if self.is_admin else None)

        self.cari_var.trace_add("write", lambda *a: self.render_table())
        self.cb_dept.bind("<<ComboboxSelected>>", lambda e: self.render_table())
        self.cb_status.bind("<<ComboboxSelected>>", lambda e: self.render_table())
        self.load_employees()

    def load_employees(self):
        self.emp_data = DB.run(
            "SELECT id, nama, jabatan, departemen, email, telepon, gaji, tanggal_masuk, status FROM karyawan",
            fetch="all") or []
        depts = sorted({r["departemen"] or "Umum" for r in self.emp_data})
        vals = ["Semua Departemen"] + depts
        self.cb_dept["values"] = vals
        if self.f_dept.get() not in vals:
            self.f_dept.set("Semua Departemen")
        self.render_table()

    def sort_by(self, col):
        if self.sort_col == col:
            self.sort_rev = not self.sort_rev
        else:
            self.sort_col, self.sort_rev = col, False
        self.render_table()

    def render_table(self):
        if not hasattr(self, "tree") or not self.tree.winfo_exists():
            return
        kw = self.cari_var.get().strip().lower()
        d, s = self.f_dept.get(), self.f_status.get()
        res = []
        for r in self.emp_data:
            if d != "Semua Departemen" and (r["departemen"] or "Umum") != d:
                continue
            if s != "Semua Status" and (r["status"] or "Aktif") != s:
                continue
            hay = " ".join(str(r[k] or "") for k in ("nama", "jabatan", "departemen", "email", "telepon")).lower()
            if kw and kw not in hay:
                continue
            res.append(r)

        def keyf(r):
            v = r[self.sort_col]
            if self.sort_col in ("id", "gaji"):
                return float(v or 0)
            return str(v or "").lower()

        res.sort(key=keyf, reverse=self.sort_rev)
        self.filtered = res

        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(res):
            tgl = r["tanggal_masuk"]
            tgl = tgl.strftime("%d-%m-%Y") if hasattr(tgl, "strftime") else "-"
            stt = r["status"] or "Aktif"
            tags = ["even" if i % 2 else "odd"]
            if stt == "Cuti":
                tags.append("cuti")
            elif stt == "Nonaktif":
                tags.append("nonaktif")
            self.tree.insert("", "end", iid=str(r["id"]), tags=tags, values=(
                r["id"], r["nama"], r["jabatan"] or "-", r["departemen"] or "Umum", r["email"] or "-",
                r["telepon"] or "-", rp(r["gaji"]).replace("Rp ", ""), tgl, stt))

        for key, head, *_ in self.EMP_COLS:
            arrow = (" ▼" if self.sort_rev else " ▲") if key == self.sort_col else ""
            self.tree.heading(key, text=head + arrow)

        if res:
            self.empty_lbl.place_forget()
        else:
            self.empty_lbl.place(relx=0.5, rely=0.5, anchor="center")
        tot = sum(float(r["gaji"] or 0) for r in res)
        self.info_lbl.config(text=f"Menampilkan {len(res)} dari {len(self.emp_data)} karyawan   •   "
                                  f"Total gaji tampil: {rp(tot)}")

    def selected_employee(self, warn=True):
        sel = self.tree.selection()
        if sel:
            for r in self.emp_data:
                if str(r["id"]) == sel[0]:
                    return r
        if warn:
            messagebox.showwarning("Peringatan", "Pilih data karyawan dari tabel terlebih dahulu.")
        return None

    def popup_menu(self, e):
        iid = self.tree.identify_row(e.y)
        if iid:
            self.tree.selection_set(iid)
            self.menu.tk_popup(e.x_root, e.y_root)

    def copy_email(self):
        r = self.selected_employee()
        if r and r["email"]:
            self.root.clipboard_clear()
            self.root.clipboard_append(r["email"])
            self.toast("Email disalin ke clipboard", "info")

    # ---------- validasi & CRUD ----------
    def employee_fields(self):
        jab = DB.run("SELECT DISTINCT jabatan FROM karyawan WHERE jabatan IS NOT NULL AND jabatan<>'' "
                     "ORDER BY jabatan", fetch="all", silent=True) or []
        dep = DB.run("SELECT DISTINCT departemen FROM karyawan WHERE departemen IS NOT NULL ORDER BY departemen",
                     fetch="all", silent=True) or []
        depts = sorted(set(DEPT_DEFAULT) | {r["departemen"] for r in dep})
        return [
            {"key": "nama", "label": "Nama Lengkap", "full": True},
            {"key": "jabatan", "label": "Jabatan", "type": "combo", "values": [r["jabatan"] for r in jab]},
            {"key": "departemen", "label": "Departemen", "type": "combo", "values": depts, "default": "Umum"},
            {"key": "email", "label": "Email"},
            {"key": "telepon", "label": "No. Telepon"},
            {"key": "gaji", "label": "Gaji (Rp)"},
            {"key": "tanggal_masuk", "label": "Tanggal Masuk (YYYY-MM-DD)", "required": False,
             "default": date.today().isoformat()},
            {"key": "status", "label": "Status", "type": "combo", "values": STATUS_LIST,
             "readonly": True, "default": "Aktif"},
        ]

    def validate_employee(self, v, emp_id=None):
        if not v.get("nama"):
            return "Nama lengkap wajib diisi.", None
        if not v.get("jabatan"):
            return "Jabatan wajib diisi.", None
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v.get("email", "")):
            return "Format email tidak valid.", None
        digits = re.sub(r"\D", "", v.get("telepon", ""))
        if not 8 <= len(digits) <= 15:
            return "No. telepon harus 8–15 digit.", None
        raw = v.get("gaji", "")
        if not re.fullmatch(r"(?i)(rp)?\s*[\d.,\s]+", raw):
            return "Gaji harus berupa angka (contoh: 5000000).", None
        gaji = int(re.sub(r"\D", "", raw) or 0)
        tgl = v.get("tanggal_masuk") or date.today().isoformat()
        try:
            datetime.strptime(tgl, "%Y-%m-%d")
        except ValueError:
            return "Format tanggal harus YYYY-MM-DD (contoh: 2026-01-31).", None
        stt = v.get("status") or "Aktif"
        if stt not in STATUS_LIST:
            stt = "Aktif"
        dup = DB.run("SELECT id FROM karyawan WHERE email=%s AND id<>%s", (v["email"], emp_id or 0),
                     "one", silent=True)
        if dup:
            return "Email sudah dipakai karyawan lain.", None
        return None, {"nama": v["nama"], "jabatan": v["jabatan"], "departemen": v.get("departemen") or "Umum",
                      "email": v["email"], "telepon": v["telepon"], "gaji": gaji,
                      "tanggal_masuk": tgl, "status": stt}

    def add_employee(self):
        if not self.require_admin("menambah data"):
            return
        FormDialog(self, "Tambah Karyawan", "Lengkapi data karyawan baru.", self.employee_fields(),
                   self._save_new)

    def _save_new(self, v):
        err, d = self.validate_employee(v)
        if err:
            return err
        ok = DB.run(
            "INSERT INTO karyawan (nama, jabatan, departemen, email, telepon, gaji, tanggal_masuk, status) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (d["nama"], d["jabatan"], d["departemen"], d["email"], d["telepon"], d["gaji"],
             d["tanggal_masuk"], d["status"]))
        if ok is None:
            return "Gagal menyimpan ke database."
        self.log("TAMBAH", f"Menambah karyawan {d['nama']}")
        self.load_employees()
        self.toast("Karyawan berhasil ditambahkan")
        return None

    def edit_employee(self):
        if not self.require_admin("mengubah data"):
            return
        r = self.selected_employee()
        if not r:
            return
        init = dict(r)
        init["gaji"] = int(float(r["gaji"] or 0))
        init["tanggal_masuk"] = r["tanggal_masuk"].isoformat() if hasattr(r["tanggal_masuk"], "isoformat") else ""
        FormDialog(self, "Ubah Data Karyawan", f"Mengubah data: {r['nama']}", self.employee_fields(),
                   lambda v, i=r["id"]: self._save_edit(i, v), initial=init)

    def _save_edit(self, emp_id, v):
        err, d = self.validate_employee(v, emp_id)
        if err:
            return err
        ok = DB.run(
            "UPDATE karyawan SET nama=%s, jabatan=%s, departemen=%s, email=%s, telepon=%s, gaji=%s, "
            "tanggal_masuk=%s, status=%s WHERE id=%s",
            (d["nama"], d["jabatan"], d["departemen"], d["email"], d["telepon"], d["gaji"],
             d["tanggal_masuk"], d["status"], emp_id))
        if ok is None:
            return "Gagal memperbarui data."
        self.log("UBAH", f"Mengubah data karyawan {d['nama']} (ID {emp_id})")
        self.load_employees()
        self.toast("Data karyawan berhasil diperbarui")
        return None

    def delete_employee(self):
        if not self.require_admin("menghapus data"):
            return
        r = self.selected_employee()
        if not r:
            return
        if messagebox.askyesno("Konfirmasi Hapus", f"Yakin ingin menghapus karyawan:\n\n{r['nama']} ({r['jabatan']})?"):
            if DB.run("DELETE FROM karyawan WHERE id=%s", (r["id"],)) is not None:
                self.log("HAPUS", f"Menghapus karyawan {r['nama']} (ID {r['id']})")
                self.load_employees()
                self.toast("Data karyawan dihapus", "error")

    # ---------- import / export ----------
    CSV_HEAD = ["nama", "jabatan", "departemen", "email", "telepon", "gaji", "tanggal_masuk", "status"]

    def export_csv(self):
        rows = self.filtered
        if not rows:
            messagebox.showinfo("Export", "Tidak ada data untuk diexport.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("File CSV", "*.csv")],
                                            initialfile=f"karyawan_{datetime.now():%Y%m%d_%H%M}.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["id"] + self.CSV_HEAD)
                for r in rows:
                    w.writerow([r["id"], r["nama"], r["jabatan"], r["departemen"], r["email"], r["telepon"],
                                int(float(r["gaji"] or 0)),
                                r["tanggal_masuk"].isoformat() if hasattr(r["tanggal_masuk"], "isoformat") else "",
                                r["status"]])
        except OSError as err:
            messagebox.showerror("Export Gagal", str(err))
            return
        self.log("EXPORT", f"Export {len(rows)} data karyawan ke CSV")
        self.toast(f"{len(rows)} data berhasil diexport")

    def save_template(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("File CSV", "*.csv")],
                                            initialfile="template_import_karyawan.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(self.CSV_HEAD)
                w.writerow(["Budi Santoso", "Staf IT", "IT", "budi@contoh.com", "081234567890",
                            "6500000", date.today().isoformat(), "Aktif"])
        except OSError as err:
            messagebox.showerror("Gagal", str(err))
            return
        self.toast("Template CSV disimpan", "info")

    def import_csv(self):
        if not self.require_admin("mengimport data"):
            return
        path = filedialog.askopenfilename(filetypes=[("File CSV", "*.csv")])
        if not path:
            return
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;")
                except csv.Error:
                    dialect = csv.excel
                reader = csv.DictReader(f, dialect=dialect)
                lines = [{(k or "").strip().lower(): (v or "").strip() for k, v in row.items()} for row in reader]
        except (OSError, UnicodeDecodeError) as err:
            messagebox.showerror("Import Gagal", str(err))
            return
        good, bad, seen = [], [], set()
        for n, row in enumerate(lines, start=2):
            err, d = self.validate_employee(row)
            if not err and d["email"].lower() in seen:
                err = "Email ganda di dalam file."
            if err:
                bad.append(f"Baris {n}: {err}")
                continue
            seen.add(d["email"].lower())
            good.append((d["nama"], d["jabatan"], d["departemen"], d["email"], d["telepon"], d["gaji"],
                         d["tanggal_masuk"], d["status"]))
        if good:
            DB.run("INSERT INTO karyawan (nama, jabatan, departemen, email, telepon, gaji, tanggal_masuk, status) "
                   "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", good, many=True)
            self.log("IMPORT", f"Import {len(good)} data karyawan dari CSV")
            self.load_employees()
        msg = f"Berhasil diimport: {len(good)} data\nDilewati: {len(bad)} baris"
        if bad:
            msg += "\n\n" + "\n".join(bad[:8]) + ("\n…" if len(bad) > 8 else "")
        messagebox.showinfo("Hasil Import", msg)

    # ============================================================
    #  MANAJEMEN USER
    # ============================================================
    def build_user(self, parent):
        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        tk.Label(bar, text="Akun yang dapat mengakses aplikasi ini", bg=BG, fg=MUTED, font=F_BASE).pack(side="left")
        HoverButton(bar, "➕  Tambah User", self.add_user, bg=SUCCESS).pack(side="right")

        outer, inner = self.make_card(parent)
        outer.pack(fill="both", expand=True)
        inner.pack_configure(padx=0, pady=0)
        cols = [("username", "Username", 180, "w"), ("nama_lengkap", "Nama Lengkap", 280, "w"),
                ("role", "Role", 120, "center")]
        tf, self.utree = self.make_tree(inner, cols)
        tf.pack(fill="both", expand=True)

        foot = tk.Frame(parent, bg=BG)
        foot.pack(fill="x", pady=(12, 0))
        HoverButton(foot, "🗑️  Hapus", self.delete_user, bg="#3B1D26", fg="#FCA5A5", hover="#4C2430",
                    pady=7).pack(side="right")
        HoverButton(foot, "🔑  Reset Password", self.reset_user_pw, bg=CARD2, fg=TEXT, pady=7).pack(
            side="right", padx=8)
        HoverButton(foot, "✏️  Ubah Nama / Role", self.edit_user, bg=WARN, fg="#1F2937", pady=7).pack(side="right")
        self.load_users()

    def load_users(self):
        self.users = DB.run("SELECT username, nama_lengkap, role FROM users ORDER BY username",
                            fetch="all") or []
        self.utree.delete(*self.utree.get_children())
        for i, u in enumerate(self.users):
            self.utree.insert("", "end", iid=u["username"], tags=["even" if i % 2 else "odd"],
                              values=(u["username"], u["nama_lengkap"], u["role"].upper()))

    def selected_user(self):
        sel = self.utree.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih user dari tabel terlebih dahulu.")
            return None
        return next((u for u in self.users if u["username"] == sel[0]), None)

    def count_admins(self):
        r = DB.run("SELECT COUNT(*) AS n FROM users WHERE role='admin'", fetch="one", silent=True)
        return int((r or {}).get("n") or 0)

    def add_user(self):
        fields = [
            {"key": "username", "label": "Username"},
            {"key": "nama_lengkap", "label": "Nama Lengkap"},
            {"key": "role", "label": "Role", "type": "combo", "values": ["admin", "staff"],
             "readonly": True, "default": "staff"},
            {"key": "password", "label": "Password (min. 6 karakter)", "type": "password"},
        ]
        FormDialog(self, "Tambah User", "Buat akun baru untuk pengguna aplikasi.", fields, self._save_user,
                   width=540)

    def _save_user(self, v):
        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", v["username"]):
            return "Username 3–30 karakter (huruf, angka, _ . -)."
        if not v["nama_lengkap"]:
            return "Nama lengkap wajib diisi."
        if len(v["password"]) < 6:
            return "Password minimal 6 karakter."
        if DB.run("SELECT username FROM users WHERE username=%s", (v["username"],), "one", silent=True):
            return "Username sudah dipakai."
        if DB.run("INSERT INTO users (username, password, nama_lengkap, role) VALUES (%s,%s,%s,%s)",
                  (v["username"], hash_pw(v["password"]), v["nama_lengkap"], v["role"])) is None:
            return "Gagal menyimpan user."
        self.log("USER", f"Menambah user {v['username']} ({v['role']})")
        self.load_users()
        self.toast("User berhasil ditambahkan")
        return None

    def edit_user(self):
        u = self.selected_user()
        if not u:
            return
        fields = [
            {"key": "nama_lengkap", "label": "Nama Lengkap", "full": True},
            {"key": "role", "label": "Role", "type": "combo", "values": ["admin", "staff"],
             "readonly": True, "full": True},
        ]
        FormDialog(self, "Ubah User", f"Akun: {u['username']}", fields,
                   lambda v, name=u["username"], old=u["role"]: self._save_user_edit(name, old, v),
                   initial=u, width=480)

    def _save_user_edit(self, username, old_role, v):
        if not v["nama_lengkap"]:
            return "Nama lengkap wajib diisi."
        if old_role == "admin" and v["role"] != "admin" and self.count_admins() <= 1:
            return "Tidak bisa menurunkan satu-satunya admin."
        if DB.run("UPDATE users SET nama_lengkap=%s, role=%s WHERE username=%s",
                  (v["nama_lengkap"], v["role"], username)) is None:
            return "Gagal memperbarui user."
        if username == self.user["username"]:
            self.user["nama_lengkap"], self.user["role"] = v["nama_lengkap"], v["role"]
        self.log("USER", f"Mengubah user {username}")
        self.load_users()
        self.toast("User berhasil diperbarui")
        return None

    def reset_user_pw(self):
        u = self.selected_user()
        if not u:
            return
        fields = [{"key": "password", "label": "Password Baru (min. 6 karakter)", "type": "password", "full": True}]

        def save(v, name=u["username"]):
            if len(v["password"]) < 6:
                return "Password minimal 6 karakter."
            if DB.run("UPDATE users SET password=%s WHERE username=%s", (hash_pw(v["password"]), name)) is None:
                return "Gagal mengubah password."
            self.log("PASSWORD", f"Reset password user {name}")
            self.toast("Password berhasil direset")
            return None

        FormDialog(self, "Reset Password", f"Akun: {u['username']}", fields, save, width=460,
                   save_text="🔑  Reset")

    def delete_user(self):
        u = self.selected_user()
        if not u:
            return
        if u["username"] == self.user["username"]:
            messagebox.showerror("Tidak Diizinkan", "Anda tidak dapat menghapus akun yang sedang dipakai.")
            return
        if u["role"] == "admin" and self.count_admins() <= 1:
            messagebox.showerror("Tidak Diizinkan", "Tidak bisa menghapus satu-satunya admin.")
            return
        if messagebox.askyesno("Konfirmasi", f"Hapus user '{u['username']}'?"):
            if DB.run("DELETE FROM users WHERE username=%s", (u["username"],)) is not None:
                self.log("USER", f"Menghapus user {u['username']}")
                self.load_users()
                self.toast("User dihapus", "error")

    # ============================================================
    #  LOG AKTIVITAS
    # ============================================================
    def build_log(self, parent):
        self.log_cari = tk.StringVar()
        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        box = ModernEntry(bar, textvariable=self.log_cari, icon="🔍", bg=CARD, width=30)
        box.pack(side="left")
        HoverButton(bar, "🧹  Bersihkan Log", self.clear_log, bg="#3B1D26", fg="#FCA5A5",
                    hover="#4C2430").pack(side="right")
        HoverButton(bar, "🔄  Muat Ulang", self.load_log, bg=CARD2, fg=TEXT).pack(side="right", padx=8)

        outer, inner = self.make_card(parent)
        outer.pack(fill="both", expand=True)
        inner.pack_configure(padx=0, pady=0)
        cols = [("waktu", "Waktu", 150, "center"), ("pengguna", "Pengguna", 170, "w"),
                ("aksi", "Aksi", 100, "center"), ("detail", "Detail", 560, "w")]
        tf, self.ltree = self.make_tree(inner, cols)
        tf.pack(fill="both", expand=True)
        self.log_cari.trace_add("write", lambda *a: self.render_log())
        self.load_log()

    def load_log(self):
        self.log_rows = DB.run("SELECT waktu, pengguna, aksi, detail FROM aktivitas ORDER BY id DESC LIMIT 1000",
                               fetch="all") or []
        self.render_log()

    def render_log(self):
        if not hasattr(self, "ltree") or not self.ltree.winfo_exists():
            return
        kw = self.log_cari.get().strip().lower()
        self.ltree.delete(*self.ltree.get_children())
        i = 0
        for r in self.log_rows:
            if kw and kw not in f"{r['pengguna']} {r['aksi']} {r['detail']}".lower():
                continue
            w = r["waktu"]
            self.ltree.insert("", "end", tags=["even" if i % 2 else "odd"],
                              values=(w.strftime("%d-%m-%Y %H:%M:%S") if w else "-", r["pengguna"],
                                      r["aksi"], r["detail"]))
            i += 1

    def clear_log(self):
        if messagebox.askyesno("Konfirmasi", "Hapus SEMUA riwayat aktivitas? Tindakan ini tidak dapat dibatalkan."):
            DB.run("DELETE FROM aktivitas")
            self.log("USER", "Membersihkan log aktivitas")
            self.load_log()
            self.toast("Log dibersihkan", "info")

    # ============================================================
    #  PROFIL
    # ============================================================
    def build_profil(self, parent):
        parent.columnconfigure(0, weight=1, uniform="p")
        parent.columnconfigure(1, weight=2, uniform="p")
        parent.rowconfigure(0, weight=1)

        outer, body = self.make_card(parent)
        outer.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        av = tk.Canvas(body, width=110, height=110, bg=CARD, highlightthickness=0)
        av.pack(pady=(26, 10))
        av.create_oval(4, 4, 106, 106, fill=PRIMARY, outline=lighten(PRIMARY, 0.4), width=3)
        av.create_text(55, 55, text=self.user["nama_lengkap"][:1].upper(), fill="white",
                       font=("Segoe UI", 38, "bold"))
        tk.Label(body, text=self.user["nama_lengkap"], bg=CARD, fg=TEXT, font=("Segoe UI", 16, "bold")).pack()
        tk.Label(body, text="@" + self.user["username"], bg=CARD, fg=MUTED, font=F_BASE).pack(pady=(2, 10))
        col = SUCCESS if self.is_admin else ACCENT
        tk.Label(body, text="  ● " + self.user["role"].upper() + "  ", bg=mix(CARD, col, 0.2), fg=col,
                 font=("Segoe UI", 9, "bold"), pady=4).pack()
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=22)
        tk.Label(body, text=("Anda memiliki akses penuh: kelola karyawan, user, dan log."
                             if self.is_admin else "Anda memiliki akses lihat data & export."),
                 bg=CARD, fg=MUTED, font=F_SMALL, wraplength=240, justify="center").pack()

        outer, body = self.make_card(parent, "Ganti Password", "Gunakan password yang kuat & mudah Anda ingat")
        outer.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.pw_old, self.pw_new, self.pw_new2 = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for text, var in (("PASSWORD LAMA", self.pw_old), ("PASSWORD BARU", self.pw_new),
                          ("ULANGI PASSWORD BARU", self.pw_new2)):
            tk.Label(body, text=text, font=("Segoe UI", 8, "bold"), bg=CARD, fg=MUTED).pack(anchor="w", pady=(14, 5))
            ModernEntry(body, textvariable=var, icon="🔒", show="•", toggle=True).pack(fill="x")
        self.pw_msg = tk.Label(body, text="", bg=CARD, fg="#FCA5A5", font=F_SMALL)
        self.pw_msg.pack(anchor="w", pady=(12, 0))
        HoverButton(body, "💾  Simpan Password Baru", self.change_password, pady=11).pack(anchor="w", pady=(10, 0))

    def change_password(self):
        old, new, new2 = self.pw_old.get(), self.pw_new.get(), self.pw_new2.get()
        row = DB.run("SELECT password FROM users WHERE username=%s", (self.user["username"],), "one")
        stored = (row or {}).get("password", "")
        if stored not in (hash_pw(old), old) or not old:
            self.pw_msg.config(text="⚠  Password lama salah.", fg="#FCA5A5")
            return
        if len(new) < 6:
            self.pw_msg.config(text="⚠  Password baru minimal 6 karakter.", fg="#FCA5A5")
            return
        if new != new2:
            self.pw_msg.config(text="⚠  Konfirmasi password tidak sama.", fg="#FCA5A5")
            return
        if DB.run("UPDATE users SET password=%s WHERE username=%s", (hash_pw(new), self.user["username"])) is None:
            return
        self.log("PASSWORD", "Mengganti password sendiri")
        for v in (self.pw_old, self.pw_new, self.pw_new2):
            v.set("")
        self.pw_msg.config(text="")
        self.toast("Password berhasil diganti")

    # ============================================================
    #  PENGATURAN (Database & OOP)
    # ============================================================
    OOP_PILLARS = [
        ("🔒", "Enkapsulasi", PRIMARY,
         "Data & perilaku dibungkus dalam satu class, detail internal disembunyikan.",
         [("class DB", "Koneksi, cursor & commit dibungkus di DB.run()"),
          ("class NexusHR", "State (user, settings, emp_data) tersimpan di dalam objek"),
          ("class ModernEntry", "Entry, border fokus & tombol mata jadi satu widget")]),
        ("🎭", "Abstraksi", ACCENT,
         "Pemakai class cukup tahu apa yang dilakukan, bukan bagaimana caranya.",
         [("DB.run(sql, params, fetch)", "Pemanggil tidak perlu mengurus koneksi MySQL"),
          ("FormDialog(fields, on_save)", "Form dibuat dari daftar field + callback"),
          ("rcard() / make_tree()", "Membuat kartu & tabel tanpa detail Tkinter")]),
        ("🧬", "Pewarisan (Inheritance)", SUCCESS,
         "Class turunan memakai ulang sifat & method dari class induk.",
         [("HoverButton  ←  tk.Label", "Label biasa jadi tombol dengan efek hover"),
          ("ModernEntry  ←  tk.Frame", "Frame jadi input dengan border menyala"),
          ("ScrollFrame  ←  tk.Frame", "Frame jadi area yang bisa di-scroll"),
          ("FormDialog  ←  tk.Toplevel", "Jendela jadi dialog form generik")]),
        ("🔀", "Polimorfisme", WARN,
         "Satu antarmuka yang sama, perilaku berbeda sesuai objek atau konteksnya.",
         [("FormDialog.save()", "Memanggil on_save() berbeda: tambah, ubah, reset password"),
          ("getattr(self, f'build_{key}')", "Tiap halaman punya build_* sendiri"),
          ("super().__init__()", "Widget turunan menimpa (override) perilaku bawaan Tk")]),
    ]

    def build_pengaturan(self, parent):
        self.set_tab = getattr(self, "set_tab", "database")
        bar = tk.Frame(parent, bg=BG)
        bar.pack(fill="x", pady=(0, 12))
        body = tk.Frame(parent, bg=BG)
        body.pack(fill="both", expand=True)

        def show(tab):
            self.set_tab = tab
            for w in bar.winfo_children():
                w.destroy()
            for key, text in (("database", "🗄️  Database"), ("oop", "🧩  OOP")):
                on = key == tab
                HoverButton(bar, text, lambda k=key: show(k), bg=PRIMARY if on else CARD,
                            fg="white" if on else MUTED, hover=lighten(PRIMARY, 0.1) if on else CARD2,
                            pady=8).pack(side="left", padx=(0, 8))
            for w in body.winfo_children():
                w.destroy()
            (self.build_set_database if tab == "database" else self.build_set_oop)(body)

        show(self.set_tab)

    def build_set_database(self, parent):
        cols = DB.run(
            "SELECT TABLE_NAME AS tabel, COLUMN_NAME AS kolom, COLUMN_TYPE AS tipe, COLUMN_KEY AS kunci "
            "FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s ORDER BY TABLE_NAME, ORDINAL_POSITION",
            (DB_NAME,), "all") or []
        counts = {}
        for t in sorted({c["tabel"] for c in cols}):
            r = DB.run(f"SELECT COUNT(*) AS n FROM `{t}`", fetch="one", silent=True)
            counts[t] = int((r or {}).get("n") or 0)

        outer, body = self.make_card(parent, f"Database: {DB_NAME}", "Struktur tabel dibaca langsung dari MySQL")
        outer.pack(fill="both", expand=True)
        spec = [("tabel", "Tabel", 150, "w"), ("kolom", "Kolom", 190, "w"), ("tipe", "Tipe", 180, "w"),
                ("kunci", "Key", 90, "center"), ("baris", "Jumlah Baris", 120, "center")]
        tf, tree = self.make_tree(body, spec)
        tf.pack(fill="both", expand=True)
        for i, c in enumerate(cols):
            tree.insert("", "end", tags=["even" if i % 2 else "odd"],
                        values=(c["tabel"], c["kolom"], c["tipe"], c["kunci"] or "", counts.get(c["tabel"], 0)))

    def build_set_oop(self, parent):
        sf = ScrollFrame(parent)
        sf.pack(fill="both", expand=True)
        g = sf.inner
        g.columnconfigure(0, weight=1, uniform="o")
        g.columnconfigure(1, weight=1, uniform="o")
        mono = ("Consolas", 10, "bold")
        for i, (icon, name, color, desc, items) in enumerate(self.OOP_PILLARS):
            box, body = self.rcard(g, accent=color)
            box.grid(row=i // 2, column=i % 2, sticky="nsew",
                     padx=(0, 8) if i % 2 == 0 else (8, 0), pady=(0, 16))
            head = tk.Frame(body, bg=CARD)
            head.pack(fill="x", pady=(10, 4))
            tk.Label(head, text=icon, bg=mix(CARD, color, 0.25), fg=color, font=("Segoe UI Emoji", 16),
                     width=3, pady=6).pack(side="left")
            ttl = tk.Frame(head, bg=CARD)
            ttl.pack(side="left", padx=14)
            tk.Label(ttl, text=name, bg=CARD, fg=TEXT, font=("Segoe UI", 14, "bold")).pack(anchor="w")
            tk.Label(ttl, text=desc, bg=CARD, fg=MUTED, font=F_SMALL, wraplength=330,
                     justify="left").pack(anchor="w", pady=(2, 0))
            tk.Label(head, text=f"0{i + 1}", bg=CARD, fg=mix(CARD, color, 0.45),
                     font=("Segoe UI", 26, "bold")).pack(side="right", anchor="n")
            tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(10, 8))
            for code, expl in items:
                row = tk.Frame(body, bg=mix(CARD, color, 0.07))
                row.pack(fill="x", pady=3)
                tk.Frame(row, bg=color, width=3).pack(side="left", fill="y")
                txt = tk.Frame(row, bg=row["bg"])
                txt.pack(side="left", fill="x", expand=True, padx=12, pady=7)
                tk.Label(txt, text=code, bg=row["bg"], fg=lighten(color, 0.25), font=mono,
                         anchor="w").pack(anchor="w")
                tk.Label(txt, text=expl, bg=row["bg"], fg=TEXT, font=F_SMALL, anchor="w",
                         wraplength=370, justify="left").pack(anchor="w", pady=(2, 0))
            tk.Frame(body, bg=CARD, height=6).pack()


# ============================================================
if __name__ == "__main__":
    # Beri identitas sendiri ke Windows agar taskbar tidak memakai ikon python.exe
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("nexus.hr.karyawan.app")
    except Exception:
        pass
    root = tk.Tk()
    app = NexusHR(root)
    root.mainloop()