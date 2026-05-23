import babase
import bascenev1 as bs
from tools import corelib
from .handlers import handlemsg, handlemsg_all

Commands = [
    'fly',
    'invisible',
    'headless',
    'creepy',
    'celebrate',
    'spaz',
    'speed',
    'floater'
]

CommandAliases = [
    'inv',
    'hl',
    'creep',
    'celeb',
    'flo'
]


def ExcelCommand(command, arguments, clientid, accountid):

    if command == 'speed':
        speed(arguments)

    elif command == 'fly':
        fly(arguments)

    elif command in ['inv', 'invisible']:
        invi(arguments)

    elif command in ['hl', 'headless']:
        headless(arguments)

    elif command in ['creepy', 'creep']:
        creep(arguments)

    elif command in ['celebrate', 'celeb']:
        celeb(arguments)

    elif command == 'spaz':
        spaz(arguments)

    elif command in ['floater', 'flo']:
        floater_cmd(arguments, clientid)


# ================= FLOATER =================

def floater_cmd(arguments, clientid):

    try:

        from features import floater

        if arguments == [] or arguments == ['']:

            floater.assignFloInputs(clientid)

        else:

            floater.assignFloInputs(int(arguments[0]))

        bs.broadcastmessage(
            'Floater Enabled!',
            color=(0, 1, 1),
            transient=True
        )

    except Exception as e:

        print('Floater Error:', e)

        bs.broadcastmessage(
            f'Floater Error: {e}',
            color=(1, 0, 0),
            transient=True
        )


# ================= SPEED =================

def speed(arguments):

    if arguments == [] or arguments == ['']:
        return

    try:
        corelib.set_speed(float(arguments[0]))
    except:
        pass


# ================= FLY =================

def fly(arguments):

    if arguments == [] or arguments == ['']:
        return

    activity = bs.get_foreground_host_activity()

    if arguments[0] == 'all':

        for players in activity.players:

            try:

                node = players.actor.node

                node.fly = not node.fly

            except:
                pass

    else:

        try:

            player = int(arguments[0])

            node = activity.players[player].actor.node

            node.fly = not node.fly

        except:
            return


# ================= INVISIBLE =================

def invi(arguments):

    if arguments == [] or arguments == ['']:
        return

    activity = bs.get_foreground_host_activity()

    if arguments[0] == 'all':

        for i in activity.players:

            try:

                body = i.actor.node

                body.head_mesh = None
                body.torso_mesh = None
                body.upper_arm_mesh = None
                body.forearm_mesh = None
                body.pelvis_mesh = None
                body.hand_mesh = None
                body.toes_mesh = None
                body.upper_leg_mesh = None
                body.lower_leg_mesh = None
                body.style = 'cyborg'

            except:
                pass

    else:

        try:

            player = int(arguments[0])

            body = activity.players[player].actor.node

            body.head_mesh = None
            body.torso_mesh = None
            body.upper_arm_mesh = None
            body.forearm_mesh = None
            body.pelvis_mesh = None
            body.hand_mesh = None
            body.toes_mesh = None
            body.upper_leg_mesh = None
            body.lower_leg_mesh = None
            body.style = 'cyborg'

        except:
            return


# ================= HEADLESS =================

def headless(arguments):

    if arguments == [] or arguments == ['']:
        return

    activity = bs.get_foreground_host_activity()

    if arguments[0] == 'all':

        for players in activity.players:

            try:

                node = players.actor.node

                node.head_mesh = None
                node.style = 'cyborg'

            except:
                pass

    else:

        try:

            player = int(arguments[0])

            node = activity.players[player].actor.node

            node.head_mesh = None
            node.style = 'cyborg'

        except:
            return


# ================= CREEP =================

def creep(arguments):

    if arguments == [] or arguments == ['']:
        return

    activity = bs.get_foreground_host_activity()

    if arguments[0] == 'all':

        for players in activity.players:

            try:

                node = players.actor.node

                node.head_mesh = None

                players.actor.handlemessage(
                    bs.PowerupMessage(
                        poweruptype='punch'
                    )
                )

                players.actor.handlemessage(
                    bs.PowerupMessage(
                        poweruptype='shield'
                    )
                )

            except:
                pass

    else:

        try:

            player = int(arguments[0])

            node = activity.players[player].actor.node

            node.head_mesh = None

            activity.players[player].actor.handlemessage(
                bs.PowerupMessage(
                    poweruptype='punch'
                )
            )

            activity.players[player].actor.handlemessage(
                bs.PowerupMessage(
                    poweruptype='shield'
                )
            )

        except:
            return


# ================= CELEB =================

def celeb(arguments):

    if arguments == [] or arguments == ['']:
        return

    if arguments[0] == 'all':

        handlemsg_all(bs.CelebrateMessage())

    else:

        try:

            player = int(arguments[0])

            handlemsg(
                player,
                bs.CelebrateMessage()
            )

        except:
            return


# ================= SPAZ =================

def spaz(arguments):

    if arguments == [] or arguments == ['']:
        return

    return 