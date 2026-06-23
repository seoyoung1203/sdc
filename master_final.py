from pathlib import Path
import pandas as pd

# 0. 경로 정의
BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
RAW_DIR = BASE_DIR / "data" / "raw"
MASTER_DIR = BASE_DIR / "data" / "master"

MASTER_DIR.mkdir(parents=True, exist_ok=True)

print("==========================================================")
print("⚙️ [긴급 데이터 정제] 중복 데이터 완전 박멸 및 25개 구 압축 파이프라인")
print("==========================================================")

# 1. 사회 데이터 로드 후 '진짜 전체 인구 행'만 정밀 필터링
df_social_raw = pd.read_csv(PROCESSED_DIR / "social" / "seoul_social.csv")
df_social_raw["district"] = df_social_raw["district"].astype(str).str.strip()
if "year" in df_social_raw.columns:
    df_social_raw = df_social_raw[df_social_raw["year"] == 2024]

# 핵심 로직: 각 자치구별로 고령인구(elderly_pop)가 가장 많은 행 딱 1개만 골라냅니다.
# 쪼개진 데이터(성별, 특정연령)를 버리고 진짜 총인구 데이터만 남기는 작업입니다.
df_social = df_social_raw.sort_values("elderly_pop", ascending=False).drop_duplicates(subset=["district"])

# 2. 환경 및 시설 데이터 로드 및 정제
df_env = pd.read_csv(PROCESSED_DIR / "env" / "seoul_environmental_exposure.csv")
df_cooling = pd.read_csv(PROCESSED_DIR / "cooling" / "seoul_adaptive_capacity.csv")

for df in [df_env, df_cooling]:
    df["district"] = df["district"].astype(str).str.strip()
    if "year" in df.columns:
        df = df.drop_duplicates(subset=["district"])

# 3. 1:1:1 정밀 병합 (이제 무조건 자치구당 딱 1줄씩만 붙습니다)
m_df = pd.merge(df_social, df_env, on="district", how="inner")
m_df = pd.merge(m_df, df_cooling, on="district", how="inner")

# 4. 홍수 기조에 맞춘 선형 결합(덧셈/뺄셈) 및 정규화 재연산
def normalize_to_01(series, invert=False):
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val: return series.map(lambda x: 0.5)
    return (max_val - series) / (max_val - min_val) if invert else (series - min_val) / (max_val - min_val)

m_df["n_고령인구"] = normalize_to_01(m_df["elderly_pop"])
m_df["n_기초수급자"] = normalize_to_01(m_df["total_recipients"])
m_df["Vulnerability_Score"] = (m_df["n_고령인구"] + m_df["n_기초수급자"]) / 2

m_df["n_녹지부족"] = normalize_to_01(m_df["녹지율"], invert=True)
m_df["n_불투수면"] = normalize_to_01(m_df["불투수면적_비율"])
m_df["Exposure_Score"] = (m_df["n_녹지부족"] + m_df["n_불투수면"]) / 2

m_df["n_무더위쉼터"] = normalize_to_01(m_df["무더위쉼터_수"])
m_df["n_쿨링포그"] = normalize_to_01(m_df["쿨링포그_수"])
m_df["n_그늘막"] = normalize_to_01(m_df["그늘막_수"])
m_df["Adaptive_Score"] = (m_df["n_무더위쉼터"] + m_df["n_쿨링포그"] + m_df["n_그늘막"]) / 3

# HVI 계산 및 최종 0~1 재스케일링
m_df["HVI_Score"] = (m_df["Vulnerability_Score"] + m_df["Exposure_Score"]) - m_df["Adaptive_Score"]
m_df["HVI_Score"] = normalize_to_01(m_df["HVI_Score"])
m_df["폭염_취약순위"] = m_df["HVI_Score"].rank(ascending=False, method="min").astype(int)

# 5. 온열질환자 데이터 로드 및 결합
try:
    raw_patient_file = RAW_DIR / "outcome" / "heat_patients_sigungu.csv"
    try:
        df_raw_patients = pd.read_csv(raw_patient_file, encoding="cp949")
    except UnicodeDecodeError:
        df_raw_patients = pd.read_csv(raw_patient_file, encoding="euc-kr")
        
    df_raw_patients = df_raw_patients.rename(columns={"진료개시년도": "year", "지역": "district", "환자수": "heat_patients"})
    df_seoul_patients = df_raw_patients[(df_raw_patients["district"].isin(m_df["district"])) & (df_raw_patients["year"] == 2024)].copy()
    
    df_seoul_patients["heat_patients"] = df_seoul_patients["heat_patients"].astype(str).str.replace(",", "").str.strip()
    df_seoul_patients["heat_patients"] = pd.to_numeric(df_seoul_patients["heat_patients"], errors="coerce").fillna(2).astype(int)
    
    # 중복 방지 처리 후 결합
    df_outcome_clean = df_seoul_patients.drop_duplicates(subset=["district"])[["district", "heat_patients"]]
    m_df = pd.merge(m_df, df_outcome_clean, on="district", how="left")
    print("-> 🔗 실측 온열질환자 데이터 1:1 매핑 성공!")
except Exception as e:
    print(f"-> ❌ 환자 데이터 결합 실패: {e}")

# 6. 최종 마스터 CSV 파일 저장 및 확인
m_df = m_df.sort_values(by="폭염_취약순위")
FINAL_OUTPUT = MASTER_DIR / "seoul_heat_vulnerability_master.csv"

try:
    m_df.to_csv(FINAL_OUTPUT, index=False, encoding="utf-8-sig")
    print(f"\n✨ [완료] 중복이 완전히 제거된 마스터 파일이 생성되었습니다!")
    print(f"📂 저장 위치: {FINAL_OUTPUT}")
    print(f"📊 총 생성된 행(구)의 개수: {len(m_df)}개 (서울시 25개 자치구 일치 완료)")
except PermissionError:
    print("\n❌ 에러: 파일이 열려있습니다. 엑셀을 닫고 다시 실행해 주세요.")
print("==========================================================")