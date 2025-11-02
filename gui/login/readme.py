def readme():
    import streamlit as st
    st.markdown("""
        # EchoLink: Social & Mood Tracking App

        EchoLink is a social networking web application built with Streamlit, designed to connect friends, track daily moods, and provide a visual monthly mood calendar. Users can interact via chats, post updates, and explore their friends’ mood trends.


        ### Table of Contents

        - Features

        - Demo

        - Installation

        - Usage

        - Data Structure

        - Mood Tracking

        - Recommended Friends Algorithm

        - Tech Stack

        - Contributing

        - License

        # Test Account
        - Username: ```user1```
        - Password: ```userPW101```

        <br>

        # Features

        **User Authentication**: Login and session tracking.

        **Daily Mood Tracker**: Input your daily mood with emoji representation.

        **Monthly Mood Calendar**: Visualize your mood across the month.

        **Friend Interaction**: Chat with friends and see their mood.

        **Recommended Friends**: Suggest friends based on common interests or interactions.

        **Post Updates**: Create and view posts.

        **Persistent Data**: All data stored in JSON files (users.json, chat.json, post.json, mood.json).

        <br>

        # Demo

        Display your mood with large emojis.

        White calendar cells with no background color.

        View last 5 days of moods and monthly calendar.

        ### Installation
        Clone the repository

        ```python
        git clone https://github.com/yourusername/echolink.git
        cd echolink
        ```

        Create and activate virtual environment
        ```python
        python -m venv venv
        source venv/bin/activate   # Linux/Mac
        venv\Scripts\activate      # Windows
        ```

        Install dependencies
        ```python
        pip install -r requirements.txt
        ```

        Run the app
        ```python
        streamlit run main.py
        ```
        ## Usage

        - Login with your username and password.

        - Navigate to Mood Tracker to input today’s mood.

        - View your Last 5 Days Mood or Monthly Mood Calendar.

        - Chat with friends and view their moods in real-time.

        - Create posts in the Post section.

        Data Structure:
        ```python
        users.json
        {
        "users": [
            {
            "user_id": 1,
            "username": "user1",
            "password": "userPW101",
            "name": "John Doe",
            "gender": "Male",
            "bday": "1990-01-01",
            "contact_num": "0123456789",
            "profile_pic": "",
            "status": "online",
            "last_active": "2025-11-01 14:32:10",
            "chat_ids": [1],
            "friends": [[2, "2025-10-29"]],
            "friend_request": [[3, "2025-10-29"]]
            }
        ],
        "next_user_id": 2
        }

        mood.json
        {
        "moods": [
            {
            "user_id": 1,
            "moods": [
                {"date": "2025-11-01", "mood": "😊"},
                {"date": "2025-11-02", "mood": "😴"}
            ]
            }
        ]
        }

        ```

        ## Mood Tracking

        **Daily Mood Check-in**: Only today’s mood can be updated.

        **Last 5 Days Mood**: Displays the last 5 days’ moods with emojis; empty days show ❌.

        **Monthly Mood Calendar**: Large emoji representation, white background, easy visualization.

        ## Recommended Friends Algorithm

        Algorithm Idea:

        Compare mutual friends count.

        Compare similar mood patterns over last 5 days.

        Suggest users with highest combined similarity score.

        score = mutual_friends_count + mood_similarity_count
        recommended = sorted(users, key=lambda u: score[u.user_id], reverse=True)

        ## Tech Stack

        Frontend / Web App: Streamlit

        Backend / Data Storage: JSON files

        Data Processing: Python (datetime, pandas)

        Mood Calendar: streamlit-calendar + custom CSS

        Optional AI Chatbox: OpenAI API for mood analysis

        ## Contributing

        **Fork the repository**

        Create your feature branch: git checkout -b feature/your-feature

        Commit your changes: ```git commit -m "Add feature"```

        Push to the branch: ```git push origin branch`

        Open a Pull Request

        ## License

        https://github.com/davidabouuy1025/echolink.git (HD)
                
        https://github.com/davidabouuy1025/echo.git (D)
                
        https://echolink.streamlit.app/ (Deployment)
    """)