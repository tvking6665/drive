import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 차량 관리 시스템", layout="centered")

# 2. 헤더 구성
st.markdown('<h2 style="text-align: center;">🚗 차량 운행 및 연료 기록부</h2>', unsafe_allow_html=True)

# 3. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_last_dist(car_name):
    try:
        # 실시간 데이터 로드
        df = conn.read(ttl=0)
        
        if df.empty:
            return 0
            
        # 해당 차량 데이터만 필터링
        car_df = df[df['차량'] == car_name]
        
        if not car_df.empty:
            # 마지막 행의 '종료거리' 값을 가져옴
            last_val = car_df.iloc[-1]['종료거리']
            
            # [핵심 보강] 숫자로 변환 가능한 것만 추출 (글자나 공백은 NaN으로 변경 후 0 처리)
            num_val = pd.to_numeric(last_val, errors='coerce')
            
            if pd.isna(num_val):
                return 0
            return int(num_val)
            
        return 0
    except:
        return 0

# 4. 운행 정보 입력
selected_date = st.date_input("📅 날짜", datetime.now())
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)

driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("👤 운전자", driver_list)
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# 주행 거리 입력 (오류 방지용 int 변환 강화)
last_km = get_last_dist(selected_car)
c1, c2 = st.columns(2)
with c1:
    start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "통근노선 시작", "직접 입력"])
    if start_node == "직접 입력": start_node = st.text_input("출발지 상세")
    # value를 0 또는 숫자로 확실히 고정
    start_km = st.number_input("📍 시작 거리 (km)", value=int(last_km) if last_km else 0)
with c2:
    end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점", "직접 입력"])
    if end_node == "직접 입력": end_node = st.text_input("목적지 상세")
    end_km = st.number_input("🏁 종료 거리 (km)", value=int(start_km))

st.divider()

# 5. 연료 주입 정보
fuel_needed = st.checkbox("⛽ 오늘 연료나 요소수를 주입했나요?")
f_type, f_amt, f_cost = "-", 0, 0
if fuel_needed:
    fc1, fc2, fc3 = st.columns(3)
    with fc1: f_type = st.selectbox("종류", ["LPi", "경유", "요소수"])
    with fc2: f_amt = st.number_input("주입량", min_value=0)
    with fc3: f_cost = st.number_input("결제금액(원)", min_value=0)

st.divider()
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "기타"])
memo = st.text_area("비고 (특이사항)")

# 6. 저장 로직 (데이터 타입 강제 지정)
if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
    else:
        try:
            # 저장할 데이터를 딕셔너리로 구성 (타입 명시)
            data_to_add = {
                "날짜": str(selected_date.strftime('%Y-%m-%d')),
                "차량": str(selected_car),
                "운전자": str(selected_driver),
                "출발지": str(start_node),
                "목적지": str(end_node),
                "시작거리": int(start_km),
                "종료거리": int(end_km),
                "주행거리": int(end_km - start_km),
                "운행내용": str(purpose),
                "비고": str(memo),
                "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "연료종류": str(f_type),
                "주입량": float(f_amt),
                "결제금액": int(f_cost)
            }
            
            new_row = pd.DataFrame([data_to_add])
            
            # 기존 시트 데이터 읽기
            existing_df = conn.read(ttl=0)
            
            # 병합 시 데이터 타입 불일치 방지
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            
            # 구글 시트 업데이트
            conn.update(data=updated_df)
            
            st.success("데이터가 성공적으로 저장되었습니다!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")

# 7. 최근 기록 보기
with st.expander("📊 최근 기록 보기"):
    try:
        df_hist = conn.read(ttl=0)
        st.dataframe(df_hist.tail(5).iloc[::-1], use_container_width=True)
    except:
        st.write("데이터가 없습니다.")
