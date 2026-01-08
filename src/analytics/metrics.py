import numpy as np
import pandas as pd


def _to_returns(equity: pd.Series) -> pd.Series:
    """Convertit une courbe d'equity en rendements simples."""
    equity = pd.Series(equity).dropna()
    rets = equity.pct_change().dropna()
    return rets


def sharpe_ratio(equity: pd.Series, periods_per_year: int = 365, rf: float = 0.0) -> float:
    """
    Sharpe annualisé (crypto souvent 365).
    - equity: série de valeur portefeuille
    - rf: taux sans risque annuel (ex: 0.02 = 2%)
    """
    rets = _to_returns(equity)
    if len(rets) < 2:
        return float("nan")

    # rf journalier approx
    rf_per_period = rf / periods_per_year
    excess = rets - rf_per_period

    vol = excess.std(ddof=1)
    if vol == 0 or np.isnan(vol):
        return float("nan")

    sharpe = (excess.mean() / vol) * np.sqrt(periods_per_year)
    return float(sharpe)


def max_drawdown(equity: pd.Series) -> float:
    """Max drawdown en % (valeur négative)."""
    equity = pd.Series(equity).dropna()
    if equity.empty:
        return float("nan")

    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min())
