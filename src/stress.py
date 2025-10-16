import numpy as np, pandas as pd

def kernel_curve(x, y, grid, sigma=0.012, n_boot=200, min_eff_n=8, seed=42):
    """高斯核回归 + bootstrap IQR；返回 shock, est, p25, p75, effN"""
    rng = np.random.default_rng(seed)
    xv = x.values.astype(float); yv = y.values.astype(float)
    est=[]; p25=[]; p75=[]; effN=[]
    for g in grid:
        w = np.exp(-((xv - g)**2) / (2 * sigma**2))
        n_eff = int((w / (w.max() if w.max() else 1) > 0.1).sum())
        effN.append(n_eff)
        if n_eff < min_eff_n or w.sum() == 0:
            est += [np.nan]; p25 += [np.nan]; p75 += [np.nan]; continue
        mu = np.average(yv, weights=w)
        idx = np.arange(len(xv))
        bs=[]
        for _ in range(n_boot):
            samp = rng.choice(idx, size=len(idx), replace=True, p=w / w.sum())
            bs.append(np.average(yv[samp], weights=w[samp]))
        est.append(mu)
        p25.append(np.nanpercentile(bs, 25))
        p75.append(np.nanpercentile(bs, 75))
    return pd.DataFrame({"shock": grid, "est": est, "p25": p25, "p75": p75, "effN": effN})
