import pandas as pd
from datetime import timedelta

import yfinance as yf


# yfinance a des limites sur l'intraday (15m/30m/1h)
_MAX_DAYS_BY_INTERVAL = {
    "15m": 59,     # ~60 jours max
    "30m": 59,
    "1h": 729,     # ~730 jours max
    "1d": 5000,    # large
}

# mapping simple pour FX si tu veux "EUR/USD" dans l'UI
_YF_SYMBOL_MAP = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
}


def _clip_dates_for_interval(start: pd.Timestamp, end: pd.Timestamp, interval: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    max_days = _MAX_DAYS_BY_INTERVAL.get(interval, 365)
    if (end - start).days > max_days:
        start = end - timedelta(days=max_days)
    return start, end


def get_prices(symbols, start, end, interval="1d") -> pd.DataFrame:
    """
    Retourne un DataFrame avec colonnes = symbols (les noms UI), index datetime,
    valeurs = Close.
    """
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)

    # ⚠️ yfinance veut souvent end "exclusive", on ajoute 1 jour pour être sûr en daily
    if interval == "1d":
        end_yf = end + pd.Timedelta(days=1)
    else:
        end_yf = end

    # Clip pour éviter les data vides en intraday
    start_clip, end_clip = _clip_dates_for_interval(start, end_yf, interval)

    out = {}

    for sym in symbols:
        yf_sym = _YF_SYMBOL_MAP.get(sym, sym)

        data = yf.download(
            yf_sym,
            start=start_clip,
            end=end_clip,
            interval=interval,
            progress=False,
            auto_adjust=False,
            threads=False,
        )

        # yfinance renvoie parfois colonnes multiindex
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if data is None or data.empty:
            continue

        # on prend Close
        if "Close" not in data.columns:
            continue

        s = data["Close"].dropna()

        # index timezone parfois -> on normalise
        if getattr(s.index, "tz", None) is not None:
            s.index = s.index.tz_convert(None)

        out[sym] = s

    df = pd.DataFrame(out)

    # si tout est vide → on renvoie DF vide (la page Streamlit affichera une erreur claire)
    return df
