# Released under the MIT License. See LICENSE for details.
"""PowerupBox API 9: The Ultimate Bridge (Customs + Defaults + BA-EX)"""

from __future__ import annotations
import os
import json
import random
from typing import TYPE_CHECKING, override

import babase
import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence

# --- PATHS ---
try:
    storage_dir = babase.app.env.python_directory_storage
    COIN_DATA_PATH = os.path.join(storage_dir, 'coin_data.json')
except Exception:
    COIN_DATA_PATH = './coin_data.json'

DEFAULT_POWERUP_INTERVAL = 8.0

class _TouchedMessage: pass
class PowerupAcceptMessage: pass

class PowerupBoxFactory:
    _STORENAME = bs.storagename()

    def __init__(self) -> None:
        from bascenev1 import get_default_powerup_distribution
        shared = SharedObjects.get()
        
        self.mesh = bs.getmesh('powerup')
        self.powerup_sound = bs.getsound('powerup01')
        self.cash_sound = bs.getsound('cashRegister')
        self.error_sound = bs.getsound('error')

        # Custom Textures
        self.tex_coin = bs.gettexture('coin')
        self.tex_ice_impact = bs.gettexture('bombColorIce') 
        self.tex_fake = bs.gettexture('buttonJump') 

        # Materials
        self.powerup_material = bs.Material()
        self.powerup_accept_material = bs.Material() 
        
        self.powerup_material.add_actions(actions=(
            ('modify_part_collision', 'friction', 0.5),
            ('message', 'our_node', 'at_connect', _TouchedMessage()),
        ))

        # --- THE BRIDGE DISTRIBUTION ---
        self._powerupdist: list[str] = []
        
        # 1. Default PWPs (Punch, Triple, etc.)
        for p, freq in get_default_powerup_distribution():
            for _ in range(int(freq)): self._powerupdist.append(p)
        
        # 2. Your Custom PWPs
        self._powerupdist.extend(['coin_box']*3 + ['ice_impact']*2 + ['fake_box']*2)
        
        # 3. BA-EX Items (Adding to the same spawn pool)
        ex_items = [
            'nitrogen_bomb', 'Xfactor_bomb', 's.m.b_bomb', 'T784_bomb', 
            'stun_bomb', 'supplies', 'gloo_wall_bomb', 'teleport_bomb', 
            'cosmic_bomb', 'electro-bombs', 'blackhole_bomb', 
            'superhuman_healing', 'super_shield', 'attraction_bomb'
        ]
        self._powerupdist.extend(ex_items * 2)

    def get_random_powerup_type(self) -> str:
        return random.choice(self._powerupdist)

    @classmethod
    def get(cls) -> PowerupBoxFactory:
        activity = bs.getactivity()
        if cls._STORENAME not in activity.customdata:
            activity.customdata[cls._STORENAME] = PowerupBoxFactory()
        return activity.customdata[cls._STORENAME]

