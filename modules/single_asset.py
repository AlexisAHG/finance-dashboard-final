"""
Single Asset Analysis Module (Quant A)
======================================
Implements backtesting strategies and performance analysis
for individual assets.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional


class SingleAssetAnalysis:
    """
    Single asset backtesting and analysis class.
    
    Implements multiple trading strategies:
    - Buy and Hold
    - Moving Average Crossover
    - RSI Strategy
    - Momentum Strategy
    """
    
    def __init__(self, data: pd.DataFrame, initial_capital: float = 10000):
        """
        Initialize the analyzer.
        
        Args:
            data: DataFrame with OHLCV data
            initial_capital: Starting capital for backtesting
        """
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.results = None
    
    def buy_and_hold(self) -> pd.DataFrame:
        """
        Simple buy and hold strategy.
        
        Returns:
            DataFrame with strategy results
        """
        df = self.data.copy()
        
        # Calculate number of shares we can buy
        initial_price = df['Close'].iloc[0]
        shares = self.initial_capital / initial_price
        
        # Calculate portfolio value over time
        df['Strategy_Value'] = shares * df['Close']
        df['Strategy_Returns'] = df['Close'].pct_change()
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        df['Position'] = 1  # Always in the market
        
        self.results = df
        return df
    
    def ma_crossover(self, short_window: int = 20, long_window: int = 50) -> pd.DataFrame:
        """
        Moving Average Crossover Strategy.
        
        Buy when short MA crosses above long MA.
        Sell when short MA crosses below long MA.
        
        Args:
            short_window: Short moving average period
            long_window: Long moving average period
            
        Returns:
            DataFrame with strategy results
        """
        df = self.data.copy()
        
        # Calculate moving averages
        df['SMA_Short'] = df['Close'].rolling(window=short_window).mean()
        df['SMA_Long'] = df['Close'].rolling(window=long_window).mean()
        
        # Generate signals
        df['Signal'] = 0
        df.loc[df['SMA_Short'] > df['SMA_Long'], 'Signal'] = 1
        df.loc[df['SMA_Short'] <= df['SMA_Long'], 'Signal'] = -1
        
        # Position: 1 = long, 0 = out of market
        df['Position'] = df['Signal'].apply(lambda x: 1 if x == 1 else 0)
        
        # Shift position to avoid look-ahead bias
        df['Position'] = df['Position'].shift(1).fillna(0)
        
        # Calculate returns
        df['Strategy_Returns'] = df['Close'].pct_change() * df['Position']
        df['Strategy_Returns'] = df['Strategy_Returns'].fillna(0)
        
        # Calculate portfolio value
        df['Strategy_Value'] = self.initial_capital * (1 + df['Strategy_Returns']).cumprod()
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        
        self.results = df
        return df
    
    def rsi_strategy(self, period: int = 14, oversold: int = 30, overbought: int = 70) -> pd.DataFrame:
        """
        RSI-based trading strategy.
        
        Buy when RSI < oversold level.
        Sell when RSI > overbought level.
        
        Args:
            period: RSI calculation period
            oversold: RSI level to trigger buy
            overbought: RSI level to trigger sell
            
        Returns:
            DataFrame with strategy results
        """
        df = self.data.copy()
        
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signal when RSI crosses below oversold
        df.loc[df['RSI'] < oversold, 'Signal'] = 1
        # Sell signal when RSI crosses above overbought
        df.loc[df['RSI'] > overbought, 'Signal'] = -1
        
        # Create position based on signals (hold position until opposite signal)
        df['Position'] = 0
        in_position = False
        
        for i in range(len(df)):
            if df['Signal'].iloc[i] == 1 and not in_position:
                in_position = True
            elif df['Signal'].iloc[i] == -1 and in_position:
                in_position = False
            
            df.iloc[i, df.columns.get_loc('Position')] = 1 if in_position else 0
        
        # Shift position to avoid look-ahead bias
        df['Position'] = df['Position'].shift(1).fillna(0)
        
        # Calculate returns
        df['Strategy_Returns'] = df['Close'].pct_change() * df['Position']
        df['Strategy_Returns'] = df['Strategy_Returns'].fillna(0)
        
        # Calculate portfolio value
        df['Strategy_Value'] = self.initial_capital * (1 + df['Strategy_Returns']).cumprod()
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        
        self.results = df
        return df
    
    def momentum_strategy(self, lookback: int = 20) -> pd.DataFrame:
        """
        Momentum-based trading strategy.
        
        Go long when price is above its N-day ago price.
        Go out when price is below its N-day ago price.
        
        Args:
            lookback: Number of days to look back for momentum
            
        Returns:
            DataFrame with strategy results
        """
        df = self.data.copy()
        
        # Calculate momentum
        df['Momentum'] = df['Close'] / df['Close'].shift(lookback) - 1
        df['Momentum_MA'] = df['Momentum'].rolling(window=5).mean()
        
        # Generate signals based on momentum
        df['Signal'] = 0
        df.loc[df['Momentum'] > 0, 'Signal'] = 1
        df.loc[df['Momentum'] <= 0, 'Signal'] = -1
        
        # Position
        df['Position'] = df['Signal'].apply(lambda x: 1 if x == 1 else 0)
        
        # Shift position to avoid look-ahead bias
        df['Position'] = df['Position'].shift(1).fillna(0)
        
        # Calculate returns
        df['Strategy_Returns'] = df['Close'].pct_change() * df['Position']
        df['Strategy_Returns'] = df['Strategy_Returns'].fillna(0)
        
        # Calculate portfolio value
        df['Strategy_Value'] = self.initial_capital * (1 + df['Strategy_Returns']).cumprod()
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        
        self.results = df
        return df
    
    def bollinger_bands_strategy(self, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
        """
        Bollinger Bands trading strategy.
        
        Buy when price touches lower band.
        Sell when price touches upper band.
        
        Args:
            window: Rolling window for Bollinger Bands
            num_std: Number of standard deviations for bands
            
        Returns:
            DataFrame with strategy results
        """
        df = self.data.copy()
        
        # Calculate Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=window).mean()
        rolling_std = df['Close'].rolling(window=window).std()
        df['BB_Upper'] = df['BB_Middle'] + (rolling_std * num_std)
        df['BB_Lower'] = df['BB_Middle'] - (rolling_std * num_std)
        
        # Generate signals
        df['Signal'] = 0
        df.loc[df['Close'] < df['BB_Lower'], 'Signal'] = 1  # Buy
        df.loc[df['Close'] > df['BB_Upper'], 'Signal'] = -1  # Sell
        
        # Create position
        df['Position'] = 0
        in_position = False
        
        for i in range(len(df)):
            if df['Signal'].iloc[i] == 1 and not in_position:
                in_position = True
            elif df['Signal'].iloc[i] == -1 and in_position:
                in_position = False
            
            df.iloc[i, df.columns.get_loc('Position')] = 1 if in_position else 0
        
        # Shift position
        df['Position'] = df['Position'].shift(1).fillna(0)
        
        # Calculate returns
        df['Strategy_Returns'] = df['Close'].pct_change() * df['Position']
        df['Strategy_Returns'] = df['Strategy_Returns'].fillna(0)
        
        # Calculate portfolio value
        df['Strategy_Value'] = self.initial_capital * (1 + df['Strategy_Returns']).cumprod()
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        
        self.results = df
        return df
    
    def get_trade_statistics(self) -> Dict:
        """
        Calculate trading statistics from backtest results.
        
        Returns:
            Dictionary with trade statistics
        """
        if self.results is None:
            return {}
        
        df = self.results.copy()
        
        # Identify trades (when position changes)
        df['Trade'] = df['Position'].diff().abs()
        
        # Calculate number of trades
        num_trades = df['Trade'].sum() / 2  # Entry + Exit = 1 trade
        
        # Calculate winning trades
        df['Trade_Return'] = df['Strategy_Returns'].where(df['Trade'] == 1, 0)
        winning_trades = (df['Trade_Return'] > 0).sum()
        losing_trades = (df['Trade_Return'] < 0).sum()
        
        total_trades = winning_trades + losing_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': num_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate
        }
