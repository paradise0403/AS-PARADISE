from .handlers import send
from tools import playlist
import random
import _thread
import _babase
import _bascenev1
import setting
from playersdata import pdata
from serverdata import serverdata
import babase
import bascenev1 as bs
from babase._general import Call
from tools import logger
from spazmod import ashx_pets  # Ensure ashx_pets.py is in the same folder

# Commands list
Commands = ['unban', 'recents', 'info', 'createteam', 'showid', 'hideid', 'lm', 'gp',
            'party', 'quit', 'kickvote', 'maxplayers', 'playlist', 'ban',
            'kick', 'remove', 'end', 'quit', 'mute', 'unmute', 'slowmo', 'nv',
            'dv', 'pause', 'tint',
            'cameramode', 'createrole', 'addrole', 'removerole', 'addcommand',
            'addcmd', 'removecommand', 'getroles', 'removecmd', 'changetag',
            'customtag', 'customeffect', 'removeeffect', 'removetag', 'add',
            'spectators', 'lobbytime', 'pet', 'custompet']

CommandAliases = ['max', 'rm', 'next', 'restart', 'mutechat', 'unmutechat',
                  'sm', 'slow', 'night', 'day', 'pausegame', 'camera_mode',
                  'rotate_camera', 'effect', 'p']

def success_msg(cmd_name):
    """Prints the execution notice in the game chat."""
    bs.chatmessage(f"{cmd_name.upper()} command is executed \ue048")

def ExcelCommand(command, arguments, clientid, accountid):
    # Standard IF/ELIF for better compatibility
    if command == 'unban':
        unban(arguments)
        success_msg(command)
    elif command == 'recents':
        get_recents(clientid)
    elif command == 'info':
        get_player_info(arguments, clientid)
        success_msg(command)
    elif command in ['maxplayers', 'max']:
        changepartysize(arguments)
        success_msg(command)
    elif command == 'createteam':
        create_team(arguments)
        success_msg(command)
    elif command == 'playlist':
        changeplaylist(arguments)
        success_msg(command)
    elif command == 'kick':
        kick(arguments)
        success_msg(command)
    elif command == 'ban':
        ban(arguments)
        success_msg(command)
    elif command in ['end', 'next']:
        end(arguments)
        success_msg(command)
    elif command == 'kickvote':
        kikvote(arguments, clientid)
        success_msg(command)
    elif command == 'hideid':
        hide_player_spec()
        success_msg(command)
    elif command == 'showid':
        show_player_spec()
        success_msg(command)
    elif command == 'lm':
        last_msgs(clientid)
        success_msg(command)
    elif command == 'gp':
        get_profiles(arguments, clientid)
        success_msg(command)
    elif command == 'party':
        party_toggle(arguments)
        success_msg(command)
    elif command in ['quit', 'restart']:
        quit_game(arguments)
        success_msg(command)
    elif command in ['mute', 'mutechat']:
        mute(arguments)
        success_msg(command)
    elif command in ['unmute', 'unmutechat']:
        un_mute(arguments)
        success_msg(command)
    elif command in ['remove', 'rm']:
        remove(arguments)
        success_msg(command)
    elif command in ['sm', 'slow', 'slowmo']:
        slow_motion(arguments)
        success_msg(command)
        bs.chatmessage("Slo-Mo Mode Toggled!")
    elif command in ['nv', 'night']:
        nv(arguments)
        success_msg(command)
    elif command == 'tint':
        tint(arguments)
        success_msg(command)
    elif command in ['pause', 'pausegame']:
        pause(arguments)
        success_msg(command)
    elif command in ['cameraMode', 'camera_mode', 'rotate_camera']:
        rotate_camera(arguments)
        success_msg(command)
    elif command == 'createrole':
        create_role(arguments)
        success_msg(command)
    elif command == 'addrole':
        add_role_to_player(arguments)
        success_msg(command)
    elif command == 'removerole':
        remove_role_from_player(arguments)
        success_msg(command)
    elif command == 'getroles':
        get_roles_of_player(arguments, clientid)
        success_msg(command)
    elif command in ['addcommand', 'addcmd']:
        add_command_to_role(arguments)
        success_msg(command)
    elif command in ['removecommand', 'removecmd']:
        remove_command_to_role(arguments)
        success_msg(command)
    elif command == 'changetag':
        change_role_tag(arguments)
        success_msg(command)
    elif command == 'customtag':
        set_custom_tag(arguments)
        success_msg(command)
    elif command in ['customeffect', 'effect']:
        set_custom_effect(arguments)
        success_msg(command)
    elif command == 'removetag':
        remove_custom_tag(arguments)
        success_msg(command)
    elif command == 'removeeffect':
        remove_custom_effect(arguments)
        success_msg(command)
    elif command == 'spectators':
        spectators(arguments)
        success_msg(command)
    elif command == 'lobbytime':
        change_lobby_check_time(arguments)
        success_msg(command)
    
    # --- PET COMMAND LOGIC ---
    elif command in ['pet', 'p', 'custompet']:
        try:
            target_id = int(arguments[0]) if (arguments and arguments[0] != '') else clientid
            # Direct call to the pet handler
            ashx_pets.handle_pet_command(arguments, target_id)
            success_msg(command)
        except Exception as e:
            print(f"Pet Command Error: {e}")

