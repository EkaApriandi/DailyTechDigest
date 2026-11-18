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
        "Chrome/124.0.0.0 Safari/537.36 DailyTechDigest/2.0"
    )
}

def clean_html(raw_html: str) -> str:
    """Membersihkan tag HTML dan menyisakan teks bersih."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    # Hapus script, style, gambar, video, dan elemen navigasi
    for tag in soup(["script", "style", "figure", "img", "iframe", "svg", "audio", "video"]):
        tag.decompose()
    text = soup.get_text(separator=" ").strip()
    return " ".join(text.split())

def fetch_lead_paragraphs_from_url(url: str, timeout: int = 6) -> str:
    """
    Mengambil paragraf pembuka langsung dari URL artikel jika ringkasan RSS terlalu singkat / kosong.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer", "aside", "figure", "form", "button"]):
                tag.decompose()
            paras = []
            for p in soup.find_all("p"):
                txt = " ".join(p.get_text().split()).strip()
                # Filter paragraf yang bermakna dan bukan disclaimer/kebijakan
                if len(txt) > 40 and not any(skip in txt.lower() for skip in [
                    "cookie", "subscribe", "newsletter", "terms of use", "privacy policy",
                    "all rights reserved", "advertisement", "sign in"
                ]):
                    paras.append(txt)
                    if len(paras) >= 3:
                        break
            if paras:
                return " ".join(paras)
    except Exception as e:
        logger.debug(f"Lead scraper skipped for {url}: {e}")
    return ""

def fetch_feed_articles(feed_info: Dict[str, str], db: DigestDatabase, limit: int = MAX_ARTICLES_PER_FEED) -> List[Dict[str, Any]]:
    """Mengambil artikel terbaru dari satu RSS Feed dengan filter deduplikasi dan pengayaan teks."""
    url = feed_info["url"]
    source_name = feed_info["name"]
    category = feed_info["category"]
    is_id = source_name in ["BBC Indonesia", "Antara Terkini"] or "Indonesia" in category

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

            # Ambil konten terbaik dari RSS
            raw_summary = ""
            # Periksa 'content' terlebih dahulu karena sering kali memuat teks lebih lengkap
            if entry.get("content"):
                raw_summary = entry["content"][0].get("value", "")

            # Jika 'content' kosong atau lebih pendek dari summary/description
            summary_candidate = entry.get("summary") or entry.get("description") or ""
            if len(summary_candidate) > len(raw_summary):
                raw_summary = summary_candidate

            cleaned_summary = clean_html(raw_summary)

            # Jika ringkasan dari RSS terlalu minim (< 120 karakter atau terpotong '...'),
            # ambil paragraf pembuka langsung dari situs web artikel
            if len(cleaned_summary) < 120 or cleaned_summary.endswith("...") or "presented by" in cleaned_summary.lower():
                lead = fetch_lead_paragraphs_from_url(link)
                if lead and len(lead) > len(cleaned_summary):
                    cleaned_summary = lead

            articles.append({
                "category": category,
                "source": source_name,
                "title": title,
                "link": link,
                "summary_raw": cleaned_summary,
                "published": entry.get("published", ""),
                "is_indonesian": is_id
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
