import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json
import numpy as np

# 0. 핵심 연동 주소 설정
SHEET_ID = "1_4z6RBNn8HQ1_xfznsITZ0yGWu5xpP-BYDmOdi_ftaE"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzLMy1LMbCp-SpIC-ZGkGJS8ZeXkQ_xhzYwJPYD2YtSf9bZuwoNiDZ-KCFpuhv0AdAc/exec"

# 1. 페이지 설정 및 스타일
st.set_page_config(page_title="전우정밀 시스템", layout="centered")

st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; }
    div[data-testid="stExpander"] div[role="button"] p { font-weight: bold; color: #2e7d32; }
    div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 사원 로그인 데이터 설정
USER_LIST = ["선택하세요", "관리자", "김태종", "김동현", "이학장"]
USER_PW = {
    "관리자": "1111",
    "김태종": "0000",
    "김동현": "0000",
    "이학장": "0000"
}

CAR_MAP = {
    "7.5톤": "7.5톤(파비스) 3528",
    "2.5톤": "2.5톤(마이티) 8569",
    "1톤": "1톤(포터) 5378",
    "통근차": "통근차(솔라티) 8740"
}
REVERSE_CAR_MAP = {v: k for k, v in CAR_MAP.items()}

DRIVER_DEFAULT_CAR = {
    "김동현": "7.5톤",
    "김태종": "1톤",
    "이학장": "1톤"
}

def check_login():
    if "login_success" not in st.session_state:
        st.session_state.login_success = False

    if not st.session_state.login_success:
        st.markdown('<p class="main-title">🔐 업무 시스템 로그인</p>', unsafe_allow_html=True)
        
        with st.container():
            selected_user = st.selectbox("사용자 이름을 선택하세요", USER_LIST)
            input_pw = st.text_input("비밀번호를 입력하세요", type="password")
            
            if st.button("로그인", use_container_width=True, type="primary"):
                if selected_user == "선택하세요":
                    st.warning("사용자를 먼저 선택해주세요.")
                elif USER_PW.get(selected_user) == input_pw:
                    st.session_state.login_success = True
                    st.session_state.user_name = selected_user
                    st.rerun()
                else:
                    st.error("비밀번호가 일치하지 않습니다.")
        return False
    return True

if check_login():
    if st.sidebar.button("로그아웃"):
        st.session_state.login_success = False
        st.rerun()

    col1, col2 = st.columns([1, 4])
    with col1:
        st.write("🏢")
    with col2:
        st.markdown(f'<p class="main-title">차량 운행 및 주유 기록부 ({st.session_state.user_name}님)</p>', unsafe_allow_html=True)

    # 데이터 실시간 로드 함수 (시간초 캐시 버스팅 강화)
    @st.cache_data(ttl=0)
    def load_live_data(timestamp):
        try:
            df = pd.read_csv(f"{CSV_URL}&timestamp={timestamp}")
            int_columns = ["시작거리", "종료거리", "주행거리", "주입량", "결제금액"]
            for col in int_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
            df = df.replace({np.nan: ""})
            if "주입량" in df.columns:
                df["주입량"] = df["주입량"].replace({0: ""})
            if "결제금액" in df.columns:
                df["결제금액"] = df["결제금액"].replace({0: ""})
                
            return df
        except Exception as e:
            return pd.DataFrame(columns=["날짜", "차량", "운전자", "출발지", "목적지", "시작거리", "종료거리", "주행거리", "운행내용", "비고", "입력시간", "연료종류", "주입량", "결제금액"])

    # 강제 리프레시용 타임스탬프 발행
    current_ts = datetime.now().timestamp()
    
    def get_last_dist(car_full_name):
        try:
            df = load_live_data(current_ts)
            car_df = df[df['차량'] == car_full_name]
            if not car_df.empty:
                return int(car_df.iloc[-1]['종료거리'])
            return 0
        except:
            return 0

    def highlight_reconstructed(row):
        if str(row['연료종류']).strip() != "":
            return ['background-color: #fff9c4; color: black; font-weight: bold;'] * len(row)
        return [''] * len(row)

    if "submit_disabled" not in st.session_state:
        st.session_state.submit_disabled = False

    # -------------------------------------------------------------------------
    # [버그 해결 핵심] 실시간 반응이 필요한 차량 및 운전자 선택 UI를 Form 외부로 분리
    # -------------------------------------------------------------------------
    selected_date = st.date_input("📅 운행 및 주유 날짜", datetime.now())
    
    # 운전자 선택 UI
    selected_driver_base = st.session_state.user_name if st.session_state.user_name != "관리자" else "목록에서 선택"
    if selected_driver_base == "목록에서 선택":
        selected_driver_base = st.selectbox("👤 운전자 선택", ["김동현", "김태종", "이학장", "목록에 없음 (직접입력)"])
    
    # 키패드 상시 활성화를 위한 입력창
    custom_driver_name = st.text_input("✍️ [목록에 없음 선택시] 운전자 성명을 직접 입력하세요", placeholder="예: 김xx")
    
    if selected_driver_base == "목록에 없음 (직접입력)":
        selected_driver = custom_driver_name.strip()
    else:
        selected_driver = selected_driver_base

    # 차량 선택 및 인덱스 처리
    ui_car_list = ["7.5톤", "2.5톤", "1톤", "통근차"]
    default_car_index = 0
    
    if selected_driver in DRIVER_DEFAULT_CAR:
        target_car = DRIVER_DEFAULT_CAR[selected_driver]
        if target_car in ui_car_list:
            default_car_index = ui_car_list.index(target_car)

    selected_car_ui = st.selectbox("🚗 차량 선택", ui_car_list, index=default_car_index)
    actual_car_name = CAR_MAP[selected_car_ui]

    # Form 외부에 있으므로 차량이 바뀔 때마다 하단의 last_km가 실시간으로 재계산됩니다.
    last_km = get_last_dist(actual_car_name)

    # -------------------------------------------------------------------------
    # 메인 입력 폼 섹션 (나머지 입력 및 저장 기능)
    # -------------------------------------------------------------------------
    with st.form(key="vehicle_form", clear_on_submit=False):
        
        st.markdown(f"**선택된 차량:** {actual_car_name} (최종 종료거리: {last_km:,} km)")
        st.divider()

        col_start, col_end = st.columns(2)
        with col_start:
            start_node = st.selectbox("📍 출발지", ["회사", "통근노선 시작", "직접 입력"])
            if start_node == "직접 입력": 
                start_node = st.text_input("출발지 상세")
            # 완벽하게 연동된 실시간 마일리지를 기본값으로 주입
            start_km = st.number_input("📍 시작 거리 (km)", value=last_km, step=1)

        with col_end:
            end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점", "직접 입력"])
            if end_node == "직접 입력": 
                end_node = st.text_input("목적지 상세")
            end_km = st.number_input("🏁 종료 거리 (km)", value=start_km, step=1, help="시작 거리보다 큰 값을 입력하세요")

        total_distance = end_km - start_km

        st.divider()

        st.markdown("### ⛽ 주유 기록 (선택 입력)")
        col_fuel1, col_fuel2, col_fuel3 = st.columns(3)
        
        with col_fuel1:
            fuel_type = st.selectbox("연료 종류", ["없음", "경유", "LPG", "요소수"])
        with col_fuel2:
            fuel_amount = st.number_input("주입량 (L)", min_value=0, value=0, step=1)
        with col_fuel3:
            fuel_price = st.number_input("결제 금액 (원)", min_value=0, value=0, step=1000)

        st.divider()

        purpose = st.selectbox("📝 운행 내용",
