# ba_meta require api 9

from __future__ import annotations
from typing import TYPE_CHECKING, override

import random
import bascenev1 as bs
import bauiv1 as bui
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.actor.popuptext import PopupText
from bauiv1lib.popup import PopupWindow
from bauiv1lib.confirm import ConfirmWindow
from bascenev1lib.mainmenu import MainMenuActivity, MainMenuSession
from bascenev1lib.actor.spaz import Spaz, BombDiedMessage, PunchHitMessage, POWERUP_WEAR_OFF_TIME
from bascenev1lib.actor import bomb
from bascenev1lib.actor import powerupbox as pb
from bascenev1lib.actor import spazbot as bots

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable

GLOBAL = {"Tab": 'Action 1', 'OT': []}
all_bombs: list[str] = ['curative', 's.m.b', 'Xfactor']
calls: dict = dict()

def apply():
    global apg, cfg, stg
    apg = bui.app.config
    register = dict(ex.pw2_register())
    if 'ex_pow_settings' in apg:
        config = apg['ex_pow_settings']
        for c in register:
            if c not in config:
                apg['ex_pow_settings'] = register
    else:
        apg['ex_pow_settings'] = register
    set = {
        "allow_powerups_in_bots": False,
        "powerups_with_shield": False,
        "sound_when_exploding": False,
        "powerups_with_name": False,
        "explosion_on_death": False,
        "show_time": False,
        "antibomb": False,
        "powerup_animations": 'none',
        "poweup_shield_glow": 1.0,
        "powerup_time": 8}
    if 'ex_settings' in apg:
        config = apg['ex_settings']
        for c in set:
            if c not in config:
                apg['ex_settings'] = set
    else:
        apg['ex_settings'] = set
    apg.apply_and_commit()
    stg = apg['ex_settings']
    cfg = apg['ex_pow_settings']

def getlanguage(text, alm: list = []):
    if not any(alm):
        alm = [a for a in range(62)]
    lang = bui.app.lang.language
    setphrases = {
        "Action 1":
            {"Spanish": "Potenciadores (EX)",
             "English": "Powerups (EX)",
             "Portuguese": "Powerups (EX)"},
        "nitrogen_bomb":
            {"Spanish": "Bombas nitrógenas",
             "English": "Nitrogen bomb",
             "Portuguese": "Bomba de nitrogênio"},
        "Xfactor_bomb":
            {"Spanish": "Factor-X",
             "English": "X-Factor",
             "Portuguese": "Factor-X"},
        "s.m.b_bomb":
            {"Spanish": "Bombas S.M.B",
             "English": "S.M.B Bomb",
             "Portuguese": "S.M.B Bomba"},
        "supplies":
            {"Spanish": "Refuerzos Aéreos",
             "English": "Supplies",
             "Portuguese": "Suprimentos"},
        "T784_bomb":
            {"Spanish": "Torreta-784",
             "English": "T-784",
             "Portuguese": "T-784"},
        "stun_bomb":
            {"Spanish": "Bombas aturdidoras",
             "English": "Stun bombs",
             "Portuguese": "Bombas atordoante"},
        "gloo_wall_bomb":
            {"Spanish": "Pared gloo",
             "English": "Wall gloo",
             "Portuguese": "Parede de gelo"},
        "teleport_bomb":
            {"Spanish": "Tele-bomba",
             "English": "Tele-bomb",
             "Portuguese": "Tele-bomba"},
        "cosmic_bomb":
            {"Spanish": "Bomba cósmica",
             "English": "Cosmic bomb",
             "Portuguese": "bomba cósmica"},
        "electro-bombs":
            {"Spanish": "Bombas Extranocivas",
             "English": "Extra-harmful bombs",
             "Portuguese": "Bombas Extranocivas"},
        "blackhole_bomb":
            {"Spanish": "Bomba Neo-S",
             "English": "New-S bomb",
             "Portuguese": "Bomba Neo-S"},
        "Only.Host":
            {"Spanish": "Opción exclusiva para el host.",
             "English": "Sorry, only the host has permission.",
             "Portuguese": "Apenas o anfitrião é permitido."},
        "act.button.punch":
            {"Spanish": "Genera un nuevo potenciador.",
             "English": "Generate a new powerup.",
             "Portuguese": "Gerar um novo powerup."},
        "act.button.jump":
            {"Spanish": "Animaciones al aparecer.",
             "English": "Animations when appearing.",
             "Portuguese": "Animações ao aparecer."},
        "act.anim1":
            {"Spanish": "Lado izquierdo.",
             "English": "Left side.",
             "Portuguese": "Lado esquerdo."},
        "act.anim2":
            {"Spanish": "Aros de cebolla.",
             "English": "Onion rings.",
             "Portuguese": "Anéis de cebola."},
        "act.anim3":
            {"Spanish": "Dragón.",
             "English": "Dragon.",
             "Portuguese": "Dragão."},
        "act.anim4":
            {"Spanish": "Efecto glitch",
             "English": "Glitch effect",
             "Portuguese": "Efeito glitch"},
        "ow.switches.antibomb":
            {"Spanish": "Inmune a las explociones",
             "English": "Immune to explosions.",
             "Portuguese": "Imune a explosões"},
        "Action 2":
            {"Spanish": "Más opciones",
             "English": "More options",
             "Portuguese": "Mais opções"},
        "ow.activity":
            {"Spanish": "Observar",
             "English": "Display",
             "Portuguese": "Exibição"},
        "ow.switches":
            {"Spanish": "Ajustes 2",
             "English": "Settings 2",
             "Portuguese": "Definições 2"},
        "ow.changes":
            {"Spanish": "Ajustes 1",
             "English": "Settings 1",
             "Portuguese": "Definições 1"},
        "ow.changes.poweup_shield_glow":
            {"Spanish": "Modificar intensidad del escudo",
             "English": "Modify shield intensity",
             "Portuguese": "Modificar a intensidade do escudo"},
        "ow.changes.time_powerup":
            {"Spanish": "Cambiar tiempo del potenciador",
             "English": "Change powerup time",
             "Portuguese": "Alterar hora do powerup"},
        "ow.switches.sound_when_exploding":
            {"Spanish": "Sonido al explotar",
             "English": "Sound when exploding",
             "Portuguese": "Som ao explodir"},
        "ow.switches.explosion_on_death":
            {"Spanish": "Animación de explosión al morir",
             "English": "Explosion animation on death",
             "Portuguese": "Animação de explosão na morte"},
        "ow.switches.powerups_with_name":
            {"Spanish": "Mostrar nombre en los potenciadores",
             "English": "Show name on powerups",
             "Portuguese": "Mostrar nome em powerups"},
        "ow.switches.show_time":
            {"Spanish": "Mostrar Temporizador",
             "English": "Show end time",
             "Portuguese": "Mostrar cronômetro"},
        "ow.switches.powerups_with_shield":
            {"Spanish": "Potenciadores con escudo",
             "English": "Powerups with shield",
             "Portuguese": "Powerups com escudo"},
        "attr_blackhole_bomb":
            {"Spanish": "Atrae e inmoviliza a los jugadores. \n Al estallar creará a \"Sombrita\" que ayudará contra los enemigos.",
             "English": "Pulls in and immobilizes players. \n When it explodes it will create \"Shadow\" that will help against enemies.",
             "Portuguese": "Atrai e imobiliza os jogadores. \n Quando explodir, criará uma \"Sombra\" que ajudará contra os inimigos."},
        "attr_electro-bombs":
            {"Spanish": f"Daño extra de {ex.damage_eb}×{ex.repeat_eb}. \n mientras estás envenenado te reduce la efectividad en un 80%",
             "English": f"Extra damage {ex.damage_eb}×{ex.repeat_eb}. \n while poisoned reduces your effectiveness by 80%",
             "Portuguese": f"Dano extra {ex.damage_eb}×{ex.repeat_eb}. \n enquanto envenenado reduz sua eficácia em 80%"},
        "attr_cosmic_bomb":
            {"Spanish": "Al explotar genera una caja que aumenta 50% de efectividad.",
             "English": "When it explodes, it spawns a crate that increases its effectiveness by 50%",
             "Portuguese": "Quando explode, gera uma caixa que aumenta sua eficácia em 50%."},
        "attr_teleport_bomb":
            {"Spanish": "Teletransporta y cura",
             "English": "Teleport and heal.",
             "Portuguese": "Teletransportar e curar."},
        "attr_gloo_wall_bomb":
            {"Spanish": f"Crea una pared de hielo insana que bloquea el paso por {ex.duration_gw} segundos.",
             "English": f"Creates a wall of ice that blocks passage for {ex.duration_gw} seconds.",
             "Portuguese": f"Cria uma parede de gelo que bloqueia a passagem por {ex.duration_gw} segundos."},
        "superhuman_healing":
            {"Spanish": "Ultra Resistencia",
             "English": "Superhuman healing",
             "Portuguese": "Cura de ferro"},
        "attr_superhuman_healing":
            {"Spanish": f"Cada {ex.time_sh} segundos los personajes recuperan un {ex.percentage_sh}% de su salud faltante.\n Cuando tengas la salud llena, creará un escudo de energía que aumentará\n gradualmente {ex.shield_hitpoints_sh} puntos de vida.",
             "English": f"Every {ex.time_sh} seconds characters recover {ex.percentage_sh}% of their missing health.\n When you have full health, create an electro-shield that increases {ex.shield_hitpoints_sh} health points",
             "Portuguese": f"A cada {ex.time_sh} segundos, os personagens recuperam {ex.percentage_sh}% de sua saúde perdida.\n Quando você estiver com a saúde completa, crie um escudo elétrico\n que aumente {ex.shield_hitpoints_sh} pontos de saúde."},
        "super_shield":
            {"Spanish": "Super electro-escudo",
             "English": "Super shield",
             "Portuguese": "Super-Proteção"},
        "attr_super_shield":
            {"Spanish": f"Durante {ex.duration_ss} segundos crea un escudo que reduce el {ex.reduction_ss}% del daño recibido.\n Cuando el efecto termina, crea una explosión que aleja a los jugadores cercanos.",
             "English": f"For {ex.duration_ss} seconds creates a shield that reduces {ex.reduction_ss}% of the damage taken.\n When the shield is broken it creates an area of explosion that blows away nearby players.",
             "Portuguese": f"Por {ex.duration_ss} segundos cria um escudo que reduz {ex.reduction_ss}% do dano recebido.\n Quando o escudo é quebrado cria uma área de explosão que afasta os jogadores próximos."},
        "allow_in_bots":
            {"Spanish": "Permitir potenciadores en bots",
             "English": "Allow powerups on bots",
             "Portuguese": "Permitir powerups em bots"},
        "+info":
            {"Spanish": "Más información",
             "English": "More information",
             "Portuguese": "Mais informação"},
        "category-1":
            {"Spanish": "Categoría: Desplegable",
             "English": "Category: Deployable",
             "Portuguese": "Categoria: Arremessáveis"},
        "category-2":
            {"Spanish": "Categoría: Consumible",
             "English": "Category: Absorption",
             "Portuguese": "Categoria: absorção"},
        "attr_supplies":
            {"Spanish": "Función disponible solo si estás cerca de enemigos.",
             "English": "Function available only if you are close to enemies.",
             "Portuguese": "Função disponível apenas se você estiver perto de inimigos."},
        "attr_T784_bomb":
            {"Spanish": f"Crea una torreta que inflige \"{ex.damage_t784}\" daño. \n No se lleva bien con «El Huevón»",
             "English": f"Creates a turret that inflicts \"{ex.damage_t784}\" damage. \n He doesn't get along with «Happy Egg»",
             "Portuguese": f"Cria uma torre que reparte \"{ex.damage_t784}\" danos. \n Ele não se dá bem com «Ovo Vivo»"},
        "attr_s.m.b_bomb":
            {"Spanish": "Empuja a los rivales alcanzados por la explosión. \n Dato: S.M.B (Súper Mega Bomba) inspirado en algún juguete de un Ruso.",
             "English": "Pushes rivals hit by the explosion.",
             "Portuguese": "Empurra para longe os adversários atingidos pela explosão."},
        "attr_nitrogen_bomb":
            {"Spanish": "Crea una zona fría. \n Dato: Más frías que el invierno de Ushuaia.",
             "English": "Creates a cold zone. \n Fact: Colder than Ushuaia's winter.",
             "Portuguese": "Crea una zona fría. \n Fato: Mais frio que o inverno de Ushuaia."},
        "attr_Xfactor_bomb":
            {"Spanish": "Persiguen al rival mas cercano. \n Al estár cerca de un enemigo puede atraerlo.",
             "English": "Detects nearby rivals. \n Being close to an enemy can attract it.",
             "Portuguese": "Detecta rivais próximos. \n Fato: Feito no Brasil. \n Estar perto de um inimigo pode atraí-lo."},
        "attr_stun_bomb":
            {"Spanish": "Aturde y ralentiza a los jugadores durante 3,5 segundos \n Nota: Los jugadores ven un video de GoDeiK ¡Y se duermen!",
             "English": "Stuns and slows players for 3.5 seconds",
             "Portuguese": "Atordoa e retarda os jogadores por 3.5 segundos"},     
        "attributes":
            {"Spanish": "Atributos:",
             "English": "Attributes:",
             "Portuguese": "Atributos:"},
        "Creator":
            {"Spanish": "Mod creado por @PatrónModz",
             "English": "Mod created by @PatrónModz",
             "Portuguese": "Mod creado by @PatrónModz"},
        "Mod Info":
            {"Spanish": f"¿PowerupMánager? ¡No! \n --- EX-Powerups --- \n Prueba los {alm[0]} diferentes potenciadores y \n hazte con la partida",
             "English": f"PowerupManager? No! \n --- EX-Powerups --- \n Try the {alm[0]} different powerups and \n win the game",
             "Portuguese": f"PowerupManager? Não! \n --- EX-Powerups --- \n Experimente os {alm[0]} powerups diferentes \n e ganhe o jogo"},
        }
    language = ["Spanish", "English", "Portuguese"]
    if lang not in language:
        lang = "English"
    if text not in setphrases:
        return text
    return setphrases[text][lang]

