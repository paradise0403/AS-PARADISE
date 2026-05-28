import functools
import random

import setting
from playersdata import pdata
from stats import mystats
from typing import Sequence

import babase
import bascenev1 as bs
import babase as ba
import math
import weakref
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.gameutils import SharedObjects
import bascenev1lib
from bascenev1lib.actor.playerspaz import *

_settings = setting.get_settings_data()

RANK_EFFECT_MAP = {
    1: ["surrounder"],
    2: ["fairydust", "shine"],
    3: ["sweat"],
    4: ["metal"],
    5: ["iceground"],
}

class SurroundBallFactory:
    def __init__(self):
        # Textures
        self.bonesTex = bs.gettexture("powerupCurse")
        self.bearTex = bs.gettexture("bearColor")
        self.aliTex = bs.gettexture("aliColor")
        self.b9000Tex = bs.gettexture("cyborgColor")
        self.frostyTex = bs.gettexture("frostyColor")
        self.cubeTex = bs.gettexture("crossOutMask")
        # Meshes (use getmesh instead of getmodel)
        self.bonesModel = bs.getmesh("bonesHead")
        self.bearModel = bs.getmesh("bearHead")
        self.aliModel = bs.getmesh("aliHead")
        self.b9000Model = bs.getmesh("cyborgHead")
        self.frostyModel = bs.getmesh("frostyHead")
        self.cubeModel = bs.getmesh("powerup")
        try:
            self.mikuModel = bs.getmesh("operaSingerHead")
            self.mikuTex = bs.gettexture("operaSingerColor")
        except Exception:
            ba.print_exception()
            self.mikuModel = self.bonesModel
            self.mikuTex = self.bonesTex

        # Material
        self.ballMaterial = bs.Material()
        self.impactSound = bs.getsound("impactMedium")
        self.ballMaterial.add_actions(
            actions=("modify_node_collision", "collide", False)
        )


class SurroundBall(bs.Actor):
    def __init__(self, spaz, shape="bones"):
        super().__init__()
        self.spazRef = weakref.ref(spaz)
        factory = self.getFactory()
        s_model, s_texture = {
            "bones": (factory.bonesModel, factory.bonesTex),
            "bear": (factory.bearModel, factory.bearTex),
            "ali": (factory.aliModel, factory.aliTex),
            "b9000": (factory.b9000Model, factory.b9000Tex),
            "miku": (factory.mikuModel, factory.mikuTex),
            "frosty": (factory.frostyModel, factory.frostyTex),
            "RedCube": (factory.cubeModel, factory.cubeTex)
        }.get(shape, (factory.bonesModel, factory.bonesTex))

        self.node = bs.newnode(
            "prop",
            attrs={
                "mesh": s_model,
                "body": "sphere",
                "color_texture": s_texture,
                "reflection": "soft",
                "mesh_scale": 0.5,
                "body_scale": 0.1,
                "density": 0.1,
                "reflection_scale": [0.15],
                "shadow_size": 0.6,
                "position": spaz.node.position,
                "velocity": (0, 0, 0),
                "materials": [SharedObjects.get().object_material, factory.ballMaterial]
            },
            delegate=self
        )

        self.surroundTimer = None
        self.surroundRadius = 1.0
        self.angleDelta = math.pi / 12.0
        self.curAngle = random.random() * math.pi * 2.0
        self.curHeight = 0.0
        self.curHeightDir = 1
        self.heightDelta = 0.2
        self.heightMax = 1.0
        self.heightMin = 0.1

        # Start movement timer
        self.initTimer(spaz.node.position)

    def getTargetPosition(self, spazPos):
        p = spazPos
        pt = (p[0] + self.surroundRadius * math.cos(self.curAngle),
              p[1] + self.curHeight,
              p[2] + self.surroundRadius * math.sin(self.curAngle))
        self.curAngle += self.angleDelta
        self.curHeight += self.heightDelta * self.curHeightDir
        if self.curHeight > self.heightMax or self.curHeight < self.heightMin:
            self.curHeightDir = -self.curHeightDir
        return pt

    def initTimer(self, p):
        self.node.position = self.getTargetPosition(p)
        # API 9: just use seconds, no TimeType/TimeFormat
        self.surroundTimer = bs.Timer(1/30.0, self.circleMove, repeat=True)

    def circleMove(self):
        spaz = self.spazRef()
        if spaz is None or not spaz.is_alive() or not spaz.node.exists():
            self.handlemessage(bs.DieMessage())
            return
        p = spaz.node.position
        pt = self.getTargetPosition(p)
        pn = self.node.position
        d = [pt[0] - pn[0], pt[1] - pn[1], pt[2] - pn[2]]
        speed = self.getMaxSpeedByDir(d)
        self.node.velocity = speed

    @staticmethod
    def getMaxSpeedByDir(direction):
        k = 7.0 / max((abs(x) for x in direction))
        return tuple(x * k for x in direction)

    def handlemessage(self, m):
        super().handlemessage(m)
        if isinstance(m, bs.DieMessage):
            if self.surroundTimer is not None:
                self.surroundTimer = None
            if self.node.exists():
                self.node.delete()
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())

    @classmethod
    def getFactory(cls):
        activity = bs.getactivity()
        if activity is None:
            raise Exception("No current activity")
        try:
            return activity._sharedSurroundBallFactory
        except Exception:
            f = activity._sharedSurroundBallFactory = SurroundBallFactory()
            return f

