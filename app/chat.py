class Chat:
    def __init__(self, chat_id, sender, receiver, content):
        self.chat_id = chat_id
        self.sender = sender
        self.receiver = receiver
        self.content = content

    @staticmethod
    def create_chat_object(chat_id, sender, receiver, content):
        return Chat(chat_id, sender, receiver, content)