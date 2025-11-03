class Mood:
    def __init__(self, user_id, moods):
        self.user_id = user_id
        self.moods = moods or []

    def create_mood_object(user_id, mood):
        return Mood(user_id, mood)
    
    def mood_obj_to_dict(mood_obj):
        return [m for m in mood_obj.__dict__]