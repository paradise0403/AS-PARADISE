import babase
import bascenev1 as bs
from .handlers import handlemsg, handlemsg_all, clientid_to_myself

Commands = [
    'kill',
    'heal',
    'curse',
    'sleep',
    'superpunch',
    'gloves',
    'shield',
    'freeze',
    'unfreeze',
    'godmode'
]

CommandAliases = [
    'die',
    'heath',
    'cur',
    'sp',
    'punch',
    'protect',
    'ice',
    'thaw',
    'gm'
]


def ExcelCommand(command, arguments, clientid, accountid):

    if command in ['kill', 'die']:
        kill(arguments, clientid)

    elif command in ['heal', 'heath']:
        heal(arguments, clientid)

    elif command in ['curse', 'cur']:
        curse(arguments, clientid)

    elif command == 'sleep':
        sleep(arguments, clientid)

    elif command in ['sp', 'superpunch']:
        super_punch(arguments, clientid)

    elif command in ['gloves', 'punch']:
        gloves(arguments, clientid)

    elif command in ['shield', 'protect']:
        shield(arguments, clientid)

    elif command in ['freeze', 'ice']:
        freeze(arguments, clientid)

    elif command in ['unfreeze', 'thaw']:
        un_freeze(arguments, clientid)

    elif command in ['gm', 'godmode']:
        god_mode(arguments, clientid)


def _get_activity():
    try:
        return bs.get_foreground_host_activity()
    except Exception:
        return None


def _is_empty(arguments):
    return arguments == [] or arguments == ['']


def _safe_actor(player):

    try:
        actor = player.actor

        if actor is None:
            return None

        if not actor.node:
            return None

        if not actor.node.exists():
            return None

        return actor

    except Exception:
        return None


def _get_players(arguments, clientid):

    activity = _get_activity()

    if activity is None:
        return []

    if _is_empty(arguments):

        try:
            myself = clientid_to_myself(clientid)
            return [activity.players[myself]]
        except Exception:
            return []

    if str(arguments[0]).lower() == 'all':
        return list(activity.players)

    try:
        req_player = int(arguments[0])
        return [activity.players[req_player]]
    except Exception:
        return []


def kill(arguments, clientid):

    players = _get_players(arguments, clientid)

    for player in players:

        actor = _safe_actor(player)

        if actor:
            actor.handlemessage(bs.DieMessage())


def heal(arguments, clientid):

    players = _get_players(arguments, clientid)

    for player in players:

        actor = _safe_actor(player)

        if actor:
            actor.handlemessage(
                bs.PowerupMessage(
                    poweruptype='health'
                )
            )


def curse(arguments, clientid):

    players = _get_players(arguments, clientid)

    for player in players:

        actor = _safe_actor(player)

        if actor:
            actor.handlemessage(
                bs.PowerupMessage(
                    poweruptype='curse'
                )
            )


def sleep(arguments, clientid):

    players = _get_players(arguments, clientid)

    for player in players:

        actor = _safe_actor(player)

        if actor:
            actor.node.handlemessage(
                'knockout',
                8000
            )


def super_punch(arguments, clientid):

    players = _get_players(arguments, clientid)

    for player in players:

        actor = _safe_actor(player)

        if actor is None:
            continue

        try:

            enabled = getattr(
                actor,
                '_super_punch',
                False
            )

            if not enabled:

                actor._super_punch = True

                actor._punch_power_scale = 15
                actor._punch_cooldown = 0

                bs.broadcastmessage(
                    f'{player.getname()} SUPERPUNCH ON',
                    color=(0, 1, 0)
                )

            else:

                actor._super_punch = False

                actor._punch_power_scale = 1.2
                actor._punch_cooldown = 400

                bs.broadcastmessage(
                    f'{player.getname()} SUPERPUNCH OFF',
                    color=(1, 0, 0)
                )

        except Exception as e:
            print('Super Punch Error:', e)


def gloves(arguments, clientid):

    players = _get_players(arguments, clientid)

    for player in players:

        actor = _safe_actor(player)

        if actor:
            actor.handlemessage(
                bs.PowerupMessage(
                    poweruptype='punch'
                )
            )


def shield(arguments, clientid):

    players = _get_players(arguments, clientid)

    for player in players:

        actor = _safe_actor(player)

        if actor:
            actor.handlemessage(
                bs.PowerupMessage(
                    poweruptype='shield'
                )
            )


def freeze(arguments, clientid):

    players = _get_players(arguments, clientid)

    for player in players:

        actor = _safe_actor(player)

        if actor:
            actor.handlemessage(
                bs.FreezeMessage()
            )


def un_freeze(arguments, clientid):

    players = _get_players(arguments, clientid)

    for player in players:

        actor = _safe_actor(player)

        if actor:
            actor.handlemessage(
                bs.ThawMessage()
            )


def god_mode(arguments, clientid):

    players = _get_players(arguments, clientid)

    for player in players:

        actor = _safe_actor(player)

        if actor is None:
            continue

        try:

            enabled = getattr(
                actor,
                '_godmode',
                False
            )

            if not enabled:

                actor._godmode = True

                actor.hitpoints = 99999
                actor.hitpoints_max = 99999

                actor._punch_power_scale = 7
                actor._punch_cooldown = 0

                try:
                    actor.node.hockey = True
                except Exception:
                    pass

                bs.emitfx(
                    position=actor.node.position,
                    count=25,
                    spread=0.5,
                    scale=1.2,
                    chunk_type='spark'
                )

                bs.broadcastmessage(
                    f'{player.getname()} GODMODE ON',
                    color=(0, 1, 0)
                )

            else:

                actor._godmode = False

                actor.hitpoints_max = 1000

                if actor.hitpoints > 1000:
                    actor.hitpoints = 1000

                actor._punch_power_scale = 1.2
                actor._punch_cooldown = 400

                try:
                    actor.node.hockey = False
                except Exception:
                    pass

                bs.broadcastmessage(
                    f'{player.getname()} GODMODE OFF',
                    color=(1, 0, 0)
                )

        except Exception as e:
            print('GodMode Error:', e) 