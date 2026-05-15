import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 차량 관리 시스템", layout="centered")

# 2. 로고 및 헤더
col1, col2 = st.columns([1, 4])
with col1:
    try: st.image("logo.png", width=60)
    except: st.write("🏢")
with col2:
    st.markdown('<h2 style="margin-top:0;">차량 운행 및 연료 기록부</h2>', unsafe_allow_html=True)

# 3. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_last_dist(car_name):
    try:
        df = conn.read(ttl=0)
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            return int(car_df.iloc[-1]['종료거리'])
        return 0
    except: return 0

# 4. 입력 섹션
selected_date = st.date_input("📅 날짜", datetime.now())
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)
selected_driver = st.selectbox("👤 운전자", ["김동현", "김태종", "이학장", "직접 입력"])
if selected_driver == "직접 입력": selected_driver = st.text_input("운전자 성명 입력")

st.divider()

last_km = get_last_dist(selected_car)
c1, c2 = st.columns(2)
with c1:
    start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "통근노선 시작", "직접 입력"])
    if start_node == "직접 입력": start_node = st.text_input("출발지 상세")
    start_km = st.number_input("📍 시작 거리 (km)", value=last_km)
with c2:
    end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점", "직접 입력"])
    if end_node == "직접 입력": end_node = st.text_input("목적지 상세")
    end_km = st.number_input("🏁 종료 거리 (km)", value=start_km)

st.divider()

# 5. 연료 주입 섹션
fuel_needed = st.checkbox("오늘 연료나 요소수를 주입했나요?")
f_type, f_amt, f_cost = "-", 0, 0
if fuel_needed:
    fc1, fc2, fc3 = st.columns(3)
    with fc1: f_type = st.selectbox("종류", ["LPi", "경유", "요소수"])
    with fc2: f_amt = st.number_input("주입량", min_value=0)
    with fc3: f_cost = st.number_input("결제 금액", min_value=0)

st.divider()
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "기타"])
memo = st.text_area("비고 (특이사항)")

# 6. 저장 로직 (이미지의 시트 열 순서와 완벽 일치)
if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작습니다!")
    else:
        try:
            # [수정] 이미지 속 시트 순서: 날짜, 차량, 운전자, 출발지, 목적지, 시작거리, 종료거리, 주행거리, 운행내용, 비고, 입력시간, 연료종류, 주입량, 결제금액
            new_row = pd.DataFrame([{
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
                "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "연료종류": f_type,
                "주입량": f_amt,
                "결제금액": f_cost
            }])
            
            existing_df = conn.read(ttl=0)
            # 기존 데이터와 새 데이터를 합칠 때 열 이름이 정확히 일치해야 합니다.
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success("저장 완료!")
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")

# 7. 최근 기록 보기
with st.expander("📊 최근 기록"):
    try:
        df_hist = conn.read(ttl=0)
        st.dataframe(df_hist.tail(5).iloc[::-1], use_container_width=True)
    except: st.write("데이터가 없습니다.")
