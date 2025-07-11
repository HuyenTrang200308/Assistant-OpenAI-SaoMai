# state.py
recent_users = {}
user_last_message_time = {}
greeted_users = set()
pending_users = {}
REPLY_COOLDOWN = 10
user_quick_reply_done = set()
user_intent_history = {}  # Dict[str, Set[str]]
chat_logs = {}  # Dict[str, List[Dict]]


