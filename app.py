# =============================================================================
# lp_dashboard.py - Potential LP 모니터링 대시보드 v2.0
# 인프라프론티어자산운용(주) - LP 발굴 및 ESG 모니터링
# 실제 DART API 호출 버전
# =============================================================================

import streamlit as st

# =============================================================================
# 페이지 설정 (반드시 첫 번째 Streamlit 명령어여야 함!)
# =============================================================================
st.set_page_config(
    page_title="🏢 Potential LP 모니터링 대시보드",
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
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# DART API 설정
# =============================================================================
DART_API_KEY = "d69ac794205d2dce718abfd6a27e4e4e295accae"
BASE_URL = 'https://opendart.fss.or.kr/api'

# =============================================================================
# CSS 스타일
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
    
    .progress-box {
        background: rgba(52, 152, 219, 0.2);
        border: 1px solid #3498db;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DART API 함수들 (실제 API 호출)
# =============================================================================
@st.cache_data(ttl=86400, show_spinner=False)  # 24시간 캐싱
def get_corp_code_list():
    """
    DART에 등록된 전체 기업 코드 리스트 다운로드
    📌 활용 기법: 업로드된 DART 코드의 get_corp_code_list() 함수
    """
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
                
                # 상장사만 필터링 (stock_code가 있는 경우)
                if stock_code and stock_code.strip():
                    corp_list.append({
                        'corp_code': corp_code,
                        'corp_name': corp_name,
                        'stock_code': stock_code.strip()
                    })
            
            return pd.DataFrame(corp_list)
        else:
            return None
    except Exception as e:
        st.error(f"기업 목록 다운로드 실패: {str(e)}")
        return None

def get_financial_statement(corp_code, bsns_year, reprt_code='11011'):
    """
    재무제표 조회
    📌 활용 기법: 업로드된 DART 코드의 get_financial_statement() 함수
    
    reprt_code: 11011(사업보고서), 11012(반기보고서), 11013(1분기보고서), 11014(3분기보고서)
    """
    try:
        url = f'{BASE_URL}/fnlttSinglAcntAll.json'
        params = {
            'crtfc_key': DART_API_KEY,
            'corp_code': corp_code,
            'bsns_year': bsns_year,
            'reprt_code': reprt_code,
            'fs_div': 'CFS'  # CFS: 연결재무제표, OFS: 개별재무제표
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '000':
                return pd.DataFrame(data.get('list', []))
        return None
    except:
        return None

def extract_retained_earnings(df):
    """
    재무제표에서 이익잉여금 추출
    📌 활용 기법: 업로드된 DART 코드의 extract_retained_earnings() 함수
    """
    if df is None or df.empty:
        return None
    
    # 이익잉여금 관련 계정과목 찾기
    keywords = ['이익잉여금', '이익(손실)잉여금', '이익잉여금(결손금)']
    
    for keyword in keywords:
        retained_earnings_df = df[df['account_nm'].str.contains(keyword, na=False)]
        
        if not retained_earnings_df.empty:
            try:
                value = retained_earnings_df.iloc[0]['thstrm_amount']
                if isinstance(value, str):
                    value = value.replace(',', '')
                return float(value) if value else None
            except:
                return None
    
    return None

def extract_total_equity(df):
    """재무제표에서 자본총계 추출"""
    if df is None or df.empty:
        return None
    
    keywords = ['자본총계', '자본 총계', '자본합계']
    
    for keyword in keywords:
        equity_df = df[df['account_nm'].str.contains(keyword, na=False)]
        
        if not equity_df.empty:
            try:
                value = equity_df.iloc[0]['thstrm_amount']
                if isinstance(value, str):
                    value = value.replace(',', '')
                return float(value) if value else None
            except:
                return None
    
    return None

def extract_revenue(df):
    """재무제표에서 매출액 추출"""
    if df is None or df.empty:
        return None
    
    keywords = ['매출액', '수익(매출액)', '영업수익']
    
    for keyword in keywords:
        revenue_df = df[df['account_nm'].str.contains(keyword, na=False)]
        
        if not revenue_df.empty:
            try:
                value = revenue_df.iloc[0]['thstrm_amount']
                if isinstance(value, str):
                    value = value.replace(',', '')
                return float(value) if value else None
            except:
                return None
    
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_retained_earnings(corp_df, bsns_year='2023', _progress_callback=None):
    """
    모든 기업의 이익잉여금 조회
    📌 progress 콜백은 캐시 해시에서 제외 (_로 시작)
    """
    results = []
    total = len(corp_df)
    
    for idx, row in corp_df.iterrows():
        corp_code = row['corp_code']
        corp_name = row['corp_name']
        stock_code = row['stock_code']
        
        # API 호출 제한 고려 (초당 1회)
        time.sleep(0.5)
        
        # 진행률 업데이트
        if _progress_callback:
            _progress_callback(idx + 1, total, corp_name)
        
        # 재무제표 조회
        fs_df = get_financial_statement(corp_code, bsns_year, '11011')
        
        if fs_df is not None and not fs_df.empty:
            retained_earnings = extract_retained_earnings(fs_df)
            total_equity = extract_total_equity(fs_df)
            revenue = extract_revenue(fs_df)
            
            if retained_earnings is not None:
                results.append({
                    'corp_code': corp_code,
                    'corp_name': corp_name,
                    'stock_code': stock_code,
                    'retained_earnings': retained_earnings / 100000000,  # 억원 변환
                    'total_equity': total_equity / 100000000 if total_equity else None,
                    'revenue': revenue / 100000000 if revenue else None,
                })
    
    return pd.DataFrame(results)

# =============================================================================
# ESG 공시 검색 함수
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def search_esg_disclosures(keyword, start_date, end_date, max_results=50):
    """
    DART 공시 키워드 검색
    📌 활용 기법: 공시내용_특정Keyword_request방식.ipynb의 requests.post() 방식
    """
    try:
        url = 'https://dart.fss.or.kr/dsab007/search.ax'
        
        results = []
        page = 1
        
        while len(results) < max_results and page <= 5:
            response = requests.post(url, data={
                "currentPage": str(page),
                "keyword": keyword,
                "dspType": "A",
                "maxResults": "50",
                "startDate": start_date,
                "endDate": end_date
            }, timeout=30)
            
            if response.status_code != 200:
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            rows = soup.find_all('tr')
            
            found_in_page = 0
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
                        found_in_page += 1
                except:
                    continue
            
            if found_in_page == 0:
                break
            
            page += 1
            time.sleep(0.3)
        
        return pd.DataFrame(results[:max_results]) if results else pd.DataFrame()
        
    except Exception as e:
        return pd.DataFrame()

# =============================================================================
# LP 스코어링 함수
# =============================================================================
def calculate_lp_score(df):
    """LP 우선순위 스코어 계산"""
    df = df.copy()
    
    # 이익잉여금 점수 (정규화)
    if len(df) > 0 and df['retained_earnings'].max() > df['retained_earnings'].min():
        df['re_score'] = (df['retained_earnings'] - df['retained_earnings'].min()) / \
                         (df['retained_earnings'].max() - df['retained_earnings'].min()) * 100
    else:
        df['re_score'] = 50
    
    # 자본총계 점수
    if 'total_equity' in df.columns:
        df['total_equity'] = df['total_equity'].fillna(0)
        if df['total_equity'].max() > df['total_equity'].min():
            df['equity_score'] = (df['total_equity'] - df['total_equity'].min()) / \
                                 (df['total_equity'].max() - df['total_equity'].min()) * 100
        else:
            df['equity_score'] = 50
    else:
        df['equity_score'] = 50
    
    # 종합 스코어 (이익잉여금 70% + 자본총계 30%)
    df['lp_score'] = df['re_score'] * 0.7 + df['equity_score'] * 0.3
    
    return df.sort_values('lp_score', ascending=False)

# =============================================================================
# 유틸리티 함수
# =============================================================================
def format_number(value, unit='억원'):
    """숫자 포맷팅"""
    if pd.isna(value) or value is None:
        return 'N/A'
    if abs(value) >= 10000:
        return f"{value/10000:,.1f}조원"
    return f"{value:,.0f}{unit}"

# =============================================================================
# 메인 앱
# =============================================================================
def main():
    # 세션 상태 초기화
    if 'corp_list' not in st.session_state:
        st.session_state.corp_list = None
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = None
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # 사이드바
    with st.sidebar:
        st.markdown("## ⚙️ 설정")
        
        st.markdown("### 📊 조회 조건")
        
        bsns_year = st.selectbox(
            "사업연도",
            ['2024', '2023', '2022', '2021'],
            index=1,
            help="2024년 사업보고서는 2025년 3월 이후 공시됨"
        )
        
        min_retained_earnings = st.number_input(
            "최소 이익잉여금 (억원)", 
            min_value=0, 
            max_value=10000, 
            value=300, 
            step=100
        )
        
        st.markdown("---")
        
        # 데이터 로드 버튼
        if st.button("🚀 DART 데이터 조회", use_container_width=True, type="primary"):
            st.session_state.data_loaded = False
            st.session_state.financial_data = None
            st.rerun()
        
        if st.button("🔄 캐시 초기화", use_container_width=True):
            st.cache_data.clear()
            st.session_state.corp_list = None
            st.session_state.financial_data = None
            st.session_state.data_loaded = False
            st.rerun()
        
        st.markdown("---")
        st.markdown(f"""
        ### 📋 정보
        - **DART API:** 연결됨
        - **사업연도:** {bsns_year}
        - **버전:** v2.0
        """)
    
    # 메인 헤더
    today = datetime.now()
    st.markdown(f"""
    <div class="main-header">
        <h1>🏢 Potential LP 모니터링 대시보드 v2.0</h1>
        <p>📅 오늘: {today.strftime('%Y년 %m월 %d일')} | 인프라프론티어자산운용(주) | DART API 실시간 연동</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 탭 구성
    tab0, tab1, tab2, tab3 = st.tabs([
        "📖 사용 메뉴얼", "🔍 LP 발굴", "🌱 ESG 모니터링", "📋 데이터"
    ])
    
    # =========================================================================
    # TAB 0: 사용 메뉴얼
    # =========================================================================
    with tab0:
        st.markdown("## 📖 대시보드 사용 메뉴얼")
        st.markdown("Potential LP(유한책임사원) 발굴을 위한 DART 연동 대시보드입니다.")
        
        st.markdown("---")
        
        st.markdown("### 1️⃣ 사용 방법")
        st.markdown("""
        <div class="manual-section">
        <h4>🚀 데이터 조회 순서</h4>
        <p>1. 사이드바에서 <strong>사업연도</strong> 선택 (2023년 권장)</p>
        <p>2. <strong>최소 이익잉여금</strong> 기준 설정 (기본 300억원)</p>
        <p>3. <strong>🚀 DART 데이터 조회</strong> 버튼 클릭</p>
        <p>4. 조회 완료까지 대기 (약 10~30분 소요)</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="tip-box">
        <strong>💡 참고사항</strong><br>
        • 2024년 사업보고서는 2025년 3월 이후에 공시됩니다<br>
        • 최초 조회 시 시간이 걸리지만, 이후 24시간 동안 캐시됩니다<br>
        • API 호출 제한(초당 1회)으로 인해 전체 조회에 시간이 소요됩니다
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.markdown("### 2️⃣ 활용된 DART API 기법")
        st.markdown("""
        <div class="manual-section">
        <h4>🔧 업로드된 강의 코드 활용</h4>
        <table style="color: #fff; width: 100%;">
        <tr><th style="text-align:left;">함수</th><th style="text-align:left;">출처</th><th style="text-align:left;">기능</th></tr>
        <tr><td>get_corp_code_list()</td><td>DART 코드</td><td>상장사 목록 조회</td></tr>
        <tr><td>get_financial_statement()</td><td>DART 코드</td><td>재무제표 조회</td></tr>
        <tr><td>extract_retained_earnings()</td><td>DART 코드</td><td>이익잉여금 추출</td></tr>
        <tr><td>search_esg_disclosures()</td><td>공시 Keyword</td><td>ESG 공시 검색</td></tr>
        </table>
        </div>
        """, unsafe_allow_html=True)
    
    # =========================================================================
    # TAB 1: LP 발굴
    # =========================================================================
    with tab1:
        st.markdown("## 🔍 Potential LP 발굴")
        
        # 데이터 로드 상태 확인
        if st.session_state.financial_data is None:
            st.info("👈 사이드바에서 **🚀 DART 데이터 조회** 버튼을 클릭하세요.")
            
            # 자동 로드 시작
            if not st.session_state.data_loaded:
                st.markdown("---")
                st.markdown("### 📊 데이터 조회 시작")
                
                # Step 1: 기업 목록 로드
                with st.spinner("1단계: 상장기업 목록 다운로드 중..."):
                    corp_df = get_corp_code_list()
                
                if corp_df is None or corp_df.empty:
                    st.error("기업 목록을 가져올 수 없습니다. API 키를 확인해주세요.")
                    return
                
                st.success(f"✅ 총 {len(corp_df)}개 상장기업 발견")
                st.session_state.corp_list = corp_df
                
                # Step 2: 재무정보 조회
                st.markdown(f"### 2단계: {bsns_year}년 재무정보 조회")
                st.warning(f"⏳ 약 {len(corp_df) // 2}초 소요 예상 (API 호출 제한)")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(current, total, corp_name):
                    progress_bar.progress(current / total)
                    status_text.text(f"진행 중... {current}/{total} ({current/total*100:.1f}%) - {corp_name}")
                
                # 재무정보 조회
                financial_df = fetch_all_retained_earnings(
                    corp_df,
                    bsns_year,
                    _progress_callback=update_progress
                )
                
                progress_bar.progress(1.0)
                status_text.text("완료!")
                
                if financial_df is not None and not financial_df.empty:
                    st.session_state.financial_data = financial_df
                    st.session_state.data_loaded = True
                    st.success(f"✅ {len(financial_df)}개 기업 재무정보 조회 완료!")
                    st.rerun()
                else:
                    st.error("재무정보를 가져올 수 없습니다.")
        
        else:
            # 데이터가 있는 경우 표시
            df = st.session_state.financial_data.copy()
            
            # 이익잉여금 필터링
            df_filtered = df[df['retained_earnings'] >= min_retained_earnings].copy()
            
            # LP 스코어 계산
            if len(df_filtered) > 0:
                df_filtered = calculate_lp_score(df_filtered)
            
            st.markdown(f"이익잉여금 **{min_retained_earnings}억원** 이상 기업 | 총 **{len(df_filtered)}개** 기업")
            
            # 요약 카드
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">총 기업 수</div>
                    <div class="metric-value">{len(df_filtered)}개</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if len(df_filtered) > 0:
                    avg_re = df_filtered['retained_earnings'].mean()
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">평균 이익잉여금</div>
                        <div class="metric-value">{format_number(avg_re)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">평균 이익잉여금</div>
                        <div class="metric-value">N/A</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col3:
                if len(df_filtered) > 0:
                    max_re = df_filtered['retained_earnings'].max()
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">최대 이익잉여금</div>
                        <div class="metric-value">{format_number(max_re)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">최대 이익잉여금</div>
                        <div class="metric-value">N/A</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col4:
                if len(df_filtered) > 0 and 'lp_score' in df_filtered.columns:
                    avg_score = df_filtered['lp_score'].mean()
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">평균 LP 스코어</div>
                        <div class="metric-value">{avg_score:.1f}점</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">평균 LP 스코어</div>
                        <div class="metric-value">N/A</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 기업 리스트 (상위 50개)
            st.markdown("### 📋 LP 후보 기업 목록 (이익잉여금 순)")
            
            if len(df_filtered) > 0:
                for idx, row in df_filtered.head(50).iterrows():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        equity_str = format_number(row.get('total_equity')) if pd.notna(row.get('total_equity')) else 'N/A'
                        revenue_str = format_number(row.get('revenue')) if pd.notna(row.get('revenue')) else 'N/A'
                        
                        st.markdown(f"""
                        <div class="company-card">
                            <div class="company-name">{row['corp_name']} ({row['stock_code']})</div>
                            <div class="company-info">
                                <strong>이익잉여금:</strong> {format_number(row['retained_earnings'])} | 
                                <strong>자본총계:</strong> {equity_str} | 
                                <strong>매출액:</strong> {revenue_str}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if 'lp_score' in row and pd.notna(row['lp_score']):
                            st.markdown(f"""
                            <div class="metric-card" style="text-align: center;">
                                <div class="metric-title">LP 스코어</div>
                                <div class="metric-value">{row['lp_score']:.1f}</div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("조건에 맞는 기업이 없습니다. 최소 이익잉여금 기준을 낮춰보세요.")
            
            # 다운로드 버튼
            st.markdown("---")
            if len(df_filtered) > 0:
                csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    "📥 CSV 다운로드",
                    csv,
                    f"potential_lp_{bsns_year}_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True
                )
    
    # =========================================================================
    # TAB 2: ESG 모니터링
    # =========================================================================
    with tab2:
        st.markdown("## 🌱 ESG 모니터링")
        
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
                
                if df_news is not None and not df_news.empty:
                    st.success(f"✅ {len(df_news)}건 검색 완료!")
                    
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
                    st.info("검색 결과가 없습니다.")
    
    # =========================================================================
    # TAB 3: 데이터
    # =========================================================================
    with tab3:
        st.markdown("### 📋 전체 데이터")
        
        if st.session_state.financial_data is not None:
            df = st.session_state.financial_data.copy()
            
            # 이익잉여금 순 정렬
            df = df.sort_values('retained_earnings', ascending=False).reset_index(drop=True)
            
            # 표시용 컬럼명 변경
            display_df = df.rename(columns={
                'corp_name': '기업명',
                'stock_code': '종목코드',
                'retained_earnings': '이익잉여금(억원)',
                'total_equity': '자본총계(억원)',
                'revenue': '매출액(억원)'
            })
            
            st.dataframe(display_df, use_container_width=True, height=500)
            
            # 다운로드
            csv = display_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 전체 데이터 다운로드",
                csv,
                f"dart_financial_data_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info("데이터가 없습니다. LP 발굴 탭에서 먼저 데이터를 조회하세요.")
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        🏢 Potential LP 모니터링 대시보드 v2.0 | 인프라프론티어자산운용(주) | DART API 실시간 연동
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
