from __future__ import annotations
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Network
    timeout_seconds: float = Field(20.0, description="HTTP timeout")
    proxy: Optional[str] = Field(None, description="HTTP(S) proxy URL if needed")

    # Binance P2P settings
    asset: str = Field("USDT", description="Crypto asset to query")
    fiat: str = Field("BRL", description="Fiat currency, BRL for Brazil")
    rows_per_page: int = Field(50, description="Rows per page for Binance API")
    max_pages: int = Field(20, description="Maximum pages to fetch per side")

    # Storage
    db_path: str = Field("/workspace/p2p_merchant.db", description="SQLite database path")

    # CLI
    user_agent: str = Field(
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        description="User-Agent header for Binance P2P endpoints",
    )

    class Config:
        env_prefix = "P2P_"
        env_file = ".env"


settings = Settings()  # type: ignore
