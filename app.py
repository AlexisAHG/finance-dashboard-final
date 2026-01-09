"""
Quant Dashboard Pro - Enhanced UI
=================================
Same logic as original, with professional CSS design
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pytz

from modules.single_asset import SingleAssetAnalysis
from modules.portfolio import PortfolioAnalysis
from utils.data_fetcher import DataFetcher
from utils.metrics import FinancialMetrics

st.set_page_config(
    page_title="Quant Dashboard Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'paper_trades' not in st.session_state:
    st.session_state.paper_trades = []
if 'paper_balance' not in st.session_state:
    st.session_state.paper_balance = 1000000.0
if 'paper_positions' not in st.session_state:
    st.session_state.paper_positions = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# ============================================================
# PRO CSS - Style Quant Terminal Pro
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', -apple-system, sans-serif; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
    background: linear-gradient(180deg, #0a0e14 0%, #111820 100%);
    color: #f1f5f9;
}

.main .block-container {
    max-width: 1400px;
    padding-top: 1rem !important;
}

/* HEADER GRADIENT */
.pro-header {
    text-align: center;
    padding: 30px 0 20px 0;
}
.pro-title {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00d4aa 0%, #6366f1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 5px;
}
.pro-subtitle {
    color: #64748b;
    font-size: 1rem;
    font-weight: 400;
}

/* MARKET STATUS */
.status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: #111820;
    border-radius: 10px;
    margin-bottom: 20px;
    border: 1px solid #1e293b;
}
.status-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 10px;
    animation: pulse 2s infinite;
}
.status-dot.open { background: #10b981; box-shadow: 0 0 10px rgba(16,185,129,0.5); }
.status-dot.closed { background: #ef4444; box-shadow: 0 0 10px rgba(239,68,68,0.5); }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }

/* CARDS PRO */
.card-pro {
    background: #111820;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
    border-left: 3px solid #00d4aa;
    margin-bottom: 10px;
}
.card-pro:hover {
    border-color: rgba(0,212,170,0.3);
    box-shadow: 0 8px 32px rgba(0,212,170,0.1);
    transform: translateY(-2px);
}
.card-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #64748b;
    margin-bottom: 8px;
}
.card-value {
    font-size: 28px;
    font-weight: 700;
    color: #f1f5f9;
}
.card-change { font-size: 13px; font-weight: 500; margin-top: 4px; }
.card-up { color: #10b981; }
.card-down { color: #ef4444; }

/* SECTION TITLE */
.section-title {
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
    margin: 20px 0 16px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, #1e293b 0%, transparent 100%);
}

/* BUTTONS */
.stButton > button {
    background: linear-gradient(135deg, #00d4aa 0%, #6366f1 100%);
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 10px 24px;
    transition: all 0.3s;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0,212,170,0.4);
}

/* METRICS */
[data-testid="stMetricValue"] { font-size: 24px; color: #f1f5f9 !important; }
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 12px; text-transform: uppercase; }

/* TABLES */
.stDataFrame { background: #111820 !important; }
div[data-testid="stDataFrame"] > div { background: #111820; border-radius: 10px; }

/* SELECTBOX */
.stSelectbox > div > div { background: #1a2332; border-color: #1e293b; }
div[data-baseweb="select"] > div { background: #1a2332 !important; }

/* Fix colors */
h1, h2, h3, h4, p, span, div, label { color: #f1f5f9; }
</style>
""", unsafe_allow_html=True)


def is_market_open():
    """Check if US market is open."""
    paris = pytz.timezone('Europe/Paris')
    now = datetime.now(paris)
    if now.weekday() >= 5:
        return False
    if now.hour >= 15 and now.hour < 22:
        return True
    return False


def get_ticker_data():
    """Get ticker data."""
    fetcher = DataFetcher()
    tickers = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'BTC-USD', 'ETH-USD', 'AMZN']
    data = []
    for sym in tickers:
        try:
            df = fetcher.get_stock_data(sym, period="2d", interval="1d")
            if df is not None and len(df) >= 2:
                curr = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                chg = ((curr - prev) / prev) * 100
                data.append({'symbol': sym.replace('-USD', ''), 'price': curr, 'change': chg})
        except:
            pass
    return data


