import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정 및 모바일 최적화 스타일
st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# 모바일 가독성을 위한 최적화 CSS
st.markdown("""
    <style>
    .main-title {
        font-size: 22px !important;
        font-weight: bold;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
    }
    .stHeader { font-size: 18px !important; }
    /* 안내 문구(Caption) 스타일 강조 */
    .stCaption {
        font-size: 13px !important;
        color: #FF4B4B !important;
        margin-top: -15px !important;
        margin-bottom: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 전우정밀 로고 및 제목
col1, col2 = st.columns([1, 4])
with col1:
    try:
        st.image("logo.png", width=55)
    except:
        st.write("🏢")

with col2:
    st.markdown('<p class="main-title">전우정밀 차량 운행 기록부</p>', unsafe_allow_html=True)

# 3. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_last_dist(car_name):
    try:
        df = conn.read()
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            return int(car_df.iloc[-1]['종료거리'])
        return 0
    except:
        return 0

# 4. 상단 기본 정보
selected_date = st.date_input("📅 운행 날짜", datetime.now())

car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)

driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("👤 운전자", driver_list)
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# 5. 주행 정보 입력 (가이드 문구 포함)
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
    # [핵심] 입력창 바로 아래에 상시 노출되는 붉은색 계열 가이드 문구
    st.caption(f"⚠️ {start_km}km 이상 입력하세요")

st.divider()

# 6. 운행 내용 및 기타
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "기타"])
memo = st.text_area("비고 (특이사항)", height=80, placeholder="주유 기록이나 차량 특이사항을 적어주세요.")

total_distance = end_km - start_km

# 7. 기록 저장 기능
if st.button("🚀 운행 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error(f"입력 오류: 종료 거리({end_km}km)가 시작 거리({start_km}km)보다 작습니다!")
    elif not selected_driver:
        st.warning("운전자를 입력하거나 선택해주세요.")
    else:
        try:
            # 새로운 행 데이터 생성
            new_row = pd.DataFrame([{
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
            }])
            
            # 기존 데이터 로드 후 합치기
            existing_df = conn.read()
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            
            # 구글 시트 업데이트
            conn.update(data=updated_df)
            
            st.success(f"✅ {total_distance}km 주행 기록이 저장되었습니다!")
            st.balloons()
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다: {e}")

# 8. 하단 최근 이력 (모바일 공간 절약을 위해 간소화)
with st.expander("📊 최근 기록 (5건)"):
    try:
        history = conn.read()
        st.dataframe(history.tail(5).iloc[::-1], use_container_width=True)
    except:
        st.write("기록이 없습니다.")
