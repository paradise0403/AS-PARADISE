# Ender Server Bot (Auto spawn when <=2 players)

from bascenev1lib.actor.spaz import Spaz
from babase import Plugin
import babase
import bascenev1 as bs

from bascenev1 import (
    get_foreground_host_activity as ga,
    getnodes as GN,
    timer as tick,
    StandMessage,
    DieMessage
)

from math import dist
from random import choice


# --------------------------------------------------
# Base Bot
# --------------------------------------------------

class Bot:

    def __init__(self, position=(0, 0, 0)):

        self.bot = Spaz(
            color=(0, 0, 0),
            highlight=(0, 0, 0),
            character="Pixel"
        )

        self.bot.handlemessage(StandMessage(position, 0))
        self.node = self.bot.node
        self.node.name = "A\ue047S"

    def on(self, i):

        for _ in [1, 0]:
            getattr(
                self.bot,
                "on_" + ["jump", "bomb", "pickup", "punch"][i]
                + "_" + ["release", "press"][_]
            )()

    def move(self, x, z):

        self.bot.on_move_left_right(x)
        self.bot.on_move_up_down(z)

    def on_run(self, v):

        self.bot.on_run(v)


# --------------------------------------------------
# Ender AI
# --------------------------------------------------

class Ender(Bot):

    def __init__(self):

        players = [
            n for n in GN()
            if n.exists() and n.getnodetype() == "spaz"
        ]

        if players:
            pos = choice(players).position
        else:
            pos = (0, 0.1, 0)

        super().__init__(pos)

        self._think_timer = bs.Timer(
            0.15,
            bs.WeakCall(self._think),
            repeat=True
        )

    def _target(self):

        if not self.node.exists():
            return None

        my = self.node.position

        players = [
            n for n in GN()
            if n.exists() and n.getnodetype() == "spaz"
            and n is not self.node
        ]

        if not players:
            return None

        return min(players, key=lambda n: dist(my, n.position))

    def skill(self):

        self.on(3)
        tick(0.05, lambda: self.on(2))

    def _think(self):

        if not self.node.exists():
            return

        t = self._target()

        if not t:

            self.on_run(0)
            self.move(0, 0)
            return

        dx = t.position[0] - self.node.position[0]
        dz = t.position[2] - self.node.position[2]

        length = (dx**2 + dz**2) ** 0.5

        if length == 0:
            return

        dx /= length
        dz /= length

        self.on_run(1)
        self.move(dx, -dz)

        if dist(self.node.position, t.position) < 1.6:
            self.skill()


# --------------------------------------------------
# Server Bot Manager
# --------------------------------------------------

ender_bot = None


def check_players():

    global ender_bot

    activity = ga()

    if activity is None:
        return

    count = len(activity.players)

    if count <= 1:

        if ender_bot is None or not ender_bot.node.exists():

            print("Spawning Ender bot (low players)")

            with activity.context:
                ender_bot = Ender()

    else:

        if ender_bot and ender_bot.node.exists():

            print("Removing Ender bot")

            with activity.context:
                ender_bot.node.handlemessage(DieMessage())

            ender_bot = None


# --------------------------------------------------
# Plugin
# --------------------------------------------------

# ba_meta require api 9
# ba_meta export babase.Plugin

class EnderServerPlugin(Plugin):

    def __init__(self):

        print("Ender server bot loaded")

        self.timer = babase.AppTimer(
            5.0,
            check_players,
            repeat=True
        ) 
