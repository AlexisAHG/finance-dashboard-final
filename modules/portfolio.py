"""
Portfolio Analysis Module (Quant B)
===================================
Implements multi-asset portfolio analysis, optimization,
and rebalancing strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional


class PortfolioAnalysis:
    """
    Multi-asset portfolio analysis and simulation class.
    
    Features:
    - Portfolio value calculation
    - Risk metrics (volatility, VaR, Sharpe)
    - Correlation analysis
    - Rebalancing simulation
    - Diversification analysis
    """
    
    def __init__(self, prices: pd.DataFrame, weights: Dict[str, float], initial_capital: float = 100000):
        """
        Initialize portfolio analyzer.
        
        Args:
            prices: DataFrame with asset prices (columns = assets)
            weights: Dictionary mapping asset names to weights
            initial_capital: Starting capital
        """
        self.prices = prices.copy()
        self.weights = weights
        self.initial_capital = initial_capital
        self.assets = list(prices.columns)
        
        # Normalize weights to ensure they sum to 1
        weight_sum = sum(weights.values())
        self.weights = {k: v/weight_sum for k, v in weights.items()}
        
        # Calculate returns
        self.returns = self.prices.pct_change().dropna()
    
    def calculate_portfolio_value(self) -> Tuple[pd.Series, Dict]:
        """
        Calculate portfolio value over time and performance metrics.
        
        Returns:
            Tuple of (portfolio value series, metrics dictionary)
        """
        # Calculate weighted returns
        portfolio_returns = pd.Series(0.0, index=self.returns.index)
        
        for asset in self.assets:
            if asset in self.weights:
                portfolio_returns += self.returns[asset] * self.weights[asset]
        
        # Calculate cumulative portfolio value
        portfolio_value = self.initial_capital * (1 + portfolio_returns).cumprod()
        
        # Prepend initial value
        first_date = self.prices.index[0]
        portfolio_value = pd.concat([
            pd.Series([self.initial_capital], index=[first_date]),
            portfolio_value
        ])
        
        # Calculate metrics
        metrics = self._calculate_metrics(portfolio_returns, portfolio_value)
        
        return portfolio_value, metrics
    
    def _calculate_metrics(self, returns: pd.Series, portfolio_value: pd.Series) -> Dict:
        """
        Calculate comprehensive portfolio metrics.
        
        Args:
            returns: Portfolio returns series
            portfolio_value: Portfolio value series
            
        Returns:
            Dictionary of performance metrics
        """
        # Basic returns
        total_return = ((portfolio_value.iloc[-1] / portfolio_value.iloc[0]) - 1) * 100
        
        # Annualized volatility
        volatility = returns.std() * np.sqrt(252) * 100
        
        # Sharpe Ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        excess_returns = returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_returns / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.0001
        sortino_ratio = excess_returns / downside_std if downside_std > 0 else 0
        
        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # Value at Risk (95%)
        var_95 = np.percentile(returns, 5) * 100
        
        # Conditional VaR (Expected Shortfall)
        cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * 100
        
        # Diversification Ratio
        # Individual asset volatilities weighted
        individual_vols = self.returns.std() * np.sqrt(252)
        weighted_avg_vol = sum(self.weights.get(asset, 0) * individual_vols.get(asset, 0) 
                              for asset in self.assets)
        portfolio_vol = returns.std() * np.sqrt(252)
        diversification_ratio = weighted_avg_vol / portfolio_vol if portfolio_vol > 0 else 1
        
        # Calmar Ratio
        calmar_ratio = (returns.mean() * 252) / abs(max_drawdown/100) if max_drawdown != 0 else 0
        
        return {
            'total_return': total_return,
            'portfolio_volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'diversification_ratio': diversification_ratio,
            'calmar_ratio': calmar_ratio,
            'final_value': portfolio_value.iloc[-1]
        }
    
    def calculate_correlation_matrix(self) -> pd.DataFrame:
        """
        Calculate asset correlation matrix.
        
        Returns:
            Correlation matrix DataFrame
        """
        return self.returns.corr()
    
    def calculate_covariance_matrix(self) -> pd.DataFrame:
        """
        Calculate asset covariance matrix (annualized).
        
        Returns:
            Covariance matrix DataFrame
        """
        return self.returns.cov() * 252
    
    def simulate_rebalancing(self, frequency: str = "Monthly") -> Tuple[pd.Series, Dict]:
        """
        Simulate portfolio with periodic rebalancing.
        
        Args:
            frequency: Rebalancing frequency ("Monthly", "Quarterly", "Yearly")
            
        Returns:
            Tuple of (portfolio value series, metrics dictionary)
        """
        # Map frequency to pandas offset
        freq_map = {
            "Monthly": "ME",
            "Quarterly": "QE",
            "Yearly": "YE"
        }
        
        offset = freq_map.get(frequency, "ME")
        
        # Get rebalancing dates
        rebal_dates = self.prices.resample(offset).last().index
        
        # Initialize portfolio
        portfolio_value = pd.Series(dtype=float)
        current_capital = self.initial_capital
        current_holdings = {}
        
        # Initial allocation
        for asset in self.assets:
            if asset in self.weights:
                allocation = current_capital * self.weights[asset]
                shares = allocation / self.prices[asset].iloc[0]
                current_holdings[asset] = shares
        
        # Simulate day by day
        for i, date in enumerate(self.prices.index):
            # Calculate current value
            daily_value = sum(
                current_holdings.get(asset, 0) * self.prices[asset].loc[date]
                for asset in self.assets
            )
            portfolio_value.loc[date] = daily_value
            
            # Rebalance if needed
            if date in rebal_dates and i > 0:
                current_capital = daily_value
                for asset in self.assets:
                    if asset in self.weights:
                        allocation = current_capital * self.weights[asset]
                        shares = allocation / self.prices[asset].loc[date]
                        current_holdings[asset] = shares
        
        # Calculate returns and metrics
        returns = portfolio_value.pct_change().dropna()
        metrics = self._calculate_metrics(returns, portfolio_value)
        
        return portfolio_value, metrics
    
    def calculate_efficient_frontier(self, n_portfolios: int = 1000) -> pd.DataFrame:
        """
        Calculate efficient frontier using Monte Carlo simulation.
        
        Args:
            n_portfolios: Number of random portfolios to generate
            
        Returns:
            DataFrame with portfolio returns, volatilities, and weights
        """
        results = []
        
        n_assets = len(self.assets)
        
        for _ in range(n_portfolios):
            # Generate random weights
            weights = np.random.random(n_assets)
            weights /= weights.sum()
            
            # Calculate portfolio return and volatility
            port_return = np.sum(self.returns.mean() * weights) * 252
            port_vol = np.sqrt(np.dot(weights.T, np.dot(self.returns.cov() * 252, weights)))
            
            # Sharpe ratio
            sharpe = (port_return - 0.02) / port_vol
            
            results.append({
                'Return': port_return * 100,
                'Volatility': port_vol * 100,
                'Sharpe': sharpe,
                **{f'Weight_{asset}': w for asset, w in zip(self.assets, weights)}
            })
        
        return pd.DataFrame(results)
    
    def get_asset_contribution(self) -> pd.DataFrame:
        """
        Calculate each asset's contribution to portfolio risk and return.
        
        Returns:
            DataFrame with asset contributions
        """
        # Calculate marginal contributions
        cov_matrix = self.returns.cov() * 252
        weights_array = np.array([self.weights.get(asset, 0) for asset in self.assets])
        
        # Portfolio volatility
        port_vol = np.sqrt(np.dot(weights_array.T, np.dot(cov_matrix, weights_array)))
        
        # Marginal contribution to risk
        mcr = np.dot(cov_matrix, weights_array) / port_vol
        
        # Component contribution to risk
        ccr = weights_array * mcr
        
        # Return contribution
        mean_returns = self.returns.mean() * 252
        return_contrib = weights_array * mean_returns.values
        
        contribution_df = pd.DataFrame({
            'Asset': self.assets,
            'Weight': [self.weights.get(asset, 0) * 100 for asset in self.assets],
            'Return Contribution': return_contrib * 100,
            'Risk Contribution': ccr / ccr.sum() * 100,
            'Marginal Risk': mcr * 100
        })
        
        return contribution_df
    
    def stress_test(self, scenarios: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """
        Perform stress testing on the portfolio.
        
        Args:
            scenarios: Dictionary of scenario names to asset shocks
            
        Returns:
            DataFrame with stress test results
        """
        results = []
        
        current_value = self.initial_capital * (1 + self.returns.sum()).prod()
        
        for scenario_name, shocks in scenarios.items():
            stressed_value = 0
            
            for asset in self.assets:
                weight = self.weights.get(asset, 0)
                shock = shocks.get(asset, 0)
                
                asset_value = current_value * weight
                stressed_asset_value = asset_value * (1 + shock/100)
                stressed_value += stressed_asset_value
            
            pnl = stressed_value - current_value
            pnl_pct = (pnl / current_value) * 100
            
            results.append({
                'Scenario': scenario_name,
                'Portfolio Value': stressed_value,
                'P&L': pnl,
                'P&L (%)': pnl_pct
            })
        
        return pd.DataFrame(results)


def calculate_optimal_weights(returns: pd.DataFrame, target_return: float = None) -> Dict[str, float]:
    """
    Calculate optimal portfolio weights using mean-variance optimization.
    
    Args:
        returns: DataFrame of asset returns
        target_return: Target portfolio return (optional)
        
    Returns:
        Dictionary of optimal weights
    """
    from scipy.optimize import minimize
    
    n_assets = len(returns.columns)
    assets = returns.columns.tolist()
    
    # Expected returns and covariance
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    
    def portfolio_volatility(weights):
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    
    def neg_sharpe_ratio(weights):
        port_return = np.sum(mean_returns * weights)
        port_vol = portfolio_volatility(weights)
        return -(port_return - 0.02) / port_vol
    
    # Constraints
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    
    if target_return is not None:
        constraints.append({
            'type': 'eq',
            'fun': lambda x: np.sum(mean_returns * x) - target_return
        })
    
    # Bounds (0 to 1 for each asset - no short selling)
    bounds = tuple((0, 1) for _ in range(n_assets))
    
    # Initial guess (equal weights)
    initial_weights = np.array([1/n_assets] * n_assets)
    
    # Optimize
    result = minimize(
        neg_sharpe_ratio,
        initial_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )
    
    if result.success:
        return {asset: weight for asset, weight in zip(assets, result.x)}
    else:
        # Return equal weights if optimization fails
        return {asset: 1/n_assets for asset in assets}
