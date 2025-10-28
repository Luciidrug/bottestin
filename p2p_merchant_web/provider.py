from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AdUpdate:
    price: Optional[float] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    status: Optional[str] = None  # 'active'|'paused'


class MockProvider:
    def __init__(self) -> None:
        self.mode = "mock"
        self.has_credentials = False

    def push_update(self, external_id: Optional[str], update: AdUpdate) -> None:
        # No-op; in real provider we'd call Binance Merchant API
        return


class BinanceMerchantProvider:
    def __init__(self, api_key: str, api_secret: str) -> None:
        self.mode = "binance"
        self.api_key = api_key
        self.api_secret = api_secret
        self.has_credentials = True
        # NOTE: Real implementation should sign requests (HMAC-SHA256) and call official merchant endpoints

    def push_update(self, external_id: Optional[str], update: AdUpdate) -> None:
        # TODO: Implement actual API calls when merchant endpoints and permissions are provided
        # For now, no-op
        return


def get_provider():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    if api_key and api_secret:
        return BinanceMerchantProvider(api_key, api_secret)
    return MockProvider()
