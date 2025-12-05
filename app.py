"""
LP Dashboard v2.2 - Potential LP 모니터링 대시보드
인프라프론티어자산운용(주)

v2.2 개선사항:
- IPO 캘린더 탭 추가 (수요예측, 청약일정, 상장일정)
- 파일 기반 저장 방식 (CSV로 중간 저장)
- 38커뮤니케이션 / ipostock.co.kr 데이터 스크래핑
- IPO 펀드 운용자를 위한 기능 강화
"""

import streamlit as st

# =============================================================================
# 페이지 설정
# =============================================================================
st.set_page_config(
    page_title="🏢 LP & IPO 모니터링 대시보드",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import zipfile
import io
import xml.etree.ElementTree as ET
import time
import re
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 설정
# =============================================================================
DART_API_KEY = "d69ac794205d2dce718abfd6a27e4e4e295accae"
BASE_URL = 'https://opendart.fss.or.kr/api'

# =============================================================================
# CSS 스타일
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    
    .stApp { font-family: 'Noto Sans KR', sans-serif; }
    
    .main-header {
        background: linear-gradient(90deg, #0f3460 0%, #1a1a2e 100%);
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border: 1px solid #3498db;
    }
    .main-header h1 { color: #ffffff; font-size: 1.6rem; margin: 0; font-weight: 700; }
    .main-header p { color: #aaaaaa; margin: 0.3rem 0 0 0; font-size: 0.85rem; }
    
    .metric-card {
        background: linear-gradient(145deg, #16213e 0%, #1a1a2e 100%);
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #0f3460;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .metric-card:hover { border-color: #3498db; }
    .metric-title { color: #888888; font-size: 0.75rem; margin-bottom: 0.3rem; }
    .metric-value { color: #ffffff; font-size: 1.2rem; font-weight: 700; }
    .metric-sub { color: #666; font-size: 0.7rem; margin-top: 0.2rem; }
    
    .company-card {
        background: linear-gradient(145deg, #16213e 0%, #1a1a2e 100%);
        border-radius: 10px;
        padding: 0.8rem 1rem;
        border: 1px solid #0f3460;
        margin-bottom: 0.5rem;
    }
    .company-card:hover { border-color: #3498db; }
    .company-name { color: #ffffff; font-size: 0.95rem; font-weight: 700; margin-bottom: 0.2rem; }
    .company-info { color: #aaaaaa; font-size: 0.8rem; line-height: 1.4; }
    
    .ipo-card {
        background: linear-gradient(145deg, #1a2a3a 0%, #16213e 100%);
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #2980b9;
        margin-bottom: 0.8rem;
    }
    .ipo-card:hover { border-color: #3498db; transform: translateY(-2px); transition: all 0.3s; }
    .ipo-name { color: #3498db; font-size: 1rem; font-weight: 700; margin-bottom: 0.3rem; }
    .ipo-detail { color: #bbb; font-size: 0.85rem; line-height: 1.5; }
    .ipo-date { color: #f39c12; font-weight: 600; }
    .ipo-price { color: #27ae60; font-weight: 600; }
    
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .badge-forecast { background: #9b59b6; color: white; }
    .badge-subscription { background: #e74c3c; color: white; }
    .badge-listing { background: #27ae60; color: white; }
    .badge-ir { background: #f39c12; color: white; }
    
    .info-box {
        background: rgba(52, 152, 219, 0.1);
        border-left: 4px solid #3498db;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        color: #87ceeb;
    }
    
    .warning-box {
        background: rgba(241, 196, 15, 0.1);
        border-left: 4px solid #f1c40f;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
        color: #f9e79f;
    }
    
    .calendar-day {
        background: #1a1a2e;
        border: 1px solid #2c3e50;
        border-radius: 8px;
        padding: 0.5rem;
        min-height: 80px;
        margin: 2px;
    }
    .calendar-day:hover { border-color: #3498db; }
    .calendar-date { color: #888; font-size: 0.8rem; margin-bottom: 0.3rem; }
    .calendar-event { 
        font-size: 0.7rem; 
        padding: 0.2rem 0.4rem; 
        border-radius: 4px; 
        margin: 2px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# IPO 데이터 스크래핑 함수
# =============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ipo_calendar_from_ipostock(year=2025, month=12):
    """IPOStock에서 IPO 캘린더 데이터 스크래핑"""
    try:
        url = f'http://www.ipostock.co.kr/sub03/ipo06.asp?thisYear={year}&thisMonth={month}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'euc-kr'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        events = []
        # 캘린더 테이블에서 이벤트 추출
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '')
            if '/view_pg/view_04.asp' in href:
                title = link.get('title', link.text.strip())
                # 날짜는 부모 요소에서 추출 시도
                parent = link.find_parent('td')
                if parent:
                    # 이벤트 유형 추정 (색상 또는 위치 기반)
                    events.append({
                        'company': title,
                        'link': f"http://www.ipostock.co.kr{href}" if href.startswith('/') else href
                    })
        
        return events
    except Exception as e:
        return []

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_ipo_schedule_38():
    """38커뮤니케이션에서 IPO 일정 스크래핑"""
    try:
        schedules = {
            'subscription': [],  # 청약일정
            'listing': [],      # 상장일정
            'forecast': [],     # 수요예측
            'approval': []      # 승인종목
        }
        
        # 공모주 청약일정
        url = 'http://www.38.co.kr/html/fund/index.htm?o=k'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 테이블 파싱
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 5:
                    try:
                        company_cell = cells[0]
                        company_link = company_cell.find('a')
                        if company_link:
                            company = company_link.text.strip()
                            # 날짜와 가격 정보 추출
                            date_text = cells[1].text.strip() if len(cells) > 1 else ''
                            price_text = cells[2].text.strip() if len(cells) > 2 else ''
                            
                            if company and '스팩' not in company:  # SPAC 제외 옵션
                                schedules['subscription'].append({
                                    'company': company,
                                    'date': date_text,
                                    'price': price_text,
                                    'type': '청약'
                                })
                    except:
                        continue
        
        # 신규상장 일정
        url2 = 'http://www.38.co.kr/html/fund/index.htm?o=nw'
        response2 = requests.get(url2, headers=headers, timeout=15)
        response2.encoding = 'euc-kr'
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        
        tables2 = soup2.find_all('table')
        for table in tables2:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    try:
                        company_cell = cells[0]
                        company_link = company_cell.find('a')
                        if company_link:
                            company = company_link.text.strip()
                            date_text = cells[1].text.strip() if len(cells) > 1 else ''
                            
                            if company:
                                schedules['listing'].append({
                                    'company': company,
                                    'date': date_text,
                                    'type': '상장'
                                })
                    except:
                        continue
        
        # 수요예측 일정
        url3 = 'http://www.38.co.kr/html/fund/index.htm?o=r'
        response3 = requests.get(url3, headers=headers, timeout=15)
        response3.encoding = 'euc-kr'
        soup3 = BeautifulSoup(response3.text, 'html.parser')
        
        tables3 = soup3.find_all('table')
        for table in tables3:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    try:
                        company_cell = cells[0]
                        company_link = company_cell.find('a')
                        if company_link:
                            company = company_link.text.strip()
                            date_text = cells[1].text.strip() if len(cells) > 1 else ''
                            
                            if company:
                                schedules['forecast'].append({
                                    'company': company,
                                    'date': date_text,
                                    'type': '수요예측'
                                })
                    except:
                        continue
        
        return schedules
    except Exception as e:
        return {'subscription': [], 'listing': [], 'forecast': [], 'approval': []}

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_approved_companies():
    """승인 종목 리스트 가져오기"""
    try:
        url = 'http://www.38.co.kr/html/ipo/ipo.htm?key=1'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        companies = []
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 8:
                    try:
                        date_text = cells[0].text.strip()
                        company_link = cells[1].find('a')
                        if company_link and date_text:
                            company = company_link.text.strip()
                            request_date = cells[2].text.strip()
                            capital = cells[3].text.strip()
                            revenue = cells[4].text.strip()
                            profit = cells[5].text.strip()
                            underwriter = cells[6].text.strip()
                            industry = cells[7].text.strip()
                            
                            companies.append({
                                'approval_date': date_text,
                                'company': company,
                                'request_date': request_date,
                                'capital': capital,
                                'revenue': revenue,
                                'profit': profit,
                                'underwriter': underwriter,
                                'industry': industry
                            })
                    except:
                        continue
        
        return companies
    except Exception as e:
        return []

# =============================================================================
# DART API 함수들
# =============================================================================
@st.cache_data(ttl=86400, show_spinner=False)
def get_corp_code_list():
    """상장기업 코드 목록"""
    try:
        url = f'{BASE_URL}/corpCode.xml'
        params = {'crtfc_key': DART_API_KEY}
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                xml_data = z.read('CORPCODE.xml')
            
            root = ET.fromstring(xml_data)
            corp_list = []
            
            for corp in root.findall('list'):
                corp_code = corp.find('corp_code').text
                corp_name = corp.find('corp_name').text
                stock_code_elem = corp.find('stock_code')
                stock_code = stock_code_elem.text if stock_code_elem is not None else None
                
                if stock_code and stock_code.strip():
                    corp_list.append({
                        'corp_code': corp_code,
                        'corp_name': corp_name,
                        'stock_code': stock_code.strip()
                    })
            
            return pd.DataFrame(corp_list)
        return None
    except Exception as e:
        return None

def get_financial_statement(corp_code, bsns_year, reprt_code='11011'):
    """재무제표 조회"""
    try:
        url = f'{BASE_URL}/fnlttSinglAcntAll.json'
        params = {
            'crtfc_key': DART_API_KEY,
            'corp_code': corp_code,
            'bsns_year': bsns_year,
            'reprt_code': reprt_code,
            'fs_div': 'CFS'
        }
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '000':
                return pd.DataFrame(data.get('list', []))
        return None
    except:
        return None

def extract_financial_data(df):
    """재무데이터 추출"""
    result = {'retained_earnings': None, 'total_equity': None, 'revenue': None}
    
    if df is None or df.empty:
        return result
    
    # 이익잉여금
    for kw in ['이익잉여금', '이익(손실)잉여금']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['retained_earnings'] = float(val) / 100000000 if val else None
                break
            except:
                pass
    
    # 자본총계
    for kw in ['자본총계', '자본 총계']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['total_equity'] = float(val) / 100000000 if val else None
                break
            except:
                pass
    
    # 매출액
    for kw in ['매출액', '수익(매출액)', '영업수익']:
        match = df[df['account_nm'].str.contains(kw, na=False)]
        if not match.empty:
            try:
                val = match.iloc[0]['thstrm_amount']
                if isinstance(val, str):
                    val = val.replace(',', '')
                result['revenue'] = float(val) / 100000000 if val else None
                break
            except:
                pass
    
    return result

def fetch_single_company(corp_code, corp_name, stock_code, bsns_year):
    """단일 기업 조회"""
    fs_df = get_financial_statement(corp_code, bsns_year)
    fin_data = extract_financial_data(fs_df)
    
    if fin_data['retained_earnings'] is not None:
        return {
            'corp_code': corp_code,
            'corp_name': corp_name,
            'stock_code': stock_code,
            **fin_data
        }
    return None

def calculate_lp_score(df):
    """LP 스코어 계산"""
    df = df.copy()
    if len(df) == 0:
        return df
    
    # 이익잉여금 스코어
    if df['retained_earnings'].max() > df['retained_earnings'].min():
        df['re_score'] = (df['retained_earnings'] - df['retained_earnings'].min()) / \
                         (df['retained_earnings'].max() - df['retained_earnings'].min()) * 100
    else:
        df['re_score'] = 50
    
    # 자본총계 스코어
    df['total_equity'] = df['total_equity'].fillna(0)
    if df['total_equity'].max() > df['total_equity'].min():
        df['equity_score'] = (df['total_equity'] - df['total_equity'].min()) / \
                             (df['total_equity'].max() - df['total_equity'].min()) * 100
    else:
        df['equity_score'] = 50
    
    df['lp_score'] = df['re_score'] * 0.7 + df['equity_score'] * 0.3
    return df.sort_values('lp_score', ascending=False)

def format_number(value, unit='억원'):
    """숫자 포맷팅"""
    if pd.isna(value) or value is None:
        return 'N/A'
    if abs(value) >= 10000:
        return f"{value/10000:,.1f}조원"
    return f"{value:,.0f}{unit}"

# =============================================================================
# ESG 검색
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def search_esg_disclosures(keyword, start_date, end_date, max_results=30):
    """ESG 키워드 검색"""
    try:
        url = 'https://dart.fss.or.kr/dsab007/search.ax'
        results = []
        
        response = requests.post(url, data={
            "currentPage": "1",
            "keyword": keyword,
            "dspType": "A",
            "maxResults": "50",
            "startDate": start_date,
            "endDate": end_date
        }, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for row in soup.find_all('tr'):
                try:
                    company_tag = row.find('a', class_='company')
                    if company_tag:
                        results.append({
                            'company': company_tag.text.strip(),
                            'report': row.find('a', class_='second').text.strip() if row.find('a', class_='second') else '',
                            'date': row.find('td', class_='date').text.strip() if row.find('td', class_='date') else '',
                            'keyword': keyword
                        })
                except:
                    continue
        
        return pd.DataFrame(results[:max_results]) if results else pd.DataFrame()
    except:
        return pd.DataFrame()

# =============================================================================
# 메인 앱
# =============================================================================
def main():
    # 세션 상태 초기화
    if 'corp_list' not in st.session_state:
        st.session_state.corp_list = None
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = pd.DataFrame()
    if 'current_idx' not in st.session_state:
        st.session_state.current_idx = 0
    
    # 사이드바
    with st.sidebar:
        st.markdown("## ⚙️ 설정")
        
        st.markdown("### 📊 LP 조회")
        bsns_year = st.selectbox("사업연도", ['2024', '2023', '2022'], index=0)
        min_re = st.number_input("최소 이익잉여금 (억원)", 0, 10000, 300, 100)
        batch_size = st.selectbox("배치 크기", [30, 50, 100], index=1)
        
        st.markdown("### 📅 IPO 캘린더")
        ipo_year = st.selectbox("연도", [2025, 2024], index=0)
        ipo_month = st.selectbox("월", list(range(1, 13)), index=datetime.now().month - 1)
        
        st.markdown("---")
        
        if st.button("🔄 전체 초기화", use_container_width=True):
            st.cache_data.clear()
            st.session_state.corp_list = None
            st.session_state.financial_data = pd.DataFrame()
            st.session_state.current_idx = 0
            st.rerun()
        
        st.markdown(f"""
        ### 📋 현재 상태
        - **LP 후보:** {len(st.session_state.financial_data)}개
        - **버전:** v2.2
        """)
    
    # 메인 헤더
    st.markdown(f"""
    <div class="main-header">
        <h1>🏢 LP & IPO 모니터링 대시보드 v2.2</h1>
        <p>📅 {datetime.now().strftime('%Y년 %m월 %d일')} | 인프라프론티어자산운용(주) | IPO 펀드 + LP 발굴</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 탭
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 IPO 캘린더", "🔍 LP 발굴", "🌱 ESG 모니터링", "📋 데이터"
    ])
    
    # =========================================================================
    # TAB 1: IPO 캘린더
    # =========================================================================
    with tab1:
        st.markdown("## 📅 IPO 일정 캘린더")
        st.caption("38커뮤니케이션 / IPOStock 데이터 기반")
        
        # IPO 데이터 로드
        with st.spinner("IPO 일정 불러오는 중..."):
            ipo_schedules = fetch_ipo_schedule_38()
            approved = fetch_approved_companies()
        
        # 요약 메트릭
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">청약 예정</div>
                <div class="metric-value" style="color:#e74c3c">{len(ipo_schedules['subscription'])}건</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">상장 예정</div>
                <div class="metric-value" style="color:#27ae60">{len(ipo_schedules['listing'])}건</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">수요예측</div>
                <div class="metric-value" style="color:#9b59b6">{len(ipo_schedules['forecast'])}건</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">승인 종목</div>
                <div class="metric-value" style="color:#f39c12">{len(approved)}건</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 탭 내 서브탭
        sub1, sub2, sub3, sub4 = st.tabs([
            "📝 청약 일정", "📈 상장 일정", "🎯 수요예측", "✅ 승인 종목"
        ])
        
        with sub1:
            st.markdown("### 📝 공모주 청약 일정")
            
            if ipo_schedules['subscription']:
                for item in ipo_schedules['subscription'][:20]:
                    st.markdown(f"""
                    <div class="ipo-card">
                        <div class="ipo-name">
                            <span class="status-badge badge-subscription">청약</span> {item['company']}
                        </div>
                        <div class="ipo-detail">
                            📅 청약일: <span class="ipo-date">{item.get('date', '-')}</span> | 
                            💰 공모가: <span class="ipo-price">{item.get('price', '-')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("현재 예정된 청약 일정이 없습니다.")
        
        with sub2:
            st.markdown("### 📈 신규 상장 일정")
            
            if ipo_schedules['listing']:
                for item in ipo_schedules['listing'][:20]:
                    st.markdown(f"""
                    <div class="ipo-card">
                        <div class="ipo-name">
                            <span class="status-badge badge-listing">상장</span> {item['company']}
                        </div>
                        <div class="ipo-detail">
                            📅 상장일: <span class="ipo-date">{item.get('date', '-')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("현재 예정된 상장 일정이 없습니다.")
        
        with sub3:
            st.markdown("### 🎯 수요예측 일정")
            st.caption("기관투자자 대상 수요예측 - IPO 펀드 투자 검토 시점")
            
            if ipo_schedules['forecast']:
                for item in ipo_schedules['forecast'][:20]:
                    st.markdown(f"""
                    <div class="ipo-card">
                        <div class="ipo-name">
                            <span class="status-badge badge-forecast">수요예측</span> {item['company']}
                        </div>
                        <div class="ipo-detail">
                            📅 수요예측일: <span class="ipo-date">{item.get('date', '-')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("현재 예정된 수요예측 일정이 없습니다.")
        
        with sub4:
            st.markdown("### ✅ 상장 승인 종목")
            st.caption("상장예비심사 승인 완료 - 향후 IPO 진행 예정")
            
            if approved:
                # 테이블 형태로 표시
                df_approved = pd.DataFrame(approved[:30])
                if not df_approved.empty:
                    st.dataframe(
                        df_approved.rename(columns={
                            'approval_date': '승인일',
                            'company': '기업명',
                            'request_date': '청구일',
                            'capital': '자본금(백만)',
                            'revenue': '매출액(백만)',
                            'profit': '당기순이익(백만)',
                            'underwriter': '주간사',
                            'industry': '업종'
                        }),
                        use_container_width=True,
                        height=400
                    )
            else:
                st.info("승인 종목 정보를 불러올 수 없습니다.")
        
        # IPO 펀드 운용자 팁
        st.markdown("---")
        st.markdown("""
        <div class="info-box">
            <strong>💡 IPO 펀드 운용 가이드</strong><br>
            • <strong>수요예측 2주 전:</strong> IR 자료 검토, 밸류에이션 분석 시작<br>
            • <strong>수요예측 기간:</strong> 기관투자자 참여 결정, 희망가격 제출<br>
            • <strong>청약일:</strong> 일반 청약 진행 (균등/비례 배정)<br>
            • <strong>상장일:</strong> 시초가 형성, 단기 트레이딩 또는 장기 보유 결정
        </div>
        """, unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 2: LP 발굴
    # =========================================================================
    with tab2:
        st.markdown("## 🔍 Potential LP 발굴")
        
        # 기업 목록 로드
        if st.session_state.corp_list is None:
            st.markdown("""
            <div class="info-box">
                <strong>💡 사용 방법</strong><br>
                1. "기업 목록 불러오기" 클릭<br>
                2. "다음 배치 조회" 버튼으로 50개씩 조회<br>
                3. 원하는 만큼 데이터 수집 후 CSV 다운로드
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📥 기업 목록 불러오기", type="primary", use_container_width=True):
                with st.spinner("상장기업 목록 다운로드 중..."):
                    corp_df = get_corp_code_list()
                
                if corp_df is not None:
                    st.session_state.corp_list = corp_df
                    st.success(f"✅ {len(corp_df)}개 상장기업 로드!")
                    st.rerun()
        
        else:
            corp_df = st.session_state.corp_list
            total = len(corp_df)
            current_idx = st.session_state.current_idx
            
            # 진행 상태
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">조회 진행</div>
                    <div class="metric-value">{current_idx}/{total}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">LP 후보</div>
                    <div class="metric-value">{len(st.session_state.financial_data)}개</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                pct = current_idx / total * 100 if total > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">진행률</div>
                    <div class="metric-value">{pct:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.progress(current_idx / total if total > 0 else 0)
            
            # 배치 조회
            if current_idx < total:
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button(f"⏭️ 다음 {batch_size}개 조회", type="primary", use_container_width=True):
                        end_idx = min(current_idx + batch_size, total)
                        batch = corp_df.iloc[current_idx:end_idx]
                        
                        progress = st.progress(0)
                        results = []
                        
                        for i, row in enumerate(batch.itertuples()):
                            progress.progress((i + 1) / len(batch), f"{row.corp_name} 조회 중...")
                            result = fetch_single_company(row.corp_code, row.corp_name, row.stock_code, bsns_year)
                            if result:
                                results.append(result)
                            time.sleep(0.2)
                        
                        if results:
                            new_df = pd.DataFrame(results)
                            if st.session_state.financial_data.empty:
                                st.session_state.financial_data = new_df
                            else:
                                st.session_state.financial_data = pd.concat([
                                    st.session_state.financial_data, new_df
                                ], ignore_index=True)
                        
                        st.session_state.current_idx = end_idx
                        st.rerun()
                
                with col_btn2:
                    if st.button("⏩ 3배치 연속 (150개)", use_container_width=True):
                        for _ in range(3):
                            if st.session_state.current_idx >= total:
                                break
                            
                            end_idx = min(st.session_state.current_idx + batch_size, total)
                            batch = corp_df.iloc[st.session_state.current_idx:end_idx]
                            
                            results = []
                            for row in batch.itertuples():
                                result = fetch_single_company(row.corp_code, row.corp_name, row.stock_code, bsns_year)
                                if result:
                                    results.append(result)
                                time.sleep(0.2)
                            
                            if results:
                                new_df = pd.DataFrame(results)
                                if st.session_state.financial_data.empty:
                                    st.session_state.financial_data = new_df
                                else:
                                    st.session_state.financial_data = pd.concat([
                                        st.session_state.financial_data, new_df
                                    ], ignore_index=True)
                            
                            st.session_state.current_idx = end_idx
                        
                        st.rerun()
            else:
                st.success("🎉 모든 기업 조회 완료!")
            
            st.markdown("---")
            
            # 결과 표시
            if not st.session_state.financial_data.empty:
                df = st.session_state.financial_data.copy()
                df_filtered = df[df['retained_earnings'] >= min_re].copy()
                
                if len(df_filtered) > 0:
                    df_filtered = calculate_lp_score(df_filtered)
                
                st.markdown(f"### 📋 LP 후보 ({min_re}억원 이상): {len(df_filtered)}개")
                
                if len(df_filtered) > 0:
                    for _, row in df_filtered.head(25).iterrows():
                        st.markdown(f"""
                        <div class="company-card">
                            <div class="company-name">{row['corp_name']} ({row['stock_code']})</div>
                            <div class="company-info">
                                이익잉여금: <strong>{format_number(row['retained_earnings'])}</strong> | 
                                자본총계: {format_number(row.get('total_equity'))} | 
                                스코어: <strong>{row.get('lp_score', 0):.1f}</strong>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        "📥 LP 후보 CSV 다운로드",
                        csv,
                        f"potential_lp_{bsns_year}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
    
    # =========================================================================
    # TAB 3: ESG 모니터링
    # =========================================================================
    with tab3:
        st.markdown("## 🌱 ESG 공시 검색")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            keyword = st.selectbox("키워드", ["탄소중립", "RE100", "ESG경영", "지속가능경영", "친환경"])
        with col2:
            start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
        with col3:
            end_date = st.date_input("종료일", datetime.now())
        
        if st.button("🔍 검색", use_container_width=True):
            with st.spinner("검색 중..."):
                df_esg = search_esg_disclosures(keyword, start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
            
            if not df_esg.empty:
                st.success(f"✅ {len(df_esg)}건")
                for _, row in df_esg.iterrows():
                    st.markdown(f"""
                    <div class="company-card">
                        <div class="company-name">{row['company']}</div>
                        <div class="company-info">{row['report']} | 📅 {row['date']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("검색 결과가 없습니다.")
    
    # =========================================================================
    # TAB 4: 데이터
    # =========================================================================
    with tab4:
        st.markdown("## 📋 전체 데이터")
        
        if not st.session_state.financial_data.empty:
            df = st.session_state.financial_data.sort_values('retained_earnings', ascending=False)
            st.dataframe(df.rename(columns={
                'corp_name': '기업명', 'stock_code': '종목코드',
                'retained_earnings': '이익잉여금(억)', 'total_equity': '자본총계(억)', 'revenue': '매출액(억)'
            }), use_container_width=True, height=500)
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("📥 전체 다운로드", csv, f"all_data_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.info("LP 발굴 탭에서 조회를 시작하세요.")
    
    # 푸터
    st.markdown("---")
    st.markdown('<div style="text-align:center;color:#666;padding:0.5rem;">🏢 LP & IPO 모니터링 대시보드 v2.2 | 인프라프론티어자산운용(주)</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
