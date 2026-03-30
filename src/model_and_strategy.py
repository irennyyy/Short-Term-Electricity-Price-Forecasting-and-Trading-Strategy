from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "clean_price_data.csv"
RESULTS_DIR = PROJECT_ROOT / "results"

RESULTS_DIR.mkdir(exist_ok=True)

# =========================
# 1. Load data
# =========================
df = pd.read_csv(DATA_FILE)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)

print("Data loaded successfully")
print(df.head())
print("Total rows before filtering:", len(df))

# =========================
# 2. Remove extreme spikes
# =========================
upper_cap = df["price"].quantile(0.99)
lower_cap = df["price"].quantile(0.01)
df = df[(df["price"] < upper_cap) & (df["price"] > lower_cap)].copy().reset_index(drop=True)

print(f"\nRemoved extreme tails. Lower cap = {lower_cap:.2f}, Upper cap = {upper_cap:.2f}")
print("Total rows after filtering:", len(df))

# =========================
# 3. Feature engineering on FULL dataset
# =========================
df["ma_short"] = df["price"].rolling(window=8).mean()      # 2 hours
df["ma_long"] = df["price"].rolling(window=32).mean()      # 8 hours

df["roll_mean"] = df["price"].rolling(window=32).mean()
df["roll_std"] = df["price"].rolling(window=32).std()

df["zscore"] = (df["price"] - df["roll_mean"]) / df["roll_std"]

# 用于标准化PnL，避免接近0的价格导致爆炸
df["price_scale"] = df["roll_mean"].abs().clip(lower=1.0)

# =========================
# 4. Generate signals on FULL dataset
# =========================

# ---- Trend-following ----
df["trend_signal"] = 0
df.loc[df["ma_short"] > df["ma_long"], "trend_signal"] = 1

# ---- Mean-reversion ----
df["mr_signal"] = 0

entry_threshold_high = 2.0
entry_threshold_low = -1.0
exit_threshold = 0.3
cooldown_periods = 4

current_position = 0
cooldown = 0

for i in range(len(df)):
    z = df.loc[i, "zscore"]

    if pd.isna(z):
        df.loc[i, "mr_signal"] = 0
        continue

    if cooldown > 0:
        cooldown -= 1

    if current_position == 0 and cooldown == 0:
        if z > entry_threshold_high:
            current_position = -1   # too high -> short
        elif z < entry_threshold_low:
            current_position = 1    # too low -> long

    elif current_position == 1:
        if z >= -exit_threshold:
            current_position = 0
            cooldown = cooldown_periods

    elif current_position == -1:
        if z <= exit_threshold:
            current_position = 0
            cooldown = cooldown_periods

    df.loc[i, "mr_signal"] = current_position

# =========================
# 5. Backtest using scaled PnL
# =========================
transaction_cost = 0.001

df["price_change"] = df["price"].diff()

# 标准化后的单期收益 proxy
df["scaled_move"] = df["price_change"] / df["price_scale"]

# baseline
df["market_pnl"] = df["scaled_move"]

# trend-following
df["trend_position_change"] = df["trend_signal"].diff().abs().fillna(0)
df["trend_cost"] = df["trend_position_change"] * transaction_cost
df["trend_pnl"] = df["trend_signal"].shift(1) * df["scaled_move"] - df["trend_cost"]

# mean-reversion
df["mr_position_change"] = df["mr_signal"].diff().abs().fillna(0)
df["mr_cost"] = df["mr_position_change"] * transaction_cost
df["mr_pnl"] = df["mr_signal"].shift(1) * df["scaled_move"] - df["mr_cost"]

# cumulative pnl
df["cum_market_pnl"] = df["market_pnl"].fillna(0).cumsum()
df["cum_trend_pnl"] = df["trend_pnl"].fillna(0).cumsum()
df["cum_mr_pnl"] = df["mr_pnl"].fillna(0).cumsum()

# =========================
# 6. Train / Test split AFTER features
# =========================
split_date = pd.Timestamp("2026-03-21 00:00:00")

train_df = df[df["timestamp"] < split_date].copy()
test_df = df[df["timestamp"] >= split_date].copy()

print("\nTrain rows:", len(train_df))
print("Test rows:", len(test_df))

# =========================
# 7. Metrics
# =========================
def sharpe_ratio(pnl_series, periods_per_year=96 * 365):
    s = pnl_series.dropna()
    if len(s) == 0 or s.std() == 0:
        return np.nan
    return s.mean() / s.std() * np.sqrt(periods_per_year)

