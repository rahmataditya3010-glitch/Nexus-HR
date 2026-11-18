# -*- coding: utf-8 -*-
"""Akses database MySQL: class DB, init_db(), dan pembuatan tabel modul."""
import mysql.connector
from tkinter import messagebox

from config import *
from helpers import hash_pw


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
            host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"]
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
