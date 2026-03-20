import babase
import bascenev1 as bs
import os
import json
import datetime

# Improved path logic to prevent crashing during startup
try:
    storage_dir = babase.app.env.python_directory_storage
    DATA_PATH = os.path.join(storage_dir, 'coin_data.json')
except Exception:
    DATA_PATH = './coin_data.json'

def _get_data():
    if not os.path.exists(DATA_PATH): return {}
    try:
        with open(DATA_PATH, 'r') as f: return json.load(f)
    except Exception: return {}

def _save_data(data):
    try:
        with open(DATA_PATH, 'w') as f: json.dump(data, f, indent=4)
    except Exception as e: print(f"Error saving coin_data: {e}")

def get_coins(account_id):
    data = _get_data()
    return data.get(account_id, {}).get('coins', 0)

def add_coins(account_id, amount):
    data = _get_data()
    if account_id not in data:
        data[account_id] = {'coins': 0, 'last_daily': '', 'items': []}
    data[account_id]['coins'] += int(amount)
    if data[account_id]['coins'] < 0: data[account_id]['coins'] = 0
    _save_data(data)
    return data[account_id]['coins']

def get_top_cashers(limit=10):
    """Returns the richest players."""
    data = _get_data()
    # Sort by coins
    sorted_data = sorted(data.items(), key=lambda x: x[1].get('coins', 0), reverse=True)
    return sorted_data[:limit]

def claim_daily(account_id):
    try:
        data = _get_data()
        today = str(datetime.date.today())
        
        # Player ka data check aur initialize karna
        if account_id not in data:
            data[account_id] = {'coins': 0, 'last_daily': '', 'items': []}
        
        # Check agar aaj claim ho chuka hai
        if data[account_id].get('last_daily') == today:
            return False, "Already claimed today!"
        
        # Coins update karna (Ensuring it's an integer)
        current_coins = int(data[account_id].get('coins', 0))
        data[account_id]['coins'] = current_coins + 50
        data[account_id]['last_daily'] = today
        
        # Data save karna
        _save_data(data)
        return True, "Claimed 50 \ue01d!"
        
    except Exception as e:
        print(f"Error in claim_daily: {e}")
        return False, "Error processing request!"

def reward_by_score(session, winning_team):
    """Direct payout: Lists each player on a new line."""
    try:
        if winning_team is not None:
            announcement = "\ue043 WINNER REWARDS \ue043\n"
            reward_sent = False
            
            for player in winning_team.players:
                acc_id = player.get_v1_account_id()
                if acc_id:
                    add_coins(acc_id, 10)
                    name = player.getname(icon=False)
                    # Create the line: "Player got 10 tickets"
                    announcement += f"{name} got 10 \ue01d\n"
                    reward_sent = True
            
            if reward_sent:
                bs.broadcastmessage(announcement, color=(1, 0.9, 0))
    except Exception as e:
        print(f"Coin Reward Error: {e}")