class Builder:
    # ===== T784 ===== #
    cooldown_t784: float = 0.1 #0.3
    hitpoints_t784: int = 840 #400
    max_cure_t784: int = 180 #80
    min_cure_t784: int = 35 #20
    size_t784: float = 12.0 #9.0
    damage_t784: int = 280 #200
    # ===== Gloo Wall ===== #
    duration_gw: int = 15
    # ===== Cosmic Bomb ===== #
    duration_cb: int = 3
    extra_power_cb: float = 1.5 #1.3
    # ===== Electro Bomb ===== #
    damage_eb: int = 40
    repeat_eb: int = 9
    eff_eb: float = 0.2
    # ==== Sombrita ==== #
    sombrita_hp: int = 3000
    # ==== Superhuman Healing ==== #
    shield_hitpoints_sh: int = 30
    percentage_sh: int = 25
    time_sh: float = 1.5
    # ==== Super Shield ==== #
    reduction_ss: int = 90
    duration_ss: int = 7

    def pw2_register():
        return {
               'nitrogen_bomb': 3,
               'Xfactor_bomb': 3,
               's.m.b_bomb': 3,
               'T784_bomb': 3,
               'stun_bomb': 3,
               'supplies': 3,
               'gloo_wall_bomb': 3,
               'teleport_bomb': 2,
               'cosmic_bomb': 3,
               'electro-bombs': 2,
               'blackhole_bomb': 1,
               'superhuman_healing': 1,
               'super_shield': 2,
               'attraction_bomb': 3,
               }.items()
    
    def get_random_color(x: float = 2.0, m: int = 1, mx: float = 0.5):
        return tuple(max(round(s, m), mx) for s in
                   [random.random()*x,
                    random.random()*x,
                    random.random()*x])
    
    def call_hiperbox(data: list):
        try:
            act = bs.getactivity()
            with act.context:
                hb = HiperBox(type=data[0],
                     position=data[1]).autoretain()
        except Exception as e: print(e, '%?')
        return hb
    
    def spawn_hiperbox(defs: dict):
        all_pos = []
        points = defs.points.items()
        for key, value in points:
            if 'spawn' in key:
                if len(value) == 3:
                    all_pos.append(value)
        if not any(all_pos):
            return
        while len(all_pos) > 5:
            pos = random.choice(all_pos)
            all_pos.remove(pos)
        boxes = []
        for pow, _i in cfg.items():
            for x in range(int(_i)):
                boxes.append(pow)
        if not any(boxes):
            return
        for i, p in enumerate(all_pos):
            box = random.choice(boxes)
            pos = [x for x in p]
            pos[0] += (1.5-random.random()*3)
            pos[1] += 1.0 
            pos[2] += (1.5-random.random()*3)
           # bs.timer(0.33 * i,
            #     bs.Call(ex.call_hiperbox, [box, pos]))
            
    def hiperbox(type: str, in_ui: bool = False):
        if in_ui:
            t = bui.gettexture
            m = bui.getmesh
        else:
            t = bs.gettexture
            m = bs.getmesh
        mesh = {'nitrogen_bomb': m('shield'),
                }.get(type, m('powerup'))
        tex = {'nitrogen_bomb': t('bombColorIce'),
               'Xfactor_bomb': t('textClearButton'),
               's.m.b_bomb': t('touchArrowsActions'),
               'T784_bomb': t('star'),
               'supplies': t('logoEaster'),
               'stun_bomb': t('ouyaUButton'),
               'gloo_wall_bomb': t('bombColorIce'),
               'teleport_bomb': t('rightButton'),
               'cosmic_bomb': t('achievementFootballShutout'),
               'cosmic_box': t('landMineLit'),
               'electro-bombs': t('levelIcon'),
               'blackhole_bomb': t('replayIcon'),
               'superhuman_healing': t('achievementStayinAlive'),
               'super_shield': t('ouyaOButton'),
               'attraction_bomb': t('backIcon'),
              }.get(type, t('eggTex2'))
        scale = {'nitrogen_bomb': 0.25,
                }.get(type, 1.0)
        ref, refs = {'T784_bomb': ('soft', 1.4),
                     'supplies': ('soft', 1.4),
                     'stun_bomb': ('soft', 1.8),
                     's.m.b_bomb': ('soft', 1.8),
                     'cosmic_bomb': ('soft', 2.0),
                     'cosmic_box': ('soft', 1.3),
                     'nitrogen_bomb': ('soft', 0.2),
                     'gloo_wall_bomb': ('powerup', 1.5),
                     'levelIcon': ('soft', 0.2),
                     'super_shield': ('soft', 1.8),
                    }.get(type, ('powerup', 1.0))
        return {'tex': tex,
                'mesh': mesh,
                'scale': scale,
                'ref': ref,
                'refs': refs}
    
    def materials(callback: Callable = None):
        factory = pb.PowerupBoxFactory.get()
        spazfactory = SpazFactory.get()
        shared = SharedObjects.get()
        powerup_material = bs.Material() #factory.powerup_material
        freeze_material = bs.Material()
        xfactor_material1 = bs.Material()
        xfactor_material2 = bs.Material()
        no_pickup_material = bs.Material()
        no_collision_material = bs.Material()
        touch_material = bs.Material()
        no_object_material = bs.Material()
        collision_material = bs.Material()
        no_object_material.add_actions(
            conditions=('they_have_material', shared.object_material),
            actions=(
                ('modify_part_collision', 'collide', False),
                ('modify_part_collision', 'physical', False)
            ))
        no_collision_material.add_actions(
            actions=(('modify_part_collision', 'collide', False)))
        xfactor_material1.add_actions(
                conditions=('they_have_material', shared.footing_material),
                actions=(
                    ('modify_part_collision', 'collide', True),
                    ('modify_part_collision', 'physical', True),
                    ('message', 'our_node', 'at_connect', _TouchMessage())))
        xfactor_material2.add_actions(
                conditions=('they_have_material', shared.player_material),
                actions=(
                    ('modify_part_collision', 'collide', True),
                    ('modify_part_collision', 'physical', False),
                    ('message', 'our_node', 'at_connect', ExplodeMessage())))
        no_pickup_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'collide', False))
        powerup_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'collide', False))
        powerup_material.add_actions(
                conditions=('they_have_material', factory.powerup_accept_material),
                actions=(
                    ('modify_part_collision', 'collide', True),
                    ('modify_part_collision', 'physical', False),
                    ('message', 'our_node', 'at_connect', pb._TouchedMessage()),
                ))
        collision_material.add_actions(
            actions=(('modify_part_collision', 'collide', True)))
        if stg['allow_powerups_in_bots']:
            powerup_material.add_actions(
                conditions=('they_have_material', shared.player_material),
                actions=(
                    #('modify_part_collision', 'friction', 5),
                    ('modify_part_collision', 'collide', True),
                    ('modify_part_collision', 'physical', False),
                    ('message', 'our_node', 'at_connect', pb._TouchedMessage()),
                ))
        if callback is not None:
            freeze_material.add_actions(
                conditions=('they_have_material', shared.player_material),
                actions=(('modify_part_collision', 'collide', True),
                        ('modify_part_collision', 'physical', False),
                        ('call', 'at_connect', callback)))
            touch_material.add_actions(
                 conditions=('they_have_material', shared.player_material),
                actions=(('modify_part_collision', 'collide', False),
                        ('modify_part_collision', 'physical', False),
                        ('call', 'at_connect', callback)))
        return [powerup_material, #0
                freeze_material, #1
                xfactor_material1, #2
                xfactor_material2, #3
                no_pickup_material, #4
                no_collision_material, #5
                touch_material, #6
                no_object_material, #7
                collision_material, #8
                ]
    
    def smb_eff(**kwargs):
        for i in range(4):
            Smb(i, **kwargs).autoretain()
        bs.getsound('cheer').play()

    def impulse(owner: bs.Node, msg: Any):
        if isinstance(msg, bs.HitMessage):
            for i in range(2):
                owner.handlemessage(
                    'impulse', msg.pos[0], msg.pos[1], msg.pos[2],
                    msg.velocity[0], msg.velocity[1]+2.0, msg.velocity[2], msg.magnitude,
                    msg.velocity_magnitude, msg.radius, 0, msg.force_direction[0],
                    msg.force_direction[1], msg.force_direction[2])
    
    def calculate(a: float, b: float, c: int = 2):
        try:
            value = round(a * b / 100, c)
            return value
        except: return 0
    
    def petage(a: float, b: float, c: int = 2):
        try:
            value = round(100 * a / b, c)
            return value
        except: return 0
    
    def fake_explosion(position: Sequence[float],
                       radius: float = 1.8,
                       sound: bool = True,
                       color: Sequence[float] = (0.23, 0.23, 0.23)):
        explosion = bs.newnode('explosion',
                   attrs={'position': position, 'color': color,
                          'radius': radius, 'big': False})
        bs.timer(1.0, explosion.delete)
        if sound:
            sounds = ['explosion0'+str(n) for n in range(1,6)]
            sound = random.choice(sounds)
            bs.getsound(sound).play()
    
    def hitmessage(msg: Any,
                   delegate: Any = None,
                   reduction: int = 0,
                   die: bool = True):
        mag = msg.magnitude * 1.0
        velocity_mag = msg.velocity_magnitude
        damage_scale = 0.22
        if not hasattr(delegate, 'hitpoints_max'):
            delegate.hitpoints_max = delegate.hitpoints
        if not msg.flat_damage:
            if bool(reduction):
                damage = round(ex.calculate(mag +
                    velocity_mag,reduction),2)
            else:
                damage = round(mag + velocity_mag,2)
        else:
            damage = round(msg.flat_damage, 2)
        if msg.hit_type == 'explosion':
            damage = min(ex.calculate(damage, 40),
                         ex.hitpoints_t784 * 0.5)
        elif msg.hit_type == 'punch':
            damage = min(damage, 1000)
            if msg.hit_subtype == 'super_punch':
                SpazFactory.get().punch_sound_stronger.play(
                             1.0,
                             position=delegate.node.position)
            if damage > 500:
                sounds = SpazFactory.get().punch_sound_strong
                sound = sounds[random.randrange(len(sounds))]
            else:
                sound = SpazFactory.get().punch_sound
            sound.play(1.0, position=delegate.node.position)
        damage = int(damage)
        delegate.hitpoints = max(
            delegate.hitpoints-damage, 0)
        if damage != 0:
            dmg = (f'-{int(ex.petage(damage, delegate.hitpoints_max, 0))}%')
            bs.show_damage_count(dmg, delegate.node.position, msg.force_direction)
        try: delegate.update_hp()
        except: pass
        if die:
            if delegate.hitpoints == 0:
                delegate.node.handlemessage(bs.DieMessage())
    
    def getnodepos(nodes: list[bs.Node], x: float = 5.0):
        return (
               (nodes[0].position[0] - nodes[1].position[0]) * x,
               (nodes[0].position[1] - nodes[1].position[1]) * x,
               (nodes[0].position[2] - nodes[1].position[2]) * x)
    
    def getnodedis(nodes: list[bs.Node]):
        dis = [abs(nodes[0].position[0] - nodes[1].position[0]),
               abs(nodes[0].position[2] - nodes[1].position[2])]
        dis.sort(reverse=True)
        return dis
    
    def zap(node: bs.Node):
        if not node:
            return
        def misil(loc: bs.Node):
            a = (loc.position[0], 8.0, loc.position[2])
            b = (0.0, -9.0, 0.0)
            boom = bomb.Bomb(
                position=a, bomb_type='impact', blast_radius=5.0,
                velocity=b, bomb_scale=2.38).autoretain()
            boom.node.add_death_action(
                bs.Call(loc.delete))
        loc = bs.newnode('locator',
            #owner=node,
            attrs={'shape': 'circleOutline',
                   'position': node.position,
                   'color': (6,0,0),
                   'opacity': 0.3,
                   'size': [2.5],
                   'draw_beauty': False,
                   'additive': True})
        #node.connectattr('position_center', loc, 'position')
        bs.timer(0.7, bs.Call(misil, loc))
    
    def health(msg, hp: int = 0):
        hp = int(ex.Cosmic(msg.node, hp))
        hp_min = int(ex.Cosmic(msg.node, ex.min_cure_t784))
        popup = lambda x, msg=msg: PopupText(text=x,
              color=(0.1, 1.0, 0.1), scale=1.5,
              random_offset=0.0, position=msg.node.position).autoretain()
        if msg.shield:
            hp_max = msg.shield_hitpoints_max
            if msg.shield_hitpoints >= hp_max:
                hp = hp_min
            msg.shield_hitpoints += hp
            popup('+'+str(hp)+'SHP')
        else:
            hp_max = msg.hitpoints_max
            if msg.hitpoints >= hp_max:
                hp = hp_min
            msg.hitpoints += hp
            popup('+'+str(hp)+'HP')
            bs.getsound('healthPowerup').play()
    
    def superhuman_health(self) -> None:
        if self._dead or not self.node:
            self.ex_superhuman_health = None
            return
        popup = lambda x: PopupText(text=x,
              color=(0.1, 1.0, 0.1), scale=1.5,
              random_offset=0.0, position=self.node.position).autoretain()
        tm = ex.time_sh / 2
        if self.shield:
            ex_shield = getattr(self, 'ex_shield_sh_color', None)
            if self.shield.color == ex_shield and self.shield_hitpoints < 1000:
                self.shield_hitpoints += ex.shield_hitpoints_sh
                self.shield_hitpoints_max = self.shield_hitpoints
                self.shield_hitpoints = min(self.shield_hitpoints, 1000)
                popup('+' + str(ex.shield_hitpoints_sh) + 'SHP')
        else:
            hp = self.hitpoints_max - self.hitpoints
            cure = int(hp / 100 * ex.percentage_sh)
            cure = max(cure, 25)
            if self.hitpoints < self.hitpoints_max:
                self.hitpoints = min(self.hitpoints + cure, self.hitpoints_max)
                text = '+' + str(max(int(cure * 100 / self.hitpoints_max), 1)) + '%'
                popup(text)
                tm = ex.time_sh
                bs.getsound('healthPowerup').play()
            else:
                self.equip_shields()
                self.shield.color = (0.0, 1.0, 0.0)
                self.shield_hitpoints = 0
                self.ex_shield_sh_color = self.shield.color
        bs.timer(tm, bs.Call(ex.superhuman_health, self))
    
    def super_shield(self) -> None:
        if self._dead or not self.node or self.ex_super_shield is None:
            self.ex_super_shield = None
            return
        
        def break_shield(self=self):
            if self.shield:
                ex_shield = getattr(self, 'ex_shield_ss_color', None)
                if self.shield.color != ex_shield:
                    self.ex_super_shield = None
                    return
            s = 100000000
            damage = (s - self.shield_hitpoints)
            if self.shield is not None:
                self.shield.delete()
                self.shield = None
                self.ex_super_shield = None
                bs.getsound('shieldDown').play()
            self.shield_hitpoints = s
            if damage > 0:
                tank = int(damage - ex.calculate(damage, ex.reduction_ss))
                msg = bs.HitMessage(srcnode=self.node, flat_damage=tank, velocity=(0, 0, 0))
                self.node.handlemessage(msg)
                text = '-' + str(int(ex.petage(tank, self.hitpoints_max)))  + '%'
                PopupText(text=text, random_offset=0.0,
                    color=(0.8, 0.1, 0.1), scale=1.5,
                    position=self.node.position).autoretain()
        
        def blast(self=self):
            ExBlast(owner=self.node,
                    blast_radius=2.5,
                    blast_type='super_shield',
                    position=self.node.position,
                    velocity=(80.0, 20.0, 80.0),
                    source_player=self.source_player)
        
        def all_calls():
            break_shield()
            blast()

        if self.shield:
            ex_shield = getattr(self, 'ex_shield_ss_color', None)
            if self.shield.color != ex_shield:
                self.shield.delete()
                self.shield = None
        else:
            self.equip_shields()
            self.shield.color = (1.2, 1.2, 0.0)
            self.shield_hitpoints = 100000000
            self.ex_shield_ss_color = self.shield.color
            self.shield_hitpoints_max = self.shield_hitpoints
            ex.timer_in_nodes(self.shield,
                time=ex.duration_ss,
                callback=all_calls,
                position=(0.0, 1.2, -0.0))
        bs.timer(0.5, bs.Call(ex.super_shield, self))
    
    def effect_attraction(self, enemy: bs.Actor | None) -> None:
        if (enemy is not None and self.node
        and self.owner is not None and self.owner):
            p = ex.getnodepos([self.owner, self.node], x=8.0)
            self.node.velocity = p
            self.node.extra_acceleration = p
            enemy._pick_up(self.node)
            enemy.node.handlemessage('knockout', 5000)
        if not hasattr(self, 'eff_attraction_timer'):
            for n in range(int(5 / 0.1)):
                bs.timer(n * 0.1, bs.Call(ex.effect_attraction, self, enemy))
            bs.timer(n * 0.1, bs.Call(ex.end_effect_attraction, self, enemy))
            self.eff_attraction_timer = False
    
    def end_effect_attraction(self, enemy: bs.Node = None) -> None:
        if (enemy is not None and enemy and self.node
        and self.owner is not None and self.owner):
            enemy.handlemessage(bs.StandMessage(position=self.owner.position))
        if self.node:
            self.node.delete()
            bs.getsound('laserReverse').play()
    
    def eco_sound(res: str, repeat: float = 0.8) -> None:
        values = [1.0, 0.75, 0.5, 0.25, 0.1, 0.01]
        values.sort(reverse=True)
        for n, val in enumerate(values):
            sound = bs.getsound(res)
            for n1 in [0.0, 0.2]:
                bs.timer(n * repeat + n1,
                     bs.Call(sound.play, volume=val))
    
    def getspazzes() -> list:
        spazzes = []
        if bs.getnodes() != []:
            for node in bs.getnodes():
                if node.getnodetype() == 'spaz':
                    spazzes.append(node)
        return spazzes
    
    def get_team(player: bs.Player):
        try:
            if player is not None:
                team = []
                players = getattr(player.team, 'players', [])
                for p in players:
                    team.append(p.actor.node)
                return team
            else:
                return []
        except:
            return []
    
    def timer_in_nodes(node: bs.Node,
                       time: int = 5,
                       call: Callable[[], None] | None = None,
                       callback: Callable[[], None] | None = None,
                       position: Sequence[float] = (0.0, 0.7, 0.0)):
        if type(time) is not int:
            raise TypeError("'" + str(time) + "' is not type 'int'")
        time = [s+1 for s in range(int(time))]
        time.sort(reverse=True)
        time.append(0)
        
        def text(i):
            if not node:
                return
            if i != 0 and callable(call):
                try: call(i)
                except: call()
            if i > 0:
                c = tuple(max(random.random()*2, 0.3) for q in range(3))
                m = bs.newnode('math', owner=node, attrs={'input1':
                    (position[0], position[1], position[2]),'operation': 'add'})
                node.connectattr('position', m, 'input2')
                popup = PopupText(
                        text=str(i), color=c, scale=1.8,
                        random_offset=0.0, position=node.position).autoretain()
                m.connectattr('output', popup.node, 'position')
                bs.timer(1.0, bs.Call(popup.handlemessage, bs.DieMessage()))
            if i == 0:
                if callable(callback):
                    callback()
        for i, n in enumerate(time):
            bs.timer(0.0 + i, bs.Call(text, n))
    
    def supp(self):
        nodes = []
        for node in ex.getspazzes():
            if (self.node != node and
                node not in ex.get_team(self._player)):
                nodes.append(node)
        for i, node in enumerate(nodes):
            bs.timer(0.15 * i, bs.Call(ex.zap, node))
    
    def new_init_hitmessage(self, *args, **kwargs):
        calls['hitmessage'](self, *args, **kwargs)
        self.cls_owner = (self.srcnode.getdelegate(object)
            if self.srcnode else self._source_player.actor
            if self._source_player else None)
        if getattr(self.cls_owner, 'cosmic_power', False):
            if self.flat_damage is not None:
                self.flat_damage = int(self.flat_damage * ex.extra_power_cb)
            else:
                self.magnitude *= ex.extra_power_cb
        if getattr(self.cls_owner, '_eb_eff', False):
            if self.flat_damage is not None:
                self.flat_damage = int(self.flat_damage * ex.eff_eb)
            else:
                self.magnitude *= ex.eff_eb
    
    def Cosmic(node: bs.Node, value: float):
        cls_node = node.getdelegate(object)
        if getattr(cls_node, '_eb_eff', False):
            return value
        m = bs.HitMessage(srcnode=node)
        return value * m.magnitude
    
    def enter_the_expw_activity():
        def callback():
            bs.new_host_session(ExPowerupsSession)
        if not ex.in_expw_activity():
            bs.fade_screen(False, time=0.5, endcall=callback)
    
    def in_expw_activity():
        a = bs.get_foreground_host_activity()
        return isinstance(a, ExPowerupsActivity)
    
    def electricity(node: bs.Node, owner: bs.Node):
        type = node.getnodetype()
        cls_node = node.getdelegate(object)
        def call(i: int):
            if not node:
                return
            msg = bs.HitMessage(
                srcnode=owner,
                velocity=(0, 0, 0),
                flat_damage=ex.damage_eb,
                hit_subtype='electro')
            node.handlemessage(msg)
            if type == 'spaz':
                node.handlemessage('knockout', 100.0)
                if ex.repeat_eb == i+1:
                    cls_node._eb_eff = False
                PopupText(text='-'+str(msg.flat_damage)+'HP',
                  color=(0.8, 0.1, 0.1), scale=1.0,
                  random_offset=0.0, position=node.position).autoretain()
        if type == 'spaz':
            cls_node._eb_eff = True
        if not getattr(node, 'invincible', False):
            for i in range(ex.repeat_eb):
                bs.timer(2.0 * (i+1), bs.Call(call, i))
