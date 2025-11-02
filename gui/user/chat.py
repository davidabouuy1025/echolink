import streamlit as st
from streamlit_autorefresh import st_autorefresh
from app.user import User
from app.manager import ManagerSQL  # make sure your manager.py is imported

def chat():
    st_autorefresh(interval=1000)

    # --- Initialize session variables ---
    if "chat_friend" not in st.session_state:
        st.session_state.chat_friend = ""
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""
    if "friend_id" not in st.session_state:
        st.session_state.friend_id = ""
    if "chat_menu" not in st.session_state:
        st.session_state.chat_menu = "Chat"

    # --- ManagerSQL instance ---
    manager: ManagerSQL = st.session_state.manager
    user_id = st.session_state.user_id

    # --- Fetch friends from DB ---
    conn = manager._get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.user_id, u.username, u.gender, u.remark
            FROM users u
            INNER JOIN friends f ON (f.user_id = %s AND f.friend_id = u.user_id)
        """, (user_id,))
        friends_data = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    if not friends_data:
        st.warning("You may want to add some friends first 🤔")
        return

    friend_disp = {f["username"]: f["user_id"] for f in friends_data}

    # --- Friend selection ---
    selected_friend = st.selectbox("Select Your Friend", friend_disp.keys())
    friend_id = friend_disp[selected_friend]
    st.session_state.chat_friend = friend_id

    # --- Friend Profile ---
    chat_friend = next((f for f in friends_data if f["user_id"] == friend_id), None)
    if chat_friend:
        st.subheader(f"@{chat_friend['username']}")
        pronoun = {"Male": "His", "Female": "Her"}.get(chat_friend["gender"], "Their")
        st.write(f"{pronoun}: {chat_friend['remark']}")

    # --- Initialize chat counter ---
    chat_key = f"chat_count_{friend_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = len(manager.get_chat_history(user_id, friend_id))

    # --- Smart rerun if new message count detected ---
    current_count = len(manager.get_chat_history(user_id, friend_id))
    if current_count != st.session_state[chat_key]:
        st.session_state[chat_key] = current_count
        st.rerun()

    # --- Load chat history ---
    chat_history = manager.get_chat_history(user_id, friend_id)

    # --- Chat UI ---
    with st.form("chat-preview"):
        if not chat_history:
            st.markdown("<span style='text-align:center'>Start your chat with your friends! 🤗</span>", unsafe_allow_html=True)

        for c in chat_history:
            if c.sender == user_id:
                st.markdown(f"<h6 style='text-align: right'>{c.content} 🟢</h6>", unsafe_allow_html=True)
            else:
                st.markdown(f"🔵 **{selected_friend}:** {c.content}")

        st.divider()
        col1, col2 = st.columns([8, 2])
        with col1:
            new_message = st.text_input("Type a message...", value=st.session_state.chat_input, label_visibility="collapsed")
        with col2:
            send_button = st.form_submit_button("Send", use_container_width=True)

        # --- Send new message ---
        if send_button and new_message.strip():
            result = manager.add_chat(user_id, friend_id, new_message)
            if result == "sent":
                st.session_state.chat_input = ""
                st.session_state[f"chat_count_{friend_id}"] = len(manager.get_chat_history(user_id, friend_id))
                st.rerun()
            else:
                st.error(result)
