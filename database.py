import sqlite3
from pathlib import Path
from config import DB_PATH

class DigestDatabase:
    """Mengelola penyimpanan artikel yang sudah pernah dikirim agar tidak duplikat."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def init_db(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS seen_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_seen_url ON seen_articles(url)")
            conn.commit()

    def is_seen(self, url: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM seen_articles WHERE url = ?", (url.strip(),))
            return cursor.fetchone() is not None

    def mark_as_seen(self, url: str, title: str, source: str) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO seen_articles (url, title, source)
                VALUES (?, ?, ?)
            """, (url.strip(), title.strip(), source.strip()))
            conn.commit()

    def cleanup_old_records(self, days: int = 30) -> int:
        """Menghapus riwayat artikel lama agar database tetap ringan."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM seen_articles 
                WHERE created_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            conn.commit()
            return cursor.rowcount
