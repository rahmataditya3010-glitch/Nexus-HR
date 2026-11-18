# -*- coding: utf-8 -*-
"""
db_server.py - menjalankan MariaDB portable di latar belakang untuk Nexus HR.
"""
import atexit
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

HOST = "127.0.0.1"
PORT = 3307                      # bukan 3306, supaya tidak bentrok dengan Laragon/MySQL lain
DB_NAME = "karyawan_DB"          # nama database aplikasi
SQL_FILE = "database.sql"        # dump awal (opsional), diletakkan di sebelah exe

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Data disimpan di folder user (bisa ditulis), bukan di Program Files
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "NexusHR" / "mariadb_data"

_proc = None


def _app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def _find_base():
    app = _app_dir()
    for base in (app / "mariadb", app / "_internal" / "mariadb"):
        if (base / "bin" / "mysqld.exe").exists():
            return base
    raise FileNotFoundError(
        "Folder 'mariadb' tidak ditemukan di sebelah aplikasi.\n"
        "Pastikan folder mariadb (berisi bin\\mysqld.exe) ikut disalin."
    )


def _find_exe(base, *names):
    for n in names:
        p = base / "bin" / n
        if p.exists():
            return p
    return None


def _port_open(timeout=0.5):
    try:
        with socket.create_connection((HOST, PORT), timeout=timeout):
            return True
    except OSError:
        return False


def _init_data(base):
    """Buat folder data MariaDB saat pertama kali dijalankan."""
    if (DATA_DIR / "mysql").exists():
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    installer = _find_exe(base, "mariadb-install-db.exe", "mysql_install_db.exe")
    if installer is None:
        raise FileNotFoundError("mariadb-install-db.exe tidak ada di folder mariadb\\bin")
    subprocess.run(
        [str(installer), f"--datadir={DATA_DIR}"],
        check=True, creationflags=NO_WINDOW,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _first_run_import(base):
    """Buat database dan import database.sql sekali saja."""
    marker = DATA_DIR / ".imported"
    if marker.exists():
        return
    client = _find_exe(base, "mariadb.exe", "mysql.exe")
    if client is None:
        return
    common = [str(client), "-uroot", f"--host={HOST}", f"--port={PORT}", "--default-character-set=utf8mb4"]
    subprocess.run(
        common + ["-e", f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"],
        check=True, creationflags=NO_WINDOW,
    )
    sql_path = None
    for p in (_app_dir() / SQL_FILE, _app_dir() / "_internal" / SQL_FILE):
        if p.exists():
            sql_path = p
            break
    if sql_path is not None:
        data = sql_path.read_bytes()
        # Dump dari MySQL 8 punya sintaks yang tidak dikenal MariaDB
        data = data.replace(b"utf8mb4_0900_ai_ci", b"utf8mb4_general_ci")
        data = data.replace(b" DEFAULT ENCRYPTION='N'", b"")
        subprocess.run(
            common + [DB_NAME], input=data, check=True, creationflags=NO_WINDOW,
        )
    marker.write_text("ok", encoding="utf-8")


def start_server():
    """Nyalakan MariaDB kalau belum jalan. Aman dipanggil berkali-kali."""
    global _proc
    if _port_open():
        return  # sudah jalan (mis. instance Nexus HR lain)

    base = _find_base()
    _init_data(base)

    log = DATA_DIR / "error.log"
    _proc = subprocess.Popen(
        [
            str(base / "bin" / "mysqld.exe"),
            f"--basedir={base}",
            f"--datadir={DATA_DIR}",
            f"--port={PORT}",
            f"--bind-address={HOST}",
            "--skip-name-resolve",
            "--character-set-server=utf8mb4",
            "--collation-server=utf8mb4_general_ci",
            "--innodb-buffer-pool-size=64M",
            f"--log-error={log}",
        ],
        creationflags=NO_WINDOW,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    for _ in range(120):  # tunggu maksimal ~60 detik
        if _port_open():
            break
        if _proc.poll() is not None:
            raise RuntimeError(f"MariaDB berhenti sendiri. Lihat log: {log}")
        time.sleep(0.5)
    else:
        raise RuntimeError(f"MariaDB tidak merespons. Lihat log: {log}")

    _first_run_import(base)


def stop_server():
    """Matikan MariaDB, hanya jika dinyalakan oleh instance ini."""
    global _proc
    if _proc is None:
        return
    try:
        base = _find_base()
        admin = _find_exe(base, "mariadb-admin.exe", "mysqladmin.exe")
        if admin is not None:
            subprocess.run(
                [str(admin), "-uroot", f"--host={HOST}", f"--port={PORT}", "shutdown"],
                timeout=30, creationflags=NO_WINDOW,
            )
            _proc.wait(timeout=30)
        else:
            _proc.terminate()
    except Exception:
        try:
            _proc.terminate()
        except Exception:
            pass
    _proc = None


atexit.register(stop_server)