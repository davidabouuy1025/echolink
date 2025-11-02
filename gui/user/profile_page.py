import streamlit as st
import datetime
from PIL import Image

def profile():
    manager = st.session_state.manager
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

    with st.form("update-form"):
        st.header("Profile")

        # --- Profile Picture ---
        profile_pic = current_user.get("profile_pic")
        if profile_pic and profile_pic.strip() != "":
            try:
                st.image(profile_pic, width=100, caption="Your Profile Picture")
            except Exception:
                st.image("https://cdn-icons-png.flaticon.com/512/3177/3177440.png", width=100, caption="Default Avatar")
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/3177/3177440.png", width=100, caption="Default Avatar")

        col1, col2 = st.columns(2)
        with col1:
            upload_file = st.file_uploader("Change Picture", type=["jpg", "jpeg", "png"])
        with col2:
            new_username = st.text_input("Username", value=current_user["username"], disabled=True)
            new_password = st.text_input("Password", value=current_user["password"], type="password")

        # --- Personal Info ---
        col3, col4 = st.columns(2)
        with col3:
            new_name = st.text_input("Name", value=current_user.get("name") or "")

            # --- Birthday handling ---
            try:
                if current_user.get("bday"):
                    bday_value = datetime.date.fromisoformat(current_user["bday"])
                else:
                    bday_value = datetime.date(1970, 1, 1)
            except ValueError:
                bday_value = datetime.date(1970, 1, 1)

            new_bday = st.date_input(
                "Birthday",
                value=bday_value,
                min_value=datetime.date(1930, 1, 1),
                max_value=datetime.date.today()
            )

            age = datetime.date.today().year - new_bday.year
            new_bday_str = new_bday.isoformat()

        with col4:
            col5, col6 = st.columns(2)
            with col5:
                st.text_input("Age", age, disabled=True)
            with col6:
                gender_options = ["His 👦", "Her 👧", "Secret"]
                current_gender = current_user.get("gender") or "Secret"
                new_gender = st.selectbox("Gender", gender_options, index=gender_options.index(current_gender))

            new_contact_num = st.text_input("Contact number", value=current_user.get("contact_num") or "")

        st.write("")
        st.write("")

        # --- Submit ---
        update_button = st.form_submit_button("Update Profile", use_container_width=True)

        if update_button:
            # Validate input (basic check)
            errors = []
            if not new_password or len(new_password) < 4:
                errors.append("Password must be at least 4 characters")
            if not new_name:
                errors.append("Name cannot be empty")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                manager.update_profile(user_id, new_password, new_name, new_bday_str, new_gender, new_contact_num, upload_file)
                st.session_state.success_msg = "Profile updated successfully ✅"
                st.rerun()

    if "success_msg" in st.session_state and st.session_state.success_msg != "":
        st.success(st.session_state.success_msg)
        st.session_state.success_msg = ""
