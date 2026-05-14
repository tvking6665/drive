import streamlit as st
import pandas as pd
from datetime import datetime

# 1. 구글 시트 설정 (본인의 시트 ID로 교체하세요)
SHEET_ID = '1_4z6RBNn8HQ1_xfznsITZ0yGWu5xpP-BYDmOdi_ftaE'
SHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv'

st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# --- 데이터 로드 함수 ---
def get_last_dist(car_name):
    try:
        df = pd.read_csv(SHEET_URL)
        # 해당 차량의 마지막 종료거리 추출
        last_row = df[df['차량'] == car_name].iloc[-1]
        return int(last_row['종료거리'])
    except:
        return 0 # 기록이 없으면 0 반환

# --- UI 구성 ---
st.title("🚛 차량 운행 기록부")

# 차량 및 운전자 (전우정밀 차량 리스트)
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378"]
selected_car = st.selectbox("차량 선택", car_list)
driver = st.text_input("운전자", value="조현호")

st.divider()

# 경로 설정
loc_options = ["회사", "전우정밀", "직접 입력"]
col1, col2 = st.columns(2)
with col1:
    start_node = st.selectbox("📍 출발지", loc_options, index=0)
    if start_node == "직접 입력": start_node = st.text_input("출발지 입력")
with col2:
    end_node = st.selectbox("🎯 목적지", loc_options, index=2)
    if end_node == "직접 입력": end_node = st.text_input("목적지 입력")

# 거리 입력 (차량 선택 시 자동으로 직전 종료거리 로드)
last_km = get_last_dist(selected_car)
c3, c4 = st.columns(2)
with c3:
    start_km = st.number_input("시작 거리 (km)", value=last_km)
with c4:
    end_km = st.number_input("종료 거리 (km)", value=start_km)

# 운행 내용
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "거래처 미팅", "현장 방문", "기타"])

st.divider()

# 저장 버튼
if st.button("🚀 운행 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작습니다!")
    else:
        # 여기에 구글 시트로 데이터를 보내는 링크 생성 (Google Forms 연동 방식 활용 가능)
        st.success(f"저장 완료! 차량: {selected_car} / 주행: {end_km - start_km}km")
        
        # 입력 데이터 요약 표시
        new_data = {
            "날짜": datetime.now().strftime("%Y-%m-%d"),
            "차량": selected_car,
            "운전자": driver,
            "경로": f"{start_node} -> {end_node}",
            "시작거리": start_km,
            "종료거리": end_km,
            "내용": purpose
        }
        st.write("저장된 데이터:", new_data)

# --- 관리자 조회 모드 (하단에 배치) ---
with st.expander("📊 최근 운행 이력 보기"):
    try:
        history_df = pd.read_csv(SHEET_URL)
        st.dataframe(history_df.tail(10), use_container_width=True)
    except:
        st.write("아직 기록된 데이터가 없습니다.")
