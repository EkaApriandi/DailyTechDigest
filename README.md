# 🌅 Daily Tech & AI Digest Bot

Bot kurasi berita teknologi dan riset AI otomatis yang dikirim langsung ke Telegram pribadi Anda setiap pagi. Dibangun dengan standar **Anti-Slop**: ringkas, *high-signal*, bebas duplikasi, dan tanpa bloatware.

---

## 🌟 Fitur Utama

1. **📰 Sumber Terkurasi Multi-Kategori:**
   - 🤖 **AI & Machine Learning:** MIT Technology Review AI, VentureBeat AI.
   - 💻 **Tech & Startups:** Hacker News Frontpage, TechCrunch.
   - 🛠️ **Engineering & Inovasi:** Ars Technica.
2. **🛡️ Deduplikasi Cerdas (SQLite):**
   - Artikel yang sudah pernah dikirim tidak akan pernah dikirim ulang. Setiap pagi Anda hanya menerima berita yang benar-benar baru.
3. **⚡ Dual-Engine Summarizer:**
   - **Engine Ekstraktif Lokal (Default):** Membersihkan boilerplate web dan mengekstrak intisari 1-2 kalimat secara instan tanpa biaya API.
   - **Engine AI (Opsional):** Jika Anda mengisi `GEMINI_API_KEY` di `.env`, bot otomatis merangkum intisari eksekutif dalam Bahasa Indonesia.
4. **📱 Format Pesan Elegan & Auto-Chunking:**
   - Didesain bersih dengan tautan sumber langsung.
   - Otomatis membagi pesan jika melebihi batas 4096 karakter Telegram tanpa memotong artikel di tengah jalan.
5. **🎛️ Mode Fleksibel:**
   - `python main.py --now` -> Kirim digest sekarang juga.
   - `python main.py --dry-run` -> Pratinjau berita di terminal tanpa mengirim ke Telegram.
   - `python main.py --daemon` -> Menjalankan penjadwal internal harian (setiap jam 07:00 pagi).

---

## 🚀 Panduan Setup Cepat

### Langkah 1: Dapatkan Chat ID Telegram Pribadi Anda
1. Buka Telegram dan cari bot: **`@userinfobot`**.
2. Klik **Start** atau kirim pesan apa saja.
3. Bot akan membalas dengan info profil Anda, salin angka pada baris **`Id:`** (contoh: `6118296244`).

---

### Langkah 2: Konfigurasi `.env`
1. Masuk ke folder proyek:
   ```powershell
   cd d:\Projects\ide-project\02-daily-tech-digest
   ```
2. Salin template konfigurasi:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Buka file `.env` dan masukkan data Anda:
   ```env
   # Token bot dari @BotFather (bisa memakai bot yang sudah Anda punya)
   TELEGRAM_BOT_TOKEN=8924812566:AAHQt0OVjixqGBAwXYKwwitKwtMRAFCLN6c

   # Chat ID pribadi Anda dari @userinfobot
   TELEGRAM_CHAT_ID=6118296244

   # Jam kirim harian (format 24 jam HH:MM)
   DIGEST_TIME=07:00

   # Jumlah artikel maksimal per sumber
   MAX_ARTICLES_PER_FEED=3
   ```

---

### Langkah 3: Install Dependensi & Uji Coba

```powershell
# Buat & aktifkan virtual environment jika belum ada
python -m venv .venv
.venv\Scripts\activate

# Install dependensi
pip install -r requirements.txt

# Tes koneksi ke Telegram Anda
python main.py --test

# Jalankan pengiriman digest langsung sekarang
python main.py --now
```

---

## ⏰ Cara Mengatur Jadwal Otomatis (Scheduler)

Pilih salah satu metode yang paling sesuai:

### Opsi A: Menggunakan Background Daemon Bawaan
Jalankan bot dalam mode daemon:
```powershell
python main.py --daemon
```
Skrip akan terus berjalan di latar belakang dan otomatis mengirim digest setiap jam `07:00` pagi (sesuai setting `DIGEST_TIME` di `.env`).

---

### Opsi B: Menggunakan Windows Task Scheduler
Jika ingin Windows menjalankan skrip otomatis setiap pagi tanpa membuka terminal terus-menerus:
1. Tekan tombol `Windows + S`, ketik **Task Scheduler** lalu buka.
2. Klik **Create Basic Task...** di panel kanan.
3. Beri nama: `Daily Tech Digest`.
4. Trigger: Pilih **Daily**, atur jam `07:00 AM`.
5. Action: Pilih **Start a Program**:
   - **Program/script:** `python.exe` (atau path ke python venv Anda)
   - **Add arguments:** `main.py --now`
   - **Start in:** `D:\Projects\ide-project\02-daily-tech-digest`
6. Selesai! Windows akan mengeksekusi bot otomatis setiap pagi.

---

### Opsi C: Menjalankan di Server / Cloud (Linux / Railway Cron)
Jika menggunakan server Linux VPS atau cloud:
Tambahkan satu baris di crontab (`crontab -e`):
```bash
# Jalankan setiap hari jam 07:00 pagi
0 7 * * * cd /path/to/02-daily-tech-digest && /path/to/venv/bin/python main.py --now
```

---

## 📂 Struktur File

```text
02-daily-tech-digest/
├── config.py         # Konfigurasi sumber RSS feed & environment
├── database.py       # Penyimpanan SQLite deduplikasi artikel
├── fetcher.py        # Pengambil data RSS & pembersih HTML
├── summarizer.py     # Peringkas ekstraktif lokal & Gemini AI
├── notifier.py       # Pengirim pesan Telegram berformat HTML & auto-chunker
├── scheduler.py      # Pengatur jadwal harian (daemon mode)
├── main.py           # Entrypoint CLI (--now, --daemon, --dry-run, --test)
├── requirements.txt  # Daftar dependensi
├── .env.example      # Template konfigurasi
└── README.md         # Dokumentasi panduan ini
```
