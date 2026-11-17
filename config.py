import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
env_file = BASE_DIR / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(env_file)
except ImportError:
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
DIGEST_TIME = os.getenv("DIGEST_TIME", "07:00").strip()
MAX_ARTICLES_PER_FEED = int(os.getenv("MAX_ARTICLES_PER_FEED", "3"))

raw_db_path = os.getenv("DATABASE_PATH", "digest.db")
db_p = Path(raw_db_path)
DB_PATH = db_p if db_p.is_absolute() else (BASE_DIR / db_p)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Daftar RSS Feed berita umum dunia, nasional, dan teknologi terkurasi
RSS_FEEDS = [
    {
        "category": "🌍 Peristiwa Dunia (World News)",
        "name": "BBC World",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
    },
    {
        "category": "🇮🇩 Sorotan Utama Indonesia",
        "name": "BBC Indonesia",
        "url": "https://feeds.bbci.co.uk/indonesia/rss.xml",
    },
    {
        "category": "🇮🇩 Sorotan Utama Indonesia",
        "name": "Antara Terkini",
        "url": "https://www.antaranews.com/rss/terkini.xml",
    },
    {
        "category": "🤖 Tren AI & Riset Masa Depan",
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
    },
    {
        "category": "🤖 Tren AI & Riset Masa Depan",
        "name": "MIT Tech Review",
        "url": "https://www.technologyreview.com/feed/",
    },
    {
        "category": "💻 Bisnis, Startup & Teknologi",
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
    },
    {
        "category": "💻 Bisnis, Startup & Teknologi",
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
    },
    {
        "category": "🌐 Gadget & Budaya Digital",
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
    }
]
