# Released under the MIT License. See LICENSE for details.
#
"""Defines Actor(s)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence

DEFAULT_POWERUP_INTERVAL = 8.0


class _TouchedMessage:
    pass


class PowerupBoxFactory:

    _STORENAME = bs.storagename()

    def __init__(self) -> None:
        from bascenev1 import get_default_powerup_distribution

        shared = SharedObjects.get()
        self._lastpoweruptype: str | None = None

        self.mesh = bs.getmesh('powerup')
        self.mesh_simple = bs.getmesh('powerupSimple')

        self.tex_bomb = bs.gettexture('powerupBomb')
        self.tex_punch = bs.gettexture('powerupPunch')
        self.tex_ice_bombs = bs.gettexture('powerupIceBombs')
        self.tex_sticky_bombs = bs.gettexture('powerupStickyBombs')
        # ? removed shield texture
        self.tex_impact_bombs = bs.gettexture('powerupImpactBombs')
        self.tex_health = bs.gettexture('powerupHealth')
        self.tex_land_mines = bs.gettexture('powerupLandMines')
        self.tex_curse = bs.gettexture('powerupCurse')

        self.health_powerup_sound = bs.getsound('healthPowerup')
        self.powerup_sound = bs.getsound('powerup01')
        self.powerdown_sound = bs.getsound('powerdown01')
        self.drop_sound = bs.getsound('boxDrop')

        self.powerup_material = bs.Material()
        self.powerup_accept_material = bs.Material()

        self.powerup_material.add_actions(
            conditions=('they_have_material', self.powerup_accept_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', _TouchedMessage()),
            ),
        )

        self.powerup_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'collide', False),
        )

        self.powerup_material.add_actions(
            conditions=('they_have_material', shared.footing_material),
            actions=('impact_sound', self.drop_sound, 0.5, 0.1),
        )

        # ? remove shield from spawn
        self._powerupdist: list[str] = []
        for powerup, freq in get_default_powerup_distribution():
            if powerup == 'shield':
                continue
            for _ in range(int(freq)):
                self._powerupdist.append(powerup)

    def get_random_powerup_type(self, forcetype=None, excludetypes=None):
        if excludetypes is None:
            excludetypes = []
        if forcetype:
            ptype = forcetype
        else:
            if self._lastpoweruptype == 'curse':
                ptype = 'health'
            else:
                while True:
                    ptype = self._powerupdist[
                        random.randint(0, len(self._powerupdist) - 1)
                    ]
                    if ptype not in excludetypes:
                        break
        self._lastpoweruptype = ptype
        return ptype

    @classmethod
    def get(cls):
        activity = bs.getactivity()
        if activity is None:
            raise bs.ContextError('No current activity.')
        if cls._STORENAME not in activity.customdata:
            activity.customdata[cls._STORENAME] = PowerupBoxFactory()
        return activity.customdata[cls._STORENAME]


class PowerupBox(bs.Actor):

    poweruptype: str
    node: bs.Node

    def __init__(self,
                 position: Sequence[float] = (0.0, 1.0, 0.0),
                 poweruptype: str = 'triple_bombs',
                 expire: bool = True):

        super().__init__()
        shared = SharedObjects.get()
        factory = PowerupBoxFactory.get()

        self.poweruptype = poweruptype
        self._powersgiven = False

        if poweruptype == 'triple_bombs':
            tex = factory.tex_bomb
        elif poweruptype == 'punch':
            tex = factory.tex_punch
        elif poweruptype == 'ice_bombs':
            tex = factory.tex_ice_bombs
        elif poweruptype == 'impact_bombs':
            tex = factory.tex_impact_bombs
        elif poweruptype == 'land_mines':
            tex = factory.tex_land_mines
        elif poweruptype == 'sticky_bombs':
            tex = factory.tex_sticky_bombs
        elif poweruptype == 'health':
            tex = factory.tex_health
        elif poweruptype == 'curse':
            tex = factory.tex_curse
        else:
            raise ValueError('invalid poweruptype: ' + str(poweruptype))

        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'position': position,
                'mesh': factory.mesh,
                'light_mesh': factory.mesh_simple,
                'shadow_size': 0.5,
                'color_texture': tex,
                'reflection': 'powerup',
                'reflection_scale': [1.0],
                'materials': (factory.powerup_material, shared.object_material),
            },
        )

        # ?? NAME
        m = bs.newnode('math', owner=self.node,
                       attrs={'input1': (0, 0.6, 0), 'operation': 'add'})
        self.node.connectattr('position', m, 'input2')

        name_txt = bs.newnode('text', owner=self.node, attrs={
            'text': poweruptype.upper(),
            'in_world': True,
            'scale': 0.01,
            'color': (1, 1, 1),
            'h_align': 'center'
        })
        m.connectattr('output', name_txt, 'position')

        # ?? TIMER
        m2 = bs.newnode('math', owner=self.node,
                        attrs={'input1': (0, 0.9, 0), 'operation': 'add'})
        self.node.connectattr('position', m2, 'input2')

        timer_txt = bs.newnode('text', owner=self.node, attrs={
            'text': '8',
            'in_world': True,
            'scale': 0.012,
            'h_align': 'center'
        })
        m2.connectattr('output', timer_txt, 'position')

        def tick(t):
            if not timer_txt.exists():
                return
            timer_txt.text = str(t)

            if t >= 5:
                timer_txt.color = (0, 1, 0)
            elif t >= 3:
                timer_txt.color = (1, 1, 0)
            else:
                timer_txt.color = (1, 0, 0)

        for i in range(8):
            bs.timer(i, lambda i=i: tick(8 - i))

        # animate
        curve = bs.animate(self.node, 'mesh_scale', {0: 0, 0.14: 1.6, 0.2: 1})
        bs.timer(0.2, curve.delete)

        if expire:
            bs.timer(5.5, bs.WeakCall(self._start_flashing))
            bs.timer(7.0, bs.WeakCall(self.handlemessage, bs.DieMessage()))

    def _start_flashing(self):
        if self.node:
            self.node.flashing = True

    @override
    def handlemessage(self, msg: Any):

        if isinstance(msg, bs.PowerupAcceptMessage):
            factory = PowerupBoxFactory.get()

            if self.poweruptype == 'health':
                factory.health_powerup_sound.play(
                    3, position=self.node.position
                )

            factory.powerup_sound.play(3, position=self.node.position)
            self._powersgiven = True
            self.handlemessage(bs.DieMessage())

        elif isinstance(msg, _TouchedMessage):
            if not self._powersgiven:
                node = bs.getcollision().opposingnode
                node.handlemessage(
                    bs.PowerupMessage(self.poweruptype,
                                      sourcenode=self.node)
                )

        elif isinstance(msg, bs.DieMessage):
            if self.node:
                bs.animate(self.node, 'mesh_scale', {0: 1, 0.1: 0})
                bs.timer(0.1, self.node.delete)

        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())

        elif isinstance(msg, bs.HitMessage):
            if msg.hit_type != 'punch':
                self.handlemessage(bs.DieMessage())
        else:
            return super().handlemessage(msg)

        return None