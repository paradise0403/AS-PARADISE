# Released under the MIT License. See LICENSE for details.
#
"""Defines some lovely Actor(s)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable


# FIXME: Should make this an Actor.
class Spawner:
    """Utility for delayed spawning of objects.

    Creates a Circle Out effect and sends a Spawner.SpawnMessage to the
    current activity after a delay.
    """

    class SpawnMessage:
        """Spawn message sent by a Spawner after its delay has passed."""

        spawner: Spawner
        data: Any
        pt: Sequence[float]

        def __init__(
            self,
            spawner: Spawner,
            data: Any,
            pt: Sequence[float],
        ):
            self.spawner = spawner
            self.data = data
            self.pt = pt

    def __init__(
        self,
        *,
        data: Any = None,
        pt: Sequence[float] = (0, 0, 0),
        spawn_time: float = 1.0,
        send_spawn_message: bool = True,
        spawn_callback: Callable[[], Any] | None = None,
    ):
        self._spawn_callback = spawn_callback
        self._send_spawn_message = send_spawn_message
        self._spawner_sound = bs.getsound('swip2')
        self._data = data
        self._pt = pt
        
        # Base invisible light to track position
        self._light = bs.newnode(
            'light',
            attrs={
                'position': tuple(pt),
                'radius': 0.1,
                'color': (1, 1, 1),
                'intensity': 0.0,
            },
        )
        
        self._spawner_sound.play(position=self._light.position)
        bs.timer(spawn_time, self._spawn)

    def _spawn(self) -> None:
        """The actual spawn with the Circle Out effect."""
        pos = self._pt
        
        # --- ROBUST COLOR DETECTION ---
        # Default white/cyan lightning color
        eff_color = (0.8, 0.8, 1.0) 
        
        try:
            if isinstance(self._data, dict) and 'color' in self._data:
                eff_color = tuple(self._data['color'])[:3]
            elif hasattr(self._data, 'color'):
                eff_color = tuple(self._data.color)[:3]
            elif hasattr(self._data, 'get_color'):
                eff_color = tuple(self._data.get_color())[:3]
        except Exception:
            pass # Keep default if color extraction fails

        # --- CIRCLE OUT EFFECT ---
        # Locator node is used for 'circleOutline'
        ring = bs.newnode('locator', attrs={
            'shape': 'circleOutline',
            'position': (pos[0], pos[1] + 0.05, pos[2]),
            'color': eff_color,
            'opacity': 1.0,
            'draw_beauty': True,
            'additive': True,
        })

        # Animate Size (Array) and Opacity
        bs.animate_array(ring, 'size', 1, {0.0: [0.0], 0.4: [5.0]})
        bs.animate(ring, 'opacity', {0.0: 1.0, 0.4: 0.0})
        
        # Cleanup ring
        bs.timer(0.45, ring.delete)

        # Optional: Add a quick flash to make it look 'hit'
        flash = bs.newnode('light', attrs={
            'position': pos,
            'color': eff_color,
            'radius': 0.4,
            'intensity': 2.0
        })
        bs.animate(flash, 'intensity', {0: 2.0, 0.2: 0})
        bs.timer(0.2, flash.delete)

        # Cleanup original node and trigger spawn logic
        bs.timer(1.0, self._light.delete)
        if self._spawn_callback is not None:
            self._spawn_callback()
        if self._send_spawn_message:
            activity = bs.getactivity()
            if activity is not None:
                activity.handlemessage(
                    self.SpawnMessage(self, self._data, self._pt)
                )
 