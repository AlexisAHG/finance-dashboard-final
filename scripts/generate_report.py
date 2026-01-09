#!/usr/bin/env python3
"""
Daily Report Generator - Professional Edition
=============================================
Generates a comprehensive, styled PDF report at 8pm via cron job.
Adapted for finance-dashboard project structure.

Cron setup (20h Paris):
    0 20 * * * cd /home/alexis_hanna_ah/finance-dashboard && /home/alexis_hanna_ah/finance-dashboard/venv/bin/python scripts/generate_report.py >> logs/cron.log 2>&1
"""

import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import pytz
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import YOUR project modules
try:
    from utils.data_fetcher import DataFetcher
    from utils.metrics import FinancialMetrics
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    sys.exit(1)

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False
    logger.warning("fpdf not installed - PDF reports disabled. Run: pip install fpdf2")

# Watchlist
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD",
    "SPY", "QQQ",
    "BTC-USD", "ETH-USD",
    "EURUSD=X", "GC=F",
    "ENGI.PA", "TTE.PA"
]

REPORTS_DIR = PROJECT_ROOT / "reports"
PARIS_TZ = pytz.timezone("Europe/Paris")


# ============================================================
# CUSTOM PDF CLASS - PROFESSIONAL STYLED
# ============================================================
if HAS_FPDF:
    class ProPDF(FPDF):
        def header(self):
            # Dark header background
            self.set_fill_color(16, 24, 32)
            self.rect(0, 0, 210, 40, 'F')
            
            # Main title
            self.set_font("Helvetica", "B", 24)
            self.set_text_color(255, 255, 255)
            self.set_y(10)
            self.cell(0, 10, "QUANT DASHBOARD PRO", ln=True, align="C")
            
            # Subtitle with accent color
            self.set_font("Helvetica", "", 10)
            self.set_text_color(0, 212, 170)  # Teal accent
            self.cell(0, 10, "DAILY MARKET REPORT & ANALYTICS", ln=True, align="C")
            self.ln(20)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            paris_time = datetime.now(PARIS_TZ).strftime("%H:%M")
            self.cell(0, 10, f'Generated automatically via Cron at {paris_time} Paris | Page {self.page_no()}', 0, 0, 'C')


