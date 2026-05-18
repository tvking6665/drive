import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 설정
st.set_page_config(page_title="전우정밀 차량관리", layout="centered")
st.markdown("### 🚗 차량 운행 기록부 (새 시트)")

# 🌟 [오류 해결 핵심] Secrets의 private_key 줄바꿈 문자 강제 교정 로직
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    if "private_key" in st.secrets["connections"]["gsheets"]:
        orig_key = st.secrets["connections"]["gsheets"]["private_key"]
        # 깨진 줄바꿈이나 문자열 내 실제 \n 텍스트를 파이썬이 읽을 수 있는 줄바꿈으로 변경
        if "\\n" in orig_key:
            st.secrets["connections"]["gsheets"]["private_key"] = orig_key.replace("\\n", "\n")

# 2. 구글 시트 연결 (안전하게 교정된 Secrets 적용)
url = "https://docs.google.com/spreadsheets/d/1GdHg3aKD2OXEdUx6NhLK7kOQE-uWA5JGHzmqQE1SMRw/edit?gid=0#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def get_dist(car_name):
    try:
        df = conn.read(spreadsheet=url, ttl=0)
        car_df = df[df['차량'] == car_name]
        if not car_df.empty:
            val = car_df.iloc[-1]['종료거리']
            num_val = pd.to_numeric(val, errors='coerce')
            return int(num_val) if pd.notnull(num_val) else 0
        return 0
    except:
        return 0

# 3. 데이터 입력
d = st.date_input("📅 날짜", datetime.now())
car_list = ["7.5톤(파비스) 3528", "2.5톤(마이티) 8569", "1톤(포터) 5378", "통근차(솔라티) 8740"]
car = st.selectbox("🚗 차량 선택", car_list)

dr = st.selectbox("👤 운전자", ["김동현", "김태종", "이학장", "직접입력"])
if dr == "직접입력":
    dr = st.text_input("운전자 성명 입력")

st.divider()

# 시작거리 자동 계산
last_km = get_dist(car)

c1, c2 = st.columns(2)
with c1:
    s_node = st.text_input("📍 출발지", value="회사")
    s_km = st.number_input("시작거리(km)", value=int(last_km))

with c2:
    # 엑셀 드롭다운 목록 반영
    node_list = ["회사", "A사", "B사", "C사", "D사", "직접입력"]
    e_node = st.selectbox("🎯 목적지 선택", node_list)
    
    if e_node == "직접입력":
        e_node = st.text_input("목적지 직접 입력", placeholder="예: 대구공장")
        
    e_km = st.number_input("종료거리(km)", value=int(s_km))

st.divider()

p = st.selectbox("📝 운행내용", ["납품", "통근", "업무", "기타"])
m = st.text_area("비고(특이사항)")

# 4. 저장 로직
if st.button("🚀 기록 저장", use_container_width=True, type="primary"):
    if not e_node or e_node.strip() == "":
        st.error("목적지를 선택하거나 입력해 주세요!")
    elif e_km < s_km:
        st.error("종료거리가 시작거리보다 작을 수 없습니다!")
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
            
            df_old = conn.read(spreadsheet=url, ttl=0)
            df_final = pd.concat([df_old, new_row], ignore_index=True)
            
            conn.update(spreadsheet=url, data=df_final)
            
            st.success("성공적으로 저장되었습니다!")
            st.balloons()
            st.rerun()
            
        except Exception as e:
            st.error(f"저장 실패: {e}")

# 최근 기록 보기
with st.expander("📊 최근 기록 확인"):
    try:
        df_hist = conn.read(spreadsheet=url, ttl=0)
        st.dataframe(df_hist.tail(5).iloc[::-1], use_container_width=True)
    except:
        st.write("데이터를 불러올 수 없습니다.")
