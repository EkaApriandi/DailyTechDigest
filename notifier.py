import html
import time
from datetime import datetime
from typing import Dict, List, Any
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from database import DigestDatabase
from summarizer import process_article_details

def send_telegram_message(text: str, chat_id: str = TELEGRAM_CHAT_ID, token: str = TELEGRAM_BOT_TOKEN) -> bool:
    """Mengirim satu pesan ke Telegram via HTTP API."""
    if not token or not chat_id:
        print("[Notifier Error] Token bot atau Chat ID Telegram belum diatur di .env!")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            return True
        else:
            print(f"[Notifier Error] Telegram API: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"[Notifier Error] Gagal mengirim pesan: {e}")
        return False

def format_article_item(art: Dict[str, Any]) -> str:
    """
    Memformat satu artikel menjadi teks HTML Telegram yang rapi, informatif,
    lengkap tanpa terpotong, dan bertautan ke sumber asli.
    """
    title_id = html.escape(art.get("title_id") or art.get("title", ""))
    source = html.escape(art.get("source", ""))
    summary_id = html.escape(art.get("summary_id") or art.get("summary_raw", ""))
    link = art.get("link", "")

    # Tampilkan judul asli dalam kurung jika judul aslinya bahasa Inggris dan berbeda dari judul terjemahan
    orig_title = art.get("title", "").strip()
    sub_title_line = f"<i>Sumber: {source}</i>"
    if orig_title and orig_title.lower() != title_id.lower() and not art.get("is_indonesian", False):
        orig_escaped = html.escape(orig_title)
        sub_title_line = f"<i>Sumber: {source}</i>\n<i>(Judul asli: {orig_escaped})</i>"

    return (
        f"📌 <b>{title_id}</b>\n"
        f"{sub_title_line}\n\n"
        f"{summary_id}\n\n"
        f"👉 <a href=\"{link}\">Baca Sumber Asli</a>"
    )

def build_category_messages(categorized_articles: Dict[str, List[Dict[str, Any]]], db: DigestDatabase) -> List[str]:
    """
    Menyusun artikel yang sudah diproses dan diterjemahkan menjadi daftar pesan Telegram
    yang terpisah per kategori dengan pemisah visual yang rapi dan nyaman dibaca.
    """
    today_str = datetime.now().strftime("%d %B %Y")
    
    messages: List[str] = []
    sent_articles: List[Dict[str, Any]] = []

    # Pesan pengantar pembuka
    intro_message = (
        f"🌅 <b>DAILY WORLD & TECH DIGEST · {today_str}</b>\n"
        f"<i>Rangkuman lengkap berita dunia, nasional, dan teknologi hari ini. "
        f"Seluruh berita telah dikurasi, dirincikan lengkap, dan diterjemahkan ke Bahasa Indonesia:</i>"
    )
    messages.append(intro_message)

    for category, articles in categorized_articles.items():
        if not articles:
            continue

        category_header = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>{category.upper()}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        current_msg = category_header
        article_items: List[str] = []

        for art in articles:
            # Proses pengayaan teks dan translasi ke bahasa Indonesia
            enriched_art = process_article_details(art)
            sent_articles.append(enriched_art)
            
            item_html = format_article_item(enriched_art)
            article_items.append(item_html)

        # Gabungkan artikel-artikel dalam kategori ini
        separator = "\n\n────────────────────\n\n"
        for i, item in enumerate(article_items):
            # Cek panjang jika digabung
            addition = item if i == 0 else (separator + item)
            
            if len(current_msg) + len(addition) > 3800:
                # Jika pesan melebihi batas Telegram, pecah ke pesan baru
                messages.append(current_msg.strip())
                current_msg = f"<b>{category.upper()} (Lanjutan)</b>\n━━━━━━━━━━━━━━━━━━━━\n\n" + item
            else:
                current_msg += addition

        if current_msg.strip():
            messages.append(current_msg.strip())

    # Tandai semua artikel yang terkirim di database agar tidak duplikat di pengiriman berikutnya
    for art in sent_articles:
        db.mark_as_seen(art["link"], art["title"], art["source"])

    return messages

def dispatch_daily_digest(categorized_articles: Dict[str, List[Dict[str, Any]]], db: DigestDatabase) -> bool:
    """Mengirim seluruh potongan pesan digest per kategori ke Telegram pengguna."""
    if not categorized_articles:
        print("[Notifier] Tidak ada artikel baru hari ini.")
        return True

    print("[Notifier] Memproses rincian lengkap artikel & menerjemahkan ke Bahasa Indonesia...")
    messages = build_category_messages(categorized_articles, db)
    print(f"[Notifier] Menyiapkan {len(messages)} pesan kategori untuk dikirim ke Telegram...")

    all_success = True
    for i, msg in enumerate(messages, 1):
        success = send_telegram_message(msg)
        if success:
            print(f"[Notifier] Bagian {i}/{len(messages)} berhasil dikirim.")
        else:
            print(f"[Notifier] Bagian {i}/{len(messages)} gagal dikirim.")
            all_success = False
        
        # Jeda sejenak antar pengiriman agar tertib di Telegram API
        if i < len(messages):
            time.sleep(1.0)

    return all_success
