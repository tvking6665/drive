import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# 사용자 정의 스타일
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; }
    </style>
    """, unsafe_allow_html=True)

# 2. 로고 및 제목
col1, col2 = st.columns([1, 4])
with col1:
    try:
        st.image("logo.png", width=60)
    except:
        st.write("🏢")
with col2:
    st.markdown('<p class="main-title">차량 운행 기록부</p>', unsafe_allow_html=True)

# 3. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_last_dist(car_name):
    try:
        # 실시간 데이터를 가져오기 위해 ttl=0 설정
        df = conn.read(ttl=0)
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            val = car_df.iloc[-1]['종료거리']
            # 숫자가 아닌 값이 섞여있을 경우를 대비해 숫자로 변환
            num_val = pd.to_numeric(val, errors='coerce')
            return int(num_val) if pd.notnull(num_val) else 0
        return 0
    except:
        return 0

# 4. 운행 정보 입력
selected_date = st.date_input("📅 운행 날짜", datetime.now())
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)

selected_driver = st.selectbox("👤 운전자", ["김동현", "김태종", "이학장", "직접 입력"])
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# 5. 주행 거리 입력
last_km = get_last_dist(selected_car)
col_start, col_end = st.columns(2)
with col_start:
    start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "통근노선 시작", "직접 입력"])
    if start_node == "직접 입력": start_node = st.text_input("출발지 상세")
    start_km = st.number_input("📍 시작 거리 (km)", value=int(last_km))

with col_end:
    end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점", "직접 입력"])
    if end_node == "직접 입력": end_node = st.text_input("목적지 상세")
    end_km = st.number_input("🏁 종료 거리 (km)", value=int(start_km))

st.divider()

# 6. 운행 내용 및 비고
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "기타"])
memo = st.text_area("비고
