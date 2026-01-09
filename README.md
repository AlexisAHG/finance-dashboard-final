# Finance Dashboard Project

## DIRECT ACCESS TO LIVE SITE
The application is fully functional and accessible via the following link:
http://34.140.210.188:8501/

(The project runs 24/7 on a Google Cloud Virtual Machine).

---

## Team & Roles
This project was completed by a team of two students:
* **Quant A (Single Asset Module):** Vivien Winnoc
* **Quant B (Portfolio Module):** Alexis Hanna (@AlexisAHG)

## Project Description
This platform supports fundamental portfolio managers with quantitative tools. It aims to simulate a professional workflow where users can:
1. Retrieve real-time financial data for multiple assets.
2. Backtest trading strategies on single assets (Quant A).
3. Simulate portfolio allocation and analyze diversification effects (Quant B).

## Local Installation
To run the project locally on your machine, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/AlexisAHG/finance-dashboard-final.git](https://github.com/AlexisAHG/finance-dashboard-final.git)
    cd finance-dashboard-final
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Launch the application:**
    ```bash
    streamlit run app.py
    ```

---

## Quant A — Single Asset Backtesting Module

### Objective
The goal of this module is to evaluate systematic trading strategies
on a single asset using historical price data.

### Implemented Strategies
- Buy & Hold
- Momentum (configurable lookback window)

### Methodology
- Historical prices are fetched from external data providers
- Trading positions are computed using lagged signals
- Equity curves are computed using a vectorized backtesting engine
- Performance metrics are evaluated on the resulting equity curve

### Metrics
- Sharpe Ratio (annualized)
- Maximum Drawdown

### Results Interpretation
The momentum strategy allows capturing medium-term trends,
while Buy & Hold serves as a baseline benchmark.

---

# Quant B — Multi-Asset Portfolio Module

### Objective
The goal of this module is to extend the analysis to a multivariate setting, simulating portfolio performance across multiple assets (e.g., AAPL, MSFT, GOOGL) to observe diversification effects.

### Implemented Strategies
* **Equal Weight Portfolio:** Automatically distributes capital equally among selected assets.
* **Custom Weight Allocation:** Allows the user to define specific weights for each asset to test different exposure scenarios.

### Methodology
* **Multi-Asset Data Fetching:** Concurrent retrieval of historical prices for a basket of assets.
* **Portfolio Construction:** Calculation of weighted returns based on user-defined allocation.
* **Diversification Analysis:** Computation of the correlation matrix to visualize relationships between assets.
* **Benchmarking:** Comparison of the portfolio's cumulative return against individual component assets.

### Metrics
* **Portfolio Volatility & Return:** Annualized risk and return metrics for the aggregated portfolio.
* **Correlation Matrix:** Heatmap visualization to assess diversification potential.
* **Diversification Effect:** Visual comparison showing how the portfolio mitigates risk compared to holding single volatile assets.


