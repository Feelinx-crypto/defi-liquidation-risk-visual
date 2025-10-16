import pandas as pd

def liq_daily_count(df_logs: pd.DataFrame) -> pd.DataFrame:
    # df_logs 需含 "timestamp" 列为 datetime（UTC）
    d = df_logs.copy()
    d["date"] = pd.to_datetime(d["timestamp"]).dt.tz_convert("UTC").dt.date
    return d.groupby("date").size().reset_index(name="liq_cnt")

def merge_ret_vs_liq(daily_px: pd.DataFrame, daily_liq: pd.DataFrame) -> pd.DataFrame:
    px = daily_px.copy()
    px["date"] = pd.to_datetime(px["date"]).dt.date
    liq = daily_liq.copy()
    liq["date"] = pd.to_datetime(liq["date"]).dt.date
    m = pd.merge(liq, px[["date","ret","price"]], on="date", how="inner").dropna()
    m["ret"] = m["ret"].astype(float)
    m["liq_cnt"] = m["liq_cnt"].astype(int)
    return m
