import requests, pandas as pd

def binance_daily(symbol: str = "ETHUSDT", limit: int = 1000) -> pd.DataFrame:
    urls = [
        "https://api.binance.com/api/v3/klines",
        "https://data-api.binance.vision/api/v3/klines",
    ]
    for u in urls:
        r = requests.get(u, params={"symbol": symbol, "interval": "1d", "limit": limit}, timeout=30)
        if r.status_code == 200:
            k = r.json()
            df = pd.DataFrame(k, columns=["ot","o","h","l","c","v","ct","qv","t","tb","tq","x"])
            out = pd.DataFrame({
                "date": pd.to_datetime(df["ct"], unit="ms", utc=True).dt.date,
                "price": df["c"].astype(float)
            })
            out["ret"] = out["price"].pct_change()
            return out
    raise RuntimeError("Binance daily price fetch failed")
