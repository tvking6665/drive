import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정 및 스타일
st.set_page_config(page_title="전우정밀 차량/연료 관리", layout="centered")

st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; }
    .stHeader { font-size: 18px !important; }
    .fuel-section { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# 2. 로고 및 제목
col1, col2 = st.columns([1, 4])
with col1:
    try: st.image("logo.png", width=60)
    except: st.write("🏢")
with col2:
    st.markdown('<p class="main-title">차량 운행 및 연료 기록부</p>', unsafe_allow_html=True)

# 3. 구글 시트 연결 및 이전 거리 호출
conn = st.connection("gsheets", type=GSheetsConnection)

def get_last_dist(car_name):
    try:
        df = conn.read()
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            return int(car_df.iloc[-1]['종료거리'])
        return 0
    except: return 0

# 4. 운행 정보 입력
selected_date = st.date_input("📅 운행 날짜", datetime.now())
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)

driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("👤 운전자", driver_list)
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# 5. 주행 거리 입력
last_km = get_last_dist(selected_car)
col_start, col_end = st.columns(2)
with col_start:
    start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "통근노선 시작", "직접 입력"])
    if start_node == "직접 입력": start_node = st.text_input("출발지 상세")
    start_km = st.number_input("📍 시작 거리 (km)", value=last_km)
with col_end:
    end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점", "직접 입력"])
    if end_node == "직접 입력": end_node = st.text_input("목적지 상세")
    end_km = st.number_input("🏁 종료 거리 (km)", value=start_km, help="시작 거리보다 큰 값을 입력하세요")

st.divider()

# 6. 연료 주입 정보 (이미지 구성 반영)
st.markdown("### ⛽ 연료 및 요소수 주입")
fuel_needed = st.checkbox("오늘 연료나 요소수를 주입했나요?")

# 기본값 설정 (주입 안 했을 경우 시트에 '-' 또는 0으로 기록)
fuel_type = "-"
fuel_amount = 0
fuel_cost = 0

if fuel_needed:
    st.markdown('<div class="fuel-section">', unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        fuel_type = st.selectbox("종류", ["LPi", "경유", "요소수"])
    with f_col2:
        # LPi는 금액 위주, 경유/요소수는 리터 위주 입력 안내
        label = "주입금액(원)" if fuel_type == "LPi" else "주입량(L)"
        fuel_amount = st.number_input(label, min_value=0, step=1)
    with f_col3:
        fuel_cost = st.number_input("결제 총액(원)", min_value=0, step=1000)
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# 7. 운행 내용 및 비고
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "기타"])
memo = st.text_area("비고 (특이사항)", height=100)
total_distance = end_km - start_km

# 8. 저장 로직 (권한 오류 해결 버전)
if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
    elif not selected_driver:
        st.warning("운전자를 확인하세요.")
    else:
        try:
            # 신규 데이터 생성
            new_row = {
                "날짜": selected_date.strftime('%Y-%m-%d'),
                "차량": selected_car,
                "운전자": selected_driver,
                "출발지": start_node,
                "목적지": end_node,
                "시작거리": start_km,
                "종료거리": end_km,
                "주행거리": total_distance,
                "연료종류": fuel_type,
                "주입량": fuel_amount,
                "결제금액": fuel_cost,
                "운행내용": purpose,
                "비고": memo,
                "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # [수정된 부분] 명시적으로 데이터프레임을 읽어와서 합친 후 다시 씁니다.
            existing_df = conn.read(ttl=0) # 캐시 없이 즉시 읽기
            updated_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
            
            # 다시 쓰기 시도
            conn.update(data=updated_df)
            
            st.success("저장 완료!")
            st.balloons()
            st.rerun() # 저장 후 화면 갱신
            
        except Exception as e:
            st.error(f"저장 실패: {e}")
            st.info("💡 만약 이 오류가 계속된다면, Streamlit Cloud의 'Secrets' 설정에서 시트 URL이 정확한지 확인이 필요합니다.")

# 9. 최근 기록 보기
with st.expander("📊 최근 기록 보기"):
    try:
        history_df = conn.read()
        st.dataframe(history_df.tail(5).iloc[::-1], use_container_width=True)
    except:
        st.write("데이터가 없습니다.")