# --- CORE COMMAND FUNCTIONS ---

def slow_motion(arguments):
    activity = bs.get_foreground_host_activity()
    if activity:
        with activity.context:
            activity.globalsnode.slow_motion = not activity.globalsnode.slow_motion

def pause(arguments):
    activity = bs.get_foreground_host_activity()
    if activity:
        with activity.context:
            activity.globalsnode.paused = not activity.globalsnode.paused

def nv(arguments):
    activity = bs.get_foreground_host_activity()
    if activity:
        with activity.context:
            nv_tint = (0.5, 0.5, 1.0)
            if list(activity.globalsnode.tint) == [0.5, 0.5, 1.0]:
                activity.globalsnode.tint = (1, 1, 1)
                activity.globalsnode.ambient_color = (1, 1, 1)
            else:
                activity.globalsnode.tint = nv_tint
                activity.globalsnode.ambient_color = (1.5, 1.5, 1.5)

def tint(arguments):
    if len(arguments) == 3:
        try:
            r, g, b = float(arguments[0]), float(arguments[1]), float(arguments[2])
            activity = bs.get_foreground_host_activity()
            if activity:
                with activity.context:
                    activity.globalsnode.tint = (r, g, b)
        except Exception:
            pass

def rotate_camera(arguments):
    activity = bs.get_foreground_host_activity()
    if activity:
        with activity.context:
            activity.globalsnode.camera_mode = 'rotate' if activity.globalsnode.camera_mode != 'rotate' else 'normal'

def end(arguments):
    activity = bs.get_foreground_host_activity()
    if activity:
        with activity.context:
            activity.end_game()

def quit_game(arguments):
    babase.quit()

def create_team(arguments):
    if len(arguments) == 0:
        bs.chatmessage("Enter team name")
    else:
        from bascenev1._team import SessionTeam
        session = bs.get_foreground_host_session()
        session.sessionteams.append(SessionTeam(
            team_id=len(session.sessionteams) + 1,
            name=str(arguments[0]),
            color=(random.uniform(0, 1.2), random.uniform(0, 1.2), random.uniform(0, 1.2))))
        from bascenev1._lobby import Lobby
        session.lobby = Lobby()

def hide_player_spec():
    _babase.hide_player_device_id(True)

def show_player_spec():
    _babase.hide_player_device_id(False)

def get_player_info(arguments, client_id):
    if not arguments:
        send("Invalid client id", client_id)
        return
    for account in serverdata.recents:
        if account['client_id'] == int(arguments[0]):
            send(pdata.get_detailed_info(account["pbid"]), client_id)

