from pathlib import Path
import pandas as pd

# 만약 코드를 분리하셨다면 아래 공통 함수 import 주석을 해제하세요.
from utils.cooling import *

# --- 경로 정의 ---
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "cooling"
PROCESSED_DIR = BASE_DIR / "data" / "processed" / "cooling"

# 엑셀 파일명 경로 매핑
climate_shelter_file = RAW_DIR / "climate_shelter.xlsx"
smart_shelter_file = RAW_DIR / "smart_shelter.xlsx"
canopy_file = RAW_DIR / "canopy.xlsx"
cooling_fog_file = RAW_DIR / "cooling_fog.xlsx"

# 1. 자치구별 통계 산출
df_climate = count_by_district(
    climate_shelter_file, load_climate_shelter, "climate_shelter_cnt"
)
df_smart = count_by_district(
    smart_shelter_file, load_smart_shelter, "smart_shelter_cnt"
)
df_canopy = count_by_district(canopy_file, load_canopy, "그늘막_수")
df_cooling = count_by_district(cooling_fog_file, load_cooling_fog, "쿨링포그_수")

# 2. 서울시 25개 자치구 마스터 프레임 고정 선언
seoul_districts = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
]
final_adaptive = pd.DataFrame({"district": seoul_districts})

# 3. 데이터 Left Join 일괄 통합 및 공백 데이터는 0개 처리
final_adaptive = pd.merge(final_adaptive, df_climate, on="district", how="left")
final_adaptive = pd.merge(final_adaptive, df_smart, on="district", how="left")
final_adaptive = pd.merge(final_adaptive, df_canopy, on="district", how="left")
final_adaptive = pd.merge(final_adaptive, df_cooling, on="district", how="left")
final_adaptive = final_adaptive.fillna(0)

# 4. 분석 프레임워크 가이드 결합 (무더위쉼터 = 기후동행 + 스마트쉼터)
final_adaptive["무더위쉼터_수"] = (
    final_adaptive["climate_shelter_cnt"] + final_adaptive["smart_shelter_cnt"]
)
final_adaptive = final_adaptive[
    ["district", "무더위쉼터_수", "쿨링포그_수", "그늘막_수"]
].copy()

# 데이터 최종 정수형(Int) 스케일링
for col in ["무더위쉼터_수", "쿨링포그_수", "그늘막_수"]:
    final_adaptive[col] = final_adaptive[col].astype(int)

# 5. 최종 결과 CSV 저장
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
final_adaptive.to_csv(
    PROCESSED_DIR / "seoul_adaptive_capacity.csv",
    index=False,
    encoding="utf-8-sig",
)

print("--- [성공] 모든 엑셀 데이터 파싱 및 통합 완료 ---")
print(final_adaptive.to_string(index=False))