class PowerupBox(bs.Actor):
    def __init__(self, position: Sequence[float] = (0.0, 1.0, 0.0), 
                 poweruptype: str | None = None, expire: bool = True):
        super().__init__()
        factory = PowerupBoxFactory.get()
        shared = SharedObjects.get()
        self.poweruptype = poweruptype if poweruptype else factory.get_random_powerup_type()
        self._powersgiven = False

        t = bs.gettexture
        m = bs.getmesh
        
        # Visual Mapping for EVERYTHING
        v_map = {
            'coin_box': (t('coin'), m('powerup'), 1.0),
            'ice_impact': (t('bombColorIce'), m('powerup'), 1.0),
            'fake_box': (t('tickets'), m('powerup'), 1.0),
            'nitrogen_bomb': (t('bombColorIce'), m('shield'), 0.25),
            'Xfactor_bomb': (t('textClearButton'), m('powerup'), 1.0),
            's.m.b_bomb': (t('touchArrowsActions'), m('powerup'), 1.0),
            'T784_bomb': (t('star'), m('powerup'), 1.0),
            'supplies': (t('logoEaster'), m('powerup'), 1.0),
            'stun_bomb': (t('ouyaUButton'), m('powerup'), 1.0),
            'gloo_wall_bomb': (t('bombColorIce'), m('powerup'), 1.0),
            'teleport_bomb': (t('rightButton'), m('powerup'), 1.0),
            'cosmic_bomb': (t('achievementFootballShutout'), m('powerup'), 1.0),
            'electro-bombs': (t('levelIcon'), m('powerup'), 1.0),
            'blackhole_bomb': (t('replayIcon'), m('powerup'), 1.0),
            'superhuman_healing': (t('achievementStayinAlive'), m('powerup'), 1.0),
            'super_shield': (t('ouyaOButton'), m('powerup'), 1.0),
            'attraction_bomb': (t('backIcon'), m('powerup'), 1.0),
        }

        tex, mesh, scale = v_map.get(self.poweruptype, (t('powerupBomb'), m('powerup'), 1.0))

        self.node = bs.newnode('prop', delegate=self, attrs={
            'body': 'box', 'position': position, 'mesh': mesh,
            'color_texture': tex, 'reflection': 'powerup',
            'mesh_scale': scale,
            'materials': (factory.powerup_material, shared.object_material, shared.footing_material)
        })

        if expire:
            bs.timer(DEFAULT_POWERUP_INTERVAL - 1.0, bs.WeakCall(self._start_flashing))
            bs.timer(DEFAULT_POWERUP_INTERVAL, bs.WeakCall(self.handlemessage, bs.DieMessage()))

    def _start_flashing(self) -> None:
        if self.node: self.node.flashing = True

    def _handle_bridge_action(self, spaz: Any) -> None:
        """Central hub to execute effects."""
        factory = PowerupBoxFactory.get()
        
        # --- CUSTOMS ---
        if self.poweruptype == 'coin_box':
            player = spaz.getplayer(bs.Player, True)
            if player:
                acc_id = player.sessionplayer.get_v1_account_id()
                data = {}
                if os.path.exists(COIN_DATA_PATH):
                    with open(COIN_DATA_PATH, 'r') as f: data = json.load(f)
                stats = data.get(acc_id, {'coins': 0, 'name': player.getname(full=True)})
                stats['coins'] += 50
                data[acc_id] = stats
                with open(COIN_DATA_PATH, 'w') as f: json.dump(data, f, indent=4)
                factory.cash_sound.play(position=self.node.position)
                bs.broadcastmessage(f"\ue01d {player.getname()}: +50 \ue01d", color=(0.2, 1, 0.2))

        elif self.poweruptype == 'ice_impact':
            spaz.bomb_type = 'ice_impact'
            bs.broadcastmessage("\ue045 ICE-IMPACT EQUIPPED!", color=(0.4, 0.8, 1.0))

        elif self.poweruptype == 'fake_box':
            factory.error_sound.play(position=self.node.position)
            bs.broadcastmessage("\ue00d NO PWP FOR U \ue00d", color=(1, 0, 0))

        # --- BA-EX BRIDGE ---
        else:
            # Ye seedha baExPowerups plugin ke function ko call marega
            # Plugin must be in mods folder!
            if hasattr(spaz, 'ex_powerup_call'):
                spaz.ex_powerup_call(self.poweruptype)

        self.handlemessage(PowerupAcceptMessage())

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, (bs.PowerupAcceptMessage, PowerupAcceptMessage)):
            if self.node:
                PowerupBoxFactory.get().powerup_sound.play(position=self.node.position)
                self._powersgiven = True
                self.handlemessage(bs.DieMessage())
        elif isinstance(msg, _TouchedMessage):
            if not self._powersgiven and self.node:
                try:
                    from bascenev1lib.actor.spaz import Spaz
                    node = bs.getcollision().opposingnode
                    spaz = node.getdelegate(Spaz, False)
                    if spaz and spaz.is_alive():
                        # Everything that is NOT a default PWP
                        special = [
                            'coin_box', 'ice_impact', 'fake_box', 'nitrogen_bomb', 
                            'T784_bomb', 'super_shield', 'blackhole_bomb', 'Xfactor_bomb',
                            'supplies', 'teleport_bomb', 'cosmic_bomb', 'electro-bombs',
                            'stun_bomb', 'gloo_wall_bomb', 'superhuman_healing', 'attraction_bomb', 's.m.b_bomb'
                        ]
                        if self.poweruptype in special:
                            self._handle_bridge_action(spaz)
                        else:
                            # Standard bomb logic (Triple bombs, etc.)
                            node.handlemessage(bs.PowerupMessage(self.poweruptype, sourcenode=self.node))
                            self.handlemessage(bs.PowerupAcceptMessage())
                except Exception: pass
        elif isinstance(msg, bs.DieMessage):
            if self.node: self.node.delete()
        else: super().handlemessage(msg)