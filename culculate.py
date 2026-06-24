from pathlib import Path
import pandas as pd

# -----------------------------------------------------------------
# 0.1 ~ 1 범위 변환 (Min-Max Rescaling) 함수
# -----------------------------------------------------------------
def normalize_to_01_1(series, invert=False):
    """
    모든 변수를 동일한 시점에 0.1 ~ 1 범위로 정규화하는 마스터 함수
    - invert=False: 값이 클수록 위험 (고령자 비율, 불투수면 등 -> 1에 수렴)
    - invert=True : 값이 클수록 안전 (녹지율, 대피시설 -> 반전하여 부족도로 가공)
    """
    min_val = series.min()
    max_val = series.max()

    if max_val == min_val:
        return series.map(lambda x: 0.55)

    if invert:
        norm = (max_val - series) / (max_val - min_val)
    else:
        norm = (series - min_val) / (max_val - min_val)

    return (norm * 0.9) + 0.1


# --- 프로젝트 상대 경로 자동 보정 정의 ---
CURRENT_DIR = Path(__file__).resolve().parent
if CURRENT_DIR.name == "scripts":
    SDC_DIR = CURRENT_DIR.parent
elif CURRENT_DIR.name == "sdc":
    SDC_DIR = CURRENT_DIR
else:
    SDC_DIR = CURRENT_DIR / "sdc" if (CURRENT_DIR / "sdc").exists() else CURRENT_DIR

PROCESSED_DIR = SDC_DIR / "data" / "processed"
MASTER_DIR = SDC_DIR / "data" / "master"
MASTER_DIR.mkdir(parents=True, exist_ok=True)


# =================================================================
# 1. 기후 파일들로부터 서울시 공통 Hazard 상수 도출
# =================================================================
print("[프로세스 1] 기후(Climate) 데이터셋 분석 및 Hazard 상수 산출 시작...")

try:
    df_avg_temp = pd.read_csv(PROCESSED_DIR / "climate" / "avg_temp.csv")
    df_heat_index = pd.read_csv(PROCESSED_DIR / "climate" / "heat_index.csv")
    df_summer_night = pd.read_csv(PROCESSED_DIR / "climate" / "summer_night.csv")

    norm_heatwave = normalize_to_01_1(df_avg_temp["summer_heatwave_days"])[df_avg_temp["year"] == 2025].values[0]
    norm_index = normalize_to_01_1(df_heat_index["summer_avg_heat_index"])[df_heat_index["year"] == 2025].values[0]
    norm_night = normalize_to_01_1(df_summer_night["summer_tropical_nights"])[df_summer_night["year"] == 2025].values[0]

    HAZARD_CONSTANT = (norm_heatwave + norm_index + norm_night) / 3
    print(f"-> [산출 완료] 2025년 기준 서울시 공통 Hazard 강도 상수: {HAZARD_CONSTANT:.4f}")

except Exception as e:
    HAZARD_CONSTANT = 1.0
    print(f"-> [안내] 기후 파일 파싱 중 예외 발생({e}). 기본값({HAZARD_CONSTANT})으로 대체합니다.")


# =================================================================
# 2. 복지·환경·시설 데이터셋 병합 (Merge)
# =================================================================
print(f"\n[프로세스 2] 복지·환경·시설 데이터셋 병합 중... (타겟 경로: {PROCESSED_DIR})")

social_file_path = PROCESSED_DIR / "social" / "seoul_welfare_status.csv"
env_file_path = PROCESSED_DIR / "env" / "seoul_environmental_exposure.csv"
cooling_file_path = PROCESSED_DIR / "cooling" / "seoul_adaptive_capacity.csv"

if not social_file_path.exists():
    raise FileNotFoundError(f"❌ 1단계 파일이 존재하지 않습니다. 생성 위치를 확인하세요: {social_file_path}")

df_social = pd.read_csv(social_file_path)
df_env = pd.read_csv(env_file_path)
df_cooling = pd.read_csv(cooling_file_path)

if "year" in df_social.columns:
    latest_year = df_social["year"].max()
    df_social = df_social[df_social["year"] == latest_year]

df_social["district"] = df_social["district"].astype(str).str.strip()
df_env["district"] = df_env["district"].astype(str).str.strip()
df_cooling["district"] = df_cooling["district"].astype(str).str.strip()

