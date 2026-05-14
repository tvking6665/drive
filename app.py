import streamlit as st
import pandas as pd
from datetime import datetime
import requests # 직접 시트에 쓰기 위해 추가

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# CSS 및 로고 설정 (기존과 동일)
st.markdown("""<style>.main-title {font-size: 22px !important; font-weight: bold; margin-bottom: 5px; display: flex; align-items: center;} .stCaption {font-size: 13px !important; color: #FF4B4B !important; margin-top: -15px !important; margin-bottom: 10px !important;}</style>""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 4])
with col1:
    try: st.image("logo.png", width=55)
    except: st.write("🏢")
with col2: st.markdown('<p class="main-title">전우정밀 차량 운행 기록부</p>', unsafe_allow_html=True)

# 2. 구글 시트 정보 (중요: image_ae5e80.png의 그 시트 주소)
SHEET_ID = '1_4z6RBNn8HQ1_xfznsITZ0yGWu5xpP-BYDmOdi_ftaE'
# 데이터를 읽어오기 위한 주소
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

def get_last_dist(car_name):
    try:
        df = pd.read_csv(READ_URL)
        car_df = df[df['차량'] == car_name]
        if not car_df.empty: return int(car_df.iloc[-1]['종료거리'])
        return 0
    except: return 0

# 3. 입력 섹션
selected_date = st.date_input("📅 운행 날짜", datetime.now())
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)
driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("👤 운전자", driver_list)
if selected_driver == "직접 입력": selected_driver = st.text_input("운전자 성명 입력")

st.divider()

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
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "기타"])
memo = st.text_area("비고 (특이사항)", height=80)

# 4. 저장 기능 (라이브러리 충돌 없는 방식)
if st.button("🚀 운행 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("입력 오류: 종료 거리가 시작 거리보다 작습니다!")
    elif not selected_driver:
        st.warning("운전자를 입력해주세요.")
    else:
        try:
            # 폼 데이터를 구글 시트에 직접 전송하는 가장 확실한 방법은 
            # 구글 앱스 스크립트(Apps Script)를 사용하는 것이지만, 
            # 우선 라이브러리 설정을 다시 한번 초기화하는 방식으로 시도합니다.
            
            from streamlit_gsheets import GSheetsConnection
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            new_row = pd.DataFrame([{
                "날짜": selected_date.strftime('%Y-%m-%d'), "차량": selected_car,
                "운전자": selected_driver, "출발지": start_node, "목적지": end_node,
                "시작거리": start_km, "종료거리": end_km, "주행거리": end_km - start_km,
                "운행내용": purpose, "비고": memo, "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])
            
            df = conn.read()
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success("✅ 저장 성공!")
            st.balloons()
        except Exception as e:
            st.error("보안 정책으로 인해 직접 저장이 차단되었습니다.")
            st.info("💡 해결법: 시트 공유 설정에서 '편집자'로 되어있음에도 안된다면, Streamlit 대시보드에서 앱을 'Reboot' 하거나 Secrets 설정을 다시 확인해야 합니다.")

with st.expander("📊 최근 기록"):
    try:
        history = pd.read_csv(READ_URL)
        st.dataframe(history.tail(5).iloc[::-1], use_container_width=True)
    except: st.write("기록이 없습니다.")
