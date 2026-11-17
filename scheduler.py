import time
from datetime import datetime
import schedule

from config import DIGEST_TIME
from database import DigestDatabase
from fetcher import fetch_all_fresh_articles
from notifier import dispatch_daily_digest

def run_digest_cycle() -> None:
    """Eksekusi satu putaran pengambilan dan pengiriman digest harian."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Memulai siklus kurasi Daily Tech Digest...")

    db = DigestDatabase()
    
    # Bersihkan riwayat lama lebih dari 30 hari agar DB tetap ramping
    db.cleanup_old_records(days=30)

    # Ambil artikel segar
    articles = fetch_all_fresh_articles(db)
    total_articles = sum(len(v) for v in articles.values())
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ditemukan {total_articles} artikel baru.")

    if total_articles == 0:
        print("[Scheduler] Tidak ada artikel baru untuk dikirim.")
        return

    # Kirim ke Telegram
    success = dispatch_daily_digest(articles, db)
    if success:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Digest berhasil dikirim ke Telegram!")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Gagal mengirim sebagian/seluruh digest.")

def start_scheduler_daemon() -> None:
    """Menjalankan proses daemon yang otomatis mengeksekusi digest setiap pagi."""
    print("=" * 60)
    print("⏰ DAILY TECH DIGEST SCHEDULER AKTIF")
    print(f"📅 Waktu Pengiriman Setiap Hari: {DIGEST_TIME} (Waktu Lokal)")
    print("👉 Tekan Ctrl + C di terminal untuk menghentikan.")
    print("=" * 60)

    # Daftarkan jadwal harian
    schedule.every().day.at(DIGEST_TIME).do(run_digest_cycle)

    # Loop pengecekan jadwal
    while True:
        schedule.run_pending()
        time.sleep(30)
