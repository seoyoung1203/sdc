from pathlib import Path
import pandas as pd

from utils.social import *

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "social"
PROCESSED_DIR = BASE_DIR / "data" / "processed" / "social"

elderly_file = RAW_DIR / "자치구별+고령인구(추계인구)_20260622232629.csv"
recipient_file = (
    RAW_DIR / "국민기초생활보장+연령별+일반수급자(구별)_20260622232847.csv"
)

# -----------------------------------------------------------------
# 1. 자치구별 고령인구 데이터 전처리
# -----------------------------------------------------------------

df_elderly_raw = pd.read_csv(elderly_file, encoding="utf-8", header=None)

# 0번째 행(연도), 1번째 행(구분), 2번째 열(자치구)을 바탕으로 새 컬럼명 생성
years = df_elderly_raw.iloc[0].ffill()
types = df_elderly_raw.iloc[1]

new_cols = []
for y, t in zip(years, types):
    if pd.isna(y) or "자치구" in str(y):
        new_cols.append(t)
    else:
        new_cols.append(f"{int(float(y))}_{t}")

df_elderly_raw.columns = new_cols
df_elderly_raw = df_elderly_raw.iloc[2:].reset_index(drop=True)
df_elderly_raw = df_elderly_raw.rename(columns={"자치구별(2)": "district"})

# 필요한 '계' 컬럼(총 고령인구)만 필터링하여 남기기
keep_cols = ["district"] + [c for c in df_elderly_raw.columns if "_계" in c]
df_elderly = df_elderly_raw[keep_cols]
df_elderly = clean_district_data(df_elderly_raw, "district")

# 가로 데이터를 세로로 변환
elderly_melted = df_elderly.melt(
    id_vars=["district"], var_name="year", value_name="elderly_pop"
)
elderly_melted["year"] = pd.to_numeric(
    elderly_melted["year"].str.extract(r"(\d+)")[0]
)
elderly_melted["elderly_pop"] = pd.to_numeric(
    elderly_melted["elderly_pop"].astype(str).str.replace(",", ""),
    errors="coerce",
)


# -----------------------------------------------------------------
# 2. 국민기초생활보장 수급자 데이터 전처리 
# -----------------------------------------------------------------

df_recipient_raw = pd.read_csv(recipient_file, encoding="utf-8", header=1)

# 첫 두 컬럼 이름 수정 (시점 -> year, 자치구별(2) -> district)
df_recipient_raw.columns.values[0] = "year"
df_recipient_raw.columns.values[2] = "district"

# '소계' 컬럼 이름을 'total_recipients'로 명확하게 변경
df_recipient_raw = df_recipient_raw.rename(columns={"소계": "total_recipients"})

df_recipient = clean_district_data(df_recipient_raw, "district")

# 데이터 타입 변환 및 콤마 제거
age_cols = ["65~69세", "70~74세", "75~79세", "80세이상"]
target_cols = ["total_recipients"] + age_cols

for col in target_cols:
    df_recipient[col] = (
        df_recipient[col].astype(str).str.replace(",", "").str.strip()
    )
    df_recipient[col] = pd.to_numeric(df_recipient[col], errors="coerce")

# 65세 이상 수급자 합산
df_recipient["elderly_recipients"] = df_recipient[age_cols].sum(axis=1)
df_recipient["year"] = pd.to_numeric(df_recipient["year"], errors="coerce")

recipient_cleaned = df_recipient[
    ["year", "district", "total_recipients", "elderly_recipients"]
].copy()


# -----------------------------------------------------------------
# 3. 데이터 병합 및 추가 지표 생성
# -----------------------------------------------------------------
final_df = pd.merge(
    elderly_melted, recipient_cleaned, on=["year", "district"], how="inner"
)

# 고령자 대비 고령 수급자 비율(%) 계산
final_df["elderly_recipient_ratio"] = (
    final_df["elderly_recipients"] / final_df["elderly_pop"] * 100
).round(2)

final_df = final_df.sort_values("elderly_pop", ascending=False).drop_duplicates(subset=["district", "year"])

# 결과 저장
save_csv(final_df, PROCESSED_DIR / "seoul_welfare_status.csv")

print("--- 전처리 완료 결과 확인 ---")
print(final_df.head())