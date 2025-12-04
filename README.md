# 🏢 Potential LP 모니터링 대시보드

인프라프론티어자산운용(주)를 위한 **Potential LP(유한책임사원) 발굴 및 ESG 모니터링 대시보드**입니다.

## 🎯 주요 기능

### 1. 🔍 LP 발굴
- **DART API 연동**: 이익잉여금 300억원 이상 기업 자동 조회
- **필터링**: 업종, ESG 등급, 이익잉여금 기준 필터링
- **LP 스코어**: 이익잉여금(40%) + 자본(20%) + ESG(40%) 가중 점수
- **다운로드**: Excel/CSV 형식 다운로드

### 2. 🌱 ESG 모니터링
- **키워드 검색**: "탄소중립", "RE100", "ESG경영" 등 DART 공시 검색
- **지속가능경영보고서**: 최근 공시 목록
- **ESG 등급**: 서스틴베스트 기준 등급 조회

### 3. 📊 분석
- 업종별 이익잉여금 분포 차트
- ESG 등급별 기업 분포
- LP 스코어 구성 분석

## 🚀 배포

### Streamlit Cloud
1. GitHub에 Repository 생성
2. `app.py`, `requirements.txt` 업로드
3. [share.streamlit.io](https://share.streamlit.io) 에서 배포

### DART API 키 설정
Streamlit Cloud → Settings → Secrets에 추가:
```toml
DART_API_KEY = "your_api_key_here"
```

## 📁 파일 구조

```
lp-dashboard/
├── app.py              # 메인 대시보드 코드
├── requirements.txt    # Python 패키지
├── README.md           # 설명서
└── data/               # 데이터 폴더 (선택)
    └── sample_data.csv
```

## 🔧 활용 기법

| 강의 파일 | 활용 기법 | 적용 위치 |
|----------|----------|----------|
| 사업보고서_추출.ipynb | DART API, pd.read_html() | 재무제표 조회 |
| 공시내용_특정Keyword.ipynb | requests.post(), BeautifulSoup | ESG 공시 검색 |
| ESG등급상관관계.ipynb | 등급 수치화 | ESG 스코어 계산 |
| 최적화_사례_시뮬레이션.ipynb | 목적함수, 가중 스코어 | LP 스코어 계산 |

## 📧 문의

- **담당자**: 박연준
- **이메일**: yjpark@ifasset.co.kr
- **버전**: v1.0 (2025.12)

---
© 2025 인프라프론티어자산운용(주)
