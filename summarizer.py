import os
import re
import html
import logging
from typing import Dict, Any, List
import requests

from config import GEMINI_API_KEY

logger = logging.getLogger("DigestSummarizer")

# Cache in-memory untuk menghindari translasi berulang
_TRANSLATION_CACHE: Dict[str, str] = {}

def is_indonesian_text(text: str) -> bool:
    """Mendeteksi apakah teks kemungkinan besar sudah berbahasa Indonesia."""
    if not text:
        return False
    # Kata-kata fungsional umum bahasa Indonesia
    id_words = {
        "yang", "dan", "di", "ini", "ke", "dari", "untuk", "pada", "adalah",
        "dengan", "dalam", "tidak", "akan", "juga", "oleh", "sudah", "bisa",
        "dapat", "sebagai", "tersebut", "mereka", "saat", "bahwa", "pemerintah"
    }
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    if not words:
        return False
    match_count = sum(1 for w in words if w in id_words)
    # Jika proporsi kata bahasa Indonesia cukup tinggi (> 10% atau minimal 3 kata cocok)
    return match_count >= 3 or (len(words) > 0 and (match_count / len(words)) > 0.15)

def translate_to_indonesian(text: str) -> str:
    """
    Menerjemahkan teks dari Bahasa Inggris ke Bahasa Indonesia secara gratis & berkualitas tinggi
    menggunakan MyMemory API dengan pemecahan berbasis kalimat dan caching.
    """
    if not text or not text.strip():
        return ""
    
    clean_input = text.strip()
    
    # Jika sudah bahasa Indonesia, kembalikan langsung
    if is_indonesian_text(clean_input):
        return clean_input

    # Cek cache
    if clean_input in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[clean_input]

    # MyMemory API membatasi ~500 karakter per request.
    # Kita pecah menjadi kelompok kalimat agar translasi tetap utuh dan mengalir.
    sentences = re.split(r'(?<=[.!?])\s+', clean_input)
    chunks: List[str] = []
    curr = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(curr) + len(s) + 1 <= 400:
            curr = f"{curr} {s}".strip()
        else:
            if curr:
                chunks.append(curr)
            curr = s
    if curr:
        chunks.append(curr)

    if not chunks:
        return clean_input

    translated_parts = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DailyDigestBot/2.0"}

    for chunk in chunks:
        # Jika chunk sangat pendek dan sudah di-cache
        if chunk in _TRANSLATION_CACHE:
            translated_parts.append(_TRANSLATION_CACHE[chunk])
            continue

        success = False
        try:
            url = "https://api.mymemory.translated.net/get"
            params = {"q": chunk, "langpair": "en|id"}
            resp = requests.get(url, params=params, headers=headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                t_text = data.get("responseData", {}).get("translatedText")
                # Pastikan respon valid dan bukan pesan warning kuota
                if t_text and not t_text.upper().startswith("MYMEMORY WARNING"):
                    decoded = html.unescape(t_text)
                    _TRANSLATION_CACHE[chunk] = decoded
                    translated_parts.append(decoded)
                    success = True
        except Exception as e:
            logger.debug(f"Translasi via MyMemory error: {e}")

        if not success:
            # Fallback jika jaringan offline atau error
            translated_parts.append(chunk)

    result = " ".join(translated_parts).strip()
    _TRANSLATION_CACHE[clean_input] = result
    return result

def clean_article_text(text: str) -> str:
    """Membersihkan boilerplate umum dari RSS feed."""
    if not text:
        return ""
    cleaned = text
    # Hapus boilerplate umum
    boilerplate_patterns = [
        r'The post .* appeared first on .*\.?',
        r'Read the full story at .*\.?',
        r'Baca kisah lengkapnya di .*\.?',
        r'Read more\.\.\.?',
        r'Continue reading\.\.\.?',
        r'Presented by Gravitee\.?',
        r'Presented by .*\.?',
        r'\[\s*\.\.\.\s*\]',
        r'©\s*\d{4}.*reserved\.?',
        r'All rights reserved\.?',
    ]
    for pat in boilerplate_patterns:
        cleaned = re.sub(pat, '', cleaned, flags=re.IGNORECASE)
    
    return " ".join(cleaned.split()).strip()

def extract_detailed_summary(title: str, text: str, max_sentences: int = 4) -> str:
    """
    Mengekstrak penjelasan lengkap dan tuntas dari artikel tanpa memotong kalimat.
    Menghasilkan 2-4 kalimat lengkap yang padat fakta.
    """
    cleaned = clean_article_text(text)
    if not cleaned:
        return title

    # Pecah menjadi kalimat-kalimat lengkap
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    valid_sentences = []

    for s in sentences:
        s = s.strip()
        # Lewati kalimat yang terlalu pendek atau hanya label/iklan
        if len(s) < 25:
            continue
        # Lewati kalimat promo umum
        if any(w in s.lower() for w in ["subscribe", "newsletter", "sign up", "terms of use", "privacy policy"]):
            continue
        valid_sentences.append(s)
        if len(valid_sentences) >= max_sentences:
            break

    if not valid_sentences:
        return cleaned if len(cleaned) < 400 else title

    return " ".join(valid_sentences)

def ai_summarize_gemini(title: str, text: str) -> str:
    """Merangkum intisari artikel menggunakan Gemini API jika kunci tersedia di .env."""
    if not GEMINI_API_KEY:
        return ""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = (
            "Kamu adalah asisten kurator berita profesional. Berikan rincian berita berikut secara LENGKAP, "
            "JELAS, dan MENDALAM dalam Bahasa Indonesia (2-3 kalimat lengkap yang mengalir dan menjelaskan peristiwa, "
            "latar belakang, serta implikasinya). JANGAN memotong kalimat di tengah jalan. Hindari kata pembuka seperti 'Berita ini...' atau 'Tentu saja'. Langsung sajikan faktanya.\n\n"
            f"Judul Asli: {title}\n"
            f"Teks Berita: {text[:1500]}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 250,
                "temperature": 0.2
            }
        }
        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            ai_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return " ".join(ai_text.split())
    except Exception as e:
        logger.warning(f"Gemini API summarization gagal: {e}")

    return ""

def process_article_details(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Memproses artikel agar memiliki judul dan rincian lengkap dalam Bahasa Indonesia:
    - Judul diterjemahkan ke Bahasa Indonesia (jika berbahasa asing).
    - Rincian berita lengkap tanpa terpotong (tidak menggunakan '...').
    - Menggunakan Gemini AI jika ada API key, atau translasi mendalam bebas kuota.
    """
    orig_title = article.get("title", "").strip()
    raw_summary = article.get("summary_raw", "").strip()
    is_id = article.get("is_indonesian", False)

    # 1. Judul Bahasa Indonesia
    if is_id or is_indonesian_text(orig_title):
        title_id = orig_title
    else:
        title_id = translate_to_indonesian(orig_title)

    # 2. Rincian Lengkap Bahasa Indonesia
    summary_id = ""
    # Coba gunakan Gemini AI jika key tersedia
    if GEMINI_API_KEY:
        summary_id = ai_summarize_gemini(orig_title, raw_summary)

    # Fallback ke ekstraksi kalimat lengkap + translasi berkualitas
    if not summary_id:
        detailed_en = extract_detailed_summary(orig_title, raw_summary, max_sentences=4)
        if is_id or is_indonesian_text(detailed_en):
            summary_id = detailed_en
        else:
            summary_id = translate_to_indonesian(detailed_en)

    return {
        **article,
        "title_id": title_id,
        "summary_id": summary_id
    }