def collect_daily_data(tickers: list) -> dict:
    """Collect daily data for all tickers using YOUR DataFetcher."""
    logger.info(f"Collecting data for {len(tickers)} tickers...")
    
    fetcher = DataFetcher()
    
    results = {
        "timestamp": datetime.now(PARIS_TZ).isoformat(),
        "date": datetime.now(PARIS_TZ).strftime("%Y-%m-%d"),
        "assets": {},
        "errors": [],
    }
    
    for ticker in tickers:
        try:
            df = fetcher.get_stock_data(ticker, period="5d", interval="1d")
            
            if df is not None and len(df) >= 2:
                current = df['Close'].iloc[-1]
                previous = df['Close'].iloc[-2]
                change_pct = ((current - previous) / previous) * 100
                
                # Calculate metrics
                returns = df['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252) * 100
                
                # Max drawdown
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.cummax()
                drawdown = (cumulative - running_max) / running_max
                max_drawdown = drawdown.min() * 100
                
                results["assets"][ticker] = {
                    "daily": {
                        "open": float(df['Open'].iloc[-1]),
                        "high": float(df['High'].iloc[-1]),
                        "low": float(df['Low'].iloc[-1]),
                        "close": float(current),
                        "volume": int(df['Volume'].iloc[-1]),
                        "change_pct": float(change_pct),
                    },
                    "stats": {
                        "volatility": float(volatility),
                        "max_drawdown": float(max_drawdown)
                    }
                }
                
                logger.info(f"  ✓ {ticker}: ${current:.2f} ({change_pct:+.2f}%)")
            else:
                results["errors"].append(f"No data: {ticker}")
                logger.warning(f"  ✗ {ticker}: No data")
                
        except Exception as e:
            results["errors"].append(f"{ticker}: {str(e)}")
            logger.error(f"  ✗ {ticker}: {e}")
    
    return results


def calculate_metrics(data: dict) -> dict:
    """Calculate aggregate metrics."""
    assets = data.get("assets", {})
    if not assets:
        return {}
    
    returns = []
    gainers, losers = [], []
    
    for ticker, info in assets.items():
        daily = info.get("daily", {})
        if daily:
            change = daily.get("change_pct", 0)
            returns.append(change)
            if change > 0:
                gainers.append((ticker, change))
            elif change < 0:
                losers.append((ticker, change))
    
    gainers.sort(key=lambda x: x[1], reverse=True)
    losers.sort(key=lambda x: x[1])
    
    return {
        "total_assets": len(assets),
        "avg_return": float(np.mean(returns)) if returns else 0,
        "positive_count": len(gainers),
        "negative_count": len(losers),
        "top_gainers": gainers[:5],
        "top_losers": losers[:5],
    }


def generate_text_report(data: dict, metrics: dict) -> str:
    """Generate plain text report."""
    lines = [
        "=" * 60,
        "         DAILY MARKET REPORT - QUANT DASHBOARD PRO",
        f"         Generated: {data['timestamp']}",
        "=" * 60,
        "",
        "SUMMARY",
        "-" * 40,
        f"Date:           {data['date']}",
        f"Assets Tracked: {metrics.get('total_assets', 0)}",
        f"Avg Return:     {metrics.get('avg_return', 0):+.2f}%",
        f"Gainers:        {metrics.get('positive_count', 0)}",
        f"Losers:         {metrics.get('negative_count', 0)}",
        "",
        "TOP GAINERS",
        "-" * 40
    ]
    
    for ticker, change in metrics.get("top_gainers", []):
        lines.append(f"  {ticker:<12} {change:+.2f}%")
    
    lines.extend(["", "TOP LOSERS", "-" * 40])
    
    for ticker, change in metrics.get("top_losers", []):
        lines.append(f"  {ticker:<12} {change:+.2f}%")
    
    lines.extend([
        "",
        "DETAILED DATA",
        "-" * 40,
        f"{'Ticker':<12} {'Close':>10} {'Change':>10} {'Volume':>15}"
    ])
    
    sorted_assets = sorted(
        data.get("assets", {}).items(),
        key=lambda x: x[1]['daily']['change_pct'],
        reverse=True
    )
    
    for ticker, info in sorted_assets:
        daily = info.get("daily", {})
        if daily:
            lines.append(
                f"{ticker:<12} "
                f"${daily.get('close', 0):>9.2f} "
                f"{daily.get('change_pct', 0):>+9.2f}% "
                f"{daily.get('volume', 0):>14,}"
            )
    
    lines.extend([
        "",
        "=" * 60,
        "                    End of Report",
        "=" * 60
    ])
    
    return "\n".join(lines)


def generate_json_report(data: dict, metrics: dict) -> str:
    """Generate JSON report."""
    return json.dumps({
        "metadata": {
            "generated": data["timestamp"],
            "date": data["date"],
            "generator": "Quant Dashboard Pro Daily Report"
        },
        "summary": metrics,
        "assets": data["assets"],
        "errors": data["errors"]
    }, indent=2, default=str)


def generate_pdf_report(data: dict, metrics: dict, path: Path) -> bool:
    """Generate the Professional Styled PDF."""
    if not HAS_FPDF:
        logger.warning("PDF generation skipped - fpdf not installed")
        return False
    
    try:
        pdf = ProPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # --- SECTION 1: MARKET OVERVIEW ---
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(16, 24, 32)
        pdf.cell(0, 10, f"MARKET OVERVIEW  |  {data['date']}", ln=True)
        
        # Separator line
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Summary metrics
        pdf.set_font("Helvetica", "", 12)
        avg_ret = metrics.get('avg_return', 0)
        
        pdf.cell(40, 10, "Average Return: ")
        
        if avg_ret >= 0:
            pdf.set_text_color(16, 185, 129)  # Green
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(30, 10, f"+{avg_ret:.2f}%")
        else:
            pdf.set_text_color(239, 68, 68)  # Red
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(30, 10, f"{avg_ret:.2f}%")
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(10, 10, " | ")
        pdf.cell(30, 10, f"Assets: {metrics.get('total_assets', 0)}")
        pdf.cell(10, 10, " | ")
        pdf.cell(50, 10, f"Up: {metrics.get('positive_count', 0)} / Down: {metrics.get('negative_count', 0)}", ln=True)
        pdf.ln(10)

        # --- SECTION 2: TOP MOVERS ---
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(236, 253, 245)  # Light green
        pdf.cell(90, 8, " TOP GAINERS", 1, 0, 'L', True)
        pdf.cell(10, 8, "")
        pdf.set_fill_color(254, 242, 242)  # Light red
        pdf.cell(90, 8, " TOP LOSERS", 1, 1, 'L', True)
        
        pdf.set_font("Helvetica", "", 10)
        gainers = metrics.get("top_gainers", [])
        losers = metrics.get("top_losers", [])
        
        for i in range(5):
            # Gainers column
            if i < len(gainers):
                ticker, change = gainers[i]
                pdf.set_text_color(0, 0, 0)
                pdf.cell(60, 8, f"  {ticker}", 'L')
                pdf.set_text_color(16, 185, 129)
                pdf.cell(30, 8, f"+{change:.2f}%", 'R')
            else:
                pdf.cell(90, 8, "")
            
            pdf.cell(10, 8, "")
            
            # Losers column
            if i < len(losers):
                ticker, change = losers[i]
                pdf.set_text_color(0, 0, 0)
                pdf.cell(60, 8, f"  {ticker}", 'L')
                pdf.set_text_color(239, 68, 68)
                pdf.cell(30, 8, f"{change:.2f}%", 'R', ln=True)
            else:
                pdf.cell(90, 8, "", ln=True)

        pdf.ln(15)

        # --- SECTION 3: DETAILED TABLE ---
        pdf.set_text_color(16, 24, 32)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "DETAILED ASSET PERFORMANCE", ln=True)
        pdf.set_draw_color(16, 24, 32)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Table headers
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 10, "Ticker", 0, 0, 'L', True)
        pdf.cell(40, 10, "Close", 0, 0, 'R', True)
        pdf.cell(40, 10, "Change", 0, 0, 'R', True)
        pdf.cell(70, 10, "Volume", 0, 1, 'R', True)
        
        # Table rows
        pdf.set_font("Helvetica", "", 10)
        
        sorted_assets = sorted(
            data.get("assets", {}).items(),
            key=lambda x: x[1]['daily']['change_pct'],
            reverse=True
        )
        
        for ticker, info in sorted_assets:
            daily = info.get("daily", {})
            if daily:
                pdf.set_text_color(0, 0, 0)
                pdf.cell(40, 8, ticker)
                pdf.cell(40, 8, f"${daily.get('close', 0):,.2f}", 0, 0, 'R')
                
                change = daily.get('change_pct', 0)
                if change >= 0:
                    pdf.set_text_color(16, 185, 129)
                    txt = f"+{change:.2f}%"
                else:
                    pdf.set_text_color(239, 68, 68)
                    txt = f"{change:.2f}%"
                pdf.cell(40, 8, txt, 0, 0, 'R')
                
                pdf.set_text_color(100, 116, 139)
                pdf.cell(70, 8, f"{daily.get('volume', 0):,}", 0, 1, 'R')
                
                pdf.set_draw_color(240, 240, 240)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())

        pdf.output(str(path))
        logger.info(f"PDF generated: {path}")
        return True
        
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return False


