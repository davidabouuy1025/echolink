import mysql.connector
from datetime import datetime

class User:
    def __init__(self, user_id, username, password, name, gender, bday, contact_num,
                 profile_pic, status, last_active, remark, chat_ids, friends, friend_request):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.name = name
        self.gender = gender
        self.bday = bday
        self.contact_num = contact_num
        self.profile_pic = profile_pic
        self.status = status
        self.last_active = last_active
        self.remark = remark
        self.chat_ids = chat_ids or []
        self.friends = friends or []
        self.friend_request = friend_request or []

    @staticmethod
    def create_user_object(user_id, username, password, current_dt):
        """Factory method for creating new users"""
        return User(user_id, username, password, "", "", "", "", "", "online",
                    current_dt, "", [], [], [])

# ────────────────────────────────────────────────────────────────
# MANAGER (Database access layer)
# ────────────────────────────────────────────────────────────────

class UserManager:
    def __init__(self, config):
        self.conn = mysql.connector.connect(**config)
        self.cursor = self.conn.cursor(dictionary=True)
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL,
                name VARCHAR(100),
                gender VARCHAR(10),
                bday DATE,
                contact_num VARCHAR(20),
                profile_pic VARCHAR(255),
                status VARCHAR(20),
                last_active DATETIME,
                remark TEXT,
                chat_ids JSON,
                friends JSON,
                friend_request JSON
            );
        """)
        self.conn.commit()

    def add_user(self, username, password):
        now = datetime.now()
        sql = """INSERT INTO users (username, password, status, last_active, chat_ids, friends, friend_request)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        self.cursor.execute(sql, (username, password, "online", now, "[]", "[]", "[]"))
        self.conn.commit()

    def get_user_by_username(self, username):
        self.cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = self.cursor.fetchone()
        if not row:
            return None
        return User(**row)

    def validate_username(self, username):
        self.cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        return self.cursor.fetchone() is not None
    
    def validate_password(password: str):
        if len(password) < 6:
            return "Password must be at least 6 characters"
        # Add more rules here if needed
        return None

    def login_user(self, username, password):
        self.cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = self.cursor.fetchone()
        if not user:
            return False, "Username not found"
        elif user["password"] != password:
            return False, "Username and password don't match"
        return True, "Successfully logged in"

    def update_status(self, user_id, status):
        self.cursor.execute("UPDATE users SET status = %s WHERE user_id = %s", (status, user_id))
        self.conn.commit()
