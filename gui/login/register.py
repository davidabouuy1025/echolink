import streamlit as st
import datetime



def register():
    manager = st.session_state.manager

    col1, col2 = st.columns(2)

    with col1:
        with st.form("register-form"):
            st.header("Create Account")
            new_username = st.text_input("Enter username: ")
            new_password = st.text_input("Enter password: ", type="password")
            register_button = st.form_submit_button("Create new account")

            if register_button:
                user_id, result = manager.add_user(new_username, new_password)

                if not user_id:
                    for e in result:
                        st.error(e)
                else:
                    st.toast(result)
                    current_user = next((u for u in manager.users if u.username == new_username), None)
                    current_user.status = "online"
                    manager.save()
                    st.session_state.page = "user"
                    st.session_state.user_id = user_id
                    manager.save()
                    st.rerun()
    with col2:
        img_path = "wallpaper/wallpaper.png"
        st.image(img_path, width='stretch')
        