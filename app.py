import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 구글 시트 정보 (이미 공유 설정 완료하신 시트)
SHEET_ID = '1_4z6RBNn8HQ1_xfznsITZ0yGWu5xpP-BYDmOdi_ftaE'
SHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'

st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# --- 데이터 로드 함수: 시트에서 해당 차량의 마지막 종료거리를 가져옴 ---
def get_last_dist(car_name):
    try:
        # 실시간으로 시트 읽기 (캐시 방지를 위해 매번 새로 읽음)
        df = pd.read_csv(SHEET_URL)
        # 선택한 차량의 데이터만 필터링
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            # 마지막 행의 '종료거리' 반환[cite: 2]
            return int(car_df.iloc[-1]['종료거리'])
        return 0 # 기록이 전혀 없는 차량일 경우
    except Exception as e:
        return 0

st.title("🚛 차량 운행 기록부")

# --- 1. 기본 정보 입력 ---
selected_date = st.date_input("📅 운행 날짜", datetime.now())[cite: 2]

car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378"]
selected_car = st.selectbox("🚗 차량 선택", car_list)[cite: 2]

# --- 2. 운전자 선택 (명단 반영) ---[cite: 2]
driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("👤 운전자", driver_list)
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# --- 3. 경로 및 주행 거리 (핵심 기능) ---
col1, col2 = st.columns(2)
with col1:
    start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "직접 입력"])
    if start_node == "직접 입력": start_node = st.text_input("출발지 상세")
with col2:
    end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "직접 입력"])
    if end_node == "직접 입력": end_node = st.text_input("목적지 상세")

# 차량 선택(selected_car)이 바뀔 때마다 아래 숫자가 자동으로 업데이트됨[cite: 2]
last_km = get_last_dist(selected_car) 

c3, c4 = st.columns(2)
with c3:
    # 시작거리는 시트에서 가져온 직전 종료거리로 고정[cite: 2]
    start_km = st.number_input("📍 시작 거리 (km)", value=last_km, help="구글 시트의 마지막 종료거리를 자동으로 불러왔습니다.")
with c4:
    # 종료거리는 시작거리부터 입력 시작[cite: 2]
    end_km = st.number_input("🏁 종료 거리 (km)", value=start_km)

# --- 4. 기타 정보 ---
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "거래처 미팅", "현장 방문", "기타"])

st.divider()

# --- 5. 저장 버튼 ---
if st.button("🚀 운행 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작을 수 없습니다! 다시 확인해 주세요.")
    elif not selected_driver:
        st.warning("운전자를 선택하거나 입력해 주세요.")
    else:
        st.success(f"데이터 준비 완료: {selected_car} | 주행거리: {end_km - start_km}km")
        # 실제 저장 로직(Google Forms 등)이 연결될 자리[cite: 2]
        st.info("시트에 기록을 확정하려면 관리자가 제공한 제출 링크를 클릭해야 합니다.")

# --- 6. 하단 이력 조회 (최신순) ---[cite: 2]
with st.expander("📊 최근 운행 이력 보기 (최근 10건)"):
    try:
        history_df = pd.read_csv(SHEET_URL)
        st.dataframe(history_df.tail(10).iloc[::-1], use_container_width=True)
    except:
        st.write("데이터를 불러오는 중입니다. 시트에 첫 데이터가 입력되면 표시됩니다.")
