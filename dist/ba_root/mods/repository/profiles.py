
from repository.db import run_query


def init_db():
    run_query("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        v2Tag TEXT,
        lastIP TEXT,
        server_profile_created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)


init_db()


def get_profile(v2Tag):
    rows = run_query(
        "SELECT id, v2Tag, lastIP FROM profiles WHERE v2Tag = ?",
        (v2Tag,),
        fetch=True,
    )
    if rows:
        return {
            'id': rows[0][0],
            'v2Tag': rows[0][1],
            'lastIP': rows[0][2],
        }
    return None


def upsert_ip(v2Tag, ip):
    run_query("""
    INSERT INTO profiles (v2Tag, lastIP) VALUES (?, ?)
    ON CONFLICT(v2Tag) DO UPDATE SET lastIP=excluded.lastIP
    """, (v2Tag, ip))
