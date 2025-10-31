import streamlit as st
import datetime
from streamlit_autorefresh import st_autorefresh
from gui.user.dashboard import dashboard
from gui.user.chat import chat
from gui.user.friend import friend
from gui.user.profile_page import profile
from gui.user.show_json import show_json

def user_page():
    # Variables
    manager = st.session_state.manager
    user_id = st.session_state.user_id
    current_user = next((u for u in manager.users if str(u.user_id) == str(user_id)), None)
    # update_last_active()
    # st_autorefresh(interval=1000, key="refresh-all")
    # if current_user.last_active != datetime.datetime.now().strftime("%Y-%m-%d %H:%M"):
    #     current_user.last_active = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    #     manager.save()

    if not current_user:
        st.warning("User data not loaded yet, Please refresh  or log in again")
        st.stop()

    # Session states
    if "logout_triggered" in st.session_state and st.session_state.logout_triggered:
        st.session_state.logout_triggered = False
        st.rerun()

    if current_user.username and current_user.password and current_user.name and current_user.gender and current_user.bday and current_user.contact_num:
        st.session_state.profile_not_completed = "completed"
    else:
        st.session_state.profile_not_completed = "incompleted"

    if "username" not in st.session_state:
        st.session_state.username = ""

    if "chat_menu" not in st.session_state:
        st.session_state.chat_menu = ""

    if "success_msg" not in st.session_state:
        st.session_state.success_msg = ""

    if "status" not in st.session_state:
        st.session_state.status = "offline"

    if st.session_state.get("refresh") == "refresh":
        st.session_state.refresh = "unchanged"
        st.rerun()

    if st.session_state.profile_not_completed == "incompleted":
        st.warning("⚠️ Please complete your profile 😉")

    # Page design
    st.markdown("<h1 style='text-align:center'>EchoLink 🔎🔊</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("# :rainbow[EchoLink]", unsafe_allow_html=True)
    st.sidebar.write(f"@{current_user.username}")
    st.divider()
    menu = st.sidebar.radio("Menu", ["Dashboard", "Chats", "Friends",  "Profile"])
    st.sidebar.button("Logout 🚪", on_click=logout, use_container_width=True)

    if menu == "Dashboard":
        dashboard()
    elif menu == "Chats":
        chat()
    elif menu == "Friends":
        friend()
    elif menu == "Profile":
        profile()
    
    # for user in manager.users:
    #     last_active = datetime.datetime.fromisoformat(user.last_active)
    #     if (datetime.datetime.now() - last_active).seconds > 20:
    #         user.status = "offline"
    #     manager.save()


def update_last_active():
    # Reload from disk to get the latest data
    # manager = Manager.load_data()
    # user_id = st.session_state.user_id
    manager = st.session_state.manager
    username = st.session_state.username
    current_user = next((u for u in manager.users if u.username == username), None)
    st.info(current_user)
    
    if current_user:
        current_user.last_active = datetime.datetime.now().isoformat()
        manager.save()

    # Optional: update your in-session copy too
    # st.session_state.manager = manager

def logout():
    st.session_state.status = "offline"
    manager = st.session_state.manager
    manager.save()
    st.session_state.page = "login"
    st.session_state.username = None
    st.session_state.user_id = ""
    st.session_state.logout_triggered = True