import streamlit as st
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="차량 운행 기록부", page_icon="🚚")

st.title("🚚 차량 운행 기록부 (전우정밀)")

# 구글 시트 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 1. 운행 날짜 선택
selected_date = st.date_input("🗓️ 운행 날짜", datetime.now())

# 2. 운행 정보 입력
st.subheader("📍 운행 정보 입력")
col1, col2 = st.columns(2)

with col1:
    departure = st.text_input("출발지", placeholder="예: 본사")
    start_km = st.number_input("출발 시 주행거리 (km)", min_value=0, value=0)

with col2:
    destination = st.text_input("목적지", placeholder="예: 거래처")
    end_km = st.number_input("도착 시 주행거리 (km)", min_value=0, value=0)

purpose = st.text_input("운행 목적")
memo = st.text_area("비고")

total_distance = end_km - start_km
st.divider()

# 3. 저장 로직
if st.button("구글 시트에 저장하기"):
    if total_distance <= 0 and (start_km != 0 or end_km != 0):
        st.error("주행거리를 다시 확인해 주세요.")
    elif not departure or not destination:
        st.warning("출발지와 목적지를 입력해 주세요.")
    else:
        # 새로운 데이터 행 만들기
        new_data = pd.DataFrame([{
            "날짜": selected_date.strftime('%Y-%m-%d'),
            "출발지": departure,
            "목적지": destination,
            "출발거리": start_km,
            "도착거리": end_km,
            "주행거리": total_distance,
            "운행목적": purpose,
            "비고": memo,
            "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }])
        
        # 기존 데이터 가져오기 및 추가
        try:
            existing_data = conn.read()
            updated_df = pd.concat([existing_data, new_data], ignore_index=True)
            conn.update(data=updated_df)
            st.success("✅ 구글 시트에 기록되었습니다!")
            st.balloons()
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다: {e}")
            st.info("구글 시트의 공유 설정에서 '링크가 있는 모든 사용자'에게 '편집자' 권한을 주었는지 확인해 주세요.")
