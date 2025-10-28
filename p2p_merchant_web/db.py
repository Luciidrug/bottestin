from __future__ import annotations
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

DB_PATH = "/workspace/p2p_merchant_web.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT,
    title TEXT NOT NULL,
    trade_type TEXT NOT NULL,
    price REAL NOT NULL,
    min_amount REAL,
    max_amount REAL,
    fiat TEXT NOT NULL,
    asset TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    updated_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ads_external ON ads(external_id);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def list_ads() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM ads ORDER BY id DESC")
    return [dict(row) for row in cur.fetchall()]


def create_ad(
    title: str,
    trade_type: str,
    price: float,
    min_amount: Optional[float],
    max_amount: Optional[float],
    fiat: str,
    asset: str,
    external_id: Optional[str],
) -> int:
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ads (external_id, title, trade_type, price, min_amount, max_amount, fiat, asset, status, updated_at)
        VALUES (?,?,?,?,?,?,?,?, 'active', ?)
        """,
        (external_id, title, trade_type, price, min_amount, max_amount, fiat, asset, now),
    )
    conn.commit()
    return int(cur.lastrowid)


def get_ad(ad_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.execute("SELECT * FROM ads WHERE id = ?", (ad_id,))
    row = cur.fetchone()
    return dict(row) if row else None


def update_ad_fields(
    ad_id: int,
    title: Optional[str] = None,
    price: Optional[float] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> None:
    conn = get_connection()
    sets = []
    params: List[Any] = []
    if title is not None:
        sets.append("title = ?")
        params.append(title)
    if price is not None:
        sets.append("price = ?")
        params.append(price)
    if min_amount is not None:
        sets.append("min_amount = ?")
        params.append(min_amount)
    if max_amount is not None:
        sets.append("max_amount = ?")
        params.append(max_amount)
    sets.append("updated_at = ?")
    params.append(datetime.now(timezone.utc).isoformat())
    params.append(ad_id)
    sql = f"UPDATE ads SET {', '.join(sets)} WHERE id = ?"
    conn.execute(sql, params)
    conn.commit()


def toggle_ad_status(ad_id: int) -> None:
    conn = get_connection()
    cur = conn.execute("SELECT status FROM ads WHERE id = ?", (ad_id,))
    row = cur.fetchone()
    if not row:
        return
    new_status = "paused" if row[0] == "active" else "active"
    conn.execute("UPDATE ads SET status = ?, updated_at = ? WHERE id = ?", (
        new_status,
        datetime.now(timezone.utc).isoformat(),
        ad_id,
    ))
    conn.commit()
