import streamlit as st
import datetime

def register():
    manager = st.session_state.manager  # ManagerSQL instance

    col1, col2 = st.columns(2)

    with col1:
        with st.form("register-form"):
            st.header("Create Account")
            new_username = st.text_input("Enter username: ")
            new_password = st.text_input("Enter password: ", type="password")
            register_button = st.form_submit_button("Create new account")

            if register_button:
                # Add user via ManagerSQL
                user_id, result = manager.add_user(new_username, new_password)

                if not user_id:
                    for e in result:
                        st.error(e)
                else:
                    st.toast(result)

                    # Fetch full user info from DB
                    conn = manager._get_conn()
                    cursor = conn.cursor(dictionary=True)
                    try:
                        cursor.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
                        current_user = cursor.fetchone()
                    finally:
                        cursor.close()
                        conn.close()

                    # Optionally mark user online
                    manager.update_profile(current_user["user_id"], current_user["password"],
                                           current_user["name"], current_user["bday"],
                                           current_user["gender"], current_user["contact_num"])

                    st.session_state.page = "user"
                    st.session_state.user_id = user_id
                    st.rerun()

    with col2:
        img_path = "wallpaper/wallpaper.png"
        st.image(img_path, width='stretch')
