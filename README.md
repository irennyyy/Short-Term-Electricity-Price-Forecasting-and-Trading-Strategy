Short term electricity price trading strategy
1. Overview

This project investigates short-term trading strategies using 15-minute German day-ahead electricity price data.

The goal is not just to build a profitable strategy, but to evaluate whether simple signals remain robust under realistic conditions, including:

Data cleaning
Transaction costs
Outlier filtering
Train/test split (out-of-sample validation)

2. Dataset
Source: ENTSO-E Transparency Platform
Market: Germany (BZN|DE-LU)
Frequency: 15-minute intervals
Period: March 2026
Key fields:
timestamp
price (EUR/MWh)


3. Data Processing

Raw CSV files were merged and cleaned:

Combined multiple daily files
Parsed timestamps from MTU format
Removed duplicated entries (Sequence 1 vs Sequence 2)
Filtered extreme values (top/bottom 1%) to reduce spikes impact
Sorted and resampled into a continuous time series

Final dataset:

~2700 observations
Cleaned and aligned time series


4. Methodology
4.1 Train / Test Split
Train: before 2026-03-21
Test: after 2026-03-21

This ensures out-of-sample evaluation, avoiding misleading in-sample results.


4. Methodology
4.1 Train / Test Split
Train: before 2026-03-21
Test: after 2026-03-21

This ensures out-of-sample evaluation, avoiding misleading in-sample results.


(2) Mean-Reversion Strategy
Rolling window: 8 hours
Z-score:[]


Trading rules:

Short if z > 1.5
Long if z < -1.5
Exit when |z| < 0.3
Cooldown period applied to reduce over-trading

4.3 Backtesting Assumptions
PnL based on price differences
Transaction cost applied per position change
Signals are shifted to avoid look-ahead bias
Scaled PnL used for stability

5. Result

| Strategy        | Dataset | Final PnL | Sharpe | Max Drawdown |
| Trend-following | Test    | Positive  | High   | Moderate     |
| Mean-reversion  | Test    | Negative  | Low    | Large        |

Key Findings
1. Strategy performance is not stable across time
Mean-reversion works in training data
Fails in test period
2. Trend-following is more robust out-of-sample
Positive PnL in test set
Better risk-adjusted performance
3. Electricity prices are regime-dependent
Some periods show mean-reverting behaviour
Others exhibit trending dynamics


6. Visualisation

The project includes:

Price with moving averages
Z-score signals
Train/test split visualisation
Strategy PnL comparison

Example outputs:

price_ma_plot.png
zscore_plot.png
test_strategy_comparison_pnl.png

7. Key Takeaway

This project demonstrates that:

Apparent profitability in historical data does not guarantee out-of-sample performance.

Simple strategies such as mean-reversion may look effective in-sample but fail when tested on unseen data.

Robust evaluation requires:

Proper data cleaning
Transaction cost modelling
Out-of-sample testing

8. Future Improvements
- Add volatility-based position sizing
- Include intraday price signals
- Try machine learning models (e.g. regression / LSTM)
- Incorporate external features (weather, demand, renewables)