m_df = pd.merge(df_social, df_env, on="district", how="inner")
m_df = pd.merge(m_df, df_cooling, on="district", how="inner")


# =================================================================
# 3. 0.1 ~ 1 범위 일괄 정규화 연산
# =================================================================
print("[프로세스 3] 비율(%) 및 실측 컬럼 기반 0.1~1 범위 일괄 정규화 진행 중...")

m_df["n_고령인구비율"] = normalize_to_01_1(m_df["고령인구_비율"], invert=False)
m_df["n_기초수급자비율"] = normalize_to_01_1(m_df["기초수급자_비율"], invert=False)
m_df["Vulnerability_Score"] = (m_df["n_고령인구비율"] + m_df["n_기초수급자비율"]) / 2

m_df["n_녹지부족"] = normalize_to_01_1(m_df["녹지율"], invert=True)
m_df["n_불투수면"] = normalize_to_01_1(m_df["불투수면적_비율"], invert=False)
m_df["Exposure_Score"] = (m_df["n_녹지부족"] + m_df["n_불투수면"]) / 2

m_df["n_무더위쉼터"] = normalize_to_01_1(m_df["무더위쉼터_수"], invert=False)
m_df["n_쿨링포그"] = normalize_to_01_1(m_df["쿨링포그_수"], invert=False)
m_df["n_그늘막"] = normalize_to_01_1(m_df["그늘막_수"], invert=False)
m_df["Adaptive_Score"] = (m_df["n_무더위쉼터"] + m_df["n_쿨링포그"] + m_df["n_그늘막"]) / 3


# =================================================================
# 4. 선형 합산(V + E - AC) 구조 적용 및 리스크 산출
# =================================================================
print("[프로세스 4] 홍수식 선형 합산(V + E - AC) 구조 적용 및 리스크 산출...")

m_df["HVI_Score"] = m_df["Vulnerability_Score"] + m_df["Exposure_Score"] - m_df["Adaptive_Score"]
m_df["Heat_Risk_Score"] = HAZARD_CONSTANT * m_df["HVI_Score"]

m_df["폭염_취약순위"] = m_df["HVI_Score"].rank(ascending=False, method="min").astype(int)
m_df = m_df.sort_values(by="폭염_취약순위").reset_index(drop=True)


# =================================================================
# 5. [최종 보완] 중구 기호(*) 및 결측치 완벽 차단 레이어
# =================================================================
print("\n[프로세스 5] 실측 온열질환자 데이터(seoul_outcome.csv) 안전 정제 및 결합 시작...")

outcome_file_path = PROCESSED_DIR / "outcome" / "seoul_outcome.csv"

if not outcome_file_path.exists():
    print(f"⚠️ [경고] 실측 파일이 해당 경로에 존재하지 않습니다: {outcome_file_path}")
    m_df["heat_patients"] = 0
else:
    try:
        df_outcome = pd.read_csv(outcome_file_path)
        df_outcome["district"] = df_outcome["district"].astype(str).str.strip()
        
        if "heat_patients" in df_outcome.columns:
            # 1단계: 문자열로 강제 변환 후 앞뒤 공백 및 쉼표 정제
            df_outcome["heat_patients"] = df_outcome["heat_patients"].astype(str).str.replace(",", "").str.strip()
            
            # 2단계: 중구의 '*'나 미기재 항목을 파이썬이 인식 가능한 NaN으로 강제 변환
            df_outcome["heat_patients"] = pd.to_numeric(df_outcome["heat_patients"], errors="coerce")
            
            # 3단계: [중요] 변환된 NaN(결측치)을 타입 변환 전에 '먼저' 0명으로 확실하게 채우기
            df_outcome["heat_patients"] = df_outcome["heat_patients"].fillna(0).astype(int)
        else:
            raise KeyError("seoul_outcome.csv 파일 내에 'heat_patients' 컬럼이 존재하지 않습니다.")

        # 정제가 끝난 깨끗한 데이터셋(int형)을 마스터 프레임과 병합
        m_df = pd.merge(m_df, df_outcome, on="district", how="left")
        
        # 만약 마스터 프레임에만 존재하고 실측 파일엔 없는 구가 있다면 최종 방어 처리
        m_df["heat_patients"] = m_df["heat_patients"].fillna(0).astype(int)
        
        print("✅ [성공] 중구의 별표(*)를 포함한 모든 결측치가 안전하게 0명으로 정제되어 병합되었습니다!")
        print(f"-> 전체 자치구 온열질환자 수 검증:\n{m_df[['district', 'heat_patients']].to_string(index=False)}")
        
    except Exception as e:
        print(f"❌ [에러 발생] 데이터 정제 및 파싱 중 오류 발생: {e}")
        m_df["heat_patients"] = 0

