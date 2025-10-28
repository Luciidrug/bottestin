from __future__ import annotations
from typing import Optional, Tuple
import sqlite3
from datetime import datetime, timedelta, timezone
import math
from .config import settings


def _parse_dt(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s)
    except Exception:
        # Fallback: treat as UTC now
        return datetime.now(timezone.utc)


def calculate_new_deals(
    conn: sqlite3.Connection,
    advertiser_user_no: Optional[str] = None,
    days: int = 1,
) -> Tuple[int, float]:
    """
    Estimate new deals over the last period using changes in month_order_count.

    Returns (new_deals_count, avg_new_deals_per_merchant)
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    where = "WHERE captured_at >= ?"
    params = [since.isoformat()]
    if advertiser_user_no:
        where += " AND advertiser_user_no = ?"
        params.append(advertiser_user_no)
    sql = f"""
    WITH latest AS (
        SELECT advertiser_user_no,
               MAX(captured_at) AS latest_ts
          FROM ad_snapshots
          {where}
         GROUP BY advertiser_user_no
    ), first AS (
        SELECT s.advertiser_user_no,
               MIN(s.captured_at) AS first_ts
          FROM ad_snapshots s
          JOIN latest l USING (advertiser_user_no)
         WHERE s.captured_at >= ?
         GROUP BY s.advertiser_user_no
    ), joined AS (
        SELECT l.advertiser_user_no,
               (SELECT advertiser_month_order_count FROM ad_snapshots s WHERE s.advertiser_user_no = l.advertiser_user_no AND s.captured_at = l.latest_ts LIMIT 1) AS last_count,
               (SELECT advertiser_month_order_count FROM ad_snapshots s WHERE s.advertiser_user_no = f.advertiser_user_no AND s.captured_at = f.first_ts LIMIT 1) AS first_count
          FROM latest l
          JOIN first f USING (advertiser_user_no)
    )
    SELECT SUM(CASE WHEN last_count IS NOT NULL AND first_count IS NOT NULL AND last_count >= first_count THEN (last_count - first_count) ELSE 0 END) AS new_deals,
           COUNT(*) AS merchants
      FROM joined
    """
    # since param appears twice
    params2 = [since.isoformat()] + params
    cur = conn.execute(sql, params2)
    row = cur.fetchone()
    new_deals = int(row[0] or 0)
    merchants = int(row[1] or 0)
    avg_per_merchant = (new_deals / merchants) if merchants else 0.0
    return new_deals, avg_per_merchant


def calculate_average_check(
    conn: sqlite3.Connection,
    days: int = 1,
) -> float:
    """
    Approximate average check using the midpoint between min and max of ad ranges.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    sql = """
    SELECT AVG( 
        CASE 
            WHEN max_single_trans_amount IS NOT NULL AND min_single_trans_amount IS NOT NULL THEN (max_single_trans_amount + min_single_trans_amount) / 2.0
            WHEN max_single_trans_amount IS NOT NULL THEN max_single_trans_amount * 0.6
            WHEN min_single_trans_amount IS NOT NULL THEN min_single_trans_amount * 1.2
            ELSE NULL
        END
    ) AS avg_check
      FROM ad_snapshots
     WHERE captured_at >= ? AND advertiser_is_merchant = 1 AND fiat_unit = ? AND asset = ?
    """
    cur = conn.execute(sql, (since.isoformat(), settings.fiat, settings.asset))
    row = cur.fetchone()
    return float(row[0] or 0.0)


def calculate_average_commission(
    conn: sqlite3.Connection,
    days: int = 1,
) -> float:
    """
    Estimate average commission as spread between top SELL and BUY prices relative to mid.
    This is a rough proxy; actual commission depends on fees and merchant policies.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    sql = """
    WITH latest_prices AS (
        SELECT trade_type,
               AVG(price) AS avg_price
          FROM ad_snapshots
         WHERE captured_at >= ? AND advertiser_is_merchant = 1 AND fiat_unit = ? AND asset = ?
         GROUP BY trade_type
    )
    SELECT 
        (SELECT avg_price FROM latest_prices WHERE trade_type = 'SELL') AS sell_avg,
        (SELECT avg_price FROM latest_prices WHERE trade_type = 'BUY') AS buy_avg
    """
    cur = conn.execute(sql, (since.isoformat(), settings.fiat, settings.asset))
    row = cur.fetchone()
    sell_avg = float(row[0] or 0.0)
    buy_avg = float(row[1] or 0.0)
    if sell_avg <= 0 or buy_avg <= 0:
        return 0.0
    mid = (sell_avg + buy_avg) / 2.0
    spread = abs(sell_avg - buy_avg)
    commission_pct = (spread / mid) * 100.0
    return commission_pct
