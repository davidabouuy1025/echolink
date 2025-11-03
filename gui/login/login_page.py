import streamlit as st
from manager.manager import Manager

st.set_page_config(layout='wide', page_title='EchoLink')

def login_page():
    if "manager" not in st.session_state:
        st.session_state.manager = Manager()

    if "page" not in st.session_state:
        st.session_state.page = "login"

    if "user_id" not in st.session_state:
        st.session_state.user_id = ""

    if "refresh" not in st.session_state:
        st.session_state.refresh = "unchanged"

    manager = st.session_state.manager

    if st.session_state.page == "login":
        st.title("EchoLink 🔎🔊")
        st.sidebar.title("EchoLink Navigation")
        menu = st.sidebar.radio("Select", ["Login", "Register", "README"])

        if menu == "Login":
            from gui.login.login import login
            login()
        elif menu == "Register":
            from gui.login.register import register
            register()

        elif menu == "README":
            from gui.login.readme import readme
            readme()

    elif st.session_state.page == "user":
        from gui.user.user_page import user_page
        user_page()