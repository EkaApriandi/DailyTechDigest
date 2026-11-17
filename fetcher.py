import logging
from typing import Any, Dict, List
import requests
import feedparser
from bs4 import BeautifulSoup

from config import RSS_FEEDS, MAX_ARTICLES_PER_FEED
from database import DigestDatabase

logger = logging.getLogger("DigestFetcher")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 DailyTechDigest/1.0"
    )
}

def clean_html(raw_html: str) -> str:
    """Membersihkan tag HTML dan menyisakan teks bersih."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    # Hapus script, style, dan elemen iklan
    for tag in soup(["script", "style", "figure", "img", "iframe"]):
        tag.decompose()
    text = soup.get_text(separator=" ").strip()
    return " ".join(text.split())

def fetch_feed_articles(feed_info: Dict[str, str], db: DigestDatabase, limit: int = MAX_ARTICLES_PER_FEED) -> List[Dict[str, Any]]:
    """Mengambil artikel terbaru dari satu RSS Feed dengan filter deduplikasi."""
    url = feed_info["url"]
    source_name = feed_info["name"]
    category = feed_info["category"]
    articles = []

    try:
        response = requests.get(url, headers=HEADERS, timeout=12)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)

        count = 0
        for entry in parsed.entries:
            link = entry.get("link", "").strip()
            title = entry.get("title", "").strip()

            if not link or not title:
                continue

            # Cek apakah artikel sudah pernah dikirim sebelumnya
            if db.is_seen(link):
                continue

            # Ambil ringkasan / deskripsi artikel
            raw_summary = (
                entry.get("summary")
                or entry.get("description")
                or (entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "")
            )
            cleaned_summary = clean_html(raw_summary)

            articles.append({
                "category": category,
                "source": source_name,
                "title": title,
                "link": link,
                "summary_raw": cleaned_summary,
                "published": entry.get("published", "")
            })

            count += 1
            if count >= limit:
                break

    except Exception as e:
        logger.warning(f"Gagal mengambil feed [{source_name}]: {e}")

    return articles

def fetch_all_fresh_articles(db: DigestDatabase) -> Dict[str, List[Dict[str, Any]]]:
    """Mengambil seluruh artikel terbaru yang belum pernah dibaca, dikelompokkan per kategori."""
    categorized: Dict[str, List[Dict[str, Any]]] = {}

    for feed in RSS_FEEDS:
        category = feed["category"]
        if category not in categorized:
            categorized[category] = []

        fresh = fetch_feed_articles(feed, db)
        categorized[category].extend(fresh)

    # Hapus kategori yang kosong
    return {k: v for k, v in categorized.items() if v}
