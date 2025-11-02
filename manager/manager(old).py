import os
import json 
import calendar as cal
import datetime
import pandas as pd
from PIL import Image
from filelock import FileLock
from app.user import User
from app.chat import Chat
from app.post import Post
from app.mood import Mood

class Manager():
    def __init__(self, user_path = "data/user.json", chat_path="data/chat.json", post_path="data/post.json", mood_path="data/mood.json"):
        self.users = []
        self.chats = []
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

    def load_data(self):
        try:
            with FileLock(self.users_path + ".lock"):
                with open(self.users_path, "r") as f:
                    user_data = json.load(f)
        except:
            user_data = {}
        
        self.users = [
            User(
                u["user_id"], 
                u["username"], 
                u["password"], 
                u["name"], 
                u["gender"], 
                u["bday"], 
                u["contact_num"], 
                u["profile_pic"], 
                u["status"], 
                u["last_active"], 
                u["remark"], 
                u["chat_ids"], 
                u["friends"], 
                u["friend_request"]
                ) 
            for u in user_data.get("users", [])
        ]

        try:
            with FileLock(self.chat_path + ".lock"):
                with open(self.chat_path, 'r') as f:
                    chat_data = json.load(f)
        except:
            chat_data = {}

        self.chat = [
            Chat(c["chat_id"], c["sender"], c["receiver"], c["content"]) 
            for c in chat_data.get("chats", [])
        ]

        self.next_user_id = user_data.get("next_user_id", 1)
        self.next_chat_id = chat_data.get("next_chat_id", 1)

        try:
            with FileLock(self.post_path, ".lock"):
                with open(self.post_path, 'r') as f:
                    post_data = json.load(f)
        except:
            post_data = {}

        self.posts = [
            Post(p["post_id"], p["user_id"], p["post_path"], p["datetime"])
            for p in post_data.get("chat", [])
        ]

        self.next_post_id = post_data.get("next_path_id", 1)

        try:
            with FileLock(self.mood_path, ".lock"):
                with open(self.mood_path, 'r') as f:
                    mood_data = json.load(f)
        except:
            mood_data = {}

        self.moods = [
            Mood(m["user_id"], m["moods"])
            for m in mood_data.get("moods", [])
        ]

    def save_data(self):
        # Save user data
        os.makedirs(os.path.dirname(self.users_path), exist_ok=True)

        user_data_to_save = {
            "users": [u.__dict__ for u in self.users],
            "next_user_id": self.next_user_id
        }

        try:
            with FileLock(self.users_path + ".lock"):
                with open(self.users_path, "w") as f:
                    json.dump(user_data_to_save, f, indent=4)
        except OSError as e:
            print("[System] Error saving user data")
            raise

        # Save chat data
        os.makedirs(os.path.dirname(self.chat_path), exist_ok=True)

        chat_data_to_save = {
            "chats": [c.__dict__ for c in self.chat],
            "next_chat_id": self.next_chat_id
        }

        try:
            with FileLock(self.chat_path + ".lock"):
                with open(self.chat_path, "w") as f:
                    json.dump(chat_data_to_save, f, indent=4)
        except OSError:
            print("[System] Error saving chat data")
            raise

        # Save post data
        os.makedirs(os.path.dirname(self.post_path), exist_ok=True)

        post_data_to_save = {
            "posts": [p.__dict__ for p in self.posts],
            "next_post_id": self.next_post_id
        }

        try:
            with FileLock(self.post_path + ".lock"):
                with open(self.post_path, "w") as f:
                    json.dump(post_data_to_save, f, indent=4)
        except OSError:
            print("[System] Error saving post data")
            raise

        # Save mood data
        os.makedirs(os.path.dirname(self.mood_path), exist_ok=True)

        mood_data_to_save = {
            "moods": [m.__dict__ for m in self.moods],
        }

        try:
            with FileLock(self.mood_path + ".lock"):
                with open(self.mood_path, "w") as f:
                    json.dump(mood_data_to_save, f, indent=4)
        except OSError:
            print("[System] Error saving post data")
            raise

    def save(self):
        self.save_data()

    def add_user(self, username, password):
        user_id = self.next_user_id
        result1 = User.username_validation(username)
        if result1:
            return None, result1
        result2 = User.password_validation(password)
        if result2:
            return None, result2
        current_dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.users.append(User.create_user_object(user_id, username, password, current_dt, [], [], []))
        self.next_user_id += 1
        self.save_data()
        return user_id, "[System] Successfully created user"
    
    def update_profile(self, user_id, new_password, new_name, new_bday, new_gender, new_contact_num, upload_file):
        """Update user profile and optionally save uploaded profile picture."""
        user = next((u for u in self.users if u.user_id == user_id), None)

        if not user:
            return "User not found"

        # Ensure folder exists
        profile_dir = "profile_pics"
        os.makedirs(profile_dir, exist_ok=True)

        # Handle profile picture upload
        if upload_file:
            img = Image.open(upload_file)
            file_ext = os.path.splitext(upload_file.name)[1] or ".png"
            save_path = os.path.join(profile_dir, f"{user_id}{file_ext}")

            counter = 1
            while os.path.exists(save_path):
                save_path = os.path.join(profile_dir, f"{user_id}_{counter}{file_ext}")
                counter += 1

            img.save(save_path)
            user.profile_pic = save_path  # Update user's profile picture path

        # Update other user fields
        user.password = new_password
        user.name = new_name
        user.bday = new_bday
        user.gender = new_gender
        user.contact_num = new_contact_num

        # Save all user data
        self.save_data()
        return "Profile updated successfully"

    def add_chat(self, sender, receiver, content):
        if not content:
            return "Please type something"
        chat_id = self.next_chat_id
        new_chat = Chat(chat_id, sender, receiver, content)
        self.chat.append(new_chat)

        # Add chat ID to both users
        sender_user = next((u for u in self.users if u.user_id == sender), None)
        receiver_user = next((u for u in self.users if u.user_id == receiver), None)

        if sender_user and receiver_user:
            sender_user.chat_ids.append(chat_id)
            receiver_user.chat_ids.append(chat_id)
            self.next_chat_id += 1
            self.save_data()
            return "sent"
        return "Unexpected error"
    
    def add_friend(self, current_user, friend_uname):
        new_req = []
        current_dt = datetime.datetime.now().strftime("%d/%m/%Y")
        friend = next((f for f in self.users if f.username == friend_uname), None)
        new_req.append(current_dt)
        new_req.append(current_user.user_id)
        friend.friend_request.append(new_req)
        self.save_data()
        return True
    
    def accept_request(self, current_user, sender):
        # Add each other as friends
        current_dt = datetime.datetime.now().strftime("%d/%m/%Y")
        current_user.friends.append([current_dt, sender.user_id])
        sender.friends.append([current_dt, current_user.user_id])
        # Remove request
        current_user.friend_request = [req for req in current_user.friend_request if req[1] != sender.user_id]
        # Save data
        self.save_data()

    def get_chat_history(self, user_id, friend_id):
        # Get all messages between user_id and friend_id
        self.load_data()
        return [c for c in self.chat if (c.sender == user_id and c.receiver == friend_id) or (c.sender == friend_id and c.receiver == user_id)]

    def unfriend(self, current_user, target_user_id):
        # Remove friend from both sides
        current_user.friends = [friend for friend in current_user.friends if str(friend[1]) != str(target_user_id)]

        target_user = next((u for u in self.users if u.user_id == target_user_id), None)
        print(target_user)
        if target_user:
            target_user.friends = [friend for friend in target_user.friends if friend[1] != current_user.user_id]

        # Delete all chat messages between both
        chats_to_delete = []
        for chat in self.chat:  # assuming self.chats is a list of chat objects or dicts
            if (
                (chat.sender == current_user.user_id and chat.receiver == target_user_id)
                or (chat.sender_id == target_user_id and chat.receiver_id == current_user.user_id)
            ):
                chats_to_delete.append(chat)

        for chat in chats_to_delete:
            self.chats.remove(chat)
            
        # Save changes
        self.save_data()
        return True
    
    def add_post(self, user_id, post_path):
        next_id = self.next_post_id
        current_dt = datetime.datetime.now().strftime("%d/%m/%Y")

        # Ensure folder exists
        post_dir = "user_posts"
        os.makedirs(post_dir, exist_ok=True)

        # Handle post photo
        img = Image.open(post_path)
        file_ext = os.path.splitext(post_path.name)[1] or ".png"
        save_path = os.path.join(post_dir, f"{user_id}_post{next_id}{file_ext}")
        counter = 1

        while os.path.exists(save_path):
            save_path = os.path.join(post_dir, f"{user_id}_{counter}{file_ext}")
            counter += 1

        img.save(save_path)

        new_post = Post(next_id, user_id, save_path, current_dt)
        self.posts.append(new_post)
        self.next_post_id += 1
        self.save_data()
        return True
    
    def get_post(self, user_id):
        return [path.image_path for path in self.posts if path.user_id == user_id]
    
    def get_user_moods(self, user_id):
        mood_obj = next((m for m in self.moods if str(m.user_id) == str(user_id)), None)
        if mood_obj is None:
            mood_obj = Mood(user_id, [])
            self.moods.append(mood_obj)
            self.save_data()
        return mood_obj
    
    def set_daily_mood(self, user_id, mood):
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        mood_obj = next((m for m in self.moods if str(m.user_id) == str(user_id)), None)
        if mood_obj is None:
            mood_obj = Mood(user_id, [])
            self.moods.append(mood_obj)

        today_entry = next((m for m in mood_obj.moods if m['date'] == today), None)
        if today_entry:
            today_entry['mood'] = mood
        else:
            mood_obj.moods.append({
                "date": today,
                "mood": mood
            })

        self.save_data()
        return True

    def get_last_n_days_moods(self, user_id, n):
        # Get user mood object
        moods = self.get_user_moods(user_id)
        all_moods = moods.__dict__.get("moods", [])

        # Sort
        moods_sorted = sorted(
            all_moods,
            key=lambda x: datetime.datetime.strptime(x["date"], "%Y-%m-%d"),
            reverse=True
        )

        # Take last 5
        latest_n = moods_sorted[:n]

        today = datetime.datetime.now().date()
        dates_needed = [
            (today - datetime.timedelta(days=i)).
            strftime("%Y-%m-%d") 
            for i in range(n)
        ]

        mood_dict = {m["date"]: m["mood"] for m in latest_n}

        result = []
        for date in sorted(dates_needed, reverse=True):
            result.append({
                "date": date,
                "mood": mood_dict.get(date, None)
            })

        return result

    def get_monthly_moods_df(self, user_id):
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

        # ✅ Use the actual `calendar` module
        num_days = cal.monthrange(year, month)[1]
        all_dates = [datetime.date(year, month, d) for d in range(1, num_days + 1)]
        df = pd.DataFrame({"date": all_dates})

        mood_df = pd.DataFrame(moods) if moods else pd.DataFrame(columns=["date", "mood"])

        if not mood_df.empty and "date" in mood_df:
            mood_df["date"] = pd.to_datetime(mood_df["date"]).dt.date

        # Merge mood data into the monthly frame
        df = df.merge(mood_df, on="date", how="left").fillna({"mood": "unknown"})

        # ✅ Convert mood strings to emojis
        df["mood"] = df["mood"].map(mood_emojis1).fillna("❓")

        return df
        
    def add_remark(self, user_id, remark):
        current_user = next((u for u in self.users if str(u.user_id) == str(user_id)))
        # print(current_user)
        # print(current_user.username)
        # print(remark)
        current_user.remark = remark
        # print(current_user.remark)
        self.save_data()


