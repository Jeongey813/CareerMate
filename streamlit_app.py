import streamlit as st
from openai import OpenAI

# Show title and description.
st.title("💬Career Mate👩🏻‍💻")
st.write(
    "CareerMate는 OpenAI의 GPT-4o 모델을 사용하여 응답을 생성하는 맞춤형 챗봇입니다. 
    "사용자의 직업과 위치에 맞춘 뉴스, 트렌드, 이벤트, 정보를 제공하며,전문 분야에 대한 설명과 피드백까지 지원해 실질적인 커리어 성장을 돕습니다."
    "이 앱을 사용하려면 OpenAI API 키가 필요하며, [여기](https://platform.openai.com/account/api-keys)에서 발급받을 수 있습니다.. "
    "또한 [이 튜토리얼](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)을 따라 단계별로 이 앱을 만드는 방법을 배울 수 있습니다."
)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("What is up?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate a response using the OpenAI API.
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )

        # Stream the response to the chat using `st.write_stream`, then store it in 
        # session state.
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
