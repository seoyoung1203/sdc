import pandas as pd
from pathlib import Path

from utils.climate import *

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw" / "climate"
PROCESSED_DIR = BASE_DIR / "data" / "processed" / "climate"

file_path = RAW_DIR / "seoul_heat_index.csv"

df = pd.read_csv(
    file_path,
    encoding="cp949",
    skiprows=3
)

df = df.rename(columns={
    "일자": "date",
    "기온(°C)": "temp",
    "습도(%rh)": "humidity",
    "체감온도(°C)": "heat_index"
})

for col in [
    "temp",
    "humidity",
    "heat_index"
]:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = add_year_month(df)

df = filter_years(df)

summer_df = filter_summer(df)

heat_index = yearly_mean(
    summer_df,
    "heat_index",
    "summer_avg_heat_index"
)

humidity = yearly_mean(
    summer_df,
    "humidity",
    "summer_avg_humidity"
)

result = (
    heat_index
    .merge(humidity, on="year")
)

save_csv(
    result,
    PROCESSED_DIR / "heat_index.csv"
)

print(result)