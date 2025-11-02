import streamlit as st
import datetime
from PIL import Image

def dashboard():
    manager = st.session_state.manager  # ManagerSQL instance
    user_id = st.session_state.user_id

    # --- Fetch user info from DB ---
    conn = manager._get_conn()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
        current_user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    # Session state
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    # --- Image ---
    img_path = "wallpaper/wallpaper.png"
    st.image(img_path)
    st.divider()

    # --- Dashboard Overview ---
    with st.container():
        st.header("Dashboard 📊")
        disp1, disp2, disp3 = st.columns(3)
        with disp1:
            st.metric("Username", f"@{current_user['username']}")

            # Friend count from DB
            conn = manager._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM friends WHERE user_id=%s", (user_id,))
            friend_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            st.metric("Friends", friend_count)
        with disp2:
            # Friend requests
            conn = manager._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM friend_requests WHERE receiver_id=%s", (user_id,))
            friend_request = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            st.metric("Friend Requests", friend_request)

            # Total messages sent
            conn = manager._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chats WHERE sender=%s", (user_id,))
            msg_count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            st.metric("Total Messages Sent", msg_count)
        with disp3:
            if current_user['profile_pic']:
                st.image(current_user['profile_pic'], width='content', caption="Your Profile Picture")
            else:
                st.image("https://cdn-icons-png.flaticon.com/512/3177/3177440.png", width=100, caption="Default Avatar")

    st.divider()

    with st.container():
        st.header("Shortcut 🖇️")
        col1, col2 = st.columns(2)

        # --- Remark ---
        with col1:
            st.subheader("Remark 💬")
            remark = st.text_area(label="Remark", placeholder="Anything you wanna share?", value=current_user['remark'], label_visibility='hidden')
            if st.button("Save Remark"):
                manager.add_remark(user_id, remark)
                st.toast(f"Remark for {datetime.datetime.now().strftime('%Y-%m-%d')} updated!")

        # --- Mood ---
        with col2:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            user_moods = manager.get_user_moods(user_id)
            today_entry = next((m for m in user_moods.moods if m['date'] == today), None)

            mood_options = ["happy", "sad", "angry", "neutral", "excited", "tired"]
            mood_emojis = {
                "happy": "Happy 😊",
                "sad": "Sad 😢",
                "angry": "Angry 😡",
                "neutral": "Neutral 😐",
                "excited": "Excited 🤩",
                "tired": "Tired 😴"
            }

            if today_entry:
                default_index = mood_options.index(today_entry['mood'])
            else:
                default_index = 3  # Neutral

            st.subheader("Today Mood 🤩")
            mood_selected = st.selectbox("Today's Mood:", options=list(mood_emojis.values()), index=default_index)

            if st.button("Save Mood"):
                mood_key = [k for k, v in mood_emojis.items() if v == mood_selected][0]
                manager.set_daily_mood(user_id, mood_key)
                st.toast(f"Mood for {today} saved as {mood_selected}!")

    st.divider()

    # --- Personal Posts ---
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.header("Your Posts 📸🦋")
            post_button = st.button("Post")
        with col2:
            st.session_state.uploaded_file = st.file_uploader(
                "Upload Posts",
                type=["jpg", "jpeg", "png"],
                key=f"file_uploader_{st.session_state.uploader_key}"
            )

        if post_button:
            if st.session_state.uploaded_file:
                manager.add_post(user_id, st.session_state.uploaded_file)
                st.session_state.uploaded_file = None
                st.session_state.uploader_key += 1
                st.rerun()
            else:
                st.error("⚠️ You can't post without uploading anything")

        # Display posts
        post_paths = manager.get_post(user_id)
        if post_paths:
            num_cols = 3
            cols = st.columns(num_cols)
            for idx, photo_path in enumerate(post_paths):
                try:
                    img = Image.open(photo_path)
                    col = cols[idx % num_cols]
                    col.image(img, width=300)
                except FileNotFoundError:
                    st.write(f"⚠️ File '{photo_path}' Not Found")
