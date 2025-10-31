import streamlit as st
from PIL import Image

def dashboard():
    # Variables
    manager = st.session_state.manager
    user_id = st.session_state.user_id
    current_user = next((u for u in manager.users if str(u.user_id) == str(user_id)), None)

    # Session state
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    # --- Image ---
    img_path = "wallpaper/wallpaper.png"
    st.image(img_path)
    st.divider()

    # --- Dashboard Overview ---
    with st.container(border=True):
        st.header("Dashboard 📊")
        st.write("")
        disp1, disp2, disp3 = st.columns(3)
        with disp1:
            st.metric("Username", f"@{current_user.username}")

            friend_count = len(current_user.friends)
            st.metric("Friends", friend_count)
        with disp2:
            friend_request = len(current_user.friend_request)
            st.metric("Friend Requests", friend_request)

            msg_count = len(current_user.chat_ids)
            st.metric("Total Message Sent", msg_count)
        with disp3:
            if current_user.profile_pic:
                st.image(current_user.profile_pic, width='content', caption="Your Profile Picture")
            else:
                st.image("https://cdn-icons-png.flaticon.com/512/3177/3177440.png", width=100, caption="Default Avatar")

    st.divider()

    # --- Personal Posts ---
    with st.container(border=True):
        col1, col2= st.columns(2)
        with col1:
            st.header("Your Posts 📸🦋")
            post_button = st.button("Post", width=200)
        with col2:
            st.session_state.uploaded_file = st.file_uploader("Upload Posts", type=["jpg", "jpeg", "png"])

        if post_button:
            if st.session_state.uploaded_file:
                result = manager.add_post(user_id, st.session_state.uploaded_file)
                st.session_state.uploaded_file = None
                st.rerun()
            else:
                st.error("⚠️ You can't post without uploading anything")

        st.write("")
        st.warning("After uploading, please click the 'X' to remove the previous photo")
        st.write("")

        # Get all path
        post_paths = manager.get_post(user_id)

        if post_paths:
            # Number of columns
            num_cols = 3

            # Create columns
            cols = st.columns(num_cols)

            for idx, photo_path in enumerate(post_paths):
                # Open image
                img = Image.open(photo_path)

                # Determine which column to put this image in
                col = cols[idx % num_cols]
                col.image(img, width=300)