OUTPUT_PATH = MASTER_DIR / "F_seoul_heat_vulnerability_master.csv"
m_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
print(f"[2단계 마스터 통합 완료] -> 저장경로: {OUTPUT_PATH}")


# =================================================================
# 6. [3단계 복구 완료] 취약성 1위 자치구 동적 4대 도메인 쪼개기 분리
# =================================================================
print("\n==========================================================")
print("[3단계: 취약성 1위 자치구 동적 판별 및 4대 도메인 쪼개기 가동]")
print("==========================================================")

# 가감산 연산 결과 정렬된 최상단(0번 인덱스) 자치구 자동 로드
top_1_district = m_df.iloc[0]["district"]
top_1_score = m_df.iloc[0]["HVI_Score"]
print(f"🎯 동적 판정 결과 폭염 취약성 1위 자치구: [{top_1_district}] (지수: {top_1_score:.4f})\n")

# 1위 자치구 데이터만 타겟팅 필터링
df_target = m_df[m_df["district"] == top_1_district].copy()

# -----------------------------------------------------------------
# 1. 사회적 취약성 데이터 (원시 비율 변수 및 최종 스코어 포함)
# -----------------------------------------------------------------
social_cols = [
    "district", "year", "total_pop_2024", "elderly_pop", "total_recipients", 
    "elderly_recipients", "고령인구_비율", "기초수급자_비율", "elderly_recipient_ratio", "Vulnerability_Score"
]
df_social_out = df_target[social_cols].copy()
social_file = MASTER_DIR / f"{top_1_district}_social_vulnerability.csv"
df_social_out.to_csv(social_file, index=False, encoding="utf-8-sig")
print(f"파일 1 생성 완료 (사회적 취약성): {social_file.name}")

# -----------------------------------------------------------------
# 2. 환경 노출 데이터 (녹지율, 불투수면적 비율 및 스코어)
# -----------------------------------------------------------------
env_cols = ["district", "year", "녹지율", "불투수면적_비율", "Exposure_Score"]
df_env_out = df_target[env_cols].copy()
env_file = MASTER_DIR / f"{top_1_district}_env_exposure.csv"
df_env_out.to_csv(env_file, index=False, encoding="utf-8-sig")
print(f"파일 2 생성 완료 (환경 노출): {env_file.name}")

# -----------------------------------------------------------------
# 3. 위험 감소 요소 데이터 (무더위쉼터, 쿨링포그, 그늘막 개수 및 스코어)
# -----------------------------------------------------------------
adaptive_cols = ["district", "year", "무더위쉼터_수", "쿨링포그_수", "그늘막_수", "Adaptive_Score"]
df_adaptive_out = df_target[adaptive_cols].copy()
adaptive_file = MASTER_DIR / f"{top_1_district}_adaptive_capacity.csv"
df_adaptive_out.to_csv(adaptive_file, index=False, encoding="utf-8-sig")
print(f"파일 3 생성 완료 (위험 감소 요소): {adaptive_file.name}")

# -----------------------------------------------------------------
# 4. 실측 피해 데이터 (온열질환자 수 및 최종 취약 순위 결과)
# -----------------------------------------------------------------
outcome_cols = ["district", "year", "heat_patients", "HVI_Score", "Heat_Risk_Score", "폭염_취약순위"]
df_outcome_out = df_target[outcome_cols].copy()
outcome_file = MASTER_DIR / f"{top_1_district}_heat_patients_outcome.csv"
df_outcome_out.to_csv(outcome_file, index=False, encoding="utf-8-sig")
print(f"파일 4 생성 완료 (실측 온열질환자): {outcome_file.name}")

print("==========================================================")
print(f"모든 파이프라인이 연동되어 [{top_1_district}] 데이터의 4대 파일 분리가 완료되었습니다.")
print("==========================================================")