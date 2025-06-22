import streamlit as st
import datetime

# --------------------------------------------------
# 라이브러리 호환 처리
# --------------------------------------------------
try:
    # OpenAI >= 1.0
    from openai import OpenAI  # type: ignore
    _USE_V2 = True
except ImportError:  # pragma: no cover
    import openai  # type: ignore
    _USE_V2 = False

# --------------------------------------------------
# 스트림릿 페이지 설정
# --------------------------------------------------
st.set_page_config(page_title="CareerMate", page_icon="👩🏻‍💻", layout="centered")

# --------------------------------------------------
# 헤더
# --------------------------------------------------
st.title("👩🏻‍💻 CareerMate 💬")
st.markdown(
    """
    CareerMate는 GPT‑4o‑mini 모델을 활용해 사용자의 **직업**과 **위치**를 기반으로  
    맞춤형 뉴스, 업계 트렌드, 지역 이벤트 정보를 제공하는 지능형 챗봇입니다.  

    💡 매일 아침 원하는 시간에 개인화된 브리핑을 받아보세요!
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

# --------------------------------------------------
# 시스템 프롬프트 (동적)
# --------------------------------------------------
system_prompt = (
    f"You are CareerMate, a Korean AI career companion. "
    f"The user is a '{profession}' located in '{location}' and interested in '{interests}'. "
    f"Focus on news, trends, and local events relevant to these topics. "
    f"When possible, keep responses concise, informative, and in Korean. "
    f"The user prefers a daily briefing at {briefing_time.strftime('%H:%M')} Asia/Seoul. "
)

# --------------------------------------------------
# 이전 메시지 렌더링
# --------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --------------------------------------------------
# 헬퍼: 스트림 반환
# --------------------------------------------------

def _request_stream(payload):
    """OpenAI 스트림 요청 (라이브러리 버전별 분기)"""
    if _USE_V2:
        return client.chat.completions.create(
            model="gpt-4o-mini",
            messages=payload,
            stream=True,
        )
    # OpenAI 0.x
    return _openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=payload,
        stream=True,
    )


def _parse_chunk(chunk):
    """gpt‑4 스트리밍 델타에서 텍스트 추출"""
    if _USE_V2:
        delta = chunk.choices[0].delta
    else:
        delta = chunk.choices[0].delta
    return getattr(delta, "content", "") or ""


# --------------------------------------------------
# 챗 입력 처리
# --------------------------------------------------
if prompt := st.chat_input("궁금한 점을 입력하세요 …"):

    # 필수 입력 검증
    if not profession or not interests or not location:
        st.warning("👀 먼저 직업, 흥미 분야, 지역 정보를 모두 입력해 주세요!")
        st.stop()

    # 세션 히스토리에 사용자 메시지 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 요청 payload 구성
    payload = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    # OpenAI 스트림 요청
    _stream = _request_stream(payload)

    # 스트림릿 UI로 실시간 출력
    def _generator():
        for _chunk in _stream:
            _text = _parse_chunk(_chunk)
            if _text:
                yield _text

    with st.chat_message("assistant"):
        assistant_reply = st.write_stream(_generator())

    # 히스토리에 AI 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

# --------------------------------------------------
# 사이드바 — 브리핑 설정 안내
# --------------------------------------------------
with st.sidebar:
    st.success(
        f"⏰ 매일 **{briefing_time.strftime('%H:%M')}** 브리핑이 설정되어 있습니다.\n"
        "서버 측 스케줄러(예: cron, APScheduler)와 이메일/슬랙 Webhook을 연동해 자동 전달 기능을 구현해 보세요!"
    )
