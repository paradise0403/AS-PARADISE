# Released under the MIT License. See LICENSE for details.

from datetime import datetime
import babase
import bascenev1 as bs
import setting
from chathandle.chatfilter import chatfilter
from chathandle.chatcommands import command_executor
from features import votingmachine
from playersdata import pdata
from serverdata import serverdata
from tools import logger, servercheck
from features.discord_bot import chat_buffer, chat_lock, player_info

# --- IMPORT QUIZ SYSTEM ---
try:
    from ba_root.mods import question
except ImportError:
    try:
        import question
    except:
        question = None

def clean_bs_text(text: str) -> str:
    return ''.join(
        ch for ch in text
        if not (0xE000 <= ord(ch) <= 0xF8FF)
    )

settings = setting.get_settings_data()

def filter_chat_message(msg, client_id):
    if msg:
        # --- QUIZ CHECK HOOK ---
        # Sabse pehle check karo ki answer sahi hai ya nahi
        if question:
            question.handle_chat(msg, client_id)

        name = "Unknown"
        pbid = "unknown"
        v2 = "unknown"

        for i in bs.get_game_roster():
            if i['client_id'] == client_id:
                pbid = i.get('account_id', 'unknown')
                v2 = i.get('display_string', 'unknown')
                try:
                    name = i['players'][0]['name_full']
                except:
                    name = "<in-lobby>"
                break

        clean_name = clean_bs_text(name)
        clean_v2 = clean_bs_text(v2)
        clean_msg = clean_bs_text(msg)

        if clean_name == "<in-lobby>":
            display_name = clean_v2
        else:
            display_name = clean_name

        with chat_lock:
            player_info[client_id] = {
                "name": clean_name,
                "pbid": pbid,
                "v2": v2
            }

            if display_name == clean_v2:
                chat_buffer.append(f"?? <:v2:1462179402535272550>{display_name}: {clean_msg}")
            else:
                chat_buffer.append(f"?? {display_name}: {clean_msg}")

    now = datetime.now()
    if client_id == -1:
        if msg.startswith("/"):
            command_executor.execute(msg, client_id)
            return None
        logger.log(f"Host msg: | {msg}", "chat")
        return msg

    acid = ""
    displaystring = ""
    currentname = ""

    for i in bs.get_game_roster():
        if i['client_id'] == client_id:
            acid = i['account_id']
            try:
                currentname = i['players'][0]['name_full']
            except:
                currentname = "<in-lobby>"
            displaystring = i['display_string']

    if acid:
        msg = chatfilter.filter(msg, acid, client_id)
    else:
        bs.broadcastmessage("\ue00cFetching your account info , please wait\ue047",
                            transient=True, clients=[client_id])
        return

    if msg == None:
        return

    logger.log(f'{acid}  |  {displaystring}| {currentname} | {msg}', "chat")
    
    if msg.startswith("/"):
        msg = command_executor.execute(msg, client_id)
        if msg == None:
            return

    if msg in ["end", "dv", "nv", "sm"] and settings["allowVotes"]:
        votingmachine.vote(acid, client_id, msg)

    if acid in serverdata.clients and serverdata.clients[acid]["verified"]:
        if serverdata.muted:
            bs.broadcastmessage("\ue041Server on mute\ue04d", transient=True, clients=[client_id])
            return
        elif acid in pdata.get_blacklist()["muted-ids"] and now < datetime.strptime(pdata.get_blacklist()["muted-ids"][acid]["till"], "%Y-%m-%d %H:%M:%S"):
            bs.broadcastmessage("\ue04fYou are on mute\ue00c", transient=True, clients=[client_id])
            return None
        elif servercheck.get_account_age(serverdata.clients[acid]["accountAge"]) < settings['minAgeToChatInHours']:
            bs.broadcastmessage("\ue045New accounts not allowed to chat\ue04f", transient=True, clients=[client_id])
            return None
        else:
            if msg.startswith(",") and settings["allowTeamChat"]:
                return command_executor.QuickAccess(msg, client_id)
            if msg.startswith(".") and settings["allowInGameChat"]:
                return command_executor.QuickAccess(msg, client_id)
            return msg
    else:
        bs.broadcastmessage("\ue020Fetching your account info\ue046", transient=True, clients=[client_id])
        return None