def render_ticker_bar():
    """Render animated ticker."""
    ticker_data = get_ticker_data()
    items_html = ""
    for item in ticker_data:
        color = "#10b981" if item['change'] >= 0 else "#ef4444"
        arrow = "▲" if item['change'] >= 0 else "▼"
        items_html += f'<div class="ticker-item"><span class="ticker-sym">{item["symbol"]}</span><span class="ticker-price">${item["price"]:,.2f}</span><span style="color:{color};margin-left:5px;">{arrow} {abs(item["change"]):.2f}%</span></div>'
    
    html = f"""
    <!DOCTYPE html><html><head><style>
    body {{ margin:0; background:#0a0e14; overflow:hidden; font-family:'Inter',sans-serif; }}
    .ticker-wrap {{ width:100%; background:linear-gradient(90deg,#111820 0%,#1a2332 50%,#111820 100%); padding:12px 0; border-bottom:1px solid #1e293b; white-space:nowrap; display:flex; }}
    .ticker {{ display:inline-block; animation:scroll 60s linear infinite; }}
    @keyframes scroll {{ 0%{{transform:translateX(0);}} 100%{{transform:translateX(-50%);}} }}
    .ticker-item {{ display:inline-block; margin:0 30px; font-size:13px; }}
    .ticker-sym {{ font-weight:600; color:#f1f5f9; }}
    .ticker-price {{ color:#94a3b8; margin-left:8px; }}
    .ticker-wrap:hover .ticker {{ animation-play-state:paused; }}
    </style></head><body>
    <div class="ticker-wrap"><div class="ticker">{items_html}{items_html}</div></div>
    </body></html>
    """
    components.html(html, height=50, scrolling=False)


def render_header():
    """Render pro header."""
    st.markdown("""
        <div class="pro-header">
            <div class="pro-title">Quant Dashboard Pro</div>
            <div class="pro-subtitle">Professional Quantitative Analysis Platform</div>
        </div>
    """, unsafe_allow_html=True)


