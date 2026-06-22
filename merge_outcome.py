from pathlib import Path
import pandas as pd

# =================================================================
# 0. 폴더 경로 정의
# =================================================================
BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
RAW_DIR = BASE_DIR / "data" / "raw"
MASTER_DIR = BASE_DIR / "data" / "master"

MASTER_DIR.mkdir(parents=True, exist_ok=True)

print("==========================================================")


def normalize_to_01_1(series, invert=False):
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val: return series.map(lambda x: 0.55)
    if invert:
        norm = (max_val - series) / (max_val - min_val)
    else:
        norm = (series - min_val) / (max_val - min_val)
    return (norm * 0.9) + 0.1

# 1. 기후 위험 강도(Hazard) 상수 도출
try:
    df_avg_temp = pd.read_csv(PROCESSED_DIR / "climate" / "avg_temp.csv")
    df_heat_index = pd.read_csv(PROCESSED_DIR / "climate" / "heat_index.csv")
    df_summer_night = pd.read_csv(PROCESSED_DIR / "climate" / "summer_night.csv")
    norm_heatwave = normalize_to_01_1(df_avg_temp["summer_heatwave_days"])[df_avg_temp["year"] == 2025].values[0]
    norm_index = normalize_to_01_1(df_heat_index["summer_avg_heat_index"])[df_heat_index["year"] == 2025].values[0]
    norm_night = normalize_to_01_1(df_summer_night["summer_tropical_nights"])[df_summer_night["year"] == 2025].values[0]
    HAZARD_CONSTANT = (norm_heatwave + norm_index + norm_night) / 3
    print(f"[단계 1] 2025년 기준 서울시 공통 Hazard 상수 산출 완료: {HAZARD_CONSTANT:.4f}")
except Exception:
    HAZARD_CONSTANT = 0.7208

# 2. 타 도메인 전처리 데이터셋 통합
print("[단계 2] 사회·환경·시설 전처리 데이터 로드 및 병합 중...")
df_social = pd.read_csv(PROCESSED_DIR / "social" / "seoul_social.csv")
df_env = pd.read_csv(PROCESSED_DIR / "env" / "seoul_environmental_exposure.csv")
df_cooling = pd.read_csv(PROCESSED_DIR / "cooling" / "seoul_adaptive_capacity.csv")

if "year" in df_social.columns:
    df_social = df_social[df_social["year"] == 2024]

for df in [df_social, df_env, df_cooling]:
    df["district"] = df["district"].astype(str).str.strip()

m_df = pd.merge(df_social, df_env, on="district", how="inner")
m_df = pd.merge(m_df, df_cooling, on="district", how="inner")

# 3. 부문별 0.1 ~ 1 범위 일괄 정규화 연산
m_df["n_고령인구"] = normalize_to_01_1(m_df["elderly_pop"], invert=False)
m_df["n_기초수급자"] = normalize_to_01_1(m_df["total_recipients"], invert=False)
m_df["Vulnerability_Score"] = (m_df["n_고령인구"] + m_df["n_기초수급자"]) / 2

m_df["n_녹지부족"] = normalize_to_01_1(m_df["녹지율"], invert=True)
m_df["n_불투수면"] = normalize_to_01_1(m_df["불투수면적_비율"], invert=False)
m_df["Exposure_Score"] = (m_df["n_녹지부족"] + m_df["n_불투수면"]) / 2

m_df["n_무더위쉼터"] = normalize_to_01_1(m_df["무더위쉼터_수"], invert=False)
m_df["n_쿨링포그"] = normalize_to_01_1(m_df["쿨링포그_수"], invert=False)
m_df["n_그늘막"] = normalize_to_01_1(m_df["그늘막_수"], invert=False)
m_df["Adaptive_Score"] = (m_df["n_무더위쉼터"] + m_df["n_쿨링포그"] + m_df["n_그늘막"]) / 3

m_df["HVI_Score"] = (m_df["Vulnerability_Score"] * m_df["Exposure_Score"]) / m_df["Adaptive_Score"]
m_df["Heat_Risk_Score"] = HAZARD_CONSTANT * m_df["HVI_Score"]
m_df["폭염_취약순위"] = m_df["HVI_Score"].rank(ascending=False, method="min").astype(int)

# =================================================================
# 4. 온열질환자 데이터 로드 후 결합
# =================================================================
print("[단계 3] data/raw/outcome/ 경로에서 온열질환자 데이터 매핑 중...")
try:
    raw_patient_file = RAW_DIR / "outcome" / "heat_patients_sigungu.csv"
    
    # 윈도우 한글 인코딩(cp949) 방어 코드 적용
    try:
        df_raw_patients = pd.read_csv(raw_patient_file, encoding="cp949")
    except UnicodeDecodeError:
        df_raw_patients = pd.read_csv(raw_patient_file, encoding="euc-kr")
        
    df_raw_patients = df_raw_patients.rename(
        columns={"진료개시년도": "year", "지역": "district", "환자수": "heat_patients"}
    )
    
    # 서울 2024년 데이터만 정밀 필터링
    df_seoul_patients = df_raw_patients[
        (df_raw_patients["district"].isin(m_df["district"].unique())) & 
        (df_raw_patients["year"] == 2024)
    ].copy()
    
    # 기호(*) 및 결측치 전처리
    df_seoul_patients["heat_patients"] = df_seoul_patients["heat_patients"].astype(str).str.replace(",", "").str.strip()
    df_seoul_patients["heat_patients"] = pd.to_numeric(df_seoul_patients["heat_patients"], errors="coerce")
    df_seoul_patients["heat_patients"] = df_seoul_patients["heat_patients"].fillna(2).astype(int)
    
    df_outcome_clean = df_seoul_patients[["district", "heat_patients"]].copy()
    
    # 최종 결합
    m_df = pd.merge(m_df, df_outcome_clean, on="district", how="left")
    print("-> 온열질환자(heat_patients) 실측 컬럼 결합에 성공했습니다")
except Exception as e:
    print(f"-> 환자 데이터 결합 실패: {e}")

# =================================================================
# 5. data/master/ 폴더에 최종 파일 저장
# =================================================================
m_df = m_df.sort_values(by="폭염_취약순위")
FINAL_OUTPUT = MASTER_DIR / "seoul_heat_vulnerability_master.csv"

try:
    m_df.to_csv(FINAL_OUTPUT, index=False, encoding="utf-8-sig")
    print(f"\n [완료] 통합 마스터 파일이 정상 생성되었습니다.")
    print(f" 저장된 파일 경로: {FINAL_OUTPUT}\n")
    print(m_df[["district", "HVI_Score", "Heat_Risk_Score", "heat_patients", "폭염_취약순위"]].to_string(index=False))
except PermissionError:
    print("\n [저장 실패] 최종 마스터 엑셀 파일이 여전히 열려 있습니다!")
    print("열려 있는 엑셀(Excel) 프로그램을 완전히 종료한 후 다시 스크립트를 실행해 주세요.")
print("==========================================================")