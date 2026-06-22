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