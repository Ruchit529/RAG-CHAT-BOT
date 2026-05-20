import streamlit as st
import requests
import os

st.set_page_config(
    page_title="AI PDF Chat",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Document Chatbot")


backend_url = os.environ.get("BACKEND_URL")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("Ask a question")

if prompt:

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                response = requests.post(
                    f"{backend_url}/ask",
                    json={"question": prompt}
                )

                answer = response.json()["answer"]

            except Exception as e:

                answer = f"Error: {str(e)}"

            st.write(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })
    
