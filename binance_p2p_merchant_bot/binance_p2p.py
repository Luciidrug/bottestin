from __future__ import annotations
from typing import Dict, Any, Iterable, List, Optional
from dataclasses import dataclass
from .http_client import HttpClient, make_default_client
from .config import settings


SEARCH_URLS = [
    # Try multiple endpoints as Binance changes frequently
    "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search",
    "https://p2p.binance.com/bapi/c2c/v2/public/c2c/adv/search",
    "https://p2p.binance.com/bapi/c2c/adv/v1/public/adv/search",
]


@dataclass
class Advertiser:
    user_no: str
    nick_name: str
    month_order_count: Optional[int]
    month_finish_rate: Optional[float]
    positive_rate: Optional[float]
    is_merchant: bool


@dataclass
class Ad:
    adv_no: str
    trade_type: str  # BUY or SELL (from buyer perspective)
    asset: str
    fiat_unit: str
    price: float
    min_single_trans_amount: Optional[float]
    max_single_trans_amount: Optional[float]
    surplus_amount: Optional[float]
    max_single_trans_quantity: Optional[float]
    order_count: Optional[int]
    advertiser: Advertiser


def _parse_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(str(value).replace(",", ""))
    except Exception:
        return None


def parse_ad(item: Dict[str, Any]) -> Optional[Ad]:
    try:
        adv = item.get("adv") or {}
        advertiser = item.get("advertiser") or {}
        return Ad(
            adv_no=str(adv.get("advNo")),
            trade_type=str(adv.get("tradeType")),
            asset=str(adv.get("asset")),
            fiat_unit=str(adv.get("fiatUnit")),
            price=float(adv.get("price")),
            min_single_trans_amount=_parse_float(adv.get("minSingleTransAmount")),
            max_single_trans_amount=_parse_float(adv.get("maxSingleTransAmount")),
            surplus_amount=_parse_float(adv.get("surplusAmount")),
            max_single_trans_quantity=_parse_float(adv.get("maxSingleTransQuantity")),
            order_count=int(adv.get("orderCount")) if adv.get("orderCount") is not None else None,
            advertiser=Advertiser(
                user_no=str(advertiser.get("userNo")),
                nick_name=str(advertiser.get("nickName")),
                month_order_count=int(advertiser.get("monthOrderCount")) if advertiser.get("monthOrderCount") is not None else None,
                month_finish_rate=_parse_float(advertiser.get("monthFinishRate")),
                positive_rate=_parse_float(advertiser.get("positiveRate")),
                is_merchant=bool(advertiser.get("userType") == "merchant" or advertiser.get("isMerchant") is True),
            ),
        )
    except Exception:
        return None


def search_ads(
    client: Optional[HttpClient],
    trade_type: str,
    asset: str = settings.asset,
    fiat: str = settings.fiat,
    page: int = 1,
    rows: int = settings.rows_per_page,
    pay_types: Optional[List[str]] = None,
    publisher_type: Optional[str] = None,  # "merchant" or None
) -> Dict[str, Any]:
    if client is None:
        client = make_default_client()
    payload = {
        "page": page,
        "rows": rows,
        "asset": asset,
        "tradeType": trade_type,
        "fiat": fiat,
        "payTypes": pay_types or [],
    }
    if publisher_type:
        payload["publisherType"] = publisher_type
    # Try multiple endpoints until one returns non-empty data or success flag
    last_error: Optional[Exception] = None
    for url in SEARCH_URLS:
        try:
            data = client.post_json(url, json=payload)
            # Expected schema: { code, data: [ { adv, advertiser } ], total, success }
            if isinstance(data, dict) and data.get("success") and isinstance(data.get("data"), list):
                return data
            # Some endpoints return HTTP 200 with no data; continue
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
    if last_error:
        raise last_error
    return {"code": "000000", "data": [], "total": 0, "success": False}


def iter_all_ads(
    trade_type: str,
    asset: str = settings.asset,
    fiat: str = settings.fiat,
    include_non_merchants: bool = False,
    max_pages: int = settings.max_pages,
) -> Iterable[Ad]:
    client = make_default_client()
    try:
        for page in range(1, max_pages + 1):
            data = search_ads(
                client=client,
                trade_type=trade_type,
                asset=asset,
                fiat=fiat,
                page=page,
                rows=settings.rows_per_page,
                publisher_type=None if include_non_merchants else "merchant",
            )
            items = data.get("data") or []
            if not items:
                break
            for item in items:
                ad = parse_ad(item)
                if ad is None:
                    continue
                if not include_non_merchants and not ad.advertiser.is_merchant:
                    continue
                yield ad
    finally:
        client.close()
