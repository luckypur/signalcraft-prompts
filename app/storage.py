import os
import sqlite3
from pathlib import Path

SEEDS = [
    ("db", "Database outage", "For database degradation, acknowledge write/read impact; provide next update within 30 minutes. Do not promise a repair ETA without confirmation."),
    ("payment", "Payment delays", "For payment-processing problems, clarify if charges were captured or only authorized. Never claim a refund completed without ledger confirmation."),
    ("auth", "Login and authentication", "For sign-in failures, mention affected login paths; never request passwords, OTPs or MFA recovery codes."),
    ("delivery", "Delivery status drift", "For delivery tracking failures, separate a delayed tracking update from an actual missing parcel. Don't guarantee an arrival date."),
    ("privacy", "Potential personal data incident", "For suspected data exposure, do not assert personal information was leaked before verification; refer to the security response team."),
    ("api", "API error spikes", "For API 5xx incidents, explain which endpoints are affected and whether retries are safe; avoid providing an unsupported recovery estimate."),
]


def connect(path: str | None = None):
    location = path or os.getenv("DB_PATH", "/app/data/signalcraft.sqlite3")
    Path(location).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(location, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runbooks(id TEXT PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS generations(
          id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          incident TEXT, audience TEXT, variant TEXT, prompt TEXT, output TEXT, provider TEXT
        );
    """)
    conn.executemany("INSERT OR IGNORE INTO runbooks(id,title,content) VALUES (?,?,?)", SEEDS)
    conn.commit()
    return conn


def runbooks(conn):
    return [dict(x) for x in conn.execute("SELECT id,title,content FROM runbooks")]
