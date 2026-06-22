from pathlib import Path
import pandas as pd

def save_csv(df, output_path):
    """결과 데이터를 csv로 저장 (폴더 자동 생성)"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def clean_district_data(df, district_col):
    """자치구 데이터 정제 ('소계', '합계' 제외)"""
    df = df.copy()
    invalid_names = ["소계", "합계"]
    df = df[~df[district_col].isin(invalid_names)]
    df[district_col] = df[district_col].str.strip()
    return df


def melt_yearly_columns(df, id_vars, value_name, var_name="year"):
    """가로로 나열된 연도별 컬럼을 세로 구조로 변환"""
    melted = df.melt(id_vars=id_vars, var_name=var_name, value_name=value_name)
    melted[var_name] = pd.to_numeric(
        melted[var_name].str.extract(r"(\d+)")[0], errors="coerce"
    )
    return melted.dropna(subset=[var_name]).reset_index(drop=True)