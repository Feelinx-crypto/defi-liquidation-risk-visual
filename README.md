# DeFi Liquidation Risk Visualization

A data-driven analysis and visualization system for Aave V3 liquidation events across multiple blockchain networks, with a focus on Ethereum mainnet.

## Overview

DeFi lending protocols allow users to borrow assets against cryptocurrency collateral, but positions face liquidation when collateral values drop below protocol thresholds. This project provides:

- **Multi-chain data extraction** of Aave V3 `LiquidationCall` events via the Etherscan API
- **Price data integration** from Binance (daily ETH/USDT candles)
- **Risk metric computation** including daily liquidation counts, return-liquidation correlation, and asymmetry analysis
- **Kernel regression stress testing** estimating expected liquidation volumes under hypothetical price shocks
- **Publication-quality visualizations** (Matplotlib) and exploratory Jupyter notebooks

## Architecture

```
Etherscan API ──► src/api.py ──► src/extract_multi_chain.py
                                        │
Binance API ───► src/prices.py          │
                      │                 ▼
                      └──────► src/features.py
                                   │
                          ┌────────┴────────┐
                          ▼                 ▼
                    src/stress.py     notebooks/
                    (Stress Curves)   (EDA + Analysis)
```

## Key Findings (7,832 liquidation events, Jan–Oct 2025)

- **2.4:1 asymmetry**: Down days average 45.8 liquidations vs. 18.8 on up days
- **Nonlinear stress response**: A 10% daily ETH drop associates with ~84 liquidations (IQR: 80–88); estimates beyond -15% are data-sparse (N_eff < 2)
- **Temporal clustering**: Liquidation spikes align with periods of elevated ETH volatility
- **Critical threshold**: The -5% daily return mark is an inflection point for accelerating liquidation activity

## Project Structure

```
├── src/
│   ├── api.py                 # Etherscan API wrapper (log fetching, block queries)
│   ├── config.py              # Chain/asset configuration (addresses, start blocks)
│   ├── extract_multi_chain.py # Multi-chain liquidation event extraction
│   ├── features.py            # Feature engineering (daily aggregation, returns)
│   ├── prices.py              # Binance price data fetching
│   └── stress.py              # Kernel regression, ensemble model, SHAP, anomaly detection
├── notebooks/
│   ├── 01_quick_eda.ipynb     # Exploratory data analysis
│   └── 02_stress_test.ipynb   # Stress-test analysis
├── data/
│   ├── aave_liqs_ethscan.csv  # Raw liquidation events (7,832 events)
│   ├── eth_ret_vs_liq.csv     # Merged daily returns + liquidation counts
│   ├── stress_curve_1d.csv    # 1-day stress curve output
│   └── stress_curve_7d.csv    # 7-day stress curve output
├── figs/                      # Generated figures (PNG + PDF)
├── gen_paper_figs.py          # Script to generate all paper figures
├── .github/workflows/
│   └── update.yml             # Automated data refresh (GitHub Actions)
├── Makefile
└── requirements.txt
```

## Installation

```bash
git clone https://github.com/Feelinx-crypto/defi-liquidation-risk-visual.git
cd defi-liquidation-risk-visual
pip install -r requirements.txt
```

## Usage

### Offline Reproduction (no API keys needed)

Pre-collected data is included under `data/`. You can regenerate all figures
and run the stress-testing pipeline without any API keys:

```bash
pip install -r requirements.txt
python gen_paper_figs.py          # Regenerates all paper figures and refreshes stress_curve_*.csv
python scripts/export_paper_latex.py  # Writes LaTeX snippets used by template_extracted/main.tex
python -c "
from src.stress import train_ensemble, compute_shap, detect_anomalies
import pandas as pd
merged = pd.read_csv('data/eth_ret_vs_liq.csv')
merged['date'] = pd.to_datetime(merged['date'])
models = train_ensemble(merged)
print('RF MAE:', round(models['mae_rf'], 2))
print('GB MAE:', round(models['mae_gb'], 2))
print(compute_shap(models))
print(detect_anomalies(merged))
"
```

Expected outputs:

- Figures: `figs/fig1_daily_liqs.pdf` … `figs/fig6_liq_distribution.pdf`
- Stress curves: `data/stress_curve_1d.csv`, `data/stress_curve_7d.csv`
- Report snippets: `../template_extracted/auto_numbers.tex`, `../template_extracted/auto_summary_table.tex`, `../template_extracted/auto_stress_table.tex`, `../template_extracted/auto_model_table.tex`

### Refresh Data (requires API keys)
```bash
export ETHERSCAN_API_KEY=your_key   # Required for on-chain data
make update                          # Re-extract liquidation events and price data
```

### Generate Paper Figures
```bash
python gen_paper_figs.py   # Outputs PDF + PNG to figs/
```

### Run Notebooks
```bash
jupyter notebook notebooks/01_quick_eda.ipynb
jupyter notebook notebooks/02_stress_test.ipynb
```

## Methodology

1. **Data Extraction**: Queries Aave V3 `LiquidationCall` event logs from Ethereum via the Etherscan API (`src/api.py` + `src/extract_multi_chain.py`). Supports Ethereum, Polygon, Arbitrum, and Optimism.

2. **Feature Engineering**: Aggregates events into daily counts, fetches ETH/USDT closing prices from Binance, computes simple percentage returns, and merges into a unified dataset (`src/features.py` + `src/prices.py`).

3. **Stress Testing**: Uses a Nadaraya-Watson kernel regression estimator to model the conditional expectation of liquidation counts given hypothetical ETH price shocks, with confidence bands and effective sample counts (`src/stress.py`).

4. **Visualization**: Publication-quality Matplotlib figures for the research paper; Jupyter notebooks for interactive exploration.

## Data Sources

- **Etherscan API**: On-chain Aave V3 liquidation event logs
- **Binance API**: Daily ETH/USDT candlestick data

## Tech Stack

- Python 3.10+
- pandas / NumPy / SciPy (data processing & statistics)
- Matplotlib / Plotly (visualization)
- Jupyter (interactive analysis)
- GitHub Actions (automated data refresh)

## Academic Context

This project was developed as part of a Duke Kunshan University Signature Work project, investigating liquidation risk dynamics in decentralized finance through data visualization. The accompanying research paper analyzes 7,832 liquidation events and demonstrates the nonlinear, asymmetric relationship between ETH price movements and Aave V3 liquidation activity.

## License

MIT
