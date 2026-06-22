import pandas as pd
from pathlib import Path

from utils.climate import *

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw" / "climate"
PROCESSED_DIR = BASE_DIR / "data" / "processed" / "climate"

file_path = RAW_DIR / "avg_temp.csv"

df = pd.read_csv(
    file_path,
    encoding="cp949",
    skiprows=6
)

df.columns = [
    "date",
    "station",
    "mean_temp",
    "min_temp",
    "max_temp"
]

for col in [
    "mean_temp",
    "min_temp",
    "max_temp"
]:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = add_year_month(df)

df = filter_years(df)

summer_df = filter_summer(df)

summer_df["heatwave"] = (
    summer_df["max_temp"] >= 30
).astype(int)

avg_temp = yearly_mean(
    summer_df,
    "mean_temp",
    "summer_avg_temp"
)

max_temp = yearly_mean(
    summer_df,
    "max_temp",
    "summer_max_temp"
)

heatwave = (
    summer_df
    .groupby("year")["heatwave"]
    .sum()
    .reset_index()
    .rename(columns={
        "heatwave":
        "summer_heatwave_days"
    })
)

result = (
    avg_temp
    .merge(max_temp, on="year")
    .merge(heatwave, on="year")
)

save_csv(
    result,
    PROCESSED_DIR / "avg_temp.csv"
)

print(result)