# ================================================================================================================== #
    def _bomb_wear_off_flash(self, tex: bs.Texture) -> None:
        if self.node:
            self.node.billboard_texture = tex
            self.node.billboard_opacity = 1.0
            self.node.billboard_cross_out = True
    def powerup_bomb(self, bomb: str, powerup: str):
        if not bomb in all_bombs:
            all_bombs.append(bomb)
        self.bomb_type = bomb
        tex = ex.hiperbox(powerup)['tex']
        if self.powerups_expire:
            self.node.mini_billboard_2_texture = tex
            t_ms = int(bs.time() * 1000.0)
            assert isinstance(t_ms, int)
            self.node.mini_billboard_2_start_time = t_ms
            self.node.mini_billboard_2_end_time = (
                t_ms + POWERUP_WEAR_OFF_TIME)
            self._bomb_wear_off_flash_timer = bs.Timer(
                (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
                bs.Call(ex._bomb_wear_off_flash, self, tex))
            self._bomb_wear_off_timer = bs.Timer(
                POWERUP_WEAR_OFF_TIME / 1000.0,
                bs.WeakCall(self._bomb_wear_off))
    def count_bombs(self, count: int, bomb: str, powerup: str):
        if not bomb in all_bombs:
            all_bombs.append(bomb)
        if not hasattr(self, 'ex_count_bomb'):
            self.ex_count_bomb = 0
            self.ex_count_bomb_text = lambda s=self: PopupText(
                text='x'+str(s.ex_count_bomb),
                color=(0.1, 1.0, 0.1), scale=1.8,
                random_offset=0.0, position=s.node.position).autoretain()
        self.ex_bomb = bomb
        self.ex_count_bomb = min(
            self.ex_count_bomb + count, count)
        self.ex_count_bomb_text()
    def powerup_call(self, tag: str):
        if tag == 'null':
            self.node.color = (0,6,1)
        elif tag == 'nitrogen_bomb':
            ex.powerup_bomb(self, 'nitrogen', tag)
        elif tag == 'Xfactor_bomb':
            ex.count_bombs(self, 2, 'Xfactor', tag)
        elif tag == 's.m.b_bomb':
            ex.count_bombs(self, 1, 's.m.b', tag)
        elif tag == 'T784_bomb':
            ex.count_bombs(self, 1, 'T784', tag)
        elif tag == 'stun_bomb':
            ex.powerup_bomb(self, 'stun', tag)
        elif tag == 'gloo_wall_bomb':
            ex.count_bombs(self, 1, 'gloo', tag)
        elif tag == 'teleport_bomb':
            ex.count_bombs(self, 1, 'teleport', tag)
        elif tag == 'cosmic_bomb':
            ex.count_bombs(self, 1, 'cosmic', tag)
            #ex.powerup_call(self, 'cosmic_box')
        elif tag == 'electro-bombs':
            ex.powerup_bomb(self, 'electro', tag)
        elif tag == 'blackhole_bomb':
            ex.count_bombs(self, 1, 'blackhole', tag)
        elif tag == 'supplies':
            ex.supp(self)
        elif tag == 'attraction_bomb':
            ex.count_bombs(self, 1, 'attraction', tag)
        elif tag == 'super_shield':
            if not getattr(self, 'ex_super_shield', None):
                self.ex_super_shield = True
                ex.super_shield(self)
        elif tag == 'superhuman_healing':
            if not getattr(self, 'ex_superhuman_health', None):
                self.ex_superhuman_health = True
                ex.superhuman_health(self)
        elif tag == 'cosmic_box':
            if not getattr(self, 'cosmic_power', False):
                self.cosmic_power = True
                c = list(self.node.color)
                c[1] += 1.5
                self.node.color = tuple(c)
    def drop_bomb(self):
        bomb_type = self.bomb_type
        if getattr(self, 'ex_bomb', None):
            bomb_type = self.ex_bomb
        if (bomb_type not in all_bombs
        or self.node.counter_text != ''):
            return calls['drop_bomb'](self)
        if (self.land_mine_count <= 0 and self.bomb_count <= 0) or self.frozen:
            return None
        assert self.node
        pos = self.node.position_forward
        vel = self.node.velocity
        dropping_bomb = True
        bomb = ExBomb(position=(pos[0], pos[1] - 0.0, pos[2]),
                      velocity=(vel[0], vel[1], vel[2]),
                      bomb_scale=1.0,
                      bomb_type=bomb_type,
                      blast_radius=self.blast_radius,
                      source_player=self.source_player,
                      owner=self.node).autoretain()
        assert bomb.node
        if getattr(self, 'ex_count_bomb', 0) > 0:
            self.ex_count_bomb -= 1
            self.ex_count_bomb_text()
            if self.ex_count_bomb < 1:
                #self.bomb_type = self.ex_bomb
                del self.ex_bomb
        else:
            if dropping_bomb:
                self.bomb_count -= 1
                bomb.node.add_death_action(
                    bs.WeakCall(self.handlemessage, BombDiedMessage()))
        self._pick_up(bomb.node)
        for clb in self._dropped_bomb_callbacks:
            clb(self, bomb)
        return bomb
# ================================================================================================================== #
class _TouchMessage:
    pass
class ExplodeMessage:
    pass
class ExplodeBombMessage:
    pass
# ================================================================================================================== #
class ExBlast(bomb.Blast):
    def __init__(self,
                 position: Sequence[float] = (0.0, 1.0, 0.0),
                 velocity: Sequence[float] = (0.0, 0.0, 0.0),
                 owner: bs.Node = None, **kwargs):
        super().__init__(position=position, **kwargs)
        self.owner = owner
        self.position = position
        self.velocity = velocity
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired
        if isinstance(msg, bomb.ExplodeHitMessage):
            node = bs.getcollision().opposingnode
            cls_node = node.getdelegate(object)
            pos = self.position
            nodepos = self.node.position
            mag = 2000.0
            if self.blast_type == 'nitrogen':
                mag = 672.0
                if node.getnodetype() == 'spaz':
                    if cls_node.shield:
                        mag = 1300.0
            elif self.blast_type == 'curative':
                if node.getnodetype() == 'spaz':
                    ex.health(cls_node, 100)
                return
            elif self.blast_type == 'electro':
                team = ex.get_team(self._source_player)
                if self.owner == node:
                    return
                if node in team:
                    return
                ex.electricity(node, self.owner)
            elif self.blast_type == 'super_shield':
                team = ex.get_team(self._source_player)
                if self.owner == node:
                    return
                if node in team:
                    return
                return ex.impulse(node,
                    bs.HitMessage(pos=self.position,
                                  velocity=self.velocity,
                                  magnitude=1200,
                                  hit_subtype='stun',
                                  radius=800))
            node.handlemessage(
                bs.HitMessage(pos=nodepos,
                              velocity=(0, 0, 0),
                              magnitude=mag,
                              hit_type=self.hit_type,
                              hit_subtype=self.hit_subtype,
                              radius=self.radius,
                              source_player=bs.existing(self._source_player)))
        else:
            return super().handlemessage(msg)

# ===================== ExObjects =============================================================================================

class ExBomb(bomb.Bomb):
    def __init__(self,
                 bomb_type: str = 'normal', **kwargs):
        self.type = {'Xfactor': 'impact',
                     's.m.b': 'impact',
                     'T784': 'impact',
                     'gloo': 'impact',
                     'teleport': 'impact',
                     'cosmic': 'impact',
                     'blackhole': 'impact',
                     'curative': 'impact',
                     'attraction': 'land_mine',
                    }.get(bomb_type, 'normal')
        super().__init__(bomb_type=self.type, **kwargs)
        factory = bomb.BombFactory.get()
        tex = self.node.color_texture
        mod = self.node.mesh
        scale = None
        self.xp_sound = None
        if bomb_type == 'nitrogen':
            tex = bs.gettexture('powerupIceBombs')
            #mod = bs.getmesh('shield')
            self.node.reflection = 'soft'
            self.node.reflection_scale = [1.3]
            self.xp_sound = 'hiss'
            #scale = 0.25
        elif bomb_type == 'Xfactor':
            tex = bs.gettexture('eggTex1')
            mod = bs.getmesh('egg')
            self.node.reflection = 'soft'
            self.node.reflection_scale = [0.23]
            mat1, mat2 = (ex.materials()[2], ex.materials()[3], )
            self.node.materials += (mat1, mat2, )
            scale = 0.5
        elif bomb_type == 's.m.b':
            tex = bs.gettexture('powerupIceBombs')
            mod = bs.getmesh('shield')
            self.node.reflection = 'soft'
            self.node.reflection_scale = [2.6]
            scale = 0.25
        elif bomb_type == 'T784':
            tex = bs.gettexture('ouyaOButton')
            mod = bs.getmesh('shield')
            self.node.reflection = 'soft'
            self.node.reflection_scale = [1.4]
            self.blast_radius = 0.0
            scale = 0.25
        elif bomb_type == 'stun':
            tex = bs.gettexture('eggTex3')
            #mod = bs.getmesh('shield')
            self.node.reflection = 'soft'
            self.node.reflection_scale = [1.8]
            self.xp_sound = 'hiss'
            #scale = 0.25
        elif bomb_type == 'gloo':
            tex = bs.gettexture('powerupIceBombs')
            mod = bs.getmesh('tnt')
            self.node.reflection = 'soft'
            self.node.reflection_scale = [0.23]
            scale = 0.50
        elif bomb_type == 'teleport':
            tex = bs.gettexture('aliColorMask')
            self.node.reflection = 'soft'
            self.node.gravity_scale = 0.5
            self.node.reflection_scale = [1.3]
        elif bomb_type == 'cosmic':
            tex = bs.gettexture('eggTex2')
            self.node.reflection = 'soft'
            self.node.gravity_scale = 0.5
            self.node.reflection_scale = [1.3]
            mat = ex.materials()[2]
            self.node.materials += (mat, )
        elif bomb_type == 'electro':
            tex = bs.gettexture('eggTex3')
            mod = bs.getmesh('flash') 
            #self.node.reflection = 'soft'
            #self.node.reflection_scale = [1.0]
            scale = 0.4
        elif bomb_type == 'blackhole':
            tex = bs.gettexture('rgbStripes')
            #mod = bs.getmesh('flash') 
            self.node.reflection = 'soft'
            self.node.reflection_scale = [0.0]
            self.blast_radius *= 3.0
            scale = 0.9
        elif bomb_type == 'curative':
            tex = bs.gettexture('powerupHealth')
            mod = bs.getmesh('shield')
            self.node.reflection = 'soft'
            self.node.reflection_scale = [1.4]
            scale = 0.25
        elif bomb_type == 'attraction':
            tex = bs.gettexture('achievementCrossHair')
            mat = ex.materials(self._attraction)[1], ex.materials()[2]
            self.node.materials += mat
        self.node.color_texture = tex
        self.node.mesh = mod
        self.bomb_type = bomb_type
        if scale is not None:
            bs.animate(self.node, 'mesh_scale',
                {0: 0, 0.2: 1.3 * scale, 0.26: scale})
    def _handle_impact(self) -> None:
        node = bs.getcollision().opposingnode
        node_delegate = node.getdelegate(object)
        if node:
            if (self.type == 'impact' and
                (node is self.owner or
                 (isinstance(node_delegate, ExBomb) and node_delegate.type
                  == 'impact' and node_delegate.owner is self.owner))):
                return
        self.handlemessage(bomb.ExplodeMessage())
    def arm(self) -> None:
        if self.bomb_type in ['land_mine', 'impact']:
            return super().arm()
    def explode(self) -> None:
        if self._exploded:
            return
        self._exploded = True
        if self.node:
            blast = ExBlast(position=self.node.position,
                            velocity=self.node.velocity,
                            blast_radius=self.blast_radius,
                            blast_type=self.bomb_type,
                            source_player=bs.existing(self._source_player),
                            hit_type=self.hit_type,
                            owner=self.owner,
                            hit_subtype=self.bomb_type).autoretain()
            for callback in self._explode_callbacks:
                callback(self, blast)
        if self.bomb_type == 'nitrogen':
            MiniZone(owner=self.owner,
                     position=self.node.position)
        elif self.bomb_type == 'stun':
            MiniZone(owner=self.owner, type='stun',
                     duration=8.0, color=(2.0 ,0.0 ,2.0),
                     radius=2.0, position=self.node.position)
        bs.timer(0.001, bs.WeakCall(self.handlemessage, bs.DieMessage()))
    def handlemessage(self, msg: Any) -> Any:
        if not self.node:
            return
        if isinstance(msg, _TouchMessage):
            if self.bomb_type == 'Xfactor':
                if hasattr(self, 'region'):
                    if self.region:
                        self.region.delete()
                self.xfactor_touch = True
                mat = ex.materials(self._xfactor)[1]
                bs.getsound('bunnyJump').play()
                self.region = bs.newnode('region',
                   owner=self.node,
                   attrs={'scale': [60.0 for s in range(3)],
                          'type': 'sphere',
                          'materials': [mat]})
                self.node.connectattr('position', self.region, 'position')
                v = self.node.velocity
                self.node.velocity = (v[0], v[1]+12, v[2])
            elif self.bomb_type == 'cosmic':
                def call(id: int):
                    extra = 1.33
                    self.blast_radius *= extra
                    scale = self.node.mesh_scale
                    bs.animate(self.node, 'mesh_scale',
                        {0: scale, 0.2: scale * extra})
                    bs.getsound('tick').play()
                def callback():
                    if self.owner:
                        p = self.node.position
                        ExtraPowerBox(self.owner, type='cosmic_box', position=p).autoretain()
                    self.handlemessage(
                        bomb.ExplodeMessage())
                if not getattr(self, '_countdown', None):
                    ex.timer_in_nodes(
                        position=(0.0, 0.47, 0.0),
                        time=ex.duration_cb,
                        node=self.node,
                        call=call,
                        callback=callback)
                    self._countdown = True
            elif self.bomb_type == 'attraction':
                if not hasattr(self, 'eff_attraction'):
                    self.eff_attraction = True
                    bs.getsound('laser').play()
        elif isinstance(msg, ExplodeMessage):
            node = bs.getcollision().opposingnode
            if self.owner != node:
                self.explode()
        elif isinstance(msg, ExplodeBombMessage):
            if self.bomb_type == 'blackhole':
                bs.getsound('explosion05').play()
            self.explode()
        else:
            if isinstance(msg, bomb.ExplodeMessage):
                if self.bomb_type != 'Xfactor' and not self.owner:
                    return self.handlemessage(ExplodeBombMessage())
                if self.xp_sound is not None:
                    bs.getsound(self.xp_sound).play()
                if self.bomb_type == 's.m.b':
                    ex.smb_eff(owner=self.owner, position=self.node.position)
                elif self.bomb_type == 'Xfactor':
                    return
                elif self.bomb_type == 'T784':
                    Tr784(owner=self.owner, position=self.node.position).autoretain()
                    ex.eco_sound('activateBeep')
                    return self.handlemessage(bs.DieMessage())
                elif self.bomb_type == 'gloo':
                    ex.eco_sound('hiss', 0.3)
                    GlooWall(owner=self.owner, position=self.node.position).autoretain()
                    return self.handlemessage(bs.DieMessage())
                elif self.bomb_type == 'blackhole':
                    if self.node and not self.node.sticky:
                        self.node.sticky = True
                        Portal(self.owner, self.node, self.node.position)
                        ex.eco_sound('shieldHit', 0.35)
                    return
                elif self.bomb_type == 'teleport':
                    if self.owner is not None:
                        self.owner.handlemessage(
                            bs.StandMessage(position=self.node.position))
                        self.owner.handlemessage(
                            bs.PowerupMessage(poweruptype='health'))
                    ex.fake_explosion(
                        position=self.node.position,
                        color=(1.2, 0.23, 0.23),
                        sound=False, radius=1.8)
                    ex.eco_sound('spawn', 0.3)
                    return self.handlemessage(bs.DieMessage())
            elif isinstance(msg, bomb.ImpactMessage):
                if self.bomb_type == 'cosmic':
                    return
            elif isinstance(msg, bs.HitMessage):
                if self.bomb_type == 'Xfactor':
                    return
            elif isinstance(msg, bs.DroppedMessage):
                if self.bomb_type == 'cosmic':
                    def call():
                        if self.node:
                            self.node.sticky = True
                    bs.timer(0.1, call)
            return super().handlemessage(msg)
    def _xfactor(self):
        node = bs.getcollision().opposingnode
        cls_node = node.getdelegate(object)
        team = ex.get_team(self._source_player)
        if self.owner != node:
            if node in team:
                return
        if self.owner == node or getattr(cls_node, '_dead', None):
            return
        x = 5.0
        node_vel = ex.getnodepos([node, self.node], x=x)
        dis = ex.getnodedis([self.node, node])
        if dis[0] <= 3.0:
            cls_node._pick_up(self.node)
            node.handlemessage('knockout', 2000.0)
            if cls_node.shield:
                if not getattr(cls_node, 'ex_super_shield', None):
                    cls_node.shield.delete()
                    cls_node.shield = None
                    bs.getsound('shieldDown').play()
        vel = (
            node_vel[0]  * 1.0 if dis[0] < 6 else node_vel[0] * 0.5,
            2.5,
            node_vel[2]  * 1.0 if dis[0] < 6 else node_vel[2] * 0.2)
        self.node.velocity = vel
    def _attraction(self):
        if getattr(self, 'eff_attraction', None):
            node = bs.getcollision().opposingnode
            if node == self.owner:
                ex.end_effect_attraction(self,
                    getattr(self, 'enemy', None))
            else:
                cls_node = node.getdelegate(object)
                ex.effect_attraction(self, cls_node)
                self.enemy = node

class GreenMiniBall(bs.Actor):
    def __init__(self,
                 owner: bs.Node = None,
                 enemy: bs.Node = None,
                 position: Sequence[float] = (0.0, 1.0, 0.0)):
        super().__init__()
        self.owner = owner
        self.enemy = enemy
        self.scale = scale = 0.15
        self.touch = 0
        shared = SharedObjects.get()
        mesh = bs.getmesh('shield')
        tex = bs.gettexture('eggTex2')
        mat1 = ex.materials(self.call)[1]
        mat2 = ex.materials()[4]
        mat3 = ex.materials()[2]
        position = (position[0], position[1]+0.5, position[2])
        self.node = bs.newnode('prop',
                owner=enemy,
                delegate=self,
                attrs={'body': 'sphere',
                       'mesh_scale': scale,
                       'body_scale': 0.35,
                       'position': position,
                       'mesh': mesh,
                       'shadow_size': 0.5,
                       'color_texture': tex,
                       'reflection': 'soft',
                       'reflection_scale': [1.4],
                       'materials': (mat1, mat2, mat3,
                                     shared.object_material)})
        bs.timer(5.0, bs.Call(self.handlemessage, bs.DieMessage()))
    def call(self):
        if self.touch != 0:
            self.touch = 0
            return
        self.touch += 1
        node = bs.getcollision().opposingnode
        cls_node = node.getdelegate(object)
        if getattr(cls_node, '_dead', None):
            return
        if self.owner == node:
            ex.health(cls_node, ex.max_cure_t784)
        else:
            if not node.invincible:
                mag = ex.damage_t784
                msg = bs.HitMessage(
                    srcnode=self.owner,
                    velocity=(0, 0, 0),
                    flat_damage=mag,
                    hit_subtype='T784')
                node.handlemessage(msg)
                PopupText(text='-'+str(msg.flat_damage)+'HP',
                  color=(0.8, 0.1, 0.1), scale=1.0,
                  random_offset=0.0, position=node.position).autoretain()
        self.handlemessage(bs.DieMessage())
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, _TouchMessage):
            if self.node:
                node_vel = ex.getnodepos([self.enemy, self.node], x=6.6)
                self.node.velocity = node_vel
                dis = ex.getnodedis([self.enemy, self.node])
                if dis[0] <= 1.0:
                    p1, p2 = self.node.position, self.enemy.position
                    bs.animate_array(self.node, 'position', 3, {0: p1, 0.05: p2})
        elif isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        else:
            super().handlemessage(msg)

