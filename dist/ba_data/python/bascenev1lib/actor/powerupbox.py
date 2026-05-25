# Released under the MIT License. See LICENSE for details.
#
"""Defines Actor(s)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects
import setting

settings = setting.get_settings_data()

if TYPE_CHECKING:
    from typing import Any, Sequence

DEFAULT_POWERUP_INTERVAL = 8.0


class _TouchedMessage:
    pass


class PowerupBoxFactory:

    _STORENAME = bs.storagename()

    def __init__(self) -> None:

        shared = SharedObjects.get()
        self._lastpoweruptype: str | None = None

        self.mesh = bs.getmesh('powerup')
        self.mesh_simple = bs.getmesh('powerupSimple')

        self.tex_bomb = bs.gettexture('powerupBomb')
        self.tex_punch = bs.gettexture('powerupPunch')
        self.tex_ice_bombs = bs.gettexture('powerupIceBombs')
        self.tex_sticky_bombs = bs.gettexture('powerupStickyBombs')
        self.tex_impact_bombs = bs.gettexture('powerupImpactBombs')
        self.tex_health = bs.gettexture('powerupHealth')
        self.tex_land_mines = bs.gettexture('powerupLandMines')
        self.tex_curse = bs.gettexture('powerupCurse')
        self.tex_shield = bs.gettexture('powerupShield')

        # CUSTOM
        self.tex_teleport_bomb = bs.gettexture('aliColorMask')
        self.tex_headache = bs.gettexture('achievementEmpty')
        self.tex_impact_curse = bs.gettexture('powerupCurse')
        self.tex_ice_impact = bs.gettexture('bombColorIce')
        self.tex_ice_mine = bs.gettexture('egg2')

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

        self._powerupdist: list[str] = []

        key_map = {
            'triple_bombs': 'triple_bombs',
            'ice_bombs': 'ice_bombs',
            'impact_bombs': 'impact_bombs',
            'sticky_bombs': 'sticky_bombs',
            'land_mines': 'land_mines',
            'punch': 'punch',
            'shield': 'shield',
            'health': 'health',
            'curse': 'curse'
        }

        qty = settings.get('powerupDistribution', {})

        for powerup, setting_name in key_map.items():
            amount = int(qty.get(setting_name, 0))
            for _ in range(amount):
                self._powerupdist.append(powerup)

        custom = settings.get('customPowerups', {})

        if custom.get('enable', True):
            for pwp in [
                'teleport_bomb',
                'headache',
                'impact_curse',
                'ice_impact',
                'ice_mine'
            ]:
                amount = int(custom.get(pwp, 0))
                for _ in range(amount):
                    self._powerupdist.append(pwp)

        if not self._powerupdist:
            self._powerupdist.append('health')
 
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
                        random.randint(
                            0,
                            len(self._powerupdist) - 1
                        )
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

    def __init__(
        self,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        poweruptype: str = 'triple_bombs',
        expire: bool = True,
    ):

        super().__init__()

        shared = SharedObjects.get()
        factory = PowerupBoxFactory.get()

        self.poweruptype = poweruptype
        self._powersgiven = False

        if poweruptype == 'triple_bombs':
            tex = factory.tex_bomb
            display_name = 'TRIPLE_BOMBS'

        elif poweruptype == 'punch':
            tex = factory.tex_punch
            display_name = 'PUNCH'

        elif poweruptype == 'ice_bombs':
            tex = factory.tex_ice_bombs
            display_name = 'ICE_BOMBS'

        elif poweruptype == 'impact_bombs':
            tex = factory.tex_impact_bombs
            display_name = 'IMPACT_BOMBS'

        elif poweruptype == 'land_mines':
            tex = factory.tex_land_mines
            display_name = 'LAND_MINES'

        elif poweruptype == 'sticky_bombs':
            tex = factory.tex_sticky_bombs
            display_name = 'STICKY_BOMBS'

        elif poweruptype == 'health':
            tex = factory.tex_health
            display_name = 'HEALTH'

        elif poweruptype == 'curse':
            tex = factory.tex_curse
            display_name = 'CURSE'

        elif poweruptype == 'shield':
            tex = factory.tex_shield
            display_name = 'SHIELD'

        elif poweruptype == 'teleport_bomb':
            tex = factory.tex_teleport_bomb
            display_name = 'TELEPORT_BOMB'

        elif poweruptype == 'impact_curse':
            tex = factory.tex_impact_curse
            display_name = 'IMPACT_CURSE'

        elif poweruptype == 'ice_impact':
            tex = factory.tex_ice_impact
            display_name = 'ICE_IMPACT'

        elif poweruptype == 'ice_mine':
            tex = factory.tex_ice_mine
            display_name = 'ICE_MINE'

        elif poweruptype == 'headache':
            tex = factory.tex_headache
            display_name = 'HEADACHE-BOMBS'

        else:
            raise ValueError(
                'invalid poweruptype: ' + str(poweruptype)
            )

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
                'materials': (
                    factory.powerup_material,
                    shared.object_material,
                ),
            },
        )

        # NAME TEXT
        m = bs.newnode(
            'math',
            owner=self.node,
            attrs={
                'input1': (0, 0.6, 0),
                'operation': 'add'
            },
        )

        self.node.connectattr('position', m, 'input2')

        name_txt = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': display_name,
                'in_world': True,
                'scale': 0.01,
                'color': (1, 1, 1),
                'h_align': 'center',
            },
        )

        m.connectattr('output', name_txt, 'position')

        # TIMER TEXT
        m2 = bs.newnode(
            'math',
            owner=self.node,
            attrs={
                'input1': (0, 0.9, 0),
                'operation': 'add'
            },
        )

        self.node.connectattr('position', m2, 'input2')

        timer_txt = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': '8',
                'in_world': True,
                'scale': 0.012,
                'h_align': 'center',
            },
        )

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

        # SPAWN ANIMATION
        curve = bs.animate(
            self.node,
            'mesh_scale',
            {0: 0, 0.14: 1.6, 0.2: 1},
        )

        bs.timer(0.2, curve.delete)

        if expire:

            bs.timer(
                5.5,
                bs.WeakCall(self._start_flashing)
            )

            bs.timer(
                7.0,
                bs.WeakCall(
                    self.handlemessage,
                    bs.DieMessage()
                )
            )

    def _start_flashing(self):

        if self.node:
            self.node.flashing = True

    # TELEPORT
    def _give_teleport_bomb(self, node):

        try:

            spaz = node.getdelegate(object)

            if spaz is None:
                return False

            old_count = getattr(
                spaz,
                '_teleport_bomb_count',
                0
            )

            spaz._teleport_bomb_count = old_count + 1

            bs.broadcastmessage(
                'You got 1 Teleport Bomb!',
                color=(1, 0.3, 1),
                transient=True,
            )

            return True

        except Exception as e:
            print('Teleport bomb error:', e)
            return False

    # HEADACHE
    def _give_headache(self, node):

        try:
            spaz = node.getdelegate(object)

            if spaz is None:
                return False

            old_count = getattr(spaz, '_headache_count', 0)

            # GIVE 3
            spaz._headache_count = old_count + 3

            bs.broadcastmessage(
                'You got 3 HEADACHE-Bombs!',
                color=(1, 0.2, 0.8),
                transient=True,
            )

            return True

        except Exception as e:
            print('Headache powerup error:', e)
            return False

    # CUSTOM BOMBS GIVE SYSTEM
    def _give_custom_bomb(self, node, attr, amount, text, color):

        try:
            spaz = node.getdelegate(object)

            if spaz is None:
                return False

            old = getattr(spaz, attr, 0)
            setattr(spaz, attr, old + amount)

            bs.broadcastmessage(
                text,
                color=color,
                transient=True,
            )

            return True

        except Exception as e:
            print('custom bomb give error:', e)
            return False

    @override
    def handlemessage(self, msg: Any):

        if isinstance(msg, bs.PowerupAcceptMessage):

            factory = PowerupBoxFactory.get()

            if self.poweruptype == 'health':

                factory.health_powerup_sound.play(
                    3,
                    position=self.node.position,
                )

            factory.powerup_sound.play(
                3,
                position=self.node.position
            )

            self._powersgiven = True

            self.handlemessage(bs.DieMessage())

        elif isinstance(msg, _TouchedMessage):

            if not self._powersgiven:

                node = bs.getcollision().opposingnode

                # TELEPORT
                if self.poweruptype == 'teleport_bomb':

                    ok = self._give_teleport_bomb(node)

                    if ok:

                        self._powersgiven = True

                        factory = PowerupBoxFactory.get()

                        factory.powerup_sound.play(
                            3,
                            position=self.node.position,
                        )

                        self.handlemessage(bs.DieMessage())

                    return None

                # HEADACHE
                if self.poweruptype == 'headache':

                    ok = self._give_headache(node)

                    if ok:

                        self._powersgiven = True

                        factory = PowerupBoxFactory.get()

                        factory.powerup_sound.play(
                            3,
                            position=self.node.position,
                        )

                        self.handlemessage(bs.DieMessage())

                    return None

                # IMPACT CURSE
                if self.poweruptype == 'impact_curse':

                    ok = self._give_custom_bomb(
                        node,
                        '_impact_curse_count',
                        3,
                        'You got 3 Impact Curse Bombs!',
                        (0.8, 0.1, 1),
                    )

                    if ok:
                        self._powersgiven = True

                        PowerupBoxFactory.get().powerup_sound.play(
                            3,
                            position=self.node.position,
                        )

                        self.handlemessage(bs.DieMessage())

                    return None

                # ICE IMPACT
                if self.poweruptype == 'ice_impact':

                    ok = self._give_custom_bomb(
                        node,
                        '_ice_impact_count',
                        3,
                        'You got 3 Ice Impact Bombs!',
                        (0.2, 0.8, 1),
                    )

                    if ok:
                        self._powersgiven = True

                        PowerupBoxFactory.get().powerup_sound.play(
                            3,
                            position=self.node.position,
                        )

                        self.handlemessage(bs.DieMessage())

                    return None

                # ICE MINE
                if self.poweruptype == 'ice_mine':

                    ok = self._give_custom_bomb(
                        node,
                        '_ice_mine_count',
                        3,
                        'You got 3 Ice Mines!',
                        (0.1, 0.6, 1),
                    )

                    if ok:
                        self._powersgiven = True

                        PowerupBoxFactory.get().powerup_sound.play(
                            3,
                            position=self.node.position,
                        )

                        self.handlemessage(bs.DieMessage())

                    return None 

                # NORMAL POWERUPS
                node.handlemessage(
                    bs.PowerupMessage(
                        self.poweruptype,
                        sourcenode=self.node,
                    )
                )

        elif isinstance(msg, bs.DieMessage):

            if self.node:

                bs.animate(
                    self.node,
                    'mesh_scale',
                    {0: 1, 0.1: 0}
                )

                bs.timer(0.1, self.node.delete)

        elif isinstance(msg, bs.OutOfBoundsMessage):

            self.handlemessage(bs.DieMessage())

        elif isinstance(msg, bs.HitMessage):

            if msg.hit_type != 'punch':
                self.handlemessage(bs.DieMessage())

        else:
            return super().handlemessage(msg)

        return None 
