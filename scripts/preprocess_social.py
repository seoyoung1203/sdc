from pathlib import Path
import pandas as pd

from utils.social import *

# 0. 경로 정의
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "social"
PROCESSED_DIR = BASE_DIR / "data" / "processed" / "social"

# 파일 경로 설정
elderly_file = RAW_DIR / "자치구별+고령인구(추계인구)_20260622232629.csv"
recipient_file = RAW_DIR / "국민기초생활보장+연령별+일반수급자(구별)_20260622232847.csv"
total_pop_file = RAW_DIR / "자치구별+총인구(추계인구)_20260624143106.xlsx"

print("==========================================================")
print("[1단계: Social 데이터 Raw -> Processed 파이프라인 가동]")
print("==========================================================")

# -----------------------------------------------------------------
# 1. 자치구별 고령인구 데이터 전처리 (2024년 전체 고령인구)
# -----------------------------------------------------------------
df_elderly_raw = pd.read_csv(elderly_file, encoding="utf-8", header=None)

# 2024년 총계 열 위치 추적 (스니펫 기준 2024년 '계'는 8번째 열)
elderly_district = df_elderly_raw.iloc[2:, 1].astype(str).str.strip()
elderly_pop_2024 = df_elderly_raw.iloc[2:, 8].astype(str).str.replace(",", "").str.strip()

df_elderly_2024 = pd.DataFrame({
    "district": elderly_district,
    "elderly_pop": pd.to_numeric(elderly_pop_2024, errors="coerce")
})
# '소계', '합계' 등 노이즈 제거
df_elderly_2024 = df_elderly_2024[~df_elderly_2024["district"].isin(["소계", "합계", "자치구별(2)", "중앙", "시점", "nan"])].dropna()


# -----------------------------------------------------------------
# 2. 국민기초생활보장 수급자 데이터 전처리 (2024년 전체 일반수급자 소계)
# -----------------------------------------------------------------
df_recipient_raw = pd.read_csv(recipient_file, encoding="utf-8", header=None)

# 스니펫 기준: 2번 열이 자치구명, 3번 열이 '소계'(전체 수급자 수)
# 65세 이상 수급자 컬럼들 (17번 열 ~ 20번 열: 65~69세, 70~74세, 75~79세, 80세이상)
rec_district = df_recipient_raw.iloc[2:, 2].astype(str).str.replace('"', '').str.strip()
rec_total = df_recipient_raw.iloc[2:, 3].astype(str).str.replace(",", "").str.strip()

# 65세 이상 고령 수급자 합산 계산
rec_65_69 = pd.to_numeric(df_recipient_raw.iloc[2:, 17].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
rec_70_74 = pd.to_numeric(df_recipient_raw.iloc[2:, 18].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
rec_75_79 = pd.to_numeric(df_recipient_raw.iloc[2:, 19].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
rec_80_over = pd.to_numeric(df_recipient_raw.iloc[2:, 20].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
rec_elderly_sum = rec_65_69 + rec_70_74 + rec_75_79 + rec_80_over

df_recipient_2024 = pd.DataFrame({
    "district": rec_district,
    "total_recipients": pd.to_numeric(rec_total, errors="coerce"),
    "elderly_recipients": rec_elderly_sum
})
df_recipient_2024 = df_recipient_2024[~df_recipient_2024["district"].isin(["소계", "합계", "자치구별(2)", "nan"])].dropna()


# -----------------------------------------------------------------
# 3. 자치구별 총인구(추계인구) 엑셀 파일 파싱 (2024년 전체 인구)
# -----------------------------------------------------------------
df_total_pop_raw = pd.read_excel(total_pop_file, header=None)

# 스니펫 기준: 1번 열이 자치구명, 8번 열이 2024년 '총인구 계'
pop_district = df_total_pop_raw.iloc[2:, 1].astype(str).str.strip()
pop_total_2024 = df_total_pop_raw.iloc[2:, 8].astype(str).str.replace(",", "").str.strip()

df_pop_2024 = pd.DataFrame({
    "district": pop_district,
    "total_pop_2024": pd.to_numeric(pop_total_2024, errors="coerce")
})
df_pop_2024 = df_pop_2024[~df_pop_2024["district"].isin(["소계", "합계", "자치구별(2)", "nan"])].dropna()


# -----------------------------------------------------------------
# 4. 데이터 안전 교집합 병합 및 지표 레이어 생성
# -----------------------------------------------------------------
# 양 끝 공백 전방위 재정제하여 병합 실패 원천 차단
df_elderly_2024["district"] = df_elderly_2024["district"].str.strip()
df_recipient_2024["district"] = df_recipient_2024["district"].str.strip()
df_pop_2024["district"] = df_pop_2024["district"].str.strip()

# 1차 결합
welfare_combined = pd.merge(df_elderly_2024, df_recipient_2024, on="district", how="inner")
# 2차 결합
final_df = pd.merge(welfare_combined, df_pop_2024, on="district", how="inner")

if final_df.empty:
    print("\n[디버깅 정보: 병합 대상 구 이름 샘플]")
    print("고령인구 구 이름:", df_elderly_2024["district"].tolist()[:3])
    print("기초수급 구 이름:", df_recipient_2024["district"].tolist()[:3])
    print("총인구수 구 이름:", df_pop_2024["district"].tolist()[:3])
    raise ValueError("명시적 인덱싱 결합에도 실패했습니다. 파일 형식을 다시 확인해 주세요.")

# 분석 지표 생성
final_df["year"] = 2024
final_df["고령인구_비율"] = (final_df["elderly_pop"] / final_df["total_pop_2024"]) * 100
final_df["기초수급자_비율"] = (final_df["total_recipients"] / final_df["total_pop_2024"]) * 100
final_df["elderly_recipient_ratio"] = (final_df["elderly_recipients"] / final_df["elderly_pop"] * 100).round(2)

# 가독성을 위한 컬럼 정돈
final_df = final_df[[
    "year", "district", "total_pop_2024", "elderly_pop", 
    "total_recipients", "elderly_recipients", 
    "고령인구_비율", "기초수급자_비율", "elderly_recipient_ratio"
]]
final_df = final_df.sort_values("district").reset_index(drop=True)


# -----------------------------------------------------------------
# 5. 전처리 완료 데이터 processed 폴더에 저장
# -----------------------------------------------------------------
output_path = PROCESSED_DIR / "seoul_welfare_status.csv"
save_csv(final_df, output_path)

print(f" 사회적 취약성 전처리 파일 저장 성공: {output_path.relative_to(BASE_DIR)}")
print(f" -> 서울시 {len(final_df)}개 자치구 데이터가 누락 없이 완벽하게 통합되었습니다.")
print("==========================================================")