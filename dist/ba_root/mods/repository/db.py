import os
import sqlite3
import time
import random

DB_PATH = os.path.expanduser("~/shared_bcs_data/bcsserverdata.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

MAX_RETRIES = 5
RETRY_DELAY = (0.1, 0.5)


def get_connection():
    """Get a SQLite connection with WAL enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def run_query(query, params=(), fetch=False):
    """Execute query with retry logic. Returns rows if fetch=True."""
    retries = 0
    while True:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall() if fetch else None
            conn.commit()
            conn.close()
            return rows
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                retries += 1
                if retries > MAX_RETRIES:
                    raise RuntimeError(
                        "Max retries exceeded due to DB lock") from e
                time.sleep(random.uniform(*RETRY_DELAY))
            else:
                raise
