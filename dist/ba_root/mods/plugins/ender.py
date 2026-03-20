# Ender Server Bot
# Auto spawn when players <= 2

from bascenev1lib.actor.spaz import Spaz
from babase import Plugin, get_string_height as gsh, get_string_width as gsw
import babase
import bascenev1 as bs

from bascenev1 import (
    get_foreground_host_activity as ga,
    getnodes as GN,
    timer as tick,
    Timer as tock,
    StandMessage,
    DieMessage,
    newnode,
    animate,
    time
)

from math import dist
from random import choice, random


# -------------------------------------------------
# Base Bot
# -------------------------------------------------

class Bot:

    def __init__(self, position=(0,0,0), color=(0,0,0), highlight=(0,0,0),
                 character="Agent Johnson"):

        self.bot = Spaz(
            color=color,
            highlight=highlight,
            character=character
        )

        self.bot.handlemessage(StandMessage(position,0))
        self.node = self.bot.node
        self.node.name = self.__class__.__name__

        self.bub = Bubble(self.node)

    def on(self,i):
        for _ in [1,0]:
            getattr(
                self.bot,
                "on_"+["jump","bomb","pickup","punch"][i]+"_"+["release","press"][_]
            )()

    def move(self,x,z):
        self.bot.on_move_left_right(x)
        self.bot.on_move_up_down(z)

    def on_run(self,v):
        self.bot.on_run(v)


# -------------------------------------------------
# Speech Bubble
# -------------------------------------------------

class Bubble:

    def __init__(self,head,res="\u2588"):

        self.head=head
        self.res=res
        self.text=""
        self.kids=[]

        self.node=newnode(
            "math",
            delegate=self,
            owner=head,
            attrs={"input1":(0,0,0),"operation":"add"}
        )

        head.connectattr("position",self.node,"input2")

        for _ in [0,0.85]:
            n=TEX(self.node,color=(_,_,_))
            self.kids.append(n)
            self.node.connectattr("output",n,"position")

    def push(self,text=""):

        if not text:
            self.anim(1,0)
            self.text=""
            return

        ls=len(text.splitlines())
        self.node.input1=(0,1.3+0.32*ls,0)

        bg,t=self.kids
        bg.text=(round(GSW(text)/GSW(self.res)+1)*self.res+"\n")*ls
        t.text=text

        if not self.text:
            self.anim(0,1)

        self.text=text
        tock(3.5,self.push)

    def anim(self,p1,p2):
        try:
            [animate(_,"opacity",{0:p1,0.2:p2}) for _ in self.kids]
        except:
            pass


# -------------------------------------------------
# Ender AI
# -------------------------------------------------

class Ender(Bot):

    def __init__(self):

        players=[n for n in GN() if n.exists() and n.getnodetype()=="spaz"]

        if players:
            pos=choice(players).position
        else:
            pos=(0,0.1,0)

        super().__init__(pos)

        self.last_skill=0
        self.last_speech=0

        self._think_timer=tock(0.15,self._think,repeat=True)
        self._protect_timer=tock(0.01,self._protect,repeat=True)

        self.pursuit=[
            "Come here",
            "You can't escape",
            "I'm coming for you"
        ]

        self.idle=[
            "Anyone here?",
            "Boring...",
            "Where did everyone go?"
        ]

    def _say(self,msg):

        now=time()

        if now-self.last_speech>1.5:
            self.bub.push(msg)
            self.last_speech=now

    def _target(self):

        if not self.node.exists():
            return None

        my=self.node.position

        players=[n for n in GN()
                 if n.exists() and n.getnodetype()=="spaz" and n is not self.node]

        if not players:
            return None

        return min(players,key=lambda n:dist(my,n.position))

    def skill(self):
        self.on(3)
        tick(0.05,lambda:self.on(2))

    def _protect(self):

        if not self.node.exists():
            return

        t=self._target()

        if not t:
            return

        d=dist(self.node.position,t.position)

        if d<1.6:
            self.skill()

    def _think(self):

        if not self.node.exists():
            return

        t=self._target()

        if not t:

            if random()<0.02:
                self._say(choice(self.idle))

            self.on_run(0)
            self.move(0,0)
            return

        if random()<0.05:
            self._say(choice(self.pursuit))

        dx=t.position[0]-self.node.position[0]
        dz=t.position[2]-self.node.position[2]

        l=(dx**2+dz**2)**0.5

        if l==0:
            return

        dx/=l
        dz/=l

        self.on_run(1)
        self.move(dx,-dz)


# -------------------------------------------------
# Helpers
# -------------------------------------------------

GSW=lambda s:gsw(s,suppress_warning=True)
GSH=lambda s:gsh(s,suppress_warning=True)

TEX=lambda o,**k:newnode(
    "text",
    owner=o,
    attrs={
        "in_world":True,
        "scale":0.01,
        "flatness":1,
        "h_align":"center",
        **k
    }
)


# -------------------------------------------------
# SERVER AUTO SPAWN SYSTEM
# -------------------------------------------------

ender_bot=None

def check_players():

    global ender_bot

    activity=ga()

    if activity is None:
        return

    players=activity.players
    count=len(players)

    if count<=2:

        if ender_bot is None or not ender_bot.node.exists():
            print("Ender spawned (low players)")
            ender_bot=Ender()

    else:

        if ender_bot and ender_bot.node.exists():
            print("Ender removed (enough players)")
            ender_bot.node.handlemessage(DieMessage())
            ender_bot=None


def start_checker():
    bs.Timer(5.0,check_players,repeat=True)


# -------------------------------------------------
# Plugin
# -------------------------------------------------

# ba_meta require api 9
# ba_meta export babase.Plugin

class EnderServerPlugin(Plugin):

    def __init__(self):

        print("Ender server bot loaded")

        # delay start so activity exists
        babase.apptimer(5.0,start_checker) 