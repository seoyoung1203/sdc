import pandas as pd
from pathlib import Path

# ============================================
# 경로 설정
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

PROCESSED_DIR.mkdir(exist_ok=True)

# ============================================
# 파일 경로
# ============================================

file_path = RAW_DIR / "seoul_heat_index.csv"

# ============================================
# CSV 읽기
# 검색조건 부분 제거
# ============================================

df = pd.read_csv(
    file_path,
    encoding="cp949",
    skiprows=3
)

# print(df.columns)

# ============================================
# 컬럼명 변경
# ============================================

df = df.rename(columns={
    "일자": "date",
    "기온(°C)": "temp",
    "습도(%rh)": "humidity",
    "체감온도(°C)": "heat_index"
})

# ============================================
# 날짜 변환
# ============================================

df["date"] = pd.to_datetime(df["date"])

# ============================================
# 숫자형 변환
# ============================================

num_cols = [
    "temp",
    "humidity",
    "heat_index"
]

for col in num_cols:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

# ============================================
# 연도 / 월 추가
# ============================================

df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month

# ============================================
# 폭염 여부 생성
# 체감온도 33도 이상
# ============================================

df["severe_heat"] = (
    df["heat_index"] >= 30
).astype(int)

# ============================================
# 폭염 데이터만 따로 저장
# ============================================

heatwave_df = df[
    df["severe_heat"] == 1
]

# ============================================
# 저장
# ============================================

output_path = (
    PROCESSED_DIR /
    "seoul_heat_index_processed.csv"
)

df.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"
)

# ============================================
# 폭염일만 저장
# ============================================

heatwave_output = (
    PROCESSED_DIR /
    "seoul_severe_heat_only.csv"
)

heatwave_df.to_csv(
    heatwave_output,
    index=False,
    encoding="utf-8-sig"
)

# ============================================
# 확인
# ============================================

print(df.head())

print("\n폭염일 수")
print(len(heatwave_df))

print("\n저장 완료")
print(output_path)