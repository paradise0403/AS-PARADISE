import os
import sys
import json
import babase
import bascenev1 as bs
from spazmod import tag  # your tag.py

# --- CORRECT PATHS ---
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))  # script/dist
CUSTOM_JSON_PATH = os.path.join(BASE_PATH, 'baroot', 'mods', 'playersdata', 'custom.json')
try:
    storage_dir = babase.app.env.python_directory_storage
    DATA_PATH = os.path.join(storage_dir, 'coin_data.json')
except Exception:
    DATA_PATH = './coin_data.json'

# --- SEND FUNCTION ---
def get_send_func():
    try:
        import handlers
        return handlers.send
    except ImportError:
        try:
            from .handlers import send
            return send
        except:
            mod_dir = os.path.dirname(os.path.abspath(__file__))
            if mod_dir not in sys.path:
                sys.path.append(mod_dir)
            import handlers
            return handlers.send

# --- JSON HELPERS ---
def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

# --- COINS ---
def get_coins(account_id):
    data = load_json(DATA_PATH)
    return data.get(account_id, {}).get('coins', 0)

def deduct_coins(account_id, amount):
    data = load_json(DATA_PATH)
    if account_id not in data: return False
    curr = int(data[account_id].get('coins', 0))
    if curr < amount: return False
    data[account_id]['coins'] = curr - amount
    save_json(DATA_PATH, data)
    return True

# --- TAG SAVE/APPLY ---
def save_tag(account_id, tag_text, anim_id):
    data = load_json(CUSTOM_JSON_PATH)
    if "customtag" not in data:
        data["customtag"] = {}
    data["customtag"][account_id] = {"tag": tag_text, "anim": anim_id}
    save_json(CUSTOM_JSON_PATH, data)

def apply_tag_to_spaz(spaz, account_id):
    """Apply a player's tag to their in-game character."""
    custom_data = load_json(CUSTOM_JSON_PATH).get("customtag", {})
    if account_id in custom_data:
        node = getattr(spaz, 'node', None)
        if node:
            data = custom_data[account_id]
            tag_text = data.get("tag", "")
            anim_id = data.get("anim", 1)
            tag.addtag(node, spaz)

# --- /buytag COMMAND ---
def handle_buy_tag(arguments, client_id, account_id):
    send = get_send_func()
    if not arguments or len(arguments) < 2:
        send("Usage: /buytag <text> <effect_num>", client_id)
        return

    tag_text = " ".join(arguments[:-1])
    try:
        anim_id = int(arguments[-1])
    except:
        anim_id = 1

    prices = {1:25, 2:45, 3:40, 4:50, 5:60}
    total_cost = len(tag_text) * prices.get(anim_id, 25)
    print(f'total cost = {total_cost}')
    
    if total_cost > 0:
        if not deduct_coins(account_id, total_cost):
            send(f"Purchase Failed! You need {total_cost} coins", client_id)
            return

    # Save/overwrite tag
    #save_tag(account_id, tag_text, anim_id)

    # Apply immediately if player has spawned
    try:
        session = bs.get_foreground_host_session()
        for sp in session.sessionplayers:
            if sp.get_v1_account_id() == account_id:
                #'''
                from playersdata import pdata
                custom = pdata.get_custom()
                custom["customtag"][account_id] = {
                    "tag": tag_text,
                    "anim": anim_id
                }
                pdata.CacheData.custom = custom
                pdata.commit_c()
                print('success added taggy!')
                #'''
                #import coin_system
                #bank = coin_system.get_coins(account_id)
                #print(bank)
                #fire = get_coins(account_id)
                #print(f'how much coins u have is ---> {fire}')
        print('adding a tag?')
    except Exception as e:
        print("Error applying tag immediately:", e)

    send(f"Success! Tag '{tag_text}' purchased and applied!\nCost: {total_cost} coins", client_id)

def handle_buy_effect(arguments, client_id, account_id):
    send = get_send_func()

    if not arguments:
        send("Usage: /buyeffect <effect_name>", client_id)
        return

    effect_name = arguments[0].lower()

    # VALID EFFECTS LIST (same as your system)
    valid_effects = [
        "spark", "sparkground",
        "sweat", "sweatground",
        "distortion",
        "glow",
        "shine", "highlightshine", "rainbow",
        "scorch",
        "ice", "iceground",
        "slime", "metal", "splinter",
        "fairydust",
        "firespark",
        "noeffect"
    ]

    if effect_name not in valid_effects:
        send(f"Invalid effect: {effect_name}", client_id)
        return

    # 💰 PRICE SYSTEM (800–2500 range)
    prices = {
        "spark": 800,
        "sparkground": 850,
        "sweat": 900,
        "sweatground": 950,
        "distortion": 1200,
        "glow": 1500,
        "shine": 1100,
        "highlightshine": 1150,
        "rainbow": 2000,
        "scorch": 1400,
        "ice": 1200,
        "iceground": 1250,
        "slime": 1300,
        "metal": 1400,
        "splinter": 1350,
        "fairydust": 1600,
        "firespark": 2500,
        "noeffect": 0
    }

    cost = prices.get(effect_name, 1000)

    if cost > 0:
        if not deduct_coins(account_id, cost):
            send(f"Not enough coins! Need {cost}", client_id)
            return

    try:
        from playersdata import pdata

        custom = pdata.get_custom()

        if "customeffects" not in custom:
            custom["customeffects"] = {}

        current = custom["customeffects"].get(account_id, [])

        # fix if string
        if isinstance(current, str):
            current = [current]

        # avoid duplicate
        if effect_name in current:
            send(f"You already have '{effect_name}'", client_id)
            return

        current.append(effect_name)

        custom["customeffects"][account_id] = current

        pdata.CacheData.custom = custom
        pdata.commit_c()

    except Exception as e:
        print("Effect error:", e)
        send("Error applying effect!", client_id)
        return

    send(f"Effect '{effect_name}' purchased!\nCost: {cost}", client_id)

