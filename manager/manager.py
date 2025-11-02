# manager_sql.py
import os
import json
import datetime
import calendar as cal
import pandas as pd
from PIL import Image
import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling
import streamlit as st
from typing import Optional, List, Tuple

# import your domain classes (must be on pythonpath)
from app.user import User, UserManager
from app.chat import Chat
from app.post import Post, PostManager
from app.mood import Mood, MoodManager\

# Configure this to your environment / Streamlit secrets.
# You can pass a dict to Manager(...) or set these env vars.
DEFAULT_DB_CONFIG = {
    "host": st.secrets["mysql"]["host"],
    "port": int(st.secrets["mysql"]["port"]),
    "user": st.secrets["mysql"]["user"],
    "password": st.secrets["mysql"]["password"],
    "database": st.secrets["mysql"]["database"],
    "autocommit": False,
}


class ManagerSQL:
    """
    MySQL-backed Manager to replace the JSON-based Manager.
    Uses mysql.connector with connection pooling and transactions.
    Public method names and return types match your previous Manager.
    """

    def __init__(self, db_config: dict = None, pool_name: str = "echolink_pool", pool_size: int = 5):
        self.db_config = db_config or DEFAULT_DB_CONFIG
        # create database if not exists (best-effort)
        self._ensure_database()
        # init connection pool
        self.pool = pooling.MySQLConnectionPool(pool_name=pool_name, pool_size=pool_size, **self.db_config)
        # cache some in-memory lists for quick reads (optional)
        # but we will read/write from DB for each operation to avoid stale overwrites
        # id counters are derived from DB auto-increment
        self.init_db()  # creates tables if they don't exist

    # -------- DB helpers --------
    def _get_conn(self):
        return self.pool.get_connection()

    def _ensure_database(self):
        # Ensure database exists (connect without database)
        cfg = dict(self.db_config)
        db = cfg.pop("database", None)
        try:
            cnx = mysql.connector.connect(**cfg)
            cursor = cnx.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cnx.commit()
            cursor.close()
            cnx.close()
        except Exception:
            # If cannot create DB, assume it exists or user will create manually
            pass

    # -------- Schema / Initialization --------
    def init_db(self):
        """Create tables if they don't exist. Uses transactions to be safe."""
        create_table_sql = [
            # users
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(255) DEFAULT '',
                gender VARCHAR(50) DEFAULT '',
                bday VARCHAR(50) DEFAULT '',
                contact_num VARCHAR(100) DEFAULT '',
                profile_pic TEXT,
                status VARCHAR(50) DEFAULT 'offline',
                last_active VARCHAR(100) DEFAULT '',
                remark TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            # chats
            """
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INT PRIMARY KEY AUTO_INCREMENT,
                sender INT NOT NULL,
                receiver INT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (receiver) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            # friend_requests
            """
            CREATE TABLE IF NOT EXISTS friend_requests (
                req_id INT PRIMARY KEY AUTO_INCREMENT,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                req_date VARCHAR(50),
                UNIQUE KEY uq_req (sender_id, receiver_id),
                FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            # friends (mutual)
            """
            CREATE TABLE IF NOT EXISTS friends (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                friend_id INT NOT NULL,
                since_date VARCHAR(50),
                UNIQUE KEY uq_friend (user_id, friend_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (friend_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            # posts
            """
            CREATE TABLE IF NOT EXISTS posts (
                post_id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                image_path TEXT,
                dt VARCHAR(50),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            # moods
            """
            CREATE TABLE IF NOT EXISTS moods (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                mood_date VARCHAR(50) NOT NULL,
                mood_value VARCHAR(100),
                UNIQUE KEY uq_mood (user_id, mood_date),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        ]

        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            for sql in create_table_sql:
                cursor.execute(sql)
            conn.commit()
        finally:
            cursor.close()
            conn.close()


    # -------- User methods (match previous interface) --------
    def add_user(self, username: str, password: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Return (user_id, message) on success, (None, error) on validation error.
        """
        # Validate using your User static validators (they internally used Manager with JSON; we skip that)
        # But to keep behavior consistent, call the same validations if present:
        
        # err1 = UserManager.validate_username(username)
        # if err1:
        #     return None, err1
        # err2 = UserManager.validate_password(password)
        # if err2:
        #     return None, err2

        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            insert = "INSERT INTO users (username, password, status, last_active) VALUES (%s, %s, %s, %s)"
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute(insert, (username, password, "online", now))
            conn.commit()
            user_id = cursor.lastrowid
            return user_id, "[System] Successfully created user"
        except mysql.connector.IntegrityError as e:
            # duplicate username
            return None, ["Username exists"]
        finally:
            cursor.close()
            conn.close()

    def update_profile(self, user_id: int, new_password: str, new_name: str, new_bday: str, new_gender: str, new_contact_num: str, upload_file=None) -> str:
        """
        Update user's profile; returns "Profile updated successfully" or error string.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            # handle profile pic saving if provided (same behavior as JSON manager)
            if upload_file:
                profile_dir = "profile_pics"
                os.makedirs(profile_dir, exist_ok=True)
                file_ext = os.path.splitext(upload_file.name)[1] or ".png"
                save_path = os.path.join(profile_dir, f"{user_id}{file_ext}")
                counter = 1
                while os.path.exists(save_path):
                    save_path = os.path.join(profile_dir, f"{user_id}_{counter}{file_ext}")
                    counter += 1
                Image.open(upload_file).save(save_path)
                profile_pic = save_path
                cursor.execute("UPDATE users SET profile_pic=%s WHERE user_id=%s", (profile_pic, user_id))

            cursor.execute("""
                UPDATE users SET password=%s, name=%s, bday=%s, gender=%s, contact_num=%s WHERE user_id=%s
            """, (new_password, new_name, new_bday, new_gender, new_contact_num, user_id))
            conn.commit()
            return "Profile updated successfully"
        finally:
            cursor.close()
            conn.close()

    # -------- Chat methods --------
    def add_chat(self, sender: int, receiver: int, content: str) -> str:
        if not content:
            return "Please type something"
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            insert = "INSERT INTO chats (sender, receiver, content) VALUES (%s, %s, %s)"
            cursor.execute(insert, (sender, receiver, content))
            conn.commit()
            chat_id = cursor.lastrowid
            # maintain chat_ids in users? Previously you appended chat_ids to User.__dict__
            # To keep compatibility, we won't store chat_ids column; instead, frontend can query chats table.
            return "sent"
        finally:
            cursor.close()
            conn.close()

    def get_chat_history(self, user_id: int, friend_id: int) -> List[Chat]:
        conn = self._get_conn()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT chat_id, sender, receiver, content
                FROM chats
                WHERE (sender=%s AND receiver=%s) OR (sender=%s AND receiver=%s)
                ORDER BY chat_id ASC
            """
            cursor.execute(sql, (user_id, friend_id, friend_id, user_id))
            rows = cursor.fetchall()
            # Convert to Chat objects
            chats = [Chat(r["chat_id"], r["sender"], r["receiver"], r["content"]) for r in rows]
            return chats
        finally:
            cursor.close()
            conn.close()

    # -------- Friend methods --------
    def add_friend(self, current_user: User, friend_uname: str) -> bool:
        # find friend
        conn = self._get_conn()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT user_id FROM users WHERE username=%s", (friend_uname,))
            row = cursor.fetchone()
            if not row:
                return False
            friend_id = row["user_id"]
            current_dt = datetime.datetime.now().strftime("%d/%m/%Y")
            # insert into friend_requests if not exists
            try:
                cursor.execute("INSERT INTO friend_requests (sender_id, receiver_id, req_date) VALUES (%s,%s,%s)",
                               (current_user.user_id, friend_id, current_dt))
                conn.commit()
            except mysql.connector.IntegrityError:
                # already exists
                pass
            return True
        finally:
            cursor.close()
            conn.close()

    def accept_request(self, current_user: User, sender: User):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            current_dt = datetime.datetime.now().strftime("%d/%m/%Y")
            # create friendship both sides, using INSERT IGNORE-style logic via try/except
            try:
                cursor.execute("INSERT INTO friends (user_id, friend_id, since_date) VALUES (%s,%s,%s)",
                               (current_user.user_id, sender.user_id, current_dt))
            except mysql.connector.IntegrityError:
                pass
            try:
                cursor.execute("INSERT INTO friends (user_id, friend_id, since_date) VALUES (%s,%s,%s)",
                               (sender.user_id, current_user.user_id, current_dt))
            except mysql.connector.IntegrityError:
                pass
            # remove friend_request
            cursor.execute("DELETE FROM friend_requests WHERE sender_id=%s AND receiver_id=%s", (sender.user_id, current_user.user_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def unfriend(self, current_user: User, target_user_id: int) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM friends WHERE (user_id=%s AND friend_id=%s) OR (user_id=%s AND friend_id=%s)",
                           (current_user.user_id, target_user_id, target_user_id, current_user.user_id))
            # delete chats
            cursor.execute("DELETE FROM chats WHERE (sender=%s AND receiver=%s) OR (sender=%s AND receiver=%s)",
                           (current_user.user_id, target_user_id, target_user_id, current_user.user_id))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    # -------- Post methods --------
    def add_post(self, user_id: int, post_file) -> bool:
        post_dir = "user_posts"
        os.makedirs(post_dir, exist_ok=True)
        # Use same filename logic as JSON manager
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            next_dt = datetime.datetime.now().strftime("%d/%m/%Y")
            # save file
            # compute next post id using auto-increment; we'll insert file then update path
            file_ext = os.path.splitext(post_file.name)[1] or ".png"
            # Insert row first to get post_id
            cursor.execute("INSERT INTO posts (user_id, image_path, dt) VALUES (%s, %s, %s)", (user_id, "", next_dt))
            post_id = cursor.lastrowid
            save_path = os.path.join(post_dir, f"{user_id}_post{post_id}{file_ext}")
            counter = 1
            while os.path.exists(save_path):
                save_path = os.path.join(post_dir, f"{user_id}_{counter}{file_ext}")
                counter += 1
            Image.open(post_file).save(save_path)
            # update record with actual path
            cursor.execute("UPDATE posts SET image_path=%s WHERE post_id=%s", (save_path, post_id))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    def get_post(self, user_id: int) -> List[str]:
        conn = self._get_conn()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT image_path FROM posts WHERE user_id=%s ORDER BY post_id DESC", (user_id,))
            rows = cursor.fetchall()
            return [r["image_path"] for r in rows]
        finally:
            cursor.close()
            conn.close()

    # -------- Mood methods --------
    def get_user_moods(self, user_id: int) -> Mood:
        # Build Mood object with list of {date,mood}
        conn = self._get_conn()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT mood_date, mood_value FROM moods WHERE user_id=%s ORDER BY mood_date ASC", (user_id,))
            rows = cursor.fetchall()
            moods = [{"date": r["mood_date"], "mood": r["mood_value"]} for r in rows]
            if not moods:
                # create an empty mood entry for user (equivalent to previous behavior)
                # no DB insertion required until set_daily_mood is called
                return Mood(user_id, [])
            return Mood(user_id, moods)
        finally:
            cursor.close()
            conn.close()

    def set_daily_mood(self, user_id: int, mood_value: str) -> bool:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            # insert or update
            cursor.execute("""
                INSERT INTO moods (user_id, mood_date, mood_value) VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE mood_value=VALUES(mood_value)
            """, (user_id, today, mood_value))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()

    def get_last_n_days_moods(self, user_id: int, n: int):
        # Return list of {date,mood} similar to previous Manager
        # We'll query last n days from today and match DB rows
        today = datetime.date.today()
        dates_needed = [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n)]
        conn = self._get_conn()
        cursor = conn.cursor(dictionary=True)
        try:
            # fetch moods for these dates
            cursor.execute("""
                SELECT mood_date, mood_value FROM moods
                WHERE user_id=%s AND mood_date IN (%s)
            """ % ("%s", ", ".join(["%s"] * len(dates_needed))), tuple([user_id] + dates_needed))
            rows = cursor.fetchall()
            mood_map = {r["mood_date"]: r["mood_value"] for r in rows}
            result = [{"date": d, "mood": mood_map.get(d, None)} for d in sorted(dates_needed, reverse=True)]
            return result
        finally:
            cursor.close()
            conn.close()

    def get_monthly_moods_df(self, user_id: int):
        moods_obj = self.get_user_moods(user_id)
        if hasattr(moods_obj, "__dict__"):
            moods = moods_obj.__dict__.get("moods", [])
        elif isinstance(moods_obj, dict):
            moods = moods_obj.get("moods", [])
        elif isinstance(moods_obj, list):
            moods = moods_obj
        else:
            moods = []

        today = datetime.date.today()
        year = today.year
        month = today.month

        mood_emojis1 = {
            "happy": "😊",
            "sad": "😢",
            "angry": "😡",
            "neutral": "😐",
            "excited": "🤩",
            "tired": "😴"
        }

        num_days = cal.monthrange(year, month)[1]
        all_dates = [datetime.date(year, month, d) for d in range(1, num_days + 1)]
        df = pd.DataFrame({"date": all_dates})

        mood_df = pd.DataFrame(moods) if moods else pd.DataFrame(columns=["date", "mood"])
        if not mood_df.empty and "date" in mood_df:
            mood_df["date"] = pd.to_datetime(mood_df["date"]).dt.date

        df = df.merge(mood_df, on="date", how="left").fillna({"mood": "unknown"})
        df["mood"] = df["mood"].map(mood_emojis1).fillna("❓")
        return df

    # -------- Remark --------
    def add_remark(self, user_id: int, remark: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET remark=%s WHERE user_id=%s", (remark, user_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    # -------- Utility: migrate existing JSON files into MySQL (optional) --------
    def migrate_from_json(self, data_dir: str = "data"):
        """
        Read JSON files from old structure and insert into DB.
        Use with caution — run once.
        """
        # users
        users_path = os.path.join(data_dir, "user.json")
        if os.path.exists(users_path):
            with open(users_path, "r", encoding="utf-8") as f:
                ud = json.load(f)
            for u in ud.get("users", []):
                try:
                    self.add_user(u["username"], u["password"])
                    # update other fields
                    # find user_id
                    conn = self._get_conn()
                    cur = conn.cursor(dictionary=True)
                    cur.execute("SELECT user_id FROM users WHERE username=%s", (u["username"],))
                    r = cur.fetchone()
                    if r:
                        uid = r["user_id"]
                        cur.execute("""UPDATE users SET name=%s, gender=%s, bday=%s, contact_num=%s, profile_pic=%s, status=%s, last_active=%s, remark=%s WHERE user_id=%s""",
                                    (u.get("name",""), u.get("gender",""), u.get("bday",""), u.get("contact_num",""), u.get("profile_pic",""), u.get("status",""), u.get("last_active",""), u.get("remark",""), uid))
                        conn.commit()
                    cur.close()
                    conn.close()
                except Exception:
                    pass

        # chats
        chats_path = os.path.join(data_dir, "chat.json")
        if os.path.exists(chats_path):
            with open(chats_path, "r", encoding="utf-8") as f:
                cd = json.load(f)
            for c in cd.get("chats", []):
                try:
                    self.add_chat(c["sender"], c["receiver"], c["content"])
                except Exception:
                    pass

        # posts
        posts_path = os.path.join(data_dir, "post.json")
        if os.path.exists(posts_path):
            with open(posts_path, "r", encoding="utf-8") as f:
                pdx = json.load(f)
            for p in pdx.get("posts", []):
                # p may contain post_path; we only migrate metadata, not copying files
                try:
                    conn = self._get_conn()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO posts (user_id, image_path, dt) VALUES (%s, %s, %s)",
                                (p.get("user_id"), p.get("post_path"), p.get("datetime")))
                    conn.commit()
                    cur.close()
                    conn.close()
                except Exception:
                    pass

        # moods
        moods_path = os.path.join(data_dir, "mood.json")
        if os.path.exists(moods_path):
            with open(moods_path, "r", encoding="utf-8") as f:
                md = json.load(f)
            for m in md.get("moods", []):
                uid = m.get("user_id")
                for entry in m.get("moods", []):
                    try:
                        self.set_daily_mood(uid, entry.get("mood"))
                    except Exception:
                        pass

        return True
