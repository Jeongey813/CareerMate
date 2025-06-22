import streamlit as st
import datetime

# --------------------------------------------------
# 라이브러리 호환 처리
# --------------------------------------------------
try:
    from openai import OpenAI  # type: ignore
    _USE_V2 = True
except ImportError:  # pragma: no cover
    import openai  # type: ignore
    _USE_V2 = False

# --------------------------------------------------
# 상수 및 오늘 날짜 고정 (질문한 날)
# --------------------------------------------------
TODAY = datetime.date(2025, 6, 23)  # 질문한 날 고정

# --------------------------------------------------
# Streamlit 페이지 설정
# --------------------------------------------------
st.set_page_config(page_title="CareerMate", page_icon="👩🏻‍💻", layout="centered")

# --------------------------------------------------
# 헤더
# --------------------------------------------------
st.title("👩🏻‍💻 CareerMate 💬")
st.markdown(
    """
    CareerMate는 GPT‑4o‑mini 모델을 활용해 사용자의 **직업**·**관심사**·**지역** 정보를 기반으로  
    **2025‑06‑23 기준 최신** 뉴스·트렌드·이벤트를 제공하는 지능형 커리어 챗봇입니다.  

    💡 입력 완료 시 바로 오늘자 개인화 브리핑을 받아보세요!
    """
)

st.divider()

# --------------------------------------------------
# 사용자 기본 정보 입력
# --------------------------------------------------
st.subheader("📝 기본 정보 입력")

profession = st.text_input("직업 / 전문 분야", placeholder="예: 데이터 분석가, UX 디자이너 …")
interests = st.text_input("흥미 있는 분야 (콤마로 구분)", placeholder="예: AI, 데이터 시각화, 스타트업 …")
location = st.text_input("거주 지역 또는 관심 지역", placeholder="예: 서울, 베를린, 부산 …")
briefing_time = st.time_input("매일 브리핑 받을 시간", value=datetime.time(9, 0))

# --------------------------------------------------
# OpenAI API 키 입력
# --------------------------------------------------
openai_api_key = st.text_input("🔑 OpenAI API Key", type="password", placeholder="sk-…")

if not openai_api_key:
    st.info("API 키를 입력해야 챗봇을 사용할 수 있습니다.", icon="🗝️")
    st.stop()

# --------------------------------------------------
# OpenAI 클라이언트 초기화
# --------------------------------------------------
if _USE_V2:
    client = OpenAI(api_key=openai_api_key)
else:  # OpenAI 0.x
    import openai as _openai  # noqa: N812
    _openai.api_key = openai_api_key

# --------------------------------------------------
# 세션 스테이트 초기화
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "briefing_generated" not in st.session_state:
    st.session_state.briefing_generated = False

# --------------------------------------------------
# 시스템 프롬프트 (항상 최신 지시)
# --------------------------------------------------
system_prompt_base = (
    f"You are CareerMate, a Korean AI career companion. "
    f"Today's date is {TODAY.isoformat()}. Always provide the most recent information "
    f"(preferably from the last 10 days prior to {TODAY.isoformat()}) when answering. "
    f"The user is a '{{profession}}' located in '{{location}}' and interested in '{{interests}}'. "
    f"Keep responses concise, informative, markdown-formatted, and in Korean."
)

# --------------------------------------------------
# 자동 브리핑 생성 함수
# --------------------------------------------------

def generate_daily_briefing():
    """GPT를 호출해 오늘자 맞춤 브리핑을 생성한다."""
    briefing_prompt = (
        f"Please provide a concise (max 10 bullet points) daily briefing for a '{profession}' "
        f"in '{location}', interested in '{interests}'. Include:\n"
        f"1. 3 key news headlines (since {TODAY - datetime.timedelta(days=10)}).\n"
        f"2. 2 emerging industry trends.\n"
        f"3. 2 upcoming local events (with dates).\n"
        f"All content must be up to date as of {TODAY}. Respond in Korean with markdown bullets."
    )

    payload = [
        {"role": "system", "content": system_prompt_base.format(
            profession=profession, location=location, interests=interests)},
        {"role": "user", "content": briefing_prompt},
    ]

    if _USE_V2:
        result = client.chat.completions.create(model="gpt-4o-mini", messages=payload)
        return result.choices[0].message.content.strip()
    result = _openai.ChatCompletion.create(model="gpt-4o-mini", messages=payload)
    return result.choices[0].message.content.strip()

# --------------------------------------------------
# 입력 완료 시 자동 브리핑
# --------------------------------------------------
if all([profession, interests, location]) and not st.session_state.briefing_generated:
    with st.spinner("오늘자 브리핑을 생성 중입니다…"):
        daily_brief = generate_daily_briefing()
    st.session_state.messages.append({"role": "assistant", "content": daily_brief})
    st.session_state.briefing_generated = True

# 이미 생성된 브리핑 포함해 이전 메시지 렌더링
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --------------------------------------------------
# 헬퍼: OpenAI 스트림 요청
# --------------------------------------------------

def _request_stream(payload):
    if _USE_V2:
        return client.chat.completions.create(model="gpt-4o-mini", messages=payload, stream=True)
    return _openai.ChatCompletion.create(model="gpt-4o-mini", messages=payload, stream=True)


def _parse_chunk(chunk):
    delta = chunk.choices[0].delta
    return getattr(delta, "content", "") or ""

# --------------------------------------------------
# 대화 입력 처리
# --------------------------------------------------
if prompt := st.chat_input("궁금한 점을 입력하세요 …"):

    if not all([profession, interests, location]):
        st.warning("👀 먼저 직업·흥미·지역 정보를 모두 입력해 주세요!")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 사용자 프로필을 반영한 시스템 프롬프트
    system_prompt = system_prompt_base.format(
        profession=profession, location=location, interests=interests
    )

    payload = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    _stream = _request_stream(payload)

    def _gen():
        for ch in _stream:
            txt = _parse_chunk(ch)
            if txt:
                yield txt

    with st.chat_message("assistant"):
        assistant_reply = st.write_stream(_gen())

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

# --------------------------------------------------
# 사이드바 — 브리핑 설정 안내
# --------------------------------------------------
with st.sidebar:
    st.success(
        f"⏰ 매일 **{briefing_time.strftime('%H:%M')}** (Asia/Seoul) 브리핑이 설정되어 있습니다.\n"
        "서버 측 스케줄러(예: cron, APScheduler)와 이메일/Slack Webhook을 연동해 자동 전달 기능을 구현해 보세요!"
    )
