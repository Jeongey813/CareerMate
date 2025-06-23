import streamlit as st
import datetime

# --------------------------------------------------
# 🔵 글로벌 스타일 (CSS)
# --------------------------------------------------
st.markdown(
    """
    <style>
    /* 전체 배경을 하늘색으로 */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
        background-color: #e6f2ff;
    }

    /* 본문 흰색 박스 영역 */
    .white-section {
        background-color: #ffffff;
        padding: 2rem;
        margin-top: -1.5rem;
        border-top-left-radius: 1rem;
        border-top-right-radius: 1rem;
    }

    /* 입력 필드: 밑줄만 보이도록 */
    input[data-testid="stTextInput"],
    textarea[data-testid="stTextArea"] {
        background-color: #ffffff !important;
        border: none !important;
        border-bottom: 2px solid #000000 !important;
        border-radius: 0 !important;
        padding: 0.35rem 0.5rem !important;
        box-shadow: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# 앱 기본 정보
# --------------------------------------------------
st.set_page_config(page_title="CareerMate", page_icon="👩🏻‍💻", layout="centered")
TODAY = datetime.date(2025, 6, 23)

# --------------------------------------------------
# 헤더 + 설명 (하늘색 배경 영역)
# --------------------------------------------------
st.markdown(
    f"""
    <h1>👩🏻‍💻 CareerMate 💬</h1>
    <div style='font-size:1.05rem;line-height:1.6;'>
        CareerMate는 GPT‑4o‑mini 모델을 활용해 사용자의 <b>직업</b>·<b>관심사</b>·<b>지역</b> 정보를 기반으로<br/>
        <b>{TODAY:%Y‑%m‑%d} 기준 최신</b> 뉴스·트렌드·이벤트를 제공하는 지능형 커리어 챗봇입니다.<br/><br/>
        💡 입력 완료 시 바로 오늘자 개인화 브리핑을 받아보세요!
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# --------------------------------------------------
# 🔲 흰색 섹션 시작
# --------------------------------------------------
st.markdown('<div class="white-section">', unsafe_allow_html=True)

# --------------------------------------------------
# 사용자 입력 필드
# --------------------------------------------------
profession = st.text_input("직업 / 전문 분야", placeholder="예: 데이터 분석가, UX 디자이너 …")
interests = st.text_input("흥미 있는 분야 (콤마로 구분)", placeholder="예: AI, 데이터 시각화, 스타트업 …")
location = st.text_input("거주 지역 또는 관심 지역", placeholder="예: 서울, 베를린, 부산 …")
briefing_time = st.time_input("매일 브리핑 받을 시간", value=datetime.time(9, 0))
openai_api_key = st.text_input("🔑 OpenAI API Key", type="password", placeholder="sk‑…")

if not openai_api_key:
    st.info("API 키를 입력해야 챗봇을 사용할 수 있습니다.", icon="🗝️")
    st.stop()

# --------------------------------------------------
# OpenAI 초기화
# --------------------------------------------------
try:
    from openai import OpenAI  # type: ignore
    client = OpenAI(api_key=openai_api_key)
    _USE_V2 = True
except ImportError:  # fallback to 0.x
    import openai as _openai
    _openai.api_key = openai_api_key
    _USE_V2 = False

# --------------------------------------------------
# 세션 상태
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "briefing_generated" not in st.session_state:
    st.session_state.briefing_generated = False

# --------------------------------------------------
# 시스템 프롬프트 베이스
# --------------------------------------------------
system_prompt_base = (
    f"You are CareerMate, a Korean AI career companion. "
    f"Today's date is {TODAY}. Provide only the most recent info (≤10 days old) or upcoming events. "
    f"For '이벤트' or '행사' queries, list items scheduled ≥ {TODAY}. "
    f"The user is a '{{profession}}' in '{{location}}' interested in '{{interests}}'. "
    f"Respond in concise Korean markdown."
)

# --------------------------------------------------
# 💡 브리핑 생성 함수
# --------------------------------------------------

def generate_daily_briefing():
    user_prompt = (
        f"Please provide a concise (≤10 bullets) daily briefing for a '{profession}' in '{location}', "
        f"interested in '{interests}'. Include:\n"
        f"1. 3 key news headlines (since {TODAY - datetime.timedelta(days=10)}).\n"
        f"2. 2 emerging industry trends.\n"
        f"3. 2 local events on/after {TODAY}.\n"
        f"Respond in Korean markdown."
    )
    payload = [
        {"role": "system", "content": system_prompt_base.format(
            profession=profession, location=location, interests=interests)},
        {"role": "user", "content": user_prompt},
    ]
    if _USE_V2:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=payload)
        return res.choices[0].message.content.strip()
    res = _openai.ChatCompletion.create(model="gpt-4o-mini", messages=payload)
    return res.choices[0].message.content.strip()

# --------------------------------------------------
# 브리핑 자동 실행
# --------------------------------------------------
if all([profession, interests, location]) and not st.session_state.briefing_generated:
    with st.spinner("오늘자 브리핑을 생성 중입니다…"):
        brf = generate_daily_briefing()
    st.session_state.messages.append({"role": "assistant", "content": brf})
    st.session_state.briefing_generated = True

# --------------------------------------------------
# 이전 대화 렌더링
# --------------------------------------------------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --------------------------------------------------
# 메시지 스트리밍 헬퍼
# --------------------------------------------------

def _stream_request(payload):
    if _USE_V2:
        return client.chat.completions.create(model="gpt-4o-mini", messages=payload, stream=True)
    return _openai.ChatCompletion.create(model="gpt-4o-mini", messages=payload, stream=True)


def _parse(chunk):
    delta = chunk.choices[0].delta
    return getattr(delta, "content", "")

# --------------------------------------------------
# 실시간 질문 처리
# --------------------------------------------------
if prompt := st.chat_input("궁금한 점을 입력하세요 …"):
    if not all([profession, interests, location]):
        st.warning("👀 먼저 직업·흥미·지역 정보를 모두 입력해 주세요!")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = [{"role": "system", "content": system_prompt_base.format(
        profession=profession, location=location, interests=interests)}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    stream = _stream_request(payload)

    def gen():
        for ch in stream:
            txt = _parse(ch)
            if txt:
                yield txt

    with st.chat_message("assistant"):
        reply = st.write_stream(gen())
    st.session_state.messages.append({"role": "assistant", "content": reply})

# --------------------------------------------------
# 사이드바 알림
# --------------------------------------------------
with st.sidebar:
    st.success(
        f"⏰ 매일 **{briefing_time:%H:%M}**(Asia/Seoul) 브리핑 설정 완료!\n"
        "서버 스케줄러(cron, APScheduler)+Webhook으로 자동 전달을 구현해 보세요."
    )

# --------------------------------------------------
# 🔲 흰색 섹션 종료
# --------------------------------------------------
st.markdown('</div>', unsafe_allow_html=True)
