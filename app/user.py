class User:
    def __init__(self, user_id, username, password, name, gender, bday, contact_num, profile_pic, status, last_active, remark, chat_ids, friends, friend_request):
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
    
    def create_user_object(user_id, username, password, current_dt, chat_ids, friends, friend_request):
        return User(user_id, username, password, "", "", "", "", "", "online", current_dt, "", chat_ids, friends, friend_request)
    
    def username_validation(username):
        from manager.manager import Manager
        manager = Manager()

        error  = []
        all_username = [u.username for u in manager.users]

        if username in all_username:
            error.append("Username exists")

        if error:
            return error
        
    def password_validation(password):
        from manager.manager import Manager
        manager = Manager()

        error  = []

        if len(password) < 8:
            error.append("Password is too short.")
        elif not any(char.upper() for char in password):
            error.append("Password should contain at least one uppercase.")
        elif not any(char.isnumeric() for char in password):
            error.append("Password should contain at least one number.")

        if error:
            return error
        
    def login_user(manager, username, password):
        all_users = {u.username:u.password for u in manager.users}
        
        if username not in all_users.keys():
            return False, "Username not found"
        else:
            check_user = all_users[username]
            if password != check_user:
                return False, "Username and password don't match"
            else:
                return True, "Successfully logged in"
        
    def check_id(manager, username):
        user = next((u for u in manager.user if u.username == username))
        return user.user_id

    def check_username(manager, username):
        all_username = [u.username for u in manager.users]
        return username in all_username
    
    @staticmethod
    def check_req(manager, sender_id, friend_uname):
        # Find the receiver (friend) user object
        receiver = next((u for u in manager.users if u.username == friend_uname), None)
        sender = next((u for u in manager.users if u.user_id == sender_id), None)

        # Check if user exists
        if not receiver or not sender:
            return "not_found"

        # Rule 1: Cannot add yourself
        if receiver.user_id == sender.user_id:
            return "self_request"

        # Rule 2: Already friends
        if receiver.user_id in sender.friends:
            return "already_friends"

        # Rule 3: Check if a request already exists (pending)
        for req in receiver.friend_request:
            if req[1] == sender_id:
                return "already_sent"

        return "ok"  # All clear

    @staticmethod
    def id_to_object(manager, req_list):
        result = []
        for timestamp, sender_id in req_list:
            sender_user = next((u for u in manager.users if u.user_id == sender_id), None)
            if sender_user:
                result.append([sender_user, timestamp])
        return result
    
    @staticmethod
    def id_to_object_friends(manager, req_list):
        result = []
        for item in req_list:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                date, user_id = item
            else:
                user_id = item
                date = None

            user_obj = next((u for u in manager.users if u.user_id == user_id), None)
            if user_obj:
                result.append([user_obj, date])
        return result

    @staticmethod
    def check_update(new_password, new_name, new_contact_num):
        errors = []

        if not new_password or len(new_password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if not new_name:
            errors.append("Name cannot be empty.")
        if not new_contact_num:
            errors.append("Contact number cannot be empty.")

        if errors:
            return False, errors
        return True, "ok"
    