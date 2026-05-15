import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# 2. 헤더 구성
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
if selected_driver == "직접 입력": 
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# 주행 거리 (5:5 배치)
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

# 5. 연료 주입 정보
fuel_needed = st.checkbox("⛽ 연료/요소수 주입 시 체크")
f_type, f_amt, f_cost = "-", 0, 0
if fuel_needed:
    fc1, fc2, fc3 = st.columns(3)
    with fc1: f_type = st.selectbox("종류", ["LPi", "경유", "요소수"])
    with fc2:
        l_label = "주입금액(원)" if f_type == "LPi" else "주입량(L)"
        f_amt = st.number_input(l_label, min_value=0)
    with fc3: f_cost = st.number_input("결제 총액(원)", min_value=0)

st.divider()
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "기타"])
memo = st.text_area("비고 (특이사항)")

# 6. 저장 로직 (배열 순서 일치)
if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
    else:
        try:
            # 이미지 시트 헤더 순서와 동일하게 구성
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
            
            df_existing = conn.read(ttl=0)
            df_updated = pd.concat([df_existing, new_row], ignore_index=True)
            conn.update(data=df_updated)
            
            st.success("저장 완료!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
            st.info("💡 구글 시트 공유 설정에서 서비스 계정 이메일을 추가했는지 확인해 주세요.")

with st.expander("📊 최근 기록 보기"):
    try:
        df_view = conn.read(ttl=0)
        st.dataframe(df_view.tail(5).iloc[::-1], use_container_width=True)
    except: st.write("데이터가 없습니다.")
