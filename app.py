import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 확정된 구글 시트 ID 반영
SHEET_ID = '1_4z6RBNn8HQ1_xfznsITZ0yGWu5xpP-BYDmOdi_ftaE'
SHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'

st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# --- 데이터 로드 함수 (이력 관리 및 직전 종료거리 로드) ---
def get_last_dist(car_name):
    try:
        # 구글 시트에서 실시간으로 데이터 읽기
        df = pd.read_csv(SHEET_URL)
        # 선택된 차량의 가장 마지막 행 데이터 추출
        last_row = df[df['차량'] == car_name].iloc[-1]
        return int(last_row['종료거리'])
    except:
        # 데이터가 없거나 오류 발생 시 0 반환
        return 0

st.title("🚛 차량 운행 기록부")

# --- 1. 차량 선택 (확정된 라인업) ---
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378"]
selected_car = st.selectbox("차량 선택", car_list)

# --- 2. 운전자 선택 (요청하신 명단 반영) ---
driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("운전자", driver_list)
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# --- 3. 출발지 및 목적지 설정 (요청 경로 반영) ---
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

# --- 4. 거리 입력 (시트에서 불러온 직전 종료거리가 기본값) ---
last_km = get_last_dist(selected_car)
col3, col4 = st.columns(2)

with col3:
    start_km = st.number_input("시작 거리 (km)", value=last_km)
with col4:
    end_km = st.number_input("종료 거리 (km)", value=start_km)

# --- 5. 운행 내용 ---
purpose_list = ["납품 및 업무협의", "거래처 미팅", "현장 방문", "기타"]
purpose = st.selectbox("📝 운행 내용", purpose_list)

st.divider()

# --- 6. 저장 및 이력 확인 ---
if st.button("🚀 운행 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
    elif not selected_driver or (selected_driver == "직접 입력" and not selected_driver):
        st.warning("운전자를 입력해 주세요.")
    else:
        total_dist = end_km - start_km
        st.success(f"입력 확인: {selected_car} | {selected_driver} | {total_dist}km 주행")
        
        # 현재는 저장 안내 메시지만 표시 (구글 설문지 연동 코드를 추가하여 실제 저장 가능)
        st.info("데이터가 시트 형식으로 준비되었습니다. (실제 저장을 위해서는 설문지 연동이 필요합니다.)")

# --- 하단 이력 조회 섹션 ---
with st.expander("📊 최근 운행 이력 보기 (최근 10건)"):
    try:
        history_df = pd.read_csv(SHEET_URL)
        # 시간 역순으로 최근 10개 표시
        st.dataframe(history_df.tail(10).iloc[::-1], use_container_width=True)
    except:
        st.write("구글 시트에서 데이터를 불러올 수 없습니다. 시트 공유 설정을 확인해 주세요.")
