import sqlite3
from pathlib import Path
from datetime import datetime, timezone, date

DB_PATH = Path("data/bot.sqlite3")

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS seen (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tweet_id TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS drops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dupe_key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  official_url TEXT NOT NULL,
  official_domain TEXT,
  verified INTEGER NOT NULL,
  score INTEGER NOT NULL,
  root_tweet_id TEXT,
  posted_at TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dupe_key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  official_url TEXT NOT NULL,
  official_domain TEXT,
  verified INTEGER NOT NULL,
  score INTEGER NOT NULL,
  reason TEXT,
  source_tweet_id TEXT,
  source_text TEXT,
  created_at TEXT NOT NULL,
  approved INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS meta (
  k TEXT PRIMARY KEY,
  v TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  event TEXT NOT NULL,
  detail TEXT
);
"""

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def today_utc() -> str:
    return date.today().isoformat()

def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def log_metric(conn: sqlite3.Connection, event: str, detail: str | None = None) -> None:
    conn.execute("INSERT INTO metrics(ts,event,detail) VALUES(?,?,?)", (now(), event, detail))
    conn.commit()

def mark_seen(conn: sqlite3.Connection, tweet_id: str) -> bool:
    try:
        conn.execute("INSERT INTO seen(tweet_id, created_at) VALUES(?,?)", (tweet_id, now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def has_dupe(conn: sqlite3.Connection, dupe_key: str) -> bool:
    r = conn.execute("SELECT 1 FROM drops WHERE dupe_key=?", (dupe_key,)).fetchone()
    if r:
        return True
    r2 = conn.execute("SELECT 1 FROM review_queue WHERE dupe_key=?", (dupe_key,)).fetchone()
    return r2 is not None

def insert_drop(conn: sqlite3.Connection, dupe_key: str, name: str, official_url: str, official_domain: str | None,
                verified: bool, score: int) -> int:
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO drops(dupe_key,name,official_url,official_domain,verified,score,created_at)
           VALUES(?,?,?,?,?,?,?)""",
        (dupe_key, name, official_url, official_domain, 1 if verified else 0, int(score), now()),
    )
    conn.commit()
    return int(cur.lastrowid)

def mark_posted(conn: sqlite3.Connection, drop_id: int, root_tweet_id: str) -> None:
    conn.execute("UPDATE drops SET root_tweet_id=?, posted_at=? WHERE id=?", (root_tweet_id, now(), drop_id))
    conn.commit()

def inc_post_counter(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT v FROM meta WHERE k='post_counter'").fetchone()
    cur = int(row["v"]) if row else 0
    cur += 1
    conn.execute(
        "INSERT INTO meta(k,v) VALUES('post_counter', ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
        (str(cur),),
    )
    conn.commit()
    return cur

def get_post_counter(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT v FROM meta WHERE k='post_counter'").fetchone()
    return int(row["v"]) if row else 0

def get_last_digest_day(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT v FROM meta WHERE k='last_digest_day'").fetchone()
    return row["v"] if row else None

def set_last_digest_day(conn: sqlite3.Connection, day: str) -> None:
    conn.execute(
        "INSERT INTO meta(k,v) VALUES('last_digest_day', ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
        (day,),
    )
    conn.commit()

def top_recent_drops(conn: sqlite3.Connection, limit: int = 8):
    return conn.execute(
        """SELECT name, official_url, verified, score, posted_at
           FROM drops
           WHERE posted_at IS NOT NULL
           ORDER BY posted_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()

def enqueue_review(conn: sqlite3.Connection, dupe_key: str, name: str, official_url: str, official_domain: str | None,
                   verified: bool, score: int, reason: str, source_tweet_id: str | None, source_text: str | None) -> None:
    try:
        conn.execute(
            """INSERT INTO review_queue(dupe_key,name,official_url,official_domain,verified,score,reason,source_tweet_id,source_text,created_at,approved)
               VALUES(?,?,?,?,?,?,?,?,?,?,0)""",
            (
                dupe_key, name, official_url, official_domain, 1 if verified else 0, int(score),
                reason, source_tweet_id, (source_text or "")[:2000], now()
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass

def approve_top(conn: sqlite3.Connection, limit: int) -> None:
    conn.execute(
        """UPDATE review_queue
           SET approved=1
           WHERE id IN (
             SELECT id FROM review_queue WHERE approved=0
             ORDER BY score DESC, created_at ASC
             LIMIT ?
           )""",
        (limit,),
    )
    conn.commit()

def pop_approved(conn: sqlite3.Connection, limit: int):
    return conn.execute(
        """SELECT * FROM review_queue
           WHERE approved=1
           ORDER BY score DESC, created_at ASC
           LIMIT ?""",
        (limit,),
    ).fetchall()

def remove_from_queue(conn: sqlite3.Connection, queue_id: int) -> None:
    conn.execute("DELETE FROM review_queue WHERE id=?", (queue_id,))
    conn.commit()
