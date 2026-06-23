from pathlib import Path
import pandas as pd

# =================================================================
# 0. 경로 정의
# =================================================================
BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
RAW_DIR = BASE_DIR / "data" / "raw"
MASTER_DIR = BASE_DIR / "data" / "master"

MASTER_DIR.mkdir(parents=True, exist_ok=True)

print("==========================================================")
print("🚀 [일관성 확보] 선형 가중합산 방식 폭염 취약성 분석 파이프라인")
print("==========================================================")

# -----------------------------------------------------------------
# [기능] 홍수 분석과 맞추기 위한 0 ~ 1 Min-Max 정규화 함수
# -----------------------------------------------------------------
def normalize_to_01(series, invert=False):
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val: 
        return series.map(lambda x: 0.5)
    if invert:
        return (max_val - series) / (max_val - min_val)
    else:
        return (series - min_val) / (max_val - min_val)

# 1. 타 도메인 전처리 데이터셋 통합
print("[단계 1] 사회·환경·시설 전처리 데이터 로드 및 병합 중...")
df_social = pd.read_csv(PROCESSED_DIR / "social" / "seoul_social.csv")
df_env = pd.read_csv(PROCESSED_DIR / "env" / "seoul_environmental_exposure.csv")
df_cooling = pd.read_csv(PROCESSED_DIR / "cooling" / "seoul_adaptive_capacity.csv")

if "year" in df_social.columns:
    df_social = df_social[df_social["year"] == 2024]

for df in [df_social, df_env, df_cooling]:
    df["district"] = df["district"].astype(str).str.strip()

m_df = pd.merge(df_social, df_env, on="district", how="inner")
m_df = pd.merge(m_df, df_cooling, on="district", how="inner")

# =================================================================
# 2. [수정점] 홍수 분석 기조에 맞춘 선형 결합(덧셈/뺄셈) 연산
# =================================================================
print("[단계 2] 선형 표준화 지수 산출 진행 중...")

# 부문별 세부 지표 정규화 (0~1 범위)
m_df["n_고령인구"] = normalize_to_01(m_df["elderly_pop"], invert=False)
m_df["n_기초수급자"] = normalize_to_01(m_df["total_recipients"], invert=False)
# 덧셈 평균 구조로 사회적 취약성 통합
m_df["Vulnerability_Score"] = (m_df["n_고령인구"] + m_df["n_기초수급자"]) / 2

m_df["n_녹지부족"] = normalize_to_01(m_df["녹지율"], invert=True)  # 녹지는 적을수록 위험하므로 반전
m_df["n_불투수면"] = normalize_to_01(m_df["불투수면적_비율"], invert=False)
m_df["Exposure_Score"] = (m_df["n_녹지부족"] + m_df["n_불투수면"]) / 2

m_df["n_무더위쉼터"] = normalize_to_01(m_df["무더위쉼터_수"], invert=False)
m_df["n_쿨링포그"] = normalize_to_01(m_df["쿨링포그_수"], invert=False)
m_df["n_그늘막"] = normalize_to_01(m_df["그늘막_수"], invert=False)
m_df["Adaptive_Score"] = (m_df["n_무더위쉼터"] + m_df["n_쿨링포그"] + m_df["n_그늘막"]) / 3

# 하이라이트: 곱셈/나눗셈 구조를 홍수 스타일의 가중 선형 합산 구조로 변경
# 공식: [취약성(V) + 노출(E)] - 적응능력(AC)
# 시설물이 많을수록(Adaptive) 전체 취약성 지수(HVI)를 '차감'해 주는 논리입니다.
m_df["HVI_Score"] = (m_df["Vulnerability_Score"] + m_df["Exposure_Score"]) - m_df["Adaptive_Score"]

# 분석가들이 순위 보기를 편하게 하기 위해 HVI 점수 전체를 0~1로 최종 재스케일링
m_df["HVI_Score"] = normalize_to_01(m_df["HVI_Score"])
m_df["폭염_취약순위"] = m_df["HVI_Score"].rank(ascending=False, method="min").astype(int)

# =================================================================
# 3. 온열질환자 데이터 로드 및 결합 (cp949 인코딩 방어 적용)
# =================================================================
print("[단계 3] data/raw/outcome/ 경로에서 실측 환자 데이터 매핑...")
try:
    raw_patient_file = RAW_DIR / "outcome" / "heat_patients_sigungu.csv"
    try:
        df_raw_patients = pd.read_csv(raw_patient_file, encoding="cp949")
    except UnicodeDecodeError:
        df_raw_patients = pd.read_csv(raw_patient_file, encoding="euc-kr")
        
    df_raw_patients = df_raw_patients.rename(
        columns={"진료개시년도": "year", "지역": "district", "환자수": "heat_patients"}
    )
    
    df_seoul_patients = df_raw_patients[
        (df_raw_patients["district"].isin(m_df["district"].unique())) & 
        (df_raw_patients["year"] == 2024)
    ].copy()
    
    df_seoul_patients["heat_patients"] = df_seoul_patients["heat_patients"].astype(str).str.replace(",", "").str.strip()
    df_seoul_patients["heat_patients"] = pd.to_numeric(df_seoul_patients["heat_patients"], errors="coerce")
    df_seoul_patients["heat_patients"] = df_seoul_patients["heat_patients"].fillna(2).astype(int)
    
    df_outcome_clean = df_seoul_patients[["district", "heat_patients"]].copy()
    m_df = pd.merge(m_df, df_outcome_clean, on="district", how="left")
    print("-> 🔗 실측 컬럼 결합 성공!")
except Exception as e:
    print(f"-> ❌ 환자 데이터 결합 실패: {e}")

# =================================================================
# 4. 최종 마스터 CSV 파일 저장
# =================================================================
m_df = m_df.sort_values(by="폭염_취약순위")
FINAL_OUTPUT = MASTER_DIR / "seoul_heat_vulnerability_master.csv"

try:
    m_df.to_csv(FINAL_OUTPUT, index=False, encoding="utf-8-sig")
    print(f"\n✨ [성공] 홍수 분석과 일관성이 확보된 새 마스터 파일이 생성되었습니다!")
    print(f"📂 저장 위치: {FINAL_OUTPUT}\n")
    print(m_df[["district", "Vulnerability_Score", "Exposure_Score", "Adaptive_Score", "HVI_Score", "heat_patients", "폭염_취약순위"]].to_string(index=False))
except PermissionError:
    print("\n❌ 엑셀 창을 닫고 다시 실행해 주세요.")
print("==========================================================")