from pathlib import Path
import pandas as pd

from utils.env import load_impervious_surface, load_green_space

# --- 경로 정의 ---
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "env"
PROCESSED_DIR = BASE_DIR / "data" / "processed" / "env"

# 둘 다 엑셀 파일명으로 깔끔하게 매핑
impervious_file = RAW_DIR / "impervious_surface.xlsx"
green_file = RAW_DIR / "green_space.xlsx"  # <- 엑셀로 저장한 파일명

# 1. 엑셀 전용 로더로 데이터 수집 (인코딩 에러 원천 차단)
df_impervious = load_impervious_surface(impervious_file)
df_green = load_green_space(green_file)

# 2. 서울시 25개 자치구 마스터 프레임 생성
seoul_districts = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
]
final_exposure = pd.DataFrame({"district": seoul_districts})

# 3. 데이터 Left Join 통합
final_exposure = pd.merge(final_exposure, df_impervious, on="district", how="left")
final_exposure = pd.merge(final_exposure, df_green, on="district", how="left")

# 4. 환경 변수 스케일 단일화 (1 ha = 10,000 ㎡) 및 녹지율(%) 계산
final_exposure["total_area_m2"] = final_exposure["total_area_ha"] * 10000
final_exposure["녹지율"] = (final_exposure["녹지_총면적_m2"] / final_exposure["total_area_m2"]) * 100

final_exposure["녹지율"] = final_exposure["녹지율"].round(2)
final_exposure["불투수면적_비율"] = final_exposure["불투수면적_비율"].round(2)
final_exposure = final_exposure.fillna(final_exposure.mean(numeric_only=True))

# 5. [정석 설계] 순수 물리 % 지표만 결합용으로 저장
df_exposure_save = final_exposure[["district", "녹지율", "불투수면적_비율"]].copy()

# 6. 최종 파일 아카이빙
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
df_exposure_save.to_csv(
    PROCESSED_DIR / "seoul_environmental_exposure.csv",
    index=False,
    encoding="utf-8-sig"
)

print("--- [성공] 엑셀 기반 파일 전처리 및 순수 데이터 저장 완료 ---")
print(df_exposure_save.head(5))