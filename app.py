import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정 및 모바일 최적화 스타일 적용
st.set_page_config(page_title="전우정밀 차량/연료 관리", layout="centered")

st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; }
    .stHeader { font-size: 18px !important; }
    .fuel-section { 
        background-color: rgba(28, 131, 225, 0.1); 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #1c83e1;
        margin: 10px 0; 
    }
    div[data-testid="stExpander"] p { font-size: 14px !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 로고 및 제목 배치
col1, col2 = st.columns([1, 4])
with col1:
    try:
        st.image("logo.png", width=60)
    except:
        st.write("🏢")

with col2:
    st.markdown('<p class="main-title">차량 운행 및 연료 기록부</p>', unsafe_allow_html=True)

# 3. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_last_dist(car_name):
    try:
        # 실시간 데이터를 위해 캐시(ttl)를 0으로 설정하여 읽기
        df = conn.read(ttl=0)
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            return int(car_df.iloc[-1]['종료거리'])
        return 0
    except:
        return 0

# 4. 운행 기본 정보 입력
selected_date = st.date_input("📅 운행 날짜", datetime.now())

car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)

driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("👤 운전자", driver_list)
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# 5. 주행 거리 및 노선 입력 (모바일 5:5 배치)
last_km = get_last_dist(selected_car)

col_start, col_end = st.columns(2)
with col_start:
    start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "통근노선 시작", "직접 입력"])
    if start_node == "직접 입력": start_node = st.text_input("출발지 상세")
    start_km = st.number_input("📍 시작 거리 (km)", value=last_km)

with col_end:
    end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점", "직접 입력"])
    if end_node == "직접 입력": end_node = st.text_input("목적지 상세")
    end_km = st.number_input("🏁 종료 거리 (km)", value=start_km, help="시작 거리보다 큰 값을 입력하세요")

st.divider()

# 6. 연료 및 요소수 주입 섹션
st.markdown("### ⛽ 연료 및 요소수 주입")
fuel_needed = st.checkbox("오늘 연료나 요소수를 주입했나요?")

fuel_type = "-"
fuel_amount = 0
fuel_cost = 0

if fuel_needed:
    st.markdown('<div class="fuel-section">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        fuel_type = st.selectbox("종류", ["LPi", "경유", "요소수
