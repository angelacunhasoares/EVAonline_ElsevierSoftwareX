# utils/page_layout.py
import streamlit as st


def set_page_class(class_name):
    st.markdown(
        f"""
        <script>
            document.querySelector('.stApp').classList.add('{class_name}');
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_banner():

    gif_base64_url = st.session_state.get(
        "gif_base64_url"
    )  # Assumindo que foi carregado
    st.markdown(
        f"""
        <div class="banner-container">
            <img src="{gif_base64_url}" class="banner-image" alt="Weather Animation">
            <div class="banner-text">
                <h1 class="evaonline-title"> 🌦️ EVAonline </h1>
                <h2 class="evaonline-subtitle"> Online Tool to Estimate EVApotranspiration </h2>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )