"""Read-only access to the aircraft database.

The web app never writes - the crawler owns the database - so connections are
opened read-only. The database may not exist yet on a fresh deployment (the
first crawl is still running), so queries degrade to empty results instead of
raising."""

import os
import sqlite3


def db_path():
    return os.environ.get("WTAC_DB_PATH", "planes.db")


def _query(sql, params=()):
    try:
        conn = sqlite3.connect(f"file:{db_path()}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        return []
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def search(term, limit=10):
    like = f"%{term}%"
    prefix = f"{term}%"
    rows = _query(
        "SELECT slug, name, image_url, nation, rank, br_rb FROM aircraft "
        "WHERE name LIKE ? "
        "ORDER BY CASE WHEN name LIKE ? THEN 0 ELSE 1 END, length(name), name "
        "LIMIT ?",
        (like, prefix, limit),
    )
    return [dict(row) for row in rows]


def get(identifier):
    rows = _query("SELECT * FROM aircraft WHERE slug = ?", (identifier,))
    if not rows:
        rows = _query(
            "SELECT * FROM aircraft WHERE lower(name) = lower(?)", (identifier,)
        )
    if not rows:
        rows = _query(
            "SELECT * FROM aircraft WHERE name LIKE ? ORDER BY length(name) LIMIT 1",
            (f"%{identifier}%",),
        )
    return dict(rows[0]) if rows else None


def count():
    rows = _query("SELECT COUNT(*) AS total FROM aircraft")
    return rows[0]["total"] if rows else 0
