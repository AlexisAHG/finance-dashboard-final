import pandas as pd


def buy_and_hold(prices: pd.Series) -> pd.Series:
    """
    Buy & Hold: toujours investi (position = 1).
    Retourne une Series de positions (0/1) alignée sur prices.
    """
    return pd.Series(1.0, index=prices.index, name="position")


def momentum(prices: pd.Series, lookback: int = 20, threshold: float = 0.0) -> pd.Series:
    """
    Momentum simple:
    - calcule le rendement sur 'lookback' jours
    - si momentum > threshold => position = 1 sinon 0

    lookback: fenêtre de lookback (ex: 20 jours)
    threshold: seuil (0.0 = on investit si momentum positif)
    """
    mom = prices.pct_change(lookback)
    pos = (mom > threshold).astype(float)
    pos = pos.fillna(0.0)
    pos.name = "position"
    return pos


def sma_crossover(prices: pd.Series, fast: int = 20, slow: int = 50) -> pd.Series:
    """
    Bonus (facultatif mais très bien pour le projet):
    SMA crossover:
    - position = 1 si SMA(fast) > SMA(slow), sinon 0
    """
    sma_fast = prices.rolling(fast).mean()
    sma_slow = prices.rolling(slow).mean()
    pos = (sma_fast > sma_slow).astype(float).fillna(0.0)
    pos.name = "position"
    return pos