def get_recents(client_id):
    for players in serverdata.recents:
        send(f"{players['client_id']} {players['deviceId']} {players['pbid']}", client_id)

def changepartysize(arguments):
    if arguments:
        bs.set_public_party_max_size(int(arguments[0]))

def changeplaylist(arguments):
    if arguments:
        serverdata.coopmode = (arguments[0] == 'coop')
        playlist.setPlaylist(arguments[0])

def kick(arguments):
    if arguments:
        cl_id = int(arguments[0])
        for ros in bs.get_game_roster():
            if ros["client_id"] == cl_id:
                logger.log("Kicked " + ros["display_string"])
        bs.disconnect_client(cl_id)

def kikvote(arguments, clientid):
    if not arguments or len(arguments) < 2:
        return
    if arguments[0] == 'enable':
        if arguments[1] == 'all':
            _babase.set_enable_default_kick_voting(True)
        else:
            try:
                cl_id = int(arguments[1])
                for ros in bs.get_game_roster():
                    if ros["client_id"] == cl_id:
                        pdata.enable_kick_vote(ros["account_id"])
                        send("Kick-vote will be enabled upon restart", clientid)
            except Exception: pass
    elif arguments[0] == 'disable':
        if arguments[1] == 'all':
            _babase.set_enable_default_kick_voting(False)
        else:
            try:
                cl_id = int(arguments[1])
                for ros in bs.get_game_roster():
                    if ros["client_id"] == cl_id:
                        _bascenev1.disable_kickvote(ros["account_id"])
                        pdata.disable_kick_vote(ros["account_id"], 2, "by chat command")
            except Exception: pass

def last_msgs(clientid):
    for i in bs.get_chat_messages():
        send(i, clientid)

def get_profiles(arguments, clientid):
    try:
        playerID = int(arguments[0])
        num = 1
        for i in bs.get_foreground_host_session().sessionplayers[playerID].inputdevice.get_player_profiles():
            send(f"{num})- {i}", clientid)
            num += 1
    except Exception: pass

def party_toggle(arguments):
    if arguments == ['public']:
        bs.set_public_party_enabled(True)
        bs.chatmessage("Party is public now")
    elif arguments == ['private']:
        bs.set_public_party_enabled(False)
        bs.chatmessage("Party is private now")

def ban(arguments):
    try:
        cl_id = int(arguments[0])
        duration = int(arguments[1]) if len(arguments) >= 2 else 0.5
        for ros in bs.get_game_roster():
            if ros["client_id"] == cl_id:
                pdata.ban_player(ros['account_id'], duration, "by chat command")
        for account in serverdata.recents:
            if account['client_id'] == cl_id:
                pdata.ban_player(account["pbid"], duration, "by chat command")
        kick(arguments)
    except Exception: pass

def unban(arguments):
    try:
        cl_id = int(arguments[0])
        for account in serverdata.recents:
            if account['client_id'] == cl_id:
                pdata.unban_player(account["pbid"])
    except Exception: pass

def mute(arguments):
    if not arguments:
        serverdata.muted = True
        return
    try:
        cl_id = int(arguments[0])
        duration = int(arguments[1]) if len(arguments) >= 2 else 0.5
        for ros in bs.get_game_roster():
            if ros["client_id"] == cl_id:
                pdata.mute(ros['account_id'], duration, "muted by chat command")
        for account in serverdata.recents:
            if account['client_id'] == cl_id:
                pdata.mute(account["pbid"], duration, "muted by chat command")
    except Exception: pass

def un_mute(arguments):
    if not arguments:
        serverdata.muted = False
        return
    try:
        cl_id = int(arguments[0])
        for ros in bs.get_game_roster():
            if ros["client_id"] == cl_id:
                pdata.unmute(ros['account_id'])
        for account in serverdata.recents:
            if account['client_id'] == cl_id:
                pdata.unmute(account["pbid"])
    except Exception: pass

