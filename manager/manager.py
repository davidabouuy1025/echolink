import os
import json
import calendar as cal
import datetime
import time
import tempfile
import pandas as pd
from PIL import Image
from filelock import FileLock, Timeout
from app.user import User
from app.chat import Chat
from app.post import Post
from app.mood import Mood

LOCK_TIMEOUT = 5  # seconds to wait for a lock before raising Timeout (adjust as needed)


class Manager:
    def __init__(
        self,
        user_path="data/user.json",
        chat_path="data/chat.json",
        post_path="data/post.json",
        mood_path="data/mood.json",
    ):
        # canonical lists
        self.users = []
        self.chats = []
        self.posts = []
        self.moods = []

        # paths
        self.users_path = user_path
        self.chat_path = chat_path
        self.post_path = post_path
        self.mood_path = mood_path

        # next ids (will be recalculated on load)
        self.next_user_id = 1
        self.next_chat_id = 1
        self.next_post_id = 1

        # ensure data folder exists
        os.makedirs(os.path.dirname(self.users_path) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(self.chat_path) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(self.post_path) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(self.mood_path) or ".", exist_ok=True)

        # load data to initialize state
        self.load_data()

    # -------------------------
    # Helper: safe JSON read
    # -------------------------
    def _safe_read_json(self, path, default=None):
        """
        Acquire a lock on `path + ".lock"`, read JSON, retry on JSON errors,
        and return parsed dict or `default` if file missing.
        """
        lock_path = path + ".lock"
        default = {} if default is None else default

        if not os.path.exists(path):
            return default

        try:
            with FileLock(lock_path, timeout=LOCK_TIMEOUT):
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        return json.load(f)
                    except json.JSONDecodeError:
                        # The file may be being written by another process; try again a few times
                        # rather than immediately returning an empty dict and risking overwrite.
                        for _ in range(3):
                            time.sleep(0.1)
                            f.seek(0)
                            try:
                                return json.load(f)
                            except json.JSONDecodeError:
                                continue
                        # If still corrupt, raise so caller may decide to skip or recover
                        raise
        except Timeout:
            # Couldn't acquire lock — treat as no change (caller can decide)
            raise

    # -------------------------
    # Helper: safe JSON write (atomic)
    # -------------------------
    def _safe_write_json(self, path, data):
        """
        Write JSON atomically by writing to a temp file then os.replace while holding a lock.
        """
        lock_path = path + ".lock"
        tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".tmp_")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmpf:
                json.dump(data, tmpf, indent=4, ensure_ascii=False)
                tmpf.flush()
                os.fsync(tmpf.fileno())

            # Acquire lock and swap file
            with FileLock(lock_path, timeout=LOCK_TIMEOUT):
                os.replace(tmp_path, path)
        except Timeout:
            # remove tmp and surface the timeout to the caller
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            raise
        except Exception:
            # cleanup and re-raise
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            raise

    # -------------------------
    # Object ↔ dict converters
    # (keeps JSON simple and stable)
    # -------------------------
    def _user_to_dict(self, u: User):
        # Serialize only primitive fields expected by load_data()
        return {
            "user_id": u.user_id,
            "username": u.username,
            "password": u.password,
            "name": u.name,
            "gender": u.gender,
            "bday": u.bday,
            "contact_num": u.contact_num,
            "profile_pic": u.profile_pic,
            "status": u.status,
            "last_active": u.last_active,
            "remark": u.remark,
            "chat_ids": u.chat_ids,
            "friends": u.friends,
            "friend_request": u.friend_request,
        }

    def _dict_to_user(self, d: dict):
        # Must match the User constructor used in your app
        return User(
            d.get("user_id"),
            d.get("username"),
            d.get("password"),
            d.get("name"),
            d.get("gender"),
            d.get("bday"),
            d.get("contact_num"),
            d.get("profile_pic"),
            d.get("status"),
            d.get("last_active"),
            d.get("remark"),
            d.get("chat_ids", []),
            d.get("friends", []),
            d.get("friend_request", []),
        )

    def _chat_to_dict(self, c: Chat):
        return {"chat_id": c.chat_id, "sender": c.sender, "receiver": c.receiver, "content": c.content}

    def _dict_to_chat(self, d: dict):
        return Chat(d.get("chat_id"), d.get("sender"), d.get("receiver"), d.get("content"))

    def _post_to_dict(self, p: Post):
        return {"post_id": p.post_id, "user_id": p.user_id, "post_path": p.post_path, "datetime": p.datetime}

    def _dict_to_post(self, d: dict):
        return Post(d.get("post_id"), d.get("user_id"), d.get("post_path"), d.get("datetime"))

    def _mood_to_dict(self, m: Mood):
        # mood object contains user_id and list of moods
        return {"user_id": m.user_id, "moods": m.moods}

    def _dict_to_mood(self, d: dict):
        return Mood(d.get("user_id"), d.get("moods", []))

    # -------------------------
    # Load all data (safe)
    # -------------------------
    def load_data(self):
        # Load users
        try:
            user_data = self._safe_read_json(self.users_path, default={"users": [], "next_user_id": 1})
        except (Timeout, json.JSONDecodeError):
            # Lock timed out or file corrupt; keep in-memory state instead (do not overwrite disk)
            user_data = {"users": [], "next_user_id": 1}
        # Build user objects
        self.users = [self._dict_to_user(u) for u in user_data.get("users", [])]
        self.next_user_id = max(1, int(user_data.get("next_user_id", 1),) if isinstance(user_data.get("next_user_id", None), (int, str)) else 1)

        # Load chats
        try:
            chat_data = self._safe_read_json(self.chat_path, default={"chats": [], "next_chat_id": 1})
        except (Timeout, json.JSONDecodeError):
            chat_data = {"chats": [], "next_chat_id": 1}
        self.chats = [self._dict_to_chat(c) for c in chat_data.get("chats", [])]
        self.next_chat_id = max(1, int(chat_data.get("next_chat_id", 1),) if isinstance(chat_data.get("next_chat_id", None), (int, str)) else 1)

        # Load posts
        try:
            post_data = self._safe_read_json(self.post_path, default={"posts": [], "next_post_id": 1})
        except (Timeout, json.JSONDecodeError):
            post_data = {"posts": [], "next_post_id": 1}
        self.posts = [self._dict_to_post(p) for p in post_data.get("posts", [])]
        self.next_post_id = max(1, int(post_data.get("next_post_id", 1),) if isinstance(post_data.get("next_post_id", None), (int, str)) else 1)

        # Load moods
        try:
            mood_data = self._safe_read_json(self.mood_path, default={"moods": []})
        except (Timeout, json.JSONDecodeError):
            mood_data = {"moods": []}
        self.moods = [self._dict_to_mood(m) for m in mood_data.get("moods", [])]

    # -------------------------
    # Merge-on-save helpers
    # -------------------------
    def _merge_and_write(self, path, current_list, key_fn, to_dict_fn, next_id_key=None, current_next_id=1):
        """
        Generic merge + write:
        - read latest on-disk
        - create dict keyed by key_fn(d) for latest
        - overlay current_list (current in-memory changes take precedence)
        - write merged result and return updated next_id
        """
        # Read latest on-disk (fallback to defaults)
        try:
            latest = self._safe_read_json(path, default={})
        except (Timeout, json.JSONDecodeError):
            latest = {}

        latest_items = latest.get(next((k for k in ["users", "chats", "posts", "moods"] if k in latest), ""), [])
        if not isinstance(latest_items, list):
            latest_items = []

        latest_map = {key_fn(item): item for item in latest_items}

        # Overlay with current_list
        for obj in current_list:
            d = to_dict_fn(obj)
            latest_map[key_fn(d)] = d

        # Build out the payload
        # identify top-level container name
        container_key = None
        if path == self.users_path:
            container_key = "users"
        elif path == self.chat_path:
            container_key = "chats"
        elif path == self.post_path:
            container_key = "posts"
        elif path == self.mood_path:
            container_key = "moods"
        else:
            # fallback
            container_key = "items"

        out = {container_key: list(latest_map.values())}
        # handle next-id if given
        if next_id_key:
            # check latest file for next id
            latest_next = latest.get(next_id_key, None)
            if isinstance(latest_next, (int, str)):
                try:
                    latest_next = int(latest_next)
                except Exception:
                    latest_next = current_next_id
            else:
                latest_next = current_next_id

            # ensure next is at least as large as current_next_id
            merged_next = max(current_next_id, latest_next)
            out[next_id_key] = merged_next
        # write out
        self._safe_write_json(path, out)

        if next_id_key:
            return out[next_id_key]
        return None

    # -------------------------
    # Save data (merge + atomic)
    # -------------------------
    def save_data(self):
        # USERS
        self.next_user_id = self._merge_and_write(
            self.users_path,
            self.users,
            key_fn=lambda x: int(x["user_id"]) if isinstance(x, dict) and "user_id" in x else int(x.user_id),
            to_dict_fn=self._user_to_dict,
            next_id_key="next_user_id",
            current_next_id=self.next_user_id,
        ) or self.next_user_id

        # CHATS
        self.next_chat_id = self._merge_and_write(
            self.chat_path,
            self.chats,
            key_fn=lambda x: int(x["chat_id"]) if isinstance(x, dict) and "chat_id" in x else int(x.chat_id),
            to_dict_fn=self._chat_to_dict,
            next_id_key="next_chat_id",
            current_next_id=self.next_chat_id,
        ) or self.next_chat_id

        # POSTS
        self.next_post_id = self._merge_and_write(
            self.post_path,
            self.posts,
            key_fn=lambda x: int(x["post_id"]) if isinstance(x, dict) and "post_id" in x else int(x.post_id),
            to_dict_fn=self._post_to_dict,
            next_id_key="next_post_id",
            current_next_id=self.next_post_id,
        ) or self.next_post_id

        # MOODS (keyed by user_id, merge mood lists per user)
        # We'll implement moods merge separately because it's a nested list per user.
        try:
            try:
                latest = self._safe_read_json(self.mood_path, default={"moods": []})
            except (Timeout, json.JSONDecodeError):
                latest = {"moods": []}

            latest_map = {int(m["user_id"]): m for m in latest.get("moods", []) if "user_id" in m}

            # overlay current moods: merge mood lists by date (in-memory takes precedence for same date)
            for m_obj in self.moods:
                m_dict = self._mood_to_dict(m_obj)
                uid = int(m_dict["user_id"])
                existing = latest_map.get(uid, {"user_id": uid, "moods": []})
                # build map by date
                existing_map = {entry["date"]: entry for entry in existing.get("moods", [])}
                for entry in m_dict.get("moods", []):
                    existing_map[entry["date"]] = entry
                existing["moods"] = list(existing_map.values())
                latest_map[uid] = existing

            out_moods = {"moods": list(latest_map.values())}
            self._safe_write_json(self.mood_path, out_moods)
        except Timeout:
            # couldn't acquire lock for moods
            raise

    def save(self):
        return self.save_data()

    # -------------------------
    # Domain operations (use canonical lists)
    # -------------------------
    def add_user(self, username, password):
        user_id = self.next_user_id
        result1 = User.username_validation(username)
        if result1:
            return None, result1
        result2 = User.password_validation(password)
        if result2:
            return None, result2
        current_dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        new_user = User.create_user_object(user_id, username, password, current_dt, [], [], [])
        self.users.append(new_user)
        self.next_user_id += 1
        self.save_data()
        return user_id, "[System] Successfully created user"

    def update_profile(self, user_id, new_password, new_name, new_bday, new_gender, new_contact_num, upload_file):
        user = next((u for u in self.users if u.user_id == user_id), None)
        if not user:
            return "User not found"

        profile_dir = "profile_pics"
        os.makedirs(profile_dir, exist_ok=True)

        if upload_file:
            img = Image.open(upload_file)
            file_ext = os.path.splitext(upload_file.name)[1] or ".png"
            save_path = os.path.join(profile_dir, f"{user_id}{file_ext}")

            counter = 1
            while os.path.exists(save_path):
                save_path = os.path.join(profile_dir, f"{user_id}_{counter}{file_ext}")
                counter += 1

            img.save(save_path)
            user.profile_pic = save_path

        user.password = new_password
        user.name = new_name
        user.bday = new_bday
        user.gender = new_gender
        user.contact_num = new_contact_num

        self.save_data()
        return "Profile updated successfully"

    def add_chat(self, sender, receiver, content):
        if not content:
            return "Please type something"
        chat_id = self.next_chat_id
        new_chat = Chat(chat_id, sender, receiver, content)
        self.chats.append(new_chat)

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
        friend = next((f for f in self.users if f.username == friend_uname), None)
        if friend is None:
            return False
        current_dt = datetime.datetime.now().strftime("%d/%m/%Y")
        # store as [date, user_id]
        friend.friend_request.append([current_dt, current_user.user_id])
        self.save_data()
        return True

    def accept_request(self, current_user, sender):
        current_dt = datetime.datetime.now().strftime("%d/%m/%Y")
        current_user.friends.append([current_dt, sender.user_id])
        sender.friends.append([current_dt, current_user.user_id])
        current_user.friend_request = [req for req in current_user.friend_request if req[1] != sender.user_id]
        self.save_data()

    def get_chat_history(self, user_id, friend_id):
        # Load latest chat list to ensure we serve up-to-date messages
        try:
            # reload just chats on demand
            latest_chat_data = self._safe_read_json(self.chat_path, default={"chats": []})
            # rebuild in-memory chats to reflect latest disk state
            self.chats = [self._dict_to_chat(c) for c in latest_chat_data.get("chats", [])]
        except Exception:
            # if read failed, continue with in-memory cached chats
            pass

        return [
            c
            for c in self.chats
            if (c.sender == user_id and c.receiver == friend_id) or (c.sender == friend_id and c.receiver == user_id)
        ]

    def unfriend(self, current_user, target_user_id):
        current_user.friends = [friend for friend in current_user.friends if str(friend[1]) != str(target_user_id)]
        target_user = next((u for u in self.users if u.user_id == target_user_id), None)
        if target_user:
            target_user.friends = [friend for friend in target_user.friends if str(friend[1]) != str(current_user.user_id)]

        # Delete chats between both
        self.chats = [
            chat
            for chat in self.chats
            if not (
                (chat.sender == current_user.user_id and chat.receiver == target_user_id)
                or (chat.sender == target_user_id and chat.receiver == current_user.user_id)
            )
        ]

        self.save_data()
        return True

    def add_post(self, user_id, post_path):
        next_id = self.next_post_id
        current_dt = datetime.datetime.now().strftime("%d/%m/%Y")

        post_dir = "user_posts"
        os.makedirs(post_dir, exist_ok=True)

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
        return [p.post_path for p in self.posts if p.user_id == user_id]

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

        today_entry = next((m for m in mood_obj.moods if m["date"] == today), None)
        if today_entry:
            today_entry["mood"] = mood
        else:
            mood_obj.moods.append({"date": today, "mood": mood})

        self.save_data()
        return True

    def get_last_n_days_moods(self, user_id, n):
        moods = self.get_user_moods(user_id)
        all_moods = moods.__dict__.get("moods", [])

        moods_sorted = sorted(all_moods, key=lambda x: datetime.datetime.strptime(x["date"], "%Y-%m-%d"), reverse=True)
        latest_n = moods_sorted[:n]

        today = datetime.datetime.now().date()
        dates_needed = [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(n)]
        mood_dict = {m["date"]: m["mood"] for m in latest_n}

        result = []
        for date in sorted(dates_needed, reverse=True):
            result.append({"date": date, "mood": mood_dict.get(date, None)})
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
            "tired": "😴",
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

    def add_remark(self, user_id, remark):
        current_user = next((u for u in self.users if str(u.user_id) == str(user_id)), None)
        if not current_user:
            return
        current_user.remark = remark
        self.save_data()
