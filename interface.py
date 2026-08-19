import streamlit as st
from app.agent import MountainAgent

st.title("Welcome to RoMountainAgent - Let's HIKE!")

if "agent" not in st.session_state:
    st.session_state.agent = MountainAgent()

if"messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt :=st.chat_input("Ask for hike details"):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.agent.send_message(prompt)
        st.markdown(response)
