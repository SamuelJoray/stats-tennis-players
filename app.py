"""Streamlit chat UI over the Milestone B agent (src/agent.py)."""

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.agent import TennisAgent
from src.db import run_query

load_dotenv()

st.set_page_config(page_title="Tennis Stats Agent", page_icon="🎾")
st.title("🎾 Tennis Stats Agent")
st.caption("Ask questions about ATP/WTA matches from the Match Charting Project.")


@st.cache_resource
def get_agent():
    return TennisAgent()


if "history" not in st.session_state:
    st.session_state.history = []  # list of {"role", "content", "sql_log"?}

agent = get_agent()

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sql_log"):
            with st.expander("SQL used"):
                for sql in msg["sql_log"]:
                    st.code(sql, language="sql")
                    try:
                        df, _ = run_query(agent.con, sql)
                        st.dataframe(df)
                    except Exception:
                        pass

question = st.chat_input("Ask a question about the data...")
if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = agent.ask(question)
        st.markdown(result["answer"])
        if result["sql_log"]:
            with st.expander("SQL used"):
                for sql in result["sql_log"]:
                    st.code(sql, language="sql")
                    try:
                        df, _ = run_query(agent.con, sql)
                        st.dataframe(df)
                    except Exception:
                        pass

    st.session_state.history.append(
        {"role": "assistant", "content": result["answer"], "sql_log": result["sql_log"]}
    )
