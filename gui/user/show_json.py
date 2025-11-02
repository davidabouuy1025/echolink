import streamlit as st

def show_json():
    """
    Display user-related data directly from manager (MySQL), replacing JSON file usage.
    """
    manager = st.session_state.manager
    user_id = st.session_state.user_id

    # Fetch current user from database
    current_user = manager.get_user_by_id(user_id)
    if not current_user:
        st.warning("User data not loaded yet. Please refresh or log in again.")
        return

    # --- Prepare user data ---
    user_data = {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "name": current_user.name,
        "gender": current_user.gender,
        "birthday": current_user.bday,
        "contact_num": current_user.contact_num,
        "profile_pic": current_user.profile_pic,
        "status": current_user.status,
        "friends": [
            {"friend_id": fid, "username": manager.get_user_by_id(fid).username}
            for dt, fid in current_user.friends
        ],
        "friend_requests": [
            {"from_id": fid, "username": manager.get_user_by_id(fid).username}
            for fid in current_user.friend_request
        ]
    }

    # --- Display ---
    st.subheader("User Data")
    st.json(user_data)
