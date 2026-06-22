# SDC Climate Risk Project

## 프로젝트 목적

여름철 기후 리스크 데이터를 수집 및 전처리하여
GIS 기반 취약성 분석 데이터셋 구축, 정책 방향성 수립

---

## 프로젝트 구조
```
sdc/
│
data/
├── raw/
│   ├── outcome/   # 결과 변수
│   ├── climate/   # 기후 변수
│   ├── social/    # 사회 취약성
│   ├── env/       # 환경 변수
│   └── cooling/   # 폭염 저감 시설
│
├── processed/
│   ├── outcome/
│   ├── climate/
│   ├── social/
│   ├── env/
│   └── cooling/
│
└── master/
    └── heat_risk_master.csv
│
├── scripts/
│   ├── preprocess_temperature.py
│   ├── preprocess_shelter.py
│   └── merge_climate_data.py (아직)
│
├── notebooks/
│
├── gis/(지도 찍을때)
│
├── .gitignore
├── requirements.txt
└── README.md
```
---
processed/climate/

heat_index.csv
├─ 전체 체감온도 데이터

summer_weather.csv
├─ 6~8월 데이터

heat_index_30plus.csv
├─ 체감온도 30도 이상

heatwave_days.csv
├─ 최고기온 30도 이상

tropical_nights.csv
├─ 여름철 열대야일수

---

## 사용 데이터

- 기상청 기온 데이터
- 서울시 무더위쉼터 데이터

---

## 사용 기술

- Python
- pandas
- geopandas
- GIS
- GitHub

---

## 설치 방법

```bash
pip install -r requirements.txt

```
---
## 최종 정규화 파일 컬럼명
district: 서울시 25개 자치구 명칭 (공간 조인의 기준키)

year: 데이터의 기준 연도

elderly_pop: 65세 이상 고령인구 수 (명)

total_recipients: 기초생활수급자 전체 인구 수 (명)

elderly_recipients / elderly_recipient_ratio: 고령 수급자 수 및 비율

녹지율: 자치구 전체 면적 대비 녹지 면적 비율 (%)

불투수면적_비율: 아스팔트, 콘크리트 등으로 덮인 면적 비율 (%)

무더위쉼터_수 / 쿨링포그_수 / 그늘막_수: 각 자치구에 설치된 폭염 저감 시설의 개수