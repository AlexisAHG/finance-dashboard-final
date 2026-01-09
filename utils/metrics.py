"""
Financial Metrics Module
========================
Calculate various financial performance metrics
for assets and portfolios.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


class FinancialMetrics:
    """
    Static methods for calculating financial metrics.
    """
    
    @staticmethod
    def calculate_metrics(df: pd.DataFrame, initial_capital: float) -> Dict:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            df: DataFrame with strategy results (must have 'Strategy_Value' column)
            initial_capital: Initial investment amount
            
        Returns:
            Dictionary of performance metrics
        """
        if 'Strategy_Value' not in df.columns:
            return {}
        
        strategy_value = df['Strategy_Value']
        
        # Total Return
        total_return = ((strategy_value.iloc[-1] / initial_capital) - 1) * 100
        
        # Calculate returns
        if 'Strategy_Returns' in df.columns:
            returns = df['Strategy_Returns'].dropna()
        else:
            returns = strategy_value.pct_change().dropna()
        
        # Annualized Volatility
        volatility = returns.std() * np.sqrt(252) * 100
        
        # Sharpe Ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        excess_return = returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_return / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # Win Rate
        if 'Position' in df.columns:
            trading_returns = returns[df['Position'].shift(1) == 1]
            if len(trading_returns) > 0:
                win_rate = (trading_returns > 0).sum() / len(trading_returns) * 100
            else:
                win_rate = 0
        else:
            win_rate = (returns > 0).sum() / len(returns) * 100
        
        # Final Value
        final_value = strategy_value.iloc[-1]
        
        # Profit Factor
        gains = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())
        profit_factor = gains / losses if losses > 0 else float('inf')
        
        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.0001
        sortino_ratio = excess_return / downside_std if downside_std > 0 else 0
        
        # Calmar Ratio
        calmar_ratio = (returns.mean() * 252) / abs(max_drawdown/100) if max_drawdown != 0 else 0
        
        return {
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'final_value': final_value,
            'profit_factor': profit_factor,
            'calmar_ratio': calmar_ratio
        }
    
    @staticmethod
    def calculate_rolling_metrics(
        returns: pd.Series,
        window: int = 20
    ) -> pd.DataFrame:
        """
        Calculate rolling performance metrics.
        
        Args:
            returns: Series of returns
            window: Rolling window size
            
        Returns:
            DataFrame with rolling metrics
        """
        rolling_return = returns.rolling(window).mean() * 252 * 100
        rolling_vol = returns.rolling(window).std() * np.sqrt(252) * 100
        rolling_sharpe = (returns.rolling(window).mean() * 252) / (returns.rolling(window).std() * np.sqrt(252))
        
        return pd.DataFrame({
            'Rolling_Return': rolling_return,
            'Rolling_Volatility': rolling_vol,
            'Rolling_Sharpe': rolling_sharpe
        })
    
    @staticmethod
    def calculate_drawdown_series(returns: pd.Series) -> pd.Series:
        """
        Calculate drawdown series.
        
        Args:
            returns: Series of returns
            
        Returns:
            Series of drawdowns
        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return drawdown
    
    @staticmethod
    def calculate_var(
        returns: pd.Series,
        confidence_level: float = 0.95,
        method: str = 'historical'
    ) -> float:
        """
        Calculate Value at Risk.
        
        Args:
            returns: Series of returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            method: Calculation method ('historical', 'parametric')
            
        Returns:
            VaR value as a percentage
        """
        if method == 'historical':
            var = np.percentile(returns, (1 - confidence_level) * 100)
        else:  # parametric
            z_score = 1.645 if confidence_level == 0.95 else 2.326  # 95% or 99%
            var = returns.mean() - z_score * returns.std()
        
        return var * 100
    
    @staticmethod
    def calculate_beta(
        asset_returns: pd.Series,
        market_returns: pd.Series
    ) -> float:
        """
        Calculate asset beta relative to market.
        
        Args:
            asset_returns: Series of asset returns
            market_returns: Series of market returns
            
        Returns:
            Beta coefficient
        """
        # Align the series
        aligned = pd.DataFrame({
            'asset': asset_returns,
            'market': market_returns
        }).dropna()
        
        covariance = aligned['asset'].cov(aligned['market'])
        market_variance = aligned['market'].var()
        
        return covariance / market_variance if market_variance > 0 else 1
    
    @staticmethod
    def calculate_alpha(
        asset_returns: pd.Series,
        market_returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Jensen's Alpha.
        
        Args:
            asset_returns: Series of asset returns
            market_returns: Series of market returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Annualized alpha
        """
        beta = FinancialMetrics.calculate_beta(asset_returns, market_returns)
        
        daily_rf = risk_free_rate / 252
        
        asset_excess = asset_returns.mean() - daily_rf
        market_excess = market_returns.mean() - daily_rf
        
        alpha = (asset_excess - beta * market_excess) * 252
        
        return alpha * 100
    
    @staticmethod
    def calculate_information_ratio(
        asset_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """
        Calculate Information Ratio.
        
        Args:
            asset_returns: Series of asset returns
            benchmark_returns: Series of benchmark returns
            
        Returns:
            Information Ratio
        """
        active_return = asset_returns.mean() - benchmark_returns.mean()
        tracking_error = (asset_returns - benchmark_returns).std()
        
        return (active_return * 252) / (tracking_error * np.sqrt(252)) if tracking_error > 0 else 0
    
    @staticmethod
    def calculate_treynor_ratio(
        returns: pd.Series,
        market_returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Treynor Ratio.
        
        Args:
            returns: Series of portfolio/asset returns
            market_returns: Series of market returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Treynor Ratio
        """
        beta = FinancialMetrics.calculate_beta(returns, market_returns)
        
        excess_return = returns.mean() * 252 - risk_free_rate
        
        return excess_return / beta if beta != 0 else 0
    
    @staticmethod
    def generate_performance_summary(
        df: pd.DataFrame,
        initial_capital: float,
        benchmark_returns: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Generate a comprehensive performance summary.
        
        Args:
            df: DataFrame with strategy results
            initial_capital: Initial investment
            benchmark_returns: Optional benchmark returns for comparison
            
        Returns:
            DataFrame with performance summary
        """
        metrics = FinancialMetrics.calculate_metrics(df, initial_capital)
        
        summary_data = {
            'Metric': [
                'Total Return',
                'Annualized Volatility',
                'Sharpe Ratio',
                'Sortino Ratio',
                'Maximum Drawdown',
                'Win Rate',
                'Profit Factor',
                'Calmar Ratio',
                'Final Portfolio Value'
            ],
            'Value': [
                f"{metrics['total_return']:.2f}%",
                f"{metrics['volatility']:.2f}%",
                f"{metrics['sharpe_ratio']:.3f}",
                f"{metrics['sortino_ratio']:.3f}",
                f"{metrics['max_drawdown']:.2f}%",
                f"{metrics['win_rate']:.1f}%",
                f"{metrics['profit_factor']:.2f}",
                f"{metrics['calmar_ratio']:.3f}",
                f"${metrics['final_value']:,.2f}"
            ]
        }
        
        if benchmark_returns is not None and 'Strategy_Returns' in df.columns:
            returns = df['Strategy_Returns'].dropna()
            
            beta = FinancialMetrics.calculate_beta(returns, benchmark_returns)
            alpha = FinancialMetrics.calculate_alpha(returns, benchmark_returns)
            ir = FinancialMetrics.calculate_information_ratio(returns, benchmark_returns)
            
            summary_data['Metric'].extend(['Beta', 'Alpha', 'Information Ratio'])
            summary_data['Value'].extend([
                f"{beta:.3f}",
                f"{alpha:.2f}%",
                f"{ir:.3f}"
            ])
        
        return pd.DataFrame(summary_data)
