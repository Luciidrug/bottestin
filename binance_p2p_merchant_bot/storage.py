from __future__ import annotations
from typing import Iterable, Optional
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from .binance_p2p import Ad
from .config import settings


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS ad_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TIMESTAMP NOT NULL,
    adv_no TEXT NOT NULL,
    trade_type TEXT NOT NULL,
    asset TEXT NOT NULL,
    fiat_unit TEXT NOT NULL,
    price REAL NOT NULL,
    min_single_trans_amount REAL,
    max_single_trans_amount REAL,
    surplus_amount REAL,
    max_single_trans_quantity REAL,
    order_count INTEGER,
    advertiser_user_no TEXT NOT NULL,
    advertiser_nick_name TEXT,
    advertiser_month_order_count INTEGER,
    advertiser_month_finish_rate REAL,
    advertiser_positive_rate REAL,
    advertiser_is_merchant INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ad_snapshots_adv_no ON ad_snapshots(adv_no);
CREATE INDEX IF NOT EXISTS idx_ad_snapshots_captured_at ON ad_snapshots(captured_at);
CREATE INDEX IF NOT EXISTS idx_ad_snapshots_advertiser ON ad_snapshots(advertiser_user_no);
"""


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def snapshot_ads(conn: sqlite3.Connection, ads: Iterable[Ad], captured_at: Optional[datetime] = None) -> int:
    now = captured_at or datetime.now(timezone.utc)
    insert_sql = """
    INSERT INTO ad_snapshots (
        captured_at, adv_no, trade_type, asset, fiat_unit, price,
        min_single_trans_amount, max_single_trans_amount, surplus_amount, max_single_trans_quantity,
        order_count, advertiser_user_no, advertiser_nick_name, advertiser_month_order_count,
        advertiser_month_finish_rate, advertiser_positive_rate, advertiser_is_merchant
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    cur = conn.cursor()
    count = 0
    for ad in ads:
        cur.execute(
            insert_sql,
            (
                now.isoformat(),
                ad.adv_no,
                ad.trade_type,
                ad.asset,
                ad.fiat_unit,
                ad.price,
                ad.min_single_trans_amount,
                ad.max_single_trans_amount,
                ad.surplus_amount,
                ad.max_single_trans_quantity,
                ad.order_count,
                ad.advertiser.user_no,
                ad.advertiser.nick_name,
                ad.advertiser.month_order_count,
                ad.advertiser.month_finish_rate,
                ad.advertiser.positive_rate,
                1 if ad.advertiser.is_merchant else 0,
            ),
        )
        count += 1
    conn.commit()
    return count
