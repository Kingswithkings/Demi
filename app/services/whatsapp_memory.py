# app/services/whatsapp_memory.py

class WhatsAppConversationMemory:
    def __init__(self):
        self.sessions = {}  # keyed by phone number

    def get(self, phone: str):
        if phone not in self.sessions:
            self.sessions[phone] = {
                "history": [],
                "meeting": {
                    "title": None,
                    "start_time": None,
                    "end_time": None,
                    "location": None,
                },
                # NEW: states
                "state": "idle",
                "location_attempt": 0,
                "suggested_location": None, # idle | prompted | collecting | awaiting_confirmation
            }
        return self.sessions[phone]

    def add_message(self, phone: str, message: str):
        self.get(phone)["history"].append(message)

    def update_meeting(self, phone: str, updates: dict):
        meeting = self.get(phone)["meeting"]
        for k, v in updates.items():
            if v is not None and k in meeting:
                meeting[k] = v

    def is_complete(self, phone: str):
        m = self.get(phone)["meeting"]
        return all([m["start_time"], m["end_time"], m["location"]])

    def set_state(self, phone: str, state: str):
        self.get(phone)["state"] = state

    def reset(self, phone: str):
        if phone in self.sessions:
            del self.sessions[phone]


whatsapp_memory = WhatsAppConversationMemory()

class WhatsAppMemory:
    def __init__(self):
        self.sessions = {}

    def get(self, user):
        return self.sessions.setdefault(user, {
            "history": [],
            "meeting": {},
            "state": "idle"
        })

    def add_message(self, user, text):
        self.get(user)["history"].append(text)

    def update_meeting(self, user, data):
        self.get(user)["meeting"].update(data)

    def set_state(self, user, state):
        self.get(user)["state"] = state

    def reset(self, user):
        self.sessions.pop(user, None)

whatsapp_memory = WhatsAppMemory()