def remove(arguments):
    if not arguments: return
    session = bs.get_foreground_host_session()
    if arguments[0] == 'all':
        for i in session.sessionplayers:
            i.remove_from_game()
    else:
        try:
            target = int(arguments[0])
            for i in session.sessionplayers:
                if i.inputdevice.client_id == target:
                    i.remove_from_game()
        except Exception: pass

def create_role(arguments):
    if arguments: pdata.create_role(arguments[0])

def add_role_to_player(arguments):
    if len(arguments) < 2: return
    session = bs.get_foreground_host_session()
    try:
        target = int(arguments[1])
        for i in session.sessionplayers:
            if i.inputdevice.client_id == target:
                pdata.add_player_role(arguments[0], i.get_v1_account_id())
    except Exception: pass

def remove_role_from_player(arguments):
    if len(arguments) < 2: return
    session = bs.get_foreground_host_session()
    try:
        target = int(arguments[1])
        for i in session.sessionplayers:
            if i.inputdevice.client_id == target:
                pdata.remove_player_role(arguments[0], i.get_v1_account_id())
    except Exception: pass

def get_roles_of_player(arguments, clientid):
    if not arguments: return
    try:
        session = bs.get_foreground_host_session()
        target = int(arguments[0])
        for i in session.sessionplayers:
            if i.inputdevice.client_id == target:
                roles = pdata.get_player_roles(i.get_v1_account_id())
                send(",".join(roles), clientid)
    except Exception: pass

def change_role_tag(arguments):
    if len(arguments) >= 2: pdata.change_role_tag(arguments[0], arguments[1])

def set_custom_tag(arguments):
    if len(arguments) < 2:
        bs.chatmessage("Usage: /customtag [Text] [ClientID] [AnimID]")
        return
    try:
        tag_text, client_id = arguments[0], int(arguments[1])
        anim_id = int(arguments[2]) if len(arguments) >= 3 else 0
        session = bs.get_foreground_host_session()
        for i in session.sessionplayers:
            if i.inputdevice.client_id == client_id:
                pdata.set_tag({'tag': tag_text, 'anim': anim_id}, i.get_v1_account_id())
    except Exception: pass

def remove_custom_tag(arguments):
    if not arguments: return
    session = bs.get_foreground_host_session()
    try:
        target = int(arguments[0])
        for i in session.sessionplayers:
            if i.inputdevice.client_id == target:
                pdata.remove_tag(i.get_v1_account_id())
    except Exception: pass

def remove_custom_effect(arguments):
    if not arguments: return
    session = bs.get_foreground_host_session()
    try:
        target = int(arguments[0])
        for i in session.sessionplayers:
            if i.inputdevice.client_id == target:
                pdata.remove_effect(i.get_v1_account_id())
    except Exception: pass

def set_custom_effect(arguments):
    if len(arguments) < 2: return
    session = bs.get_foreground_host_session()
    try:
        target = int(arguments[1])
        for i in session.sessionplayers:
            if i.inputdevice.client_id == target:
                pdata.set_effect(arguments[0], i.get_v1_account_id())
    except Exception: pass

def add_command_to_role(arguments):
    if len(arguments) == 2: pdata.add_command_role(arguments[0], arguments[1])

def remove_command_to_role(arguments):
    if len(arguments) == 2: pdata.remove_command_role(arguments[0], arguments[1])

def spectators(arguments):
    if not arguments: return
    if arguments[0] in ['on', 'off']:
        settings = setting.get_settings_data()
        settings["white_list"]["spectators"] = (arguments[0] == 'on')
        setting.commit(settings)
        bs.chatmessage(f"Spectators {arguments[0]}")

def change_lobby_check_time(arguments):
    if not arguments: return
    try:
        val = int(arguments[0])
        settings = setting.get_settings_data()
        settings["white_list"]["lobbychecktime"] = val
        setting.commit(settings)
        bs.chatmessage(f"Lobby check time is {val} now")
    except Exception: pass 
