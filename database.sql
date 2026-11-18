CREATE DATABASE IF NOT EXISTS `karyawan_DB` CHARACTER SET utf8mb4;
USE `karyawan_DB`;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  nama_lengkap VARCHAR(100) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'staff'
);

CREATE TABLE IF NOT EXISTS karyawan (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nama VARCHAR(100) NOT NULL,
  jabatan VARCHAR(100),
  email VARCHAR(100),
  telepon VARCHAR(30),
  gaji DECIMAL(15,2) DEFAULT 0,
  departemen VARCHAR(80) DEFAULT 'Umum',
  tanggal_masuk DATE NULL,
  status VARCHAR(20) DEFAULT 'Aktif'
);

CREATE TABLE IF NOT EXISTS aktivitas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  waktu DATETIME DEFAULT CURRENT_TIMESTAMP,
  pengguna VARCHAR(100),
  aksi VARCHAR(30),
  detail VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS absensi (
  id INT AUTO_INCREMENT PRIMARY KEY,
  karyawan_id INT NOT NULL,
  tanggal DATE NOT NULL,
  jam_masuk TIME NULL,
  jam_keluar TIME NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'Hadir',
  catatan VARCHAR(150) NULL,
  UNIQUE KEY uq_absen (karyawan_id, tanggal)
);

CREATE TABLE IF NOT EXISTS cuti (
  id INT AUTO_INCREMENT PRIMARY KEY,
  karyawan_id INT NOT NULL,
  jenis VARCHAR(20) NOT NULL,
  tgl_mulai DATE NOT NULL,
  tgl_selesai DATE NOT NULL,
  jumlah_hari INT NOT NULL DEFAULT 0,
  alasan VARCHAR(255) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'Menunggu',
  diproses_oleh VARCHAR(100) NULL,
  dibuat DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS slip_gaji (
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
  UNIQUE KEY uq_slip (karyawan_id, periode)
);

-- Akun admin awal  ->  username: admin   password: admin123  (SHA-256)
INSERT IGNORE INTO users (username, password, nama_lengkap, role)
VALUES ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'Administrator', 'admin');

-- Data contoh 24 karyawan (hapus bagian ini jika tidak diperlukan)
INSERT INTO karyawan (nama, jabatan, departemen, email, telepon, gaji, tanggal_masuk, status) VALUES
('Budi Santoso','Software Engineer','IT','budi.santoso@contoh.id','081201234567',12500000,'2025-12-19','Aktif'),
('Siti Nurhaliza','HR Manager','HRD','siti.nurhaliza@contoh.id','081308888888',15000000,'2025-09-13','Aktif'),
('Agus Prasetyo','Akuntan','Keuangan','agus.prasetyo@contoh.id','081416543209',9500000,'2026-02-03','Aktif'),
('Dewi Lestari','Digital Marketer','Marketing','dewi.lestari@contoh.id','081524197530',8000000,'2026-03-18','Aktif'),
('Rizky Ramadhan','Supervisor Operasional','Operasional','rizky.ramadhan@contoh.id','081631851851',10500000,'2025-10-12','Aktif'),
('Putri Anggraini','UI/UX Designer','IT','putri.anggraini@contoh.id','081739506172',9800000,'2026-04-03','Aktif'),
('Eko Wijaya','Operator Produksi','Produksi','eko.wijaya@contoh.id','081847160493',5200000,'2025-11-17','Aktif'),
('Rina Marlina','Sales Executive','Penjualan','rina.marlina@contoh.id','081954814814',6800000,'2026-05-09','Aktif'),
('Andi Kurniawan','DevOps Engineer','IT','andi.kurniawan@contoh.id','081262469135',14000000,'2026-06-01','Aktif'),
('Maya Sari','Recruiter','HRD','maya.sari@contoh.id','081370123456',7200000,'2026-06-14','Cuti'),
('Fajar Nugroho','Staf Keuangan','Keuangan','fajar.nugroho@contoh.id','081477777777',6500000,'2026-07-07','Aktif'),
('Lia Permata','Content Creator','Marketing','lia.permata@contoh.id','081585432098',6200000,'2026-06-30','Aktif'),
('Hendra Gunawan','Kepala Produksi','Produksi','hendra.gunawan@contoh.id','081693086419',13500000,'2026-01-14','Aktif'),
('Nurul Hidayah','Sales Manager','Penjualan','nurul.hidayah@contoh.id','081700740740',14500000,'2026-01-07','Aktif'),
('Yusuf Maulana','Staf Gudang','Operasional','yusuf.maulana@contoh.id','081808395061',4800000,'2026-07-29','Aktif'),
('Tiara Kusuma','Data Analyst','IT','tiara.kusuma@contoh.id','081916049382',11000000,'2026-08-11','Aktif'),
('Bagas Saputra','QC Inspector','Produksi','bagas.saputra@contoh.id','081223703703',5600000,'2026-09-03','Aktif'),
('Citra Dewanti','Brand Manager','Marketing','citra.dewanti@contoh.id','081331358024',12000000,'2026-08-27','Aktif'),
('Dimas Aditya','Customer Service','Penjualan','dimas.aditya@contoh.id','081439012345',4900000,'2026-10-09','Aktif'),
('Ayu Wulandari','Payroll Specialist','Keuangan','ayu.wulandari@contoh.id','081546666666',8500000,'2026-10-02','Aktif'),
('Galih Pratama','Staf Logistik','Operasional','galih.pratama@contoh.id','081654320987',5500000,'2026-11-02','Aktif'),
('Wulan Sari','Admin HR','HRD','wulan.sari@contoh.id','081761975308',5300000,'2026-11-14','Aktif'),
('Irfan Hakim','Backend Developer','IT','irfan.hakim@contoh.id','081869629629',13000000,'2025-08-07','Nonaktif'),
('Mega Putri','Sales Executive','Penjualan','mega.putri@contoh.id','081977283950',6400000,'2026-11-10','Aktif');