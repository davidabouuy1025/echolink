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
            return "sent"


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

    def accept_request(self, current_user, sender):
        current_dt = datetime.datetime.now().strftime("%d/%m/%Y")
        current_user.friends.append([current_dt, sender.user_id])
        sender.friends.append([current_dt, current_user.user_id])
        current_user.friend_request = [req for req in current_user.friend_request if req[1] != sender.user_id]
        self.save_data()

    def unfriend(self, current_user, target_user_id):
        current_user.friends = [f for f in current_user.friends if f[1] != target_user_id]
        target_user = next((u for u in self.users if u.user_id == target_user_id), None)
        if target_user:
            target_user.friends = [f for f in target_user.friends if f[1] != current_user.user_id]

        chats_to_remove = [c for c in self.chat if (c.sender == current_user.user_id and c.receiver == target_user_id) or
                                                (c.sender == target_user_id and c.receiver == current_user.user_id)]
        for c in chats_to_remove:
            self.chat.remove(c)

        self.save_data()
        return True

    # ------------------- Post Methods ------------------- #
    def add_post(self, user_id, post_file):
        post_dir = "user_posts"
        os.makedirs(post_dir, exist_ok=True)

        next_id = self.next_post_id
        file_ext = os.path.splitext(post_file.name)[1] or ".png"
        save_path = os.path.join(post_dir, f"{user_id}_post{next_id}{file_ext}")
        counter = 1
        while os.path.exists(save_path):
            save_path = os.path.join(post_dir, f"{user_id}_{counter}{file_ext}")
            counter += 1
        Image.open(post_file).save(save_path)

        new_post = Post(next_id, user_id, save_path, datetime.datetime.now().strftime("%d/%m/%Y"))
        self.posts.append(new_post)
        self.next_post_id += 1
        self.save_data()
        return True

    def get_post(self, user_id):
        return [p.image_path for p in self.posts if p.user_id == user_id]

    # ------------------- Mood Methods ------------------- #
    def get_user_moods(self, user_id):
        mood_obj = next((m for m in self.moods if m.user_id == user_id), None)
        if not mood_obj:
            mood_obj = Mood(user_id, [])
            self.moods.append(mood_obj)
            self.save_data()
        return mood_obj

    def set_daily_mood(self, user_id, mood):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        mood_obj = self.get_user_moods(user_id)
        today_entry = next((m for m in mood_obj.moods if m["date"] == today), None)
        if today_entry:
            today_entry["mood"] = mood
        else:
            mood_obj.moods.append({"date": today, "mood": mood})
        self.save_data()
        return True

    def get_last_n_days_moods(self, user_id, n):
        moods = self.get_user_moods(user_id).moods
        moods_sorted = sorted(moods, key=lambda x: datetime.datetime.strptime(x["date"], "%Y-%m-%d"), reverse=True)
        latest_n = moods_sorted[:n]
        today = datetime.datetime.now().date()
        dates_needed = [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n)]
        mood_dict = {m["date"]: m["mood"] for m in latest_n}
        return [{"date": d, "mood": mood_dict.get(d)} for d in sorted(dates_needed, reverse=True)]

    def get_monthly_moods_df(self, user_id):
        moods_obj = self.get_user_moods(user_id)
        moods = moods_obj.moods if moods_obj else []
        today = datetime.date.today()
        num_days = cal.monthrange(today.year, today.month)[1]
        all_dates = [datetime.date(today.year, today.month, d) for d in range(1, num_days + 1)]
        df = pd.DataFrame({"date": all_dates})
        mood_df = pd.DataFrame(moods) if moods else pd.DataFrame(columns=["date", "mood"])
        if not mood_df.empty:
            mood_df["date"] = pd.to_datetime(mood_df["date"]).dt.date

        df = df.merge(mood_df, on="date", how="left").fillna({"mood": "unknown"})
        mood_emojis = {"happy": "😊", "sad": "😢", "angry": "😡", "neutral": "😐", "excited": "🤩", "tired": "😴"}
        df["mood"] = df["mood"].map(mood_emojis).fillna("❓")
        return df

    # ------------------- Remark ------------------- #
    def add_remark(self, user_id, remark):
        user = next((u for u in self.users if u.user_id == user_id), None)
        if user:
            user.remark = remark
            self.save_data()

    def return_user(self, user_id):
        return next((u for u in self.users if u.user_id == user_id), None)