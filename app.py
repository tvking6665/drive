import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 차량/연료 관리", layout="centered")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_last_dist(car_name):
    try:
        df = conn.read()
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            return int(car_df.iloc[-1]['종료거리'])
        return 0
    except: return 0

# 헤더
st.markdown('<p style="font-size:24px; font-weight:bold;">🚗 차량 운행 및 연료 기록부</p>', unsafe_allow_html=True)

# --- 기본 운행 정보 ---
selected_date = st.date_input("📅 날짜", datetime.now())
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)
selected_driver = st.selectbox("👤 운전자", ["김동현", "김태종", "이학장", "직접 입력"])
if selected_driver == "직접 입력": selected_driver = st.text_input("운전자 성명")

st.divider()

# --- 주행 거리 정보 ---
last_km = get_last_dist(selected_car)
col1, col2 = st.columns(2)
with col1:
    start_km = st.number_input("📍 시작 거리 (km)", value=last_km)
with col2:
    end_km = st.number_input("🏁 종료 거리 (km)", value=start_km)

st.divider()

# --- 연료 주입 정보 (새로 추가된 섹션) ---
st.markdown("### ⛽ 연료 및 요소수 주입")
fuel_needed = st.checkbox("오늘 연료나 요소수를 주입했나요?")

fuel_type = "-"
fuel_amount = 0
fuel_cost = 0

if fuel_needed:
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        fuel_type = st.selectbox("종류", ["LPi", "경유", "요소수"])
    with f_col2:
        # 가스(LPi)는 보통 금액으로 입력하시므로 단위를 상황에 맞게 노출
        unit = "원" if fuel_type == "LPi" else "리터(L)"
        fuel_amount = st.number_input(f"주입량 ({unit})", min_value=0, step=1)
    with f_col3:
        fuel_cost = st.number_input("결제 금액 (원)", min_value=0, step=100)

st.divider()

# --- 기타 정보 ---
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "기타"])
memo = st.text_area("비고 (특이사항)", height=80)

# --- 저장 로직 ---
if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리를 확인하세요!")
    else:
        try:
            new_data = pd.DataFrame([{
                "날짜": selected_date.strftime('%Y-%m-%d'),
                "차량": selected_car,
                "운전자": selected_driver,
                "시작거리": start_km,
                "종료거리": end_km,
                "주행거리": end_km - start_km,
                "연료종류": fuel_type,
                "주입량": fuel_amount,
                "결제금액": fuel_cost,
                "운행내용": purpose,
                "비고": memo,
                "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])
            
            existing_df = conn.read()
            updated_df = pd.concat([existing_df, new_data], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success("데이터가 성공적으로 저장되었습니다!")
            st.balloons()
        except Exception as e:
            st.error(f"저장 중 오류 발생: {e}")
