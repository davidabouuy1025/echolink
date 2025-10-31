import streamlit as st
import json

def show_json():
    manager = st.session_state.manager
    user_id = st.session_state.user_id
    current_user = next((u for u in manager.users if str(u.user_id) == str(user_id)), None)
    
    with open("data/chat.json", "r") as f:
        users = json.load(f)

    st.subheader("User Data")
    st.json(users)