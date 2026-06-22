from pathlib import Path
import pandas as pd


def load_impervious_surface(file_path):
    """
    [불투수면적 엑셀 파일 로더]
    - 자치구명, 구 전체면적(ha), 불투수면적 비율(%)을 깨끗하게 파싱합니다.
    - 정규화 연산을 섞지 않고, 이후 일괄 조인을 위해 순수 물리적 수치(%)만 보관합니다.
    """
    try:
        # 두 파일이 모두 .xlsx 엑셀로 저장되었을 때 실행되는 안전한 기본 엔진
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception:
        # 혹시 기존의 변환 전 csv 텍스트 성격이 남아있는 경우를 대비한 2차 방어벽
        df = pd.read_csv(file_path, encoding="cp949", engine="python", on_bad_lines="skip")

    # 분석용 컬럼 표준 이름 매핑
    df = df.rename(
        columns={
            "자치구": "district",
            "구 전체면적(ha)": "total_area_ha",
            "불투수면적 비율(%)": "불투수면적_비율",
        }
    )

    # 데이터 타입 정제 및 공백 문자 제거
    df["district"] = df["district"].astype(str).str.strip()
    df["불투수면적_비율"] = pd.to_numeric(df["불투수면적_비율"], errors="coerce")
    df["total_area_ha"] = pd.to_numeric(df["total_area_ha"], errors="coerce")

    # '합계', '소계' 등의 요약 행은 필터링하고 '구'로 끝나는 행만 추출
    df = df[df["district"].str.endswith("구")]

    return df[["district", "total_area_ha", "불투수면적_비율"]]


def load_green_space(file_path):
    """
    [녹지현황 엑셀 파일 로더]
    - 엑셀로 변환된 녹지현황 파일에서 상단의 설명 메타데이터 영역을 우회하여 
      실제 데이터 행(4번째 줄, 인덱스 3)부터 자치구명과 합계 면적(㎡)을 추출합니다.
    - 엑셀로 저장하면 천단위 쉼표(,)가 섞여 있어도 판다스가 알아서 숫자로 올바르게 변환합니다.
    """
    # 다중 헤더 및 메타데이터 영역 분석을 위해 처음에는 header 없이 로드
    df = pd.read_excel(file_path, header=None, engine="openpyxl")

    # 실 데이터 수집 (2번째 열: 자치구명, 4번째 열: 합계 면적)
    districts = df.iloc[3:, 1].astype(str).str.strip()
    green_areas = pd.to_numeric(df.iloc[3:, 3], errors="coerce")

    # 임시 데이터프레임 빌드
    green_df = pd.DataFrame({"district": districts, "녹지_총면적_m2": green_areas})
    
    # '구'로 끝나는 정식 행정 자치구만 슬라이싱
    green_df = green_df[green_df["district"].str.endswith("구")]

    return green_df