def render_status_bar():
    """Render market status."""
    paris = pytz.timezone('Europe/Paris')
    now = datetime.now(paris)
    market_open = is_market_open()
    
    status_class = "open" if market_open else "closed"
    status_text = "MARKET OPEN" if market_open else "MARKET CLOSED"
    status_color = "#10b981" if market_open else "#ef4444"
    
    st.markdown(f"""
        <div class="status-bar">
            <div>
                <span class="status-dot {status_class}"></span>
                <span style="font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:1px;color:{status_color};">{status_text}</span>
            </div>
            <div style="color:#94a3b8;font-size:14px;">
                <span style="font-weight:600;color:#f1f5f9;">{now.strftime('%H:%M')}</span> · {now.strftime('%A, %d %B')} · <span style="color:#00d4aa;font-weight:600;">PARIS</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_navigation():
    """Render navigation."""
    cols = st.columns([2.5, 1, 1, 1, 1])
    
    with cols[0]:
        st.markdown("### 📊 Quant Dashboard Pro")
    
    pages = [("Dashboard", "🏠"), ("Single Asset", "📈"), ("Portfolio", "💼"), ("Paper Trading", "📝")]
    for i, (name, icon) in enumerate(pages):
        with cols[i + 1]:
            btn_type = "primary" if st.session_state.current_page == name else "secondary"
            if st.button(f"{icon} {name}", use_container_width=True, type=btn_type, key=f"nav_{name}"):
                st.session_state.current_page = name
                st.rerun()


def render_dashboard():
    """Dashboard page."""
    st.markdown('<div class="section-title">📊 Market Overview</div>', unsafe_allow_html=True)
    
    fetcher = DataFetcher()
    
    cols = st.columns(4)
    indices = [(cols[0], "^GSPC", "S&P 500", "🇺🇸"), (cols[1], "^IXIC", "NASDAQ 100", "💻"), (cols[2], "BTC-USD", "Bitcoin", "₿"), (cols[3], "GC=F", "Gold", "🥇")]
    
    for col, sym, name, icon in indices:
        with col:
            try:
                df = fetcher.get_stock_data(sym, period='2d', interval='1d')
                if df is not None and len(df) >= 2:
                    curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
                    chg = ((curr - prev) / prev) * 100
                    chg_class = "card-up" if chg >= 0 else "card-down"
                    arrow = "↑" if chg >= 0 else "↓"
                    st.markdown(f"""
                        <div class="card-pro">
                            <div class="card-label">{icon} {name}</div>
                            <div class="card-value">${curr:,.2f}</div>
                            <div class="card-change {chg_class}">{arrow} {abs(chg):.2f}%</div>
                        </div>
                    """, unsafe_allow_html=True)
            except:
                st.metric(name, "N/A")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 S&P 500 (3M)")
        try:
            df = fetcher.get_stock_data('^GSPC', period='3mo', interval='1d')
            if df is not None:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], fill='tozeroy', line=dict(color='#00d4aa', width=2), fillcolor='rgba(0,212,170,0.1)'))
                fig.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, color='#64748b'), yaxis=dict(showgrid=True, gridcolor='#1e293b', color='#64748b'))
                st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Unable to load")
    
    with col2:
        st.markdown("#### 🪙 Bitcoin (3M)")
        try:
            df = fetcher.get_stock_data('BTC-USD', period='3mo', interval='1d')
            if df is not None:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], fill='tozeroy', line=dict(color='#f7931a', width=2), fillcolor='rgba(247,147,26,0.1)'))
                fig.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, color='#64748b'), yaxis=dict(showgrid=True, gridcolor='#1e293b', color='#64748b'))
                st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Unable to load")
    
    st.markdown('<div class="section-title">🔥 Market Movers</div>', unsafe_allow_html=True)
    
    movers = []
    for sym in ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'META', 'AMZN', 'AMD']:
        try:
            df = fetcher.get_stock_data(sym, period='2d', interval='1d')
            if df is not None and len(df) >= 2:
                curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
                movers.append({'Symbol': sym, 'Price': f"${curr:.2f}", 'Change': ((curr-prev)/prev)*100, 'Volume': f"{df['Volume'].iloc[-1]/1e6:.1f}M"})
        except:
            pass
    
    if movers:
        mdf = pd.DataFrame(movers).sort_values('Change', key=abs, ascending=False)
        mdf['Status'] = mdf['Change'].apply(lambda x: '🟢 BULLISH' if x >= 0 else '🔴 BEARISH')
        mdf['Change'] = mdf['Change'].apply(lambda x: f"{x:+.2f}%")
        st.dataframe(mdf, use_container_width=True, hide_index=True)


def render_single_asset():
    """Single Asset page - SAME LOGIC AS ORIGINAL."""
    st.markdown('<div class="section-title">📈 Single Asset Analysis</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        category = st.selectbox("Category", ["Stocks", "Crypto", "Forex", "Commodities", "French Stocks"])
    
    opts = {
        "Stocks": ["AAPL","GOOGL","MSFT","AMZN","TSLA","NVDA","META","AMD"],
        "Crypto": ["BTC-USD","ETH-USD","SOL-USD","ADA-USD"],
        "Forex": ["EURUSD=X","GBPUSD=X","USDJPY=X"],
        "Commodities": ["GC=F","SI=F","CL=F"],
        "French Stocks": ["ENGI.PA","TTE.PA","AIR.PA","BNP.PA","SAN.PA"]
    }
    
    with col2:
        asset = st.selectbox("Asset", opts[category])
    with col3:
        period = st.selectbox("Period", ["1mo","3mo","6mo","1y","2y"], index=3)
    with col4:
        strategy = st.selectbox("Strategy", ["Buy and Hold", "Moving Average Crossover", "RSI Strategy", "Momentum"])
    
    fetcher = DataFetcher()
    
    with st.spinner("Loading data..."):
        df = fetcher.get_stock_data(asset, period=period, interval="1d")
    
    if df is None or df.empty:
        st.error("Unable to fetch data")
        return
    
    curr = df['Close'].iloc[-1]
    prev = df['Close'].iloc[-2] if len(df) > 1 else curr
    chg = curr - prev
    chg_pct = (chg / prev) * 100
    
    # Price metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Current Price", f"${curr:.2f}", f"{chg_pct:+.2f}%")
    col2.metric("Open", f"${df['Open'].iloc[-1]:.2f}")
    col3.metric("High", f"${df['High'].iloc[-1]:.2f}")
    col4.metric("Low", f"${df['Low'].iloc[-1]:.2f}")
    col5.metric("Volume", f"{df['Volume'].iloc[-1]/1e6:.1f}M")
    
    st.divider()
    
    # Strategy controls and metrics
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("#### ⚙️ Strategy Parameters")
        capital = st.number_input("Initial Capital ($)", 1000, 1000000, 10000, 1000)
        
        if strategy == "Moving Average Crossover":
            short_ma = st.slider("Short MA", 5, 50, 20)
            long_ma = st.slider("Long MA", 20, 200, 50)
        elif strategy == "RSI Strategy":
            rsi_period = st.slider("RSI Period", 5, 30, 14)
            rsi_os = st.slider("Oversold", 20, 40, 30)
            rsi_ob = st.slider("Overbought", 60, 80, 70)
        elif strategy == "Momentum":
            mom_period = st.slider("Lookback", 5, 60, 20)
    
    # Run strategy
    analyzer = SingleAssetAnalysis(df, capital)
    
    if strategy == "Buy and Hold":
        result = analyzer.buy_and_hold()
    elif strategy == "Moving Average Crossover":
        result = analyzer.ma_crossover(short_ma, long_ma)
    elif strategy == "RSI Strategy":
        result = analyzer.rsi_strategy(rsi_period, rsi_os, rsi_ob)
    else:
        result = analyzer.momentum_strategy(mom_period)
    
    metrics = FinancialMetrics.calculate_metrics(result, capital)
    
    with col2:
        st.markdown("#### 📊 Performance Metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Return", f"{metrics['total_return']:.2f}%")
        m2.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.3f}")
        m3.metric("Max Drawdown", f"{metrics['max_drawdown']:.2f}%")
        m4.metric("Final Value", f"${metrics['final_value']:,.0f}")
    
    # Main chart
    st.markdown(f'<div class="section-title">📈 Price & Strategy Performance ({strategy})</div>', unsafe_allow_html=True)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])
    
    # Price line
    fig.add_trace(go.Scatter(x=result.index, y=result['Close'], name='Price', line=dict(color='#00d4aa', width=2)), row=1, col=1)
    
    # Strategy line (normalized to price scale)
    norm = result['Strategy_Value']/result['Strategy_Value'].iloc[0]*result['Close'].iloc[0]
    fig.add_trace(go.Scatter(x=result.index, y=norm, name=strategy, line=dict(color='#6366f1', width=2)), row=1, col=1)
    
    # Volume bars
    colors = ['#ef4444' if result['Close'].iloc[i]<result['Open'].iloc[i] else '#10b981' for i in range(len(result))]
    fig.add_trace(go.Bar(x=result.index, y=result['Volume'], marker_color=colors, opacity=0.7, showlegend=False), row=2, col=1)
    
    fig.update_layout(height=500, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=1.02, font=dict(color='#94a3b8')), margin=dict(l=0,r=0,t=30,b=0))
    fig.update_xaxes(showgrid=False, color='#64748b')
    fig.update_yaxes(showgrid=True, gridcolor='#1e293b', color='#64748b')
    
    st.plotly_chart(fig, use_container_width=True)


def render_portfolio():
    """Portfolio page - SAME LOGIC AS ORIGINAL."""
    st.markdown('<div class="section-title">💼 Portfolio Analysis</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ptype = st.selectbox("Portfolio", ["Tech Giants", "Diversified", "Crypto Mix", "French Stocks", "Custom"])
    
    portfolios = {
        "Tech Giants": ["AAPL","GOOGL","MSFT","NVDA"],
        "Diversified": ["AAPL","GC=F","BTC-USD"],
        "Crypto Mix": ["BTC-USD","ETH-USD","SOL-USD"],
        "French Stocks": ["ENGI.PA","TTE.PA","AIR.PA"]
    }
    
    if ptype == "Custom":
        assets = st.multiselect("Assets", ["AAPL","GOOGL","MSFT","TSLA","NVDA","META","AMZN","BTC-USD","ETH-USD","GC=F","ENGI.PA","TTE.PA"], default=["AAPL","GOOGL","MSFT"])
    else:
        assets = portfolios[ptype]
    
    with col2:
        period = st.selectbox("Period", ["3mo","6mo","1y","2y"], index=2)
    with col3:
        alloc = st.selectbox("Allocation", ["Equal Weight", "Risk Parity"])
    
    if len(assets) < 2:
        st.warning("Select at least 2 assets")
        return
    
    fetcher = DataFetcher()
    data = {}
    
    with st.spinner("Loading portfolio data..."):
        for a in assets:
            df = fetcher.get_stock_data(a, period=period, interval="1d")
            if df is not None:
                data[a] = df['Close']
    
    if len(data) < 2:
        st.error("Not enough data")
        return
    
    pdf = pd.DataFrame(data).dropna()
    
    # Calculate weights
    if alloc == "Equal Weight":
        weights = {a: 1/len(assets) for a in assets if a in data}
    else:
        rets = pdf.pct_change().dropna()
        vols = rets.std()
        inv = 1/vols
        weights = (inv/inv.sum()).to_dict()
    
    analyzer = PortfolioAnalysis(pdf, weights, 100000)
    pval, metrics = analyzer.calculate_portfolio_value()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Portfolio Value", f"${pval.iloc[-1]:,.0f}")
    col2.metric("Total Return", f"{metrics['total_return']:.2f}%")
    col3.metric("Volatility", f"{metrics['portfolio_volatility']:.2f}%")
    col4.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.3f}")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Normalized Performance")
        norm = pdf/pdf.iloc[0]*100
        fig = go.Figure()
        colors = ['#00d4aa','#6366f1','#f59e0b','#ef4444','#8b5cf6']
        for i, a in enumerate(assets):
            if a in norm.columns:
                fig.add_trace(go.Scatter(x=norm.index, y=norm[a], name=a.replace('-USD',''), line=dict(color=colors[i%len(colors)], width=2)))
        npv = pval/pval.iloc[0]*100
        fig.add_trace(go.Scatter(x=npv.index, y=npv, name='Portfolio', line=dict(color='#fbbf24', width=3)))
        fig.update_layout(height=350, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=1.1, font=dict(color='#94a3b8')), xaxis=dict(showgrid=False, color='#64748b'), yaxis=dict(showgrid=True, gridcolor='#1e293b', color='#64748b'))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🥧 Allocation")
        fig = go.Figure(data=[go.Pie(labels=[a.replace('-USD','') for a in weights.keys()], values=list(weights.values()), hole=0.5, marker_colors=['#00d4aa','#6366f1','#f59e0b','#ef4444','#8b5cf6'])])
        fig.update_layout(height=350, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', showlegend=True, legend=dict(font=dict(color='#94a3b8')))
        st.plotly_chart(fig, use_container_width=True)
    
    # Correlation
    st.markdown("#### 🔗 Correlation Matrix")
    rets = pdf.pct_change().dropna()
    corr = rets.corr()
    fig = go.Figure(data=go.Heatmap(z=corr.values, x=[a.replace('-USD','') for a in corr.columns], y=[a.replace('-USD','') for a in corr.index], colorscale='RdBu', zmid=0, text=np.round(corr.values,2), texttemplate='%{text}', textfont={"size":12}))
    fig.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)


def render_paper_trading():
    """Paper Trading page - SAME LOGIC AS ORIGINAL."""
    st.markdown('<div class="section-title">📝 Paper Trading</div>', unsafe_allow_html=True)
    
    fetcher = DataFetcher()
    
    # Calculate positions value
    pos_val = 0
    for sym, d in st.session_state.paper_positions.items():
        try:
            df = fetcher.get_stock_data(sym, period='1d', interval='1m')
            price = df['Close'].iloc[-1] if df is not None else d['avg_price']
            pos_val += price * d['quantity']
        except:
            pos_val += d['avg_price'] * d['quantity']
    
    total = st.session_state.paper_balance + pos_val
    pnl = total - 1000000
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Value", f"${total:,.2f}", f"${pnl:+,.2f}")
    col2.metric("Cash", f"${st.session_state.paper_balance:,.2f}")
    col3.metric("Invested", f"${pos_val:,.2f}", f"{len(st.session_state.paper_positions)} pos")
    col4.metric("Trades", len(st.session_state.paper_trades))
    
    st.divider()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### ➕ New Trade")
        sym = st.selectbox("Symbol", ["AAPL","GOOGL","MSFT","TSLA","NVDA","META","AMZN","BTC-USD","ETH-USD"])
        action = st.radio("Action", ["Buy","Sell"], horizontal=True)
        qty = st.number_input("Quantity", 1, 1000, 10)
        
        try:
            df = fetcher.get_stock_data(sym, period='1d', interval='1m')
            price = df['Close'].iloc[-1] if df is not None else 100
            st.info(f"Price: ${price:.2f} | Total: ${price*qty:,.2f}")
        except:
            price = 100
        
        if st.button("Execute Trade", use_container_width=True, type="primary"):
            if action == "Buy":
                cost = price * qty
                if st.session_state.paper_balance >= cost:
                    st.session_state.paper_balance -= cost
                    if sym in st.session_state.paper_positions:
                        p = st.session_state.paper_positions[sym]
                        nq = p['quantity'] + qty
                        na = (p['avg_price']*p['quantity'] + price*qty)/nq
                        st.session_state.paper_positions[sym] = {'quantity':nq,'avg_price':na}
                    else:
                        st.session_state.paper_positions[sym] = {'quantity':qty,'avg_price':price}
                    st.session_state.paper_trades.append({'Date':datetime.now().strftime('%Y-%m-%d %H:%M'),'Symbol':sym,'Action':'BUY','Qty':qty,'Price':f"${price:.2f}"})
                    st.success(f"✅ Bought {qty} {sym}")
                    st.rerun()
                else:
                    st.error("❌ Insufficient funds")
            else:
                if sym in st.session_state.paper_positions and st.session_state.paper_positions[sym]['quantity'] >= qty:
                    st.session_state.paper_balance += price * qty
                    st.session_state.paper_positions[sym]['quantity'] -= qty
                    if st.session_state.paper_positions[sym]['quantity'] == 0:
                        del st.session_state.paper_positions[sym]
                    st.session_state.paper_trades.append({'Date':datetime.now().strftime('%Y-%m-%d %H:%M'),'Symbol':sym,'Action':'SELL','Qty':qty,'Price':f"${price:.2f}"})
                    st.success(f"✅ Sold {qty} {sym}")
                    st.rerun()
                else:
                    st.error("❌ No position")
    
    with col2:
        st.markdown("#### 📊 Active Positions")
        if st.session_state.paper_positions:
            rows = []
            for sym, d in st.session_state.paper_positions.items():
                try:
                    df = fetcher.get_stock_data(sym, period='1d', interval='1m')
                    cp = df['Close'].iloc[-1] if df is not None else d['avg_price']
                except:
                    cp = d['avg_price']
                pnl = (cp-d['avg_price'])*d['quantity']
                pct = ((cp/d['avg_price'])-1)*100
                rows.append({'Symbol':sym,'Qty':d['quantity'],'Avg':f"${d['avg_price']:.2f}",'Current':f"${cp:.2f}",'Value':f"${cp*d['quantity']:,.2f}",'P&L':f"${pnl:+,.2f} ({pct:+.2f}%)"})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No positions")
        
        st.markdown("#### 📜 Trade History")
        if st.session_state.paper_trades:
            st.dataframe(pd.DataFrame(st.session_state.paper_trades[-10:][::-1]), use_container_width=True, hide_index=True)
        else:
            st.info("No trades")
    
    st.divider()
    if st.button("🔄 Reset Account"):
        st.session_state.paper_balance = 1000000.0
        st.session_state.paper_positions = {}
        st.session_state.paper_trades = []
        st.rerun()


def main():
    """Main application."""
    render_ticker_bar()
    render_header()
    render_status_bar()
    render_navigation()
    st.divider()
    
    page = st.session_state.current_page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Single Asset":
        render_single_asset()
    elif page == "Portfolio":
        render_portfolio()
    elif page == "Paper Trading":
        render_paper_trading()
    
    # Auto-refresh every 5 min
    if (datetime.now() - st.session_state.last_refresh).seconds >= 300:
        st.session_state.last_refresh = datetime.now()
        st.rerun()
    
    # Footer
    paris = pytz.timezone('Europe/Paris')
    now = datetime.now(paris)
    st.markdown(f"""
        <div style="text-align:center;padding:40px 0 20px 0;border-top:1px solid #1e293b;margin-top:40px;">
            <div style="color:#64748b;font-size:12px;">Quant Dashboard Pro © 2026 · Paris: {now.strftime('%H:%M')} · <span style="color:#10b981;">● Online</span></div>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
