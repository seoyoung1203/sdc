from pathlib import Path
import pandas as pd

# ==================================================
# 경로 설정
# ==================================================
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(exist_ok=True)

# ==================================================
# 원본 데이터 읽기
# ==================================================
input_file = RAW_DIR / "heat_patients_sigungu.csv"

df = pd.read_csv(input_file, encoding="cp949")

# ==================================================
# 서울 25개 자치구
# ==================================================
SEOUL_DISTRICTS = [
    "종로구", "중구", "용산구", "성동구", "광진구",
    "동대문구", "중랑구", "성북구", "강북구", "도봉구",
    "노원구", "은평구", "서대문구", "마포구", "양천구",
    "강서구", "구로구", "금천구", "영등포구", "동작구",
    "관악구", "서초구", "강남구", "송파구", "강동구"
]

# ==================================================
# 서울 지역만 필터링
# ==================================================
df = df[df["지역"].isin(SEOUL_DISTRICTS)].copy()

# ==================================================
# 컬럼명 변경
# ==================================================
df = df.rename(columns={
    "진료개시년도": "year",
    "지역": "sigungu",
    "환자수": "heat_patients"
})

# ==================================================
# 숫자형 변환
# * 값은 NaN 처리
# ==================================================
df["heat_patients"] = pd.to_numeric(
    df["heat_patients"],
    errors="coerce"
)

# ==================================================
# 서울 구별 누적 환자수
# ==================================================
district_summary = (
    df.groupby("sigungu", as_index=False)["heat_patients"]
      .sum()
      .sort_values("heat_patients", ascending=False)
)

# ==================================================
# 서울 연도별 환자수
# ==================================================
year_summary = (
    df.groupby("year", as_index=False)["heat_patients"]
      .sum()
      .sort_values("year")
)

# ==================================================
# 저장
# ==================================================
df.to_csv(
    PROCESSED_DIR / "seoul_heat_patients_clean.csv",
    index=False,
    encoding="utf-8-sig"
)

district_summary.to_csv(
    PROCESSED_DIR / "seoul_heat_patients_by_district.csv",
    index=False,
    encoding="utf-8-sig"
)

year_summary.to_csv(
    PROCESSED_DIR / "seoul_heat_patients_by_year.csv",
    index=False,
    encoding="utf-8-sig"
)

# ==================================================
# 결과 확인
# ==================================================
print("서울 자치구 수:", df["sigungu"].nunique())
print("데이터 건수:", len(df))

print("\n상위 10개 자치구")
print(district_summary.head(10))

print("\n저장 완료")
print(PROCESSED_DIR)