import mysql.connector
from datetime import datetime

class Mood:
    def __init__(self, mood_id, user_id, mood, created_at):
        self.mood_id = mood_id
        self.user_id = user_id
        self.mood = mood
        self.created_at = created_at

    @staticmethod
    def create_mood_object(user_id, mood):
        """Factory to create a new Mood object"""
        return Mood(None, user_id, mood, datetime.now())


# ────────────────────────────────────────────────────────────────
# MoodManager: Handles MySQL operations for moods
# ────────────────────────────────────────────────────────────────

class MoodManager:
    def __init__(self, config):
        self.conn = mysql.connector.connect(**config)
        self.cursor = self.conn.cursor(dictionary=True)
        self.create_table()

    def create_table(self):
        """Create moods table if not exists"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS moods (
                mood_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                mood VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)
        self.conn.commit()

    def add_mood(self, user_id, mood):
        """Insert a new mood entry"""
        sql = "INSERT INTO moods (user_id, mood) VALUES (%s, %s)"
        self.cursor.execute(sql, (user_id, mood))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_moods_by_user(self, user_id, limit=None):
        """Fetch moods for a specific user (latest first)"""
        query = "SELECT * FROM moods WHERE user_id = %s ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"
        self.cursor.execute(query, (user_id,))
        rows = self.cursor.fetchall()
        return [Mood(**row) for row in rows]

    def get_monthly_moods(self, user_id):
        """Get moods for the current month"""
        sql = """
        SELECT * FROM moods 
        WHERE user_id = %s 
        AND MONTH(created_at) = MONTH(CURRENT_DATE())
        AND YEAR(created_at) = YEAR(CURRENT_DATE())
        ORDER BY created_at DESC
        """
        self.cursor.execute(sql, (user_id,))
        rows = self.cursor.fetchall()
        return [Mood(**row) for row in rows]