# --- SHOP DISPLAY ---
def show_main_shop(client_id):
    send = get_send_func()
    msg = (
        "\ue045 ------ SERVER SHOP ------ \ue045\n"
        "1. SHOP TAGS\n"
        "2. SHOP EFFECTS\n"
        "3. SHOP COMMANDS\n"
        "4. SHOP ROLES\n"
        "5. SHOP SERVER\n"
        "Type: /shop <category_name>"
    )
    send(msg, client_id)

def show_tags_shop(client_id):
    send = get_send_func()
    msg = (
        "\ue043 ----- TAGS ----- \ue043\n"
        "1. Standard Color Tag - 25 \ue01d/char\n"
        "2. Red & Yellow Wave - 45 \ue01d/char\n"
        "3. Smooth Color Wave - 40 \ue01d/char\n"
        "4. Blink Letter Wave - 50 \ue01d/char\n"
        "5. Rainbow Tag - 60 \ue01d/char\n\n"
        "\ue047 Pro Tip: Use /buytag <text> <effect_num>\n"
        "\ue048 Note: Tags are applied immediately!"
    )
    send(msg, client_id)

def show_effects_shop(client_id):
    send = get_send_func()
    msg = (
        "\ue043 ----- EFFECTS ----- \ue043\n"
        "1. Spark - 800 \ue01d\n"
        "2. Spark Ground - 850 \ue01d\n"
        "3. Sweat - 900 \ue01d\n"
        "4. Sweat Ground - 950 \ue01d\n"
        "5. Distortion - 1200 \ue01d\n"
        "6. Glow - 1500 \ue01d\n"
        "7. Shine - 1100 \ue01d\n"
        "8. Highlight Shine - 1150 \ue01d\n"
        "9. Rainbow - 2000 \ue01d\n"
        "10. Scorch - 1400 \ue01d\n"
        "11. Ice - 1200 \ue01d\n"
        "12. Ice Ground - 1250 \ue01d\n"
        "13. Slime - 1300 \ue01d\n"
        "14. Metal - 1400 \ue01d\n"
        "15. Splinter - 1350 \ue01d\n"
        "16. Fairy Dust - 1600 \ue01d\n"
        "17. Fire Spark - 2500 \ue01d\n\n"
        "\ue047 Pro Tip: Use /buyeffect <effect_name>\n"
        "\ue048 Note: Effects are applied on next spawn."
    )
    send(msg, client_id)

# --- SHOP COMMAND ---
def handle_shop_command(arguments, client_id):
    send = get_send_func()
    if not arguments or arguments == ['']:
        show_main_shop(client_id)
    elif arguments[0].lower() == 'tags':
        show_tags_shop(client_id)
    elif arguments[0].lower() == 'effects':
        show_effects_shop(client_id)
    else:
        send(f"\ue043 Category '{arguments[0]}' not found!\ue043", client_id)
 

import json
import os
import babase

PLAYERS_DATA_PATH = os.path.join(
    babase.env()["python_directory_user"], "playersdata" + os.sep
)

CUSTOM_FILE = PLAYERS_DATA_PATH + "custom.json"


def add_custom_tag(account_id, tag, anim=1):
    # Ensure directory exists
    os.makedirs(PLAYERS_DATA_PATH, exist_ok=True)
    
    #print(os.path.exists(CUSTOM_FILE))

    # Load existing data
    if os.path.exists(CUSTOM_FILE):
        with open(CUSTOM_FILE, "r") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    else:
        data = {}

    # Ensure structure
    if "customtag" not in data:
        data["customtag"] = {}

    # Add/update entry
    data["customtag"][account_id] = {
        "tag": tag,
        "anim": anim
    }

    # Save file
    with open(CUSTOM_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print(f"[TAG] Added/Updated: {account_id} -> {tag} (anim {anim})")
    #print("[DEBUG] Current customtag data:")
    #print(data["customtag"])
    print("WRITING TO:", CUSTOM_FILE)
    print(os.path.abspath(CUSTOM_FILE))

# --- SPAWN HOOK ---
class TagApplier(bs.Plugin):
    """Automatically applies purchased tags when players spawn."""
    def on_player_spawn(self, player):
        session_player = getattr(player, "sessionplayer", None)
        if not session_player:
            return
        account_id = session_player.get_v1_account_id()
        spaz = getattr(session_player, "spaz", None)
        if spaz:
            apply_tag_to_spaz(spaz, account_id)
