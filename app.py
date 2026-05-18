import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# 0. 핵심 연동 주소 설정 (발급받으신 URL 반영 완료)
SHEET_ID = "1_4z6RBNn8HQ1_xfznsITZ0yGWu5xpP-BYDmOdi_ftaE"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyHCo5nOvml1M7bQEfcnjYU8jN5IX12CfWucqxv9E3jUgpAZtX7ApHyrmLZj_xUD9GX/exec"

# 1. 페이지 설정 및 모바일 최적화 스타일
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
    # 로그아웃 버튼 (상단 사이드바)
    if st.sidebar.button("로그아웃"):
        st.session_state.login_success = False
        st.rerun()

    col1, col2 = st.columns([1, 4])
    with col1:
        st.write("🏢")
    with col2:
        st.markdown(f'<p class="main-title">차량 운행 기록부 ({st.session_state.user_name}님)</p>', unsafe_allow_html=True)

    # 데이터 실시간 로드 함수 (캐시 방지 적용)
    @st.cache_data(ttl=0)
    def load_live_data():
        try:
            # 실시간 동기화를 위해 타임스탬프 파라미터 강제 추가
            return pd.read_csv(f"{CSV_URL}&timestamp={datetime.now().timestamp()}")
        except Exception as e:
            # 예외 발생 시 기본 스키마 반환
            return pd.DataFrame(columns=["날짜", "차량", "운전자", "출발지", "목적지", "시작거리", "종료거리", "주행거리", "운행내용", "비고", "입력시간"])

    def get_last_dist(car_name):
        try:
            df = load_live_data()
            car_df = df[df['차량'] == car_name]
            if not car_df.empty:
                return int(car_df.iloc[-1]['종료거리'])
            return 0
        except:
            return 0

    # 입력 UI 구성
    selected_date = st.date_input("📅 운행 날짜", datetime.now())
    car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
    selected_car = st.selectbox("🚗 차량 선택", car_list)

    selected_driver = st.session_state.user_name if st.session_state.user_name != "관리자" else "직접 입력"
    if selected_driver == "직접 입력":
        selected_driver = st.selectbox("👤 운전자 선택", ["김동현", "김태종", "이학장", "직접 입력"])
        if selected_driver == "직접 입력":
            selected_driver = st.text_input("운전자 성명 입력")

    st.divider()

    # 차량 변경 시 최근 종료 거리를 가져와 시작 거리로 자동 바인딩
    last_km = get_last_dist(selected_car)
    
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

    st.divider()

    purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "기타"])
    memo = st.text_area("비고 (특이사항)", height=100)
    total_distance = end_km - start_km

    # 4. 기록 저장 로직 (Google Apps Script API 전송)
    if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
        if end_km < start_km:
            st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
        else:
            try:
                payload = {
                    "날짜": selected_date.strftime('%Y-%m-%d'),
                    "차량": selected_car,
                    "운전자": selected_driver,
                    "출발지": start_node,
                    "목적지": end_node,
                    "시작거리": int(start_km),
                    "종료거리": int(end_km),
                    "주행거리": int(total_distance),
                    "운행내용": purpose,
                    "비고": memo,
                    "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Apps Script 웹앱 엔드포인트로 JSON 데이터 전송
                response = requests.post(WEB_APP_URL, data=json.dumps(payload))
                
                if response.status_code == 200:
                    st.success("구글 스프레드시트에 성공적으로 저장되었습니다!")
                    st.balloons()
                    # 하단 뷰어 새로고침을 위한 캐시 클리어 후 리런
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"저장 실패 (서버 응답 코드: {response.status_code})")
            except Exception as e:
                st.error(f"연결 오류가 발생했습니다: {e}")

    # 5. 최신 데이터 테이블 뷰어 (최신 등록 데이터가 맨 위로)
    with st.expander("📊 최근 운행 기록 보기 (최신순 5개)"):
        try:
            history_df = load_live_data()
            if not history_df.empty:
                st.dataframe(history_df.tail(5).iloc[::-1], use_container_width=True)
            else:
                st.info("표시할 운행 기록이 없습니다.")
        except Exception as e:
            st.write("데이터를 불러오는 중입니다...")