def effect(repeat_interval=0):
    def _activator(method):
        @functools.wraps(method)
        def _inner_activator(self, *args, **kwargs):
            def _caller():
                try:
                    method(self, *args, **kwargs)
                except:
                    if self is None or not self.is_alive() or not self.node.exists():
                        self._activations = []
                    else:
                        raise

            effect_activation = bs.Timer(repeat_interval, babase.Call(_caller),
                                         repeat=repeat_interval > 0)
            self._activations.append(effect_activation)

        return _inner_activator

    return _activator


def node(check_interval=0):
    def _activator(method):
        @functools.wraps(method)
        def _inner_activator(self):
            node = method(self)

            def _caller():
                if self is None or not self.is_alive() or not self.node.exists():
                    node.delete()
                    self._activations = []

            node_activation = bs.Timer(check_interval, babase.Call(_caller),
                                       repeat=check_interval > 0)
            try:
                self._activations.append(node_activation)
            except AttributeError:
                pass

        return _inner_activator

    return _activator


class NewPlayerSpaz(PlayerSpaz):
    def __init__(self,
                 player: bs.Player,
                 color: Sequence[float],
                 highlight: Sequence[float],
                 character: str,
                 powerups_expire: bool = True,
                 *args,
                 **kwargs):

        super().__init__(player=player,
                         color=color,
                         highlight=highlight,
                         character=character,
                         powerups_expire=powerups_expire,
                         *args,
                         **kwargs)
        self._activations = []
        self.effects = []

        babase._asyncio._asyncio_event_loop.create_task(self.set_effects())

    async def set_effects(self):
        try:
            account_id = self._player._sessionplayer.get_v1_account_id()
        except:
            return
        custom_effects = pdata.get_custom()['customeffects']

        if account_id in custom_effects:
            self.effects = [custom_effects[account_id]] if type(
                custom_effects[account_id]) is str else custom_effects[
                account_id]
        else:
            #  check if we have any effect for his rank.
            if _settings['enablestats']:
                stats = mystats.get_cached_stats()
                if account_id in stats and _settings['enableTop5effects']:
                    rank = stats[account_id]["rank"]
                    self.effects = RANK_EFFECT_MAP[
                        rank] if rank in RANK_EFFECT_MAP else []

        if len(self.effects) == 0:
            return

        self._effect_mappings = {
            "spark": self._add_spark,
            "sparkground": self._add_sparkground,
            "sweat": self._add_sweat,
            "sweatground": self._add_sweatground,
            "distortion": self._add_distortion,
            "glow": self._add_glow,
            "shine": self._add_shine,
            "highlightshine": self._add_highlightshine,
            "scorch": self._add_scorch,
            "ice": self._add_ice,
            "iceground": self._add_iceground,
            "slime": self._add_slime,
            "metal": self._add_metal,
            "splinter": self._add_splinter,
            "rainbow": self._add_rainbow,
            "fairydust": self._add_fairydust,
            "surrounder": self._add_surround,
            "fire":self._add_fire,
            "stars":self._add_stars,
            "new_rainbow":self._add_new_rainbow,
            "footprint": self._add_footprint,
            "chispitas": self._add_chispitas,
            "darkmagic": self._add_darkmagic,
            "colorfullspark": self._add_colorful_spark,
            "ring": self._add_aure,
            "brust": self._add_galactic_burst,
            "ringstars": self._add_star_ring,
            "noeffect": lambda: None,
        }

        for effect in self.effects:
            trigger = self._effect_mappings[
                effect] if effect in self._effect_mappings else lambda: None
            activity = self._activity()
            if activity:
                with activity.context:
                    trigger()

    @effect(repeat_interval=0.1)
    def _add_spark(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 10),
            scale=0.5,
            spread=0.2,
            chunk_type="spark",
        )

    def _add_surround(self):
         self.surround = SurroundBall(self, shape="bones")
        
    @effect(repeat_interval=0.1)
    def _add_sparkground(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 5),
            scale=0.2,
            spread=0.1,
            chunk_type="spark",
            emit_type="stickers",
        )

    @effect(repeat_interval=0.04)
    def _add_sweat(self):
        velocity = 4.0
        calculate_position = lambda \
            torso_position: torso_position - 0.25 + random.uniform(0, 0.5)
        calculate_velocity = lambda node_velocity, multiplier: random.uniform(
            -velocity, velocity) + node_velocity * multiplier
        position = tuple(calculate_position(coordinate)
                         for coordinate in self.node.torso_position)
        velocity = (
            calculate_velocity(self.node.velocity[0], 2),
            calculate_velocity(self.node.velocity[1], 4),
            calculate_velocity(self.node.velocity[2], 2),
        )
        bs.emitfx(
            position=position,
            velocity=velocity,
            count=10,
            scale=random.uniform(0.3, 1.4),
            spread=0.1,
            chunk_type="sweat",
        )

    @effect(repeat_interval=0.04)
    def _add_sweatground(self):
        velocity = 1.2
        calculate_position = lambda \
            torso_position: torso_position - 0.25 + random.uniform(0, 0.5)
        calculate_velocity = lambda node_velocity, multiplier: random.uniform(
            -velocity, velocity) + node_velocity * multiplier
        position = tuple(calculate_position(coordinate)
                         for coordinate in self.node.torso_position)
        velocity = (
            calculate_velocity(self.node.velocity[0], 2),
            calculate_velocity(self.node.velocity[1], 4),
            calculate_velocity(self.node.velocity[2], 2),
        )
        bs.emitfx(
            position=position,
            velocity=velocity,
            count=10,
            scale=random.uniform(0.1, 1.2),
            spread=0.1,
            chunk_type="sweat",
            emit_type="stickers",
        )

    @effect(repeat_interval=1.0)
    def _add_distortion(self):
        bs.emitfx(
            position=self.node.position,
            spread=1.0,
            emit_type="distortion"
        )
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 5),
            emit_type="tendrils",
            tendril_type="smoke",
        )

    @effect(repeat_interval=3.0)
    def _add_shine(self):
        shine_factor = 1.2
        dim_factor = 0.90

        default_color = self.node.color
        shiny_color = tuple(channel * shine_factor for channel in default_color)
        dimmy_color = tuple(channel * dim_factor for channel in default_color)
        animation = {
            0: default_color,
            1: dimmy_color,
            2: shiny_color,
            3: default_color,
        }
        bs.animate_array(self.node, "color", 3, animation)

    @effect(repeat_interval=9.0)
    def _add_highlightshine(self):
        shine_factor = 1.2
        dim_factor = 0.90

        default_highlight = self.node.highlight
        shiny_highlight = tuple(
            channel * shine_factor for channel in default_highlight)
        dimmy_highlight = tuple(
            channel * dim_factor for channel in default_highlight)
        animation = {
            0: default_highlight,
            3: dimmy_highlight,
            6: shiny_highlight,
            9: default_highlight,
        }
        bs.animate_array(self.node, "highlight", 3, animation)

    @effect(repeat_interval=2.0)
    def _add_rainbow(self):
        highlight = tuple(random.random() for _ in range(3))
        highlight = babase.safecolor(highlight)
        animation = {
            0: self.node.highlight,
            2: highlight,
        }
        bs.animate_array(self.node, "highlight", 3, animation)

    @node(check_interval=0.5)
    def _add_glow(self):
        glowing_light = bs.newnode(
            "light",
            attrs={
                "color": (1.0, 0.4, 0.5),
                "height_attenuated": False,
                "radius": 0.4}
        )
        self.node.connectattr("position", glowing_light, "position")
        bs.animate(
            glowing_light,
            "intensity",
            {0: 0.0, 1: 0.2, 2: 0.0},
            loop=True)
        return glowing_light

    @node(check_interval=0.5)
    def _add_scorch(self):
        scorcher = bs.newnode(
            "scorch",
            attrs={
                "position": self.node.position,
                "size": 1.00,
                "big": True}
        )
        self.node.connectattr("position", scorcher, "position")
        animation = {
            0: (1, 0, 0),
            1: (0, 1, 0),
            2: (1, 0, 1),
            3: (0, 1, 1),
            4: (1, 0, 0),
        }
        bs.animate_array(scorcher, "color", 3, animation, loop=True)
        return scorcher

    @effect(repeat_interval=0.5)
    def _add_ice(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(2, 8),
            scale=0.4,
            spread=0.2,
            chunk_type="ice",
        )

    @effect(repeat_interval=0.05)
    def _add_iceground(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 2),
            scale=random.uniform(0, 0.5),
            spread=1.0,
            chunk_type="ice",
            emit_type="stickers",
        )

    @effect(repeat_interval=0.25)
    def _add_slime(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 10),
            scale=0.4,
            spread=0.2,
            chunk_type="slime",
        )

    @effect(repeat_interval=0.25)
    def _add_metal(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 4),
            scale=0.4,
            spread=0.1,
            chunk_type="metal",
        )

    @effect(repeat_interval=0.75)
    def _add_splinter(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 5),
            scale=0.5,
            spread=0.2,
            chunk_type="splinter",
        )

    @effect(repeat_interval=0.001)
    def _add_fairydust(self):
        velocity = 2
        calculate_position = lambda torso_position: torso_position - 0.25 + random.uniform(0, 0.5)
        calculate_velocity = lambda node_velocity, multiplier: random.uniform(-velocity, velocity) + node_velocity * multiplier
        position = tuple(calculate_position(coordinate) for coordinate in self.node.torso_position)
        velocity = (
                    calculate_velocity(self.node.velocity[0], 6),
                    calculate_velocity(self.node.velocity[1], 8),
                    calculate_velocity(self.node.velocity[2], 8),
    )
        bs.emitfx(
                position=position,
                velocity=velocity,
                count=random.randint(100,200),
                spread=8.5,
                emit_type="fairydust",
    )
    
    
    @effect(repeat_interval=0.1)
    def _add_fire(self) -> None:
        if not self.node.exists():
            self._cm_effect_timer = None
        else:
            bs.emitfx(position=self.node.position,
            scale=3,count=50*2,spread=0.3,
            chunk_type='sweat')


    @effect(repeat_interval=0.1)
    def _add_stars(self) -> None:
        def die(node: bs.Node) -> None:
            if node:
                m = node.mesh_scale
                bs.animate(node, 'mesh_scale', {0: m, 0.1: 0})
                bs.timer(0.1, node.delete)

        if not self.node.exists() or self._dead:
            self._cm_effect_timer = None
        else:
            c = 0.3
            pos_list = [
                (c, 0, 0), (0, 0, c),
                (-c, 0, 0), (0, 0, -c)]
            
            for p in pos_list:
                m= 1.5
                np = self.node.position
                pos = (np[0]+p[0], np[1]+p[1]+0.0, np[2]+p[2])
                vel = (random.uniform(-m, m), random.uniform(2, 7), random.uniform(-m, m))

                texs = ['bombStickyColor', 'aliColor', 'aliColorMask', 'eggTex3']
                tex = bs.gettexture(random.choice(texs))
                mesh = bs.getmesh('flash')
                factory = SpazFactory.get()

                mat = bs.Material()
                mat.add_actions(
                    conditions=('they_have_material', factory.punch_material),
                    actions=(
                        ('modify_part_collision', 'collide', False),
                        ('modify_part_collision', 'physical', False),
                    ))
                node = bs.newnode('prop',
                                owner=self.node,
                                attrs={'body': 'sphere',
                                       'position': pos,
                                        'velocity': vel,
                                        'mesh': mesh,
                                        'mesh_scale': 0.1,
                                        'body_scale': 0.0,
                                        'shadow_size': 0.0,
                                        'gravity_scale': 0.5,
                                        'color_texture': tex,
                                        'reflection': 'soft',
                                        'reflection_scale': [1.5],
                                        'materials': [mat]})
                light = bs.newnode('light',
                                   owner=node,
                                   attrs={
                                       'intensity': 0.3,
                                       'volume_intensity_scale': 0.5,
                                       'color': (random.uniform(0.5, 1.5),
                                                 random.uniform(0.5, 1.5),
                                                 random.uniform(0.5, 1.5)),
                                        'radius': 0.035})
                node.connectattr('position', light, 'position')
                bs.timer(0.25, babase.Call(die, node))


    @effect(repeat_interval=1.2)   
    def _add_new_rainbow(self) -> None:
        animate = {
             0.0: (2.0, 0.0, 0.0),
             0.2: (2.0, 1.5, 0.5),
             0.4: (2.0, 2.0, 0.0),
             0.6: (0.0, 2.0, 0.0),
             0.8: (0.0, 2.0, 2.0),
             1.0: (0.0, 0.0, 2.0)
        }
        keys = {
             0.0: (2.0, 0.0, 0.0),
             0.2: (2.0, 1.5, 0.5),
             0.4: (2.0, 2.0, 0.0),
             0.6: (0.0, 2.0, 0.0),
             0.8: (0.0, 2.0, 2.0),
             1.0: (0.0, 0.0, 2.0),
            }.items()
        
        def _changecolor(color: Sequence[float]) -> None:
            if self.node.exists():
                self.node.color = color

        for time, color in keys:
            bs.animate_array(self.node, "highlight", 3, animate, loop=True)
            bs.timer(time, babase.Call(_changecolor, color))
  
   
    @effect(repeat_interval=0.15)   
    def _add_footprint(self) -> None:
        if not self.node.exists():
            self._cm_effect_timer = None
        else:
            loc = bs.newnode('locator', owner=self.node,
              attrs={
                     'position': self.node.position,
                     'shape': 'circle',
                     'color': (random.uniform(0.5, 1.5),
                               random.uniform(0.5, 1.5),
                               random.uniform(0.5, 1.5)),
                     'size': [0.2],
                     'draw_beauty': False,
                     'additive': False})
            bs.animate(loc, 'opacity', {0: 1.0, 1.9: 0.0})
            bs.timer(2.0, loc.delete)


    @effect(repeat_interval=0.1)
    def _add_chispitas(self) -> None:
        def die(node: bs.Node) -> None:
            if node:
                m = node.mesh_scale
                bs.animate(node, 'mesh_scale', {0: m, 0.1: 0})
                bs.timer(0.1, node.delete)

        if not self.node.exists() or self._dead:
            self._cm_effect_timer = None
        else:
            c = 0.3
            pos_list = [
                (c, 0, 0), (0, 0, c),
                (-c, 0, 0), (0, 0, -c)]
            
            for p in pos_list:
                m= 1.5
                np = self.node.position
                pos = (np[0]+p[0], np[1]+p[1]+0.0, np[2]+p[2])
                vel = (random.uniform(-m, m), random.uniform(2, 7), random.uniform(-m, m))

                tex = bs.gettexture('null')
                mesh = None
                factory = SpazFactory.get()

                mat = bs.Material()
                mat.add_actions(
                    conditions=('they_have_material', factory.punch_material),
                    actions=(
                        ('modify_part_collision', 'collide', False),
                        ('modify_part_collision', 'physical', False),
                    ))
                node = bs.newnode('bomb',
                                owner=self.node,
                                attrs={'body': 'sphere',
                                       'position': pos,
                                        'velocity': vel,
                                        'mesh': mesh,
                                        'mesh_scale': 0.1,
                                        'body_scale': 0.0,
                                        'color_texture': tex,
                                        'fuse_length': 0.1,
                                        'materials': [mat]})
                light = bs.newnode('light',
                                   owner=node,
                                   attrs={
                                       'intensity': 0.2,
                                       'volume_intensity_scale': 0.4,
                                       'color': (random.uniform(0.5, 1.5),
                                                 random.uniform(0.5, 1.5),
                                                 random.uniform(0.5, 1.5)),
                                        'radius': 0.025})
                node.connectattr('position', light, 'position')
                bs.timer(0.25, babase.Call(die, node)) 



    @effect(repeat_interval=0.2)
    def _add_darkmagic(self) -> None:
        def die(node: bs.Node) -> None:
            if node:
                m = node.mesh_scale
                bs.animate(node, 'mesh_scale', {0: m, 0.1: 0})
                bs.timer(0.1, node.delete)

        if not self.node.exists() or self._dead:
            self._cm_effect_timer = None
        else:
            c = 0.3
            pos_list = [
                (c, 0, 0), (0, 0, c),
                (-c, 0, 0), (0, 0, -c)]
            
            for p in pos_list:
                m= 1.5
                np = self.node.position
                pos = (np[0]+p[0], np[1]+p[1]+0.0, np[2]+p[2])
                vel = (random.uniform(-m, m), 30.0, random.uniform(-m, m))

                tex = bs.gettexture('impactBombColor')
                mesh = bs.getmesh('impactBomb')
                factory = SpazFactory.get()

                mat = bs.Material()
                mat.add_actions(
                    conditions=('they_have_material', factory.punch_material),
                    actions=(
                        ('modify_part_collision', 'collide', False),
                        ('modify_part_collision', 'physical', False),
                    ))
                node = bs.newnode('prop',
                                owner=self.node,
                                attrs={'body': 'sphere',
                                       'position': pos,
                                        'velocity': vel,
                                        'mesh': mesh,
                                        'mesh_scale': 0.4,
                                        'body_scale': 0.0,
                                        'shadow_size': 0.0,
                                        'gravity_scale': 0.5,
                                        'color_texture': tex,
                                        'reflection': 'soft',
                                        'reflection_scale': [0.0],
                                        'materials': [mat]})
                light = bs.newnode('light',
                                   owner=node,
                                   attrs={
                                       'intensity': 0.8,
                                       'volume_intensity_scale': 0.5,
                                       'color': (0.5, 0.0, 1.0),
                                       'radius': 0.035})
                node.connectattr('position', light, 'position')
                bs.timer(0.25, babase.Call(die, node)) 


    def _add_aure(self) -> None:
        def anim(node: bs.Node) -> None:
            bs.animate_array(node, 'color', 3,
                {0: (1,1,0), 0.1: (0,1,0),
                 0.2: (1,0,0), 0.3: (0,0.5,1),
                 0.4: (1,0,1)}, loop=True)
            bs.animate_array(node, 'size', 1,
                {0: [1.0], 0.2: [1.5], 0.3: [1.0]}, loop=True)

        attrs = ['torso_position', 'position_center', 'position']
        for i, pos in enumerate(attrs):
            loc = bs.newnode('locator', owner=self.node,
                  attrs={'shape': 'circleOutline',
                         'color': self.node.color,
                         'opacity': 1.0,
                         'draw_beauty': True,
                         'additive': False})
            self.node.connectattr(pos, loc, 'position')
            bs.timer(0.1 * i, babase.Call(anim, loc))


    def _add_galactic_burst(self) -> None:
        self._add_new_rainbow()
        self._add_fairydust()

 
    def _add_colorful_spark(self) -> None:
        self._add_spark()
        self._add_sweatground()
        self._add_new_rainbow()


    def _add_star_ring(self) -> None:
        self._add_fairydust()
        self._add_aure()


def apply() -> None:
    bascenev1lib.actor.playerspaz.PlayerSpaz = NewPlayerSpaz
