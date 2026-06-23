from pathlib import Path
import pandas as pd

# 0. 경로 설정
BASE_DIR = Path(__file__).resolve().parent
MASTER_DIR = BASE_DIR / "data" / "master"
MASTER_FILE = MASTER_DIR / "seoul_heat_vulnerability_master.csv"

print("==========================================================")
print("[양천구 도메인별 데이터 쪼개기] ")
print("==========================================================")

# 마스터 파일 존재 여부 확인
if not MASTER_FILE.exists():
    print(f"최종 마스터 파일이 존재하지 않습니다. 경로를 확인해 주세요: {MASTER_FILE}")
    exit()

# 데이터 로드
df = pd.read_csv(MASTER_FILE)
df["district"] = df["district"].astype(str).str.strip()

# 양천구 필터링
df_yc = df[df["district"] == "양천구"].copy()

if df_yc.empty:
    print(" 마스터 데이터셋 내에서 '양천구' 데이터를 찾을 수 없습니다.")
    exit()

# -----------------------------------------------------------------
# 1. 사회적 취약성 데이터 (고령인구, 기초생활수급자 원시값 및 스코어)
# -----------------------------------------------------------------
social_cols = ["district", "year", "elderly_pop", "total_recipients", "Vulnerability_Score"]
df_social = df_yc[social_cols].copy()
social_output = MASTER_DIR / "양천구_social_vulnerability.csv"
df_social.to_csv(social_output, index=False, encoding="utf-8-sig")
print(f"파일 1 생성 완료 (사회적 취약성): {social_output.name}")

# -----------------------------------------------------------------
# 2. 환경 노출 데이터 (녹지율, 불투수면적 비율 원시값 및 스코어)
# -----------------------------------------------------------------
env_cols = ["district", "year", "녹지율", "불투수면적_비율", "Exposure_Score"]
df_env = df_yc[env_cols].copy()
env_output = MASTER_DIR / "양천구_env_exposure.csv"
df_env.to_csv(env_output, index=False, encoding="utf-8-sig")
print(f"파일 2 생성 완료 (환경 노출): {env_output.name}")

# -----------------------------------------------------------------
# 3. 위험 감소 요소 데이터 (무더위쉼터, 쿨링포그, 그늘막 개수 및 스코어)
# -----------------------------------------------------------------
adaptive_cols = ["district", "year", "무더위쉼터_수", "쿨링포그_수", "그늘막_수", "Adaptive_Score"]
df_adaptive = df_yc[adaptive_cols].copy()
adaptive_output = MASTER_DIR / "양천구_adaptive_capacity.csv"
df_adaptive.to_csv(adaptive_output, index=False, encoding="utf-8-sig")
print(f"파일 3 생성 완료 (위험 감소 요소): {adaptive_output.name}")

# -----------------------------------------------------------------
# 4. 실측 피해 데이터 (온열질환자 수 및 최종 취약 순위 결과)
# -----------------------------------------------------------------
outcome_cols = ["district", "year", "heat_patients", "HVI_Score", "폭염_취약순위"]
df_outcome = df_yc[outcome_cols].copy()
outcome_output = MASTER_DIR / "양천구_heat_patients_outcome.csv"
df_outcome.to_csv(outcome_output, index=False, encoding="utf-8-sig")
print(f"파일 4 생성 완료 (실측 온열질환자): {outcome_output.name}")

print("==========================================================")
print("모든 도메인별 파일이 지정된 규칙에 맞게 개별 분리되었습니다.")
print("==========================================================")