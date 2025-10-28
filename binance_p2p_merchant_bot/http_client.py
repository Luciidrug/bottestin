from __future__ import annotations
import httpx
from typing import Any, Dict, Optional
from .config import settings


class HttpClient:
    def __init__(self, base_headers: Optional[Dict[str, str]] = None) -> None:
        self.base_headers = base_headers or {}
        self._client = httpx.Client(
            timeout=settings.timeout_seconds,
            proxies=settings.proxy,
            headers=self.base_headers,
        )

    def post_json(self, url: str, json: Dict[str, Any]) -> Dict[str, Any]:
        response = self._client.post(url, json=json)
        response.raise_for_status()
        return response.json()

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()


def make_default_client() -> HttpClient:
    headers = {
        "content-type": "application/json",
        "clienttype": "web",
        "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8",
        "user-agent": settings.user_agent,
        "referer": "https://p2p.binance.com/pt-BR",
    }
    return HttpClient(headers)
