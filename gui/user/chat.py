import datetime
import streamlit as st
import os
from streamlit_autorefresh import st_autorefresh
from app.user import User


def chat():
    # --- Smart auto-refresh when chat file changes (not working) ---
    # chat_file = "data/chat.json"
    # if os.path.exists(chat_file):
    #     last_modified = os.path.getmtime(chat_file)
    #     prev = st.session_state.get("chat_file_mtime", 0)
        
    #     if last_modified != prev:
    #         st.session_state.chat_file_mtime = last_modified
    #         st_autorefresh(interval=100, key="chat_refresh_once")

    # chat_file = "data/chat.json"
    # last_modified = os.path.getmtime(chat_file)
    # print(last_modified)

    st_autorefresh(interval=1500)

    if "chat_friend" not in st.session_state:
        st.session_state.chat_friend = ""

    # --- Variables ---
    manager = st.session_state.manager
    user_id = st.session_state.user_id

    st.subheader("Your Friends")
    current_user = next((u for u in manager.users if str(u.user_id) == str(user_id)), None)

    friends_disp = {user.user_id: user.username for user in manager.users}
    # st.info(friends_disp)

    friend_list = [friends_disp[friend] for dt, friend in current_user.friends]
    # st.info(friend_list)

    friend_disp = {f"{u.username}": u.user_id for u in manager.users if str(u.username) in friend_list}
    # st.info(friend_disp)

    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""

    if not friend_list:
        st.warning("You may want to add some friends first 🤔")
        return
    
    if "friend_id" not in st.session_state:
        st.session_state.friend_id = ""

    if "chat" not in st.session_state:
        st.session_state.chat = []
    
    # --- Load previous chat ---
    friend_id = st.session_state.friend_id
    chat_history = manager.get_chat_history(current_user.user_id, friend_id)

    # --- Input box ---
    selected_friend = st.selectbox("Select Your Friend", friend_disp.keys())
    friend_id = friend_disp[selected_friend]
    st.session_state.chat_friend = friend_id
    chat_friend = manager.return_user(friend_id)

    # --- Friend Profile ---
    with st.container(border=True):
        if st.session_state.chat_friend != "":
            mood_emojis = {
                "happy": "Happy 😊",
                "sad": "Sad 😢",
                "angry": "Angry 😡",
                "neutral": "Neutral 😐",
                "excited": "Excited 🤩",
                "tired": "Tired 😴",
                "no": "❌"
            }
                
            chat_friend_mood = next((m for m in manager.moods if m.user_id == st.session_state.chat_friend), None)
            if chat_friend_mood:
                today_mood_entry = next((m["mood"] for m in chat_friend_mood.moods if m["date"] == datetime.datetime.now().strftime("%Y-%m-%d")), "no")
            else:
                today_mood_entry = "no"
            # st.info(today_mood_entry)
            friend_mood = mood_emojis[today_mood_entry]

            if chat_friend:
                st.subheader(f"@{chat_friend.username}")
                st.write("")
                if chat_friend.gender == "Male":
                    pronoun = "His"
                elif chat_friend.gender == "Female":
                    pronoun = "Her"
                else:
                    pronoun = "Them"
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Mood", friend_mood)
                with col2:
                    st.metric("Remark", chat_friend.remark)

    # # --- Initialize chat counter if not exist ---
    # chat_key = f"chat_count_{friend_id}"
    # if chat_key not in st.session_state:
    #     st.session_state[chat_key] = len(manager.get_chat_history(user_id, friend_id))

    # --- Smart rerun if new message count detected ---
    # current_count = len(manager.get_chat_history(user_id, friend_id))
    # if current_count != st.session_state[chat_key]:
    #     st.session_state[chat_key] = current_count
    #     st.rerun()

    with st.form("chat-preview"):
        # --- Load previous chat ---
        manager.load_data()
        chat_history = manager.get_chat_history(current_user.user_id, friend_id)
        st.info(chat_history[-1].content)

        # No chats found
        if not chat_history:
            st.markdown("<span style='text-align:center'>Start your chat with your friends! 🤗</span>", unsafe_allow_html=True)
        
        # Display chat
        for c in chat_history:
            if c.sender == current_user.user_id:
                st.markdown(f"<h6 style='text-align: right'>{c.content} 🟢</h6>", unsafe_allow_html=True)
            else:
                st.markdown(f"🔵 **{selected_friend}:** {c.content}")

        st.divider()
        col1, col2 = st.columns([8, 2])
        with col1:
            new_message = st.text_input("Type a message...", value=st.session_state.chat_input, label_visibility="collapsed")
        with col2:
            send_button = st.form_submit_button("Send", use_container_width=True)

        # --- When message is sent ---
        if send_button and new_message.strip():
            result = manager.add_chat(current_user.user_id, friend_id, new_message)
            if result == "sent":
                st.session_state.friend_id = friend_id
                st.session_state.chat_menu = "Chat"
                st.session_state[f"chat_count_{friend_id}"] = len(manager.get_chat_history(user_id, friend_id))
                st.session_state.chat_input = ""
                st.rerun()
            else:
                st.error(result)

