# components/sidebar.py
import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.sidebar.image("./assets/logo_esalq_red.png", use_container_width=True, width=150)