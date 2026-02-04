"""
API utilities for retrieving Aave V3 liquidation events across multiple chains.

This module wraps the Etherscan V2 API. It can query the latest block height,
fetch logs in chunks and assemble the results into a pandas DataFrame.
Configuration values such as pool addresses, start blocks and API domains
come from `src.config`. Functions here remain agnostic to the specific chain
and asset.

Chain pool addresses and start blocks originate from the Aave cross-chain
data infrastructure [oai_citation:0‡arxiv.org](https://arxiv.org/html/2512.11363v1#:~:text=Table%202%3A%20Blockchain%20Configurations%20for,70%2C593%2C220%20Base%200xA238Dd80C259a72e81d7e4664a9801593F98d1c5%202%2C357%2C200%2037%2C067%2C658), and the LiquidationCall event signature
is confirmed in Aave documentation [oai_citation:1‡quicknode.com](https://www.quicknode.com/sample-app-library/ethereum-aave-liquidation-tracker#:~:text=The%20Pool,deposits%2C%20borrowing%2C%20repayments%2C%20and%20liquidations).
"""

from __future__ import annotations

import os
import time
from typing import List, Dict, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

from . import config

# Load API key from .env or environment
load_dotenv()
API_KEY = os.getenv("ETHERSCAN_API_KEY")


def _require_api_key() -> str:
    """Ensure an API key is available."""
    if not API_KEY:
        raise RuntimeError(
            "Missing ETHERSCAN_API_KEY in environment or .env file. "
            "Please set ETHERSCAN_API_KEY to a valid Etherscan token."
        )
    return API_KEY


def get_latest_block(chain_name: str) -> int:
    """
    Retrieve the most recent block height for a specified chain.

    Args:
        chain_name: Key identifying the chain (e.g. "ethereum").
    Returns:
        Integer representing the current block height.
    """
    _require_api_key()
    cfg = config.CHAINS[chain_name]
    url = f"{cfg.api_base}/api"
    params = {
        "chainid": cfg.chain_id,
        "module": "proxy",
        "action": "eth_blockNumber",
        "apikey": API_KEY,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return int(data["result"], 16)


def get_logs(
    topic0: str,
    address: str,
    start_block: int,
    end_block: int,
    chain_name: str,
    max_retry: int = 3,
    sleep_sec: float = 1.0,
) -> List[Dict]:
    """
    Fetch raw logs matching a topic within a block range on a given chain.

    Args:
        topic0: Event signature hash to filter on.
        address: Contract address emitting the events.
        start_block: Starting block (inclusive).
        end_block: Ending block (inclusive).
        chain_name: Chain key from `config.CHAINS`.
        max_retry: Maximum number of retries on failure.
        sleep_sec: Pause duration between retries.
    Returns:
        A list of log entries as dictionaries.
    """
    _require_api_key()
    cfg = config.CHAINS[chain_name]
    url = f"{cfg.api_base}/api"
    params = {
        "chainid": cfg.chain_id,
        "module": "logs",
        "action": "getLogs",
        "fromBlock": start_block,
        "toBlock": end_block,
        "topic0": topic0,
        "address": address,
        "apikey": API_KEY,
    }
    for _ in range(max_retry):
        r = requests.get(url, params=params, timeout=60)
        if r.status_code == 200:
            js = r.json()
            if js.get("status") == "1":
                return js.get("result", [])
            # Some explorers return status "0" and message "No records found"
            if js.get("status") == "0" and js.get("message") == "No records found":
                return []
        time.sleep(sleep_sec)
    return []


def chunked_get_logs(
    topic0: str,
    address: str,
    start_block: int,
    end_block: int,
    chain_name: str,
    step: int = 5_000,
) -> List[Dict]:
    """
    Retrieve logs by splitting a large block range into smaller intervals.

    Args:
        topic0: Event signature topic.
        address: Contract address emitting the events.
        start_block: Starting block number.
        end_block: Ending block number.
        chain_name: Chain key from `config.CHAINS`.
        step: Number of blocks per request.
    Returns:
        A list containing all log entries across the specified range.
    """
    out: List[Dict] = []
    cur = start_block
    while cur <= end_block:
        to_blk = min(cur + step - 1, end_block)
        out.extend(
            get_logs(
                topic0=topic0,
                address=address,
                start_block=cur,
                end_block=to_blk,
                chain_name=chain_name,
            )
        )
        cur = to_blk + 1
        time.sleep(0.2)
    return out


def extract_liquidations(
    chain_name: str,
    asset: str,
    end_block: Optional[int] = None,
    step: int = 5_000,
) -> pd.DataFrame:
    """
    Extract LiquidationCall events for a specified chain and asset.

    Args:
        chain_name: Name of the chain defined in `config.CHAINS`.
        asset: Asset symbol (for reference in the output).
        end_block: Optionally specify an explicit end block. If None,
                   the latest block height is queried.
        step: Block range for each logs query.
    Returns:
        DataFrame containing columns: chain, asset, blockNumber, timeStamp,
        transactionHash, timestamp.
    """
    if end_block is None:
        end_block = get_latest_block(chain_name)
    cfg = config.CHAINS[chain_name]
    logs = chunked_get_logs(
        topic0=config.LIQUIDATION_CALL_TOPIC,
        address=cfg.pool_address,
        start_block=cfg.start_block,
        end_block=end_block,
        chain_name=chain_name,
        step=step,
    )
    if not logs:
        return pd.DataFrame(
            columns=["chain", "asset", "blockNumber", "timeStamp", "transactionHash", "timestamp"]
        )
    df = pd.DataFrame(logs)
    # Normalise timestamp field: Etherscan may use "timeStamp" or "timestamp".
    if "timeStamp" not in df.columns and "timestamp" in df.columns:
        df["timeStamp"] = df["timestamp"]
    # Keep only required fields
    keep_cols = ["blockNumber", "timeStamp", "transactionHash"]
    df = df.loc[:, [c for c in keep_cols if c in df.columns]].copy()
    # Add chain and asset labels
    df["chain"] = chain_name
    df["asset"] = asset
    # Convert hex strings to integers where appropriate
    def _hex_to_int(x):
        if isinstance(x, str) and x.startswith("0x"):
            return int(x, 16)
        try:
            return int(x)
        except Exception:
            return None
    df["blockNumber"] = df["blockNumber"].apply(_hex_to_int)
    df["timeStamp"] = df["timeStamp"].apply(_hex_to_int)
    # Convert to pandas datetime
    df["timestamp"] = pd.to_datetime(df["timeStamp"], unit="s", utc=True)
    return df