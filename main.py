import streamlit as st
from gui.login.login_page import login_page
from manager.manager import ManagerSQL  # your MySQL manager

def main():
    st.set_page_config(layout='wide', page_title='EchoLink')

    # --- Initialize session state ---
    if "manager" not in st.session_state:
        st.session_state.manager = ManagerSQL()  # connect to MySQL

    if "page" not in st.session_state:
        st.session_state.page = "login"

    # --- Run login page ---
    try:
        login_page()
    except Exception as e:
        st.error(f"Error loading page: {e}")

if __name__ == "__main__":
    main()
