# ba_meta require api 8

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1lib.actor import bomb
from bascenev1lib.actor.bomb import BombFactory
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Sequence


def new_blast_init(
    self,
    position: Sequence[float] = (0.0, 1.0, 0.0),
    velocity: Sequence[float] = (0.0, 0.0, 0.0),
    blast_radius: float = 2.0,
    blast_type: str = "normal",
    source_player: bs.Player = None,
    hit_type: str = "explosion",
    hit_subtype: str = "normal",
):
    bs.Actor.__init__(self)

    shared = SharedObjects.get()
    factory = BombFactory.get()

    self.blast_type = blast_type
    self._source_player = source_player
    self.hit_type = hit_type
    self.hit_subtype = hit_subtype
    self.radius = blast_radius

    rmats = (factory.blast_material, shared.attack_material)
    self.node = bs.newnode(
        "region",
        delegate=self,
        attrs={
            "position": (position[0], position[1] - 0.1, position[2]),
            "scale": (self.radius, self.radius, self.radius),
            "type": "sphere",
            "materials": rmats,
        },
    )

    bs.timer(0.05, self.node.delete)

    #  Soft Lavender Explosion (no eye strain)
    explosion = bs.newnode(
        "explosion",
        attrs={
            "position": position,
            "velocity": velocity,
            "radius": self.radius,
            "big": (self.blast_type == "tnt"),
        },
    )
    explosion.color = (0.55, 0.4, 0.8)  # softer lavender

    bs.timer(1.0, explosion.delete)

    #  Pink-style smoke (soft feel)
    bs.emitfx(
        position=position,
        velocity=velocity,
        count=int(6.0 + random.random() * 6),
        emit_type="tendrils",
        tendril_type="smoke",
    )

    bs.emitfx(
        position=position,
        velocity=velocity,
        count=int(4.0 + random.random() * 4),
        emit_type="tendrils",
        tendril_type="thin_smoke",
    )

    bs.emitfx(
        position=position,
        emit_type="distortion",
        spread=2.0,
    )

    #  Soft lavender light (reduced brightness)
    light = bs.newnode(
        "light",
        attrs={
            "position": position,
            "volume_intensity_scale": 5.0,  # reduced brightness
            "color": (0.6, 0.4, 0.8),  # darker lavender
        },
    )

    bs.animate(
        light,
        "intensity",
        {
            0: 1.5,
            0.05: 0.1,
            0.1: 3.0,
            0.2: 1.5,
            0.5: 0.3,
            1.5: 0.0,
        },
    )

    bs.animate(
        light,
        "radius",
        {
            0: self.radius * 0.2,
            0.1: self.radius * 0.5,
            0.3: self.radius * 0.2,
            1.0: self.radius * 0.05,
        },
    )

    bs.timer(1.5, light.delete)

    #  Soft purple scorch (not random anymore)
    scorch = bs.newnode(
        "scorch",
        attrs={
            "position": position,
            "size": self.radius * 0.5,
            "big": (self.blast_type == "tnt"),
        },
    )
    scorch.color = (0.5, 0.3, 0.7)

    bs.animate(scorch, "presence", {3.0: 1, 10.0: 0})
    bs.timer(10.0, scorch.delete)

    #  Sounds
    lpos = light.position
    factory.random_explode_sound().play(position=lpos)
    factory.debris_fall_sound.play(position=lpos)

    bs.camerashake(intensity=2.5)


def enable() -> None:
    bomb.Blast.__init__ = new_blast_init 