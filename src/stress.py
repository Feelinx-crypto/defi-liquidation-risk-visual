"""
Stress testing module: kernel regression, ensemble model, SHAP, and anomaly detection.

Implements:
- Nadaraya-Watson kernel regression with bootstrap confidence intervals
- Ensemble stress model (kernel + RandomForest + GradientBoosting)
- SHAP feature importance for the ensemble model
- Isolation-forest-based anomaly detection for unusual liquidation days
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any


def kernel_curve(x, y, grid, sigma=0.012, n_boot=200, min_eff_n=2.0, seed=42):
    """
    Gaussian kernel regression with bootstrap uncertainty bands.

    Returns a DataFrame with columns:
      - shock: shock grid (same units as x, e.g. -0.05 for -5%)
      - est: kernel-regression estimate E[y | x=shock]
      - p25, p75: bootstrap 25th/75th percentiles for the estimate
      - effN: effective sample size (Kish ESS) for local weights

    Notes:
      - We report an estimate only when effN >= min_eff_n.
      - effN uses Kish ESS: (sum w)^2 / sum(w^2), producing non-integers.
      - Bootstrap resamples indices proportional to kernel weights and uses the
        (unweighted) mean of resampled y. This avoids overweighting the kernel
        twice and yields percentile bands that are consistent with the estimate.
    """
    rng = np.random.default_rng(seed)
    xv = x.values.astype(float)
    yv = y.values.astype(float)

    est = []
    p25 = []
    p75 = []
    effN = []

    for g in grid:
        w = np.exp(-((xv - g) ** 2) / (2 * sigma ** 2))
        w_sum = float(w.sum())
        if w_sum == 0.0:
            effN.append(0.0)
            est.append(np.nan)
            p25.append(np.nan)
            p75.append(np.nan)
            continue

        n_eff = (w_sum**2) / float(np.sum(w**2))
        effN.append(float(n_eff))

        if n_eff < float(min_eff_n):
            est.append(np.nan)
            p25.append(np.nan)
            p75.append(np.nan)
            continue

        mu = float(np.average(yv, weights=w))
        p = w / w_sum
        idx = np.arange(len(xv))
        bs = []
        for _ in range(n_boot):
            samp = rng.choice(idx, size=len(idx), replace=True, p=p)
            bs.append(float(np.mean(yv[samp])))

        est.append(mu)
        p25.append(float(np.nanpercentile(bs, 25)))
        p75.append(float(np.nanpercentile(bs, 75)))

    return pd.DataFrame({"shock": grid, "est": est, "p25": p25, "p75": p75, "effN": effN})


# ---------------------------------------------------------------------------
# Feature engineering for ML models
# ---------------------------------------------------------------------------

def build_features(merged: pd.DataFrame) -> pd.DataFrame:
    """
    Build ML features from the merged (date, ret, liq_cnt, price) DataFrame.

    Features created:
    - ret: same-day return
    - abs_ret: absolute return (magnitude of move)
    - ret_neg: max(0, -ret) — downside magnitude
    - vol_7d: rolling 7-day standard deviation of returns
    - vol_30d: rolling 30-day standard deviation of returns
    - ret_7d: cumulative 7-day return
    - momentum_3d: 3-day cumulative return (short-term momentum)
    - liq_lag1, liq_lag2, liq_lag3: lagged liquidation counts
    """
    df = merged.copy()
    df = df.sort_values("date").reset_index(drop=True)
    df["ret"] = df["ret"].astype(float)
    df["liq_cnt"] = df["liq_cnt"].astype(int)

    df["abs_ret"] = df["ret"].abs()
    df["ret_neg"] = df["ret"].clip(upper=0).abs()
    df["vol_7d"] = df["ret"].rolling(7, min_periods=3).std()
    df["vol_30d"] = df["ret"].rolling(30, min_periods=10).std()
    df["ret_7d"] = df["ret"].rolling(7, min_periods=3).sum()
    df["momentum_3d"] = df["ret"].rolling(3, min_periods=2).sum()
    df["liq_lag1"] = df["liq_cnt"].shift(1)
    df["liq_lag2"] = df["liq_cnt"].shift(2)
    df["liq_lag3"] = df["liq_cnt"].shift(3)

    return df.dropna().reset_index(drop=True)


FEATURE_COLS = [
    "ret", "abs_ret", "ret_neg",
    "vol_7d", "vol_30d", "ret_7d",
    "momentum_3d", "liq_lag1", "liq_lag2", "liq_lag3",
]


# ---------------------------------------------------------------------------
# Ensemble stress model
# ---------------------------------------------------------------------------

def train_ensemble(merged: pd.DataFrame, seed: int = 42) -> Dict[str, Any]:
    """
    Train an ensemble stress model (kernel + RandomForest + GradientBoosting).

    Args:
        merged: DataFrame with columns date, ret, liq_cnt, price.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary with keys:
        - 'rf': fitted RandomForestRegressor
        - 'gb': fitted GradientBoostingRegressor
        - 'features': DataFrame used for training
        - 'feature_names': list of feature column names
        - 'mae_rf', 'mae_gb', 'mae_kernel': cross-validated MAE for each model
    """
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import cross_val_score

    df = build_features(merged)
    X = df[FEATURE_COLS].values
    y = df["liq_cnt"].values

    rf = RandomForestRegressor(
        n_estimators=100, max_depth=10, min_samples_split=5, random_state=seed
    )
    gb = GradientBoostingRegressor(
        n_estimators=150, learning_rate=0.05, max_depth=5,
        subsample=0.8, random_state=seed
    )

    # Cross-validated MAE
    mae_rf = -cross_val_score(rf, X, y, cv=5, scoring="neg_mean_absolute_error").mean()
    mae_gb = -cross_val_score(gb, X, y, cv=5, scoring="neg_mean_absolute_error").mean()

    # Kernel baseline MAE (leave-one-out style)
    kernel_preds = []
    for i in range(len(df)):
        mask = np.ones(len(df), dtype=bool)
        mask[i] = False
        xv = df.loc[mask, "ret"].values.astype(float)
        yv = df.loc[mask, "liq_cnt"].values.astype(float)
        g = df.loc[i, "ret"]
        w = np.exp(-((xv - g) ** 2) / (2 * 0.012 ** 2))
        if w.sum() > 0:
            kernel_preds.append(np.average(yv, weights=w))
        else:
            kernel_preds.append(np.nan)
    kernel_preds = np.array(kernel_preds)
    valid = ~np.isnan(kernel_preds)
    mae_kernel = np.mean(np.abs(kernel_preds[valid] - y[valid]))

    # Fit on full data
    rf.fit(X, y)
    gb.fit(X, y)

    return {
        "rf": rf,
        "gb": gb,
        "features": df,
        "feature_names": FEATURE_COLS,
        "mae_rf": mae_rf,
        "mae_gb": mae_gb,
        "mae_kernel": mae_kernel,
    }


def ensemble_predict(models: Dict[str, Any], X: np.ndarray,
                     weights: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Generate ensemble predictions using weighted average of RF and GB.

    Args:
        models: Output of train_ensemble().
        X: Feature matrix (n_samples, n_features).
        weights: Optional [w_rf, w_gb] weights. Defaults to inverse-MAE weighting.

    Returns:
        Ensemble predictions as numpy array.
    """
    pred_rf = models["rf"].predict(X)
    pred_gb = models["gb"].predict(X)
    if weights is None:
        inv_rf = 1.0 / max(models["mae_rf"], 1e-6)
        inv_gb = 1.0 / max(models["mae_gb"], 1e-6)
        total = inv_rf + inv_gb
        weights = np.array([inv_rf / total, inv_gb / total])
    return weights[0] * pred_rf + weights[1] * pred_gb


