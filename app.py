import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# 1. 페이지 및 API 설정
st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# [필독] 아래 따옴표 안에 Apps Script에서 복사한 웹 앱 URL을 붙여넣으세요.
API_URL = "https://script.google.com/macros/s/AKfycbwh4no_4O6KuHcvWZtcZPuWCkLXlNBU0qy679AifLa9EbXpz1-sjuGTYyzKU1oxJ99l/exec"

# 구글 시트 읽기용 ID (기존과 동일)
SHEET_ID = '1_4z6RBNn8HQ1_xfznsITZ0yGWu5xpP-BYDmOdi_ftaE'
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# 2. 모바일 최적화 디자인 (로고 포함)
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

# 실시간 마지막 주행거리 가져오기 함수
def get_last_dist(car_name):
    try:
        df = pd.read_csv(READ_URL)
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            return int(car_df.iloc[-1]['종료거리'])
        return 0
    except:
        return 0

# 3. 입력 섹션
selected_date = st.date_input("📅 운행 날짜", datetime.now())

car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)

driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("👤 운전자", driver_list)
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# 4. 주행 정보 입력
last_km = get_last_dist(selected_car)

col_start, col_end = st.columns(2)
with col_start:
    start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "통근노선 시작", "직접 입력"])
    if start_node == "직접 입력": start_node = st.text_input("출발지 상세")
    start_km = st.number_input("📍 시작 거리 (km)", value=last_km)
    st.caption(f"이전 기록: {last_km}km")

with col_end:
    end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점", "직접 입력"])
    if end_node == "직접 입력": end_node = st.text_input("목적지 상세")
    end_km = st.number_input("🏁 종료 거리 (km)", value=start_km)
    st.caption(f"⚠️ {start_km}km 이상 입력하세요")

st.divider()

# 5. 운행 내용 및 비고
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "기타"])
memo = st.text_area("비고 (특이사항)", height=80, placeholder="주유 기록이나 차량 특이사항을 적어주세요.")

total_distance = end_km - start_km

# 6. 저장 로직 (Apps Script API 연동)
if st.button("🚀 운행 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error(f"입력 오류: 종료 거리({end_km}km)가 시작 거리({start_km}km)보다 작습니다!")
    elif not selected_driver:
        st.warning("운전자를 입력하거나 선택해주세요.")
    elif API_URL == "여기에_복사한_URL을_넣으세요":
        st.error("API URL이 설정되지 않았습니다. 코드를 확인해 주세요.")
    else:
        # 전송할 데이터 묶기
        payload = {
            "날짜": selected_date.strftime('%Y-%m-%d'),
            "차량": selected_car,
            "운전자": selected_driver,
            "출발지": start_node,
            "목적지": end_node,
            "시작거리": start_km,
            "종료거리": end_km,
            "주행거리": total_distance,
            "운행내용": purpose,
            "비고": memo,
            "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Apps Script로 데이터 전송
            response = requests.post(API_URL, data=json.dumps(payload))
            if response.text == "Success":
                st.success(f"✅ {total_distance}km 주행 기록이 구글 시트에 즉시 저장되었습니다!")
                st.balloons()
            else:
                st.error("저장 실패. 구글 스크립트 설정을 확인하세요.")
        except Exception as e:
            st.error(f"네트워크 오류: {e}")

# 7. 최근 이력 조회
with st.expander("📊 최근 기록 (5건)"):
    try:
        history = pd.read_csv(READ_URL)
        st.dataframe(history.tail(5).iloc[::-1], use_container_width=True)
    except:
        st.write("기록 로딩 중...")
