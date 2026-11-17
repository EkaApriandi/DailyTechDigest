import re
from typing import Dict, Any
import requests
from config import GEMINI_API_KEY

def extractive_summarize(title: str, text: str, max_chars: int = 180) -> str:
    """
    Pemroses teks lokal: membersihkan boilerplate dan menghasilkan
    1-2 kalimat intisari tanpa membutuhkan API pihak ketiga.
    """
    if not text:
        return title

    # Hapus boilerplate umum RSS feed (contoh: 'The post X appeared first on Y')
    cleaned = re.sub(r'The post .* appeared first on .*\.?', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'Read more\.\.\.?', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[\s*\.\.\.\s*\]', '', cleaned)
    cleaned = " ".join(cleaned.split())

    if not cleaned:
        return title

    # Pecah menjadi kalimat
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    summary_parts = []
    total_len = 0

    for s in sentences:
        s = s.strip()
        if not s or len(s) < 15:
            continue
        summary_parts.append(s)
        total_len += len(s)
        if total_len >= max_chars:
            break

    result = " ".join(summary_parts)
    if len(result) > max_chars:
        result = result[:max_chars].rsplit(" ", 1)[0] + "..."

    return result or title

def ai_summarize(title: str, text: str) -> str:
    """Merangkum intisari artikel menggunakan Gemini API jika kunci tersedia."""
    if not GEMINI_API_KEY:
        return extractive_summarize(title, text)

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": (
                        "Kamu adalah asisten kurator teknologi profesional. "
                        "Rangkum intisari artikel berikut dalam MAKSIMAL 1-2 KALIMAT singkat, padat, "
                        "dan informatif dalam Bahasa Indonesia. Hindari basa-basi.\n\n"
                        f"Judul: {title}\n"
                        f"Isi: {text[:800]}"
                    )
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": 100,
                "temperature": 0.2
            }
        }
        resp = requests.post(url, json=payload, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            ai_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return ai_text.replace("\n", " ")
    except Exception:
        pass

    # Fallback ke ekstraktif jika ada gangguan API
    return extractive_summarize(title, text)

def process_article_summary(article: Dict[str, Any]) -> str:
    """Memilih metode peringkasan terbaik untuk artikel."""
    title = article["title"]
    raw_summary = article["summary_raw"]
    
    if GEMINI_API_KEY:
        return ai_summarize(title, raw_summary)
    return extractive_summarize(title, raw_summary)
