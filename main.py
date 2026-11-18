import sys
from pathlib import Path

# Pastikan direktori proyek masuk ke sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DIGEST_TIME
from database import DigestDatabase
from fetcher import fetch_all_fresh_articles
from summarizer import process_article_details
from notifier import send_telegram_message
from scheduler import run_digest_cycle, start_scheduler_daemon

def check_credentials() -> bool:
    """Validasi apakah kredensial Telegram sudah terkonfigurasi."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n❌ Kredensial Telegram belum lengkap di file .env!")
        print("Pastikan baris berikut sudah diisi:")
        print("  TELEGRAM_BOT_TOKEN=token_bot_anda")
        print("  TELEGRAM_CHAT_ID=id_telegram_pribadi_anda\n")
        print("💡 Tips: Untuk mengetahui Chat ID Anda, kirim pesan apa saja ke @userinfobot di Telegram.")
        return False
    return True

def run_dry_run() -> None:
    """Mengambil artikel dan menampilkan hasil kurasi, rincian & translasi di konsol tanpa mengirim ke Telegram."""
    print("🔍 Menjalankan Dry-Run (Kurasi, Rincian & Translasi tanpa mengirim ke Telegram)...")
    db = DigestDatabase()
    articles = fetch_all_fresh_articles(db)

    total = sum(len(v) for v in articles.values())
    print(f"\nTotal artikel baru ditemukan: {total}\n")

    for cat, items in articles.items():
        print("=" * 60)
        print(f"📂 KATEGORI: {cat.upper()} ({len(items)} artikel)")
        print("=" * 60)
        for art in items:
            processed = process_article_details(art)
            print(f"\n📌 Judul (ID): {processed['title_id']}")
            if processed['title_id'] != art['title']:
                print(f"   (Judul Asli: {art['title']})")
            print(f"   Sumber   : {processed['source']}")
            print(f"   Rincian  : {processed['summary_id']}")
            print(f"   Link     : {processed['link']}")

def test_telegram_connection() -> None:
    """Menguji apakah bot bisa mengirim pesan ke Chat ID pengguna."""
    if not check_credentials():
        sys.exit(1)

    print("📡 Mengirim pesan uji coba ke Telegram...")
    pesan = "🔔 <b>Uji Coba Berhasil!</b>\nDaily Tech Digest Bot terhubung dengan akun Telegram Anda."
    ok = send_telegram_message(pesan)
    if ok:
        print("✅ Pesan uji coba berhasil diterima di Telegram Anda!")
    else:
        print("❌ Gagal mengirim pesan uji coba. Periksa kembali Token dan Chat ID.")

def print_help() -> None:
    print("Penggunaan Daily Tech Digest Bot:")
    print("  python main.py             -> Jalankan kurasi dan kirim digest sekarang")
    print("  python main.py --now       -> Sama seperti di atas")
    print("  python main.py --daemon    -> Jalankan scheduler harian otomatis (setiap jam " + DIGEST_TIME + ")")
    print("  python main.py --dry-run   -> Uji kurasi, rincian & translasi tanpa mengirim ke Telegram")
    print("  python main.py --test      -> Kirim pesan tes koneksi Telegram")

def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print_help()
        return

    if "--dry-run" in args:
        run_dry_run()
        return

    if "--test" in args or "--test-telegram" in args:
        test_telegram_connection()
        return

    if not check_credentials():
        sys.exit(1)

    if "--daemon" in args:
        start_scheduler_daemon()
    else:
        # Default: Eksekusi sekali langsung (cocok untuk Cron / Task Scheduler / Manual trigger)
        run_digest_cycle()

if __name__ == "__main__":
    main()
