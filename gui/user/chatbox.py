# chatbox.py
import streamlit as st
from streamlit_chatbox import ChatBox, Markdown
import google.generativeai as genai
from datetime import datetime
import time

# --- Fetch recent mood notes from DB via manager ---
def get_recent_mood_summary(manager, user_id, limit=5):
    try:
        df = manager.get_monthly_moods_df(user_id).sort_values("date", ascending=False)
        rows = df.head(limit).to_dict(orient="records")
        return "\n".join([
            f"{r['date']} - {r['mood']} ({r.get('note','')})"
            for r in rows
        ])
    except Exception as e:
        return f"(Unable to load mood summary: {e})"

# --- Get the latest daily mood from self.mood structure ---
def get_latest_mood(self_mood, user_id):
    try:
        moods_list = next(item["moods"] for item in self_mood["moods"] if item["user_id"] == user_id)
        if moods_list:
            latest = moods_list[-1]
            return f"{latest['date']} - {latest['mood']}"
    except Exception:
        pass
    return "No recent mood found."

# --- Get recent mood activity (3, 7, 10, 20 days) ---
# def get_recent_mood(manager, user_id):
#     # Get mood records for different day ranges
#     results = {
#         3: manager.get_last_n_days_moods(user_id, 3),
#         7: manager.get_last_n_days_moods(user_id, 7),
#         10: manager.get_last_n_days_moods(user_id, 10),
#         20: manager.get_last_n_days_moods(user_id, 20)
#     }

#     none_counts = {
#         days: sum(1 for r in moods if r["mood"] is None)
#         for days, moods in results.items()
#     }
#     best_days = min(none_counts, key=none_counts.get)
#     best_result = results[best_days]
#     score = calculate_mood_score(best_result)
#     print("Score", score)
#     return score

# def calculate_mood_score(mood_data):
#     # Define mood-to-score mapping
#     mood_scores = {
#         "happy": 5,
#         "excited": 4,
#         "neutral": 3,
#         "tired": 2,
#         "sad": 1,
#         "angry": 0
#     }
#     # Extract valid mood scores (ignore None or unknown moods)
#     scores = [mood_scores[m["mood"]] for m in mood_data if m["mood"] in mood_scores]
#     # Handle error
#     if not scores:
#         return None
#     # Calculate mean
#     mean_score = sum(scores) / len(scores)
#     return round(mean_score, 2)

# --- Main function to display the chat UI ---
def chatbox(manager, user_id, self_mood):
    st.subheader("💬 Mood Chat")

    # Init chatbox safely
    chat_box = ChatBox(
        use_rich_markdown=True,
        user_theme="green",
        assistant_theme="blue",
    )

    CHAT_NAME = f"chat_{user_id}"
    chat_box.use_chat_name(CHAT_NAME)
    chat_box.init_session()
    chat_box.output_messages()

    # User input
    query = st.chat_input("How are you feeling today?")
    if not query:
        return

    # Add user message
    chat_box.user_say(query)

    # Prepare context
    recent_mood = manager.get_last_n_days_moods(user_id, 30)
    mood_summary = get_recent_mood_summary(manager, user_id)
    latest_daily_mood = get_latest_mood(self_mood, user_id)

    system_prompt = (
        "Keep everything short, simple, direct\n"
        "You are a friendly assistant that reflects on the user's emotional pattern. (2 SENTENCES)\n"
        "Use empathy in your first paragraph. In the next paragraph, give a flexible, context-aware response — (3 SENTENCES)"
        "it could be a question, short tip, or gentle reflection based on their mood trends (1 SENTENCE)\n"
        "Recent mood tracking contains 30 days mood activity of a user, you may analyze and give a point out of 10, and explain their mood tracking, HOWEVER, IF ONLY N DAYS MOOD ACTIVITY IS AVAILABLE, DONT COMPARE TO 30 DAYS, YOU MAY DO IT OUT OF 3 DAYS, 5 DAYS, 10 DAYS, OR 20 DAYS BASED ON THE BEST"
    )

    user_prompt = (
        f"Recent mood tracking: {recent_mood}\n"
        f"Recent mood history:\n{mood_summary}\n\n"
        f"Latest daily mood: {latest_daily_mood}\n\n"
        f"User says: {query}"
    )

    # Call Gemini API
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")

    try:
        with st.spinner("Generating reply... 🤖"):
            response = model.generate_content(f"{system_prompt}\n{user_prompt}")
            reply_text = response.text.strip()
    except Exception as e:
        reply_text = f"(Error from Gemini: {e})"
        st.error(reply_text)

    # Output assistant reply
    chat_box.ai_say(Markdown(reply_text, in_expander=True, expanded=True, title="Assistant"))

    if st.button("Clear Cache 🧹"):
        chat_box.init_session(clear=True)
        st.session_state.pop(chat_box._session_key, None)
        st.rerun()
    