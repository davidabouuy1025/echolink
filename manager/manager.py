import os
import json
import datetime
from PIL import Image
from app.user import User
from app.chat import Chat
from app.post import Post

class Manager():
    def __init__(self, user_path = "data/user.json", chat_path="data/chat.json", post_path="data/post.json"):
        self.users = []
        self.chats = []
        self.posts = []
        self.users_path = user_path
        self.chat_path = chat_path
        self.post_path = post_path
        self.next_user_id = 1
        self.next_chat_id = 1 
        self.next_post_id = 1
        self.load_data()

    def load_data(self):
        try:
            with open(self.users_path, 'r') as f:
                user_data = json.load(f)
        except:
            user_data = {}
        
        self.users = [
            User(u["user_id"], u["username"], u["password"], u["name"], u["gender"], u["bday"], u["contact_num"], u["profile_pic"], u["status"], u["last_active"], u["chat_ids"], u["friends"], u["friend_request"]) 
            for u in user_data.get("users", [])
        ]

        try:
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
            with open(self.post_path, 'r') as f:
                post_data = json.load(f)
        except:
            post_data = {}

        self.posts = [
            Post(p["post_id"], p["user_id"], p["post_path"], p["datetime"])
            for p in post_data.get("chat", [])
        ]

        self.next_post_id = post_data.get("next_path_id", 1)

    def save_data(self):
        # Save user data
        os.makedirs(os.path.dirname(self.users_path), exist_ok=True)

        user_data_to_save = {
            "users": [u.__dict__ for u in self.users],
            "next_user_id": self.next_user_id
        }

        try:
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
            with open(self.post_path, "w") as f:
                json.dump(post_data_to_save, f, indent=4)
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
    
    def add_friend(self, user_id, friend_uname):
        new_req = []
        current_dt = datetime.datetime.now().strftime("%d/%m/%Y")
        friend = next((f for f in self.users if f.username == friend_uname), None)
        new_req.append(current_dt)
        new_req.append(user_id)
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
    
    def new_function():
        pass


