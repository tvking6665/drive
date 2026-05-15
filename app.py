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
        
        # 데이터가 아예 없거나 비어있는 경우 처리
        if df.empty:
            return 0
            
        # 해당 차량의 데이터만 필터링
        car_df = df[df['차량'] == car_name]
        
        if not car_df.empty:
            # 마지막 행의 '종료거리' 열 값을 가져옴
            last_val = car_df.iloc[-1]['종료거리']
            
            # 숫자로 변환 시도 (문자열 등이 섞여있으면 NaN으로 처리 후 0으로 치환)
            num_val = pd.to_numeric(last_val, errors='coerce')
            
            if pd.isna(num_val):
                return 0
            return int(num_val)
            
        return 0
    except Exception as e:
        # 에러 발생 시 로그를 남기지 않고 0 반환 (초기화 상태 대응)
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

# 주행 거리 입력 (오류 방지를 위해 int 처리 강화)
last_km = get_last_dist(selected_car)
c1, c2 = st.columns(2)
with c1:
    start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "통근노선 시작", "직접 입력"])
    if start_node == "직접 입력": start_node = st.text_input("출발지 상세")
    start_km = st.number_input("📍 시작 거리 (km)", value=int(last_km))
with c2:
    end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점", "직접 입력"])
    if end_node == "직접 입력": end_node = st.text_input("목적지 상세")
    end_km = st.number_input("🏁 종료 거리 (km)", value=int(start_km))

st.divider()

# 5. 연료 주입 섹션
fuel_needed = st.checkbox("⛽ 오늘 연료나 요소수를 주입했나요?")
f_type, f_amt, f_cost = "-", 0, 0

if fuel_needed:
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        f_type = st.selectbox("종류", ["LPi", "경유", "요소수"])
    with fc2:
        f_amt = st.number_input("주입량", min_value=0)
    with fc3:
        f_cost = st.number_input("결제금액(원)", min_value=0)

st.divider()

# 6. 운행 내용 및 비고
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "기타"])
memo = st.text_area("비고 (특이사항)")

# 7. 저장 로직
if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
    else:
        try:
            # 새 데이터 생성
            new_row = pd.DataFrame([{
                "날짜": selected_date.strftime('%Y-%m-%d'),
                "차량": selected_car,
                "운전자": selected_driver,
                "출발지": start_node,
                "목적지": end_node,
                "시작거리": start_km,
                "종료거리": end_km,
                "주행거리": end_km - start_km,
                "운행내용": purpose,
                "비고": memo,
                "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "연료종류": f_type,
                "주입량": f_amt,
                "결제금액": f_cost
            }])
            
            # 기존 데이터 읽기 및 병합
            existing_df = conn.read(ttl=0)
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            
            # 시트 업데이트
            conn.update(data=updated_df)
            
            st.success("기록이 성공적으로 저장되었습니다!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"저장 중 오류 발생: {e}")

# 8. 최근 기록 보기
with st.expander("📊 최근 기록"):
    try:
        df_hist = conn.read(ttl=0)
        st.dataframe(df_hist.tail(5).iloc[::-1], use_container_width=True)
    except:
        st.write("조회 가능한 데이터가 없습니다.")
