import streamlit as st
import datetime

# --------------------------------------------------
# 전체 배경 스타일 설정 (CSS)
# --------------------------------------------------
st.markdown("""
    <style>
    html, body {
        background-color: #e6f2ff;
    }
    [data-testid="stAppViewContainer"] > .main {
        background-color: #e6f2ff;
    }
    .white-section {
        background-color: white;
        padding: 2rem;
        margin-top: -1.5rem;
        border-top-left-radius: 1rem;
        border-top-right-radius: 1rem;
    }

    /* 입력 필드 스타일 수정 */
    input[data-testid="stTextInput"],
    textarea[data-testid="stTextArea"] {
        background-color: white !important;
        border: none !important;
        border-bottom: 2px solid black !important;
        border-radius: 0 !important;
        padding: 0.3rem 0.5rem !important;
        box-shadow: none !important;
    }
    </style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# 페이지 설정 및 날짜 고정
# --------------------------------------------------
st.set_page_config(page_title="CareerMate", page_icon="👩🏻‍💻", layout="centered")
TODAY = datetime.date(2025, 6, 23)

# --------------------------------------------------
# 상단 소개
# --------------------------------------------------
st.title("👩🏻‍💻 CareerMate 💬")
st.markdown(
    f"""
    <div class="intro-box">
    CareerMate는 GPT‑4o‑mini 모델을 활용해 사용자의 <b>직업</b>·<b>관심사</b>·<b>지역</b> 정보를 기반으로<br>
    <b>{TODAY.strftime('%Y‑%m‑%d')} 기준 최신</b> 뉴스·트렌드·이벤트를 제공하는 지능형 커리어 챗봇입니다.<br><br>
    💡 입력 완료 시 바로 오늘자 개인화 브리핑을 받아보세요!
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# --------------------------------------------------
# 사용자 입력
# --------------------------------------------------
profession = st.text_input("직업 / 전문 분야", placeholder="예: 데이터 분석가, UX 디자이너 …")
interests = st.text_input("흥미 있는 분야 (콤마로 구분)", placeholder="예: AI, 데이터 시각화, 스타트업 …")
location = st.text_input("거주 지역 또는 관심 지역", placeholder="예: 서울, 베를린, 부산 …")
briefing_time = st.time_input("매일 브리핑 받을 시간", value=datetime.time(9, 0))
openai_api_key = st.text_input("🔑 OpenAI API Key", type="password", placeholder="sk-…")

if not openai_api_key:
    st.info("API 키를 입력해야 챗봇을 사용할 수 있습니다.", icon="🗝️")
    st.stop()

# --------------------------------------------------
# OpenAI 초기화
# --------------------------------------------------
try:
    from openai import OpenAI
    client = OpenAI(api_key=openai_api_key)
    _USE_V2 = True
except ImportError:
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
# 시스템 프롬프트 구성
# --------------------------------------------------
system_prompt_base = (
    f"You are CareerMate, a Korean AI career companion. "
    f"Today's date is {TODAY.isoformat()}. Always provide the most recent information, "
    f"preferably from the last 10 days or upcoming after {TODAY.isoformat()}. "
    f"If the user asks for '이벤트' or '행사', only mention those that are scheduled for {TODAY.isoformat()} or later in '{{location}}'. "
    f"The user is a '{{profession}}' located in '{{location}}' and interested in '{{interests}}'. "
    f"Keep responses concise, informative, markdown-formatted, and in Korean."
)

# --------------------------------------------------
# 브리핑 생성 함수
# --------------------------------------------------
def generate_daily_briefing():
    prompt = (
        f"Please provide a concise (max 10 bullet points) daily briefing for a '{profession}' "
        f"in '{location}', interested in '{interests}'. Include:\n"
        f"1. 3 key news headlines (since {TODAY - datetime.timedelta(days=10)}).\n"
        f"2. 2 emerging industry trends.\n"
        f"3. 2 upcoming local events (on or after {TODAY.isoformat()}).\n"
        f"All content must be accurate as of {TODAY}. Respond in Korean with markdown bullets."
    )
    payload = [
        {"role": "system", "content": system_prompt_base.format(
            profession=profession, location=location, interests=interests)},
        {"role": "user", "content": prompt}
    ]
    if _USE_V2:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=payload)
        return response.choices[0].message.content.strip()
    else:
        response = _openai.ChatCompletion.create(model="gpt-4o-mini", messages=payload)
        return response.choices[0].message.content.strip()

