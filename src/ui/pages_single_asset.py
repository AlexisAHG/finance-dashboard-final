import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from src.data.fetchers import get_prices
from src.analytics.strategies_univariate import buy_and_hold, momentum
from src.analytics.backtest import run_backtest
from src.analytics.metrics import sharpe_ratio, max_drawdown


def render_single_asset_page():
    st.title("Quant A — Single Asset (BTC/USD)")

    # --- Sidebar controls
    st.sidebar.header("Paramètres")

    symbol = st.sidebar.selectbox("Asset", ["BTC-USD", "ETH-USD", "EUR/USD"], index=0)
    interval = st.sidebar.selectbox("Interval", ["1d", "1h", "30m", "15m"], index=0)

    strategy_name = st.sidebar.selectbox("Stratégie", ["Buy & Hold", "Momentum"], index=0)

    lookback = None
    if strategy_name == "Momentum":
        lookback = st.sidebar.slider("Lookback (Momentum)", 2, 60, 14)

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

    if pd.to_datetime(start) >= pd.to_datetime(end):
        st.error("Start doit être avant End.")
        return

    # --- Download data
    try:
        with st.spinner("Téléchargement des données..."):
            prices_df = get_prices([symbol], pd.to_datetime(start), pd.to_datetime(end), interval=interval)
    except Exception as e:
        st.error(f"Erreur lors du téléchargement des données : {e}")
        return

    # --- DEBUG (si ça re-bloque, tu verras direct ce que get_prices renvoie)
    with st.expander("🔎 Debug données (get_prices)", expanded=False):
        st.write("shape:", prices_df.shape)
        st.write("columns:", list(prices_df.columns))
        st.write("head:", prices_df.head())
        st.write("tail:", prices_df.tail())

    # --- Extract series
    if symbol not in prices_df.columns:
        st.error(f"La colonne '{symbol}' n'existe pas dans le DataFrame.")
        return

    prices = prices_df[symbol].dropna()

    if prices.empty:
        st.error("Aucune donnée retournée (vérifie les dates / interval / symbole).")
        return

    # --- Strategy position
    if strategy_name == "Buy & Hold":
        pos = buy_and_hold(prices)
    else:
        pos = momentum(prices, lookback=int(lookback))

    # --- Backtest
    equity = run_backtest(prices, pos)

    if equity is None or len(equity) == 0:
        st.error("Equity vide: problème dans run_backtest ou position.")
        return

    # --- Plot (2 courbes normalisées)
    chart_df = pd.DataFrame({
        "Price": prices / prices.iloc[0],
        "Equity": equity / equity.iloc[0],
    }).dropna()

    st.subheader("Prix vs Equity (normalisés)")
    st.line_chart(chart_df)

    # --- Metrics
    st.subheader("Metrics")
    st.write("Sharpe:", sharpe_ratio(equity))
    st.write("Max Drawdown:", max_drawdown(equity))
