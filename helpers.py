# -*- coding: utf-8 -*-
"""Fungsi bantu: warna, format angka, tanggal, hitung slip gaji, ikon, dll."""
import hashlib
import json
import math
import re
import tkinter as tk
from datetime import date, datetime, timedelta

from config import *

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