class Tr784(bs.Actor):
    def __init__(self,
                 owner: bs.Node = None,
                 position: Sequence[float] = (0.0, 1.0, 0.0)):
        super().__init__()
        self.owner = owner
        self.touch = 0
        self.hitpoints = int(ex.Cosmic(owner, ex.hitpoints_t784))
        self.last_ball = None
        self._player = owner.source_player
        self.scale = scale = 0.75
        self.team = []
        self.nodes = []
        if self._player is not None:
            self.team = self._player.team.players
        mat3 = ex.materials()[4]
        shared = SharedObjects.get()
        mesh = bs.getmesh('powerup')
        tex = bs.gettexture('ouyaOButton')
        self.node = bs.newnode('prop',
                #owner=self.owner,
                delegate=self,
                attrs={'body': 'crate',
                       'body_scale': scale,
                       'position': position,
                       'mesh': mesh,
                       'shadow_size': 0.5,
                       'density': 9.0,
                       'color_texture': tex,
                       'reflection': 'soft',
                       'reflection_scale': [1.4],
                       'materials': (mat3,
                                     shared.footing_material,
                                     shared.object_material)})
        bs.animate(self.node, 'mesh_scale',
            {0: 0, 0.14: scale * 1.6, 0.20: scale})
        self.owner.add_death_action(
            bs.WeakCall(self.handlemessage, bs.DieMessage()))
        scale = ex.Cosmic(owner, ex.size_t784)
        self.loc_color = (0, 1, 6)
        self.loc = bs.newnode('locator',
            owner=self.node,
            attrs={'shape': 'circleOutline',
                   'color': self.loc_color,
                   'opacity': 0.3,
                   'size': [scale],
                   'draw_beauty': False,
                   'additive': False})
        self.node.connectattr('position', self.loc, 'position')
        self.region_scale(x=True)
        heart = bui.charstr(bui.SpecialChar.HEART)
        self.hp = Text(text=heart+str(self.hitpoints), node=self.node,
                       position=(0.0, 0.45, 0.0))
        ex.fake_explosion(radius=1.9, position=self.node.position)
    def region_scale(self, x: bool = False, e: bool = False):
        if not self.node:
            return
        if x:
            scale = ex.Cosmic(self.owner, ex.size_t784)
            mat1 = ex.materials(self.call)[1]
            self.region = bs.newnode('region',
                   owner=self.node,
                   attrs={'type': 'sphere',
                          'materials': [mat1]})
            self.node.connectattr('position', self.region, 'position')
            t = ex.cooldown_t784
            bs.animate_array(self.region, 'scale', 3,
                {0.00: tuple(scale*0.0 for s in range(3)),
                 t-0.01: tuple(scale*0.0 for s in range(3)),
                 t: tuple(scale*0.5 for s in range(3)),
                 t+0.01: tuple(scale*0.5 for s in range(3))}, loop=x)
        else:
            if self.region:
                self.region.delete()
        if e:
            """
            self.hitpoints -= 5
            heart = bui.charstr(bui.SpecialChar.HEART)
            self.hp.node.text = heart+str(self.hitpoints)
            if self.hitpoints <= 0:
                self.handlemessage(bs.DieMessage())
            """
    def call(self):
        node = bs.getcollision().opposingnode
        if len(self.nodes) == 0:
            bs.timer(0.01, self.shoot)
        if self.owner != node:
            if node in ex.get_team(self._player):
                return
        if node not in self.nodes:
            self.nodes.append(node)
            try:
                cls_node = node.getdelegate(object)
                if cls_node._dead:
                    self.nodes.remove(node)
            except: self.nodes.remove(node)
    def shoot(self):
        if not any(self.nodes):
            return
        if len(self.nodes) >= 2:
            if self.owner in self.nodes:
                self.nodes.remove(self.owner)
        node = self.nodes[0]        
        self.nodes.clear()
        if self.last_ball is not None:
            if not self.last_ball.node:
                self.last_ball = None
            else: return
        for player in self.team:
            if self.owner != node:
                if player.actor.node == node:
                    return
        try:
            self.last_ball = ball = GreenMiniBall(
                owner=self.owner, enemy=node,
                position=self.node.position).autoretain()
            self.update_pos(ball, node)
            self.region_scale(x=False)
            ball.node.add_death_action(
                    bs.Call(self.region_scale, x=True, e=self.owner != node))
            color = self.loc_color
            bs.animate_array(self.loc, 'color', 3,
                {0: color, 0.1: (1,0,0), 0.2: color})
            bs.getsound('corkPop').play()
        except Exception as e: pass
    def update_pos(self, ball: bs.Node, node: bs.Node):
        node_vel = ex.getnodepos([node, ball.node], x=6.6)
        ball.node.velocity = node_vel
    def dead(self):
        pos = self.node.position
        ex.fake_explosion(
            color=(2.0, 0.1, 0.1),
            radius=1.2, sound=True,
            position=pos)
        ExBomb(position=(pos[0], pos[1] + 0.5, pos[2]),
               velocity=(0.0, 8.0, 0.0),
               bomb_scale=1.0,
               bomb_type='Xfactor',
               blast_radius=2.0,
               owner=self.owner).autoretain()
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.dead()
                self.region.delete()
                self.node.delete()
        elif isinstance(msg, bs.HitMessage):
            ex.hitmessage(msg, delegate=self, reduction=0)
            if self.hp.node:
                heart = bui.charstr(bui.SpecialChar.HEART)
                self.hp.node.text = heart+str(self.hitpoints)
        else:
            super().handlemessage(msg)

