import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 페이지 설정
st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# 전문가용 앱 느낌을 주는 CSS (이미지 image_af2c42.jpg 스타일 참고)
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #F5F7F9; }
    .main-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .car-badge {
        background-color: #EEF2FF;
        color: #4F46E5;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_last_info(car_name):
    try:
        df = conn.read()
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            return car_df.iloc[-1]
        return None
    except: return None

# 상단 로고 및 타이틀
col1, col2 = st.columns([1, 5])
with col1: st.image("logo.png", width=50)
with col2: st.markdown("### 법인 차량 관리")

# 카드형 레이아웃 시작
st.markdown('<div class="main-card">', unsafe_allow_html=True)

# 1. 차량 선택 및 마지막 정보 확인
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)

last_info = get_last_info(selected_car)
if last_info is not None:
    st.markdown(f'<span class="car-badge">직전 종료거리: {last_info["종료거리"]} km</span>', unsafe_allow_html=True)
    with st.expander("🔍 직전 운행 정보 보기"):
        st.write(f"최종 운전자: {last_info['운전자']}")
        st.write(f"최종 목적지: {last_info['목적지']}")

st.divider()

# 2. 운행 정보 입력
driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("👤 운전자 성명", driver_list)

col_s, col_e = st.columns(2)
with col_s:
    start_km = st.number_input("시작 거리 (km)", value=int(last_info['종료거리']) if last_info is not None else 0)
with col_e:
    end_km = st.number_input("종료 거리 (km)", value=start_km, help=f"{start_km} 이상 입력")

purpose = st.text_input("운행 내용 (목적지 등)", placeholder="예: 거래처 미팅, 현장 방문 등")

st.markdown('</div>', unsafe_allow_html=True) # 카드 닫기

# 3. 저장 버튼 (강조)
if st.button("✅ 차량 운행 정보 입력", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작습니다.")
    else:
        # (저장 로직 생략 - 이전과 동일)
        st.success("운행 정보가 기록되었습니다!")
