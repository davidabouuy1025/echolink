import streamlit as st
import datetime
import time
from app.user import User

def login():
    manager = st.session_state.manager
    img_path = "wallpaper/wallpaper.png"

    col1, col2 = st.columns(2)
    with col1:
        st.image(img_path, width='stretch')

    with col2:
        with st.form("login-form"):
            st.header("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")

        if login_button:
            success, msg = User.login_user(manager, username, password)
            with st.spinner("Loading..."):
                time.sleep(1)
            if not success:
                st.error(msg)
            else:
                current_user = next((u for u in manager.users if u.username == username and u.password == password), None)
                current_user.status = "online"
                # manager.save()
                st.session_state.page = "user"
                st.session_state.user_id = current_user.user_id
                st.rerun()