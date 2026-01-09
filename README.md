---

# Quant B — Multi-Asset Portfolio Module

### Objective
The goal of this module is to extend the analysis to a multivariate setting, allowing the user to construct a portfolio and analyze the effects of diversification on risk and return.

### Implemented Strategies
* [cite_start]**Equal Weight Portfolio:** Automatically distributes capital equally among all selected assets[cite: 42].
* [cite_start]**Custom Weight Allocation:** Allows the user to manually define specific weights for each asset to test different exposure scenarios[cite: 43].

### Methodology
* [cite_start]**Multi-Asset Data Fetching:** Historical prices are retrieved simultaneously for a basket of assets[cite: 41].
* **Portfolio Construction:** Daily portfolio returns are computed based on the user-defined allocation weights.
* [cite_start]**Diversification Analysis:** A correlation matrix is computed to visualize the relationships between assets[cite: 42].
* [cite_start]**Benchmarking:** The main chart compares the portfolio's cumulative return against individual component assets[cite: 44].

### Metrics
* [cite_start]**Correlation Matrix:** Heatmap to assess diversification potential between assets[cite: 42].
* [cite_start]**Portfolio Volatility & Annualized Return:** Risk and performance metrics for the aggregated portfolio[cite: 42].
* **Diversification Effect:** Visual comparison showing risk reduction compared to single assets.

### Results Interpretation
By combining assets with less than perfect correlation, the portfolio generally achieves lower volatility than the most volatile individual assets, illustrating the benefits of diversification.
