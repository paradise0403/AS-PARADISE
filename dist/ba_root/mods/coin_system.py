# ba_meta require api 9

import os
import json
import random
import datetime

import babase
import bascenev1 as bs


BASE_DIR = os.path.dirname(__file__)
SETTING_PATH = os.path.join(BASE_DIR, "setting.json")

try:
    storage_dir = babase.app.env.python_directory_storage
    DATA_PATH = os.path.join(storage_dir, "coin_data.json")
except Exception:
    DATA_PATH = "./coin_data.json"


def get_settings():
    try:
        with open(SETTING_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print("coin_system setting load error:", e)
        return {}


def get_quiz_settings():
    return get_settings().get("quizSystem", {})


def _get_data():
    if not os.path.exists(DATA_PATH):
        return {}

    try:
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_data(data):
    try:
        with open(DATA_PATH, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Coin save error: {e}")


def get_coins(account_id):
    data = _get_data()
    return data.get(account_id, {}).get("coins", 0)


def add_coins(account_id, amount):
    data = _get_data()

    if account_id not in data:
        data[account_id] = {
            "coins": 0,
            "last_daily": "",
            "items": []
        }

    data[account_id]["coins"] += int(amount)

    if data[account_id]["coins"] < 0:
        data[account_id]["coins"] = 0

    _save_data(data)
    return data[account_id]["coins"]


def get_top_cashers(limit=10):
    data = _get_data()
    return sorted(
        data.items(),
        key=lambda x: x[1].get("coins", 0),
        reverse=True
    )[:limit]


def claim_daily(account_id):
    try:
        data = _get_data()
        today = str(datetime.date.today())

        if account_id not in data:
            data[account_id] = {
                "coins": 0,
                "last_daily": "",
                "items": []
            }

        if data[account_id].get("last_daily") == today:
            return False, "Already claimed today!"

        data[account_id]["coins"] += 50
        data[account_id]["last_daily"] = today

        _save_data(data)
        return True, "Claimed 50 \ue01d!"

    except Exception as e:
        print(f"Daily reward error: {e}")
        return False, "Error"


_current_question = None
_current_answers = []
_answered_by = None

_quiz_timer = None
_first_timer = None


def ask_question():
    global _current_question, _current_answers, _answered_by

    quiz = get_quiz_settings()

    if not quiz.get("enable", True):
        return

    questions = quiz.get("questions", {})

    if not questions:
        print("coin_system: no quiz questions found in setting.json")
        return

    _answered_by = None
    _current_question = random.choice(list(questions.keys()))
    _current_answers = questions[_current_question]

    bs.chatmessage(
    _current_question,
    sender_override="\ue021asquiz"
)

def _get_player(client_id):
    name = "Player"
    account_id = None

    try:
        for ros in bs.get_game_roster():
            if ros.get("client_id") == client_id:
                account_id = ros.get("account_id")
                try:
                    name = ros["players"][0]["name_full"]
                except Exception:
                    name = "<in-lobby>"
                break
    except Exception as e:
        print("Roster error:", e)

    return name, account_id


def handle_chat(msg, client_id):
    global _answered_by

    if not _current_answers:
        return False

    clean_msg = str(msg).strip().lower()
    answers = [str(a).lower() for a in _current_answers]

    if clean_msg not in answers:
        return False

    name, account_id = _get_player(client_id)

    if _answered_by is not None:
        bs.chatmessage(
    f"Already awarded to {_answered_by}.",
    sender_override="\ue021asquiz"
)
        return True

    _answered_by = name

    reward = int(get_quiz_settings().get("rewardCoins", 10))

    if account_id:
        add_coins(account_id, reward)

    try:
        bs.getsound("cashRegister").play()
    except Exception:
        pass

    bs.chatmessage(
    f"Congratulations {name} you answered it correctly you won {reward} \ue01d",
    sender_override="\ue021asquiz"
)

    return True


def start_quiz():
    global _quiz_timer, _first_timer

    quiz = get_quiz_settings()

    if not quiz.get("enable", True):
        print("coin_system: quiz disabled in setting.json")
        return

    delay = float(quiz.get("questionDelay", 30))
    first_delay = float(quiz.get("firstQuestionDelay", 5))

    print("🔥 Coin Quiz start_quiz called")

    _first_timer = bs.AppTimer(first_delay, ask_question)
    _quiz_timer = bs.AppTimer(delay, ask_question, repeat=True)


def reward_by_score(session, winning_team):
    try:
        if winning_team is None:
            return

        reward = int(get_quiz_settings().get("rewardCoins", 10))

        announcement = "\ue043 ASPARADISE - WINNER REWARDS \ue043\n"
        reward_sent = False

        for player in winning_team.players:
            acc_id = player.get_v1_account_id()

            if acc_id:
                add_coins(acc_id, reward)
                name = player.getname(icon=False)
                announcement += f"{name} got {reward} \ue01d\n"
                reward_sent = True

        if reward_sent:
            bs.broadcastmessage(announcement, color=(1, 0.9, 0))

    except Exception as e:
        print(f"Coin Reward Error: {e}")


# ba_meta export babase.Plugin
class CoinQuizPlugin(babase.Plugin):

    def on_app_running(self):
        print("🔥 Coin + Quiz Plugin Loaded")
        start_quiz() 
