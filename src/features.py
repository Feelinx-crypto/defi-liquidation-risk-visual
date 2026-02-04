"""
Feature engineering utilities for liquidation risk analysis.

These functions provide minimal aggregations and merges needed to link
liquidation events with market returns. They operate on the normalised
DataFrame output from `api.extract_liquidations` and the price DataFrame
produced by `prices.binance_daily`.
"""

from __future__ import annotations
import pandas as pd

def liq_daily_count(df_logs: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily liquidation counts grouped by chain and asset.

    Args:
        df_logs: DataFrame of raw liquidation events. Must contain
                 columns: 'timestamp' (UTC datetime), 'chain', 'asset'.

    Returns:
        DataFrame with columns: 'date', 'chain', 'asset', 'liq_cnt'.
    """
    d = df_logs.copy()
    d["date"] = pd.to_datetime(d["timestamp"]).dt.tz_convert("UTC").dt.date
    grp = d.groupby(["date", "chain", "asset"]).size().reset_index(name="liq_cnt")
    return grp

def merge_ret_vs_liq(daily_px: pd.DataFrame, daily_liq: pd.DataFrame) -> pd.DataFrame:
    """
    Join daily return data with liquidation counts.

    The function performs an inner join on the 'date' column. The
    resulting DataFrame retains 'chain' and 'asset' fields from the
    liquidation counts and adds 'price' and 'ret' from the price data.

    Args:
        daily_px: Daily price and return series for a given asset.
        daily_liq: Daily liquidation counts across one or more chains.

    Returns:
        DataFrame with columns: 'date', 'chain', 'asset', 'liq_cnt',
        'price', and 'ret'.
    """
    px = daily_px.copy()
    px["date"] = pd.to_datetime(px["date"]).dt.date
    liq = daily_liq.copy()
    liq["date"] = pd.to_datetime(liq["date"]).dt.date
    m = pd.merge(liq, px[["date", "price", "ret"]], on="date", how="inner").dropna()
    m["ret"] = m["ret"].astype(float)
    m["liq_cnt"] = m["liq_cnt"].astype(int)
    return m