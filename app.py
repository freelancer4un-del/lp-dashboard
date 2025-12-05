"""
LP Dashboard v2.1 - Potential LP 모니터링 대시보드
인프라프론티어자산운용(주)

개선사항:
- Streamlit Cloud 타임아웃 해결을 위한 분할 조회 방식
- 업종별 배치 조회 (한 번에 100개씩)
- 중간 저장 기능 (세션 상태 유지)
- CSV 파일로 결과 누적 저장
"""

import streamlit as st

# =============================================================================
# 페이지 설정 (반드시 첫 번째!)
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
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    
    .stApp {
        font-family: 'Noto Sans KR', sans-serif;
    }
    
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
    }
    .metric-card:hover { border-color: #3498db; }
    .metric-title { color: #888888; font-size: 0.8rem; margin-bottom: 0.3rem; }
    .metric-value { color: #ffffff; font-size: 1.3rem; font-weight: 700; }
    .metric-sub { color: #666; font-size: 0.75rem; margin-top: 0.2rem; }
    
    .company-card {
        background: linear-gradient(145deg, #16213e 0%, #1a1a2e 100%);
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #0f3460;
        margin-bottom: 0.6rem;
    }
    .company-card:hover { border-color: #3498db; }
    .company-name { color: #ffffff; font-size: 1rem; font-weight: 700; margin-bottom: 0.3rem; }
    .company-info { color: #aaaaaa; font-size: 0.8rem; line-height: 1.5; }
    
    .progress-card {
        background: rgba(52, 152, 219, 0.1);
        border: 1px solid #3498db;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .batch-button {
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s;
    }
    .batch-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
    }
    
    .status-success { color: #27ae60; }
    .status-warning { color: #f39c12; }
    .status-error { color: #e74c3c; }
    
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
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DART API 함수들
# =============================================================================
@st.cache_data(ttl=86400, show_spinner=False)
def get_corp_code_list():
    """상장기업 코드 목록 다운로드"""
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
        st.error(f"기업 목록 다운로드 실패: {str(e)}")
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
    """재무제표에서 주요 항목 추출"""
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

def fetch_batch_financial_data(corp_batch, bsns_year, progress_placeholder=None):
    """배치 단위로 재무정보 조회"""
    results = []
    total = len(corp_batch)
    
    for idx, row in enumerate(corp_batch.itertuples()):
        # 진행률 업데이트
        if progress_placeholder:
            progress_placeholder.progress((idx + 1) / total, 
                                          text=f"조회 중... {idx+1}/{total} - {row.corp_name}")
        
        # API 호출
        fs_df = get_financial_statement(row.corp_code, bsns_year)
        fin_data = extract_financial_data(fs_df)
        
        if fin_data['retained_earnings'] is not None:
            results.append({
                'corp_code': row.corp_code,
                'corp_name': row.corp_name,
                'stock_code': row.stock_code,
                **fin_data
            })
        
        # API 호출 제한 (초당 약 5회)
        time.sleep(0.2)
    
    return pd.DataFrame(results) if results else pd.DataFrame()

@st.cache_data(ttl=1800, show_spinner=False)
def search_esg_disclosures(keyword, start_date, end_date, max_results=30):
    """ESG 키워드 공시 검색"""
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
# 메인 앱
# =============================================================================
def main():
    # 세션 상태 초기화
    if 'corp_list' not in st.session_state:
        st.session_state.corp_list = None
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = pd.DataFrame()
    if 'current_batch' not in st.session_state:
        st.session_state.current_batch = 0
    if 'batch_size' not in st.session_state:
        st.session_state.batch_size = 100
    if 'is_loading' not in st.session_state:
        st.session_state.is_loading = False
    
    # 사이드바
    with st.sidebar:
        st.markdown("## ⚙️ 설정")
        
        st.markdown("### 📊 조회 조건")
        
        bsns_year = st.selectbox(
            "사업연도",
            ['2024', '2023', '2022', '2021'],
            index=0,
            help="2024년 사업보고서는 2025년 3월 이후 공시"
        )
        
        min_re = st.number_input(
            "최소 이익잉여금 (억원)",
            min_value=0, max_value=10000, value=300, step=100
        )
        
        st.markdown("### ⚡ 배치 설정")
        batch_size = st.selectbox(
            "배치 크기",
            [50, 100, 200],
            index=1,
            help="한 번에 조회할 기업 수"
        )
        st.session_state.batch_size = batch_size
        
        st.markdown("---")
        
        # 캐시 초기화
        if st.button("🔄 전체 초기화", use_container_width=True):
            st.cache_data.clear()
            st.session_state.corp_list = None
            st.session_state.financial_data = pd.DataFrame()
            st.session_state.current_batch = 0
            st.rerun()
        
        st.markdown("---")
        st.markdown(f"""
        ### 📋 현재 상태
        - **조회된 기업:** {len(st.session_state.financial_data)}개
        - **사업연도:** {bsns_year}
        - **버전:** v2.1
        """)
    
    # 메인 헤더
    st.markdown(f"""
    <div class="main-header">
        <h1>🏢 Potential LP 모니터링 대시보드 v2.1</h1>
        <p>📅 {datetime.now().strftime('%Y년 %m월 %d일')} | 인프라프론티어자산운용(주) | 분할 조회 방식</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 탭
    tab1, tab2, tab3 = st.tabs(["🔍 LP 발굴 (분할조회)", "🌱 ESG 모니터링", "📋 전체 데이터"])
    
    # =========================================================================
    # TAB 1: LP 발굴 (분할 조회)
    # =========================================================================
    with tab1:
        st.markdown("## 🔍 Potential LP 발굴")
        
        # Step 1: 기업 목록 로드
        if st.session_state.corp_list is None:
            st.markdown("""
            <div class="info-box">
                <strong>💡 사용 방법</strong><br>
                1. 먼저 "상장기업 목록 불러오기" 버튼을 클릭하세요<br>
                2. 그 다음 "다음 배치 조회" 버튼으로 100개씩 조회합니다<br>
                3. Streamlit Cloud 타임아웃 방지를 위해 분할 조회 방식을 사용합니다
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📥 1단계: 상장기업 목록 불러오기", type="primary", use_container_width=True):
                with st.spinner("상장기업 목록 다운로드 중..."):
                    corp_df = get_corp_code_list()
                
                if corp_df is not None and not corp_df.empty:
                    st.session_state.corp_list = corp_df
                    st.success(f"✅ 총 {len(corp_df)}개 상장기업 로드 완료!")
                    st.rerun()
                else:
                    st.error("기업 목록을 가져올 수 없습니다.")
        
        else:
            corp_df = st.session_state.corp_list
            total_corps = len(corp_df)
            current_batch = st.session_state.current_batch
            batch_size = st.session_state.batch_size
            
            # 진행 상태 표시
            completed = current_batch * batch_size
            remaining = total_corps - completed
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">총 상장기업</div>
                    <div class="metric-value">{total_corps}개</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">조회 완료</div>
                    <div class="metric-value">{completed}개</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">남은 기업</div>
                    <div class="metric-value">{remaining}개</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">조회된 LP 후보</div>
                    <div class="metric-value">{len(st.session_state.financial_data)}개</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 진행률 바
            progress_pct = completed / total_corps
            st.progress(progress_pct, text=f"전체 진행률: {progress_pct*100:.1f}%")
            
            st.markdown("---")
            
            # 배치 조회 버튼
            if remaining > 0:
                st.markdown("""
                <div class="warning-box">
                    <strong>⚡ 분할 조회 안내</strong><br>
                    Streamlit Cloud 타임아웃 방지를 위해 100개씩 분할 조회합니다.<br>
                    "다음 배치 조회" 버튼을 여러 번 클릭하여 전체 데이터를 수집하세요.
                </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button(f"⏭️ 다음 배치 조회 ({batch_size}개)", type="primary", use_container_width=True):
                        st.session_state.is_loading = True
                        
                        # 현재 배치 범위 계산
                        start_idx = current_batch * batch_size
                        end_idx = min(start_idx + batch_size, total_corps)
                        
                        batch_corps = corp_df.iloc[start_idx:end_idx]
                        
                        st.markdown(f"### 📊 배치 #{current_batch + 1} 조회 중 ({start_idx+1}~{end_idx}번)")
                        
                        progress_bar = st.progress(0)
                        
                        # 배치 조회 실행
                        batch_results = fetch_batch_financial_data(batch_corps, bsns_year, progress_bar)
                        
                        # 결과 누적
                        if not batch_results.empty:
                            if st.session_state.financial_data.empty:
                                st.session_state.financial_data = batch_results
                            else:
                                st.session_state.financial_data = pd.concat([
                                    st.session_state.financial_data, 
                                    batch_results
                                ], ignore_index=True)
                            
                            st.success(f"✅ {len(batch_results)}개 기업 재무정보 추가!")
                        else:
                            st.info("이 배치에서는 이익잉여금 데이터가 있는 기업이 없습니다.")
                        
                        # 다음 배치로 이동
                        st.session_state.current_batch += 1
                        st.session_state.is_loading = False
                        st.rerun()
                
                with col_btn2:
                    if st.button("⏩ 5배치 연속 조회 (500개)", use_container_width=True):
                        for _ in range(5):
                            if remaining <= 0:
                                break
                            
                            start_idx = st.session_state.current_batch * batch_size
                            end_idx = min(start_idx + batch_size, total_corps)
                            batch_corps = corp_df.iloc[start_idx:end_idx]
                            
                            st.markdown(f"배치 #{st.session_state.current_batch + 1} 조회 중...")
                            
                            batch_results = fetch_batch_financial_data(batch_corps, bsns_year, None)
                            
                            if not batch_results.empty:
                                if st.session_state.financial_data.empty:
                                    st.session_state.financial_data = batch_results
                                else:
                                    st.session_state.financial_data = pd.concat([
                                        st.session_state.financial_data, 
                                        batch_results
                                    ], ignore_index=True)
                            
                            st.session_state.current_batch += 1
                            remaining = total_corps - (st.session_state.current_batch * batch_size)
                        
                        st.rerun()
            
            else:
                st.success("🎉 모든 상장기업 조회 완료!")
            
            st.markdown("---")
            
            # 결과 표시
            if not st.session_state.financial_data.empty:
                df = st.session_state.financial_data.copy()
                
                # 필터링
                df_filtered = df[df['retained_earnings'] >= min_re].copy()
                
                # 스코어 계산
                if len(df_filtered) > 0:
                    df_filtered = calculate_lp_score(df_filtered)
                
                st.markdown(f"### 📋 LP 후보 기업 ({min_re}억원 이상): {len(df_filtered)}개")
                
                if len(df_filtered) > 0:
                    # 상위 30개 표시
                    for idx, row in df_filtered.head(30).iterrows():
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.markdown(f"""
                            <div class="company-card">
                                <div class="company-name">{row['corp_name']} ({row['stock_code']})</div>
                                <div class="company-info">
                                    이익잉여금: <strong>{format_number(row['retained_earnings'])}</strong> | 
                                    자본총계: {format_number(row.get('total_equity'))} | 
                                    매출액: {format_number(row.get('revenue'))}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            score = row.get('lp_score', 0)
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-title">LP 스코어</div>
                                <div class="metric-value">{score:.1f}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # 다운로드
                    st.markdown("---")
                    csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        "📥 LP 후보 목록 다운로드 (CSV)",
                        csv,
                        f"potential_lp_{bsns_year}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
                else:
                    st.info(f"이익잉여금 {min_re}억원 이상인 기업이 없습니다. 기준을 낮춰보세요.")
    
    # =========================================================================
    # TAB 2: ESG 모니터링
    # =========================================================================
    with tab2:
        st.markdown("## 🌱 ESG 키워드 공시 검색")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            keyword = st.selectbox(
                "검색 키워드",
                ["탄소중립", "RE100", "ESG경영", "지속가능경영", "친환경", "녹색금융"]
            )
        
        with col2:
            start_date = st.date_input("시작일", datetime.now() - timedelta(days=90))
        
        with col3:
            end_date = st.date_input("종료일", datetime.now())
        
        if st.button("🔍 ESG 공시 검색", use_container_width=True):
            with st.spinner("검색 중..."):
                df_esg = search_esg_disclosures(
                    keyword,
                    start_date.strftime('%Y%m%d'),
                    end_date.strftime('%Y%m%d')
                )
            
            if not df_esg.empty:
                st.success(f"✅ {len(df_esg)}건 검색 완료!")
                
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
    # TAB 3: 전체 데이터
    # =========================================================================
    with tab3:
        st.markdown("## 📋 조회된 전체 데이터")
        
        if not st.session_state.financial_data.empty:
            df = st.session_state.financial_data.copy()
            df = df.sort_values('retained_earnings', ascending=False)
            
            st.dataframe(
                df.rename(columns={
                    'corp_name': '기업명',
                    'stock_code': '종목코드',
                    'retained_earnings': '이익잉여금(억)',
                    'total_equity': '자본총계(억)',
                    'revenue': '매출액(억)'
                }),
                use_container_width=True,
                height=500
            )
            
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 전체 데이터 다운로드",
                csv,
                f"dart_all_data_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info("아직 조회된 데이터가 없습니다. LP 발굴 탭에서 조회를 시작하세요.")
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#666; padding:0.5rem;">
        🏢 Potential LP 모니터링 대시보드 v2.1 | 인프라프론티어자산운용(주)
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
