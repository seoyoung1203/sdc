# SDC Climate Risk Project

## 프로젝트 목적

여름철 기후 리스크 데이터를 수집 및 전처리하여
GIS 기반 취약성 분석 데이터셋 구축, 정책 방향성 수립

---

## 프로젝트 구조
sdc/
│
├── data/
│   ├── raw/
│   │   ├── ta_20260528131309.csv
│   │   └── seoul_heat_shelter.csv
│   │
│   └── processed/
│       ├── seoul_heatwave_only.csv
│       └── seoul_heat_shelter_processed.csv
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