def max_drawdown(cum_pnl_series):
    s = cum_pnl_series.dropna()
    if len(s) == 0:
        return np.nan
    peak = s.cummax()
    drawdown = s - peak
    return drawdown.min()

def summarise(subdf, label):
    market_final = subdf["cum_market_pnl"].dropna().iloc[-1] if subdf["cum_market_pnl"].dropna().size > 0 else np.nan
    trend_final = subdf["cum_trend_pnl"].dropna().iloc[-1] if subdf["cum_trend_pnl"].dropna().size > 0 else np.nan
    mr_final = subdf["cum_mr_pnl"].dropna().iloc[-1] if subdf["cum_mr_pnl"].dropna().size > 0 else np.nan

    return pd.DataFrame({
        "dataset": [label, label, label],
        "strategy": ["market", "trend_following", "mean_reversion"],
        "final_pnl": [market_final, trend_final, mr_final],
        "sharpe": [
            np.nan,
            sharpe_ratio(subdf["trend_pnl"]),
            sharpe_ratio(subdf["mr_pnl"])
        ],
        "max_drawdown": [
            np.nan,
            max_drawdown(subdf["cum_trend_pnl"]),
            max_drawdown(subdf["cum_mr_pnl"])
        ],
        "trade_count": [
            np.nan,
            subdf["trend_position_change"].sum(),
            subdf["mr_position_change"].sum()
        ]
    })

full_summary = summarise(df, "full")
train_summary = summarise(train_df, "train")
test_summary = summarise(test_df, "test")
summary = pd.concat([full_summary, train_summary, test_summary], ignore_index=True)

# =========================
# 8. Save results
# =========================
df.to_csv(RESULTS_DIR / "full_strategy_results.csv", index=False)
train_df.to_csv(RESULTS_DIR / "train_strategy_results.csv", index=False)
test_df.to_csv(RESULTS_DIR / "test_strategy_results.csv", index=False)
summary.to_csv(RESULTS_DIR / "strategy_summary.csv", index=False)

# =========================
# 9. Plots
# =========================

plt.figure(figsize=(12, 6))
plt.plot(df["timestamp"], df["price"], label="Price")
plt.plot(df["timestamp"], df["ma_short"], label="Short MA (2h)")
plt.plot(df["timestamp"], df["ma_long"], label="Long MA (8h)")
plt.axvline(split_date, linestyle="--", label="Train/Test Split")
plt.title("Electricity Price with Moving Averages")
plt.xlabel("Time")
plt.ylabel("Price (EUR/MWh)")
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS_DIR / "price_ma_plot.png")
plt.close()

plt.figure(figsize=(12, 6))
plt.plot(df["timestamp"], df["zscore"], label="Z-score")
plt.axhline(entry_threshold_high, linestyle="--", label="Upper Entry")
plt.axhline(entry_threshold_low, linestyle="--", label="Lower Entry")
plt.axhline(exit_threshold, linestyle=":", label="Upper Exit")
plt.axhline(-exit_threshold, linestyle=":", label="Lower Exit")
plt.axvline(split_date, linestyle="--", label="Train/Test Split")
plt.title("Mean-Reversion Z-score Signal")
plt.xlabel("Time")
plt.ylabel("Z-score")
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS_DIR / "zscore_plot.png")
plt.close()

plt.figure(figsize=(12, 6))
plt.plot(df["timestamp"], df["cum_market_pnl"], label="Market")
plt.plot(df["timestamp"], df["cum_trend_pnl"], label="Trend")
plt.plot(df["timestamp"], df["cum_mr_pnl"], label="Mean Reversion")
plt.axvline(split_date, linestyle="--", label="Train/Test Split")
plt.title("Cumulative Scaled PnL Comparison")
plt.xlabel("Time")
plt.ylabel("Cumulative Scaled PnL")
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS_DIR / "strategy_comparison_pnl.png")
plt.close()

plt.figure(figsize=(12, 6))
plt.plot(test_df["timestamp"], test_df["cum_market_pnl"], label="Market")
plt.plot(test_df["timestamp"], test_df["cum_trend_pnl"], label="Trend")
plt.plot(test_df["timestamp"], test_df["cum_mr_pnl"], label="Mean Reversion")
plt.title("Test Set Cumulative Scaled PnL Comparison")
plt.xlabel("Time")
plt.ylabel("Cumulative Scaled PnL")
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS_DIR / "test_strategy_comparison_pnl.png")
plt.close()

# =========================
# 10. Print summary
# =========================
print("\n===== Strategy Summary =====")
print(summary)

print("\nResults saved to:", RESULTS_DIR)