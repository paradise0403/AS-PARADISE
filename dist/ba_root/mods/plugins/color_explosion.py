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
    """Instantiate with Purple Smoke (Circle Hidden)."""

    bs.Actor.__init__(self)

    shared = SharedObjects.get()
    factory = BombFactory.get()

    self.blast_type = blast_type
    self._source_player = source_player
    self.hit_type = hit_type
    self.hit_subtype = hit_subtype
    self.radius = blast_radius

    # Physics region (Hitbox)
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

    # Explosion node is needed for smoke color, but we make radius tiny to hide the circle
    explosion = bs.newnode(
        "explosion",
        attrs={
            "position": position,
            "velocity": velocity,
            "radius": 0.01,  # Tiny radius so purple circle isn't visible
            "big": (self.blast_type == "tnt"),
            "color": (0.6, 0.1, 1.0), # Smoke color: Purple
        },
    )
    bs.timer(1.0, explosion.delete)

    # --- SMOKE EFFECTS (Now Purple) ---
    if self.blast_type != "ice":
        bs.emitfx(
            position=position,
            velocity=velocity,
            count=int(3.0 + random.random() * 6), 
            emit_type="tendrils",
            tendril_type="thin_smoke",
        )
    bs.emitfx(
        position=position,
        velocity=velocity,
        count=int(8.0 + random.random() * 8), # Increased smoke density
        emit_type="tendrils",
        tendril_type="ice" if self.blast_type == "ice" else "smoke",
    )
    bs.emitfx(
        position=position,
        emit_type="distortion",
        spread=1.0 if self.blast_type == "tnt" else 2.0,
    )

    # --- SHRAPNEL & DEBRIS ---
    if self.blast_type == "ice":
        def emit() -> None:
            bs.emitfx(position=position, velocity=velocity, count=30, spread=2.0, scale=0.4, chunk_type="ice", emit_type="stickers")
        bs.timer(0.05, emit)
    elif self.blast_type == "sticky":
        def emit() -> None:
            bs.emitfx(position=position, velocity=velocity, count=int(4.0 + random.random() * 8), chunk_type="slime")
            bs.emitfx(position=position, velocity=velocity, count=20, chunk_type="spark", emit_type="stickers")
        bs.timer(0.05, emit)
    else:
        def emit() -> None:
            if self.blast_type != "tnt":
                bs.emitfx(position=position, velocity=velocity, count=int(4.0 + random.random() * 8), chunk_type="rock")
            bs.emitfx(position=position, velocity=velocity, count=30, scale=0.7, chunk_type="spark", emit_type="stickers")
            bs.emitfx(position=position, velocity=velocity, count=20, scale=0.8, spread=1.5, chunk_type="spark")
        bs.timer(0.05, emit)

    # --- SCORCH ---
    scorch = bs.newnode(
        "scorch",
        attrs={
            "position": position,
            "size": self.radius * 0.5,
            "big": (self.blast_type == "tnt"),
        },
    )
    scorch.color = (random.random(), random.random(), random.random())
    bs.animate(scorch, "presence", {3.000: 1, 13.000: 0})
    bs.timer(13.0, scorch.delete)

    # --- SOUNDS & CAMERA ---
    factory.random_explode_sound().play(position=position)
    bs.camerashake(intensity=5.0 if self.blast_type == "tnt" else 1.0)


def enable() -> None:
    bomb.Blast.__init__ = new_blast_init