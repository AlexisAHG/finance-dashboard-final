## Quant A — Single Asset Backtesting Module

### Objective
The goal of this module is to evaluate systematic trading strategies
on a single asset using historical price data.

### Implemented Strategies
- Buy & Hold
- Momentum (configurable lookback window)

### Methodology
- Historical prices are fetched from external data providers
- Trading positions are computed using lagged signals
- Equity curves are computed using a vectorized backtesting engine
- Performance metrics are evaluated on the resulting equity curve

### Metrics
- Sharpe Ratio (annualized)
- Maximum Drawdown

### Results Interpretation
The momentum strategy allows capturing medium-term trends,
while Buy & Hold serves as a baseline benchmark.
