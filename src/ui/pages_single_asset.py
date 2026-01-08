import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from src.data.fetchers import get_prices
from src.analytics.strategies_univariate import buy_and_hold, momentum
from src.analytics.backtest import run_backtest
from src.analytics.metrics import sharpe_ratio, max_drawdown
from src.analytics.prediction import linear_price_prediction


def render_single_asset_page():
    st.title("Quant A — Single Asset (BTC/USD)")

    # --- Sidebar controls
    st.sidebar.header("Paramètres")

    symbol = st.sidebar.selectbox("Asset", ["BTC-USD", "ETH-USD", "EUR/USD"], index=0)
    interval = st.sidebar.selectbox("Interval", ["1d", "1h", "30m", "15m"], index=0)

    strategy_name = st.sidebar.selectbox("Stratégie", ["Buy & Hold", "Momentum"], index=0)
    lookback = st.sidebar.slider("Lookback (Momentum)", 2, 60, 14)

    # prediction settings
    st.sidebar.header("Prediction")
    pred_horizon = st.sidebar.slider("Prediction horizon", 7, 180, 30)
    pred_lookback = st.sidebar.slider("Prediction lookback", 20, 200, 60)

    # dates par défaut (1 an)
    now = datetime.utcnow()
    default_start = (now - timedelta(days=365)).date()
    default_end = now.date()

    start = st.sidebar.date_input("Start", value=default_start)
    end = st.sidebar.date_input("End", value=default_end)

    run = st.sidebar.button("Run backtest")

    if not run:
        st.info("Choisis tes paramètres à gauche puis clique **Run backtest**.")
        return

    # --- Fetch data
    with st.spinner("Téléchargement des données..."):
        try:
            prices_df = get_prices([symbol], pd.to_datetime(start), pd.to_datetime(end), interval=interval)
        except Exception as e:
            st.error(f"Erreur lors du téléchargement des données : {e}")
            return

    if prices_df is None or symbol not in prices_df.columns:
        st.error("Aucune donnée retournée (vérifie les dates / interval / symbole).")
        return

    prices = prices_df[symbol].dropna()
    if prices.empty:
        st.error("Aucune donnée retournée (vérifie les dates / interval / symbole).")
        return

    # --- Strategy position
    if strategy_name == "Buy & Hold":
        pos = buy_and_hold(prices)
    else:
        pos = momentum(prices, lookback=lookback)

    # --- Backtest
    equity = run_backtest(prices, pos)

    # --- Plot (2 courbes normalisées)
    chart_df = pd.DataFrame(
        {
            "Price": prices / prices.iloc[0],
            "Equity": equity / equity.iloc[0],
        }
    )

    st.subheader("Prix vs Equity (normalisés)")
    st.line_chart(chart_df)

    # --- Metrics
    st.subheader("Metrics")
    st.write("Sharpe:", sharpe_ratio(equity))
    st.write("Max Drawdown:", max_drawdown(equity))

    # --- Prediction (baseline linéaire)
    st.subheader("Prediction (linéaire)")

    try:
        pred = linear_price_prediction(prices, horizon=pred_horizon, lookback=pred_lookback)

        pred_df = pd.DataFrame(
            {
                "Price": prices,
                "Prediction": pred,
            }
        )
        st.line_chart(pred_df)
        st.caption("Baseline: extrapolation linéaire simple sur les derniers points.")
    except Exception as e:
        st.warning(f"Prediction impossible: {e}")

    # Debug optionnel
    with st.expander("🔎 Debug données (get_prices)"):
        st.write("Head:", prices_df.head())
        st.write("Tail:", prices_df.tail())
        st.write("Nb points:", len(prices))