class Smb(bs.Actor):
    def __init__(self,
                 angle: int = 0,
                 owner: bs.Node = None,
                 position: Sequence[float] = (0.0, 1.0, 0.0)):
        super().__init__()
        self.owner = owner
        self.scale = scale = ex.Cosmic(owner, 0.7)
        mat1 = ex.materials(self.call)[1]
        mat2 = ex.materials()[4]
        shared = SharedObjects.get()
        mesh = bs.getmesh('shield')
        texs = ['aliColorMask', 'aliColor', 'eggTex3', 'eggTex2']
        tex = bs.gettexture(texs[angle])
        cls_owner = owner.getdelegate(object)
        if cls_owner is not None:
            if getattr(cls_owner, 'cosmic_power', False):
                tex = bs.gettexture('aliColorMask')
        self.node = bs.newnode('prop',
                delegate=self,
                attrs={'body': 'sphere',
                       'body_scale': 4,
                       'position': position,
                       'mesh': mesh,
                       'shadow_size': 0.5,
                       'color_texture': tex,
                       'reflection': 'soft',
                       'reflection_scale': [1.3],
                       'materials': (mat1, mat2,
                                     shared.object_material)})
        bs.animate(self.node, 'mesh_scale',
            {0: 0, 0.14: scale * 1.6, 0.20: scale})
        self.direction(angle)
    def call(self):
        if not self.node:
            return
        node = bs.getcollision().opposingnode
        if self.owner == node:
            return
        vel = (self.node.velocity[0], 550, self.node.velocity[2])
        pos = [x*50 for x in self.node.position]
        pos[1] = -50
        vel = getattr(self.node, 'velocity', (0.0, 0.0, 0.0))
        if hasattr(node, 'hold_node'):
            node.hold_node = None
        def impulse():
            if self.node and node:
                ex.impulse(node,
                    bs.HitMessage(pos=pos,
                                  velocity=vel,
                                  magnitude=500 * 4,
                                  hit_subtype='s.m.b',
                                  radius=7840))
        def blast(ix: int | None = None, imp: float = 0.5):
            if node:
                p = node.position
                c = lambda: random.choice([0.1, 0.3, 0.5] + [-0.1, -0.3, -0.5])
                x = 0.5
                if ix == 0:
                    pos = (p[0], p[1]+x, p[2])
                elif ix == 1:
                    pos = (p[0], p[1]-x, p[2])
                else:
                    pos = (p[0], p[1]-0.3, p[2])
                ExBlast(owner=self.owner,
                        blast_radius=imp, blast_type='super_shield',
                        position=pos, velocity=node.velocity,
                        source_player=getattr(self.owner, 'source_player', None))
        blast()
        impulse()
        bs.timer(0.2, impulse)
        for n1, n2 in enumerate([0.8, 1.5]):
            bs.timer(n2, bs.Call(blast, n1, n2))
    def direction(self, angle: int):
        reduction = 44.44
        mypos = self.node.position
        dis = ex.calculate(18.0, 100 - reduction)
        duration = ex.calculate(1.3, 100 - reduction)
        myangle = [(mypos[0]+dis, mypos[1], mypos[2]),
                   (mypos[0]-dis, mypos[1], mypos[2]),
                   (mypos[0], mypos[1], mypos[2]+dis),
                   (mypos[0], mypos[1], mypos[2]-dis)][min(angle, 3)]
        bs.animate_array(self.node, 'position', 3,
            {0: mypos, duration: myangle})
        bs.timer(duration, bs.Call(self.handlemessage, bs.DieMessage()))
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        else:
            super().handlemessage(msg)

class MiniZone:
    def __init__(self,
                 type: str = 'freeze',
                 duration: float = 5.0,
                 radius: float = 1.5,
                 owner: bs.Node = None,
                 color: Sequence[float] = (0, 1.5, 1.5),
                 position: Sequence[float] = (0.0, 1.0, 0.0)):
        scale = radius
        self.type = type
        self.owner = owner
        self.hypothermic_material = ex.materials(self.call)[1]
        self.show_zone = bs.newnode('shield',
            owner=self.owner,
            attrs={'position': position,
                   'color': color,
                   'radius': scale})
        #bs.getsound('shieldUp').play()
        self.region = bs.newnode('region',
               owner=self.show_zone,
               attrs={'position': position,
                      'scale': [scale*0.6 for s in range(3)],
                      'type': 'sphere',
                      'materials': [self.hypothermic_material]})
        self.show_zone.connectattr('position', self.region, 'position')
        bs.timer(duration, self.end)
    def end(self):
        if self.show_zone:
            r = self.show_zone.radius
            bs.animate(self.show_zone, 'radius', {0: r, 0.1: 0})
            bs.timer(0.1, self.show_zone.delete)
    def call(self):
        node = bs.getcollision().opposingnode
        cls_node = node.getdelegate(object)
        if self.type == 'freeze':
            node.handlemessage(bs.FreezeMessage())
        elif self.type == 'stun':
            if isinstance(cls_node, Spaz): 
                ex.impulse(node,
                    bs.HitMessage(pos=self.show_zone.position,
                                  velocity=(0,0,0),
                                  magnitude=260,
                                  hit_subtype='stun',
                                  radius=560))
                bs.timer(0.0, lambda: node.handlemessage('knockout', 2000.0))
                bs.timer(1.5, lambda: node.handlemessage('knockout', 2000.0))
                ex.fake_explosion(
                    color=(1.0, 1.0, 2.0),
                    radius=0.8, sound=False,
                    position=node.position)
                bs.getsound('shieldHit').play()

class GlooWall(bs.Actor):
    def __init__(self,
                 owner: bs.Node = None,
                 position: Sequence[float] = (0.0, 0.7, 0.0)):
        super().__init__()
        self.owner = owner
        self.scale = scale = 2.550
        mat1 = ex.materials(self.call)[1]
        shared = SharedObjects.get()
        mesh = bs.getmesh('box')
        tex = bs.gettexture('bombColorIce')
        position = (position[0], position[1] + 1.0, position[2])
        self.node = bs.newnode('prop',
                delegate=self,
                attrs={'body': 'crate',
                       'body_scale': scale,
                       'position': position,
                       'mesh': mesh,
                       'density': 1.0,
                       'shadow_size': 0.0,
                       'color_texture': tex,
                       'reflection': 'soft',
                       'sticky': True,
                       'reflection_scale': [2.6],
                       'materials': [mat1, shared.footing_material]})
        bs.animate(self.node, 'mesh_scale',
            {0: 0, 0.14: scale * 1.6, 0.20: scale - 1.0})
        #ex.timer_in_nodes(self.node, time=ex.duration_gw)
        bs.timer(ex.duration_gw, bs.Call(self.handlemessage, bs.DieMessage()))
    def call(self):
        node = bs.getcollision().opposingnode
        cls_node = node.getdelegate(object)
        cls_node._pick_up(self.node)
        #node.handlemessage(bs.FreezeMessage())
    def _dead(self):
        ex.fake_explosion(
            color=(0.0, 0.0, 2.0),
            radius=1.9,
            position=self.node.position)
        bs.emitfx(position=self.node.position,
                  velocity=(0.0, 12.0, 0.0),
                  count=50,
                  spread=2.0,
                  scale=1.7,
                  chunk_type='ice')
        try: MiniZone(owner=None,
                      position=self.node.position)
        except Exception as e: print(e, '» 1382')
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self._dead()
                self.node.delete()
        else:
            super().handlemessage(msg)

