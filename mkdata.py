import pandas as pd
from pathlib import Path

# =====================================
# 프로젝트 경로 설정
# =====================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = BASE_DIR / "processed"

PROCESSED_DIR.mkdir(exist_ok=True)

# =====================================
# 파일 경로
# =====================================

file_path = DATA_DIR / "2326_summer_data.csv"

# =====================================
# CSV 읽기
# =====================================

df = pd.read_csv(
    file_path,
    encoding="cp949",
    skiprows=6
)

# =====================================
# 컬럼 확인
# =====================================

# print(df.columns)

# =====================================
# 컬럼명 변경
# =====================================

df.columns = [
    "date",
    "station",
    # "station_name",
    "mean_temp",
    "min_temp",
    "max_temp"
]

# =====================================
# 날짜 변환
# =====================================

df["date"] = pd.to_datetime(df["date"])

# =====================================
# 숫자형 변환
# =====================================

temp_cols = [
    "mean_temp",
    "min_temp",
    "max_temp"
]

for col in temp_cols:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

# =====================================
# 폭염 여부
# 최고기온 30도 이상
# =====================================

df["heatwave"] = (
    df["max_temp"] >= 30
).astype(int)

# =====================================
# 연/월 컬럼
# =====================================

df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

# =====================================
# 여름철 데이터만 추출
# =====================================

summer_df = df[
    df["month"].isin([6, 7, 8])
].copy()

# =====================================
# 폭염 데이터만 추출
# =====================================

heatwave_df = summer_df[
    summer_df["heatwave"] == 1
].copy()

# =====================================
# 저장
# =====================================

summer_output = (
    PROCESSED_DIR /
    "seoul_summer_temperature.csv"
)

heatwave_output = (
    PROCESSED_DIR /
    "seoul_heatwave_only.csv"
)

summer_df.to_csv(
    summer_output,
    index=False,
    encoding="utf-8-sig"
)

heatwave_df.to_csv(
    heatwave_output,
    index=False,
    encoding="utf-8-sig"
)

# =====================================
# 결과 확인
# =====================================

print("\n저장 완료")

print(f"""
여름철 데이터:
{summer_output}
""")

print(f"""
폭염 데이터:
{heatwave_output}
""")

print("\n샘플 데이터")
print(summer_df.head())