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

# 차량 이름 변환 딕셔너리
CAR_MAP = {
    "7.5톤": "7.5톤(파비스) 3528",
    "2.5톤": "2.5톤(마이티) 8569",
    "1톤": "1톤(포터) 5378",
    "통근차": "통근차(솔라티) 8740"
}
REVERSE_CAR_MAP = {v: k for k, v in CAR_MAP.items()}

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

# 3. 메인 화면 (로그인 성공 시 실행)
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
    def load_live_data():
        try:
            df = pd.read_csv(f"{CSV_URL}&timestamp={datetime.now().timestamp()}")
            
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

    def get_last_dist(car_full_name):
        try:
            df = load_live_data()
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

    # 입력 UI 구성
    selected_date = st.date_input("📅 운행 및 주유 날짜", datetime.now())
    ui_car_list = ["7.5톤", "2.5톤", "1톤", "통근차"]
    selected_car_ui = st.selectbox("🚗 차량 선택", ui_car_list)
    
    actual_car_name = CAR_MAP[selected_car_ui]

    selected_driver = st.session_state.user_name if st.session_state.user_name != "관리자" else "직접 입력"
    if selected_driver == "직접 입력":
        selected_driver = st.selectbox("👤 운전자 선택", ["김동현", "김태종", "이학장", "직접 입력"])
        if selected_driver == "직접 입력":
            selected_driver = st.text_input("운전자 성명 입력")

    st.divider()

    # 주행 거리 정보
    last_km = get_last_dist(actual_car_name)
    
    col_start, col_end = st.columns(2)
    with col_start:
        start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "통근노선 시작", "직접 입력"])
        if start_node == "직접 입력": 
            start_node = st.text_input("출발지 상세")
        start_km = st.number_input("📍 시작 거리 (km)", value=last_km, step=1)

    with col_end:
        end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점", "직접 입력"])
        if end_node == "직접 입력": 
            end_node = st.text_input("목적지 상세")
        end_km = st.number_input("🏁 종료 거리 (km)", value=start_km, step=1, help="시작 거리보다 큰 값을 입력하세요")

    total_distance = end_km - start_km

    st.divider()

    # 주유 및 연료 기록 섹션
    st.markdown("### ⛽ 주유 기록 (선택 입력)")
    col_fuel1, col_fuel2, col_fuel3 = st.columns(3)
    
    with col_fuel1:
        fuel_type = st.selectbox("연료 종류", ["없음", "경유", "LPG", "요소수"])
    with col_fuel2:
        fuel_amount = st.number_input("주입량 (L)", min_value=0, value=0, step=1)
    with col_fuel3:
        fuel_price = st.number_input("결제 금액 (원)", min_value=0, value=0, step=1000)

    st.divider()

    purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "주유", "기타"])
    
    # ✨ [신규 업그레이드] 비고 선택형 체크박스 연동
    show_memo = st.checkbox("📝 비고(특이사항) 작성하기")
    memo = ""
    if show_memo:
        memo = st.text_area("특이사항 내용을 입력하세요", height=100)

    # 4. 기록 저장 로직
    if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
        if end_km < start_km:
            st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
        else:
            try:
                payload = {
                    "날짜": selected_date.strftime('%Y-%m-%d'),
                    "차량": actual_car_name,
                    "운전자": selected_driver,
                    "출발지": start_node,
                    "목적지": end_node,
                    "시작거리": int(start_km),
                    "종료거리": int(end_km),
                    "주행거리": int(total_distance),
                    "운행내용": purpose,
                    "비고": memo,
                    "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "연료종류": fuel_type if fuel_type != "없음" else "", 
                    "주입량": int(fuel_amount) if fuel_amount > 0 else "",
                    "결제금액": int(fuel_price) if fuel_price > 0 else ""
                }
                
                response = requests.post(WEB_APP_URL, data=json.dumps(payload))
                
                if response.status_code == 200:
                    st.success("구글 스프레드시트에 성공적으로 저장되었습니다!")
                    st.balloons()
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"저장 실패 (서버 응답 코드: {response.status_code})")
            except Exception as e:
                st.error(f"연결 오류가 발생했습니다: {e}")

    # 5. 차량별 필터 및 데이터 테이블 뷰어 (열 순서 조정 완료)
    with st.expander("📊 최근 운행 및 주유 기록 보기 (차량별 필터 지원)"):
        try:
            history_df = load_live_data()
            
            if not history_df.empty:
                filter_options = ["전체 보기"] + ui_car_list
                selected_filter = st.selectbox("🔍 조회할 차량을 선택하세요", filter_options, key="view_filter")
                
                history_df['차량'] = history_df['차량'].map(REVERSE_CAR_MAP).fillna(history_df['차량'])
                
                if selected_filter != "전체 보기":
                    display_df = history_df[history_df['차량'] == selected_filter]
                else:
                    display_df = history_df
                
                if not display_df.empty:
                    # ✨ [순서 변경] 주행거리가 시작거리와 종료거리 바로 앞에 오도록 배열 배치 변경
                    base_cols = ["날짜", "차량", "주행거리", "시작거리", "종료거리", "운전자", "출발지", "목적지", "운행내용", "비고", "연료종류", "주입량", "결제금액", "입력시간"]
                    target_cols = [c for c in base_cols if c in display_df.columns]
                    display_df = display_df[target_cols]
                    
                    final_df = display_df.tail(5).iloc[::-1]
                    
                    styled_df = final_df.style.apply(highlight_reconstructed, axis=1)
                    st.dataframe(styled_df, use_container_width=True)
                else:
                    st.info(f"'{selected_filter}'의 운행 기록이 존재하지 않습니다.")
            else:
                st.info("표시할 기록이 없습니다.")
        except Exception as e:
            st.write("데이터를 불러오는 중입니다...")
