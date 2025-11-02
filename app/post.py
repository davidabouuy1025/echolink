import mysql.connector
from datetime import datetime

class Post:
    def __init__(self, post_id, chat_id, user_id, image_path, created_at):
        self.post_id = post_id
        self.chat_id = chat_id
        self.user_id = user_id
        self.image_path = image_path or []
        self.created_at = created_at

    @staticmethod
    def create_post_object(chat_id, user_id, image_path):
        """Factory for creating post instances"""
        return Post(None, chat_id, user_id, image_path, datetime.now())


# ────────────────────────────────────────────────────────────────
# PostManager: Handles MySQL operations for posts
# ────────────────────────────────────────────────────────────────

class PostManager:
    def __init__(self, config):
        self.conn = mysql.connector.connect(**config)
        self.cursor = self.conn.cursor(dictionary=True)
        self.create_table()

    def create_table(self):
        """Create posts table if it doesn’t exist"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id INT NOT NULL,
                user_id INT NOT NULL,
                image_path JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
        """)
        self.conn.commit()

    def add_post(self, chat_id, user_id, image_path):
        """Insert a new post"""
        sql = """INSERT INTO posts (chat_id, user_id, image_path)
                 VALUES (%s, %s, %s)"""
        self.cursor.execute(sql, (chat_id, user_id, str(image_path)))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_posts_by_chat(self, chat_id):
        """Fetch all posts belonging to a chat"""
        self.cursor.execute("SELECT * FROM posts WHERE chat_id = %s ORDER BY created_at DESC", (chat_id,))
        rows = self.cursor.fetchall()
        return [Post(**row) for row in rows]

    def get_posts_by_user(self, user_id):
        """Fetch all posts created by a user"""
        self.cursor.execute("SELECT * FROM posts WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        rows = self.cursor.fetchall()
        return [Post(**row) for row in rows]
