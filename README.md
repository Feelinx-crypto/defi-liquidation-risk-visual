# defi-liquidation-risk-visual
A data-driven visualization and analysis of liquidation risks in DeFi lending protocols such as Aave and Compound.
## 📂 Project Structure

This repository contains modularized components for analyzing and visualizing liquidation risks in DeFi lending protocols (Aave, Compound, etc.).

- **data/** — Contains raw and processed datasets  
  - `aave_liqs_ethscan.csv`: liquidation events fetched from Etherscan  
  - `eth_daily_price.csv`: daily ETH price data from Binance  
  - `eth_ret_vs_liq.csv`: merged dataset of returns and liquidation counts  
  - `stress_curve.csv`: results from stress testing analysis  

- **src/** — Core Python modules  
  - `api.py`: Etherscan and RPC data fetching utilities  
  - `prices.py`: Binance API price loader  
  - `features.py`: feature engineering and daily liquidation aggregation ￼ 
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
pip install -r requirements.txt
cd notebooks/
jupyter notebook

<img width="624" height="50" alt="image" src="https://github.com/user-attachments/assets/a753e84f-c547-47b9-9938-00f8c133ee7d" />
