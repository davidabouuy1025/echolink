# chatbox.py
import streamlit as st
from streamlit_chatbox import ChatBox, Markdown
import google.generativeai as genai
from datetime import datetime

# --- Fetch recent mood summary from MySQL ---
def get_recent_mood_summary(manager, user_id, limit=5):
    try:
        moods = manager.get_last_n_days_moods(user_id, 30)  # last 30 days
        # Sort by date descending
        moods.sort(key=lambda x: x["date"], reverse=True)
        recent = moods[:limit]
        return "\n".join([f"{r['date']} - {r['mood']} ({r.get('note','')})" for r in recent])
    except Exception as e:
        return f"(Unable to load mood summary: {e})"

# --- Get latest mood ---
def get_latest_mood(manager, user_id):
    try:
        moods = manager.get_last_n_days_moods(user_id, 1)
        if moods:
            latest = moods[0]
            return f"{latest['date']} - {latest['mood']}"
    except Exception:
        pass
    return "No recent mood found."

# --- Main chatbox ---
def chatbox(manager, user_id):
    st.subheader("💬 Mood Chat")

    chat_box = ChatBox(
        use_rich_markdown=True,
        user_theme="green",
        assistant_theme="blue",
    )
    CHAT_NAME = f"chat_{user_id}"
    chat_box.use_chat_name(CHAT_NAME)
    chat_box.init_session()
    chat_box.output_messages()

    query = st.chat_input("How are you feeling today?")
    if not query:
        return

    chat_box.user_say(query)

    # --- Prepare context ---
    recent_mood = manager.get_last_n_days_moods(user_id, 30)
    mood_summary = get_recent_mood_summary(manager, user_id)
    latest_daily_mood = get_latest_mood(manager, user_id)

    system_prompt = (
        "Keep everything short, simple, direct.\n"
        "You are a friendly assistant that reflects on the user's emotional pattern (2 SENTENCES).\n"
        "Use empathy in your first paragraph. In the next paragraph, give a flexible, context-aware response (3 SENTENCES), "
        "it could be a question, short tip, or gentle reflection based on their mood trends (1 SENTENCE).\n"
        "Recent mood tracking contains up to 30 days of mood activity of a user. "
        "Give a score out of 10 and explain their mood tracking, but if only fewer days are available, scale appropriately (3, 5, 10, or 20 days)."
    )

    user_prompt = (
        f"Recent mood tracking (last 30 days): {recent_mood}\n"
        f"Recent mood summary:\n{mood_summary}\n\n"
        f"Latest daily mood: {latest_daily_mood}\n\n"
        f"User says: {query}"
    )

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")

    try:
        with st.spinner("Generating reply... 🤖"):
            response = model.generate_content(f"{system_prompt}\n{user_prompt}")
            reply_text = response.text.strip()
    except Exception as e:
        reply_text = f"(Error from Gemini: {e})"
        st.error(reply_text)

    chat_box.ai_say(Markdown(reply_text, in_expander=True, expanded=True, title="Assistant"))

    if st.button("Clear Cache 🧹"):
        chat_box.init_session(clear=True)
        st.session_state.pop(chat_box._session_key, None)
        st.rerun()
