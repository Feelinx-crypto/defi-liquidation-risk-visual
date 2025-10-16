import time, requests

BASE = "https://api.etherscan.io/v2/api"

def get_latest_block(api_key: str, chainid: int = 1) -> int:
    r = requests.get(BASE, params={
        "chainid": chainid, "module": "proxy", "action": "eth_blockNumber", "apikey": api_key
    }, timeout=30)
    r.raise_for_status()
    return int(r.json()["result"], 16)

def get_logs(api_key: str, topic0: str, address: str, start_block: int, end_block: int,
             chainid: int = 1, max_retry: int = 3, sleep_sec: float = 1.0):
    """一次调用拉指定区间 logs。失败自动轻度重试。"""
    params = {
        "chainid": chainid, "module": "logs", "action": "getLogs",
        "fromBlock": start_block, "toBlock": end_block,
        "topic0": topic0, "address": address, "apikey": api_key
    }
    for _ in range(max_retry):
        r = requests.get(BASE, params=params, timeout=60)
        if r.status_code == 200:
            js = r.json()
            if js.get("status") == "1":
                return js["result"]
            # 速率/临时错误，稍后重试
            time.sleep(sleep_sec)
            continue
        time.sleep(sleep_sec)
    return []  # 保底：空列表

def chunked_get_logs(api_key: str, topic0: str, address: str,
                     start_block: int, end_block: int, step: int = 5_000, chainid: int = 1):
    """分块遍历区间，避免单次过大；返回拼接后的列表。"""
    out = []
    cur = start_block
    while cur <= end_block:
        to_blk = min(cur + step - 1, end_block)
        out.extend(get_logs(api_key, topic0, address, cur, to_blk, chainid=chainid))
        cur = to_blk + 1
        time.sleep(0.2)  # 轻限速
    return out
