import html
from datetime import datetime
from typing import Dict, List, Any
import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from database import DigestDatabase
from summarizer import process_article_summary

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

def build_digest_messages(categorized_articles: Dict[str, List[Dict[str, Any]]], db: DigestDatabase) -> List[str]:
    """
    Menyusun kumpulan artikel menjadi pesan berformat HTML elegan,
    lengkap dengan pemecahan otomatis jika panjang teks melebihi batas Telegram (4096 karakter).
    """
    today_str = datetime.now().strftime("%d %b %Y")
    header = f"🌅 <b>DAILY TECH DIGEST · {today_str}</b>\n<i>Kurasi berita teknologi & riset AI terkini:</i>\n"

    chunks = []
    current_chunk = header
    sent_articles = []

    for category, articles in categorized_articles.items():
        cat_section = f"\n━━━━━━━━━━━━━━━━━━━━\n<b>{category}</b>\n"
        
        # Cek apakah header kategori muat di chunk saat ini
        if len(current_chunk) + len(cat_section) > 3500:
            chunks.append(current_chunk)
            current_chunk = cat_section
        else:
            current_chunk += cat_section

        for art in articles:
            title_escaped = html.escape(art["title"])
            source_escaped = html.escape(art["source"])
            link = art["link"]

            # Buat ringkasan padat
            summary_text = html.escape(process_article_summary(art))

            item_text = (
                f"\n• <b>{title_escaped}</b> ({source_escaped})\n"
                f"  {summary_text}\n"
                f"  👉 <a href=\"{link}\">Baca Sumber Lengkap</a>\n"
            )

            if len(current_chunk) + len(item_text) > 3800:
                chunks.append(current_chunk)
                current_chunk = item_text
            else:
                current_chunk += item_text

            sent_articles.append(art)

    if current_chunk.strip():
        chunks.append(current_chunk)

    # Tandai seluruh artikel yang masuk digest sebagai sudah dibaca
    for art in sent_articles:
        db.mark_as_seen(art["link"], art["title"], art["source"])

    return chunks

def dispatch_daily_digest(categorized_articles: Dict[str, List[Dict[str, Any]]], db: DigestDatabase) -> bool:
    """Mengirim seluruh potongan pesan digest ke Telegram pengguna."""
    if not categorized_articles:
        print("[Notifier] Tidak ada artikel baru hari ini.")
        return True

    messages = build_digest_messages(categorized_articles, db)
    all_success = True

    for i, msg in enumerate(messages, 1):
        footer = f"\n<i>(Bagian {i}/{len(messages)})</i>" if len(messages) > 1 else ""
        success = send_telegram_message(msg + footer)
        if not success:
            all_success = False

    return all_success
