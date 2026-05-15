import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 차량 관리", layout="centered")

# 2. 제목
st.markdown('<h2 style="text-align: center;">🚗 차량 운행 기록부</h2>', unsafe_allow_html=True)

# 3. 구글 시트 연결 (기본 라이브러리 사용)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_last_dist(car_name):
    try:
        df = conn.read(ttl=0)
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            val = car_df.iloc[-1]['종료거리']
            num_val = pd.to_numeric(val, errors='coerce')
            return int(num_val) if pd.notnull(num_val) else 0
        return 0
    except:
        return 0

# 4. 정보 입력창
selected_date = st.date_input("📅 날짜", datetime.now())
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
selected_car = st.selectbox("🚗 차량 선택", car_list)
selected_driver = st.selectbox("👤 운전자", ["김동현", "김태종", "이학장", "직접 입력"])
if selected_driver == "직접 입력":
    selected_driver = st.text_input("운전자 성명")

st.divider()

# 5. 주행 거리 및 경로 입력
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

# 6. 기타 정보 및 저장
purpose = st.selectbox("📝 운행 내용", ["납품 및 업무협의", "통근버스 운행", "기타"])
memo = st.text_area("비고 (특이사항)")

if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
    if end_km < start_km:
        st.error("종료 거리가 시작 거리보다 작을 수 없습니다!")
    else:
        try:
            # 새 데이터 생성 (시트 열 순서와 일치시킴)
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
                "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])
            
            # 기존 데이터 읽기 및 병합
            existing_df = conn.read(ttl=0)
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            
            # 시트 업데이트 (이 부분에서 권한 오류가 날 수 있음)
            conn.update(data=updated_df)
            
            st.success("데이터가 성공적으로 저장되었습니다!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
            st.info("💡 구글 시트 공유에서 서비스 계정 이메일을 '편집자'로 추가했는지 다시 확인해 보세요.")

# 최근 기록 보기
with st.expander("📊 최근 기록"):
    try:
        df_hist = conn.read(ttl=0)
        st.dataframe(df_hist.tail(5).iloc[::-1], use_container_width=True)
    except:
        st.write("조회 가능한 데이터가 없습니다.")
