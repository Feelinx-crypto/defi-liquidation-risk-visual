"""
Price utilities for fetching daily market data across multiple assets.

The primary source of price data is Binance's public API.  For each
supported asset, a trading pair is defined in ``config.ASSETS``.  If
the pair is unavailable or the call fails, a fallback price may be
used (e.g. 1.0 for stablecoins).
"""

from __future__ import annotations

import datetime
from typing import Optional

import pandas as pd
import requests

from . import config

# List of Binance API endpoints. The first that responds successfully will be used.
_BINANCE_KLINES_ENDPOINTS = [
    "https://api.binance.com/api/v3/klines",
    "https://data-api.binance.vision/api/v3/klines",
]

def _fetch_binance_klines(pair: str, limit: int = 1000) -> pd.DataFrame:
    """
    Fetch daily OHLCV data for a given trading pair from Binance.

    Args:
        pair: Trading pair symbol, e.g. "ETHUSDT".
        limit: Number of days of data to retrieve (max 1000).

    Returns:
        A DataFrame with columns ``date``, ``price`` and ``ret``.

    Raises:
        RuntimeError: If the Binance API requests fail.
    """
    for url in _BINANCE_KLINES_ENDPOINTS:
        try:
            r = requests.get(
                url,
                params={"symbol": pair, "interval": "1d", "limit": limit},
                timeout=30,
            )
            if r.status_code == 200:
                k = r.json()
                df = pd.DataFrame(
                    k,
                    columns=[
                        "open_time",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                        "close_time",
                        "quote_asset_volume",
                        "num_trades",
                        "taker_buy_base_volume",
                        "taker_buy_quote_volume",
                        "ignore",
                    ],
                )
                out = pd.DataFrame(
                    {
                        "date": pd.to_datetime(df["close_time"], unit="ms", utc=True).dt.date,
                        "price": df["close"].astype(float),
                    }
                )
                out["ret"] = out["price"].pct_change()
                return out
        except Exception:
            continue
    raise RuntimeError(f"Binance daily price fetch failed for pair {pair}")

def binance_daily(asset: str, limit: int = 1000) -> pd.DataFrame:
    """
    Retrieve daily price and return series for a specified asset.

    The function consults the configuration in ``config.ASSETS`` to determine
    the Binance trading pair. If a pair is defined, it attempts to fetch data via
    the Binance API. Should the API call fail or no pair be defined, a fallback
    constant price is used if specified in the configuration.

    Args:
        asset: Asset symbol (case-insensitive) matching keys in ``config.ASSETS``.
        limit: Maximum number of daily observations to retrieve (up to 1000).

    Returns:
        A DataFrame with columns ``date``, ``price`` and ``ret``.
    """
    a_key = asset.upper()
    if a_key not in config.ASSETS:
        raise ValueError(f"Unsupported asset: {asset}")
    cfg = config.ASSETS[a_key]
    # Attempt to fetch from Binance if a trading pair is defined
    if cfg.pair:
        try:
            out = _fetch_binance_klines(cfg.pair, limit=limit)
            return out
        except Exception:
            # Fallback to constant price if defined
            if cfg.fallback_price is not None:
                price = cfg.fallback_price
                today = datetime.date.today()
                df = pd.DataFrame({"date": [today], "price": [price]})
                df["ret"] = df["price"].pct_change()
                return df
            raise
    # If no pair is defined, attempt fallback
    if cfg.fallback_price is not None:
        price = cfg.fallback_price
        today = datetime.date.today()
        df = pd.DataFrame({"date": [today], "price": [price]})
        df["ret"] = df["price"].pct_change()
        return df
    else:
        raise RuntimeError(f"No trading pair or fallback price defined for asset {asset}")