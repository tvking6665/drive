import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json

# 1. 페이지 및 API 설정
st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# [중요] 본인의 웹 앱 URL을 다시 확인해 주세요
API_URL = "https://script.google.com/macros/s/AKfycbwh4no_4O6KuHcvWZtcZPuWCkLXlNBU0qy679AifLa9EbXpz1-sjuGTYyzKU1oxJ99l/exec"

# 구글 시트 읽기용 ID
SHEET_ID = '1_4z6RBNn8HQ1_xfznsITZ0yGWu5xpP-BYDmOdi_ftaE'
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# 2. 디자인 설정
st.markdown("""
    <style>
    .main-title { font-size: 22px !important; font-weight: bold; margin-bottom: 5px; display: flex; align-items: center; }
    .stCaption { font-size: 13px !important; color: #FF4B4B !important; margin-top: -15px !important; margin-bottom: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([1, 4])
with col1:
    try: st.image("logo.png", width=55)
    except: st.write("🏢")
with col2:
    st.markdown('<p class="main-title">전우정밀 차량 운행 기록부</p>', unsafe_allow_html=True)

def get_last_dist(car_name):
    try:
        df = pd.read_csv(READ_URL)
        car_df = df[df['차량'] == car_name]
        if not car_df.empty: return int(car_df.iloc[-1]['종료거리'])
        return 0
    except: return 0

# 3. 입력 섹션
now_utc = datetime.utcnow()
now_kst = now_utc + timedelta(hours=9)
selected_date = st.date_input("📅 운행 날짜", now_kst)

car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)

driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("👤 운전자", driver_list)
if selected_driver == "직접 입력": selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# 4. 주행 정보 (출발지/목적지 업데이트)
last_km = get_last_dist(selected_car)
col_s, col_e = st.columns(2)

with col_s:
    start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "통근노선 시작", "직접 입력"])
    if start_node == "직접 입력": start_node = st.text_input("출발지 상세")
    start_km = st.number_input("📍 시작 거리 (km)", value=last_km)

with col_e:
    # 요청하신 목적지 리스트를 추가했습니다.
    dest_list = [
        "구산", "KDS", "고광메탈", "한국하이테크", "송원테크", 
        "제이테크", "DLS성주", "AST", "평화정공", 
        "왜관(VPHC)", "동아금속", "통근노선 종점", "직접 입력"
    ]
    end_node = st.selectbox("🎯 목적지", dest_list)
    if end_node == "직접 입력": end_node = st.text_input("목적지 상세")
    end_km = st.number_input("🏁 종료 거리 (km)", value=start_km)
    st.caption(f"⚠️ {start_km}km 이상 입력하세요")

st.divider()

# 5. 운행 내용
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "기타"])
memo = st.text_area("비고 (특이사항)", height=80)

# 6. 저장 로직
if st.button("🚀 운행 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리를 확인하세요.")
    elif not selected_driver:
        st.warning("운전자를 선택하세요.")
    else:
        current_kst = datetime.utcnow() + timedelta(hours=9)
        payload = {
            "날짜": selected_date.strftime('%Y-%m-%d'),
            "차량": selected_car,
            "운전자": selected_driver,
            "출발지": start_node,
            "목적지": end_node,
            "시작거리": start_km,
            "종료거리": end_km,
            "주행거리": end_km - start_km,
            "운행내용": purpose,
            "비고": memo,
            "입력시간": current_kst.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            response = requests.post(API_URL, data=json.dumps(payload))
            if response.text == "Success":
                st.success("✅ 저장 성공! (한국 시간 기준)")
                st.balloons()
            else: st.error("저장 실패")
        except Exception as e:
            st.error(f"오류: {e}")

# 7. 이력 조회
with st.expander("📊 최근 기록 (5건)"):
    try:
        history = pd.read_csv(READ_URL)
        st.dataframe(history.tail(5).iloc[::-1], use_container_width=True)
    except: st.write("로딩 중...")
