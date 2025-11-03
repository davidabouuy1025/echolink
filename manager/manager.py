# manager_sql.py
import os
import json
import datetime
import calendar as cal
import pandas as pd
from PIL import Image
from filelock import FileLock
import threading
from app.user import User
from app.chat import Chat
from app.post import Post
from app.mood import Mood

class Manager:
    def __init__(self, user_path="data/user.json", chat_path="data/chat.json",
                 post_path="data/post.json", mood_path="data/mood.json"):
        self.users = []
        self.chat = []
        self.posts = []
        self.moods = []

        self.users_path = user_path
        self.chat_path = chat_path
        self.post_path = post_path
        self.mood_path = mood_path

        self.next_user_id = 1
        self.next_chat_id = 1
        self.next_post_id = 1

        self.load_data()

    # ------------------- Load Data ------------------- #
    def load_data(self):
        self.users, self.next_user_id = self._load_json(self.users_path, "users", User, "next_user_id")
        self.chat, self.next_chat_id = self._load_json(self.chat_path, "chats", Chat, "next_chat_id")
        self.posts, self.next_post_id = self._load_json(self.post_path, "posts", Post, "next_post_id")
        self.moods, _ = self._load_json(self.mood_path, "moods", Mood)

    def _load_json(self, path, key, cls, next_id_key=None):
        data_list = []
        next_id = 1
        chat_thread_lock = threading.Lock()
        try:
            with chat_thread_lock:
                with FileLock(path + ".lock"):
                    with open(path, "r") as f:
                        data = json.load(f)
        except:
            data = {}

        if key in data:
            if cls == User:
                data_list = [
                    User(u["user_id"], u["username"], u["password"], u["name"], u["gender"], u["bday"],
                         u["contact_num"], u["profile_pic"], u["status"], u["last_active"], u["remark"],
                         u["chat_ids"], u["friends"], u["friend_request"])
                    for u in data[key]
                ]
            elif cls == Chat:
                data_list = [
                    Chat(c["chat_id"], c["sender"], c["receiver"], c["content"])
                    for c in data[key]
                ]
            elif cls == Post:
                data_list = [
                    Post(p["chat_id"], p["user_id"], p["image_path"], p["datetime"])
                    for p in data[key]
                ]
            elif cls == Mood:
                data_list = [
                    Mood(m["user_id"], m["moods"])
                    for m in data[key]
                ]

        if next_id_key:
            next_id = data.get(next_id_key, 1)

        return data_list, next_id

    # ------------------- Save Data ------------------- #
    def save_data(self):
        self._save_json(self.users_path, "users", self.users, "next_user_id", self.next_user_id)
        self._save_json(self.chat_path, "chats", self.chat, "next_chat_id", self.next_chat_id)
        self._save_json(self.post_path, "posts", self.posts, "next_post_id", self.next_post_id)
        self._save_json(self.mood_path, "moods", self.moods)

    def _save_json(self, path, key, obj_list, next_id_key=None, next_id_value=None):
        chat_thread_lock = threading.Lock()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        data_to_save = {key: [o.__dict__ for o in obj_list]}
        if next_id_key and next_id_value is not None:
            data_to_save[next_id_key] = next_id_value

        with chat_thread_lock:
            with FileLock(path + ".lock"):
                with open(path, "w") as f:
                    json.dump(data_to_save, f, indent=4)
                    print(f"Save {path}")

    def save(self):
        self.save_data()

    # ------------------- User Methods ------------------- #
    def add_user(self, username, password):
        user_id = self.next_user_id
        if User.username_validation(username):
            return None, User.username_validation(username)
        if User.password_validation(password):
            return None, User.password_validation(password)

        current_dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        new_user = User.create_user_object(user_id, username, password, current_dt, [], [], [])
        self.users.append(new_user)
        self.next_user_id += 1
        self.save_data()
        return user_id, "[System] Successfully created user"

    def update_profile(self, user_id, new_password, new_name, new_bday, new_gender, new_contact_num, upload_file=None):
        user = next((u for u in self.users if u.user_id == user_id), None)
        if not user:
            return "User not found"

        # Profile pic
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
            user.profile_pic = save_path

        user.password = new_password
        user.name = new_name
        user.bday = new_bday
        user.gender = new_gender
        user.contact_num = new_contact_num

        self.save_data()
        return "Profile updated successfully"

    # ------------------- Chat Methods ------------------- #
    def add_chat(self, sender, receiver, content):
        chat_thread_lock = threading.Lock()
        with chat_thread_lock:
            chat_id = self.next_chat_id
            new_chat = Chat(chat_id, sender, receiver, content)
            self.chat.append(new_chat)
            self.next_chat_id += 1
            self.save_data()
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

    def get_chat_history(self, user_id, friend_id):
        chat_thread_lock = threading.Lock()
        
        with chat_thread_lock:
            self.load_data()
            return [c for c in self.chat if
                    (str(c.sender) == str(user_id) and str(c.receiver) == str(friend_id)) or
                    (str(c.sender) == str(friend_id) and str(c.receiver) == str(user_id))]
    
    # ------------------- Friend Methods ------------------- #
    def add_friend(self, current_user, friend_uname):
        friend = next((f for f in self.users if f.username == friend_uname), None)
        if not friend:
            return False
        current_dt = datetime.datetime.now().strftime("%d/%m/%Y")
        friend.friend_request.append([current_dt, current_user.user_id])
        self.save_data()
        return True
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

    # ------------------- Remark ------------------- #
    def add_remark(self, user_id, remark):
        user = next((u for u in self.users if u.user_id == user_id), None)
        if user:
            user.remark = remark
            self.save_data()

    def return_user(self, user_id):
        return next((u for u in self.users if u.user_id == user_id), None)
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
