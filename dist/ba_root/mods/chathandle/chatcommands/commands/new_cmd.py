# ba_meta require api 9

import os
import json
import bascenev1 as bs

from . import normal_commands
from . import management
from . import fun
from . import cheats
from bascenev1lib.actor.zoomtext import ZoomText


BASE_DIR = os.path.dirname(__file__)
MODS_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..', '..'))
ROLES_PATH = os.path.join(MODS_DIR, 'playersdata', 'roles.json')


Commands = [
    'cmdlist',
    'help',
    'zm',
    'rolelist',
    'acl',
    'vcl',
    'tcl',
    'ccl',
    'lcl'
]

CommandAliases = [
    'cmds',
    'commands',
    'zoommessage'
]


MODULES = {
    'NORMAL': normal_commands,
    'MANAGEMENT': management,
    'FUN': fun,
    'CHEATS': cheats,
}


ROLE_MAP = {
    'acl': 'admin',
    'vcl': 'vip',
    'tcl': 'tcs',
    'ccl': 'cs',
    'lcl': 'leadstaff'
}


# ==================================================
# MAIN EXECUTOR
# ==================================================

def ExcelCommand(command, arguments, clientid, accountid):

    if command in ['cmdlist', 'cmds', 'commands']:
        cmd_list()

    elif command == 'help':
        help_cmd(arguments)

    elif command in ['zm', 'zoommessage']:
        zm(arguments, clientid)

    elif command == 'rolelist':
        role_list()

    elif command in ROLE_MAP:
        role_cmd_list(ROLE_MAP[command])


# ==================================================
# HELPERS
# ==================================================

def _merge(commands, aliases):
    return sorted(list(set(list(commands) + list(aliases))))


def _chunk_list(items, size=6):
    return [items[i:i + size] for i in range(0, len(items), size)]


def _all_commands():

    data = {}

    for section, module in MODULES.items():

        cmds = getattr(module, 'Commands', [])
        aliases = getattr(module, 'CommandAliases', [])

        data[section] = _merge(cmds, aliases)

    data['NEW'] = _merge(Commands, CommandAliases)

    return data


def _flat_commands():

    flat = {}

    for section, cmds in _all_commands().items():

        for cmd in cmds:
            flat[cmd] = section

    return flat


def _guess_usage(cmd, section):

    if section == 'NORMAL':
        return f'Type /{cmd}'

    if section in ['MANAGEMENT', 'FUN', 'CHEATS']:
        return f'Type /{cmd} <id/all>'

    if section == 'NEW':

        if cmd == 'help':
            return 'Type /help <command>'

        return f'Type /{cmd}'

    return f'Type /{cmd}'


def _send(msg):

    bs.chatmessage(
        msg,
        sender_override=u'\ue043AS PARADISE'
    )


# ==================================================
# CMD LIST
# ==================================================

def cmd_list():

    data = _all_commands()

    _send(u'\ue043 AS PARADISE CMD LIST \ue043')
    _send('━━━━━━━━━━━━━━━━━━')

    for section in ['NORMAL', 'MANAGEMENT', 'FUN', 'CHEATS', 'NEW']:

        cmds = data.get(section, [])

        if not cmds:
            continue

        _send(f'{section} COMMANDS')

        for chunk in _chunk_list(cmds, 6):

            _send(
                ' • ' + ' , '.join(chunk)
            )

    _send('━━━━━━━━━━━━━━━━━━')


# ==================================================
# HELP CMD
# ==================================================

def help_cmd(arguments):

    flat = _flat_commands()

    if not arguments:

        _send(
            'Usage ➜ Type /help <command>'
        )

        return

    cmd = str(arguments[0]).lower().replace('/', '').strip()

    if cmd not in flat:

        _send(
            f'No command found: /{cmd}'
        )

        return

    section = flat[cmd]

    usage = _guess_usage(cmd, section)

    _send(
        f'Usage ➜ {usage}'
    )


# ==================================================
# ZM
# ==================================================

def zm(arguments, clientid):

    if len(arguments) == 0:

        _send(
            'Usage ➜ /zm <message>'
        )

        return

    msg = " ".join(arguments)

    try:

        activity = bs.get_foreground_host_activity()

        with activity.context:

            ZoomText(
                msg,
                position=(0, 180),
                maxwidth=800,
                lifespan=1.2,
                color=(1, 1, 1),
                trailcolor=(0.5, 0, 1, 0),
                flash=False,
                jitter=2.0
            ).autoretain()

    except Exception as e:

        _send(
            f'ZM Error: {e}'
        )


# ==================================================
# LOAD ROLES
# ==================================================

def _load_roles():

    try:

        with open(ROLES_PATH, 'r') as f:
            return json.load(f)

    except Exception as e:

        _send(
            f'roles.json error: {e}'
        )

        return {}


# ==================================================
# ROLE LIST
# ==================================================

def role_list():

    roles = _load_roles()

    if not roles:
        return

    role_names = sorted(list(roles.keys()))

    _send(u'\ue043 AS PARADISE ROLE LIST \ue043')
    _send('━━━━━━━━━━━━━━━━━━')

    for chunk in _chunk_list(role_names, 5):

        _send(
            ' • ' + ' , '.join(chunk)
        )

    _send('━━━━━━━━━━━━━━━━━━')


# ==================================================
# ROLE CMD LIST
# ==================================================

def role_cmd_list(role_key):

    roles = _load_roles()

    if role_key not in roles:

        _send(
            f'Role not found: {role_key}'
        )

        return

    cmds = roles[role_key].get('commands', [])

    if not cmds:

        _send(
            f'{role_key.upper()} has no commands.'
        )

        return

    _send(
        f'\ue043 {role_key.upper()} COMMANDS \ue043'
    )

    _send('━━━━━━━━━━━━━━━━━━')

    for chunk in _chunk_list(cmds, 6):

        _send(
            ' • ' + ' , '.join(chunk)
        )

    _send('━━━━━━━━━━━━━━━━━━') 