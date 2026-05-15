import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 차량관리", layout="centered")
st.markdown("### 🚗 차량 운행 기록부")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_dist(car):
    try:
        df = conn.read(ttl=0)
        car_df = df[df['차량'] == car]
        if not car_df.empty:
            val = car_df.iloc[-1]['종료거리']
            return int(pd.to_numeric(val, errors='coerce'))
        return 0
    except:
        return 0

# 3. 입력 섹션
d = st.date_input("날짜", datetime.now())
car = st.selectbox("차량 선택", ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"])
dr = st.selectbox("운전자", ["김동현", "김태종", "이학장", "직접입력"])
if dr == "직접입력":
    dr = st.text_input("운전자 성명 입력")

st.divider()

# 시작거리 자동 불러오기
last_km = get_dist(car)

# 출발/목적지 및 거리 입력 (들여쓰기 교정 완료)
c1, c2 = st.columns(2)
with c1:
    s_node = st.text_input("출발지", value="회사")
    s_km = st.number_input("시작거리(km)", value=int(last_km))
with c2:
    e_node = st.text_input("목적지")
    e_km = st.number_input("종료거리(km)", value=int(s_km))

st.divider()

p = st.selectbox("운행내용", ["납품", "통근", "업무", "기타"])
m = st.text_area("비고(특이사항)")

# 4. 저장 로직
if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
    if e_km < s_km:
        st.error("종료거리가 시작거리보다 작을 수 없습니다.")
    else:
        try:
            new_row = pd.DataFrame([{
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
            
            # 기존 시트 읽기 및 업데이트
            df_old = conn.read(ttl=0)
            df_final = pd.concat([df_old, new_row], ignore_index=True)
            conn.update(data=df_final)
            
            st.success("성공적으로 저장되었습니다!")
            st.balloons()
            st.rerun()
        except Exception as e:
            st.error(f"저장 실패: {e}")
            st.info("새로 만든 시트의 [공유] 설정에서 서비스 계정이 '편집자'인지 확인하세요.")
