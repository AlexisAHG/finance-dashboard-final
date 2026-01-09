"""
Report Generator Module
=======================
Generates daily financial reports for tracked assets.
Designed to be run via cron job at a fixed time (e.g., 8 PM).
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class ReportGenerator:
    """
    Generates daily financial reports with key metrics.
    """
    
    # Default assets to track
    DEFAULT_ASSETS = [
        "AAPL", "GOOGL", "MSFT", "TSLA", "NVDA",  # Tech stocks
        "ENGI.PA", "TTE.PA",  # French stocks
        "GC=F",  # Gold
        "BTC-USD", "ETH-USD",  # Crypto
        "EURUSD=X"  # Forex
    ]
    
    def __init__(
        self,
        assets: Optional[List[str]] = None,
        reports_dir: str = "reports"
    ):
        """
        Initialize the report generator.
        
        Args:
            assets: List of asset symbols to track
            reports_dir: Directory to save reports
        """
        self.assets = assets or self.DEFAULT_ASSETS
        self.reports_dir = reports_dir
        
        # Create reports directory if it doesn't exist
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_daily_report(self) -> str:
        """
        Generate the daily report with all tracked assets.
        
        Returns:
            Path to the generated report file
        """
        from utils.data_fetcher import DataFetcher
        from utils.metrics import FinancialMetrics
        
        fetcher = DataFetcher()
        
        # Report header
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_time = datetime.now().strftime("%H:%M:%S")
        
        report_lines = [
            "=" * 70,
            f"DAILY FINANCIAL REPORT - {report_date}",
            f"Generated at: {report_time}",
            "=" * 70,
            ""
        ]
        
        # Summary section
        report_lines.append("📊 MARKET SUMMARY")
        report_lines.append("-" * 70)
        report_lines.append("")
        
        # Collect data for each asset
        asset_data = []
        
        for symbol in self.assets:
            try:
                # Get recent data
                df = fetcher.get_stock_data(symbol, period="1mo", interval="1d")
                
                if df is None or df.empty:
                    continue
                
                # Calculate metrics
                current_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
                daily_change = ((current_price - prev_price) / prev_price) * 100
                
                open_price = df['Open'].iloc[-1]
                high_price = df['High'].iloc[-1]
                low_price = df['Low'].iloc[-1]
                volume = df['Volume'].iloc[-1]
                
                # Calculate volatility (20-day)
                returns = df['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252) * 100
                
                # Calculate max drawdown (30-day)
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.cummax()
                drawdown = ((cumulative - running_max) / running_max).min() * 100
                
                # Monthly return
                if len(df) >= 20:
                    monthly_return = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
                else:
                    monthly_return = 0
                
                asset_data.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'daily_change': daily_change,
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'volume': volume,
                    'volatility': volatility,
                    'max_drawdown': drawdown,
                    'monthly_return': monthly_return
                })
                
            except Exception as e:
                report_lines.append(f"⚠️  Error fetching {symbol}: {str(e)}")
        
        # Format asset data in report
        for data in asset_data:
            symbol = data['symbol']
            change_emoji = "📈" if data['daily_change'] >= 0 else "📉"
            
            report_lines.append(f"{change_emoji} {symbol}")
            report_lines.append(f"   Current Price:    ${data['current_price']:.2f}")
            report_lines.append(f"   Daily Change:     {data['daily_change']:+.2f}%")
            report_lines.append(f"   Open/High/Low:    ${data['open_price']:.2f} / ${data['high_price']:.2f} / ${data['low_price']:.2f}")
            report_lines.append(f"   Volume:           {data['volume']:,.0f}")
            report_lines.append(f"   Volatility (Ann): {data['volatility']:.2f}%")
            report_lines.append(f"   Max Drawdown:     {data['max_drawdown']:.2f}%")
            report_lines.append(f"   Monthly Return:   {data['monthly_return']:+.2f}%")
            report_lines.append("")
        
        # Winners and Losers
        if asset_data:
            report_lines.append("-" * 70)
            report_lines.append("🏆 TOP PERFORMERS (Daily)")
            report_lines.append("-" * 70)
            
            sorted_by_change = sorted(asset_data, key=lambda x: x['daily_change'], reverse=True)
            
            for i, data in enumerate(sorted_by_change[:3], 1):
                report_lines.append(f"   {i}. {data['symbol']}: {data['daily_change']:+.2f}%")
            
            report_lines.append("")
            report_lines.append("📉 BOTTOM PERFORMERS (Daily)")
            report_lines.append("-" * 70)
            
            for i, data in enumerate(sorted_by_change[-3:], 1):
                report_lines.append(f"   {i}. {data['symbol']}: {data['daily_change']:+.2f}%")
            
            report_lines.append("")
        
        # Volatility ranking
        if asset_data:
            report_lines.append("-" * 70)
            report_lines.append("⚡ VOLATILITY RANKING")
            report_lines.append("-" * 70)
            
            sorted_by_vol = sorted(asset_data, key=lambda x: x['volatility'], reverse=True)
            
            for i, data in enumerate(sorted_by_vol, 1):
                report_lines.append(f"   {i}. {data['symbol']}: {data['volatility']:.2f}%")
            
            report_lines.append("")
        
        # Footer
        report_lines.append("=" * 70)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 70)
        
        # Save report
        report_filename = f"daily_report_{report_date}.txt"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        # Also save as JSON for programmatic access
        json_filename = f"daily_report_{report_date}.json"
        json_path = os.path.join(self.reports_dir, json_filename)
        
        json_data = {
            'date': report_date,
            'time': report_time,
            'assets': asset_data
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        
        return report_path
    
    def generate_weekly_summary(self) -> str:
        """
        Generate a weekly summary report.
        
        Returns:
            Path to the generated report file
        """
        from utils.data_fetcher import DataFetcher
        
        fetcher = DataFetcher()
        
        report_date = datetime.now().strftime("%Y-%m-%d")
        week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        report_lines = [
            "=" * 70,
            f"WEEKLY FINANCIAL SUMMARY",
            f"Period: {week_start} to {report_date}",
            "=" * 70,
            ""
        ]
        
        for symbol in self.assets:
            try:
                df = fetcher.get_stock_data(symbol, period="1mo", interval="1d")
                
                if df is None or df.empty:
                    continue
                
                # Get last 5 trading days
                recent = df.tail(5)
                
                if len(recent) < 2:
                    continue
                
                weekly_return = ((recent['Close'].iloc[-1] / recent['Close'].iloc[0]) - 1) * 100
                avg_volume = recent['Volume'].mean()
                high_of_week = recent['High'].max()
                low_of_week = recent['Low'].min()
                
                report_lines.append(f"📊 {symbol}")
                report_lines.append(f"   Weekly Return:  {weekly_return:+.2f}%")
                report_lines.append(f"   High of Week:   ${high_of_week:.2f}")
                report_lines.append(f"   Low of Week:    ${low_of_week:.2f}")
                report_lines.append(f"   Avg Volume:     {avg_volume:,.0f}")
                report_lines.append("")
                
            except Exception as e:
                report_lines.append(f"⚠️  Error fetching {symbol}: {str(e)}")
        
        report_lines.append("=" * 70)
        
        # Save report
        report_filename = f"weekly_summary_{report_date}.txt"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        return report_path
    
    def cleanup_old_reports(self, days_to_keep: int = 30):
        """
        Remove reports older than specified days.
        
        Args:
            days_to_keep: Number of days of reports to keep
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for filename in os.listdir(self.reports_dir):
            filepath = os.path.join(self.reports_dir, filename)
            
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff_date:
                    os.remove(filepath)


if __name__ == "__main__":
    # Generate report when run directly
    generator = ReportGenerator()
    report_path = generator.generate_daily_report()
    print(f"Report generated: {report_path}")
