import streamlit as st
import datetime
import time
from app.user import User
from streamlit_autorefresh import st_autorefresh


def friend():
    manager = st.session_state.manager
    user_id = st.session_state.user_id
    current_user = manager.get_user_by_id(user_id)  # MySQL fetch

    tab1, tab2, tab3 = st.tabs(["Add Friend", "View Request", "Edit Status"])

    if "refresh_active" not in st.session_state:
        st.session_state.refresh_active = True

    if st.session_state.refresh_active:
        st_autorefresh(interval=3000, key="auto_refresh_key")

    # --- Add Friend Tab ---
    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.header("Add Friends 🥰")
            add_friend_uname = st.text_input("Enter friend's username")
            add_button = st.button("Send Request")

            if add_button:
                friend_obj = manager.get_user_by_username(add_friend_uname)

                if not friend_obj:
                    st.warning(f"@{add_friend_uname} not found!")
                else:
                    status = manager.check_friend_status(current_user.user_id, friend_obj.user_id)

                    if status == "self_request":
                        st.warning("You cannot send a friend request to yourself 🤨")
                    elif status == "already_friends":
                        st.info(f"You are already friends with @{add_friend_uname}")
                    elif status == "already_sent":
                        st.warning(f"You have already sent a request to @{add_friend_uname}")
                    elif status == "ok":
                        manager.add_friend_request(current_user.user_id, friend_obj.user_id)
                        st.toast(f"Friend request sent to @{add_friend_uname} ✅")

        with col2:
            st.header("Recommendation")
            st.write("No suggested friends currently")

        st.divider()

        # --- Your Friends List ---
        st.header("Find Your Friend 😛")
        friends = manager.get_friends(current_user.user_id)
        if not friends:
            st.error("No friends found ☹️")
        else:
            friend_usernames = [f["username"] for f in friends]
            choose_username = st.selectbox("Select friend", friend_usernames)
            if st.button("Load Profile 🤩"):
                st.session_state.refresh_active = False
                friend_obj = manager.get_user_by_username(choose_username)
                if friend_obj:
                    st.divider()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(friend_obj.profile_pic or "https://cdn-icons-png.flaticon.com/512/3177/3177440.png", width=200)
                        st.markdown(f"## @{friend_obj.username}")
                        st.markdown(f"**Name:** {friend_obj.name}")
                        st.markdown(f"**Gender:** {friend_obj.gender}")
                        st.markdown(f"**Birthday:** {friend_obj.bday}")
                        st.markdown(f"**Status:** {friend_obj.status}")

                    with col2:
                        st.subheader(f"@{friend_obj.username}'s Posts 🖼️")
                        posts = manager.get_posts(friend_obj.user_id)
                        if posts:
                            for post in posts:
                                st.markdown(f"**Posted on:** {post['datetime']}")
                                st.image(post["image_path"], width=300)
                                st.divider()
                        else:
                            st.info("No posts yet 🥹")
                else:
                    st.error("Friend not found ❌")

    # --- Friend Requests Tab ---
    with tab2:
        st.header("Friend Requests 💌")
        requests = manager.get_friend_requests(current_user.user_id)
        if requests:
            for idx, req in enumerate(requests):
                sender = manager.get_user_by_id(req["sender_id"])
                timestamp = req["timestamp"]
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.markdown(f"Request {idx + 1}:")
                with col2:
                    st.markdown(f"@{sender.username}")
                with col3:
                    st.markdown(f"{timestamp}")
                with col4:
                    accept_button = st.button("Accept", key=f"accept_{idx}")
                with col5:
                    reject_button = st.button("Reject", key=f"reject_{idx}")

                if accept_button:
                    manager.accept_request(current_user.user_id, sender.user_id)
                    st.session_state.success_msg = f"You are now friends with @{sender.username}"
                    st.rerun()
                if reject_button:
                    manager.reject_request(current_user.user_id, sender.user_id)
                    st.info(f"Rejected friend request from @{sender.username}")
                    st.rerun()
        else:
            st.warning("No friend request 🤔")

    # --- Edit Status / Unfriend Tab ---
    with tab3:
        st.header("Your Friends 👥")
        friends = manager.get_friends(current_user.user_id)
        if friends:
            for idx, f in enumerate(friends):
                user_obj = manager.get_user_by_id(f["friend_id"])
                form_key = f"dlt_{user_obj.user_id}"
                confirm_key = f"confirm_unfriend_{user_obj.user_id}"
                with st.form(key=form_key):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f"<span style='font-size:200%'><b>Friend {idx+1}</b></span>", unsafe_allow_html=True)
                    with col2:
                        gender_icon = {"His 👦": "👦", "Her 👧": "👧"}.get(user_obj.gender, "❔")
                        st.markdown(f"<span style='font-size:170%'>#{user_obj.username} {gender_icon}</span>", unsafe_allow_html=True)
                    with col3:
                        status_icon = "🟢" if user_obj.status == "online" else "🔴"
                        st.markdown(f"<span style='font-size:170%'>{user_obj.status} {status_icon}</span>", unsafe_allow_html=True)
                    with col4:
                        unfriend_button = st.form_submit_button("Unfriend ❌", use_container_width=True)

                if unfriend_button:
                    st.session_state.refresh_active = False
                    st.session_state[confirm_key] = True

                if st.session_state.get(confirm_key, False):
                    st.warning(f"Are you sure you want to unfriend @{user_obj.username}? This will **delete all chats**.", icon="⚠️")
                    colA, colB = st.columns(2)
                    with colA:
                        yes = st.button("Yes, unfriend", key=f"yes_{user_obj.user_id}")
                    with colB:
                        no = st.button("Cancel", key=f"no_{user_obj.user_id}")

                    if yes:
                        with st.spinner("Processing...", show_time=True):
                            time.sleep(1)
                            manager.unfriend(current_user.user_id, user_obj.user_id)
                            st.success(f"You have unfriended @{user_obj.username} and all chats were deleted.")
                            st.session_state[confirm_key] = False
                            st.session_state.refresh_active = True
                            st.rerun()
                    elif no:
                        st.session_state[confirm_key] = False
                        st.session_state.refresh_active = True
                        st.session_state.success_msg = "Cancelled. No changes made."
                        st.rerun()

        else:
            st.warning("No friends found 🥹")

    if "success_msg" in st.session_state and st.session_state.success_msg != "":
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = ""
