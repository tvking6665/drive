import streamlit as st
import pandas as pd
import os
from PIL import Image

# 1. 앱 페이지 설정 (휴대폰 아이콘 이름 및 로고 설정)
# 아이콘으로 사용할 이미지 불러오기
try:
    favicon = Image.open("logo.png")
    st.set_page_config(
        page_title="원소재 정보", # 휴대폰 홈 화면에 표시될 이름
        page_icon=favicon,       # 휴대폰 홈 화면에 표시될 로고
        layout="centered"
    )
except:
    st.set_page_config(
        page_title="원소재 정보",
        page_icon="📊",
        layout="centered"
    )

# 2. CSS 스타일 최적화
st.markdown("""
<style>
    .main .block-container { padding: 1rem 0.5rem; }
    .company-name { font-size: 14px; font-weight: bold; color: #0047AB; margin-bottom: 2px; }
    .app-title { font-size: 22px; font-weight: 800; margin-top: 0px; margin-bottom: 10px; }
    
    /* 버튼 스타일 */
    div.stButton > button:first-child {
        width: 100%;
        background-color: #1c83e1;
        color: white;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
        margin-top: 10px;
    }
    
    /* 조회 결과 박스 */
    .search-result-box {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1.5px solid #1c83e1;
        padding: 10px;
        border-radius: 8px;
        color: #58a6ff !important;
        font-weight: bold;
        margin: 10px 0px;
    }
    
    /* 최종 요약 박스 (초록색) */
    .calc-box {
        background-color: rgba(40, 167, 69, 0.15);
        border: 2px solid #28a745;
        padding: 15px;
        border-radius: 8px;
        color: #72ff8d !important;
        font-weight: bold;
        font-size: 16px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# 3. 데이터 로드 및 전처리
@st.cache_data(ttl=600)
def load_data():
    file_name = "data.xlsx"
    if os.path.exists(file_name):
        try:
            df = pd.read_excel(file_name, engine='openpyxl')
            df.columns = df.columns.str.strip() # 컬럼명 공백 제거
            # 고객사 데이터가 비어있을 경우 대비
            if '고객사' in df.columns:
                df['고객사'] = df['고객사'].fillna('미지정')
            return df
        except:
            return None
    return None

# 데이터 필드 추출용 함수
def get_val(row, cols):
    for c in cols:
        if c in row.index and pd.notnull(row[c]):
            return row[c]
    return "-"

df = load_data()

# 4. 상단 헤더 영역
h_col1, h_col2 = st.columns([1, 4])
with h_col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=60)
with h_col2:
    st.markdown('<p class="company-name">Jeon Woo Precision Co., LTD</p>', unsafe_allow_html=True)
    st.markdown('<a href="http://mes.jwjm.com/bang.asp" target="_blank" style="text-decoration:none; font-size:12px; color:#E60012; font-weight:bold;">📊 실시간 가동 현황판</a>', unsafe_allow_html=True)

st.markdown('<h1 class="app-title">원소재 정보 시스템</h1>', unsafe_allow_html=True)

if df is not None:
    # 5. 입력 및 필터 영역
    st.write("🔍 **소재 검색 및 조건 입력**")
    
    # 고객사 필터
    if '고객사' in df.columns:
        customer_list = ['전체'] + sorted(df['고객사'].unique().tolist())
        selected_customer = st.selectbox("🤝 고객사 선택", options=customer_list)
    else:
        selected_customer = '전체'

    c1, c2 = st.columns(2)
    with c1:
        name_in = st.text_input("강종명", placeholder="예: SPFC590").strip()
    with c2:
        thick_in = st.text_input("두께", placeholder="예: 1.3").strip()
    
    c3, c4 = st.columns(2)
    with c3:
        qty_in = st.number_input("생산 예상 수량 (EA)", min_value=0, value=0, step=1000)
    with c4:
        loss_rate = st.number_input("Loss율 (%)", min_value=0.0, max_value=50.0, value=3.0, step=0.5)

    # 필터링 로직
    res = df.copy()
    if selected_customer != '전체':
        res = res[res['고객사'] == selected_customer]
    if name_in:
        res = res[res['소재명'].astype(str).str.contains(name_in, case=False, na=False)]
    if thick_in:
        t_col = '두께(T)' if '두께(T)' in res.columns else '두께'
        try:
            res = res[res[t_col].astype(float) == float(thick_in)]
        except:
            pass

    st.divider()

    # 6. 조회 결과 및 계산 영역
    if not res.empty:
        # 단중 정보가 있는 데이터만 필터링
        calc_ready = res.dropna(subset=['제품 단중']).copy()
        st.markdown(f'<div class="search-result-box">✅ 조회 결과: {len(res)}건</div>', unsafe_allow_html=True)
        
        if not calc_ready.empty:
            # 드롭다운 라벨 생성 (한글화 및 프로젝트명 포함)
            def make_label(x):
                t = get_val(x, ['두께','두께(T)','T'])
                w = get_val(x, ['폭','폭(W)','W','소재폭'])
                extra = get_val(x, ['기타 정보 및 사양', '기타정보', '비고'])
                cust = get_val(x, ['고객사'])
                return f"[{cust}] {x['소재명']} (두께:{t} / 폭:{w} / 단중:{x['제품 단중']}) - {extra}"

            calc_ready['label'] = calc_ready.apply(make_label, axis=1)
            selected_label = st.selectbox("🎯 정확한 상세 규격 선택", options=calc_ready['label'].tolist())
            selected_row = calc_ready[calc_ready['label'] == selected_label].iloc[0]
            
            # 최종 적용 버튼
            if st.button("✅ 설정 내용 적용"):
                if qty_in > 0:
                    net_unit_w = float(selected_row['제품 단중'])
                    total_net_kg = net_unit_w * qty_in
                    # Loss율 반영한 Gross 중량 계산
                    total_gross_kg = total_net_kg * (1 + (loss_rate / 100))
                    total_gross_ton = total_gross_kg / 1000
                    
                    final_t = get_val(selected_row, ['두께','두께(T)','T'])
                    final_w = get_val(selected_row, ['폭','폭(W)','W','소재폭'])
                    final_extra = get_val(selected_row, ['기타 정보 및 사양', '기타정보', '비고'])
                    final_cust = get_val(selected_row, ['고객사'])
                    
                    # 최종 요약 화면 출력
                    st.markdown(f"""
                    <div class="calc-box">
                        📋 최종 적용 요약 (Loss {loss_rate}% 반영)<br>
                        - 고객사: {final_cust}<br>
                        - 규격: {selected_row['소재명']}<br>
                        - 두께: {final_t} / 폭: {final_w}<br>
                        - 제품 단중(Net): {net_unit_w} kg<br>
                        - 프로젝트명: {final_extra}<br>
                        - 생산 예상 수량: {qty_in:,} EA<br><br>
                        - 📦 순수 소요량(Net): {total_net_kg:,.0f} kg<br>
                        - 🚚 **총 구매 예정량(Gross): {total_gross_kg:,.0f} kg ({total_gross_ton:,.1f} ton)**
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("생산 수량을 입력해야 소요량이 계산됩니다.")
        else:
            st.info("💡 선택된 조건 내에 단중 정보가 있는 규격이 없습니다.")

        # 상세 데이터 테이블
        with st.expander("📊 상세 데이터 시트 확인"):
            st.table(res.astype(str).replace('nan', '-'))
    else:
        st.warning("검색 조건에 맞는 데이터가 없습니다.")
else:
    st.error("데이터 파일(data.xlsx)을 찾을 수 없습니다.")
