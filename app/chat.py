import mysql.connector
from datetime import datetime

class Chat:
    def __init__(self, chat_id, sender, receiver, content):
        self.chat_id = chat_id
        self.sender = sender
        self.receiver = receiver
        self.content = content

    @staticmethod
    def create_chat_object(chat_id, sender, receiver, content):
        return Chat(chat_id, sender, receiver, content)

    # --- DATABASE METHODS ---
    @staticmethod
    def create_table(conn):
        """Create the chats table if it doesn't exist."""
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id VARCHAR(255) PRIMARY KEY,
                sender VARCHAR(255) NOT NULL,
                receiver VARCHAR(255) NOT NULL,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()

    @staticmethod
    def add_chat(conn, chat_obj):
        """Insert a new chat message."""
        cursor = conn.cursor()
        query = """
            INSERT INTO chats (chat_id, sender, receiver, content, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            chat_obj.chat_id,
            chat_obj.sender,
            chat_obj.receiver,
            chat_obj.content,
            datetime.now()
        ))
        conn.commit()
        cursor.close()

    @staticmethod
    def get_chats_by_user(conn, user_id):
        """Retrieve all chats involving a user (sent or received)."""
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM chats 
            WHERE sender = %s OR receiver = %s
            ORDER BY created_at ASC
        """
        cursor.execute(query, (user_id, user_id))
        chats = cursor.fetchall()
        cursor.close()
        return [Chat(**row) for row in chats]

    @staticmethod
    def get_chat_between_users(conn, user1, user2):
        """Retrieve conversation between two users."""
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM chats
            WHERE (sender = %s AND receiver = %s)
               OR (sender = %s AND receiver = %s)
            ORDER BY created_at ASC
        """
        cursor.execute(query, (user1, user2, user2, user1))
        chats = cursor.fetchall()
        cursor.close()
        return [Chat(**row) for row in chats]

    @staticmethod
    def delete_chat(conn, chat_id):
        """Delete a chat message."""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chats WHERE chat_id = %s", (chat_id,))
        conn.commit()
        cursor.close()
