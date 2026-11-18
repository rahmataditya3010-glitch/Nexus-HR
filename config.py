# -*- coding: utf-8 -*-
"""Konfigurasi: koneksi database, warna, font, dan konstanta modul HR."""
import os
from datetime import time as dtime

# ============================================================
#  KONFIGURASI
# ============================================================
DB_NAME = "karyawan_DB"
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": DB_NAME,
}
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nexus_settings.json")

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

#  KONFIGURASI MODUL
# ============================================================
JAM_MASUK = dtime(8, 0)          # lewat jam ini => Terlambat
JATAH_CUTI = 12                  # hari cuti tahunan per tahun
HARI_KERJA_BULAN = 22            # pembagi potongan alpa
BPJS_PCT = 0.03                  # iuran karyawan (JHT 2% + Kesehatan 1%)
PTKP = 54_000_000                # PTKP TK/0 per tahun
STATUS_ABSEN = ["Hadir", "Terlambat", "Izin", "Sakit", "Cuti", "Alpa"]
JENIS_CUTI = ["Tahunan", "Sakit", "Melahirkan", "Penting", "Lainnya"]
