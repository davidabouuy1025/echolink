import streamlit as st
import datetime
import pandas as pd
import calendar
from streamlit_calendar import calendar
from gui.user.chatbox import chatbox

import subprocess
import sys

try:
    from streamlit_calendar import calendar
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit-calendar==1.3.1"])
    from streamlit_calendar import calendar

def display_mood_calendar(events):
    options = {
        "initialView": "dayGridMonth",
        "eventDisplay": "block",
        "height": "700px",
        "eventTextColor": "black",
        "eventBackgroundColor": "transparent"
    }

    custom_css = """
        :focus {
            outline: none !important;
            box-shadow: none !important;
        }
        .fc-event-title {
            font-size: 2rem !important;
            text-align: center !important;
        }
        .fc-day:active {
            outline: none !important;
            border: none !important;
            box-shadow: none !important;
        }
        .fc-daygrid-day {
            border: 0px solid #eee !important;
        }
    """

    calendar(events=events, options=options, custom_css=custom_css)

def moods():
    manager = st.session_state.manager
    user_id = st.session_state.user_id

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

    mood_emojis1 = {
        "happy": "😊",
        "sad": "😢",
        "angry": "😡",
        "neutral": "😐",
        "excited": "🤩",
        "tired": "😴"
    }

    if "update_mood_msg" not in st.session_state:
        st.session_state.update_mood_msg = ""

    tab1, tab2 = st.tabs(["Mood Tracker", "MoodLink (chatbox)"])


    with tab1:
        # Set default index
        if today_entry:
            default_mood = mood_emojis[today_entry['mood']]
            default_index = list(mood_emojis.values()).index(default_mood)
        else:
            default_index = 3  # Neutral 😐

        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True, height='stretch'):
                    st.header("Last 5 Days 🗓️")
                    last_5 = manager.get_last_n_days_moods(user_id, n=5)
                    # st.info(last_5)
                    if not last_5:
                        st.info("No mood records yet.")
                    else:
                        cols = st.columns(5)

                        for index, mood_entry in enumerate(last_5):
                            with cols[index]:
                                emoji = mood_emojis1.get(mood_entry.get("mood"), "❌")
                                st.markdown(
                                    f"<div style='text-align:center; font-size:120%;'>"
                                    f"<b>{mood_entry['date']}</b><br>"
                                    f"<span style='font-size:250%;'>{emoji}</span>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )

            with col2:
                with st.container(border=True, height='stretch'):
                    st.header("Today Mood 🤩")
                    mood_selected = st.selectbox(
                        "Today's Mood:",
                        options=list(mood_emojis.values()),
                        index=default_index
                    )

                    if st.button("Save Mood"):
                        mood_key = [k for k, v in mood_emojis.items() if v == mood_selected][0]
                        manager.set_daily_mood(user_id, mood_key)
                        st.session_state.update_mood_msg = f"Mood for {today} saved as {mood_selected}!"

                    if "update_mood_msg" in st.session_state and st.session_state.update_mood_msg != "":
                        st.success(st.session_state.update_mood_msg)
                        del st.session_state.update_mood_msg

        st.divider()

        # --- Monthly Mood View ---
        with st.container():
            
            df = manager.get_monthly_moods_df(user_id)
            # st.info(df)
            events = []
            for _, row in df.iterrows():
                mood = row["mood"]
                events.append({
                    "title": row["mood"],
                    "start": row["date"].isoformat(),
                    "end": row["date"].isoformat()
                })
            display_mood_calendar(events)

    with tab2:
        current_mood = manager.get_user_moods(user_id)
        chatbox(manager, user_id, current_mood)

    