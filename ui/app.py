import streamlit as st
import requests

st.title("LLM Eval Platform")

response = requests.get("http://127.0.0.1:8000/health")

if response.status_code == 200:
    st.success("API is online")
    st.json(response.json())
else:
    st.error("API is offline")
