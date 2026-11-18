# Nexus HR

Jalankan dari folder ini:

    pip install mysql-connector-python
    python main.py

Pastikan MySQL di Laragon sudah Start All.

## Struktur
- main.py          titik masuk
- app.py           class NexusHR (gabungan semua halaman)
- config.py        koneksi DB, warna, font, konstanta
- helpers.py       fungsi bantu (format, tanggal, hitung slip, ikon)
- database.py      class DB, init_db, pembuatan tabel
- widgets.py       HoverButton, ModernEntry, FormDialog, ScrollFrame, style
- core.py          sidebar/topbar, navigasi, kartu & grafik dasar
- pages/           login, dashboard, palette, karyawan, laporan, user, log, profil,
                   pengaturan, absensi, cuti, slip (+ modul_umum = helper bersama)
