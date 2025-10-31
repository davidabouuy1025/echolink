import streamlit as st
import datetime
from app.user import User
from streamlit_autorefresh import st_autorefresh

def friend():
    # Variables
    manager = st.session_state.manager
    user_id = st.session_state.user_id
    current_user = next((u for u in manager.users if str(u.user_id) == str(user_id)), None)
    
    tab = ["Add Friend", "View Request", "Edit Status"]
    tab1, tab2, tab3 = st.tabs(tab)

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
                    result = manager.add_friend(current_user.user_id, add_friend_uname)
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
                    result = manager.add_chat(current_user, sender, datetime.datetime.now().isoformat())
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

        st_autorefresh(5000, key="friend_request_autorefresh")
        manager.load_data()
            
    with tab3:
        st_autorefresh(3000, key="friend_status_autorefresh")

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
                with st.form(key=f"dlt_{friend.user_id}"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.markdown(f"<span style='font-size:200%'><b>Friend {index+1}</b></span>", unsafe_allow_html=True)
                    with col2:
                        if friend.gender == "His 👦":
                            gender_icon = "👦"
                        elif friend.gender == "Her 👧":
                            gender_icon = "👧"
                        else:
                            gender_icon = "❓"

                        st.markdown(f"<span style='font-size:170%'>#{friend.username} {gender_icon}</span>", unsafe_allow_html=True)
                    with col3:
                        if friend.status == "online":
                            status_icon = "🟢"
                        else:
                            status_icon = "🔴"

                        st.markdown(f"<span style='font-size:170%'>{friend.status} {status_icon}</span>", unsafe_allow_html=True)
                    with col4:
                        unfriend_button = st.form_submit_button("Unfriend ❌", use_container_width=True)

                    # ✅ Confirmation Prompt
                    if unfriend_button:
                        confirm = st.warning(
                            f"Are you sure you want to unfriend {friend.username}? This will delete all chats.",
                            icon="⚠️"
                        )
                        colA, colB = st.columns(2)
                        with colA:
                            yes = st.form_submit_button("Yes, unfriend", key=f"yes_{friend.user_id}")
                        with colB:
                            no = st.form_submit_button("Cancel", key=f"no_{friend.user_id}")

                        if yes:
                            result = manager.unfriend(current_user, friend.user_id)
                            st.success(f"You have unfriended {friend.username} and all chats were deleted.")
                            st.rerun()
                        elif no:
                            st.info("Cancelled. No changes made.")
        else:
            st.warning("No friends found 🥹")
            
    if "success_msg" in st.session_state and st.session_state.success_msg != "":
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = ""