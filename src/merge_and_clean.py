from pathlib import Path
import pandas as pd
import glob

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = PROJECT_ROOT / "data" / "clean_price_data.csv"

files = sorted(glob.glob(str(RAW_DIR / "*.csv")))

print("Project root:", PROJECT_ROOT)
print("Raw dir:", RAW_DIR)
print("Files found:", len(files))

if not files:
    raise FileNotFoundError(f"No CSV files found in {RAW_DIR}")

df_list = []
for file in files:
    df = pd.read_csv(file)
    df_list.append(df)

df = pd.concat(df_list, ignore_index=True)

print("Columns:", df.columns.tolist())

time_col = "MTU (CET/CEST)"
price_col = "Day-ahead Price (EUR/MWh)"
sequence_col = "Sequence"

# 只保留 Sequence 1
df = df[df[sequence_col].astype(str).str.contains("1", na=False)].copy()

# 提取开始时间
df["timestamp"] = pd.to_datetime(
    df[time_col].astype(str).str.split(" - ").str[0],
    dayfirst=True,
    errors="coerce"
)

# 提取价格
df["price"] = pd.to_numeric(df[price_col], errors="coerce")

# 保留核心列
df = df[["timestamp", "price"]].dropna()

# 排序去重
df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="first")

# 保存
df.to_csv(OUTPUT_FILE, index=False)

print("Done! Clean data saved to:")
print(OUTPUT_FILE)
print(df.head())
print(df.tail())
print("Total rows:", len(df))
print("Duplicate timestamps:", df["timestamp"].duplicated().sum())