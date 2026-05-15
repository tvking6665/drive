import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 차량 관리 시스템", layout="centered")

# 2. 로고 및 제목
col1, col2 = st.columns([1, 4])
with col1:
    try:
        st.image("logo.png", width=60)
    except:
        st.write("🏢")
with col2:
    st.markdown('<h2 style="margin: 0;">차량 운행 기록부</h2>', unsafe_allow_html=True)

# 3. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_last_dist(car_name):
    try:
        # 실시간 데이터를 가져오기 위해 ttl=0 설정
        df = conn.read(ttl=0)
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            val = car_df.iloc[-1]['종료거리']
            # 숫자가 아닌 값이 섞여있을 경우를 대비해 숫자로 강제 변환
            num_val = pd.to_numeric(val, errors='coerce')
            return int(num_val) if pd.notnull(num_val) else 0
        return 0
    except:
        return 0

# 4. 기본 정보 입력
selected_date = st.date_input("📅 운행 날짜", datetime.now())
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)

selected_driver = st.selectbox("👤 운전자", ["김동현", "김태종", "이학장", "직접 입력"])
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명 입력")

st.divider()

# 5. 주행 거리 및 목적지 입력
last_km = get_last_dist(selected_car)
col_start, col_end = st.columns(2)

with col_start:
    start_node = st.selectbox("📍 출발지", ["회사(전우정밀)", "통근노선 시작", "직접 입력"])
    if start_node == "직접 입력": 
        start_node = st.text_input("출발지 상세")
    start_km = st.number_input("📍 시작 거리 (km)", value=int(last_km))

with col_end:
    end_node = st.selectbox("🎯 목적지", ["왜관(VPHC)", "AST(2공장)", "동아금속", "통근노선 종점", "직접 입력"])
    if end_node == "직접 입력": 
        end_node = st.text_input("목적지 상세")
    end_km = st.number_input("🏁 종료 거리 (km)", value=int(start_km))

st.divider()

# 6. 운행 내용 및 비고
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "거래처 미팅", "현장 방문", "기타"])
memo = st.text_area("비고 (특이사항)", height=100)
total_distance = end_km - start_km

# 7. 저장 로직
if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
    else:
        try:
            # 새 데이터 생성
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
            
            # 기존 데이터 읽기
            existing_df = conn.read(ttl=0)
            
            # 데이터 병합 및 업데이트
            updated_df = pd.concat([existing_df, new_data], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success("운행 기록이 성공적으로 저장되었습니다!")
            st.balloons()
            st.rerun()
            
        except Exception as e:
            st.error(f"저장 실패: {e}")
            st.info("💡 구글 시트 상단 [공유] 버튼에서 아래 이메일이 [편집자]인지 확인해 주세요.")
            st.code("streamlit-gsheets-service-account@streamlit-gsheets.iam.gserviceaccount.com")

# 최근 기록 조회
with st.expander("📊 최근 기록 보기"):
    try:
        history_df = conn.read(ttl=0)
        st.dataframe(history_df.tail(5).iloc[::-1], use_container_width=True)
    except:
        st.write("데이터를 불러올 수 없습니다.")
