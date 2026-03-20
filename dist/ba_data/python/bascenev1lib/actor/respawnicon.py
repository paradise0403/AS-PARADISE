# Released under the MIT License. See LICENSE for details.
"""Implements a BCS-styled respawn icon actor for API 9."""

from __future__ import annotations
import weakref
import bascenev1 as bs

class RespawnIcon:
    """An icon with a countdown and a spinning ring (BCS Style)."""

    _MASKTEXSTORENAME = bs.storagename('masktex')
    _ICONSSTORENAME = bs.storagename('icons')

    def __init__(self, player: bs.Player, respawn_time: float):
        self._visible = True
        self._dots_epic_only = False

        on_right, offs_extra, respawn_icons = self._get_context(player)

        mask_tex = player.team.customdata.get(self._MASKTEXSTORENAME)
        if mask_tex is None:
            mask_tex = bs.gettexture('characterIconMask')
            player.team.customdata[self._MASKTEXSTORENAME] = mask_tex
        
        # Find unused slot
        index = 0
        while (index in respawn_icons and respawn_icons[index]() is not None 
               and respawn_icons[index]().visible):
            index += 1
        respawn_icons[index] = weakref.ref(self)

        offs = offs_extra + index * -53
        icon = player.get_icon()
        h_offs = -10
        ipos = (-40 - h_offs if on_right else 40 + h_offs, -180 + offs)

        # 1. THE MAIN PLAYER HEAD
        self._image = bs.NodeActor(
            bs.newnode('image', attrs={
                'texture': icon['texture'],
                'tint_texture': icon['tint_texture'],
                'tint_color': icon['tint_color'],
                'tint2_color': icon['tint2_color'],
                'mask_texture': mask_tex,
                'position': ipos,
                'scale': (32, 32),
                'opacity': 0.7,
                'absolute_scale': True,
                'attach': 'topRight' if on_right else 'topLeft',
            })
        )

        # 2. THE SPINNING BLUE RING (p_image)
        # We use 'replayIcon' just like your API 7/1.4 snippet
        r_pos = (-75 - h_offs if on_right else 75 + h_offs, -180 + offs)
        self.p_image = bs.NodeActor(
            bs.newnode('image', attrs={
                'texture': bs.gettexture('replayIcon'),
                'tint_color': (0, 0, 1), # Pure Blue
                'position': r_pos,
                'scale': (32, 32),
                'opacity': 0.65,
                'absolute_scale': True,
                'attach': 'topRight' if on_right else 'topLeft',
            })
        )
        
        # Rotation Animation (The "Spin")
        bs.animate(self.p_image.node, 'rotate', {0: 0, 1.0: 360}, loop=True)

        # 3. PLAYER NAME
        npos = (-40 - h_offs if on_right else 40 + h_offs, -205 + 49 + offs)
        self._name = bs.NodeActor(
            bs.newnode('text', attrs={
                'v_attach': 'top',
                'h_attach': 'right' if on_right else 'left',
                'text': bs.Lstr(value=player.getname()),
                'maxwidth': 100,
                'h_align': 'center',
                'v_align': 'center',
                'shadow': 1.0,
                'flatness': 1.0,
                'color': bs.safecolor(icon['tint_color']),
                'scale': 0.5,
                'position': npos,
            })
        )

        # 4. TIMER TEXT
        tpos = (-60 - h_offs if on_right else 60 + h_offs, -193 + offs)
        self._text = bs.NodeActor(
            bs.newnode('text', attrs={
                'position': tpos,
                'h_attach': 'right' if on_right else 'left',
                'h_align': 'right' if on_right else 'left',
                'scale': 0.9,
                'v_attach': 'top',
                'color': (1,1,1),
                'text': '',
            })
        )

        self._respawn_time = bs.time() + respawn_time
        self._update()
        self._timer = bs.Timer(1.0, bs.WeakCall(self._update), repeat=True)

    @property
    def visible(self) -> bool:
        return self._visible

    def _get_context(self, player: bs.Player):
        # ... (Keep your existing _get_context logic here) ...
        activity = bs.getactivity()
        on_right = False
        if isinstance(activity.session, bs.DualTeamSession):
            on_right = player.team.id % 2 == 1
            icons = player.team.customdata.setdefault(self._ICONSSTORENAME, {})
            offs_extra = -20
        else:
            icons = activity.customdata.setdefault(self._ICONSSTORENAME, {})
            offs_extra = -150 if isinstance(activity.session, bs.FreeForAllSession) else -20
        return on_right, offs_extra, icons

    def _update(self) -> None:
        remaining = int(round(self._respawn_time - bs.time()))
        if remaining > 0:
            if self._text.node:
                self._text.node.text = str(remaining)
        else:
            self._visible = False
            self._image = self._text = self.p_image = self._timer = self._name = None
 