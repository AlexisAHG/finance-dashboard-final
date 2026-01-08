from dotenv import load_dotenv
load_dotenv()

import os
import time
from datetime import datetime, timezone
from typing import List

import pandas as pd
import requests

from src.data.cache import load_cache, save_cache

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


def _to_unix(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _resolution(interval: str) -> str:
    mapping = {
        "1m": "1",
        "5m": "5",
        "15m": "15",
        "30m": "30",
        "1h": "60",
        "1d": "D",
    }
    interval = interval.lower()
    if interval not in mapping:
        raise ValueError("Interval non supporté (1m, 5m, 15m, 30m, 1h, 1d)")
    return mapping[interval]


def _get_api_key() -> str:
    key = os.getenv("FINNHUB_API_KEY")
    if not key:
        raise RuntimeError("FINNHUB_API_KEY manquant dans .env")
    return key


def get_prices(
    symbols: List[str],
    start: datetime,
    end: datetime,
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Télécharge les prix de clôture depuis Finnhub.
    Retourne un DataFrame :
    - index : datetime UTC
    - colonnes : symbols
    """
    cache_key = f"prices_{'_'.join(symbols)}_{interval}_{start.date()}_{end.date()}"
    cached = load_cache(cache_key)
    if cached is not None:
        return cached


    api_key = _get_api_key()
    resolution = _resolution(interval)

    start_u = _to_unix(start)
    end_u = _to_unix(end)

    series = []

    for symbol in symbols:
        url = f"{FINNHUB_BASE_URL}/stock/candle"
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "from": start_u,
            "to": end_u,
            "token": api_key,
        }

        for attempt in range(3):
            r = requests.get(url, params=params, timeout=10)

            if r.status_code == 429:
                time.sleep(1.5 * (attempt + 1))
                continue

            r.raise_for_status()
            data = r.json()
            break

        if data.get("s") != "ok":
            raise RuntimeError(f"Aucune donnée pour {symbol}")

        index = pd.to_datetime(data["t"], unit="s", utc=True)
        close = pd.Series(data["c"], index=index, name=symbol).astype(float)
        series.append(close)

    prices = pd.concat(series, axis=1).sort_index()

    save_cache(cache_key, prices)

    return prices
