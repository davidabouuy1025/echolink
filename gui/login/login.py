import streamlit as st
import datetime
import time
from app.user import User

def login():
    manager = st.session_state.manager  # ManagerSQL instance
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
            # MySQL login
            conn = manager._get_conn()
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
                row = cursor.fetchone()
            finally:
                cursor.close()
                conn.close()

            with st.spinner("Loading..."):
                time.sleep(1)

            if not row:
                st.error("Username or password is incorrect")
            else:
                # Store user info in session_state
                st.session_state.page = "user"
                st.session_state.user_id = row["user_id"]

                # Optionally mark user online
                manager.update_profile(row["user_id"], row["password"], row["name"], row["bday"], row["gender"], row["contact_num"])
                
                st.rerun()
