"""
Finance Dashboard - Ultimate Version
====================================
- Full Logic Preserved (Modules & Utils)
- Ticker Fixed (Iframe)
- Day/Night Theme Toggle added
"""

import streamlit as st
import streamlit.components.v1 as components # Ajouté pour le ticker
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Import custom modules
from modules.single_asset import SingleAssetAnalysis
from modules.portfolio import PortfolioAnalysis
from utils.data_fetcher import DataFetcher
from utils.metrics import FinancialMetrics

# Page configuration
st.set_page_config(
    page_title="Quant Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- THEME MANAGEMENT (JOUR/NUIT) ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

def toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

# Définition des variables de couleur selon le thème
if st.session_state.theme == 'dark':
    bg_color = "#0e1117"
    nav_bg = "#1a1a2e"
    card_bg = "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)"
    text_color = "#ffffff"
    subtext_color = "#888888"
    border_color = "#333333"
    input_bg = "#1a1a2e"
    theme_icon = "☀️"
    plotly_template = "plotly_dark"
else:
    bg_color = "#f0f2f6"
    nav_bg = "#ffffff"
    card_bg = "linear-gradient(135deg, #ffffff 0%, #f0f2f6 100%)"
    text_color = "#31333F"
    subtext_color = "#555555"
    border_color = "#cccccc"
    input_bg = "#ffffff"
    theme_icon = "🌙"
    plotly_template = "plotly_white"

# Initialize session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = {}
if 'paper_trades' not in st.session_state:
    st.session_state.paper_trades = []
if 'paper_balance' not in st.session_state:
    st.session_state.paper_balance = 1000000.0  # $1M starting
if 'paper_positions' not in st.session_state:
    st.session_state.paper_positions = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Custom CSS for professional look (Dynamique selon le thème)
st.markdown(f"""
<style>
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Main background */
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    
    /* Navigation */
    .nav-container {{
        background: {nav_bg};
        padding: 15px 30px;
        border-radius: 10px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }}
    
    .nav-logo {{
        font-size: 24px;
        font-weight: 700;
        color: {text_color};
    }}
    
    /* Cards */
    .metric-card {{
        background: {card_bg};
        padding: 20px;
        border-radius: 12px;
        border: 1px solid {border_color};
    }}
    
    .metric-card h3 {{
        color: {subtext_color};
        font-size: 14px;
        margin-bottom: 8px;
        font-weight: 400;
    }}
    
    .metric-card .value {{
        color: {text_color};
        font-size: 28px;
        font-weight: 600;
    }}
    
    /* Tables */
    .custom-table th {{
        background: {nav_bg};
        color: {subtext_color};
        border-bottom: 1px solid {border_color};
    }}
    
    .custom-table td {{
        border-bottom: 1px solid {border_color};
        color: {text_color};
    }}
    
    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: 500;
    }}
    
    /* Section headers */
    .section-header {{
        color: {text_color};
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    
    .section-subheader {{
        color: {subtext_color};
        font-size: 14px;
        margin-bottom: 20px;
    }}
    
    /* Inputs */
    .stSelectbox > div > div {{
        background-color: {input_bg};
        border-color: {border_color};
        color: {text_color};
    }}
    
    .stTextInput > div > div > input {{
        background-color: {input_bg};
        border-color: {border_color};
        color: {text_color};
    }}
    
    /* Metrics Global Override */
    [data-testid="stMetricValue"] {{
        color: {text_color} !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: {subtext_color} !important;
    }}
    h1, h2, h3, h4, p, li, span {{
        color: {text_color};
    }}
</style>
""", unsafe_allow_html=True)


def get_ticker_data():
    """Get current prices for ticker bar."""
    fetcher = DataFetcher()
    tickers = ['MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'BTC-USD', 'ETH-USD', 'AAPL']
    ticker_data = []
    
    for symbol in tickers:
        try:
            df = fetcher.get_stock_data(symbol, period="2d", interval="1d")
            if df is not None and len(df) >= 2:
                current = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                ticker_data.append({
                    'symbol': symbol.replace('-USD', ''),
                    'price': current,
                    'change': change
                })
        except:
            pass
    
    return ticker_data


def render_ticker_bar():
    """Render the ticker bar (FIXED VERSION via Iframe)."""
    ticker_data = get_ticker_data()
    
    items_html = ""
    for item in ticker_data:
        color = "#00c853" if item['change'] >= 0 else "#ff5252"
        change_symbol = "▲" if item['change'] >= 0 else "▼"
        items_html += f'''
            <div class="ticker-item">
                <span class="ticker-symbol">{item['symbol']}</span>
                <span class="ticker-price">${item['price']:,.2f}</span>
                <span style="color: {color}; margin-left: 5px;">{change_symbol} {abs(item['change']):.2f}%</span>
            </div>
        '''
    
    # CSS pour l'iframe (adapté au thème)
    iframe_bg = "#1a1a2e" if st.session_state.theme == 'dark' else "#ffffff"
    iframe_text = "#ffffff" if st.session_state.theme == 'dark' else "#000000"
    iframe_border = "#333" if st.session_state.theme == 'dark' else "#ccc"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <style>
            body {{ margin: 0; background-color: {bg_color}; overflow: hidden; font-family: 'Segoe UI', sans-serif; }}
            .ticker-wrap {{
                width: 100%;
                background: {iframe_bg};
                padding: 10px 0;
                border-bottom: 1px solid {iframe_border};
                white-space: nowrap;
                display: flex;
            }}
            .ticker {{
                display: inline-block;
                animation: ticker 40s linear infinite;
            }}
            @keyframes ticker {{
                0% {{ transform: translate3d(0, 0, 0); }}
                100% {{ transform: translate3d(-100%, 0, 0); }}
            }}
            .ticker-item {{
                display: inline-block;
                margin-right: 40px;
                color: {iframe_text};
                font-size: 14px;
            }}
            .ticker-symbol {{ font-weight: 600; }}
            .ticker-price {{ opacity: 0.7; margin-left: 8px; }}
            .ticker-wrap:hover .ticker {{ animation-play-state: paused; }}
        </style>
    </head>
    <body>
        <div class="ticker-wrap">
            <div class="ticker">
                {items_html}
                {items_html}
            </div>
        </div>
    </body>
    </html>
    """
    
    components.html(html_content, height=60, scrolling=False)


def render_navigation():
    """Render the navigation bar with Theme Toggle."""
    col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 0.5])
    
    with col1:
        st.markdown("### 📊 Quant Dashboard")
    
    with col2:
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.current_page = "Dashboard"
            st.rerun()
    
    with col3:
        if st.button("📈 Single Asset", use_container_width=True):
            st.session_state.current_page = "Single Asset"
            st.rerun()
    
    with col4:
        if st.button("💼 Portfolio", use_container_width=True):
            st.session_state.current_page = "Portfolio"
            st.rerun()
    
    with col5:
        if st.button("📝 Paper Trading", use_container_width=True):
            st.session_state.current_page = "Paper Trading"
            st.rerun()
    
    with col6:
        # Theme Toggle Button
        if st.button(theme_icon, use_container_width=True, key="theme_toggle"):
            toggle_theme()
            st.rerun()


def render_dashboard():
    """Render the main dashboard page."""
    st.markdown('<p class="section-header">📊 Market Overview</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subheader">Real-time market data and portfolio summary</p>', unsafe_allow_html=True)
    
    # Market summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    fetcher = DataFetcher()
    
    # S&P 500
    with col1:
        try:
            sp500 = fetcher.get_stock_data('^GSPC', period='2d', interval='1d')
            if sp500 is not None and len(sp500) >= 2:
                current = sp500['Close'].iloc[-1]
                prev = sp500['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                st.metric("S&P 500", f"{current:,.0f}", f"{change:+.2f}%")
        except:
            st.metric("S&P 500", "N/A", "")
    
    # NASDAQ
    with col2:
        try:
            nasdaq = fetcher.get_stock_data('^IXIC', period='2d', interval='1d')
            if nasdaq is not None and len(nasdaq) >= 2:
                current = nasdaq['Close'].iloc[-1]
                prev = nasdaq['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                st.metric("NASDAQ", f"{current:,.0f}", f"{change:+.2f}%")
        except:
            st.metric("NASDAQ", "N/A", "")
    
    # Bitcoin
    with col3:
        try:
            btc = fetcher.get_stock_data('BTC-USD', period='2d', interval='1d')
            if btc is not None and len(btc) >= 2:
                current = btc['Close'].iloc[-1]
                prev = btc['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                st.metric("Bitcoin", f"${current:,.0f}", f"{change:+.2f}%")
        except:
            st.metric("Bitcoin", "N/A", "")
    
    # Gold
    with col4:
        try:
            gold = fetcher.get_stock_data('GC=F', period='2d', interval='1d')
            if gold is not None and len(gold) >= 2:
                current = gold['Close'].iloc[-1]
                prev = gold['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                st.metric("Gold", f"${current:,.0f}", f"{change:+.2f}%")
        except:
            st.metric("Gold", "N/A", "")
    
    st.divider()
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 S&P 500 - 1 Month")
        try:
            sp500_data = fetcher.get_stock_data('^GSPC', period='1mo', interval='1d')
            if sp500_data is not None:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=sp500_data.index,
                    y=sp500_data['Close'],
                    fill='tozeroy',
                    line=dict(color='#667eea', width=2),
                    fillcolor='rgba(102, 126, 234, 0.2)'
                ))
                fig.update_layout(
                    height=300,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    template=plotly_template, # Theme support
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
                )
                st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Unable to load chart")
    
    with col2:
        st.markdown("#### 🪙 Bitcoin - 1 Month")
        try:
            btc_data = fetcher.get_stock_data('BTC-USD', period='1mo', interval='1d')
            if btc_data is not None:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=btc_data.index,
                    y=btc_data['Close'],
                    fill='tozeroy',
                    line=dict(color='#f7931a', width=2),
                    fillcolor='rgba(247, 147, 26, 0.2)'
                ))
                fig.update_layout(
                    height=300,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    template=plotly_template, # Theme support
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
                )
                st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Unable to load chart")
    
    # Top movers
    st.divider()
    st.markdown("#### 🔥 Top Movers Today")
    
    movers_data = []
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'META', 'AMZN', 'AMD']
    
    for symbol in symbols:
        try:
            df = fetcher.get_stock_data(symbol, period='2d', interval='1d')
            if df is not None and len(df) >= 2:
                current = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                volume = df['Volume'].iloc[-1]
                movers_data.append({
                    'Symbol': symbol,
                    'Price': f"${current:.2f}",
                    'Change': change,
                    'Volume': f"{volume/1e6:.1f}M"
                })
        except:
            pass
    
    if movers_data:
        movers_df = pd.DataFrame(movers_data)
        movers_df = movers_df.sort_values('Change', key=abs, ascending=False)
        
        # Display as formatted table
        for i, row in movers_df.head(8).iterrows():
            cols = st.columns(4)
            cols[0].write(row['Symbol'])
            cols[1].write(row['Price'])
            change_color = "🟢" if row['Change'] >= 0 else "🔴"
            cols[2].write(f"{change_color} {row['Change']:+.2f}%")
            cols[3].write(row['Volume'])


def render_single_asset():
    """Render the single asset analysis page."""
    st.markdown('<p class="section-header">📈 Single Asset Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subheader">Analyze individual assets with backtesting strategies</p>', unsafe_allow_html=True)
    
    # Controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        asset_category = st.selectbox(
            "Category",
            ["Stocks", "Crypto", "Forex", "Commodities", "French Stocks"]
        )
    
    asset_options = {
        "Stocks": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "AMD"],
        "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD"],
        "Forex": ["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
        "Commodities": ["GC=F", "SI=F", "CL=F"],
        "French Stocks": ["ENGI.PA", "TTE.PA", "AIR.PA", "BNP.PA", "SAN.PA"]
    }
    
    with col2:
        selected_asset = st.selectbox("Asset", asset_options[asset_category])
    
    with col3:
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
    
    with col4:
        strategy = st.selectbox(
            "Strategy",
            ["Buy and Hold", "Moving Average Crossover", "RSI Strategy", "Momentum"]
        )
    
    # Fetch data
    fetcher = DataFetcher()
    
    with st.spinner(f"Loading {selected_asset} data..."):
        df = fetcher.get_stock_data(selected_asset, period=period, interval="1d")
    
    if df is not None and not df.empty:
        # Current price metrics
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        price_change = ((current_price - prev_price) / prev_price) * 100
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Current Price", f"${current_price:.2f}", f"{price_change:+.2f}%")
        col2.metric("Open", f"${df['Open'].iloc[-1]:.2f}")
        col3.metric("High", f"${df['High'].iloc[-1]:.2f}")
        col4.metric("Low", f"${df['Low'].iloc[-1]:.2f}")
        vol = df['Volume'].iloc[-1]
        col5.metric("Volume", f"{vol/1e6:.2f}M" if vol >= 1e6 else f"{vol/1e3:.0f}K")
        
        st.divider()
        
        # Strategy parameters
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("#### ⚙️ Strategy Parameters")
            
            initial_capital = st.number_input("Initial Capital ($)", 1000, 1000000, 10000, 1000)
            
            if strategy == "Moving Average Crossover":
                short_window = st.slider("Short MA", 5, 50, 20)
                long_window = st.slider("Long MA", 20, 200, 50)
            elif strategy == "RSI Strategy":
                rsi_period = st.slider("RSI Period", 5, 30, 14)
                rsi_oversold = st.slider("Oversold", 20, 40, 30)
                rsi_overbought = st.slider("Overbought", 60, 80, 70)
            elif strategy == "Momentum":
                momentum_period = st.slider("Lookback", 5, 60, 20)
        
        # Run strategy
        analyzer = SingleAssetAnalysis(df, initial_capital)
        
        if strategy == "Buy and Hold":
            strategy_df = analyzer.buy_and_hold()
        elif strategy == "Moving Average Crossover":
            strategy_df = analyzer.ma_crossover(short_window, long_window)
        elif strategy == "RSI Strategy":
            strategy_df = analyzer.rsi_strategy(rsi_period, rsi_oversold, rsi_overbought)
        else:
            strategy_df = analyzer.momentum_strategy(momentum_period)
        
        metrics = FinancialMetrics.calculate_metrics(strategy_df, initial_capital)
        
        with col2:
            st.markdown("#### 📊 Performance Metrics")
            
            met_cols = st.columns(4)
            met_cols[0].metric("Total Return", f"{metrics['total_return']:.2f}%")
            met_cols[1].metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.3f}")
            met_cols[2].metric("Max Drawdown", f"{metrics['max_drawdown']:.2f}%")
            met_cols[3].metric("Final Value", f"${metrics['final_value']:,.2f}")
        
        # Main chart
        st.markdown("#### 📉 Price & Strategy Performance")
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # Price
        fig.add_trace(
            go.Scatter(
                x=strategy_df.index,
                y=strategy_df['Close'],
                name='Price',
                line=dict(color='#667eea', width=2)
            ),
            row=1, col=1
        )
        
        # Strategy value normalized
        normalized_strategy = strategy_df['Strategy_Value'] / strategy_df['Strategy_Value'].iloc[0] * strategy_df['Close'].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=strategy_df.index,
                y=normalized_strategy,
                name=strategy,
                line=dict(color='#00c853', width=2)
            ),
            row=1, col=1
        )
        
        # Volume
        colors = ['#ff5252' if strategy_df['Close'].iloc[i] < strategy_df['Open'].iloc[i] 
                 else '#00c853' for i in range(len(strategy_df))]
        
        fig.add_trace(
            go.Bar(x=strategy_df.index, y=strategy_df['Volume'], marker_color=colors, opacity=0.7),
            row=2, col=1
        )
        
        fig.update_layout(
            height=500,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            template=plotly_template, # Theme support
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
            xaxis2=dict(showgrid=False),
            yaxis2=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Unable to fetch data. Please try a different asset.")


def render_portfolio():
    """Render the portfolio analysis page."""
    st.markdown('<p class="section-header">💼 Portfolio Analysis</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subheader">Multi-asset portfolio management and optimization</p>', unsafe_allow_html=True)
    
    # Portfolio selection
    col1, col2, col3 = st.columns(3)
    
    with col1:
        portfolio_type = st.selectbox(
            "Portfolio",
            ["Tech Giants", "Diversified", "Crypto Mix", "French CAC40", "Custom"]
        )
    
    portfolio_map = {
        "Tech Giants": ["AAPL", "GOOGL", "MSFT", "NVDA"],
        "Diversified": ["AAPL", "GC=F", "BTC-USD", "EURUSD=X"],
        "Crypto Mix": ["BTC-USD", "ETH-USD", "SOL-USD"],
        "French CAC40": ["ENGI.PA", "TTE.PA", "AIR.PA", "BNP.PA"]
    }
    
    if portfolio_type == "Custom":
        all_assets = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN",
                     "BTC-USD", "ETH-USD", "GC=F", "EURUSD=X", "ENGI.PA", "TTE.PA"]
        selected_assets = st.multiselect("Select Assets (min 3)", all_assets, default=["AAPL", "GOOGL", "MSFT"])
    else:
        selected_assets = portfolio_map[portfolio_type]
    
    with col2:
        period = st.selectbox("Period", ["3mo", "6mo", "1y", "2y"], index=2, key="port_period")
    
    with col3:
        allocation = st.selectbox("Allocation", ["Equal Weight", "Risk Parity", "Custom"])
    
    if len(selected_assets) < 3:
        st.warning("⚠️ Please select at least 3 assets")
        return
    
    # Fetch data
    fetcher = DataFetcher()
    
    with st.spinner("Loading portfolio data..."):
        portfolio_data = {}
        for asset in selected_assets:
            df = fetcher.get_stock_data(asset, period=period, interval="1d")
            if df is not None and not df.empty:
                portfolio_data[asset] = df['Close']
    
    if len(portfolio_data) < 3:
        st.error("Unable to fetch enough data")
        return
    
    portfolio_df = pd.DataFrame(portfolio_data).dropna()
    
    # Calculate weights
    if allocation == "Equal Weight":
        weights = {asset: 1/len(selected_assets) for asset in selected_assets}
    elif allocation == "Risk Parity":
        returns = portfolio_df.pct_change().dropna()
        vols = returns.std()
        inv_vol = 1 / vols
        weights = (inv_vol / inv_vol.sum()).to_dict()
    else:
        weights = {asset: 1/len(selected_assets) for asset in selected_assets}
    
    # Portfolio metrics
    analyzer = PortfolioAnalysis(portfolio_df, weights, 100000)
    portfolio_value, metrics = analyzer.calculate_portfolio_value()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Portfolio Value", f"${portfolio_value.iloc[-1]:,.0f}")
    col2.metric("Total Return", f"{metrics['total_return']:.2f}%")
    col3.metric("Volatility", f"{metrics['portfolio_volatility']:.2f}%")
    col4.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.3f}")
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Asset Performance (Normalized)")
        
        normalized = portfolio_df / portfolio_df.iloc[0] * 100
        
        fig = go.Figure()
        colors = ['#667eea', '#00c853', '#ff9800', '#e91e63', '#00bcd4']
        
        for i, asset in enumerate(selected_assets):
            if asset in normalized.columns:
                fig.add_trace(go.Scatter(
                    x=normalized.index,
                    y=normalized[asset],
                    name=asset,
                    line=dict(color=colors[i % len(colors)], width=2)
                ))
        
        # Portfolio
        norm_portfolio = portfolio_value / portfolio_value.iloc[0] * 100
        fig.add_trace(go.Scatter(
            x=norm_portfolio.index,
            y=norm_portfolio,
            name='Portfolio',
            line=dict(color='#ffd700', width=3)
        ))
        
        fig.update_layout(
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            template=plotly_template, # Theme support
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🥧 Portfolio Allocation")
        
        fig = go.Figure(data=[go.Pie(
            labels=list(weights.keys()),
            values=list(weights.values()),
            hole=0.5,
            marker_colors=['#667eea', '#00c853', '#ff9800', '#e91e63', '#00bcd4']
        )])
        
        fig.update_layout(
            height=350,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=True,
            legend=dict(font=dict(color=subtext_color))
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Correlation matrix
    st.markdown("#### 🔗 Correlation Matrix")
    
    returns = portfolio_df.pct_change().dropna()
    corr = returns.corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.index,
        colorscale='RdBu',
        zmid=0
    ))
    
    fig.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_paper_trading():
    """Render the paper trading page."""
    st.markdown('<p class="section-header">📝 Paper Trading</p>', unsafe_allow_html=True)
    st.markdown('<p class="section-subheader">Practice trading with virtual money</p>', unsafe_allow_html=True)
    
    fetcher = DataFetcher()
    
    # Calculate total portfolio value
    total_invested = 0
    positions_value = 0
    
    for symbol, data in st.session_state.paper_positions.items():
        try:
            df = fetcher.get_stock_data(symbol, period='1d', interval='1m')
            if df is not None:
                current_price = df['Close'].iloc[-1]
                positions_value += current_price * data['quantity']
                total_invested += data['avg_price'] * data['quantity']
        except:
            positions_value += data['avg_price'] * data['quantity']
            total_invested += data['avg_price'] * data['quantity']
    
    total_value = st.session_state.paper_balance + positions_value
    total_pnl = total_value - 1000000
    
    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total Portfolio Value", f"${total_value:,.2f}", f"${total_pnl:+,.2f}")
    col2.metric("Cash Balance", f"${st.session_state.paper_balance:,.2f}", "Available to trade")
    col3.metric("Total Invested", f"${total_invested:,.2f}", f"{len(st.session_state.paper_positions)} position(s)")
    col4.metric("Total Trades", f"{len(st.session_state.paper_trades)}", "Executed trades")
    
    st.divider()
    
    # New trade form
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### ➕ New Trade")
        
        trade_symbol = st.selectbox(
            "Symbol",
            ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "META", "AMZN", "BTC-USD", "ETH-USD"]
        )
        
        trade_action = st.radio("Action", ["Buy", "Sell"], horizontal=True)
        trade_quantity = st.number_input("Quantity", min_value=1, value=10)
        
        # Get current price
        try:
            df = fetcher.get_stock_data(trade_symbol, period='1d', interval='1m')
            if df is not None:
                current_price = df['Close'].iloc[-1]
                st.info(f"Current Price: ${current_price:.2f}")
                total_cost = current_price * trade_quantity
                st.info(f"Total: ${total_cost:,.2f}")
        except:
            current_price = 100
            st.warning("Unable to fetch current price")
        
        if st.button("Execute Trade", use_container_width=True):
            if trade_action == "Buy":
                if st.session_state.paper_balance >= total_cost:
                    st.session_state.paper_balance -= total_cost
                    
                    if trade_symbol in st.session_state.paper_positions:
                        pos = st.session_state.paper_positions[trade_symbol]
                        new_qty = pos['quantity'] + trade_quantity
                        new_avg = (pos['avg_price'] * pos['quantity'] + current_price * trade_quantity) / new_qty
                        st.session_state.paper_positions[trade_symbol] = {
                            'quantity': new_qty,
                            'avg_price': new_avg
                        }
                    else:
                        st.session_state.paper_positions[trade_symbol] = {
                            'quantity': trade_quantity,
                            'avg_price': current_price
                        }
                    
                    st.session_state.paper_trades.append({
                        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'symbol': trade_symbol,
                        'action': 'BUY',
                        'quantity': trade_quantity,
                        'price': current_price
                    })
                    
                    st.success(f"✅ Bought {trade_quantity} {trade_symbol} @ ${current_price:.2f}")
                    st.rerun()
                else:
                    st.error("❌ Insufficient funds")
            
            else:  # Sell
                if trade_symbol in st.session_state.paper_positions:
                    pos = st.session_state.paper_positions[trade_symbol]
                    if pos['quantity'] >= trade_quantity:
                        st.session_state.paper_balance += current_price * trade_quantity
                        pos['quantity'] -= trade_quantity
                        
                        if pos['quantity'] == 0:
                            del st.session_state.paper_positions[trade_symbol]
                        
                        st.session_state.paper_trades.append({
                            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'symbol': trade_symbol,
                            'action': 'SELL',
                            'quantity': trade_quantity,
                            'price': current_price
                        })
                        
                        st.success(f"✅ Sold {trade_quantity} {trade_symbol} @ ${current_price:.2f}")
                        st.rerun()
                    else:
                        st.error(f"❌ Not enough shares (you have {pos['quantity']})")
                else:
                    st.error("❌ No position in this asset")
    
    with col2:
        st.markdown("#### 📊 Active Positions")
        
        if st.session_state.paper_positions:
            positions_data = []
            
            for symbol, data in st.session_state.paper_positions.items():
                try:
                    df = fetcher.get_stock_data(symbol, period='1d', interval='1m')
                    if df is not None:
                        current_price = df['Close'].iloc[-1]
                    else:
                        current_price = data['avg_price']
                except:
                    current_price = data['avg_price']
                
                total_value = current_price * data['quantity']
                pnl = (current_price - data['avg_price']) * data['quantity']
                pnl_pct = ((current_price / data['avg_price']) - 1) * 100
                
                positions_data.append({
                    'Symbol': symbol,
                    'Quantity': data['quantity'],
                    'Avg Price': f"${data['avg_price']:.2f}",
                    'Current Price': f"${current_price:.2f}",
                    'Total Value': f"${total_value:,.2f}",
                    'P&L': f"${pnl:+,.2f} ({pnl_pct:+.2f}%)"
                })
            
            positions_df = pd.DataFrame(positions_data)
            st.dataframe(positions_df, use_container_width=True, hide_index=True)
        else:
            st.info("No active positions. Make your first trade!")
        
        st.markdown("#### 📜 Trade History")
        
        if st.session_state.paper_trades:
            trades_df = pd.DataFrame(st.session_state.paper_trades[-10:][::-1])
            trades_df.columns = ['Date', 'Symbol', 'Action', 'Quantity', 'Price']
            trades_df['Price'] = trades_df['Price'].apply(lambda x: f"${x:.2f}")
            st.dataframe(trades_df, use_container_width=True, hide_index=True)
        else:
            st.info("No trades yet")
    
    # Reset button
    st.divider()
    if st.button("🔄 Reset Paper Trading Account"):
        st.session_state.paper_balance = 1000000.0
        st.session_state.paper_positions = {}
        st.session_state.paper_trades = []
        st.success("Account reset to $1,000,000")
        st.rerun()


def main():
    """Main application function."""
    
    # Render ticker bar (REPAIRED)
    render_ticker_bar()
    
    # Render navigation (THEME TOGGLE ADDED)
    render_navigation()
    
    st.divider()
    
    # Render current page
    if st.session_state.current_page == "Dashboard":
        render_dashboard()
    elif st.session_state.current_page == "Single Asset":
        render_single_asset()
    elif st.session_state.current_page == "Portfolio":
        render_portfolio()
    elif st.session_state.current_page == "Paper Trading":
        render_paper_trading()
    
    # Auto-refresh
    time_diff = (datetime.now() - st.session_state.last_refresh).seconds
    if time_diff >= 300:
        st.session_state.last_refresh = datetime.now()
        st.rerun()


if __name__ == "__main__":
    main()