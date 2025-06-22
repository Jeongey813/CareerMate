import streamlit as st
from openai import OpenAI
import datetime

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(page_title="CareerMate", page_icon="👩🏻‍💻")

# --------------------------------------------------
# App header
# --------------------------------------------------
st.title("👩🏻‍💻 CareerMate 💬")
st.write(
    "CareerMate는 OpenAI GPT‑4o 모델을 활용하여 사용자의 **직업**과 **위치**를 기반으로 "
    "맞춤형 뉴스, 업계 트렌드, 지역 이벤트 정보를 제공하는 지능형 챗봇입니다. "
    "매일 아침 개인화된 브리핑을 받아보며 커리어 성장에 실질적인 도움을 받아보세요.  \n\n"
    "앱 사용 전 [OpenAI API 키](https://platform.openai.com/account/api-keys)가 필요합니다."
)

st.divider()

# --------------------------------------------------
# User profile inputs
# --------------------------------------------------
st.subheader("📝 기본 정보 입력")

profession = st.text_input("직업 / 전문 분야 (예: 데이터 분석가, UX 디자이너 등)", key="profession")
interests = st.text_input("흥미 있는 분야 (콤마로 구분, 예: AI, 데이터 시각화, 스타트업)", key="interests")
briefing_time = st.time_input("매일 브리핑을 받을 시간", value=datetime.time(9, 0), key="briefing_time")

# --------------------------------------------------
# OpenAI API key input
# --------------------------------------------------
openai_api_key = st.text_input("🔑 OpenAI API Key", type="password", placeholder="sk-…")

if not openai_api_key:
    st.info("API 키를 입력하면 챗봇과 대화할 수 있습니다.", icon="🗝️")
    st.stop()

# --------------------------------------------------
# Validate user profile
# --------------------------------------------------
if not profession or not interests:
    st.warning("✏️ 직업과 흥미 분야를 모두 입력해 주세요.")
    st.stop()

# --------------------------------------------------
# OpenAI client initialisation
# --------------------------------------------------
client = OpenAI(api_key=openai_api_key)

# --------------------------------------------------
# Initialise chat history
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------------------------------
# Dynamic system prompt built from user profile
# --------------------------------------------------
system_prompt = (
    f"You are CareerMate, an AI career companion. "
    f"The user is a '{profession}' and is interested in '{interests}'. "
    f"Each response should prioritise news, trends, and local events that are relevant "
    f"to their profession and interests. "
    f"The user prefers a daily briefing at {briefing_time.strftime('%H:%M')} (Asia/Seoul). "
    f"Respond in Korean unless asked otherwise, and keep answers concise but informative."
)

# --------------------------------------------------
# Display previous messages
# --------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --------------------------------------------------
# Chat input area
# --------------------------------------------------
if prompt := st.chat_input("궁금한 점을 입력하세요 …"):

    # Append user prompt to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build payload with system prompt
    chat_payload = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    # Generate streaming response
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat_payload,
        stream=True,
    )

    with st.chat_message("assistant"):
        response = st.write_stream(stream)

    # Save assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# --------------------------------------------------
# Sidebar notification about briefing schedule
# --------------------------------------------------
st.sidebar.success(
    f"⏰ 매일 {briefing_time.strftime('%H:%M')}에 브리핑을 제공하도록 설정되었습니다.\n"
    "브리핑 기능을 자동화하려면 서버 측 스케줄러(cron, APScheduler 등)와 "
    "Streamlit Cloud 배치 기능을 연동해 보세요."
)
