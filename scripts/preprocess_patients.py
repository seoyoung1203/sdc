import pandas as pd
from pathlib import Path

from utils.outcome import (
    save_csv,
    clean_district_name,
    filter_seoul
)

# ============================================
# 경로
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = (
    BASE_DIR /
    "data" /
    "raw" /
    "outcome"
)

PROCESSED_DIR = (
    BASE_DIR /
    "data" /
    "processed" /
    "outcome"
)

# ============================================
# 파일
# ============================================

file_path = (
    RAW_DIR /
    "heat_patients_sigungu.csv"
)

# ============================================
# 읽기
# ============================================

df = pd.read_csv(
    file_path,
    encoding="cp949"
)

# ============================================
# 컬럼명
# ============================================

df = df.rename(columns={
    "진료개시년도": "year",
    "지역": "district",
    "환자수": "heat_patients"
})

districts = sorted(df["district"].unique())

for d in districts:
    print(d)

# ============================================
# 2023~2025
# ============================================

df["year"] = pd.to_numeric(
    df["year"],
    errors="coerce"
)

df = df[
    df["year"].between(2023, 2025)
]

# ============================================
# 구 이름 정리
# ============================================

df = clean_district_name(
    df,
    "district"
)

# 서울 25개구만 남김
df = filter_seoul(
    df,
    "district"
)

# ============================================
# 구별 환자수
# ============================================

result = (
    df.groupby("district")[
        "heat_patients"
    ]
    .sum()
    .reset_index()
)

# ============================================
# 저장
# ============================================

save_csv(
    result,
    PROCESSED_DIR /
    "heat_patients.csv"
)

print(result.head())