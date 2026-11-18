<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/d1243032-04bb-4efa-a292-48179d67313c" />
<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/a14adbc3-85db-4735-9c19-358a95dd306e" />
<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/48fc5642-b689-419f-9412-89510d5fabb1" />
<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/b5ae8b77-fb8a-42b9-a79e-795bc479f94e" />
<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/65449935-cdc3-4c67-9ead-15b942c36e11" />
<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/1732637b-20dd-4f9f-ac2e-4c5ee0dabe60" />
<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/2940dab4-5f32-40ea-b583-11ea4c38b6b6" />
<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/9bcfd534-279a-4e0d-ba64-7adce6d6984e" />
<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/e3037de8-ae25-4fc5-923f-554ef637e18d" />
<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/c50e6a3a-7dc6-4604-a880-82524c9da7a2" />
<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/cad84180-3d2d-44ba-9a07-4a2da5751dbf" />
<img width="754" height="425" alt="image" src="https://github.com/user-attachments/assets/54742275-8f4b-40ed-9743-74b0351680c9" />




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
