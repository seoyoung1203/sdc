import pandas as pd


def add_year_month(df, date_col="date"):

    df[date_col] = pd.to_datetime(df[date_col])

    df["year"] = df[date_col].dt.year
    df["month"] = df[date_col].dt.month

    return df


def filter_summer(df):

    return df[
        df["month"].isin([6, 7, 8])
    ].copy()


def filter_years(
    df,
    start_year=2023,
    end_year=2025
):

    return df[
        df["year"].between(
            start_year,
            end_year
        )
    ].copy()


def save_csv(
    df,
    output_path
):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )


def yearly_mean(
    df,
    value_col,
    output_col
):

    result = (
        df.groupby("year")[value_col]
          .mean()
          .reset_index()
    )

    return result.rename(
        columns={
            value_col: output_col
        }
    )

def load_yearly_climate_csv(
    file_path,
    skiprows=5
):
    """
    기상청 통계표 형식 CSV

    - 설명 행 제거
    - 평균, 순위 등 제거
    - 숫자 연도만 남김
    """

    df = pd.read_csv(
        file_path,
        encoding="euc-kr",
        skiprows=skiprows
    )

    year_col = df.columns[0]

    df[year_col] = pd.to_numeric(
        df[year_col],
        errors="coerce"
    )

    df = df[
        df[year_col].notna()
    ].copy()

    df[year_col] = df[year_col].astype(int)

    return df.reset_index(drop=True)