from pathlib import Path
import pandas as pd


# -----------------------------------------------------------------
# 0.1 ~ 1 범위 변환 (Min-Max Rescaling) 함수
# -----------------------------------------------------------------
def normalize_to_01_1(series, invert=False):
    """
    모든 변수를 동일한 시점에 0.1 ~ 1 범위로 정규화하는 마스터 함수
    - invert=False: 값이 클수록 위험 (고령자, 불투수면 등 -> 1에 수렴)
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


# --- 경로 ---
BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# =================================================================
# 1. 기후 파일들로부터 서울시 공통 Hazard 상수 도출
# =================================================================
print("[프로세스 1] 기후(Climate) 데이터셋 분석 및 Hazard 상수 산출 시작...")

try:
    df_avg_temp = pd.read_csv(PROCESSED_DIR / "climate" / "avg_temp.csv")
    df_heat_index = pd.read_csv(PROCESSED_DIR / "climate" / "heat_index.csv")
    df_summer_night = pd.read_csv(PROCESSED_DIR / "climate" / "summer_night.csv")

    # 역대 시계열(2023~2025) 중 가장 최신이자 위험도가 높았던 2025년을 기준으로 0.1~1 범위 환산
    norm_heatwave = normalize_to_01_1(df_avg_temp["summer_heatwave_days"])[df_avg_temp["year"] == 2025].values[0]
    norm_index = normalize_to_01_1(df_heat_index["summer_avg_heat_index"])[df_heat_index["year"] == 2025].values[0]
    norm_night = normalize_to_01_1(df_summer_night["summer_tropical_nights"])[df_summer_night["year"] == 2025].values[0]

    # 세 기후 지표의 평균값을 서울시 공통 Hazard 값으로 최종 확정
    HAZARD_CONSTANT = (norm_heatwave + norm_index + norm_night) / 3
    print(f"-> [산출 완료] 2025년 기준 서울시 공통 Hazard 강도 상수: {HAZARD_CONSTANT:.4f}")

except Exception as e:
    HAZARD_CONSTANT = 1.0
    print(f"-> [안내] 기후 파일 파싱 중 예외 발생({e}). 기본값({HAZARD_CONSTANT})으로 대체합니다.")


# =================================================================
# 2. Merge
# =================================================================
print("\n[프로세스 2] 사회·환경·시설 데이터셋 병합 중...")

df_social = pd.read_csv(PROCESSED_DIR / "social" / "seoul_social.csv")
df_env = pd.read_csv(PROCESSED_DIR / "env" / "seoul_environmental_exposure.csv")
df_cooling = pd.read_csv(PROCESSED_DIR / "cooling" / "seoul_adaptive_capacity.csv")

# 사회적 취약성 데이터가 연도별(year)로 적재되어 있다면, 가장 최신 연도 데이터만 필터링합니다.
if "year" in df_social.columns:
    latest_year = df_social["year"].max()
    df_social = df_social[df_social["year"] == latest_year]
    print(f"-> 사회 취약성 데이터는 가장 최신 연도인 {latest_year}년 데이터로 분석을 진행합니다.")

# 자치구명 공백 제거로 매칭 무결성 확보
df_social["district"] = df_social["district"].astype(str).str.strip()
df_env["district"] = df_env["district"].astype(str).str.strip()
df_cooling["district"] = df_cooling["district"].astype(str).str.strip()

# 마스터 데이터프레임 최종 병합 (Inner Join)
m_df = pd.merge(df_social, df_env, on="district", how="inner")
m_df = pd.merge(m_df, df_cooling, on="district", how="inner")


# =================================================================
# 3. 공유해주신 컬럼명 기반 0.1 ~ 1 범위 일괄 정규화 연산
# =================================================================
print("[프로세스 3] 실측 컬럼 기반 0.1~1 범위 일괄 정규화 진행 중...")

# [부문 A] 사회적 취약성 (Vulnerability) -> 많을수록 온열질환에 위험 (일반 정규화)
m_df["n_고령인구"] = normalize_to_01_1(m_df["elderly_pop"], invert=False)
m_df["n_기초수급자"] = normalize_to_01_1(m_df["total_recipients"], invert=False)
m_df["Vulnerability_Score"] = (m_df["n_고령인구"] + m_df["n_기초수급자"]) / 2

# [부문 B] 환경 노출 (Environmental Exposure) -> 녹지는 역정규화, 불투수면은 일반 정규화
m_df["n_녹지부족"] = normalize_to_01_1(m_df["녹지율"], invert=True)  # 많을수록 안전하므로 역전(부족도)
m_df["n_불투수면"] = normalize_to_01_1(m_df["불투수면적_비율"], invert=False) # 많을수록 위험
m_df["Exposure_Score"] = (m_df["n_녹지부족"] + m_df["n_불투수면"]) / 2

# [부문 C] 적응 능력 (Adaptive Capacity) -> 시설은 많을수록 안전 (일반 정규화 후 분모로 배치)
m_df["n_무더위쉼터"] = normalize_to_01_1(m_df["무더위쉼터_수"], invert=False)
m_df["n_쿨링포그"] = normalize_to_01_1(m_df["쿨링포그_수"], invert=False)
m_df["n_그늘막"] = normalize_to_01_1(m_df["그늘막_수"], invert=False)
m_df["Adaptive_Score"] = (m_df["n_무더위쉼터"] + m_df["n_쿨링포그"] + m_df["n_그늘막"]) / 3


# =================================================================
# 4. 최종 취약성 지수(HVI) 및 서울 전체 Heat Risk 연산
# =================================================================
print("[프로세스 4] 폭염 취약성 지수(HVI) 및 최종 리스크 산출 스코어 연산...")

# 공식: HVI = (Vulnerability * Exposure) / Adaptive
m_df["HVI_Score"] = (m_df["Vulnerability_Score"] * m_df["Exposure_Score"]) / m_df["Adaptive_Score"]

# 최종 Heat Risk 연산 (Hazard 공통 상수 곱산)
m_df["Heat_Risk_Score"] = HAZARD_CONSTANT * m_df["HVI_Score"]

# 취약 순위 부여 (지수가 높을수록 폭염에 취약하고 위험한 자치구)
m_df["폭염_취약순위"] = m_df["HVI_Score"].rank(ascending=False, method="min").astype(int)
m_df = m_df.sort_values(by="폭염_취약순위")


# =================================================================
# 5. GIS 매핑 연동용 최종 CSV 저장
# =================================================================
try:
    df_outcome = pd.read_csv(PROCESSED_DIR / "outcome" / "seoul_outcome.csv")
    df_outcome["district"] = df_outcome["district"].astype(str).str.strip()
    m_df = pd.merge(m_df, df_outcome, on="district", how="left")
except Exception:
    pass

OUTPUT_PATH = PROCESSED_DIR / "seoul_heat_vulnerability_master.csv"
m_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

print(f"\n[성공] : {OUTPUT_PATH}")
print("-" * 80)
print(m_df[["district", "Vulnerability_Score", "Exposure_Score", "Adaptive_Score", "HVI_Score", "Heat_Risk_Score", "폭염_취약순위"]].to_string(index=False))
print("-" * 80)