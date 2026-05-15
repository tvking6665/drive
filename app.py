import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 설정
st.set_page_config(page_title="전우정밀 차량관리", layout="centered")
st.markdown("### 🚗 차량 운행 기록부")

# 2. 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 마지막 종료거리 가져오기 함수
def get_dist(car):
    try:
        df = conn.read(ttl=0)
        car_df = df[df['차량'] == car]
        if not car_df.empty:
            return int(pd.to_numeric(car_df.iloc[-1]['종료거리'], errors='coerce'))
        return 0
    except: return 0

# 3. 입력
d = st.date_input("날짜", datetime.now())
car = st.selectbox("차량", ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"])
dr = st.selectbox("운전자", ["김동현", "김태종", "이학장", "직접입력"])
if dr == "직접입력": dr = st.text_input("이름입력")

st.divider()

last_km = get_dist(car)
c1, c2 = st.columns(2)
with c1:
    s_node = st.text_input("출발지", value="회사")
    s_km = st.number_input("시작거리", value=last_km)
with c2:
    e_node = st.text_input("목적지")
    e_km = st.number_input("종료거리", value=s_km)

st.divider()

p = st.selectbox("운행내용", ["납품", "통근", "업무", "기타"])
m = st.text_area("비고")

# 4. 저장
if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
    if e_km < s_km:
        st.error("종료거리가 시작보다 작습니다.")
    else:
        try:
            new_data = pd.DataFrame([{
                "날짜": d.strftime('%Y-%m-%d'),
                "차량": car,
                "운전자": dr,
                "출발지": s_node,
                "목적지": e_node,
                "시작거리": s_km,
                "종료거리": e_km,
                "주행거리": e_km - s_km,
                "운행내용": p,
                "비고": m,
                "입력시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])
            df_old = conn.read(ttl=0)
            df_final = pd.concat([df_old, new_data], ignore_index=True)
            conn.update(data=df_final)
            st.success("저장되었습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"오류발생: {e}")
