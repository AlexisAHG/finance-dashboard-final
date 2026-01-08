import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data.fetchers import get_prices
from src.analytics.strategies_univariate import buy_and_hold, momentum
from src.analytics.backtest import run_backtest
from src.analytics.metrics import sharpe_ratio, max_drawdown


def render_single_asset_page():
    st.title("Quant A — Single Asset (BTC/USD)")

    # =========================
    # Sidebar — paramètres
    # =========================
    st.sidebar.header("Paramètres")

    symbol = st.sidebar.selectbox(
        "Asset",
        ["BTC-USD", "ETH-USD"],
        index=0
    )

    interval = st.sidebar.selectbox(
        "Interval",
        ["1d", "1h", "30m", "15m"],
        index=0
    )

    lookback = st.sidebar.slider(
        "Lookback (Momentum)",
        min_value=2,
        max_value=60,
        value=14
    )

    now = datetime.utcnow()
    default_start = (now - timedelta(days=365)).date()
    default_end = now.date()

    start = st.sidebar.date_input("Start", value=default_start)
    end = st.sidebar.date_input("End", value=default_end)

    run = st.sidebar.button("Run backtest")

    if not run:
        st.info("Choisis tes paramètres à gauche puis clique sur **Run backtest**.")
        return

    # =========================
    # Téléchargement des prix
    # =========================
    with st.spinner("Téléchargement des données..."):
        try:
            prices_df = get_prices(
                [symbol],
                pd.to_datetime(start),
                pd.to_datetime(end),
                interval=interval
            )
        except Exception as e:
            st.error(f"Erreur lors du téléchargement des données : {e}")
            return

    if prices_df is None or symbol not in prices_df:
        st.error("Aucune donnée n'a été retournée.")
        return

    prices = prices_df[symbol].dropna()

    if prices.empty or len(prices) < 10:
        st.error("Pas assez de données exploitables.")
        return

    # =========================
    # Backtests — stratégies
    # =========================
    pos_bh = buy_and_hold(prices)
    pos_mom = momentum(prices, lookback=lookback)

    eq_bh = run_backtest(prices, pos_bh)
    eq_mom = run_backtest(prices, pos_mom)

    # =========================
    # Graphique comparatif
    # =========================
    chart_df = pd.DataFrame({
        "Price": prices / prices.iloc[0],
        "Equity (Buy & Hold)": eq_bh / eq_bh.iloc[0],
        "Equity (Momentum)": eq_mom / eq_mom.iloc[0],
    })

    st.subheader("Prix vs Equity (normalisés)")
    st.line_chart(chart_df)

    # =========================
    # Metrics
    # =========================
    metrics_df = pd.DataFrame({
        "Strategy": ["Buy & Hold", "Momentum"],
        "Sharpe": [
            sharpe_ratio(eq_bh),
            sharpe_ratio(eq_mom)
        ],
        "Max Drawdown": [
            max_drawdown(eq_bh),
            max_drawdown(eq_mom)
        ]
    })

    st.subheader("Metrics (comparaison)")
    st.dataframe(metrics_df)

    # =========================
    # BONUS — Prédiction simple
    # =========================
    st.subheader("Bonus — Prédiction simple (régression linéaire)")

    horizon = st.slider("Horizon de prédiction (jours)", 1, 30, 7)
    window = st.slider("Fenêtre d'entraînement (jours)", 30, 365, 90)

    s = prices.dropna()

    if len(s) >= window:
        y = s.iloc[-window:].values
        x = np.arange(len(y))

        a, b = np.polyfit(x, y, 1)

        x_future = np.arange(len(y), len(y) + horizon)
        y_future = a * x_future + b

        pred_index = pd.date_range(
            s.index[-1] + pd.Timedelta(days=1),
            periods=horizon,
            freq="D"
        )

        pred_series = pd.Series(y_future, index=pred_index)

        pred_df = pd.concat([
            s.iloc[-window:],
            pred_series
        ])

        pred_df = pred_df / s.iloc[-window]

        st.line_chart(pred_df)
    else:
        st.warning("Pas assez de données pour la prédiction.")
