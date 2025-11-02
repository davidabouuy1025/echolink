import streamlit as st
import datetime
import time
from gui.user.dashboard import dashboard
from gui.user.moods import moods
from gui.user.chat import chat
from gui.user.friend import friend
from gui.user.profile_page import profile
from gui.user.show_json import show_json  # Optional

def user_page():
    # --- Variables ---
    manager = st.session_state.manager
    user_id = st.session_state.user_id

    # Fetch user from DB
    current_user = manager.get_user_by_id(user_id)

    if not current_user:
        st.warning("User data not loaded yet. Please refresh or log in again.")
        st.stop()

    # --- Profile completeness ---
    profile_fields = [current_user.username, current_user.password, current_user.name,
                      current_user.gender, current_user.bday, current_user.contact_num]
    st.session_state.profile_not_completed = "completed" if all(profile_fields) else "incompleted"

    # --- Initialize session_state keys ---
    defaults = {
        "username": "",
        "chat_menu": "",
        "success_msg": "",
        "status": "offline",
        "refresh": "unchanged",
        "logout_triggered": False,
        "chat_friend": "",
        "chat_input": "",
        "friend_id": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # --- Auto-refresh handling ---
    if st.session_state.get("refresh") == "refresh":
        st.session_state.refresh = "unchanged"
        st.rerun()

    # --- Prompt profile completion ---
    if st.session_state.profile_not_completed == "incompleted":
        st.warning("⚠️ Please complete your profile 😉")

    # --- Page design ---
    st.markdown("<h1 style='text-align:center'>EchoLink 🔎🔊</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("# :rainbow[EchoLink]", unsafe_allow_html=True)
    st.sidebar.write(f"@{current_user.username}")
    st.divider()

    menu = st.sidebar.radio("Menu", ["Dashboard", "Moods", "Chats", "Friends", "Profile"])
    st.sidebar.button("Logout 🚪", on_click=logout, args=(manager, user_id), use_container_width=True)

    # --- Menu routing ---
    if menu == "Dashboard":
        dashboard()
    elif menu == "Moods":
        moods()
    elif menu == "Chats":
        chat()
    elif menu == "Friends":
        friend()
    elif menu == "Profile":
        profile()

    # --- Show success message ---
    if st.session_state.success_msg:
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = ""


# --- Status & Logout functions ---

def set_offline(manager, user_id):
    """
    Set user status to offline in the database.
    """
    manager.update_status(user_id, "offline")


def logout(manager, user_id):
    """
    Logs out the user, clears session state, and sets offline status.
    """
    set_offline(manager, user_id)
    time.sleep(0.5)

    # Clear relevant session_state keys
    keys_to_clear = [
        "page", "username", "user_id", "chat_menu", "profile_not_completed",
        "chat_friend", "chat_input", "friend_id", "success_msg",
        "refresh", "logout_triggered"
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)

    # Set page to login
    st.session_state.page = "login"
