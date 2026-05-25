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

    prices = {
    1: 25,
    2: 45,
    3: 40,
    4: 50,
    5: 60,
    6: 75,
    7: 80,
    8: 90,
    9: 100,
    10: 120,
    11: 130,
    12: 140
}
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
        "spark",
        "sparkground",
        "sweat",
        "sweatground",
        "distortion",
        "glow",
        "shine",
        "highlightshine",
        "rainbow",
        "scorch",
        "ice",
        "iceground",
        "slime",
        "metal",
        "splinter",
        "fairydust",
        "surrounder",
        "fire",
        "stars",
        "new_rainbow",
        "footprint",
        "chispitas",
        "darkmagic",
        "colorfullspark",
        "ring",
        "brust",
        "ringstars",
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
        "surrounder": 2200,
        "fire": 2500,
        "stars": 2600,
        "new_rainbow": 3000,
        "footprint": 1800,
        "chispitas": 3200,
        "darkmagic": 4000,
        "colorfullspark": 3500,
        "ring": 2800,
        "brust": 5000,
        "ringstars": 5500,
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
        "Type: /shop <category_name>"
    )
    send(msg, client_id)

def show_tags_shop(client_id):
    send = get_send_func()

    msg = (
        "\ue043 ===== TAG EFFECT SHOP ===== \ue043\n"

        "\ue047 1 = RGB Flash Tag\n"
        "   Price: 25 \ue01d per character\n"
        "\ue047 2 = Red Yellow Wave\n"
        "   Price: 45 \ue01d per character\n"
        "\ue047 3 = Fade Blink Tag\n"
        "   Price: 40 \ue01d per character\n"
        "\ue047 4 = Fast Blink Tag\n"
        "   Price: 50 \ue01d per character\n"
        "\ue047 5 = Rainbow Wave\n"
        "   Price: 60 \ue01d per character\n"
        "\ue047 6 = Ultra Rainbow\n"
        "   Price: 75 \ue01d per character\n"
        "\ue047 7 = Golden Shine\n"
        "   Price: 80 \ue01d per character\n"
        "\ue047 8 = Neon Pulse\n"
        "   Price: 90 \ue01d per character\n"
        "\ue047 9 = Vertical Bounce\n"
        "   Price: 100 \ue01d per character\n"
        "\ue047 10 = India Flag Style\n"
        "   Price: 120 \ue01d per character\n"
        "\ue047 11 = Red Blue Motion\n"
        "   Price: 130 \ue01d per character\n"
        "\ue047 12 = White Yellow Glow\n"
        "   Price: 140 \ue01d per character\n"
        "\ue046 Use: /buytag <text> <effect_id>\n"
        "\ue048 Example: /buytag ASHX 6"
    )

    send(msg, client_id)

def show_effects_shop(client_id):
    send = get_send_func()
    msg = (
        "\ue043 ----- EFFECT SHOP ----- \ue043\n"
        "spark - 800\n"
        "sparkground - 850\n"
        "sweat - 900\n"
        "sweatground - 950\n"
        "distortion - 1200\n"
        "glow - 1500\n"
        "shine - 1100\n"
        "highlightshine - 1150\n"
        "rainbow - 2000\n"
        "scorch - 1400\n"
        "ice - 1200\n"
        "iceground - 1250\n"
        "slime - 1300\n"
        "metal - 1400\n"
        "splinter - 1350\n"
        "fairydust - 1600\n"
        "surrounder - 2200\n"
        "fire - 2500\n"
        "stars - 2600\n"
        "new_rainbow - 3000\n"
        "footprint - 1800\n"
        "chispitas - 3200\n"
        "darkmagic - 4000\n"
        "colorfullspark - 3500\n"
        "ring - 2800\n"
        "brust - 5000\n"
        "ringstars - 5500\n\n"
        "Use: /buyeffect <name>\n"
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
