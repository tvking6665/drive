import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 시스템", layout="centered")

# 사용자 정의 스타일 (모바일 최적화)
st.markdown("""
    <style>
    .main-title { font-size: 24px !important; font-weight: bold; margin-bottom: 10px; display: flex; align-items: center; }
    .login-box { padding: 20px; border-radius: 10px; background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# 2. 로그인 데이터 설정
USER_LIST = ["선택하세요", "관리자", "김태종", "김동현", "이학장"]
USER_PW = {
    "관리자": "1111",
    "김태종": "0000",
    "김동현": "0000",
    "이학장": "0000"
}

# 로그인 상태 관리 함수
def check_login():
    if "login_success" not in st.session_state:
        st.session_state.login_success = False

    if not st.session_state.login_success:
        st.markdown('<p class="main-title">🔐 업무 시스템 로그인</p>', unsafe_allow_html=True)
        
        with st.container():
            # 드롭박스 형태로 사용자 선택
            selected_user = st.selectbox("사용자 이름을 선택하세요", USER_LIST)
            # 비밀번호 입력 (입력 시 **** 로 표시)
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
    # 로그아웃 버튼 (상단 사이드바)
    if st.sidebar.button("로그아웃"):
        st.session_state.login_success = False
        st.rerun()

    # --- 여기서부터 기존 차량 운행 기록부 코드 ---
    
    col1, col2 = st.columns([1, 4])
    with col1:
        try:
            st.image("logo.png", width=60)
        except:
            st.write("🏢")

    with col2:
        st.markdown(f'<p class="main-title">차량 운행 기록부 ({st.session_state.user_name}님)</p>', unsafe_allow_html=True)

    # 구글 시트 연결
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

    selected_date = st.date_input("📅 운행 날짜", datetime.now())
    car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
    selected_car = st.selectbox("🚗 차량 선택", car_list)

    # 운전자는 로그인한 정보로 자동 세팅하거나 선택 가능
    selected_driver = st.session_state.user_name if st.session_state.user_name != "관리자" else "직접 입력"
    if selected_driver == "직접 입력":
        selected_driver = st.selectbox("👤 운전자 선택", ["김동현", "김태종", "이학장", "직접 입력"])
        if selected_driver == "직접 입력":
            selected_driver = st.text_input("운전자 성명 입력")

    st.divider()

    last_km = get_last_dist(selected_car)
    col_start, col_end = st.columns(2)
    with col_start:
        start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "통근노선 시작", "직접 입력"])
        if start_node == "직접 입력": start_node = st.text_input("출발지 상세")
        start_km = st.number_input("📍 시작 거리 (km)", value=last_km)

    with col_end:
        end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점", "직접 입력"])
        if end_node == "직접 입력": end_node = st.text_input("목적지 상세")
        # Placeholder 안내 문구 추가
        end_km = st.number_input("🏁 종료 거리 (km)", value=start_km, help="시작 거리보다 큰 값을 입력하세요")

    st.divider()

    purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "기타"])
    memo = st.text_area("비고 (특이사항)", height=100)
    total_distance = end_km - start_km

    if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
        if end_km < start_km:
            st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
        else:
            try:
                new_data = pd.DataFrame([{
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
                existing_df = conn.read()
                updated_df = pd.concat([existing_df, new_data], ignore_index=True)
                conn.update(data=updated_df)
                st.success("저장 완료!")
                st.balloons()
            except Exception as e:
                st.error(f"오류: {e}")

    with st.expander("📊 최근 기록 보기"):
        try:
            history_df = conn.read()
            st.dataframe(history_df.tail(5).iloc[::-1], use_container_width=True)
        except:
            st.write("데이터가 없습니다.")
