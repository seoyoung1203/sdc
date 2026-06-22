from pathlib import Path
import pandas as pd


def count_by_district(file_path, df_loader_func, rename_col_to):
    """각 시설별 엑셀 파일을 로드한 후, 자치구(district) 단위로 개수를 집계하여 반환합니다."""
    df = df_loader_func(file_path)

    # 문자열 처리 및 공백 제거
    df["district"] = df["district"].astype(str).str.strip()

    # 자치구명이 결측치거나 잘못된 경우 필터링
    df = df[df["district"].notna() & (df["district"] != "nan") & (df["district"] != "")]

    # '구'로 끝나는 행만 추출 (예: '종로구', '강남구')
    df = df[df["district"].str.endswith("구")]

    # 자치구별 개수 집계
    counts = df.groupby("district").size().reset_index(name=rename_col_to)
    return counts


# --- [안전한 컬럼 변환이 적용된 전용 로더 함수들] ---


def load_climate_shelter(file_path):
    """기후동행쉼터 로더"""
    df = pd.read_excel(file_path, engine="openpyxl")
    
    # '구이름' 혹은 '시군구'를 찾아서 district로 매핑
    district_col = [c for c in df.columns if "구이름" in str(c) or "시군구" in str(c)]
    if district_col:
        df = df.rename(columns={district_col[0]: "district"})
    else:
        # 못 찾으면 4번째 열(Index 3)을 강제 지정 (Read-only 에러 방지 문법)
        cols = list(df.columns)
        cols[3] = "district"
        df.columns = cols
        
    return df[["district"]]


def load_smart_shelter(file_path):
    """스마트쉼터 현황 로더 (상단 제목 제외하고 진짜 데이터 행 추적)"""
    df = pd.read_excel(file_path, engine="openpyxl")
    
    start_idx = 0
    for idx, row in df.iterrows():
        if "서울" in str(row.iloc[0]) or "시도" in str(row.iloc[0]):
            start_idx = idx
            break
            
    # 헤더 재설정 및 슬라이싱
    df.columns = df.iloc[start_idx]
    df = df.iloc[start_idx+1:].reset_index(drop=True)
    
    # 두 번째 열(Index 1)이 '시군구'이므로 컬럼명을 district로 안전하게 강제 매핑
    cols = list(df.columns)
    cols[1] = "district"
    df.columns = cols
    return df[["district"]]


def load_canopy(file_path):
    """그늘막 목록 로더 (다중 헤더 우회)"""
    df = pd.read_excel(file_path, engine="openpyxl", header=None)
    
    start_idx = 0
    for idx, row in df.iterrows():
        if "연번" in str(row.iloc[0]) or "종류" in str(row.iloc[1]):
            start_idx = idx
            break
            
    df.columns = df.iloc[start_idx]
    df = df.iloc[start_idx+1:].reset_index(drop=True)
    
    # 4번째 컬럼(Index 3) '시군구'를 안전하게 district로 변경
    cols = list(df.columns)
    cols[3] = "district"
    df.columns = cols
    return df[["district"]]


def load_cooling_fog(file_path):
    """쿨링포그 목록 로더 (Read-only 에러 해결 및 주소 추적 포함)"""
    df = pd.read_excel(file_path, engine="openpyxl", header=None)
    
    start_idx = 0
    for idx, row in df.iterrows():
        if "연번" in str(row.iloc[0]) or "종류" in str(row.iloc[1]):
            start_idx = idx
            break
            
    df.columns = df.iloc[start_idx]
    df = df.iloc[start_idx+1:].reset_index(drop=True)
    
    # Read-only 에러 우회 문법 적용 (4번째: 시군구, 7번째: 주소)
    cols = list(df.columns)
    cols[3] = "district"
    cols[6] = "address"
    df.columns = cols

    # '서울특별시' 취약지 주소 복원 로직
    def extract_gu(row):
        dist = str(row["district"]).strip()
        if "구" in dist and not dist.startswith("서울"):
            return dist
        addr = str(row["address"])
        for part in addr.split():
            if part.endswith("구"):
                return part
        return dist

    df["district"] = df.apply(extract_gu, axis=1)
    return df[["district"]]