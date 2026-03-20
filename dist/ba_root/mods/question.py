import babase
import bascenev1 as bs
import os
import json
import random

# --- PATH LOGIC (Matching your coin system) ---
try:
    storage_dir = babase.app.env.python_directory_storage
    DATA_PATH = os.path.join(storage_dir, 'coin_data.json')
except Exception:
    DATA_PATH = './coin_data.json'

# --- CONFIG ---
QUIZ_INTERVAL = 60.0  # Seconds between questions
PRIZE_COINS = 10

# --- DATA HELPERS (Identical to your coin script) ---
def _get_data():
    if not os.path.exists(DATA_PATH): return {}
    try:
        with open(DATA_PATH, 'r') as f: return json.load(f)
    except Exception: return {}

def _save_data(data):
    try:
        with open(DATA_PATH, 'w') as f: json.dump(data, f, indent=4)
    except Exception as e: print(f"Error saving quiz reward: {e}")

def add_quiz_reward(account_id, amount):
    """Adds coins using your specific coin_data.json structure."""
    data = _get_data()
    # If player is new, initialize with your exact fields
    if account_id not in data:
        data[account_id] = {'coins': 0, 'last_daily': '', 'items': []}
    
    # Update coins
    current_coins = int(data[account_id].get('coins', 0))
    data[account_id]['coins'] = current_coins + int(amount)
    
    _save_data(data)
    return data[account_id]['coins']

# --- QUESTIONS ---
QUESTIONS = [
    {"q": "What is 10 + 10?", "a": "20"},
    {"q": "Who is the owner of ASPARADISE?", "a": "ashx"},
    {"q": "Which bomb has a timer?", "a": "tnt"},
    {"q": "What is 50 x 2?", "a": "100"},
    {"q": "How many teams are in a standard game?", "a": "2"},
    {"q": "What is the capital of France?", "a": "paris"},
    {"q": "Which powerup gives you boxing gloves?", "a": "punch"},
    {"q": "What is 7 + 8?", "a": "15"},
    {"q": "Can you jump and throw bombs? (yes/no)", "a": "yes"}
]

class QuizManager:
    def __init__(self):
        self.current_answer = None
        self.active = False
        # Use a slight delay before starting to ensure game is ready
        bs.AppTimer(10.0, self.start_timer)

    def start_timer(self):
        # Loop the quiz every QUIZ_INTERVAL
        bs.AppTimer(QUIZ_INTERVAL, self.ask, repeat=True)

    def ask(self):
        # We need to make sure we are in a session/activity context to broadcast
        activity = bs.get_foreground_host_activity()
        if not activity:
            return

        quiz = random.choice(QUESTIONS)
        self.current_answer = quiz['a'].lower()
        self.active = True
        
        with activity.context:
            # UI Messaging
            bs.broadcastmessage("\ue043 --- FAST FINGERS --- \ue043", color=(1, 1, 0))
            bs.broadcastmessage(f"QUESTION: {quiz['q']}", color=(1, 1, 1))
            bs.broadcastmessage(f"Type answer to win {PRIZE_COINS} \ue01d", color=(0.2, 1, 0.2))

    def check(self, msg, user_name, account_id):
        if not self.active or not self.current_answer:
            return
        
        if msg.lower().strip() == self.current_answer:
            self.active = False
            new_bal = add_quiz_reward(account_id, PRIZE_COINS)
            
            bs.broadcastmessage(f"?? {user_name} got it right!", color=(0, 1, 0))
            bs.broadcastmessage(f"Answer: {self.current_answer.upper()} | New Balance: {new_bal} \ue01d", color=(1, 1, 1))
            self.current_answer = None

# Global Quiz Instance
_quiz = QuizManager()

def handle_chat(msg, client_id):
    """
    Called from chat handler to check for quiz answers.
    """
    if msg is None: return
    
    activity = bs.get_foreground_host_activity()
    if not activity: return

    # Check the message against the active quiz
    for player in activity.players:
        if player.sessionplayer.inputdevice.client_id == client_id:
            aid = player.sessionplayer.get_v1_account_id()
            if aid:
                _quiz.check(msg, player.getname(icon=False), aid)