import config
import json

from datetime import datetime
from config import WORK_HOUR_START, WORK_HOUR_END, WORK_DAYS

# Tải từ khóa mẫu từ file keywords.json
def load_keywords():
    with open("keywords.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # Chuyển từ list → dict với key là intent
    keywords = {}
    for item in data:
        for intent, content in item.items():
            keywords[intent] = content
    return keywords

# Lấy bản đồ intent từ file keywords (dùng sau này)
INTENT_LOOKUP = {}
KEYWORDS = load_keywords()


def is_office_hours():
   # now = datetime.now()
    #hour = now.hour
    #minute = now.minute
    #weekday = now.weekday()  # Thứ 2 = 0, Chủ nhật = 6


    # Nếu là thứ 7 hoặc Chủ nhật → không phải giờ hành chính
    #if weekday >= 5:
     # return False


    # Giờ hành chính: 8h–12h và 13h–17h
    #if 8 <= hour < 12:
   #   return True
    #if 13 <= hour < 17:
     # return True


    # Giờ nghỉ trưa hoặc ngoài giờ → không tính là giờ hành chính
    return False

def match_intent(message: str, keywords: dict = None):
    if keywords is None:
        keywords = KEYWORDS  # fallback nếu không truyền

    message_lower = message.lower()
    for intent, data in keywords.items():
        all_phrases = data.get("keywords", []) + data.get("examples", [])
        for phrase in all_phrases:
            if phrase.lower() in message_lower:
                return { "intent": intent, "response": data["response"] }
    return None


def get_thread_id_from_recipient_id(recipient_id: str) -> str | None:
    try:
        thread_id = config.MAPPINGS_data['mappings'].get(recipient_id)
        return thread_id
    except:
        return None
    
    
def update_thread_id_from_recipient_id(recipient_id: str,
                                       thread_id: str) -> None:
    try:
        config.MAPPINGS_data['mappings'].update({recipient_id: thread_id})
        return None
    except:
        None

def log_message(user_id: str, message: str) -> None:
    try:
        with open("chat_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {user_id}: {message}\n")
    except Exception as e:
        print(f"Lỗi khi ghi log: {e}")
