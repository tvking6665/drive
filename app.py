import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 확정된 구글 시트 ID 및 URL
SHEET_ID = '1_4z6RBNn8HQ1_xfznsITZ0yGWu5xpP-BYDmOdi_ftaE'
SHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'

st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# --- 데이터 로드 함수 (이력 관리 및 직전 종료거리 로드) ---
def get_last_dist(car_name):
    try:
        # 구글 시트에서 실시간 데이터 읽기
        df = pd.read_csv(SHEET_URL)
        # 해당 차량의 가장 마지막 종료거리 추출
        last_row = df[df['차량'] == car_name].iloc[-1]
        return int(last_row['종료거리'])
    except:
        return 0

st.title("🚛 차량 운행 기록부")

# --- 1. 날짜 및 차량 선택 ---
# 달력 형태의 날짜 선택 위젯 추가
selected_date = st.date_input("📅 운행 날짜", datetime.now())

car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378"]
selected_car = st.selectbox("🚗 차량 선택", car_list)

# --- 2. 운전자 선택 ---
driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("👤 운전자", driver_list)
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# --- 3. 출발지 및 목적지 설정 ---
col1, col2 = st.columns(2)

with col1:
    start_options = ["회사(전우정밀)", "직접 입력"]
    start_node = st.selectbox("📍 출발지", start_options)
    if start_node == "직접 입력":
        start_node = st.text_input("출발지 상세 입력")

with col2:
    end_options = ["왜관(VPHC)", "AST(2공장)", "동아금속", "직접 입력"]
    end_node = st.selectbox("🎯 목적지", end_options)
    if end_node == "직접 입력":
        end_node = st.text_input("목적지 상세 입력")

# --- 4. 주행 거리 입력 (자동 로드 반영) ---
last_km = get_last_dist(selected_car)
col3, col4 = st.columns(2)

with col3:
    start_km = st.number_input("📍 시작 거리 (km)", value=last_km)
with col4:
    end_km = st.number_input("🏁 종료 거리 (km)", value=start_km)

# --- 5. 운행 내용 ---
purpose_list = ["납품 및 업무협의", "거래처 미팅", "현장 방문", "기타"]
purpose = st.selectbox("📝 운행 내용", purpose_list)

st.divider()

# --- 6. 저장 및 전송 로직 ---
if st.button("🚀 운행 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
    elif not selected_driver:
        st.warning("운전자를 확인해 주세요.")
    else:
        total_dist = end_km - start_km
        # 날짜를 포함한 데이터 요약
        st.success(f"입력 확인: {selected_date} | {selected_car} | {total_dist}km")
        
        # 구글 설문지 연동을 위한 안내 (추후 설문지 주소 완성 시 연동 가능)[cite: 2]
        st.info("데이터가 준비되었습니다. 최종 저장을 위해 관리자가 설정한 링크를 확인해 주세요.")

# --- 하단 최근 이력 조회 ---
with st.expander("📊 최근 운행 이력 보기 (최근 10건)"):
    try:
        history_df = pd.read_csv(SHEET_URL)
        # 최신 데이터가 위로 오도록 역순 표시[cite: 2]
        st.dataframe(history_df.tail(10).iloc[::-1], use_container_width=True)
    except:
        st.write("구글 시트 데이터를 불러올 수 없습니다.")
