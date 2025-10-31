import streamlit as st
from gui.login.login_page import login_page

def apply_custom_css(css_file):
    with open(css_file) as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def main():
    apply_custom_css("css/style.css")
    login_page()

if __name__ == "__main__":
    main()