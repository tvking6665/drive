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
    "7.5톤": "7.5톤(파비스)",
    "2.5톤": "2.5톤(마이티)",
    "1톤": "1톤(포터)",
    "통근차": "통근차(솔라티)"
}

CAR_FULL_NAME_MAP = {
    "7.5톤": "7.5톤(파비스) 3528",
    "2.5톤": "2.5톤(마이티) 8569",
    "1톤": "1톤(포터) 5378",
    "통근차": "통근차(솔라티) 8740"
}
REVERSE_CAR_MAP = {v: k for k, v in CAR_FULL_NAME_MAP.items()}

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

    # 데이터 실시간 로드 함수
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

    if "form_version" not in st.session_state:
        st.session_state.form_version = 0
        
    v = st.session_state.form_version

    # -------------------------------------------------------------------------
    # [실시간 반응 UI] 
    # -------------------------------------------------------------------------
    selected_date = st.date_input("📅 운행 및 주유 날짜", datetime.now(), key=f"date_{v}")
    
    # 1. 운전자 선택 및 입력
    selected_driver_base = st.session_state.user_name if st.session_state.user_name != "관리자" else "목록에서 선택"
    if selected_driver_base == "목록에서 선택":
        selected_driver_base = st.selectbox("👤 운전자 선택", ["김동현", "김태종", "이학장"], key=f"driver_sel_{v}")
    
    custom_driver_name = st.text_input("✍️ [목록에 이름이 없는 분만] 운전자 성명 직접 입력", placeholder="예: 박준석", key=f"driver_txt_{v}")
    selected_driver = custom_driver_name.strip() if custom_driver_name.strip() != "" else selected_driver_base

    # 2. 차량 선택
    ui_car_list = ["7.5톤", "2.5톤", "1톤", "통근차"]
    default_car_index = 0
    if selected_driver in DRIVER_DEFAULT_CAR:
        target_car = DRIVER_DEFAULT_CAR[selected_driver]
        if target_car in ui_car_list:
            default_car_index = ui_car_list.index(target_car)

    selected_car_ui = st.selectbox("🚗 차량 선택", ui_car_list, index=default_car_index, key=f"car_sel_{v}")
    display_car_name = CAR_MAP[selected_car_ui]
    actual_car_name = CAR_FULL_NAME_MAP[selected_car_ui]

    last_km = get_last_dist(actual_car_name)

    # 3. 출발지 및 목적지 선택 UI
    col_ui_start, col_ui_end = st.columns(2)
    with col_ui_start:
        start_node = st.selectbox("📍 출발지 선택", ["회사", "통근노선 시작"], key=f"start_sel_{v}")
        custom_start_node = st.text_input("✍️ [기타 장소 출발시] 출발지 직접 입력", placeholder="예: 외주공장명, 주소 등", key=f"start_txt_{v}")
        final_start_node = custom_start_node.strip() if custom_start_node.strip() != "" else ("회사(전우정밀)" if start_node == "회사" else start_node)

    with col_ui_end:
        end_node = st.selectbox("🎯 목적지 선택", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점"], key=f"end_sel_{v}")
        custom_end_node = st.text_input("✍️ [기타 장소 도착시] 목적지 직접 입력", placeholder="예: 거래처명, 주소 등", key=f"end_txt_{v}")
        final_end_node = custom_end_node.strip() if custom_end_node.strip() != "" else end_node

    # 4. 운행 내용 선택
    purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "주유", "기타"], key=f"purpose_{v}")

    # 5. 비고(특이사항) 체크박스 및 입력창
    show_memo = st.checkbox("📝 비고(특이사항) 작성하기", key=f"memo_chk_{v}")
    memo = ""
    if show_memo:
        memo = st.text_area("특이사항 내용을 입력하세요", placeholder="예: 주유 정산 필요, 차량 소음 발생 등", height=100, key=f"memo_txt_{v}")

    # -------------------------------------------------------------------------
    # 메인 입력 폼 섹션 (숫자 입력 및 데이터 최종 저장)
    # -------------------------------------------------------------------------
