import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
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
    .summary-box { background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 5px solid #1976d2; margin-bottom: 15px; }
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

# 실제 운행하시는 4대 체제 맵핑
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

    # 데이터 실시간 로드 함수 (순서 고정 및 에러 방지 강화)
    @st.cache_data(ttl=0)
    def load_live_data(timestamp):
        try:
            df = pd.read_csv(f"{CSV_URL}&timestamp={timestamp}")
            
            # 숫자형 데이터 변환 전처리 강화
            int_columns = ["시작거리", "종료거리", "주행거리", "주입량", "결제금액"]
            for col in int_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
            # 숫자가 아닌 나머지 열의 빈값(NaN)만 안전하게 빈 문자열 처리
            string_cols = [c for c in df.columns if c not in int_columns]
            for col in string_cols:
                df[col] = df[col].fillna("").astype(str)
                
            return df
        except Exception as e:
            return pd.DataFrame(columns=["날짜", "차량", "운전자", "출발지", "목적지", "시작거리", "종료거리", "주행거리", "운행내용", "비고", "입력시간", "연료종류", "주입량", "결제금액"])

    # 현재 시각 구하기 (한국 시간 기준 적용)
    kst_now = datetime.now(ZoneInfo("Asia/Seoul"))
    current_ts = kst_now.timestamp()
    
    # 실시간 원본 데이터 가져오기
    live_df = load_live_data(current_ts)
    
    # [완전 보완] 공백 제거 및 포함 조건식 정밀 매칭
    def get_last_dist(car_ui_key):
        try:
            if live_df.empty or '차량' not in live_df.columns:
                return 0
                
            full_name = CAR_FULL_NAME_MAP.get(car_ui_key, "")
            short_name = CAR_MAP.get(car_ui_key, car_ui_key)
            
            # 시트 내 텍스트 공백 부조화 문제를 해결하기 위해 양끝 공백을 자르고 비교
            # "1톤", "1톤(포터)", "1톤(포터) 5378" 중 하나라도 걸리면 매칭되도록 보완
            car_df = live_df[
                live_df['차량'].str.strip().str.contains(car_ui_key, na=False) | 
                live_df['차량'].str.strip().str.contains(short_name, na=False) | 
                live_df['차량'].str.strip().str.contains(full_name, na=False)
            ]
            
            if not car_df.empty:
                # 가장 마지막 기록의 종료거리 컬럼 값 추출
                last_val = car_df.iloc[-1]['종료거리']
                if pd.notna(last_val) and str(last_val).strip() != "" and str(last_val).strip() != "0":
                    return int(last_val)
            return 0
        except Exception as e:
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
    # [실시간 반응 UI 및 메인 입력 폼]
    # -------------------------------------------------------------------------
    selected_date = st.date_input("📅 운행 및 주유 날짜", kst_now, key=f"date_{v}")
    
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

    # [중요 수정] 선택창의 순수 키 문자열("1톤", "2.5톤" 등)을 사용하여 최신 종료거리 함수 호출
    last_km = get_last_dist(selected_car_ui)

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

    with st.form(key=f"vehicle_form_{v}", clear_on_submit=False):
        
        st.markdown(f"**선택 차량:** {display_car_name} | **출발:** {final_start_node} ➔ **도착:** {final_end_node}")
        st.divider()

       col_start, col_end = st.columns(2)
        with col_start:
            # key에 selected_car_ui를 결합하여 차량이 바뀔 때마다 입력창을 실시간으로 새로 갱신하게 만듭니다.
            start_km = st.number_input(
                "📍 시작 거리 (km)", 
                value=int(last_km), 
                step=1, 
                key=f"start_km_{selected_car_ui}_{v}"
            )
        with col_end:
            # 종료 거리도 시작 거리에 연동되어 함께 리셋되도록 key를 맞춰줍니다.
            end_km = st.number_input(
                "🏁 종료 거리 (km)", 
                value=int(start_km), 
                step=1, 
                help="시작 거리보다 큰 값을 입력하세요", 
                key=f"end_km_{selected_car_ui}_{v}"
            )

        total_distance = end_km - start_km

        st.divider()

        st.markdown("### ⛽ 주유 기록 (선택 입력)")
        col_fuel1, col_fuel2, col_fuel3 = st.columns(3)
        with col_fuel1:
            fuel_type = st.selectbox("연료 종류", ["없음", "경유", "LPG", "요소수"], key=f"fuel_type_{v}")
        with col_fuel2:
            fuel_amount = st.number_input("주입량 (L)", min_value=0, value=0, step=1, key=f"fuel_amt_{v}")
        with col_fuel3:
            fuel_price = st.number_input("결제 금액 (원)", min_value=0, value=0, step=1000, key=f"fuel_price_{v}")

        st.divider()

        submit_button = st.form_submit_button(
            label="🚀 기록 저장" if not st.session_state.submit_disabled else "⏳ 데이터 전송 및 저장 중...",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.submit_disabled
        )

        if submit_button:
            if not selected_driver:
                st.error("운전자 성명이 입력되지 않았습니다!")
            elif end_km < start_km:
                st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
            elif total_distance == 0:
                st.error("주행 거리가 0 km입니다! 종료 거리를 전일 거리보다 크게 수정 후 저장해 주세요.")
            else:
                st.session_state.submit_disabled = True
                
                with st.spinner("데이터가 저장되고 있습니다. 잠시만 기다려주세요..."):
                    try:
                        save_kst_time = datetime.now(ZoneInfo("Asia/Seoul")).strftime('%Y-%m-%d %H:%M:%S')
                        
                        payload = {
                            "날짜": selected_date.strftime('%Y-%m-%d'),
                            "차량": actual_car_name,
                            "운전자": selected_driver,
                            "출발지": final_start_node,
                            "목적지": final_end_node,
                            "시작거리": int(start_km),
                            "종료거리": int(end_km),
                            "주행거리": int(total_distance),
                            "운행내용": purpose,
                            "비고": memo,
                            "입력시간": save_kst_time,
                            "연료종류": fuel_type if fuel_type != "없음" else "", 
                            "주입량": int(fuel_amount) if fuel_amount > 0 else "",
                            "결제금액": int(fuel_price) if fuel_price > 0 else ""
                        }
                        
                        response = requests.post(WEB_APP_URL, data=json.dumps(payload))
                        
                        if response.status_code == 200:
                            st.toast("✅ 구글 스프레드시트에 성공적으로 저장되었습니다!")
                            st.cache_data.clear()
                            
                            st.session_state.form_version += 1
                            st.session_state.submit_disabled = False
                            st.rerun()
                        else:
                            st.error(f"저장 실패 (서버 응답 코드: {response.status_code})")
                            st.session_state.submit_disabled = False
                    except Exception as e:
                        st.error(f"연결 오류가 발생했습니다: {e}")
                        st.session_state.submit_disabled = False

    # -------------------------------------------------------------------------
    # 5. 차량별 실시간 누적 요약 표 (그랜저 제외 4대 체제)
    # -------------------------------------------------------------------------
    st.write("")
    st.markdown("---")
    
    show_summary_table = st.checkbox("📊 차량별 누적 요약 표 보기 (주행거리 / LPG금액 / 경유주입량)")
    
    if show_summary_table:
        st.markdown("<div class='summary-box'><h4>📈 차량별 실시간 누적 데이터 요약</h4></div>", unsafe_allow_html=True)
        
        if not live_df.empty:
            summary_records = []
            
            for car_key in ["7.5톤", "2.5톤", "1톤", "통근차"]:
                full_name = CAR_FULL_NAME_MAP[car_key]
                display_name = CAR_MAP[car_key]
                
                car_data = live_df[live_df['차량'].astype(str).str.contains(car_key, na=False)]
                
                # 1. 주행거리 합계
                total_dist = 0
                if '주행거리' in car_data.columns:
                    total_dist = pd.to_numeric(car_data['주행거리'], errors='coerce').fillna(0).sum()
                
                # 2. LPG 금액 합계
                lpg_amt = 0
                if '결제금액' in car_data.columns and '연료종류' in car_data.columns:
                    lpg_data = car_data[car_data['연료종류'].str.strip() == 'LPG']
                    lpg_amt = pd.to_numeric(lpg_data['결제금액'], errors='coerce').fillna(0).sum()
                
                # 3. 경유 주입량 합계
                diesel_liters = 0
                if '주입량' in car_data.columns and '연료종류' in car_data.columns:
                    diesel_data = car_data[car_data['연료종류'].str.strip() == '경유']
                    diesel_liters = pd.to_numeric(diesel_data['주입량'], errors='coerce').fillna(0).sum()
                
                summary_records.append({
                    "차종": display_name,
                    "주행거리": f"{int(total_dist):,} km",
                    "LPG금액": f"{int(lpg_amt):,} 원" if lpg_amt > 0 else "-",
                    "경유주입량": f"{int(diesel_liters):,} L" if diesel_liters > 0 else "-"
                })
            
            summary_df = pd.DataFrame(summary_records)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
        else:
            st.info("요약할 데이터가 아직 구글 시트에 없습니다.")
            
    # -------------------------------------------------------------------------
    # 6. 최근 기록 보기 테이블 뷰어 (그랜저 제외 고정)
    # -------------------------------------------------------------------------
    with st.expander("📊 최근 운행 및 주유 기록 보기", expanded=True):
        try:
            if not live_df.empty:
                filter_options = ["전체 보기"] + ["7.5톤", "2.5톤", "1톤", "통근차"]
                selected_filter = st.selectbox("🔍 조회할 차량을 선택하세요", filter_options, key="fixed_view_filter")
                
                history_df = live_df.copy()
                history_df['차량'] = history_df['차량'].map(REVERSE_CAR_MAP).fillna(history_df['차량'])
                
                if selected_filter != "전체 보기":
                    display_df = history_df[history_df['차량'] == selected_filter].copy()
                else:
                    display_df = history_df.copy()
                
                display_df['차량'] = display_df['차량'].map(CAR_MAP).fillna(display_df['차량'])
                display_df['출발지'] = display_df['출발지'].replace({"회사(전우정밀)": "회사"})
                
                if not display_df.empty:
                    base_cols = ["날짜", "운전자", "주행거리", "시작거리", "종료거리", "출발지", "목적지", "운행내용", "비고", "연료종류", "주입량", "결제금액", "차량", "입력시간"]
                    target_cols = [c for c in base_cols if c in display_df.columns]
                    display_df = display_df[target_cols]
                    
                    final_df = display_df.tail(5).iloc[::-1].copy()
                    
                    for dist_col in ["주행거리", "시작거리", "종료거리"]:
                        if dist_col in final_df.columns:
                            # 0이나 공백이 아니라면 단위 추가
                            final_df[dist_col] = final_df[dist_col].apply(lambda x: f"{int(x)} km" if x != "" and pd.notna(x) and x != 0 else "0 km")
                    
                    styled_df = final_df.style.apply(highlight_reconstructed, axis=1)
                    st.dataframe(styled_df, use_container_width=True)
                else:
                    st.info(f"'{CAR_MAP.get(selected_filter, selected_filter)}'의 운행 기록이 존재하지 않습니다.")
            else:
                st.info("표시할 기록이 없습니다.")
        except Exception as e:
            st.write("데이터를 불러오는 중입니다...")
