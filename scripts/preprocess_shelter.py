# ============================================
# 서울시 무더위쉼터 데이터 전처리
# ============================================

# 목적
# - GIS 분석 가능 형태로 정리
# - 취약성 지수 계산용 데이터 구축
# - 자치구별 쉼터 밀도 분석 가능 구조 생성
#
# 결과:
# data/processed/seoul_heat_shelter_processed.csv
# ============================================

import pandas as pd
from pathlib import Path

# ============================================
# 프로젝트 경로 설정
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

PROCESSED_DIR.mkdir(exist_ok=True)

# ============================================
# 파일 경로
# ============================================

file_path = RAW_DIR / "seoul_heat_shelter.csv"

# ============================================
# CSV 읽기
# ============================================

df = pd.read_csv(
    file_path,
    encoding="cp949"
)

# ============================================
# 원본 컬럼 확인
# ============================================

print("\n원본 컬럼")
print(df.columns)

# ============================================
# 컬럼명 표준화
# 실제 컬럼명에 맞게 수정 가능
# ============================================

rename_dict = {
    "쉼터명": "shelter_name",
    "시설명": "shelter_name",
    "자치구": "gu",
    "구": "gu",
    "주소": "address",
    "도로명주소": "address",
    "위도": "lat",
    "경도": "lon",
    "운영상태": "status",
    "시설유형": "facility_type"
}

df = df.rename(columns=rename_dict)

# ============================================
# 필요한 컬럼만 선택
# 실제 데이터 컬럼에 따라 자동 선택
# ============================================

wanted_cols = [
    "shelter_name",
    "gu",
    "address",
    "lat",
    "lon",
    "status",
    "facility_type"
]

existing_cols = [
    col for col in wanted_cols
    if col in df.columns
]

df = df[existing_cols]

# ============================================
# 문자열 공백 제거
# ============================================

str_cols = df.select_dtypes(include="object").columns

for col in str_cols:
    df[col] = df[col].astype(str).str.strip()

# ============================================
# 위도/경도 숫자형 변환
# ============================================

coord_cols = ["lat", "lon"]

for col in coord_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

# ============================================
# 운영 여부 정리
# ============================================

if "status" in df.columns:

    df["open"] = (
        df["status"]
        .astype(str)
        .str.contains("운영", na=False)
    ).astype(int)

# ============================================
# 결측치 확인
# ============================================

print("\n결측치 확인")
print(df.isnull().sum())

# ============================================
# 중복 제거
# ============================================

before_count = len(df)

df = df.drop_duplicates()

after_count = len(df)

print(f"\n중복 제거: {before_count - after_count}개")

# ============================================
# 쉼터 ID 생성
# ============================================

df = df.reset_index(drop=True)

df["shelter_id"] = df.index + 1

# shelter_id를 맨 앞으로
cols = ["shelter_id"] + [
    col for col in df.columns
    if col != "shelter_id"
]

df = df[cols]

# ============================================
# 저장
# ============================================

output_path = (
    PROCESSED_DIR /
    "seoul_heat_shelter_processed.csv"
)

df.to_csv(
    output_path,
    index=False,
    encoding="utf-8-sig"
)

# ============================================
# 결과 확인
# ============================================

print("\n저장 완료")
print(output_path)

print("\n데이터 샘플")
print(df.head())

print("\n전체 데이터 수")
print(len(df))