# ---------------------------------------------------------------------------
# SHAP feature importance
# ---------------------------------------------------------------------------

def compute_shap(models: Dict[str, Any]) -> pd.DataFrame:
    """
    Compute feature importance for the gradient boosting model.

    Attempts SHAP TreeExplainer first; falls back to sklearn permutation
    importance if SHAP is unavailable or incompatible.

    Args:
        models: Output of train_ensemble().

    Returns:
        DataFrame with columns: feature, importance, method.
    """
    df = models["features"]
    X = df[FEATURE_COLS].values
    y = df["liq_cnt"].values
    gb = models["gb"]

    # Try SHAP first
    try:
        import shap
        explainer = shap.TreeExplainer(gb)
        shap_values = explainer.shap_values(X)
        importance = pd.DataFrame({
            "feature": FEATURE_COLS,
            "importance": np.abs(shap_values).mean(axis=0),
            "method": "SHAP",
        })
    except Exception:
        # Fallback: permutation importance
        from sklearn.inspection import permutation_importance
        result = permutation_importance(gb, X, y, n_repeats=20, random_state=42)
        importance = pd.DataFrame({
            "feature": FEATURE_COLS,
            "importance": result.importances_mean,
            "method": "permutation",
        })

    return importance.sort_values("importance", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

def detect_anomalies(merged: pd.DataFrame, contamination: float = 0.05,
                     seed: int = 42) -> pd.DataFrame:
    """
    Detect anomalous liquidation days using Isolation Forest.

    Args:
        merged: DataFrame with date, ret, liq_cnt, price columns.
        contamination: Expected fraction of anomalies (default 5%).
        seed: Random seed.

    Returns:
        DataFrame of anomalous days with columns: date, ret, liq_cnt, anomaly_score.
    """
    from sklearn.ensemble import IsolationForest

    df = build_features(merged)
    X = df[FEATURE_COLS].values

    iso = IsolationForest(
        contamination=contamination, random_state=seed, n_estimators=200
    )
    df["anomaly"] = iso.fit_predict(X)
    df["anomaly_score"] = iso.decision_function(X)

    anomalies = (
        df[df["anomaly"] == -1]
        .sort_values("anomaly_score")
        [["date", "ret", "liq_cnt", "anomaly_score"]]
        .reset_index(drop=True)
    )
    return anomalies
