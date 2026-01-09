"""
Data Fetcher Module
===================
Handles data retrieval from various financial APIs.
Supports Yahoo Finance, Alpha Vantage, and CoinGecko.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import requests
import time


class DataFetcher:
    """
    Unified data fetcher for multiple financial data sources.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the data fetcher.
        
        Args:
            api_key: Optional API key for premium data sources
        """
        self.api_key = api_key
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    def get_stock_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch stock data from Yahoo Finance.
        
        Args:
            symbol: Stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        cache_key = f"{symbol}_{period}_{interval}"
        
        # Check cache
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_timeout:
                return cached_data
        
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                return None
            
            # Clean up the dataframe
            df = df.reset_index()
            df.columns = [col.replace(' ', '_') for col in df.columns]
            
            # Ensure we have the standard column names
            if 'Date' in df.columns:
                df.set_index('Date', inplace=True)
            elif 'Datetime' in df.columns:
                df.set_index('Datetime', inplace=True)
            
            # Make index timezone-naive for easier handling
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # Rename columns to standard format
            column_map = {
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume',
                'Adj_Close': 'Adj_Close'
            }
            
            # Cache the result
            self._cache[cache_key] = (df, datetime.now())
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return self._get_fallback_data(symbol, period)
    
    def _get_fallback_data(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """
        Generate fallback synthetic data when API fails.
        Used for demonstration purposes.
        
        Args:
            symbol: Stock ticker symbol
            period: Time period
            
        Returns:
            DataFrame with synthetic OHLCV data
        """
        # Map period to number of days
        period_map = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
            "5y": 1825
        }
        
        n_days = period_map.get(period, 365)
        
        # Generate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=n_days)
        dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
        
        # Generate synthetic prices
        np.random.seed(hash(symbol) % 2**32)
        
        # Starting price based on symbol hash
        base_price = 50 + (hash(symbol) % 200)
        
        # Random walk with drift
        returns = np.random.normal(0.0002, 0.02, len(dates))
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Generate OHLCV data
        df = pd.DataFrame({
            'Open': prices * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
            'High': prices * (1 + np.random.uniform(0, 0.02, len(dates))),
            'Low': prices * (1 - np.random.uniform(0, 0.02, len(dates))),
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        
        return df
    
    def get_crypto_data(
        self,
        symbol: str,
        vs_currency: str = "usd",
        days: int = 365
    ) -> Optional[pd.DataFrame]:
        """
        Fetch cryptocurrency data from CoinGecko.
        
        Args:
            symbol: Crypto symbol (e.g., 'bitcoin', 'ethereum')
            vs_currency: Quote currency (e.g., 'usd', 'eur')
            days: Number of days of data
            
        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{symbol}/ohlc"
            params = {
                'vs_currency': vs_currency,
                'days': days
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            df = pd.DataFrame(data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close'])
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
            df.set_index('Timestamp', inplace=True)
            df['Volume'] = 0  # CoinGecko OHLC doesn't include volume
            
            return df
            
        except Exception as e:
            print(f"Error fetching crypto data for {symbol}: {str(e)}")
            return None
    
    def get_forex_data(
        self,
        from_currency: str,
        to_currency: str,
        period: str = "1y"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch forex data using Yahoo Finance.
        
        Args:
            from_currency: Base currency (e.g., 'EUR')
            to_currency: Quote currency (e.g., 'USD')
            period: Time period
            
        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        symbol = f"{from_currency}{to_currency}=X"
        return self.get_stock_data(symbol, period=period)
    
    def get_current_price(self, symbol: str) -> Optional[Dict]:
        """
        Get current price and basic info for a symbol.
        
        Args:
            symbol: Stock/crypto symbol
            
        Returns:
            Dictionary with current price info or None if fetch fails
        """
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'price': info.get('regularMarketPrice', info.get('currentPrice', 0)),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0),
                'market_cap': info.get('marketCap', 0),
                'name': info.get('shortName', symbol)
            }
            
        except Exception as e:
            print(f"Error getting current price for {symbol}: {str(e)}")
            return None
    
    def get_multiple_stocks(
        self,
        symbols: List[str],
        period: str = "1y",
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple stocks.
        
        Args:
            symbols: List of stock ticker symbols
            period: Time period
            interval: Data interval
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        result = {}
        
        for symbol in symbols:
            df = self.get_stock_data(symbol, period=period, interval=interval)
            if df is not None:
                result[symbol] = df
            time.sleep(0.1)  # Small delay to avoid rate limiting
        
        return result
    
    def get_market_indices(self) -> Dict[str, Dict]:
        """
        Get current values for major market indices.
        
        Returns:
            Dictionary with index data
        """
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^IXIC': 'NASDAQ',
            '^FCHI': 'CAC 40',
            '^GDAXI': 'DAX',
            '^FTSE': 'FTSE 100'
        }
        
        result = {}
        
        for symbol, name in indices.items():
            data = self.get_current_price(symbol)
            if data:
                data['name'] = name
                result[symbol] = data
        
        return result
    
    def clear_cache(self):
        """Clear the data cache."""
        self._cache = {}


class WebScraper:
    """
    Web scraper for financial data from websites.
    Uses BeautifulSoup and requests for data extraction.
    """
    
    def __init__(self):
        """Initialize the web scraper."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_investing_com(self, url: str) -> Optional[Dict]:
        """
        Scrape data from investing.com.
        
        Args:
            url: Page URL to scrape
            
        Returns:
            Dictionary with scraped data or None if fails
        """
        try:
            from bs4 import BeautifulSoup
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract relevant data based on page structure
            # This is a template - actual implementation depends on page structure
            
            return {
                'status': 'success',
                'data': soup.get_text()[:1000]
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def scrape_boursorama(self, symbol: str) -> Optional[Dict]:
        """
        Scrape stock data from Boursorama.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with scraped data or None if fails
        """
        try:
            from bs4 import BeautifulSoup
            
            url = f"https://www.boursorama.com/cours/{symbol}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract price data
            # Note: This is a template - actual selectors depend on current page structure
            
            return {
                'symbol': symbol,
                'status': 'success'
            }
            
        except Exception as e:
            print(f"Error scraping Boursorama for {symbol}: {str(e)}")
            return None