class Text:
    
    def __init__(self,
                 text: str = '*',
                 position_type: str = 'position',
                 node: bs.Node = None,
                 scale: float = 1.0,
                 color: Sequence[float] = (1.0 ,1.0 ,1.0),
                 position: Sequence[float] = (0.0, 0.7, 0.0)):
        self.owner = node
        if node is None:
            return
        m = bs.newnode('math',owner=node,attrs={'input1':
            (position[0], position[1], position[2]),'operation': 'add'})
        node.connectattr(position_type, m, 'input2')
        if len(color) == 3:
            color = (color[0], color[1], color[2], 1.0)
        self.node = bs.newnode('text',owner=node,
                attrs={'text': text,
                      'in_world': True,
                      'scale': 0.02,
                      'shadow': 0.5,
                      'flatness': 1.0,
                      'color': color,
                      'h_align': 'center'}) 
        m.connectattr('output', self.node, 'position')
        bs.animate(self.node, 'scale', {0: 0.017*scale*0.8,0.4: 0.017*scale*0.8, 0.5: 0.01*scale})
    
    def _new_color(self):
        colors = [
            (1.0, 1.0, 0.0), (0.1, 1.0, 0.0),
            (1.0, 1.0, 0.5), (0.0, 1.0, 1.5)]
        c = self.node.color
        while(c):
            color = random.choice(colors)
            if color is not c: break
        bs.animate_array(self.node,
            'color', 3, {0: c, 0.1: color})

class ExtraPowerBox(bs.Actor):
    
    def __init__(self,
                 owner: bs.Node = None,
                 type: str = 'null',
                 position: Sequence[float] = (0.0, 1.0, 0.0)):
        super().__init__()
        self.type = type
        self.touch = False
        self.owner = owner
        self.player = owner.getdelegate(object)
        shared = SharedObjects.get()
        pieces = ex.hiperbox(type)
        pieces['scale'] *= 0.75
        self.powerup_material = ex.materials()[0]
        self.node = bs.newnode('prop',
            delegate=self,
            attrs={'body': 'box',
                   'position': position,
                   'mesh': pieces['mesh'],
                   'shadow_size': 0.5,
                   'color_texture': pieces['tex'],
                   'reflection': pieces['ref'],
                   'reflection_scale': [pieces['refs']],
                   'materials': (self.powerup_material,
                                 shared.object_material)})
        bs.animate(self.node, 'mesh_scale',
            {0: 0,
             0.14: pieces['scale'] * 1.6,
             0.20: pieces['scale']})
        self.owner.add_death_action(
            bs.Call(self.handlemessage, bs.DieMessage()))
        self.shield = bs.newnode('shield',
            owner=self.node,
            attrs={'radius': 0.8,
                   'hurt': 1-1.5,
                   'color': (0.0, 1.0, 0.0)})
        self.node.connectattr('position', self.shield, 'position')
    
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, pb._TouchedMessage):
            if self.touch:
                return
            try:
                node = bs.getcollision().opposingnode
                cls_node = node.getdelegate(object)
                team = ex.get_team(self.player)
                if self.owner == node or node in team:
                    self.touch = True
                    tex = self.node.color_texture
                    cls_node.ex_powerup_call(self.type)
                    cls_node._flash_billboard(tex)
                else: return
            except: return
            bs.getsound('powerup01').play(3,
                position=self.node.position)
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.DieMessage):
            if self.node:
                if msg.immediate:
                    self.node.delete()
                else:
                    mesh_scale = self.node.mesh_scale
                    bs.animate(self.node, 'mesh_scale',
                        {0: mesh_scale, 0.1: 0})
                    bs.timer(0.1, self.node.delete)
        else:
            return super().handlemessage(msg)

class Portal:
    
    def __init__(self,
                 owner: bs.Node = None,
                 node: bs.Node = None,
                 position: Sequence[float] = (0.0, 1.0, 0.0)):
        self.scale = scale = 6.0
        self.owner = owner
        self.node = node
        mat = ex.materials(self.call)[1]
        self.region = bs.newnode('region',
           owner=node,
           attrs={'scale': [scale*0.6 for s in range(3)],
                  'type': 'sphere',
                  'position': position,
                  'materials': [mat]})
        if node is not None:
            self.region.connectattr('position', node, 'position')
        self.shield = bs.newnode('shield', owner=self.region,
            attrs={'radius': scale, 'color': (0.5, 0.5, 0.5), 'hurt': 1-2.5})
        self.region.connectattr('position', self.shield, 'position')
        bs.timer(0.5, self.effect)
    
    def effect(self):
        def xp():
            self._sombra()
            self.node.handlemessage(ExplodeBombMessage())
        s = self.scale
        bs.animate(self.shield, 'radius', {0: s, 1.0: 0})
        bs.timer(1.0, xp)
    
    def call(self):
        node = bs.getcollision().opposingnode
        cls_node = node.getdelegate(object)
        if self.owner == node:
            return
        if node in ex.get_team(self.owner.source_player):
            return
        if self.node:
            cls_node._pick_up(self.node)
            node.handlemessage('knockout', 5000.0)
    
    def _sombra(self):
        cls_owner = self.owner.getdelegate(object)
        cls_owner._bots = BotSet()
        cls_owner._bots.owner = self.owner
        cls_owner._bots.spawn_bot(
            bot_type=bs.Call(SombritaBot,
                    source_player=self.owner.source_player),
            pos=self.node.position,
            spawn_time=1.0,
            on_spawn_call=None)
        self.owner.add_death_action(lambda:
            setattr(self, '_bots', None))

# === Bots ===

class SombritaBot(bots.BrawlerBot):
    run = True
    default_boxing_gloves = False
    character = 'Taobao Mascot'
    
    def __init__(self, **kwargs):
        super().__init__()
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.hitpoints = self.hitpoints_max = ex.sombrita_hp
        self.node.color, self.node.highlight = [(0.0, 0.0, 0.0)] * 2
        self.node.color_texture, self.node.color_mask_texture = [bs.gettexture('black')] * 2
        self.node.source_player = self.source_player
        self._punch_power_scale = 2.0
    
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            if self.node:
                if msg.immediate:
                    ex.fake_explosion(self.node.position,
                            sound=False, color=ex.get_random_color())
                return Spaz.handlemessage(self, msg)
        else:
            if isinstance(msg, PunchHitMessage):
                try:
                    node = bs.getcollision().opposingnode
                    if node.getnodetype() == 'spaz':
                        self._pick_up(node)
                except Exception as e:
                    print(type(e))
            return super().handlemessage(msg)

class BotSet(bots.SpazBotSet):
    node: bs.Node = None
    owner: bs.Node = None
    
    def _update(self) -> None:
        try:
            bot_list = self._bot_lists[self._bot_update_list] = ([
                b for b in self._bot_lists[self._bot_update_list] if b])
            self.node = bot_list[-1].node
        except Exception:
            bot_list = []
        self._bot_update_list = (self._bot_update_list +
                                 1) % self._bot_list_count
        player_pts = []
        nodes = ([] if not self.owner else ex.get_team(self.owner.source_player))
        nodes.append(self.node)
        for node in ex.getspazzes():
            try:
                cls = node.getdelegate(object)
                if node in nodes or cls._dead:
                    continue
                player_pts.append((bs.Vec3(node.position),
                                   bs.Vec3(node.velocity)))
            except Exception:
                pass
        for bot in bot_list:
            bot.set_player_points(player_pts)
            bot.update_ai()
        try:
            if not self.owner or not self.node:
                self._bot_update_timer = None
                self.node.handlemessage(bs.DieMessage(immediate=True))
        except:
            pass

# ================================================================================================================== #

class HiperBox(bs.Actor):
    
    def __init__(self,
                 type: str = 'null',
                 expire: bool = True,
                 position: Sequence[float] = (0.0, 1.0, 0.0)):
        super().__init__()
        self.type = type
        self.touch = 0
        shared = SharedObjects.get()
        self.pieces = pieces = ex.hiperbox(type)
        self.powerup_material = ex.materials()[0]
        self.node = bs.newnode('prop',
            delegate=self,
            attrs={'body': 'box',
                   'position': position,
                   'mesh': pieces['mesh'],
                   'shadow_size': 0.5,
                   'color_texture': pieces['tex'],
                   'reflection': pieces['ref'],
                   'reflection_scale': [pieces['refs']],
                   'materials': (self.powerup_material,
                                 shared.object_material)})
        bs.animate(self.node, 'mesh_scale',
            {0: 0,
             0.14: pieces['scale'] * 1.6,
             0.20: pieces['scale']})
        # === Effects ===
        self._effects()
        if expire:
            bs.timer(stg['powerup_time'] - 1.5,
                     bs.Call(pb.PowerupBox._start_flashing, self))
            bs.timer(stg['powerup_time'],
                     bs.Call(self.handlemessage, bs.DieMessage()))
    
    def _effects(self) -> None:
        self.anims()
        if stg['powerups_with_shield']:
            gw = stg['poweup_shield_glow']
            self.shield = bs.newnode('shield', owner=self.node, attrs={'radius': 1.1})
            self.shield.color = tuple(gw * (random.random()*1.0) for n in range(3))
            self.node.connectattr('position', self.shield, 'position')
        if stg['show_time']:
            def call(i: int):
                if getattr(self, 'shield', None):
                    self.shield.always_show_health_bar = True
                    self.shield.hurt = (1.0 - i / stg['powerup_time'])
            ex.timer_in_nodes(self.node, time=stg['powerup_time'], call=call)
        if stg['powerups_with_name']:
            self.name = Text(text=getlanguage(self.type),
                node=self.node, position=(0.0, 0.4, 0.0))
            self.name._new_color()
    
    def anims(self) -> None:
        anim = stg['powerup_animations']
        if anim == 'anim1':
            def c():
                if self.node:
                    self.node.velocity = (0.0, 0.0, 0.0)
            p = self.node.position
            bs.animate_array(self.node, 'position', 3,
                {0: (p[0]-5.5, p[1], p[2]), 0.2: p})
            bs.timer(0.21, c)
        elif anim == 'anim2':
            loc = bs.newnode('locator', owner=self.node,
            attrs={'shape': 'circleOutline',
                   'color': ex.get_random_color(x=1.5, mx=0.3),
                   'opacity': 1.0,
                   'draw_beauty': True,
                   'additive': False})
            self.node.connectattr('position', loc, 'position')
            bs.animate_array(loc, 'size', 1, {0: [0], 0.5: [7.0]})
            bs.animate(loc, 'opacity', {0: 1.0, 0.5: 0.0})
            bs.timer(0.5, loc.delete)
        elif anim == 'anim3':
            i = bui.charstr(bui.SpecialChar.DRAGON)
            text = PopupText(text=i, position=self.node.position, scale=5.0).autoretain()
            self.node.connectattr('position', text.node, 'position')
        elif anim == 'anim4':
            def c(tex: bs.Texture):
                if self.node:
                    self.node.color_texture = tex
            x = bs.gettexture
            textures = [x('black'), x('smoke'), x('eggTex2'), x('aliColorMask'), self.node.color_texture]
            for i, t in enumerate(textures * 3):
                bs.timer(0.1 * i, bs.Call(c, t))
    
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, pb._TouchedMessage):
            if self.touch: return
            self.touch = True
            try:
                node = bs.getcollision().opposingnode
                tex = self.pieces['tex']
                cls_node = node.getdelegate(object)
                cls_node.ex_powerup_call(self.type)
                cls_node._flash_billboard(tex)
            except: return
            bs.getsound('powerup01').play(3,
                position=self.node.position)
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.HitMessage):
            if stg['antibomb']:
                return
            if msg.hit_type != 'punch':
                self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.DieMessage):
            if self.node:
                if msg.immediate:
                    self.node.delete()
                else:
                    if stg['explosion_on_death']:
                        r = random.random
                        ex.fake_explosion(self.node.position,
                            sound=stg['sound_when_exploding'],
                            color=(r()*2, r()*2, r()*2))
                    mesh_scale = self.node.mesh_scale
                    bs.animate(self.node, 'mesh_scale',
                        {0: mesh_scale, 0.1: 0})
                    bs.timer(0.1, self.node.delete)
        else:
            return super().handlemessage(msg)
        
def new_map(self, vr_overlay_offset: Sequence[float] | None = None) -> None:
    calls['map'](self, vr_overlay_offset)
    activity = bs.getactivity()
    if not isinstance(activity, ExPowerupsActivity):
       # bs.timer(0.0, bs.Call(ex.spawn_hiperbox, self.defs))
        activity._ex_powerups_timer = bs.Timer(stg['powerup_time'], bs.Call(
            ex.spawn_hiperbox, self.defs), repeat=True)

# ======================= Session =========================================================================================== #

