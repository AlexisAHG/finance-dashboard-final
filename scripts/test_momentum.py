import pandas as pd

from src.analytics.strategies_univariate import momentum
from src.analytics.backtest import run_backtest


def main():
    prices = pd.Series(
        [100, 105, 103, 110, 120],
        index=pd.date_range("2024-01-01", periods=5)
    )

    equity = run_backtest(prices, momentum(prices, lookback=2))
    print(equity)


if __name__ == "__main__":
    main()
