import time
from os import write

from rag import RagService
import config_data as config

import streamlit as st



st.title("智能客服")
st.divider()#分隔符
#在页面最下方提供用户输入框
prompt=st.chat_input()

if "message" not in st.session_state:
    st.session_state["message"]=[{"role":"assistant","content":"你好，有什么需要帮助的吗"}]

if "rag" not in st.session_state:
    st.session_state["rag"]=RagService()

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

if prompt:
    #在页面输出用户提问
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role":"user","content":prompt})

    with st.spinner("思考中"):
        res_stream=st.session_state["rag"].chain.stream({"input":prompt},config.session_config)
        #在页面输出用户提问


        res=st.chat_message("assistant").write_stream(res_stream)
        st.session_state["message"].append({"role": "assistant","content":res})