class ExPowerupsActivity(bs.Activity[bs.Player, bs.Team]):
    
    def on_transition_in(self) -> None:
        super().on_transition_in()
        map = 'Rampage'
        self._map_type = bs._map.get_map_class(map)
        self._map_type.preload()
        self._map = self._map_type()
        self.id = 1
        self.pows = list(dict(ex.pw2_register()))
        pos = (-9.595858573913574, 0.44612762331962585, -53.147159576416016, 10.304680824279785, -34.21335983276367, -44.984947204589844)
        self.globalsnode.area_of_interest_bounds = pos
        #bs.set_map_bounds(map_bounds)
        bs.setmusic(bs.MusicType.FORWARD_MARCH)
        self._pos = (0.0, 6.5, -5.0)
        self.spawnbox()
        self._generated()
    
    def spawnbox(self):
        self.powtype = powtype = self.pows[self.id]
        box = HiperBox(
            type=powtype,
            position=self._pos, expire=False).autoretain()
        box.node.is_area_of_interest = True
        box.node.add_death_action(self.spawnbox)
        self.box = box
        #bs.timer(2, self.kill_box)
    
    def box_delete(self):
        self.box.node.handlemessage(bs.DieMessage())
    
    def _generated(self):
        from bascenev1lib.actor.text import Text
        from bascenev1lib.actor.image import Image
        des = 'attr_' + self.powtype
        data = ex.hiperbox(self.powtype)
        self.nodes = [
            Text(text=getlanguage(des), position=(-380.0, 300.0), transition=Text.Transition.FADE_IN, h_align=Text.HAlign.LEFT).autoretain(),
            Image(texture=data['tex'], position=(-430.0, 300.0), scale=(60.0, 60.0), mesh_opaque=bs.getmesh('image1x1')).autoretain(),
            Text(text=getlanguage(self.powtype), position=(-480.0, 300.0), color=(ex.get_random_color(x=1.5, mx=0.8) + (1.0, )), transition=Text.Transition.FADE_IN, h_align=Text.HAlign.RIGHT).autoretain(),
            Image(texture=bs.gettexture('buttonPunch'), position=(-650.0, 200.0), scale=(70.0, 70.0), color=(1.0, 0.7, 0.0, 0.8)).autoretain(),
            Text(text=getlanguage('act.button.punch'), position=(-600.0, 200.0 - 15.0), color=(1.0, 1.0, 1.0, 0.8), h_align=Text.HAlign.LEFT).autoretain(),
            Image(texture=bs.gettexture('buttonPickUp'), position=(-650.0, 100.0), scale=(70.0, 70.0), color=(0.2, 0.6, 1.0, 0.8)).autoretain(),
            Text(text=getlanguage('ow.switches'), position=(-600.0, 100.0 - 15.0), color=(1.0, 1.0, 1.0, 0.8), h_align=Text.HAlign.LEFT).autoretain(),            
            Image(texture=bs.gettexture('buttonBomb'), position=(-650.0, 0.0), scale=(70.0, 70.0), color=(1.0, 0.3, 0.3, 0.8)).autoretain(),
            Text(text=getlanguage('ow.changes'), position=(-600.0, 0.0 - 15.0), color=(1.0, 1.0, 1.0, 0.8), h_align=Text.HAlign.LEFT).autoretain(),
            Image(texture=bs.gettexture('buttonJump'), position=(-650.0, -100.0), scale=(70.0, 70.0), color=(0.1, 1.0, 0.1, 0.8)).autoretain(),
            Text(text=getlanguage('act.button.jump'), position=(-600.0, -100.0 - 15.0), color=(1.0, 1.0, 1.0, 0.8), h_align=Text.HAlign.LEFT).autoretain(),
        ]
        self.nodes[1].node.mask_texture = bs.gettexture('characterIconMask')
    
    def _regenerated(self):
        for t in self.nodes:
            t.node.delete()
        with self.context:
            self._generated()
    
    def kill_box(self):
        if self.box:
            self.box.handlemessage(
                bs.DieMessage())
    
    def _press(self, type: bs.InputType):
        if type is bs.InputType.LEFT_PRESS:
            self.id -= 1
            if self.id < 0:
                self.id = len(self.pows) - 1
            self.box.node.delete()
            self._regenerated()
        elif type is bs.InputType.RIGHT_PRESS:
            self.id += 1
            if self.id >= len(self.pows):
                self.id = 0
            self.box.node.delete()
            self._regenerated()
        elif type is bs.InputType.PUNCH_PRESS:
            self.box_delete()
        elif type is bs.InputType.PICK_UP_PRESS:
            GLOBAL['Tab'] = 'ow.switches'
            with bs.ContextRef.empty():
                # window(transition='in_scale')
                bs.app.ui_v1.set_main_window(
                    BoxWindow(), is_top_level=True, suppress_warning=True
                )
        elif type is bs.InputType.BOMB_PRESS:
            GLOBAL['Tab'] = 'ow.changes'
            with bs.ContextRef.empty():
                # window(transition='in_scale')
                bs.app.ui_v1.set_main_window(
                    BoxWindow(), is_top_level=True, suppress_warning=True
                )
        elif type is bs.InputType.JUMP_PRESS:
            with bs.ContextRef.empty():
                AnimationsWindow()
        bs.getsound('click01').play()

class ExPowerupsSession(bs.Session):
    """Session that runs the main menu environment."""
    
    def __init__(self) -> None:
        self._activity_deps = bs.DependencySet(bs.Dependency(ExPowerupsActivity))
        super().__init__([self._activity_deps])
        self.setactivity(bs.newactivity(ExPowerupsActivity))
    
    def on_player_request(self, player: bs.SessionPlayer) -> bool:
        # Reject all player requests.
        a = bs.get_foreground_host_activity()
        c_id = player.inputdevice.client_id
        if c_id != -1:
            bs.broadcastmessage(getlanguage('Only.Host'),
                color=(0.8, 0.0, 0.0),
                clients=[c_id],
                transient=True)
            return False
        ITs = [bs.InputType.UP_PRESS,
               bs.InputType.DOWN_PRESS,
               bs.InputType.LEFT_PRESS,
               bs.InputType.RIGHT_PRESS,
               bs.InputType.PICK_UP_PRESS,
               bs.InputType.BOMB_PRESS,
               bs.InputType.JUMP_PRESS,
               bs.InputType.PUNCH_PRESS]
        for IT in ITs:
            player.assigninput(IT, bs.Call(a._press, IT))
        return True
    
    def on_player_leave(self, sessionplayer: bs.SessionPlayer) -> None:
        return
    
    def end(self):            
        bs.fade_screen(False, time=0.5,
            endcall=bs.Call(bs.new_host_session, MainMenuSession))
    
    def _request_player(self, sessionplayer: bs.SessionPlayer) -> bool:
        if self._ending:
            return False
        # Ask the bs.Session subclass to approve/deny this request.
        try:
            with self.context:
                result = self.on_player_request(sessionplayer)
        except Exception:
            result = False
        return result

# ======================= Windows =========================================================================================== #

class BoxWindow(bui.MainWindow):
    
    def __init__(self, transition='in_right', origin_widget: bui.Widget | None = None):
        columns = 2
        self._width = width = 800
        self._height = height = 500
        self._sub_height = 200
        self._scroll_width = self._width*0.90
        self._scroll_height = self._height - 180
        self._sub_width = self._scroll_width*0.95
        self.roster = bs.get_game_roster()
        self.tab_buttons = {}
        self.pys_data = []
        self.tabdefs = {"Action 1": ['settingsIcon',(0.5,1.0,0.5)],
                        "Action 2": ['achievementEmpty', (1,1,1)],
                        #"Action 3": ['folder',(0.9,0.9,0)],
                        "About": ['heart', (0.9,0,0)]}
        self.listdef = list(self.tabdefs)
        self.count = len(self.tabdefs) - 1
        self._current_tab = GLOBAL['Tab']
        app = bui.app.ui_v1
        uiscale = app.uiscale

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width+90,height+80),
                scale=1.5 if uiscale is bui.UIScale.SMALL else 1.0,
                stack_offset=(0,-30) if uiscale is bui.UIScale.SMALL else  (0,0),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        if ex.in_expw_activity():
            self.tabdefs.clear()
            self.listdef = list(self.tabdefs)
            self.count = len(self.tabdefs) - 1
            # -->
            bui.containerwidget(edit=self._root_widget, background=False)
        self._back_button = b = bui.buttonwidget(
            parent=self._root_widget,autoselect=True,
            position=(60,self._height-15),size=(130,60),
            scale=0.8,text_scale=1.2,label=bui.Lstr(resource='backText'),
            button_type='back',on_activate_call=self.main_window_back)
        
        bui.buttonwidget(edit=self._back_button, button_type='backSmall',size=(60, 60),label=bui.charstr(bui.SpecialChar.BACK))
        bui.containerwidget(edit=self._root_widget,cancel_button=b)

        self.titletext = bui.textwidget(parent=self._root_widget,position=(0, height-15),size=(width,50),
                          h_align="center",color=bui.app.ui_v1.title_color, text='titletext', v_align="center",maxwidth=width*1.3)
        
        if not ex.in_expw_activity():
            icon = bui.gettexture('nub')
            color = (0.54, 0.2, 1.0)
            btn = bui.buttonwidget(parent=self._root_widget,autoselect=True,
                       position=(10.0, self._height-(80*1)),size=(60, 60),
                       scale=0.8,text_scale=1.2,label='', button_type='square',
                       color=(0.2, 1.0, 0.2), texture=icon,
                       mesh_opaque=bui.getmesh('image1x1'),
                       mask_texture=bui.gettexture('characterIconMask'),
                       on_activate_call=bs.Call(self.btn_nub_call, 1))
            btn = bui.buttonwidget(parent=self._root_widget,autoselect=True,
                       position=(10.0, self._height-(80*2)),size=(60, 60),
                       scale=0.8,text_scale=1.2,label='', button_type='square',
                       color=(1.0, 0.2, 0.2), texture=icon,
                       mesh_opaque=bui.getmesh('image1x1'),
                       mask_texture=bui.gettexture('characterIconMask'),
                       on_activate_call=bs.Call(self.btn_nub_call, 2))
        index = 0
        for tab in range(self.count):
            for tab2 in range(columns):
                tag = self.listdef[index]
                position = (620+(tab2*120),self._height-50*2.5-(tab*120))
                text = {'About':
                            bui.Lstr(resource='gatherWindow.aboutText')
                        }.get(tag, getlanguage(tag))
                self.tab_buttons[tag] = bui.buttonwidget(parent=self._root_widget,autoselect=True,
                                        position=position,size=(110, 110),
                                        scale=1,label='',enable_sound=False,
                                        button_type='square',on_activate_call=bs.Call(self._set_tab,tag,sound=True))
                self.text = bui.textwidget(parent=self._root_widget,
                            position=(position[0]+55,position[1]+30),
                            size=(0, 0),scale=1,color=bui.app.ui_v1.title_color,
                            draw_controller=self.tab_buttons[tag],maxwidth=100,
                            text=text,h_align='center',v_align='center')
                self.image = bui.imagewidget(parent=self._root_widget,
                             size=(60,60),color=self.tabdefs[tag][1],
                             draw_controller=self.tab_buttons[tag],
                             position=(position[0]+25,position[1]+40),
                             texture=bui.gettexture(self.tabdefs[tag][0]))
                index += 1
                if index > self.count:
                    break
            if index > self.count:
                break
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget, position=(self._width*0.08,51*1.8),
            size=(self._sub_width -140,self._scroll_height +60*1.2),
            selection_loops_to_parent=True)
        self._tab_container = None
        self._set_tab(self._current_tab)
    
    def _set_tab(self, tab, sound: bool = False):
        self.sound = sound
        GLOBAL['Tab'] = tab
        if tab != "About":
            text = getlanguage(tab)
        else: text = bui.Lstr(resource='gatherWindow.aboutText')
        bui.textwidget(edit=self.titletext, text=text)
        if self._tab_container is not None and self._tab_container:
            self._tab_container.delete()
        if self.sound:
            bui.getsound('click01').play()
        if tab == 'Action 1':
            exs = [s for s, r in ex.pw2_register()]
            sub_height = (len(exs) * 205) + 20
            v = sub_height - 55
            width = 300
            self._tab_container = c = bui.containerwidget(parent=self._scrollwidget,
                size=(self._sub_width,sub_height),
                background=False,selection_loops_to_parent=True)
            v -= 40
            for num, pwx in enumerate(exs):
                max = 210.0
                tex = ex.hiperbox(pwx, in_ui=True)['tex']
                ccolor = (0.25, 0.24, 0.25) #ex.get_random_color(x=0.9, m=3)
                bui.containerwidget(parent=c,position=(7.0, v-60-(max*num)),
                    color=ccolor,scale=1.3,size=(390, 110),background=True)
                i = bui.imagewidget(parent=c,
                     size=(80, 80),
                     mask_texture=bui.gettexture('characterIconMask'),
                     mesh_opaque=bui.getmesh('image1x1'),
                     position=(30.0, v-25-(max*num)), texture=tex)
                t = bui.textwidget(parent=c,position=(80, v+15-(max*num)),size=(width,50), scale=1.2,
                    h_align="center", color=(0, 1, 0), text=getlanguage(pwx), v_align="center",maxwidth=width*0.7)
                tn = bui.textwidget(parent=c,position=(274, v-5-(max*num)),size=(width, 50), scale=1.0,
                    h_align="center", color=(0, 1, 0), text=str(cfg[pwx]), v_align="center",maxwidth=width*1.3)
                info_b = bui.buttonwidget(parent=c,autoselect=True, color=(0.3,0.7,1.0),
                                position=(160, v-45-(max*num)), size=(476, 140),
                                scale=0.4,label=getlanguage('+info'),text_scale=2.8,
                                on_activate_call=bs.Call(self._powerups_info, pwx))
                dipos = 0
                for direc in ['-', '+']:
                    bui.buttonwidget(parent=c,autoselect=True,
                                position=(405.0, v-45-(max*num) + dipos), size=(100,100),
                                repeat=True,scale=0.4,label=direc,button_type='square',text_scale=4,
                                on_activate_call=bs.Call(self._expowerups, direc, pwx))
                    dipos += 85
        elif tab == 'Action 2':
            GLOBAL['Tab'] = "Action 1"

            if not self.main_window_has_control():
                return

            self.main_window_replace(
                OptionsWindow(origin_widget=self.tab_buttons[tab], size=(800.0, 800.0))
            )
            # bui.containerwidget(edit=self._root_widget, transition='out_scale')
            return
        elif tab == 'ow.changes':
            sub_height = 0
            v = sub_height - 55
            width = 300
            self._tab_container = c = bui.columnwidget(
                parent=self._scrollwidget, left_border=-10, border=20)
            data = [
                ['ow.changes.time_powerup', bs.Call(Windowscito, value='powerup_time', config=stg, max=[3, 1, 15])],
                ['ow.changes.poweup_shield_glow', bs.Call(Windowscito, value='poweup_shield_glow', config=stg, max=[1.0, 0.1, 3.5])],
                ]
            for txt in data:
                t = bui.textwidget(parent=c, size=(width*1.6, 20), scale=1.0, selectable=True, corner_scale=1.25,
                    h_align="left", text=getlanguage(txt[0]), v_align="center",maxwidth=width*1.3,
                    click_activate=True, color=(0.1, 1.0, 0.1), on_activate_call=txt[1])
        elif tab == 'ow.switches':
            sub_height = 0
            v = sub_height - 55
            width = 300
            self._tab_container = c = bui.columnwidget(
                parent=self._scrollwidget,
                left_border=-25, border=15)
            data = [
                ['allow_powerups_in_bots', 'allow_in_bots'],
                ['powerups_with_shield', 'ow.switches.powerups_with_shield'],
                ['explosion_on_death', 'ow.switches.explosion_on_death'],
                ['show_time', 'ow.switches.show_time'],
                ['powerups_with_name', 'ow.switches.powerups_with_name'],
                ['antibomb', 'ow.switches.antibomb'],
                ]
            if stg['explosion_on_death']:
                data.insert(3, ['sound_when_exploding', 'ow.switches.sound_when_exploding'])
            for i, ck in enumerate(data):
                color = (None if ck[0] != 'sound_when_exploding' else (0.2, 0.6, 0.9))
                check = bui.checkboxwidget(parent=c, textcolor=color,
                    value=stg[ck[0]],maxwidth=width*1.3,
                    on_value_change_call=bs.Call(self._switches, ck[0]),
                    text=getlanguage(ck[1]),autoselect=True)
        else:
            sub_height = 0
            v = sub_height - 55
            width = 300
            self._tab_container = c = bui.containerwidget(parent=self._scrollwidget,
                size=(self._sub_width,sub_height),
                background=False,selection_loops_to_parent=True)
            t = bui.textwidget(parent=c,position=(110, v-20),size=(width,50),
                      scale=1.4,color=(1.2,0.2,1.2),h_align="center",v_align="center",
                      text="EX Powerups - V1.2.6",maxwidth=width*30, big=True)
            t = bui.textwidget(parent=c,position=(110, v-90),size=(width,50),
                      scale=1,color=(1.3,0.5,1.0),h_align="center",v_align="center",
                      text=getlanguage('Creator'),maxwidth=width*30)
            exs = len(ex.pw2_register())
            t = bui.textwidget(parent=c,position=(110, v-180),size=(width,50),
                      scale=1,color=(1.0,1.2,0.3),h_align="center",v_align="center",
                      text=getlanguage('Mod Info', [exs]),maxwidth=width*30)
        for select_tab,button_tab in self.tab_buttons.items():
            if select_tab == tab:
                bui.buttonwidget(edit=button_tab,color=(0.5,0.4,1.5))
            else: bui.buttonwidget(edit=button_tab,color=(0.52,0.48,0.63))
    
    def btn_nub_call(self, val: int):
        if val == 1:
            del apg['ex_pow_settings']
            apply()
        else:
            for pow in apg['ex_pow_settings']:
                apg['ex_pow_settings'][pow] = 0
        self._set_tab(GLOBAL['Tab'])
    
    def _powerups_info(self, val: str = '???'):
        t = (getlanguage('category-1') if 'bomb' in val else
             getlanguage('category-2'))
        t += ('\n' + getlanguage('attributes') + ' ' +
             getlanguage('attr_%s' % val))
        ConfirmWindow(text=t, cancel_button=False, text_scale=3.0, width=560.0, height=140.0)
    
    def _expowerups(self, res: str, val: str):
        n1 = 7
        if res == '+':
            if cfg[val] < n1:
                cfg[val] += 1
            else: cfg[val] = 0
        else:
            if cfg[val] > 0:
                cfg[val] -= 1
            else: cfg[val] = n1
        apg.apply_and_commit()
        self._set_tab(GLOBAL['Tab'])
    
    def _switches(self, setg: str, x):
        stg[setg] = False if x==0 else True
        apg.apply_and_commit()
        if setg == 'explosion_on_death':
            bui.apptimer(0.1, bs.Call(self._set_tab, GLOBAL['Tab']))

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

