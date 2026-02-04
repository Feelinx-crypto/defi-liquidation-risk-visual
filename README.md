# defi-liquidation-risk-visual

A data-driven visualization and analysis of liquidation risks in DeFi lending protocols such as Aave and Compound.

---

## 📂 Project Structure

This repository contains modularized components for analyzing and visualising liquidation risks in DeFi lending protocols. The project has been extended to support multiple assets (ETH, BTC, USDC, USDT) and multiple chains (Ethereum, Optimism, Arbitrum, Polygon, Avalanche and Base) by introducing a configuration layer and automated extraction scripts.

- **data/** — Contains raw and processed datasets
  - `aave_liqs_ethscan.csv`: liquidation events fetched from Etherscan
  - `eth_daily_price.csv`: daily ETH price data from Binance
  - `eth_ret_vs_liq.csv`: merged dataset of returns and liquidation counts
  - `stress_curve.csv`: results from stress testing analysis

- **src/** — Core Python modules
  - `config.py`: central definitions for chain parameters, pool addresses and supported assets
  - `api.py`: multichain Etherscan data fetching utilities with dynamic batching
  - `prices.py`: Binance API price loader with fallback support for stablecoins
  - `features.py`: feature engineering, grouping by date/chain/asset and merging returns vs liquidations
  - `extract_multi_chain.py`: convenience script to extract events, compute daily counts and save results across all configured chains and assets
  - `stress.py`: kernel-based stress testing functions

- **notebooks/** — Jupyter Notebooks for analysis and visualization
  - `01_quick_eda.ipynb`: exploratory data analysis and visualization
  - `02_stress_test.ipynb`: stress testing and kernel smoothing results

- **figs/** — Figures and generated visualizations
  - Includes all heatmaps, histograms, scatterplots, and stress curves

- **deliverables/** — Final reports, documentation, and presentation slides

- **docs/** — Supporting research notes and methodological explanations

---

## 🚀 How to Run

```bash
# install the required packages
pip install -r requirements.txt

# export your Etherscan API key (required for on‑chain data)
export ETHERSCAN_API_KEY=<your-etherscan-api-key>

# run the extraction script to fetch events and prices across all chains and assets
python -m src.extract_multi_chain

# optional: explore the notebooks for EDA and stress testing
jupyter notebook notebooks/01_quick_eda.ipynb


## 🕒 Automated Updates 

This repository can automatically refresh its data using **GitHub Actions**. A sample workflow (`.github/workflows/update.yml`) is provided that triggers once per day. To enable it:

1. **Create a Secret:** Create a GitHub Actions secret named `ETHERSCAN_API_KEY` in your repository settings. Store your personal Etherscan API token here so it is not exposed in the code.
2. **Workflow File:** Ensure the file `.github/workflows/update.yml` exists in your repository.

### Example Workflow (`.github/workflows/update.yml`)

```yaml      
name: Update Aave Data

# run every day at 00:00 UTC and allow manual triggering
on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    env:
      ETHERSCAN_API_KEY: ${{ secrets.ETHERSCAN_API_KEY }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run multi-chain extraction
        run: python -m src.extract_multi_chain

      - name: Commit and push updated data
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data
          git commit -m "Automated data update" || echo "No changes to commit"
          git push
```

> **Note:** Placing this file in the `.github/workflows` directory and configuring the `ETHERSCAN_API_KEY` secret will ensure your dataset stays fresh without manual intervention.
