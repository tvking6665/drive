import streamlit as st
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="차량 운행 기록부", page_icon="🚚")

# 제목 부분
st.title("🚚 차량 운행 기록부")

# 1. 운행 날짜 선택 (에러가 발생했던 부분 수정)
# datetime.now()를 사용하기 위해 상단에서 from datetime import datetime을 완료했습니다.
selected_date = st.date_input("🗓️ 운행 날짜", datetime.now())

# 2. 운행 정보 입력 섹션
st.subheader("📍 운행 정보 입력")

col1, col2 = st.columns(2)

with col1:
    departure = st.text_input("출발지", placeholder="예: 전우정밀")
    start_km = st.number_input("출발 시 주행거리 (km)", min_value=0, value=0, step=1)

with col2:
    destination = st.text_input("목적지", placeholder="예: 거래처")
    end_km = st.number_input("도착 시 주행거리 (km)", min_value=0, value=0, step=1)

# 3. 추가 정보
purpose = st.text_input("운행 목적", placeholder="예: 제품 납품 및 외주 업체 방문")
memo = st.text_area("비고 (특이사항)", placeholder="주유 기록이나 차량 상태 등을 적어주세요.")

# 4. 주행 거리 계산 및 저장
total_distance = end_km - start_km

st.divider()

if st.button("운행 기록 저장하기"):
    if total_distance < 0:
        st.error("도착 주행거리가 출발 주행거리보다 작을 수 없습니다. 다시 확인해 주세요.")
    elif not departure or not destination:
        st.warning("출발지와 목적지를 입력해 주세요.")
    else:
        # 여기에 DB 저장 또는 CSV 저장 로직을 추가할 수 있습니다.
        st.success(f"✅ {selected_date} 운행 기록이 성공적으로 입력되었습니다!")
        st.info(f"총 주행 거리: {total_distance} km")
        
        # 입력된 데이터 요약 표시
        data_summary = {
            "날짜": selected_date,
            "출발지": departure,
            "목적지": destination,
            "주행거리": f"{total_distance}km",
            "목적": purpose
        }
        st.json(data_summary)
