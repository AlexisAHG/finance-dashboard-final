import pandas as pd

def compute_returns(prices: pd.Series) -> pd.Series:
    """Returns simples."""
    return prices.pct_change().fillna(0.0)

def run_backtest(prices: pd.Series, position: pd.Series, initial_cash: float = 1.0) -> pd.Series:
    """
    Calcule la valeur cumulée du portefeuille.
    - prices: Series prix
    - position: Series 0/1 (ou poids) alignée sur prices
    - initial_cash: valeur de départ (ex: 1.0)
    """
    position = position.reindex(prices.index).fillna(0.0)

    rets = compute_returns(prices)

    # On évite le look-ahead: la position prise à t-1 s'applique au return de t
    pos_lag = position.shift(1).fillna(0.0)

    strat_rets = pos_lag * rets
    equity = (1.0 + strat_rets).cumprod() * initial_cash
    equity.name = "equity"
    return equity
