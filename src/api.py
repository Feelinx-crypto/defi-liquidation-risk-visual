import os
import time
import requests
from dotenv import load_dotenv

# 自动加载项目根目录下的 .env 文件
load_dotenv()

# 从环境变量读取 API key
API_KEY = os.getenv("ETHERSCAN_API_KEY")
BASE = "https://api.etherscan.io/v2/api"


def get_latest_block(chainid: int = 1) -> int:
    """获取最新区块高度"""
    if not API_KEY:
        raise RuntimeError("Missing ETHERSCAN_API_KEY in environment or .env file")

    r = requests.get(BASE, params={
        "chainid": chainid,
        "module": "proxy",
        "action": "eth_blockNumber",
        "apikey": API_KEY
    }, timeout=30)
    r.raise_for_status()
    return int(r.json()["result"], 16)


def get_logs(topic0: str, address: str, start_block: int, end_block: int,
             chainid: int = 1, max_retry: int = 3, sleep_sec: float = 1.0):
    """拉指定区间 logs，失败自动重试"""
    params = {
        "chainid": chainid,
        "module": "logs",
        "action": "getLogs",
        "fromBlock": start_block,
        "toBlock": end_block,
        "topic0": topic0,
        "address": address,
        "apikey": API_KEY
    }
    for _ in range(max_retry):
        r = requests.get(BASE, params=params, timeout=60)
        if r.status_code == 200:
            js = r.json()
            if js.get("status") == "1":
                return js["result"]
        time.sleep(sleep_sec)
    return []


def chunked_get_logs(topic0: str, address: str,
                     start_block: int, end_block: int, step: int = 5_000, chainid: int = 1):
    """分块遍历区间，避免单次过大；返回拼接后的列表"""
    out = []
    cur = start_block
    while cur <= end_block:
        to_blk = min(cur + step - 1, end_block)
        out.extend(get_logs(topic0, address, cur, to_blk, chainid=chainid))
        cur = to_blk + 1
        time.sleep(0.2)
    return out
