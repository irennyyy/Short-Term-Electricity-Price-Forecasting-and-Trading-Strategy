# Short-Term Electricity Price Forecasting and Trading Strategy

## Overview

This project investigates short-term trading strategies using 15-minute German day-ahead electricity price data.

The objective is not only to design trading signals, but to evaluate their robustness under realistic conditions, including data cleaning, transaction costs, and out-of-sample testing.

---

## Dataset

* Source: ENTSO-E Transparency Platform
* Market: Germany (BZN|DE-LU)
* Frequency: 15-minute intervals
* Period: March 2026

---

## Data Processing

* Merged multiple daily CSV files
* Parsed timestamps from MTU format
* Removed duplicated entries
* Filtered extreme values (top/bottom 1%)
* Generated a clean and continuous time series

---

## Methodology

### Train/Test Split

* Train: before 2026-03-21
* Test: after 2026-03-21

---

### Strategies

#### Trend-Following

* Short MA: 2 hours
* Long MA: 8 hours
* Long when short MA > long MA

#### Mean-Reversion

* Rolling window: 8 hours
* Z-score based signals
* Entry and exit thresholds with cooldown

---

### Backtesting Design

* Transaction costs included
* Signals shifted to avoid look-ahead bias
* Scaled PnL used to handle electricity price characteristics

---

## Results

![Price and Moving Averages](results/price_ma_plot.png)

![Strategy Performance](results/test_strategy_comparison_pnl.png)

---

## Key Findings

* Strategy performance is highly regime-dependent
* Mean-reversion performs well in-sample but fails out-of-sample
* Trend-following is more robust in the test period
* Standard financial strategies do not directly transfer to electricity markets

---

## Project Structure

```
├── src/
├── data/
├── results/
├── README.md
├── requirements.txt
```

---

## Key Takeaway

Out-of-sample evaluation significantly changes conclusions.

Apparent profitability in historical data does not guarantee real-world performance.