def save_reports(data: dict, metrics: dict) -> dict:
    """Save all report formats."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    date_str = data["date"]
    saved = {}
    
    # Text report
    text_path = REPORTS_DIR / f"report_{date_str}.txt"
    text_content = generate_text_report(data, metrics)
    text_path.write_text(text_content)
    saved["text"] = str(text_path)
    
    # JSON report
    json_path = REPORTS_DIR / f"report_{date_str}.json"
    json_path.write_text(generate_json_report(data, metrics))
    saved["json"] = str(json_path)
    
    # PDF report
    pdf_path = REPORTS_DIR / f"report_{date_str}.pdf"
    if generate_pdf_report(data, metrics, pdf_path):
        saved["pdf"] = str(pdf_path)
    
    # Latest report
    (REPORTS_DIR / "latest_report.txt").write_text(text_content)
    saved["latest"] = str(REPORTS_DIR / "latest_report.txt")
    
    return saved


def main(watchlist: list = None):
    """Main entry point."""
    logger.info("=" * 50)
    logger.info("Starting Pro Daily Report Generation")
    logger.info(f"Time: {datetime.now(PARIS_TZ).strftime('%Y-%m-%d %H:%M:%S')} Paris")
    logger.info("=" * 50)
    
    if watchlist is None:
        watchlist = DEFAULT_WATCHLIST
    
    try:
        data = collect_daily_data(watchlist)
        metrics = calculate_metrics(data)
        saved = save_reports(data, metrics)
        
        logger.info("")
        logger.info("=" * 50)
        logger.info("Report Generation Complete!")
        logger.info("=" * 50)
        
        for fmt, path in saved.items():
            logger.info(f"  {fmt}: {path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        custom = sys.argv[1].split(",")
        success = main(watchlist=custom)
    else:
        success = main()
    
    sys.exit(0 if success else 1)
