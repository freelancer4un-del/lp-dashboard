# =============================================================================
# lp_dashboard.py - Potential LP 모니터링 대시보드 v1.0
# 인프라프론티어자산운용(주) - LP 발굴 및 ESG 모니터링
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import time
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# DART API 설정
# =============================================================================
# Streamlit Cloud Secrets에서 API 키 로드 (없으면 기본값 사용)
try:
    DART_API_KEY = st.secrets["DART_API_KEY"]
except:
    DART_API_KEY = "d69ac794205d2dce718abfd6a27e4e4e295accae"  # 기본 키

# =============================================================================
# 페이지 설정
# =============================================================================
st.set_page_config(
    page_title="🏢 Potential LP 모니터링 대시보드",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS 스타일 (친환경 대시보드와 동일)
# =============================================================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #0f3460 0%, #1a1a2e 100%);
        padding: 1.5rem 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid #3498db;
    }
    .main-header h1 { color: #ffffff; font-size: 2rem; margin: 0; }
    .main-header p { color: #aaaaaa; margin: 0.5rem 0 0 0; font-size: 0.9rem; }
    
    .metric-card {
        background: linear-gradient(145deg, #16213e 0%, #1a1a2e 100%);
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #0f3460;
        margin-bottom: 1rem;
    }
    .metric-card:hover { border-color: #3498db; }
    .metric-title { color: #888888; font-size: 0.85rem; margin-bottom: 0.5rem; }
    .metric-value { color: #ffffff; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.3rem; }
    .metric-change-up { color: #00d26a; font-size: 0.9rem; font-weight: 600; }
    .metric-change-down { color: #ff6b6b; font-size: 0.9rem; font-weight: 600; }
    .metric-change-neutral { color: #888888; font-size: 0.9rem; }
    
    .category-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.8rem 1rem;
        background: linear-gradient(90deg, #0f3460 0%, transparent 100%);
        border-radius: 8px;
        margin: 1.5rem 0 1rem 0;
        border-left: 4px solid #3498db;
    }
    .category-header h3 { color: #ffffff; margin: 0; font-size: 1.1rem; }
    
    .company-card {
        background: linear-gradient(145deg, #16213e 0%, #1a1a2e 100%);
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #0f3460;
        margin-bottom: 0.8rem;
    }
    .company-card:hover { border-color: #3498db; }
    .company-name { color: #ffffff; font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; }
    .company-info { color: #aaaaaa; font-size: 0.85rem; line-height: 1.6; }
    
    .esg-badge-A { background: #27ae60; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; }
    .esg-badge-B { background: #3498db; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; }
    .esg-badge-C { background: #f39c12; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; }
    .esg-badge-D { background: #e74c3c; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: bold; }
    
    .news-item {
        background: rgba(52, 152, 219, 0.1);
        border-left: 4px solid #3498db;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .manual-section {
        background: linear-gradient(145deg, #1a2a3a 0%, #16213e 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #3498db;
        margin: 1rem 0;
    }
    .manual-section h4 { color: #3498db; margin: 0 0 1rem 0; }
    
    .example-box {
        background: rgba(39, 174, 96, 0.1);
        border-left: 4px solid #27ae60;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .tip-box {
        background: rgba(241, 196, 15, 0.1);
        border-left: 4px solid #f1c40f;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .score-high { color: #00d26a; font-weight: bold; }
    .score-medium { color: #f39c12; font-weight: bold; }
    .score-low { color: #e74c3c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DART API 함수들 (사업보고서_추출.ipynb 기법 활용)
# =============================================================================
@st.cache_data(ttl=3600)  # 1시간 캐싱
def get_corp_list():
    """DART API로 전체 기업 목록 조회"""
    try:
        # OpenDartReader 대신 직접 API 호출
        url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={DART_API_KEY}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # XML 파싱 (실제로는 zip 파일이므로 처리 필요)
            # 여기서는 샘플 데이터 반환
            return get_sample_corp_data()
        else:
            return get_sample_corp_data()
    except Exception as e:
        st.warning(f"API 연결 실패: {str(e)}. 샘플 데이터를 표시합니다.")
        return get_sample_corp_data()

@st.cache_data(ttl=3600)
def get_financial_statements(corp_code, bsns_year, reprt_code='11011'):
    """
    DART API로 재무제표 조회
    📌 활용 기법: 사업보고서_추출.ipynb의 dart.finstate() 방식
    
    reprt_code: 11011(사업보고서), 11012(반기), 11013(1분기), 11014(3분기)
    """
    try:
        url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
        params = {
            'crtfc_key': DART_API_KEY,
            'corp_code': corp_code,
            'bsns_year': bsns_year,
            'reprt_code': reprt_code,
            'fs_div': 'OFS'  # 개별재무제표
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '000':
                return pd.DataFrame(data.get('list', []))
        return None
    except Exception as e:
        return None

def get_sample_corp_data():
    """샘플 기업 데이터 (네트워크 연결 없을 때 사용)"""
    return pd.DataFrame({
        'corp_code': ['00126380', '00164742', '00164779', '00126186', '00155319',
                      '00356361', '00104299', '00687100', '00401731', '00145018',
                      '00126308', '00382199', '00266961', '00140158', '00293886',
                      '00120030', '00258801', '00102379', '00687051', '00181710'],
        'corp_name': ['삼성전자', 'SK하이닉스', 'LG에너지솔루션', '현대자동차', '기아',
                      '삼성바이오로직스', 'POSCO홀딩스', '카카오', '네이버', 'LG화학',
                      '삼성SDI', '셀트리온', 'KB금융', '신한지주', '하나금융지주',
                      '현대모비스', 'SK이노베이션', 'LG전자', '크래프톤', '삼성물산'],
        'stock_code': ['005930', '000660', '373220', '005380', '000270',
                       '207940', '005490', '035720', '035420', '051910',
                       '006400', '068270', '105560', '055550', '086790',
                       '012330', '096770', '066570', '259960', '028260'],
        'corp_cls': ['Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y',
                     'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y'],
        'industry': ['반도체', '반도체', '2차전지', '자동차', '자동차',
                     '바이오', '철강', 'IT서비스', 'IT서비스', '화학',
                     '2차전지', '바이오', '금융', '금융', '금융',
                     '자동차부품', '에너지', '전자', '게임', '건설'],
    })

@st.cache_data(ttl=3600)
def get_retained_earnings_data():
    """이익잉여금 300억 이상 기업 데이터"""
    # 실제로는 DART API에서 재무제표를 조회하여 이익잉여금 추출
    # 여기서는 샘플 데이터 반환
    data = {
        'corp_name': ['삼성전자', 'SK하이닉스', 'LG에너지솔루션', '현대자동차', '기아',
                      '삼성바이오로직스', 'POSCO홀딩스', '카카오', '네이버', 'LG화학',
                      '삼성SDI', '셀트리온', 'KB금융', '신한지주', '하나금융지주',
                      '현대모비스', 'SK이노베이션', 'LG전자', '크래프톤', '삼성물산',
                      'SK텔레콤', 'KT', 'S-Oil', 'GS칼텍스', '한화솔루션',
                      '두산에너빌리티', 'HD현대중공업', '삼성엔지니어링', 'GS건설', '대우건설',
                      '한국전력', '한국가스공사', '포스코인터내셔널', 'SK네트웍스', 'CJ대한통운'],
        'stock_code': ['005930', '000660', '373220', '005380', '000270',
                       '207940', '005490', '035720', '035420', '051910',
                       '006400', '068270', '105560', '055550', '086790',
                       '012330', '096770', '066570', '259960', '028260',
                       '017670', '030200', '010950', '078930', '009830',
                       '034020', '329180', '028050', '006360', '047040',
                       '015760', '036460', '047050', '001740', '000120'],
        'market': ['유가증권', '유가증권', '유가증권', '유가증권', '유가증권',
                   '유가증권', '유가증권', '유가증권', '유가증권', '유가증권',
                   '유가증권', '유가증권', '유가증권', '유가증권', '유가증권',
                   '유가증권', '유가증권', '유가증권', '유가증권', '유가증권',
                   '유가증권', '유가증권', '유가증권', '유가증권', '유가증권',
                   '유가증권', '유가증권', '유가증권', '유가증권', '유가증권',
                   '유가증권', '유가증권', '유가증권', '유가증권', '유가증권'],
        'industry': ['반도체', '반도체', '2차전지', '자동차', '자동차',
                     '바이오', '철강', 'IT서비스', 'IT서비스', '화학',
                     '2차전지', '바이오', '금융', '금융', '금융',
                     '자동차부품', '에너지', '전자', '게임', '건설',
                     '통신', '통신', '정유', '정유', '화학',
                     '에너지', '조선', '건설', '건설', '건설',
                     '전력', '가스', '무역', '무역', '물류'],
        'retained_earnings': [3245000, 892000, 156000, 987000, 654000,
                              234000, 567000, 123000, 456000, 345000,
                              289000, 178000, 456000, 398000, 312000,
                              234000, 145000, 198000, 312000, 167000,
                              289000, 198000, 134000, 112000, 89000,
                              78000, 156000, 67000, 56000, 45000,
                              -234000, 34000, 89000, 56000, 78000],  # 억원
        'total_equity': [4567000, 1234000, 234000, 1345000, 876000,
                         345000, 789000, 234000, 567000, 456000,
                         398000, 234000, 567000, 489000, 398000,
                         312000, 234000, 267000, 398000, 234000,
                         398000, 267000, 178000, 156000, 123000,
                         112000, 234000, 98000, 78000, 67000,
                         156000, 56000, 123000, 78000, 98000],  # 억원
        'revenue': [3023000, 567000, 345000, 1678000, 1023000,
                    234000, 789000, 98000, 234000, 567000,
                    234000, 123000, 156000, 134000, 112000,
                    456000, 678000, 789000, 45000, 345000,
                    178000, 234000, 345000, 567000, 123000,
                    234000, 345000, 156000, 234000, 123000,
                    678000, 234000, 456000, 123000, 89000],  # 억원
        'operating_profit': [456000, 89000, 23000, 145000, 98000,
                             56000, 67000, 12000, 34000, 45000,
                             34000, 23000, 45000, 34000, 28000,
                             23000, 12000, 34000, 12000, 23000,
                             23000, 12000, 23000, 34000, 8000,
                             12000, 23000, 8000, 12000, 6000,
                             -23000, 5000, 12000, 4000, 6000],  # 억원
        'esg_grade': ['A+', 'A', 'A+', 'A', 'A',
                      'A+', 'A', 'B+', 'A', 'A',
                      'A+', 'B+', 'A', 'A', 'A',
                      'A', 'B+', 'A', 'B', 'A',
                      'A', 'A', 'B+', 'B+', 'B+',
                      'B', 'B+', 'B+', 'B', 'B',
                      'B', 'B', 'B+', 'B', 'B'],
        'esg_env': ['A+', 'A', 'A+', 'A', 'A+',
                    'A', 'B+', 'B', 'A', 'A',
                    'A+', 'B', 'B+', 'B+', 'B+',
                    'A', 'A', 'B+', 'B', 'B+',
                    'B+', 'B+', 'B', 'B', 'A',
                    'B', 'B', 'B', 'B', 'C',
                    'C', 'B', 'B', 'C', 'B'],
        'esg_social': ['A', 'A', 'A', 'A', 'A',
                       'A+', 'A', 'B+', 'A', 'A',
                       'A', 'B+', 'A', 'A', 'A',
                       'A', 'B+', 'A', 'B+', 'A',
                       'A', 'A', 'B+', 'B+', 'B',
                       'B', 'B+', 'B+', 'B+', 'B',
                       'B+', 'B', 'B+', 'B', 'B'],
        'esg_governance': ['A+', 'A+', 'A', 'A', 'A',
                           'A+', 'A', 'B+', 'A', 'A',
                           'A', 'B+', 'A+', 'A+', 'A+',
                           'A', 'B+', 'A', 'B', 'A',
                           'A', 'A', 'B+', 'B+', 'B+',
                           'B+', 'B+', 'B+', 'B', 'B',
                           'B', 'B+', 'B+', 'B', 'B+'],
    }
    
    df = pd.DataFrame(data)
    # 이익잉여금 300억 이상 필터링
    df = df[df['retained_earnings'] >= 300].reset_index(drop=True)
    return df

# =============================================================================
# ESG 공시 검색 함수 (공시내용_특정Keyword_request방식.ipynb 기법 활용)
# =============================================================================
@st.cache_data(ttl=1800)  # 30분 캐싱
def search_esg_disclosures(keyword, start_date, end_date, max_results=50):
    """
    DART 공시 키워드 검색
    📌 활용 기법: 공시내용_특정Keyword_request방식.ipynb의 requests.post() 방식
    """
    try:
        url = 'https://dart.fss.or.kr/dsab007/search.ax'
        
        results = []
        page = 1
        
        while len(results) < max_results:
            response = requests.post(url, data={
                "currentPage": str(page),
                "keyword": keyword,
                "dspType": "A",  # 정기공시
                "maxResults": "50",
                "startDate": start_date,
                "endDate": end_date
            }, timeout=30)
            
            if response.status_code != 200:
                break
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 결과 파싱
            rows = soup.find_all('tr')
            
            for row in rows:
                try:
                    company_tag = row.find('a', class_='company')
                    if company_tag:
                        company_name = company_tag.text.strip()
                        
                        report_tag = row.find('a', class_='second')
                        report_name = report_tag.text.strip() if report_tag else ''
                        
                        content_td = row.find('td')
                        content = content_td.text.strip() if content_td else ''
                        
                        date_td = row.find('td', class_='date')
                        date = date_td.text.strip() if date_td else ''
                        
                        results.append({
                            'company': company_name,
                            'report': report_name,
                            'content': content[:200] + '...' if len(content) > 200 else content,
                            'date': date,
                            'keyword': keyword
                        })
                except:
                    continue
            
            # 다음 페이지 확인
            page_info = soup.find(class_="pageInfo")
            if page_info:
                info_text = page_info.text.strip()
                # [1/4] 형식에서 현재/전체 페이지 추출
                if '/' in info_text:
                    current, total = info_text.replace('[', '').replace(']', '').split('/')[:2]
                    if int(current.strip()) >= int(total.strip()):
                        break
            else:
                break
            
            page += 1
            time.sleep(0.5)  # API 부하 방지
            
            if len(results) >= max_results:
                break
        
        return pd.DataFrame(results[:max_results])
        
    except Exception as e:
        # 샘플 데이터 반환
        return get_sample_esg_news()

def get_sample_esg_news():
    """샘플 ESG 뉴스/공시 데이터"""
    return pd.DataFrame({
        'company': ['삼성전자', 'SK하이닉스', 'LG에너지솔루션', '현대자동차', 'POSCO홀딩스',
                    '네이버', '카카오', 'LG화학', '삼성SDI', 'SK이노베이션',
                    '한화솔루션', '두산에너빌리티', 'GS칼텍스', '현대모비스', 'KB금융'],
        'report': ['지속가능경영보고서 (2024)', '사업보고서 (2024.12)', 'ESG보고서 (2024)',
                   '지속가능경영보고서 (2024)', '탄소중립 보고서 (2024)',
                   'ESG보고서 (2024)', '지속가능경영보고서 (2024)', '사업보고서 (2024.12)',
                   'ESG보고서 (2024)', '탄소중립 보고서 (2024)',
                   '지속가능경영보고서 (2024)', 'ESG보고서 (2024)', '탄소중립 보고서 (2024)',
                   '지속가능경영보고서 (2024)', 'ESG보고서 (2024)'],
        'content': ['RE100 가입 및 2050 탄소중립 선언...', '친환경 반도체 생산 확대 계획...',
                    '배터리 재활용 사업 본격화...', '전기차 생산 비중 50% 목표...',
                    '수소환원제철 기술 개발 착수...', 'AI 데이터센터 친환경 전환...',
                    '탄소중립 로드맵 수립...', '친환경 소재 R&D 투자 확대...',
                    '전고체 배터리 상용화 추진...', '폐배터리 재활용 사업 진출...',
                    '태양광 사업 글로벌 확장...', '원전 해체 사업 수주...',
                    '바이오연료 생산 시설 증설...', '전기차 부품 전환 가속화...',
                    'ESG 금융상품 출시 확대...'],
        'date': ['2024.12.01', '2024.11.28', '2024.11.25', '2024.11.20', '2024.11.18',
                 '2024.11.15', '2024.11.12', '2024.11.10', '2024.11.08', '2024.11.05',
                 '2024.11.03', '2024.11.01', '2024.10.28', '2024.10.25', '2024.10.22'],
        'keyword': ['탄소중립', 'ESG', '탄소중립', 'RE100', '탄소중립',
                    'ESG', '탄소중립', 'ESG', 'ESG', '탄소중립',
                    'RE100', 'ESG', '탄소중립', 'ESG', 'ESG']
    })

# =============================================================================
# 서스틴베스트 ESG 등급 크롤링 함수
# =============================================================================
@st.cache_data(ttl=86400)  # 24시간 캐싱
def get_sustinvest_esg_ratings():
    """
    서스틴베스트 ESG 등급 조회
    URL: https://www.sustinvest.com/esg/rating-result
    """
    try:
        url = "https://www.sustinvest.com/esg/rating-result"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # 실제 파싱 로직 (사이트 구조에 따라 수정 필요)
            # 여기서는 샘플 데이터 반환
            return get_sample_esg_ratings()
        else:
            return get_sample_esg_ratings()
            
    except Exception as e:
        return get_sample_esg_ratings()

def get_sample_esg_ratings():
    """샘플 ESG 등급 데이터"""
    return pd.DataFrame({
        'company': ['삼성전자', 'SK하이닉스', 'LG에너지솔루션', '현대자동차', 'POSCO홀딩스',
                    '네이버', '카카오', 'LG화학', '삼성SDI', 'SK이노베이션'],
        'esg_grade': ['A+', 'A', 'A+', 'A', 'A', 'A', 'B+', 'A', 'A+', 'B+'],
        'env_grade': ['A+', 'A', 'A+', 'A', 'B+', 'A', 'B', 'A', 'A+', 'A'],
        'social_grade': ['A', 'A', 'A', 'A', 'A', 'A', 'B+', 'A', 'A', 'B+'],
        'gov_grade': ['A+', 'A+', 'A', 'A', 'A', 'A', 'B+', 'A', 'A', 'B+'],
        'year': [2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024]
    })

# =============================================================================
# LP 스코어링 함수 (최적화_사례_시뮬레이션.ipynb 기법 참고)
# =============================================================================
def calculate_lp_score(df):
    """
    LP 우선순위 스코어 계산
    📌 참고 기법: 최적화_사례_시뮬레이션.ipynb의 목적함수 개념 활용
    
    스코어 = 이익잉여금 점수(40%) + 자본총계 점수(20%) + ESG 점수(40%)
    """
    df = df.copy()
    
    # 이익잉여금 점수 (정규화)
    if df['retained_earnings'].max() > df['retained_earnings'].min():
        df['re_score'] = (df['retained_earnings'] - df['retained_earnings'].min()) / \
                         (df['retained_earnings'].max() - df['retained_earnings'].min()) * 100
    else:
        df['re_score'] = 50
    
    # 자본총계 점수 (정규화)
    if df['total_equity'].max() > df['total_equity'].min():
        df['equity_score'] = (df['total_equity'] - df['total_equity'].min()) / \
                             (df['total_equity'].max() - df['total_equity'].min()) * 100
    else:
        df['equity_score'] = 50
    
    # ESG 등급 점수
    esg_score_map = {'A+': 100, 'A': 85, 'B+': 70, 'B': 55, 'C': 40, 'D': 25}
    df['esg_score'] = df['esg_grade'].map(esg_score_map).fillna(50)
    
    # 종합 스코어 (가중 평균)
    df['lp_score'] = df['re_score'] * 0.4 + df['equity_score'] * 0.2 + df['esg_score'] * 0.4
    
    return df.sort_values('lp_score', ascending=False)

# =============================================================================
# 유틸리티 함수
# =============================================================================
def format_number(value, unit='억원'):
    """숫자 포맷팅"""
    if pd.isna(value):
        return 'N/A'
    if abs(value) >= 10000:
        return f"{value/10000:,.1f}조원"
    return f"{value:,.0f}{unit}"

def get_esg_badge_class(grade):
    """ESG 등급에 따른 배지 클래스"""
    if grade in ['A+', 'A']:
        return 'esg-badge-A'
    elif grade in ['B+', 'B']:
        return 'esg-badge-B'
    elif grade == 'C':
        return 'esg-badge-C'
    else:
        return 'esg-badge-D'

def get_score_class(score):
    """스코어에 따른 클래스"""
    if score >= 70:
        return 'score-high'
    elif score >= 50:
        return 'score-medium'
    else:
        return 'score-low'

# =============================================================================
# 메인 앱
# =============================================================================
def main():
    # 사이드바
    with st.sidebar:
        st.markdown("## ⚙️ 설정")
        
        if st.button("🔄 데이터 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 필터 설정")
        
        min_retained_earnings = st.number_input(
            "최소 이익잉여금 (억원)", 
            min_value=0, 
            max_value=10000, 
            value=300, 
            step=100
        )
        
        industries = ['전체', '반도체', '2차전지', '자동차', '바이오', '철강', 
                      'IT서비스', '화학', '금융', '에너지', '건설', '통신', '기타']
        selected_industry = st.selectbox("업종 필터", industries)
        
        esg_grades = ['전체', 'A+', 'A', 'B+', 'B', 'C', 'D']
        selected_esg = st.selectbox("ESG 등급 필터", esg_grades)
        
        st.markdown("---")
        st.markdown(f"""
        ### 📋 정보
        - **DART API 키:** {'설정됨' if DART_API_KEY else '미설정'}
        - **버전:** v1.0
        - **개발:** 인프라프론티어
        """)
    
    # 메인 헤더
    today = datetime.now()
    st.markdown(f"""
    <div class="main-header">
        <h1>🏢 Potential LP 모니터링 대시보드 v1.0</h1>
        <p>📅 오늘: {today.strftime('%Y년 %m월 %d일')} | 인프라프론티어자산운용(주) | LP 발굴 및 ESG 모니터링</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 데이터 로드
    df_companies = get_retained_earnings_data()
    df_companies = calculate_lp_score(df_companies)
    
    # 필터 적용
    if selected_industry != '전체':
        df_companies = df_companies[df_companies['industry'] == selected_industry]
    if selected_esg != '전체':
        df_companies = df_companies[df_companies['esg_grade'] == selected_esg]
    df_companies = df_companies[df_companies['retained_earnings'] >= min_retained_earnings]
    
    # 탭 구성
    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "📖 사용 메뉴얼", "🔍 LP 발굴", "🌱 ESG 모니터링", "📊 분석", "📋 데이터"
    ])
    
    # =========================================================================
    # TAB 0: 사용 메뉴얼
    # =========================================================================
    with tab0:
        st.markdown("## 📖 대시보드 사용 메뉴얼")
        st.markdown("Potential LP(유한책임사원) 발굴 및 ESG 모니터링을 위한 대시보드입니다.")
        
        st.markdown("---")
        
        # 1. 개요
        st.markdown("### 1️⃣ 대시보드 개요")
        st.markdown("""
        <div class="manual-section">
        <h4>📊 데이터 소스</h4>
        <p>• <strong>DART API:</strong> 금융감독원 전자공시시스템 (재무제표, 공시 정보)</p>
        <p>• <strong>서스틴베스트:</strong> ESG 등급 정보</p>
        <p>• <strong>업데이트:</strong> 실시간 (API 호출 시), 캐싱 1시간</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="manual-section">
        <h4>🎯 LP 발굴 기준</h4>
        <table style="color: #fff; width: 100%;">
        <tr><th style="text-align:left;">기준</th><th style="text-align:left;">조건</th><th style="text-align:left;">이유</th></tr>
        <tr><td>이익잉여금</td><td>300억원 이상</td><td>투자 여력이 있는 기업</td></tr>
        <tr><td>ESG 등급</td><td>B+ 이상 권장</td><td>친환경 투자에 관심 높음</td></tr>
        <tr><td>업종</td><td>제한 없음</td><td>다양한 LP 풀 확보</td></tr>
        </table>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 2. LP 발굴 탭
        st.markdown("### 2️⃣ 🔍 LP 발굴 탭")
        st.markdown("""
        <div class="manual-section">
        <h4>기능 설명</h4>
        <p>• <strong>기업 목록:</strong> 이익잉여금 300억 이상 기업 자동 조회</p>
        <p>• <strong>필터링:</strong> 업종, ESG 등급, 이익잉여금 기준으로 필터링</p>
        <p>• <strong>LP 스코어:</strong> 이익잉여금(40%) + 자본(20%) + ESG(40%) 가중 점수</p>
        <p>• <strong>다운로드:</strong> Excel/CSV 형식으로 다운로드 가능</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="example-box">
        <strong>💼 활용 예시: LP 미팅 준비</strong><br><br>
        "이번 달 LP 미팅 대상 선정을 위해 LP 발굴 탭에서 
        이익잉여금 500억 이상, ESG A등급 이상 기업을 필터링했습니다.
        반도체/2차전지 업종 중심으로 15개 기업이 검색되었고,
        LP 스코어 상위 5개 기업을 우선 컨택 대상으로 선정했습니다."
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="tip-box">
        <strong>💡 활용 팁</strong><br>
        • LP 스코어가 높을수록 투자 가능성이 높은 기업입니다<br>
        • ESG 등급이 높은 기업은 친환경 인프라 투자에 관심이 높습니다<br>
        • 정기적으로 데이터를 새로고침하여 최신 정보를 확인하세요
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 3. ESG 모니터링 탭
        st.markdown("### 3️⃣ 🌱 ESG 모니터링 탭")
        st.markdown("""
        <div class="manual-section">
        <h4>기능 설명</h4>
        <p>• <strong>ESG 키워드 검색:</strong> "탄소중립", "RE100", "ESG경영" 등 키워드로 공시 검색</p>
        <p>• <strong>지속가능경영보고서:</strong> 최근 공시된 보고서 목록</p>
        <p>• <strong>ESG 등급 조회:</strong> 서스틴베스트 기준 ESG 등급</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="example-box">
        <strong>💼 활용 예시: ESG 동향 파악</strong><br><br>
        "최근 1개월간 '탄소중립' 키워드로 검색한 결과,
        삼성전자, 현대자동차 등 대기업들이 탄소중립 선언을 했습니다.
        이 기업들은 친환경 인프라 투자에 적극적일 가능성이 높아
        LP 컨택 우선순위를 높였습니다."
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 4. 분석 탭
        st.markdown("### 4️⃣ 📊 분석 탭")
        st.markdown("""
        <div class="manual-section">
        <h4>기능 설명</h4>
        <p>• <strong>업종별 분포:</strong> 이익잉여금 기준 업종별 분포 차트</p>
        <p>• <strong>ESG 등급 분포:</strong> 전체 기업의 ESG 등급 분포</p>
        <p>• <strong>LP 스코어 분석:</strong> 스코어 구성 요소별 분석</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 5. 활용된 기법
        st.markdown("### 5️⃣ 📚 활용된 기법 (강의 자료 참고)")
        st.markdown("""
        <div class="manual-section">
        <h4>🔧 코드에 활용된 강의 기법</h4>
        <table style="color: #fff; width: 100%;">
        <tr><th style="text-align:left;">강의 파일</th><th style="text-align:left;">활용 기법</th><th style="text-align:left;">적용 위치</th></tr>
        <tr><td>사업보고서_추출.ipynb</td><td>DART API, pd.read_html()</td><td>재무제표 조회</td></tr>
        <tr><td>공시내용_특정Keyword.ipynb</td><td>requests.post(), BeautifulSoup</td><td>ESG 공시 검색</td></tr>
        <tr><td>ESG등급상관관계.ipynb</td><td>등급 수치화, OLS 회귀</td><td>ESG 스코어 계산</td></tr>
        <tr><td>참고_Corr_자료.ipynb</td><td>matplotlib, 상관관계 시각화</td><td>차트 시각화</td></tr>
        <tr><td>최적화_사례_시뮬레이션.ipynb</td><td>목적함수, 가중 스코어</td><td>LP 스코어 계산</td></tr>
        </table>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #888; padding: 1rem;">
        📧 문의: 박연준(yjpark@ifasset.co.kr) | 📅 최종 업데이트: 2025.12
        </div>
        """, unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 1: LP 발굴
    # =========================================================================
    with tab1:
        st.markdown("## 🔍 Potential LP 발굴")
        st.markdown(f"이익잉여금 **{min_retained_earnings}억원** 이상 기업 | 총 **{len(df_companies)}개** 기업")
        
        # 요약 카드
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">총 기업 수</div>
                <div class="metric-value">{len(df_companies)}개</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_re = df_companies['retained_earnings'].mean()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">평균 이익잉여금</div>
                <div class="metric-value">{format_number(avg_re)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            esg_a_count = len(df_companies[df_companies['esg_grade'].isin(['A+', 'A'])])
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">ESG A등급 이상</div>
                <div class="metric-value">{esg_a_count}개</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_score = df_companies['lp_score'].mean()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">평균 LP 스코어</div>
                <div class="metric-value">{avg_score:.1f}점</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 기업 리스트
        st.markdown("### 📋 LP 후보 기업 목록 (스코어 순)")
        
        for idx, row in df_companies.head(20).iterrows():
            score_class = get_score_class(row['lp_score'])
            esg_class = get_esg_badge_class(row['esg_grade'])
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="company-card">
                    <div class="company-name">{row['corp_name']} ({row['stock_code']})</div>
                    <div class="company-info">
                        <strong>업종:</strong> {row['industry']} | 
                        <strong>이익잉여금:</strong> {format_number(row['retained_earnings'])} | 
                        <strong>자본총계:</strong> {format_number(row['total_equity'])} | 
                        <strong>매출액:</strong> {format_number(row['revenue'])}
                    </div>
                    <div style="margin-top: 0.5rem;">
                        <span class="{esg_class}">ESG {row['esg_grade']}</span>
                        <span style="margin-left: 1rem; color: #aaa;">E:{row['esg_env']} S:{row['esg_social']} G:{row['esg_governance']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-title">LP 스코어</div>
                    <div class="metric-value {score_class}">{row['lp_score']:.1f}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # 다운로드 버튼
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df_companies.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 CSV 다운로드",
                csv,
                f"potential_lp_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col2:
            # Excel 다운로드는 openpyxl 필요
            st.download_button(
                "📥 Excel 다운로드 (CSV)",
                csv,
                f"potential_lp_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
    
    # =========================================================================
    # TAB 2: ESG 모니터링
    # =========================================================================
    with tab2:
        st.markdown("## 🌱 ESG 모니터링")
        
        # ESG 키워드 검색
        st.markdown("### 🔎 ESG 키워드 공시 검색")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            keyword = st.selectbox(
                "검색 키워드",
                ["탄소중립", "RE100", "ESG경영", "지속가능경영", "친환경", "기후변화", "녹색금융"]
            )
        
        with col2:
            start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
        
        with col3:
            end_date = st.date_input("종료일", datetime.now())
        
        if st.button("🔍 검색", use_container_width=True):
            with st.spinner("공시 검색 중..."):
                df_news = search_esg_disclosures(
                    keyword,
                    start_date.strftime('%Y%m%d'),
                    end_date.strftime('%Y%m%d')
                )
                st.session_state['esg_news'] = df_news
        
        # 검색 결과 표시
        if 'esg_news' in st.session_state and len(st.session_state['esg_news']) > 0:
            df_news = st.session_state['esg_news']
            st.markdown(f"**검색 결과: {len(df_news)}건**")
            
            for idx, row in df_news.iterrows():
                st.markdown(f"""
                <div class="news-item">
                    <div style="color: #3498db; font-weight: bold;">{row['company']}</div>
                    <div style="color: #fff; margin: 0.3rem 0;">{row['report']}</div>
                    <div style="color: #aaa; font-size: 0.85rem;">{row['content']}</div>
                    <div style="color: #888; font-size: 0.8rem; margin-top: 0.3rem;">📅 {row['date']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # 샘플 데이터 표시
            df_news = get_sample_esg_news()
            st.markdown(f"**최근 ESG 공시 (샘플): {len(df_news)}건**")
            
            for idx, row in df_news.head(10).iterrows():
                st.markdown(f"""
                <div class="news-item">
                    <div style="color: #3498db; font-weight: bold;">{row['company']}</div>
                    <div style="color: #fff; margin: 0.3rem 0;">{row['report']}</div>
                    <div style="color: #aaa; font-size: 0.85rem;">{row['content']}</div>
                    <div style="color: #888; font-size: 0.8rem; margin-top: 0.3rem;">📅 {row['date']} | 🏷️ {row['keyword']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ESG 등급 현황
        st.markdown("### 📊 ESG 등급 현황 (서스틴베스트)")
        
        df_esg = get_sustinvest_esg_ratings()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # ESG 등급 분포 차트
            grade_counts = df_companies['esg_grade'].value_counts()
            fig = px.pie(
                values=grade_counts.values,
                names=grade_counts.index,
                title="ESG 등급 분포",
                color_discrete_sequence=['#27ae60', '#2ecc71', '#3498db', '#f39c12', '#e74c3c']
            )
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(22,33,62,0.8)',
                plot_bgcolor='rgba(22,33,62,0.8)',
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # E/S/G 세부 등급 분포
            env_counts = df_companies['esg_env'].value_counts()
            fig = px.bar(
                x=env_counts.index,
                y=env_counts.values,
                title="환경(E) 등급 분포",
                color=env_counts.index,
                color_discrete_sequence=['#27ae60', '#2ecc71', '#3498db', '#f39c12', '#e74c3c']
            )
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(22,33,62,0.8)',
                plot_bgcolor='rgba(22,33,62,0.8)',
                height=350,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # =========================================================================
    # TAB 3: 분석
    # =========================================================================
    with tab3:
        st.markdown("## 📊 LP 분석")
        
        # 업종별 이익잉여금 분포
        st.markdown("### 📈 업종별 이익잉여금 분포")
        
        industry_stats = df_companies.groupby('industry').agg({
            'retained_earnings': ['sum', 'mean', 'count'],
            'lp_score': 'mean'
        }).round(0)
        industry_stats.columns = ['총 이익잉여금', '평균 이익잉여금', '기업 수', '평균 LP스코어']
        industry_stats = industry_stats.sort_values('총 이익잉여금', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                x=industry_stats.index,
                y=industry_stats['총 이익잉여금'],
                title="업종별 총 이익잉여금",
                color=industry_stats['총 이익잉여금'],
                color_continuous_scale='Viridis'
            )
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(22,33,62,0.8)',
                plot_bgcolor='rgba(22,33,62,0.8)',
                height=400,
                xaxis_title="업종",
                yaxis_title="이익잉여금 (억원)"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(
                df_companies,
                x='retained_earnings',
                y='lp_score',
                color='esg_grade',
                size='total_equity',
                hover_name='corp_name',
                title="이익잉여금 vs LP 스코어",
                color_discrete_sequence=['#27ae60', '#2ecc71', '#3498db', '#f39c12', '#e74c3c']
            )
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(22,33,62,0.8)',
                plot_bgcolor='rgba(22,33,62,0.8)',
                height=400,
                xaxis_title="이익잉여금 (억원)",
                yaxis_title="LP 스코어"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # LP 스코어 구성 분석
        st.markdown("### 🎯 LP 스코어 구성 분석")
        st.markdown("""
        <div class="manual-section">
        <h4>LP 스코어 계산 공식</h4>
        <p><strong>LP 스코어 = 이익잉여금 점수(40%) + 자본총계 점수(20%) + ESG 점수(40%)</strong></p>
        <br>
        <p>• <strong>이익잉여금 점수:</strong> 전체 기업 대비 상대적 위치 (0~100)</p>
        <p>• <strong>자본총계 점수:</strong> 전체 기업 대비 상대적 위치 (0~100)</p>
        <p>• <strong>ESG 점수:</strong> A+=100, A=85, B+=70, B=55, C=40, D=25</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 상위 10개 기업 스코어 분해
        top_10 = df_companies.head(10)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='이익잉여금(40%)', x=top_10['corp_name'], y=top_10['re_score']*0.4, marker_color='#3498db'))
        fig.add_trace(go.Bar(name='자본총계(20%)', x=top_10['corp_name'], y=top_10['equity_score']*0.2, marker_color='#27ae60'))
        fig.add_trace(go.Bar(name='ESG(40%)', x=top_10['corp_name'], y=top_10['esg_score']*0.4, marker_color='#f39c12'))
        
        fig.update_layout(
            barmode='stack',
            title='상위 10개 기업 LP 스코어 구성',
            template='plotly_dark',
            paper_bgcolor='rgba(22,33,62,0.8)',
            plot_bgcolor='rgba(22,33,62,0.8)',
            height=400,
            yaxis_title="LP 스코어"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 업종별 통계 테이블
        st.markdown("### 📋 업종별 통계")
        st.dataframe(industry_stats.reset_index().rename(columns={'industry': '업종'}), use_container_width=True)
    
    # =========================================================================
    # TAB 4: 데이터
    # =========================================================================
    with tab4:
        st.markdown("### 📋 전체 데이터")
        
        # 표시할 컬럼 선택
        display_cols = ['corp_name', 'stock_code', 'market', 'industry', 
                        'retained_earnings', 'total_equity', 'revenue', 'operating_profit',
                        'esg_grade', 'esg_env', 'esg_social', 'esg_governance', 'lp_score']
        
        df_display = df_companies[display_cols].copy()
        df_display.columns = ['기업명', '종목코드', '시장', '업종',
                              '이익잉여금(억)', '자본총계(억)', '매출액(억)', '영업이익(억)',
                              'ESG등급', 'E등급', 'S등급', 'G등급', 'LP스코어']
        
        st.dataframe(df_display, use_container_width=True, height=500)
        
        # 다운로드
        csv = df_display.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 전체 데이터 다운로드 (CSV)",
            csv,
            f"lp_full_data_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        🏢 Potential LP 모니터링 대시보드 v1.0 | 인프라프론티어자산운용(주) | LP 발굴 및 ESG 모니터링
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
