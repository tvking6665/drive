import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# 2. 구글 시트 연결 (Secrets에 설정한 정보 사용)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 데이터 로드 함수: 이전 종료거리를 가져옴 ---
def get_last_dist(car_name):
    try:
        df = conn.read()
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            return int(car_df.iloc[-1]['종료거리'])
        return 0
    except:
        return 0

# 제목 부분
st.title("🚛 전우정밀 차량 운행 기록부")

# 3. 기본 정보 입력
col_date, col_car = st.columns(2)
with col_date:
    selected_date = st.date_input("📅 운행 날짜", datetime.now())
with col_car:
    car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378"]
    selected_car = st.selectbox("🚗 차량 선택", car_list)

driver_list = ["김동현", "김태종", "이학장", "직접 입력"]
selected_driver = st.selectbox("👤 운전자", driver_list)
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# 4. 경로 및 주행 거리 (핵심 기능)
last_km = get_last_dist(selected_car)

col1, col2 = st.columns(2)
with col1:
    start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "직접 입력"])
    if start_node == "직접 입력": start_node = st.text_input("출발지 상세")
    start_km = st.number_input("📍 시작 거리 (km)", value=last_km, help="마지막 기록을 불러왔습니다.")

with col2:
    end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "직접 입력"])
    if end_node == "직접 입력": end_node = st.text_input("목적지 상세")
    end_km = st.number_input("🏁 종료 거리 (km)", value=start_km)

st.divider()

# 5. 운행 내용 및 비고
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "거래처 미팅", "현장 방문", "기타"])
memo = st.text_area("비고 (특이사항)", placeholder="주유 기록이나 차량 상태 등을 적어주세요.")

total_distance = end_km - start_km
if total_distance > 0:
    st.info(f"이번 주행 거리: {total_distance} km")

# 6. 저장 버튼 (실제 구글 시트 저장 로직 포함)
if st.button("🚀 운행 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
    elif not selected_driver:
        st.warning("운전자를 입력해 주세요.")
    else:
        try:
            # 시트에 추가할 데이터 구성
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
            
            # 구글 시트에 업데이트
            existing_df = conn.read()
            updated_df = pd.concat([existing_df, new_data], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success(f"✅ {selected_car} 기록이 시트에 저장되었습니다!")
            st.balloons()
        except Exception as e:
            st.error(f"저장 중 오류 발생: {e}")

# 7. 하단 이력 조회
with st.expander("📊 최근 운행 이력 보기"):
    try:
        history_df = conn.read()
        st.dataframe(history_df.tail(10).iloc[::-1], use_container_width=True)
    except:
        st.write("데이터를 불러오는 중입니다.")
