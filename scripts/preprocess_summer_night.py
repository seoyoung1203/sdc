import pandas as pd
from pathlib import Path

from utils.climate import (
    load_yearly_climate_csv,
    filter_years,
    save_csv
)

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw" / "climate"
PROCESSED_DIR = BASE_DIR / "data" / "processed" / "climate"

file_path = RAW_DIR / "summer_night.csv"

df = load_yearly_climate_csv(file_path)

df = df.rename(columns={
    "6월": "jun",
    "7월": "jul",
    "8월": "aug"
})

for col in ["jun", "jul", "aug"]:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

# 핵심!
df = df[
    df["jun"].notna()
].copy()

df = df.rename(columns={
    df.columns[0]: "year"
})

df = filter_years(df)

result = pd.DataFrame()

result["year"] = df["year"]

result["summer_tropical_nights"] = (
    df["jun"] +
    df["jul"] +
    df["aug"]
)

save_csv(
    result,
    PROCESSED_DIR / "summer_night.csv"
)

print(result)