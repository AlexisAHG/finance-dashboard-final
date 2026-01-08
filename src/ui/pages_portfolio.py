import streamlit as st
import pandas as pd
import numpy as np

from src.data.fetchers import get_prices
from src.analytics.metrics import sharpe_ratio, max_drawdown


def _compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.dropna(how="any")
    return prices.pct_change().dropna()


def _simulate_equal_weight_portfolio(
    prices: pd.DataFrame,
    rebalancing: str = "Monthly",
    initial_value: float = 1.0,
) -> pd.Series:
    """
    Equal-weight portfolio with optional rebalancing:
      - None: initialize equal weights then let them drift
      - Weekly: rebalance every Monday
      - Monthly: rebalance on first trading day of each month
    """
    prices = prices.dropna(how="any")
    if prices.shape[1] < 3:
        raise ValueError("Quant B requires at least 3 assets.")

    rets = _compute_returns(prices)
    idx = rets.index

    n = rets.shape[1]
    target_w = np.ones(n) / n
    w = target_w.copy()

    # rebalance flags
    if rebalancing == "None":
        reb = np.zeros(len(idx), dtype=bool)
        reb[0] = True
    elif rebalancing == "Weekly":
        reb = (idx.weekday == 0).to_numpy()
        reb[0] = True
    elif rebalancing == "Monthly":
        p = idx.to_period("M")
        reb = (p != p.shift(1))
        reb[0] = True
    else:
        raise ValueError("Rebalancing must be one of: None, Weekly, Monthly")

    equity = np.empty(len(idx), dtype=float)
    value = float(initial_value)

    for i in range(len(idx)):
        if reb[i]:
            w = target_w.copy()

        r = rets.iloc[i].to_numpy(dtype=float)
        pr = float(np.dot(w, r))
        value *= (1.0 + pr)
        equity[i] = value

        # drift weights
        w = w * (1.0 + r)
        s = w.sum()
        if s != 0:
            w = w / s

    return pd.Series(equity, index=idx, name="portfolio_equity")


def render_portfolio_page():
    st.title("Quant B — Portfolio")
    st.caption("Equal-weight portfolio · optional rebalancing · diagnostics (corr/vol)")

    with st.expander("What this model is doing (and what it is not)"):
        st.markdown(
            """
**What it does**
- Builds an **equal-weight** portfolio across the selected assets.
- Applies optional **rebalancing** (None / Weekly / Monthly).
- Compares assets vs portfolio on a **normalized** basis (start = 1).

**What it is not**
- Not a forecasting model, and not meant for live trading signals.

**Key limitations**
- No transaction costs, no slippage, close-to-close execution assumption.
            """
        )

    with st.sidebar:
        st.subheader("Quant B — Parameters")

        tickers_raw = st.text_input(
            "Tickers (comma-separated, min 3)",
            value="AAPL, MSFT, GOOGL",
        )
        tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]

        start = st.date_input("Start date", value=pd.to_datetime("2024-01-01")).isoformat()
        end = st.date_input("End date", value=pd.to_datetime("today")).isoformat()
        interval = st.selectbox("Interval", ["1d"], index=0)

        rebalancing = st.selectbox("Rebalancing", ["None", "Weekly", "Monthly"], index=2)
        run = st.button("Run portfolio backtest")

    if not run:
        st.info("Set your parameters, then click **Run portfolio backtest**.")
        return

    if len(tickers) < 3:
        st.error("Quant B requires at least 3 assets.")
        return

    with st.spinner("Downloading prices and running simulation..."):
        prices = get_prices(tickers, start=start, end=end, interval=interval)

    if prices is None or prices.empty or prices.shape[1] < 3:
        st.error("Not enough data. Try different tickers or an earlier start date.")
        return

    prices = prices.dropna(how="any")

    # Portfolio with selected rebalancing
    equity_reb = _simulate_equal_weight_portfolio(
        prices, rebalancing=rebalancing, initial_value=1.0
    )

    # Benchmark: no rebalancing
    equity_no_reb = _simulate_equal_weight_portfolio(
        prices, rebalancing="None", initial_value=1.0
    )

    returns = _compute_returns(prices)

    st.subheader("Assets vs Portfolio (normalized)")
    st.caption(
    "The benchmark portfolio (no rebalancing) isolates the effect of rebalancing: "
    "same assets, same weights at inception, only the rebalancing rule changes."
    )

    norm_prices = prices / prices.iloc[0]
    norm_reb = equity_reb / equity_reb.iloc[0]
    norm_no_reb = equity_no_reb / equity_no_reb.iloc[0]

    chart_df = norm_prices.copy()
    chart_df["Portfolio (rebalanced)"] = norm_reb
    chart_df["Portfolio (no rebalancing)"] = norm_no_reb

    st.line_chart(chart_df)

    st.subheader("Portfolio metrics comparison")
    periods = 252

    def _metrics(eq: pd.Series):
        norm = eq / eq.iloc[0]
        return {
            "return": float(norm.iloc[-1] - 1.0),
            "sharpe": sharpe_ratio(eq, periods_per_year=periods, rf=0.0),
            "mdd": max_drawdown(eq),
        }

    m_reb = _metrics(equity_reb)
    m_no = _metrics(equity_no_reb)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Rebalanced portfolio**")
        st.metric("Total return", f"{m_reb['return']*100:.2f}%")
        st.metric("Sharpe", f"{m_reb['sharpe']:.2f}")
        st.metric("Max drawdown", f"{m_reb['mdd']*100:.2f}%")

    with c2:
        st.markdown("**No rebalancing (benchmark)**")
        st.metric("Total return", f"{m_no['return']*100:.2f}%")
        st.metric("Sharpe", f"{m_no['sharpe']:.2f}")
        st.metric("Max drawdown", f"{m_no['mdd']*100:.2f}%")

    st.subheader("Correlation matrix (assets)")
    st.dataframe(returns.corr())

    st.subheader("Annualized volatility (assets)")
    ann_vol = returns.std() * (periods ** 0.5)
    st.dataframe(ann_vol.sort_values(ascending=False).to_frame("ann_vol"))

    with st.expander("Model limitations"):
        st.markdown(
            """
- Data source: Yahoo Finance (via `yfinance` inside the project fetcher).
- Close-to-close returns, no transaction costs, no slippage.
- Equal-weight portfolio; rebalancing resets weights to equal allocation.
            """
        )
