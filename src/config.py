"""
Configuration module for multi-chain and multi-asset settings.

This module centralises the information required to extract data across
multiple blockchains and assets. It defines dataclasses for chains and
assets, stores the LiquidationCall event signature for Aave V3 and
provides dictionaries of supported chains and assets. Downstream
functions can import this module to parameterise API calls and data
processing logic.

Chain addresses and start blocks come from the cross-chain Aave V3 data
infrastructure paper (arXiv:2512.11363). The event signature is
confirmed by Aave’s official documentation.
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
    # Per-chain token addresses for filtering liquidation events.
    # Keys are chain names from CHAINS; values are ERC-20 contract addresses.
    # If a chain is missing, events on that chain are NOT filtered by asset.
    token_addresses: Optional[Dict[str, str]] = None

# Topic 0 for the Aave V3 LiquidationCall event.
LIQUIDATION_CALL_TOPIC = (
    "0xe413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286"
)

# Chain configurations (address and start block from Aave V3 cross-chain research).
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
# Token addresses are per-chain mappings used to filter LiquidationCall events
# by collateralAsset (topic1) or debtAsset (topic2).
# If a chain key is absent, events on that chain are returned unfiltered.
ASSETS: Dict[str, AssetConfig] = {
    "ETH": AssetConfig(
        symbol="ETH", pair="ETHUSDT",
        token_addresses={
            "ethereum":  "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
            "optimism":  "0x4200000000000000000000000000000000000006",  # WETH
            "arbitrum":  "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH
            "polygon":   "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",  # WETH
            "avalanche": "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB",  # WETH.e
            "base":      "0x4200000000000000000000000000000000000006",  # WETH
        },
    ),
    "BTC": AssetConfig(
        symbol="BTC", pair="BTCUSDT",
        token_addresses={
            "ethereum":  "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
            "optimism":  "0x68f180fcCe6836688e9084f035309E29Bf0A2095",  # WBTC
            "arbitrum":  "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",  # WBTC
            "polygon":   "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",  # WBTC
            "avalanche": "0x50b7545627a5162F82A992c33b87aDc75187B218",  # WBTC.e
        },
    ),
    "USDC": AssetConfig(
        symbol="USDC", pair="USDCUSDT", fallback_price=1.0,
        token_addresses={
            "ethereum":  "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "optimism":  "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",  # native USDC
            "arbitrum":  "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # native USDC
            "polygon":   "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",  # native USDC
            "avalanche": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",  # native USDC
            "base":      "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # native USDC
        },
    ),
    "USDT": AssetConfig(
        symbol="USDT", pair=None, fallback_price=1.0,
        token_addresses={
            "ethereum":  "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "optimism":  "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
            "arbitrum":  "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
            "polygon":   "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
            "avalanche": "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",  # USDt
        },
    ),
}