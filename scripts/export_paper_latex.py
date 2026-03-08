#!/usr/bin/env python3
"""
Export paper-ready LaTeX snippets from the repo's CSV outputs.

This script is meant to eliminate manual copy/paste of headline numbers into the
report, preventing inconsistencies between:
  - data/*.csv (authoritative outputs)
  - template_extracted/main.tex (narrative + tables)

Outputs (by default):
  - template_extracted/auto_numbers.tex
  - template_extracted/auto_summary_table.tex
  - template_extracted/auto_stress_table.tex
  - template_extracted/auto_model_table.tex
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _template_dir(repo_root: Path) -> Path:
    return repo_root.parent / "template_extracted"


def _load_merged(data_dir: Path) -> pd.DataFrame:
    merged = pd.read_csv(data_dir / "eth_ret_vs_liq.csv")
    merged["date"] = pd.to_datetime(merged["date"])
    merged["ret"] = merged["ret"].astype(float)
    merged["liq_cnt"] = merged["liq_cnt"].astype(int)
    return merged


def _load_curve(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["shock"] = df["shock"].astype(float)
    for col in ["est", "p25", "p75", "effN"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["shock_round"] = df["shock"].round(3)
    return df


def _row_at_shock(curve: pd.DataFrame, shock: float) -> dict[str, float | None]:
    target = round(float(shock), 3)
    subset = curve[curve["shock_round"] == target]
    if subset.empty:
        # Fallback: nearest value
        idx = (curve["shock"] - shock).abs().idxmin()
        subset = curve.loc[[idx]]

    row = subset.iloc[0]
    return {
        "shock": float(row["shock"]),
        "est": None if np.isnan(row["est"]) else float(row["est"]),
        "p25": None if np.isnan(row["p25"]) else float(row["p25"]),
        "p75": None if np.isnan(row["p75"]) else float(row["p75"]),
        "effN": None if np.isnan(row["effN"]) else float(row["effN"]),
    }


def _fmt_count(x: float | None) -> str:
    return "--" if x is None else f"{int(round(x))}"


def _fmt_iqr(p25: float | None, p75: float | None) -> str:
    if p25 is None or p75 is None:
        return "--"
    return f"{int(round(p25))}--{int(round(p75))}"


def _fmt_float(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}"

def _fmt_int_with_commas_latex(x: int) -> str:
    # Use LaTeX-friendly thousands separators (e.g., 1{,}043)
    return f"{x:,}".replace(",", "{,}")


def _fmt_pct_signed(x: float, digits: int = 2) -> str:
    sign = "+" if x > 0 else ""
    return f"{sign}{x:.{digits}f}\\%"


def _fmt_pct(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}\\%"


def _write_auto_numbers(out_path: Path, *, merged: pd.DataFrame, curve_1d: pd.DataFrame) -> None:
    mean_down = float(merged.loc[merged["ret"] < 0, "liq_cnt"].mean())
    mean_up = float(merged.loc[merged["ret"] > 0, "liq_cnt"].mean())
    ratio = mean_down / mean_up if mean_up else float("nan")

    down_days = int((merged["ret"] < 0).sum())
    total_days = int(len(merged))
    share_days = down_days / total_days if total_days else float("nan")

    liq_down = int(merged.loc[merged["ret"] < 0, "liq_cnt"].sum())
    liq_total = int(merged["liq_cnt"].sum())
    share_liq = liq_down / liq_total if liq_total else float("nan")

    mean_liq = float(merged["liq_cnt"].mean())
    median_liq = float(merged["liq_cnt"].median())

    s5 = _row_at_shock(curve_1d, -0.05)
    s10 = _row_at_shock(curve_1d, -0.10)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% AUTO-GENERATED FILE. DO NOT EDIT BY HAND.",
        "% Regenerate via: python defi-liquidation-risk-visual/scripts/export_paper_latex.py",
        "",
        f"\\newcommand{{\\MeanDownDays}}{{{_fmt_float(mean_down, 1)}}}",
        f"\\newcommand{{\\MeanUpDays}}{{{_fmt_float(mean_up, 1)}}}",
        f"\\newcommand{{\\MeanRatioDownUp}}{{{_fmt_float(ratio, 2)}}}",
        f"\\newcommand{{\\ShareDownDays}}{{{_fmt_float(share_days * 100, 1)}\\%}}",
        f"\\newcommand{{\\ShareDownLiqs}}{{{_fmt_float(share_liq * 100, 1)}\\%}}",
        f"\\newcommand{{\\MeanDailyLiq}}{{{_fmt_float(mean_liq, 1)}}}",
        f"\\newcommand{{\\MedianDailyLiq}}{{{int(median_liq)}}}",
        "",
        f"\\newcommand{{\\StressOneDayMinusFiveEst}}{{{_fmt_count(s5['est'])}}}",
        f"\\newcommand{{\\StressOneDayMinusFiveIQR}}{{{_fmt_iqr(s5['p25'], s5['p75'])}}}",
        f"\\newcommand{{\\StressOneDayMinusTenEst}}{{{_fmt_count(s10['est'])}}}",
        f"\\newcommand{{\\StressOneDayMinusTenIQR}}{{{_fmt_iqr(s10['p25'], s10['p75'])}}}",
        "",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def _write_summary_table(out_path: Path, *, merged: pd.DataFrame) -> None:
    total_events = int(merged["liq_cnt"].sum())
    obs_days = int(len(merged))

    mean_liq = float(merged["liq_cnt"].mean())
    median_liq = float(merged["liq_cnt"].median())
    max_liq = int(merged["liq_cnt"].max())
    std_liq = float(merged["liq_cnt"].std(ddof=1))

    mean_ret = float(merged["ret"].mean())
    std_ret = float(merged["ret"].std(ddof=1))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% AUTO-GENERATED FILE. DO NOT EDIT BY HAND.",
        "% Regenerate via: python defi-liquidation-risk-visual/scripts/export_paper_latex.py",
        "",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Summary statistics of the liquidation dataset (Jan 9 -- Oct 15, 2025).}",
        "\\label{tab:summary}",
        "\\begin{tabular}{lr}",
        "\\toprule",
        "\\textbf{Metric} & \\textbf{Value} \\\\",
        "\\midrule",
        f"Total liquidation events & {_fmt_int_with_commas_latex(total_events)} \\\\",
        f"Observation days & {obs_days} \\\\",
        f"Mean daily liquidations & {_fmt_float(mean_liq, 1)} \\\\",
        f"Median daily liquidations & {int(median_liq)} \\\\",
        f"Max daily liquidations & {_fmt_int_with_commas_latex(max_liq)} \\\\",
        f"Std.\\ dev.\\ of daily liquidations & {_fmt_float(std_liq, 1)} \\\\",
        f"Mean daily ETH return & {_fmt_pct_signed(mean_ret * 100, 2)} \\\\",
        f"Std.\\ dev.\\ of daily ETH return & {_fmt_pct(std_ret * 100, 2)} \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_stress_table(out_path: Path, *, curve_1d: pd.DataFrame, curve_7d: pd.DataFrame) -> None:
    shocks = [-0.05, -0.10, -0.15, -0.20]
    rows_1d = [_row_at_shock(curve_1d, s) for s in shocks]
    rows_7d = [_row_at_shock(curve_7d, s) for s in shocks]

    def fmt_row(rows: list[dict[str, float | None]], key: str) -> list[str]:
        if key == "iqr":
            return [_fmt_iqr(r["p25"], r["p75"]) for r in rows]
        return [_fmt_count(r[key]) for r in rows]  # type: ignore[index]

    est_1d = fmt_row(rows_1d, "est")
    iqr_1d = fmt_row(rows_1d, "iqr")
    est_7d = fmt_row(rows_7d, "est")
    iqr_7d = fmt_row(rows_7d, "iqr")
    eff_1d = ["--" if r["effN"] is None else _fmt_float(float(r["effN"]), 1) for r in rows_1d]
    eff_7d = ["--" if r["effN"] is None else _fmt_float(float(r["effN"]), 1) for r in rows_7d]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% AUTO-GENERATED FILE. DO NOT EDIT BY HAND.",
        "% Regenerate via: python defi-liquidation-risk-visual/scripts/export_paper_latex.py",
        "",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Estimated daily liquidation counts under hypothetical ETH price shocks (kernel regression with bootstrap IQR). Point estimates are omitted when $N_{\\text{eff}} < 2$.}",
        "\\label{tab:stress}",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "\\textbf{Shock Scenario} & \\textbf{$-$5\\%} & \\textbf{$-$10\\%} & \\textbf{$-$15\\%} & \\textbf{$-$20\\%} \\\\",
        "\\midrule",
        f"1-Day shock (est.) & {est_1d[0]} & {est_1d[1]} & {est_1d[2]} & {est_1d[3]} \\\\",
        f"1-Day shock (IQR) & {iqr_1d[0]} & {iqr_1d[1]} & {iqr_1d[2]} & {iqr_1d[3]} \\\\",
        f"7-Day cumulative (est.) & {est_7d[0]} & {est_7d[1]} & {est_7d[2]} & {est_7d[3]} \\\\",
        f"7-Day cumulative (IQR) & {iqr_7d[0]} & {iqr_7d[1]} & {iqr_7d[2]} & {iqr_7d[3]} \\\\",
        f"$N_{{\\text{{eff}}}}$ (1-Day) & {eff_1d[0]} & {eff_1d[1]} & {eff_1d[2]} & {eff_1d[3]} \\\\",
        f"$N_{{\\text{{eff}}}}$ (7-Day) & {eff_7d[0]} & {eff_7d[1]} & {eff_7d[2]} & {eff_7d[3]} \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def _write_model_table(out_path: Path, *, merged: pd.DataFrame, repo_root: Path) -> None:
    """
    Export a compact model-comparison table (MAE).

    Uses the repo's own implementation (`src/stress.py:train_ensemble`) so the
    reported numbers match the code used for the analysis.
    """
    import sys

    sys.path.append(str(repo_root))
    from src.stress import train_ensemble  # type: ignore

    models = train_ensemble(merged)
    mae_kernel = float(models["mae_kernel"])
    mae_rf = float(models["mae_rf"])
    mae_gb = float(models["mae_gb"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% AUTO-GENERATED FILE. DO NOT EDIT BY HAND.",
        "% Regenerate via: python defi-liquidation-risk-visual/scripts/export_paper_latex.py",
        "",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Out-of-sample model comparison (mean absolute error; lower is better).}",
        "\\label{tab:model_mae}",
        "\\begin{tabular}{lcc}",
        "\\toprule",
        "\\textbf{Model} & \\textbf{Feature set} & \\textbf{MAE} \\\\",
        "\\midrule",
        f"Kernel regression & Return-only & {_fmt_float(mae_kernel, 1)} \\\\",
        f"Random forest & Multi-feature & {_fmt_float(mae_rf, 1)} \\\\",
        f"Gradient boosting & Multi-feature & {_fmt_float(mae_gb, 1)} \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--template-dir",
        type=Path,
        default=None,
        help="Path to template_extracted (defaults to ../template_extracted)",
    )
    args = parser.parse_args()

    repo_root = _repo_root()
    data_dir = repo_root / "data"
    template_dir = args.template_dir or _template_dir(repo_root)

    merged = _load_merged(data_dir)
    curve_1d = _load_curve(data_dir / "stress_curve_1d.csv")
    curve_7d = _load_curve(data_dir / "stress_curve_7d.csv")

    _write_auto_numbers(template_dir / "auto_numbers.tex", merged=merged, curve_1d=curve_1d)
    _write_summary_table(template_dir / "auto_summary_table.tex", merged=merged)
    _write_stress_table(template_dir / "auto_stress_table.tex", curve_1d=curve_1d, curve_7d=curve_7d)
    _write_model_table(template_dir / "auto_model_table.tex", merged=merged, repo_root=repo_root)

    print(f"Wrote: {template_dir / 'auto_numbers.tex'}")
    print(f"Wrote: {template_dir / 'auto_summary_table.tex'}")
    print(f"Wrote: {template_dir / 'auto_stress_table.tex'}")
    print(f"Wrote: {template_dir / 'auto_model_table.tex'}")


if __name__ == "__main__":
    main()
