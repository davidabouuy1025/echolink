class Post:
    def __init__(self, chat_id, user_id, image_path, datetime):
        self.chat_id = chat_id
        self.user_id = user_id
        self.image_path = image_path or []
        self.datetime = datetime 

    def create_post_object(chat_id, user_id, image_path, datetime):
        return Post(chat_id, user_id, image_path, datetime)