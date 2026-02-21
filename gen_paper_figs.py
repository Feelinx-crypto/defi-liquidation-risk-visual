"""Generate publication-quality figures for the SW paper."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LogNorm
import os, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.stress import kernel_curve

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})

DATA = "data"
FIGS = "figs"
os.makedirs(FIGS, exist_ok=True)

# Load data
liqs = pd.read_csv(f"{DATA}/aave_liqs_ethscan.csv", parse_dates=["timestamp"])
merged = pd.read_csv(f"{DATA}/eth_ret_vs_liq.csv")
merged["date"] = pd.to_datetime(merged["date"])
merged["ret"] = merged["ret"].astype(float)
merged["liq_cnt"] = merged["liq_cnt"].astype(int)

print(f"Liquidation events: {len(liqs)}")
print(f"Merged daily rows: {len(merged)}")
print(f"Date range: {merged['date'].min()} to {merged['date'].max()}")

# ── Fig 1: Daily Liquidation Time Series ──
daily = liqs.groupby(liqs["timestamp"].dt.date).size()
daily.index = pd.to_datetime(daily.index)

fig, ax = plt.subplots(figsize=(8, 3.5))
ax.fill_between(daily.index, daily.values, alpha=0.3, color='#2196F3')
ax.plot(daily.index, daily.values, lw=0.8, color='#1565C0')
ax.set_xlabel("Date")
ax.set_ylabel("Daily Liquidation Count")
ax.set_title("Aave V3 Liquidation Events on Ethereum (Jan–Oct 2025)")
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator())
fig.autofmt_xdate()
plt.savefig(f"{FIGS}/fig1_daily_liqs.pdf")
plt.savefig(f"{FIGS}/fig1_daily_liqs.png")
plt.close()
print("Saved fig1")

# ── Fig 2: Scatter — ETH Return vs Liquidation Count ──
fig, ax = plt.subplots(figsize=(6, 4.5))
sc = ax.scatter(
    merged["ret"] * 100, merged["liq_cnt"],
    s=15, alpha=0.6, c=merged["liq_cnt"],
    cmap='YlOrRd', edgecolors='none'
)
ax.axvline(0, ls="--", lw=0.8, color="gray", alpha=0.6)
ax.set_xlabel("ETH Daily Return (%)")
ax.set_ylabel("Liquidation Count")
ax.set_title("ETH Daily Return vs. Aave Liquidations")
ax.set_xlim(-15, 15)
ax.set_ylim(0, merged["liq_cnt"].quantile(0.98) * 1.15)
plt.colorbar(sc, label="Liquidation Count", shrink=0.8)
plt.savefig(f"{FIGS}/fig2_ret_vs_liq.pdf")
plt.savefig(f"{FIGS}/fig2_ret_vs_liq.png")
plt.close()
print("Saved fig2")

# ── Fig 3: 2D Histogram Heatmap ──
fig, ax = plt.subplots(figsize=(6, 4.5))
h = ax.hist2d(
    merged["ret"] * 100, merged["liq_cnt"],
    bins=[50, 50],
    range=[[-15, 15], [0, merged["liq_cnt"].quantile(0.98)]],
    cmap="plasma",
    norm=LogNorm(vmin=1, vmax=50)
)
plt.colorbar(h[3], label="Frequency (log scale)", shrink=0.8)
ax.axvline(0, ls="--", lw=0.8, color="white", alpha=0.7)
ax.set_xlabel("ETH Daily Return (%)")
ax.set_ylabel("Liquidation Count")
ax.set_title("Joint Distribution of Returns and Liquidations")
plt.savefig(f"{FIGS}/fig3_density_heatmap.pdf")
plt.savefig(f"{FIGS}/fig3_density_heatmap.png")
plt.close()
print("Saved fig3")

# ── Fig 4: Liquidation Asymmetry (Up vs Down days) ──
m = merged.copy()
m["side"] = np.where(m["ret"] < 0, "Down Days", "Up Days")
summary = m.groupby("side")["liq_cnt"].agg(["count","sum","mean","median"])
summary.columns = ["Days", "Total Liqs", "Mean", "Median"]

fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))
colors = ['#E53935', '#43A047']

axes[0].bar(summary.index, summary["Mean"], color=colors, width=0.5)
axes[0].set_ylabel("Mean Daily Liquidations")
axes[0].set_title("Average Liquidations")
for i, v in enumerate(summary["Mean"]):
    axes[0].text(i, v + 1, f"{v:.1f}", ha='center', fontsize=10)

axes[1].bar(summary.index, summary["Total Liqs"], color=colors, width=0.5)
axes[1].set_ylabel("Total Liquidation Events")
axes[1].set_title("Cumulative Liquidations")
for i, v in enumerate(summary["Total Liqs"]):
    axes[1].text(i, v + 50, f"{v:,}", ha='center', fontsize=10)

plt.suptitle("Liquidation Asymmetry: Down Days vs. Up Days", y=1.02)
plt.tight_layout()
plt.savefig(f"{FIGS}/fig4_asymmetry.pdf")
plt.savefig(f"{FIGS}/fig4_asymmetry.png")
plt.close()
print("Saved fig4")

# ── Fig 5: Stress Curve (Kernel Regression) ──
m2 = merged.dropna(subset=["ret", "liq_cnt"]).copy()
m2 = m2.sort_values("date")
m2["ret7"] = m2["ret"].rolling(7, min_periods=3).sum()
m2 = m2.dropna(subset=["ret7"]).reset_index(drop=True)

grid = np.arange(-0.30, -0.04, 0.005)
curve1 = kernel_curve(m2["ret"], m2["liq_cnt"], grid, sigma=0.012)
curve7 = kernel_curve(m2["ret7"], m2["liq_cnt"], grid, sigma=0.020)

fig, ax = plt.subplots(figsize=(7.5, 4.5))
# 1-day shock
mask1 = curve1["est"].notna()
ax.plot(curve1.loc[mask1, "shock"]*100, curve1.loc[mask1, "est"],
        marker="o", ms=4, lw=2, color='#1565C0', label="1-Day Shock")
ax.fill_between(curve1.loc[mask1, "shock"]*100,
                curve1.loc[mask1, "p25"], curve1.loc[mask1, "p75"],
                alpha=0.15, color='#1565C0')
# 7-day cumulative shock
mask7 = curve7["est"].notna()
ax.plot(curve7.loc[mask7, "shock"]*100, curve7.loc[mask7, "est"],
        marker="s", ms=4, lw=2, color='#E53935', label="7-Day Cumulative Shock")
ax.fill_between(curve7.loc[mask7, "shock"]*100,
                curve7.loc[mask7, "p25"], curve7.loc[mask7, "p75"],
                alpha=0.15, color='#E53935')

ax.set_xlabel("ETH Price Shock (%)")
ax.set_ylabel("Estimated Daily Liquidations")
ax.set_title("Stress Curve: ETH Price Shock → Expected Liquidation Volume")
ax.legend(loc="upper left")
ax.axvline(-5, ls="--", lw=0.8, color="gray", alpha=0.5)
ax.annotate("-5% threshold", xy=(-5, ax.get_ylim()[1]*0.9),
            fontsize=9, color="gray", ha="right")

# Effective sample count on right axis
ax2 = ax.twinx()
eff = np.nan_to_num(np.maximum(
    curve1["effN"].values, curve7["effN"].values))
ax2.bar(curve1["shock"]*100, eff, width=0.4, alpha=0.1, color="gray")
ax2.set_ylabel("Effective Sample Count", color="gray")
ax2.tick_params(axis='y', labelcolor='gray')
ax2.set_ylim(0, max(5, eff.max()*1.3))

plt.savefig(f"{FIGS}/fig5_stress_curve.pdf")
plt.savefig(f"{FIGS}/fig5_stress_curve.png")
plt.close()
print("Saved fig5")

# ── Fig 6: Liquidation Distribution Histogram ──
fig, ax = plt.subplots(figsize=(7, 3.5))
bins = np.arange(0, merged["liq_cnt"].quantile(0.95)+5, 5)
ax.hist(merged["liq_cnt"], bins=bins, color='#2196F3',
        edgecolor='white', alpha=0.8)
ax.axvline(merged["liq_cnt"].median(), ls="--", lw=1.5,
           color='#E53935', label=f'Median = {merged["liq_cnt"].median():.0f}')
ax.axvline(merged["liq_cnt"].mean(), ls="-.", lw=1.5,
           color='#FF9800', label=f'Mean = {merged["liq_cnt"].mean():.1f}')
ax.set_xlabel("Daily Liquidation Count")
ax.set_ylabel("Frequency (Days)")
ax.set_title("Distribution of Daily Liquidation Counts")
ax.legend()
plt.savefig(f"{FIGS}/fig6_liq_distribution.pdf")
plt.savefig(f"{FIGS}/fig6_liq_distribution.png")
plt.close()
print("Saved fig6")

print("\nAll figures generated successfully!")


