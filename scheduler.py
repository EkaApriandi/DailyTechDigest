import time
from datetime import datetime
from zoneinfo import ZoneInfo

from config import DIGEST_TIME
from database import DigestDatabase
from fetcher import fetch_all_fresh_articles
from notifier import dispatch_daily_digest

def run_digest_cycle() -> None:
    """Eksekusi satu putaran pengambilan dan pengiriman digest harian."""
    tz = ZoneInfo("Asia/Jakarta")
    wib_now = datetime.now(tz)
    print(f"\n[{wib_now.strftime('%Y-%m-%d %H:%M:%S WIB')}] 🚀 Memulai siklus kurasi Daily Tech Digest...", flush=True)

    db = DigestDatabase()
    
    # Bersihkan riwayat lama lebih dari 30 hari agar DB tetap ramping
    db.cleanup_old_records(days=30)

    # Ambil artikel segar
    articles = fetch_all_fresh_articles(db)
    total_articles = sum(len(v) for v in articles.values())
    print(f"[{datetime.now(tz).strftime('%H:%M:%S')}] Ditemukan {total_articles} artikel baru.", flush=True)

    if total_articles == 0:
        print("[Scheduler] Tidak ada artikel baru untuk dikirim.", flush=True)
        return

    # Kirim ke Telegram
    success = dispatch_daily_digest(articles, db)
    if success:
        print(f"[{datetime.now(tz).strftime('%H:%M:%S')}] ✅ Digest berhasil dikirim ke Telegram!", flush=True)
    else:
        print(f"[{datetime.now(tz).strftime('%H:%M:%S')}] ❌ Gagal mengirim sebagian/seluruh digest.", flush=True)

def start_scheduler_daemon() -> None:
    """Menjalankan proses daemon yang otomatis mengeksekusi digest setiap pagi berbasis waktu Indonesia (WIB)."""
    tz = ZoneInfo("Asia/Jakarta")
    
    try:
        target_parts = DIGEST_TIME.split(":")
        target_hour = int(target_parts[0])
        target_minute = int(target_parts[1]) if len(target_parts) > 1 else 0
    except Exception:
        target_hour = 5
        target_minute = 0

    print("=" * 60, flush=True)
    print("⏰ DAILY TECH DIGEST SCHEDULER AKTIF", flush=True)
    print(f"📅 Target Pengiriman: {DIGEST_TIME} WIB (Asia/Jakarta)", flush=True)
    print(f"🕒 Waktu Server Saat Ini: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S WIB')}", flush=True)
    print("👉 Tekan Ctrl + C di terminal untuk menghentikan.", flush=True)
    print("=" * 60, flush=True)

    # Inisialisasi: jika dijalankan hari ini dan sudah lewat jam target, anggap hari ini sudah terlayani
    # agar tidak langsung menembak kecuali belum pernah jalan hari ini
    last_run_date = datetime.now(tz).date()

    while True:
        now_wib = datetime.now(tz)
        today_date = now_wib.date()

        # Ketika berganti hari dan waktu mencapai jam target (misal 05:00 WIB)
        if today_date != last_run_date and (now_wib.hour, now_wib.minute) >= (target_hour, target_minute):
            last_run_date = today_date
            run_digest_cycle()

        time.sleep(20)
