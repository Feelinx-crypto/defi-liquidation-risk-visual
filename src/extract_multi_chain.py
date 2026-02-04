"""
Script for batch extraction of Aave V3 liquidation events across multiple chains and assets.

This utility loops over all configured chains and assets, invokes the
`extract_liquidations` function for each pair and writes both raw
event records and aggregated daily statistics to CSV files.  It also
fetches daily price data and merges it with the liquidation counts to
facilitate subsequent stress testing.

Usage:

    python -m src.extract_multi_chain

The output CSVs will be stored under the `data` directory in the
repository root.  Filenames follow the pattern:

    aave_v3_{chain}_{asset}_events_{YYYYMMDD}.csv
    aave_v3_{chain}_{asset}_daily_{YYYYMMDD}.csv

where `YYYYMMDD` corresponds to the current UTC date.  These files
include metadata such as the chain and asset identifiers and are
timestamped to support reproducibility.
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path

from . import config
from .api import extract_liquidations
from .features import liq_daily_count, merge_ret_vs_liq
from .prices import binance_daily


def main() -> None:
    # Determine output directory relative to the repository root
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.datetime.utcnow().strftime("%Y%m%d")

    for chain_name in config.CHAINS.keys():
        for asset_name in config.ASSETS.keys():
            # Extract raw LiquidationCall events
            print(f"Extracting liquidation events for chain={chain_name}, asset={asset_name}")
            try:
                logs_df = extract_liquidations(chain_name, asset_name)
            except Exception as e:
                print(f"Error extracting events for {chain_name}-{asset_name}: {e}")
                continue
            # Save raw events to CSV
            events_fname = f"aave_v3_{chain_name}_{asset_name}_events_{date_str}.csv"
            events_path = data_dir / events_fname
            logs_df.to_csv(events_path, index=False)
            # Compute daily liquidation counts
            daily_liq = liq_daily_count(logs_df)
            # Fetch daily price data
            try:
                price_df = binance_daily(asset_name)
            except Exception as e:
                print(f"Error fetching price for {asset_name}: {e}")
                price_df = None
            if price_df is not None and not price_df.empty:
                merged = merge_ret_vs_liq(price_df, daily_liq)
                daily_fname = f"aave_v3_{chain_name}_{asset_name}_daily_{date_str}.csv"
                daily_path = data_dir / daily_fname
                merged.to_csv(daily_path, index=False)
            else:
                # If no price data is available, still save the daily liquidation counts
                daily_fname = f"aave_v3_{chain_name}_{asset_name}_liq_counts_{date_str}.csv"
                daily_path = data_dir / daily_fname
                daily_liq.to_csv(daily_path, index=False)


if __name__ == "__main__":
    main()