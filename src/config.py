"""
Configuration module for multi-chain and multi-asset settings.

This module centralises the information required to extract data across
multiple blockchains and assets. It defines dataclasses for chains and
assets, stores the LiquidationCall event signature for Aave V3 and
provides dictionaries of supported chains and assets. Downstream
functions can import this module to parameterise API calls and data
processing logic.

Chain addresses and start blocks come from the cross‑chain Aave V3 data
infrastructure paper [oai_citation:0‡arxiv.org](https://arxiv.org/html/2512.11363v1#:~:text=Table%202%3A%20Blockchain%20Configurations%20for,70%2C593%2C220%20Base%200xA238Dd80C259a72e81d7e4664a9801593F98d1c5%202%2C357%2C200%2037%2C067%2C658).  The event signature is
confirmed by Aave’s official documentation [oai_citation:1‡quicknode.com](https://www.quicknode.com/sample-app-library/ethereum-aave-liquidation-tracker#:~:text=The%20Pool,deposits%2C%20borrowing%2C%20repayments%2C%20and%20liquidations).
"""

from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class ChainConfig:
    name: str                # Human‑readable name (e.g. "ethereum")
    pool_address: str        # Aave V3 pool contract address on this chain
    start_block: int         # Block height at which the pool was deployed
    api_base: str            # Base URL of the Etherscan‑compatible API (no trailing /api)
    chain_id: int            # Chain ID (for reference)

@dataclass
class AssetConfig:
    symbol: str
    pair: Optional[str]      # Binance trading pair (e.g. "ETHUSDT"); None if not applicable
    fallback_price: Optional[float] = None  # Fallback price for stablecoins

# Topic 0 for the Aave V3 LiquidationCall event [oai_citation:2‡quicknode.com](https://www.quicknode.com/sample-app-library/ethereum-aave-liquidation-tracker#:~:text=The%20Pool,deposits%2C%20borrowing%2C%20repayments%2C%20and%20liquidations).
LIQUIDATION_CALL_TOPIC = (
    "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
)

# Chain configurations (address and start block from Aave V3 cross-chain research [oai_citation:3‡arxiv.org](https://arxiv.org/html/2512.11363v1#:~:text=Table%202%3A%20Blockchain%20Configurations%20for,70%2C593%2C220%20Base%200xA238Dd80C259a72e81d7e4664a9801593F98d1c5%202%2C357%2C200%2037%2C067%2C658)).
CHAINS: Dict[str, ChainConfig] = {
    "ethereum": ChainConfig(
        name="ethereum",
        pool_address="0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        start_block=16_291_127,
        api_base="https://api.etherscan.io/v2",
        chain_id=1,
    ),
    "optimism": ChainConfig(
        name="optimism",
        pool_address="0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        start_block=4_365_693,
        api_base="https://api-optimistic.etherscan.io/v2",
        chain_id=10,
    ),
    "arbitrum": ChainConfig(
        name="arbitrum",
        pool_address="0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        start_block=7_740_000,
        api_base="https://api.arbiscan.io/v2",
        chain_id=42_161,
    ),
    "polygon": ChainConfig(
        name="polygon",
        pool_address="0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        start_block=25_825_996,
        api_base="https://api.polygonscan.com/v2",
        chain_id=137,
    ),
    "avalanche": ChainConfig(
        name="avalanche",
        pool_address="0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        start_block=11_970_000,
        api_base="https://api.snowtrace.io/v2",
        chain_id=43_114,
    ),
    "base": ChainConfig(
        name="base",
        pool_address="0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
        start_block=2_357_200,
        api_base="https://api.basescan.org/v2",
        chain_id=8_453,
    ),
}

# Supported assets; stablecoins have fallback prices of 1.0.
ASSETS: Dict[str, AssetConfig] = {
    "ETH": AssetConfig(symbol="ETH", pair="ETHUSDT"),
    "BTC": AssetConfig(symbol="BTC", pair="BTCUSDT"),
    "USDC": AssetConfig(symbol="USDC", pair="USDCUSDT", fallback_price=1.0),
    "USDT": AssetConfig(symbol="USDT", pair=None, fallback_price=1.0),
}