import streamlit as st
import datetime
import time
from app.user import User
from streamlit_autorefresh import st_autorefresh

def friend():
    # Variables
    manager = st.session_state.manager
    user_id = st.session_state.user_id
    current_user = next((u for u in manager.users if str(u.user_id) == str(user_id)), None)
    
    tab = ["Add Friend", "View Request", "Edit Status"]
    tab1, tab2, tab3 = st.tabs(tab)

    if "refresh_active" not in st.session_state:
        st.session_state.refresh_active = True

    if st.session_state.refresh_active:
        st_autorefresh(interval=3000, key="auto_refresh_key")

    with tab1:
        # Get friend's username
        with st.container():
            st.header("Add Friends 🥰")
            st.write("")
            add_friend_uname = st.text_input("Enter friend's username")
            add_button = st.button("Send Request")

            if add_button:
                check_exist = User.check_username(manager, add_friend_uname)
                
                if not check_exist:
                    st.warning(f"@{add_friend_uname} not found!")
                    return

                friend_id = User.check_username(manager, add_friend_uname)

                check_status = User.check_req(manager, current_user.user_id, add_friend_uname)

                if check_status == "not_found":
                    st.warning(f"@{add_friend_uname} not found!")
                    return
                elif check_status == "self_request":
                    st.warning("You cannot send a friend request to yourself 🤨")
                    return
                elif check_status == "already_friends":
                    st.info(f"You are already friends with @{add_friend_uname}")
                    return
                elif check_status == "already_sent":
                    st.warning(f"You have already sent a request to @{add_friend_uname}")
                    return
                elif check_status == "ok":
                    result = manager.add_friend(current_user, add_friend_uname)
                    if result:
                        st.toast(f"Friend request sent to @{add_friend_uname} ✅")

        # View recommended friends
        with st.container():
            pass

    with tab2:
        # View Friend Request
        st.header("Friend Requests 💌")
        st.write("")
        # Change list of int to list of object
        req_list = current_user.friend_request
        req_object = User.id_to_object(manager, req_list)
        # req_object [user_object, timestamp]
        if req_object:
            for index, req in enumerate(req_object):
                sender = req[0]
                timestamp = req[1]

                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.markdown(f"Request {index + 1}:", unsafe_allow_html=True)
                with col2:
                    st.markdown(f"@{sender.username}", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"{timestamp}", unsafe_allow_html=True)
                with col4:
                    accept_button = st.button("Accept", key=f"accept_{index}")
                with col5:
                    reject_button = st.button("Reject", key=f"reject_{index}")

                # Button actions (must be inside the loop!)
                if accept_button:
                    manager.accept_request(current_user, sender)
                    st.session_state.success_msg = f"You are now friends with @{sender.username}"
                    st.rerun()

                if reject_button:
                    # Remove only the request
                    current_user.friend_request.remove(req)
                    manager.save_data()
                    st.info(f"Rejected friend request from @{sender.username}")
                    st.rerun()
        else:
            st.warning("No friend request 🤔")

        manager.load_data()
            
    with tab3:
        st.header("Your Friends 👥")
        st.write("")

        gender_emoji = {
            "His 👦": "👦",
            "Her 👧": "👧",
            "Secret": "❔",
            "": "❔"
        }

        req_list = [user_id for dt, user_id in current_user.friends]
        req_object = User.id_to_object_friends(manager, req_list)

        if req_object:
            for index, friend in enumerate(req_object):
                form_key = f"dlt_{friend.user_id}"
                confirm_key = f"confirm_unfriend_{friend.user_id}"

                with st.form(key=form_key):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f"<span style='font-size:200%'><b>Friend {index+1}</b></span>", unsafe_allow_html=True)
                    with col2:
                        gender_icon = {"His 👦": "👦", "Her 👧": "👧"}.get(friend.gender, "❓")
                        st.markdown(f"<span style='font-size:170%'>#{friend.username} {gender_icon}</span>", unsafe_allow_html=True)
                    with col3:
                        status_icon = "🟢" if friend.status == "online" else "🔴"
                        st.markdown(f"<span style='font-size:170%'>{friend.status} {status_icon}</span>", unsafe_allow_html=True)
                    with col4:
                        unfriend_button = st.form_submit_button("Unfriend ❌", use_container_width=True)

                # ✅ If Unfriend clicked, set confirmation flag
                if unfriend_button:
                    st.session_state.refresh_active = False  # stop auto-refresh
                    st.session_state[confirm_key] = True

                # ✅ Confirmation prompt outside the form
                if st.session_state.get(confirm_key, False):
                    st.warning(
                        f"Are you sure you want to unfriend @{friend.username}? This will **delete all chats**.",
                        icon="⚠️"
                    )
                    colA, colB = st.columns(2)
                    with colA:
                        yes = st.button("Yes, unfriend", key=f"yes_{friend.user_id}")
                    with colB:
                        no = st.button("Cancel", key=f"no_{friend.user_id}")

                    if yes:
                        with st.spinner("Processing...", show_time=True):
                            time.sleep(1)
                            manager.unfriend(current_user, friend.user_id)
                            st.success(f"You have unfriended @{friend.username} and all chats were deleted.")
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