class Windowscito(PopupWindow):

    def __init__(self,
                 value: str = '',
                 config: dict = {},
                 round: int = 2,
                 max: list[float] = [1, 1, 10]):
        self.value = value
        self.max = max
        self.round = round
        self.config = config
        m = 5.0
        bgc = (0.5, 0.25, 0.5)
        size = (70.0 * m, 70.0 * m)
        sc = 1.0 if bui.app.ui_v1.uiscale is bui.UIScale.SMALL else 0.6
        PopupWindow.__init__(self,
            position=(0.0, 0.0),
            size=size, scale=sc,
            bg_color=bgc)
        rw = self.root_widget
        cancel_btn = bui.buttonwidget(parent=rw,
            autoselect=True, color=(0.83, 0.33, 0.33),
            position=(size[0]*0.1, size[1]*0.8), size=(40, 40),
            scale=1.0, label='', icon=bui.gettexture('crossOut'),
            on_activate_call=self.on_popup_cancel)
        bui.containerwidget(edit=self.root_widget, cancel_button=cancel_btn)
        self.num_text = bui.textwidget(parent=rw,position=(size[0]*0.35, size[1]*0.5),
            size=(size[0]*0.31,50), scale=2.3,
            color=(0.11, 1.0, 0.11),h_align="center",v_align="center",
            text=f"{config[value]}/{max[2]}",maxwidth=size[0]*0.35*30)
        _x = -10
        btn = bui.buttonwidget(parent=rw,
            autoselect=True, color=(1.0, 0.0, 0.0), repeat=True,
            position=(_x+size[0]*0.3, size[1]*0.1), size=(50, 50),
            scale=1.5, label='-', button_type='square',
            on_activate_call=bs.Call(self._call, '-'))
        btn = bui.buttonwidget(parent=rw,
            autoselect=True, color=(0.0, 0.4, 1.0), repeat=True,
            position=(_x+(size[0]*0.3)*1.85, size[1]*0.1), size=(50, 50),
            scale=1.5, label='+', button_type='square',
            on_activate_call=bs.Call(self._call, '+'))
    
    def _call(self, type: str) -> None:
        cf = self.config
        n = self.config[self.value]
        if type == '+':
            m = self.max[2]
            if n >= m:
                self.config[self.value] = self.max[0]
            else:
                self.config[self.value] += self.max[1]
        else:
            m = self.max[0]
            if n <= m:
                self.config[self.value] = self.max[2]
            else:
                self.config[self.value] -= self.max[1]
        self.config[self.value] = round(self.config[self.value], self.round)
        bui.app.config.apply_and_commit()
        v = self.config[self.value]
        bui.textwidget(edit=self.num_text, text=f"{v}/{self.max[2]}")
    
    def on_popup_cancel(self) -> None:
        bui.containerwidget(edit=self.root_widget, transition='out_scale')

class AnimationsWindow(PopupWindow):
    
    def __init__(self):
        from bauiv1lib.radiogroup import make_radio_group
        m = 10.0
        bgc = (0.4, 0.4, 0.5)
        size = (70.0 * m, 70.0 * m)
        self._width = size[0] * 0.38
        self._height = size[1]
        maxwidth = size[0] * 0.55
        sc = 1.0 if bui.app.ui_v1.uiscale is bui.UIScale.SMALL else 0.6
        PopupWindow.__init__(self,
            position=(0.0, 0.0),
            size=size, scale=sc,
            bg_color=bgc)
        rw = self.root_widget
        cancel_btn = bui.buttonwidget(parent=rw,
            autoselect=True, color=(0.83, 0.33, 0.33),
            position=(size[0]*0.05, size[1]*0.9), size=(40*1.3, 40*1.3),
            scale=1.0, label='', icon=bui.gettexture('crossOut'),
            button_type='backSmall', on_activate_call=self.on_popup_cancel)
        bui.containerwidget(edit=self.root_widget, cancel_button=cancel_btn)
        self.title_text = bui.textwidget(
            position=(self._width+80, self._height-40),
            size=(0, 0), scale=1.5, parent=rw,
            color=(0.75, 1.0, 0.7), maxwidth=maxwidth,
            text=getlanguage('act.button.jump'),
            h_align='center', v_align='center')
        self._scrollwidget = bui.scrollwidget(
            parent=rw,
            position=(40, 60),
            highlight=False,
            size=(size[0] * 0.9,
                  size[1] * 0.8))
        self._columnwidget = bui.columnwidget(
            parent=self._scrollwidget,
            left_border=23, border=20)
        data = {}
        data2 = [
           'Auto', 'anim1', 'anim2', 'anim3', 'anim4',
            ]
        for i in data2:
            txt = ('act.' + i if not i == 'Auto' else i)
            cbox = bui.checkboxwidget(parent=self._columnwidget,
                    size=(200, 40),
                    text=getlanguage(txt),
                    maxwidth=maxwidth,
                    scale=2.0)
            data[i] = cbox
        make_radio_group(tuple(data.values()), tuple(data.keys()), stg['powerup_animations'],
                         self._movement_changed)
    
    def _movement_changed(self, v: str) -> None:
        stg['powerup_animations'] = v
        apg.apply_and_commit()
    
    def on_popup_cancel(self) -> None:
        bui.containerwidget(edit=self.root_widget, transition='out_scale')

class OptionsWindow(bui.MainWindow):

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
        size: tuple[float, float] = (800.0, 800.0),
    ):
        bgc = (0.23, 0.22, 0.5)
        sc = 1.0 if bui.app.ui_v1.uiscale is bui.UIScale.SMALL else 0.6

        super().__init__(
            root_widget=bui.containerwidget(
                size=size,
                scale=sc,
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        self._back_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(50, size[1] - 88),
            size=(60, 60),
            scale=1.3,
            autoselect=True,
            label=bui.charstr(bui.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self.main_window_back,
        )
        bui.containerwidget(
            edit=self._root_widget, cancel_button=self._back_button
        )

        btn_size = (size[0] * 0.8, 100)
        dis = 0.8
        gt = bui.gettexture
        self._width = size[0] * 0.38
        self._height = size[1]
        maxwidth = size[0] * 0.55
        self._r = 'mainMenu'
        self.buttons = list()
        self.title_text = bui.textwidget(
            parent=self._root_widget,
            position=(self._width+80, self._height-40),
            size=(0, 0), scale=1.5,
            color=(0.75, 1.0, 0.7),
            maxwidth=maxwidth,
            text=getlanguage('Action 2'),
            h_align='center',
            v_align='center')
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(40, 60),
            highlight=False,
            #color=(0.35, 0.55, 0.15),
            size=(size[0] * 0.9,
                  size[1] * 0.8))
        self._columnwidget = bui.columnwidget(
            parent=self._scrollwidget,
            left_border=23, border=20)
        buttons = [
            [gt('settingsIcon'), 'ow.changes'],
            [gt('settingsIcon'), 'ow.switches'],
            [gt('star'), 'ow.activity']
            ]
        for i, b in enumerate(buttons):
            self.buttons.append(
                bui.buttonwidget(
                    parent=self._columnwidget,
                    autoselect=True, color=(0.33, 0.33, 1.0),
                    position=(60, self._height-15), size=(220*1.85, 60),
                    scale=1.5, label=getlanguage(b[1]), icon=b[0],
                    text_scale=1.5, iconscale=1.5,
                    on_activate_call=bs.Call(self._calls, b[1]))
                )
    
    def _calls(self, tab: str):
        if tab == 'ow.activity':
            ex.enter_the_expw_activity()
        else:
            GLOBAL['Tab'] = tab
            self.main_window_back()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

# ================================================================================================================== #

# def add_plugin():
#     try: from baBearModz import BearPlugin
#     except Exception as e:
#         return bui.apptimer(2.5, lambda e=e:
#                bui.screenmessage(f'Error Plugin <{__name__}> {e}', (1,0,0)))
#     BearPlugin(icon='powerupStickyBombs',
#                creator='@PatrónModz',
#                button_color=(0.25, 1.05, 0.05),
#                plugin=ExPowerups,
#                window=BoxWindow)
    
def plugin():
    calls['drop_bomb'] = Spaz.drop_bomb
    calls['map'] = bs.Map.__init__
    calls['hitmessage'] = bs.HitMessage.__init__
    Spaz.drop_bomb = ex.drop_bomb
    Spaz.ex_powerup_call = ex.powerup_call
    bs.Map.__init__ = new_map
    bs.HitMessage.__init__ = ex.new_init_hitmessage

# ba_meta export plugin
class ExPowerups(bs.Plugin):
    global ex
    ex = Builder
    
    def on_app_running(self):
        apply()
        plugin()
        # add_plugin()

    def has_settings_ui(self) -> bool:
        return True

    def show_settings_ui(self, source_widget: Any | None) -> None:
        bs.app.ui_v1.get_main_window().main_window_replace(
            BoxWindow(origin_widget=source_widget)
        )