# --------------------------------------------------
# 자동 브리핑 실행
# --------------------------------------------------
if all([profession, interests, location]) and not st.session_state.briefing_generated:
    with st.spinner("오늘자 브리핑을 생성 중입니다…"):
        briefing = generate_daily_briefing()
    st.session_state.messages.append({"role": "assistant", "content": briefing})
    st.session_state.briefing_generated = True

# --------------------------------------------------
# 이전 대화 출력
# --------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --------------------------------------------------
# 실시간 응답 핸들링
# --------------------------------------------------
def _request_stream(payload):
    if _USE_V2:
        return client.chat.completions.create(model="gpt-4o-mini", messages=payload, stream=True)
    return _openai.ChatCompletion.create(model="gpt-4o-mini", messages=payload, stream=True)

def _parse_chunk(chunk):
    delta = chunk.choices[0].delta
    return getattr(delta, "content", "") or ""

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

    _stream = _request_stream(payload)

    def _gen():
        for ch in _stream:
            txt = _parse_chunk(ch)
            if txt:
                yield txt

    with st.chat_message("assistant"):
        reply = st.write_stream(_gen())

    st.session_state.messages.append({"role": "assistant", "content": reply})

# --------------------------------------------------
# 사이드바 알림
# --------------------------------------------------
with st.sidebar:
    st.success(
        f"⏰ 매일 **{briefing_time.strftime('%H:%M')}** (Asia/Seoul) 브리핑이 설정되어 있습니다.\n"
        "서버 측 스케줄러(예: cron, APScheduler)와 이메일/Slack Webhook을 연동해 자동 전달 기능을 구현해 보세요!"
    ) 


# --------------------------------------------------
# 📌 대답 후 카테고리 버튼 노출 + 선택 시 정보 제공
# --------------------------------------------------
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    st.divider()
    st.subheader("🔍 더 알고 싶은 주제를 선택하세요:")
    category = st.radio("카테고리 선택", ["최신 뉴스", "업계 트렌드", "지역 이벤트", "도서 추천"], horizontal=True)

    def get_category_content(cat):
        examples = {
            "최신 뉴스": f"'{location}' 지역과 '{interests}' 관련 최근 이슈 3가지 알려줘",
            "업계 트렌드": f"'{profession}' 관련 최신 산업 트렌드 3가지 알려줘",
            "지역 이벤트": f"{TODAY} 이후 '{location}'에서 열리는 흥미로운 행사 3가지 알려줘",
            "도서 추천": (
                f"'{profession}'와 관련된 전문 서적 또는 자기계발 추천 도서 3권을 알려줘.\n"
                f"각 도서에 대해 제목, 저자, 간단한 설명과 함께 한국 또는 국제 온라인 서점 구매 링크도 포함해줘.\n"
                f"구매 링크는 실제 존재하지 않아도 되지만 링크 형태 (예: https://...) 로 표현해줘."
            ),
            "채용 공고": (
                f"'{location}' 또는 온라인에서 '{profession}'와 관련된 최근 채용 공고 3건을 알려줘.\n"
                f"각 공고에 대해 직무 제목, 회사명, 위치, 마감일, 간단한 설명, 지원 링크를 포함해줘."
            )
        }
        q = examples[cat]
        payload = [
            {"role": "system", "content": system_prompt_base.format(
                profession=profession, location=location, interests=interests)},
            {"role": "user", "content": q}
        ]
        if _USE_V2:
            res = client.chat.completions.create(model="gpt-4o-mini", messages=payload)
            return res.choices[0].message.content.strip()
        res = _openai.ChatCompletion.create(model="gpt-4o-mini", messages=payload)
        return res.choices[0].message.content.strip()

    if category:
        with st.spinner(f"'{category}' 관련 정보를 불러오는 중입니다…"):
            extra = get_category_content(category)
        st.markdown(f"### 📚 {category} 요약")
        st.markdown(extra, unsafe_allow_html=True)

