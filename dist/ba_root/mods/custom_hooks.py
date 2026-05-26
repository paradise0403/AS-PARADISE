"""Custom hooks to pull of the in-game functions."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

# pylint: disable=import-error
# pylint: disable=import-outside-toplevel
# pylint: disable=protected-access

from __future__ import annotations

import _thread
import importlib
import logging
import os
import time
from datetime import datetime

import _babase
from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
import _bascenev1
from baclassic._appmode import ClassicAppMode
import bauiv1 as bui
import setting
from baclassic._servermode import ServerController
from bascenev1._activitytypes import ScoreScreenActivity
from bascenev1._map import Map
from bascenev1._session import Session
from bascenev1lib.activity import dualteamscore, multiteamscore, drawscore
from bascenev1lib.activity.coopscore import CoopScoreScreen
from bascenev1lib.actor import playerspaz
from chathandle import handlechat
from features import map_fun
from features import team_balancer, afk_check, dual_team_score as newdts
from features import text_on_map, announcement
from features import votingmachine
from playersdata import pdata
from serverdata import serverdata
from spazmod import modifyspaz
from stats import mystats
from tools import account
import ender
import coin_system
from tools import notification_manager
from tools import servercheck, server_update, logger, playlist, servercontroller

if TYPE_CHECKING:
    from typing import Any

settings = setting.get_settings_data()


def filter_chat_message(msg: str, client_id: int) -> str | None:
    """Returns all in game messages or None (ignore's message)."""
    return handlechat.filter_chat_message(msg, client_id)


# ba_meta export babase.Plugin
class modSetup(babase.Plugin):
    def on_app_running(self):
        """Runs when app is launched."""
        plus = bui.app.plus
        bootstraping()
        servercheck.checkserver().start()
        server_update.check()
        # bs.apptimer(5, account.updateOwnerIps)
        if settings["afk_remover"]['enable']:
            afk_check.checkIdle().start()
        if (settings["useV2Account"]):

            if (plus.get_v1_account_state() ==
                    'signed_in' and plus.get_v1_account_type() == 'V2'):
                logging.debug("Account V2 is active")
            else:
                logging.warning("Account V2 login require ....stay tuned.")
                bs.apptimer(3, babase.Call(logging.debug,
                                           "Starting Account V2 login process...."))
                bs.apptimer(6, account.AccountUtil)
        else:
            plus.accounts.set_primary_credentials(None)
            plus.sign_in_v1('Local')
        bs.apptimer(60, playlist.flush_playlists)

    # it works sometimes , but it blocks shutdown so server raise runtime
    # exception,   also dump server logs
    def on_app_shutdown(self):
        print("Server shutting down , lets save cache")
        # lets try  threading here
        # _thread.start_new_thread(pdata.dump_cache, ())
        # _thread.start_new_thread(notification_manager.dump_cache, ())
        # print("Done dumping memory")


def score_screen_on_begin(func) -> None:
    """Runs when score screen is displayed."""

    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)  # execute the original method
        team_balancer.balanceTeams()
        mystats.update(self._stats)
        announcement.showScoreScreenAnnouncement()
        return result

    return wrapper


ScoreScreenActivity.on_begin = score_screen_on_begin(
    ScoreScreenActivity.on_begin)


def on_map_init(func):
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        text_on_map.textonmap()
        modifyspaz.setTeamCharacter()

    return wrapper


Map.__init__ = on_map_init(Map.__init__)


def playerspaz_init(playerspaz: bs.Player, node: bs.Node, player: bs.Player):
    """Runs when player is spawned on map."""
    modifyspaz.main(playerspaz, node, player)


def bootstraping():
    """Bootstarps the server."""
    logging.warning("Bootstraping mods...")
    # server related

    # check for auto update stats
    _thread.start_new_thread(mystats.refreshStats, ())
    pdata.load_cache()
    _thread.start_new_thread(pdata.dump_cache, ())
    _thread.start_new_thread(notification_manager.dump_cache, ())

    # import plugins
    if settings["mikirogQuickTurn"]["enable"]:
        from plugins import wavedash  # pylint: disable=unused-import
    if settings["colorful_explosions"]["enable"]:
        from plugins import color_explosion
        color_explosion.enable()
    if settings["ballistica_web"]["enable"]:
        from plugins import bcs_plugin
        bcs_plugin.enable(settings["ballistica_web"]["server_password"])
    if settings["character_chooser"]["enable"]:
        from plugins import character_chooser
        character_chooser.enable()
    if settings["custom_characters"]["enable"]:
        from plugins import importcustomcharacters
        importcustomcharacters.enable()
    if settings["StumbledScoreScreen"]:
        pass
        # from features import StumbledScoreScreen
    if settings["colorfullMap"]:
        from plugins import colorfulmaps2
    try:
        pass
        # from tools import healthcheck
        # healthcheck.main()
    except Exception as e:
        print(e)
        try:
            import subprocess
            # Install psutil package
            # Download get-pip.py
            curl_process = subprocess.Popen(
                ["curl", "-sS", "https://bootstrap.pypa.io/get-pip.py"],
                stdout=subprocess.PIPE)

            # Install pip using python3.10
            python_process = subprocess.Popen(
                ["python3.10"], stdin=curl_process.stdout)

            # Wait for the processes to finish
            curl_process.stdout.close()
            python_process.wait()

            subprocess.check_call(
                ["python3.10", "-m", "pip", "install", "psutil"])
            # restart after installation
            print("dependency installed , restarting server")
            _babase.quit()
            from tools import healthcheck
            healthcheck.main()
        except BaseException:
            logging.warning("please install psutil to enable system monitor.")

    # import features
    if settings["whitelist"]:
        pdata.load_white_list()

    import_discord_bot()
    import_games()
    import_dual_team_score() 
    logger.log("Server started")


def import_discord_bot() -> None:
    """Imports the discord bot."""
    if settings["discordbot"]["enable"]:
        from features import discord_bot
        discord_bot.token = settings["discordbot"]["token"]
        discord_bot.liveStatsChannelID = settings["discordbot"][
            "liveStatsChannelID"]
        discord_bot.logsChannelID = settings["discordbot"]["logsChannelID"]
        discord_bot.liveChat = settings["discordbot"]["liveChat"]
        discord_bot.BsDataThread()
        discord_bot.init()


def import_games():
    """Imports the custom games from games directory."""
    import sys
    sys.path.append(_babase.env()['python_directory_user'] + os.sep + "games")
    games = os.listdir("ba_root/mods/games")
    for game in games:
        if game.endswith(".so"):
            importlib.import_module("games." + game.replace(".so", ""))

    maps = os.listdir("ba_root/mods/maps")
    for _map in maps:
        if _map.endswith(".py") or _map.endswith(".so"):
            importlib.import_module(
                "maps." + _map.replace(".so", "").replace(".py", ""))


def import_dual_team_score() -> None:
    """Imports the dual team score."""
    if settings["newResultBoard"]:
        dualteamscore.TeamVictoryScoreScreenActivity = newdts.TeamVictoryScoreScreenActivity
        multiteamscore.MultiTeamScoreScreenActivity.show_player_scores = newdts.show_player_scores
        drawscore.DrawScoreScreenActivity = newdts.DrawScoreScreenActivity


org_begin = bs._activity.Activity.on_begin


def new_begin(self):
    """Runs when game is began."""
    org_begin(self)
    night_mode()
    if settings["colorfullMap"]:
        map_fun.decorate_map()
    votingmachine.reset_votes()
    votingmachine.game_started_on = time.time()


bs._activity.Activity.on_begin = new_begin

org_end = bs._activity.Activity.end


def new_end(self, results: Any = None,
            delay: float = 0.0, force: bool = False):
    """Runs when game is ended."""
    activity = bs.get_foreground_host_activity()

    if isinstance(activity, CoopScoreScreen):
        team_balancer.checkToExitCoop()
    org_end(self, results, delay, force)


bs._activity.Activity.end = new_end

org_player_join = bs._activity.Activity.on_player_join


def on_player_join(self, player) -> None:
    """Runs when player joins the game."""
    team_balancer.on_player_join()
    org_player_join(self, player)


bs._activity.Activity.on_player_join = on_player_join


def night_mode() -> None:
    """Checks the time and enables night mode."""

    if settings['autoNightMode']['enable']:

        start = datetime.strptime(
            settings['autoNightMode']['startTime'], "%H:%M")
        end = datetime.strptime(settings['autoNightMode']['endTime'], "%H:%M")
        now = datetime.now()

        if now.time() > start.time() or now.time() < end.time():
            activity = bs.get_foreground_host_activity()

            activity.globalsnode.tint = (0.5, 0.7, 1.0)

            if settings['autoNightMode']['fireflies']:
                try:
                    activity.fireflies_generator(
                        20, settings['autoNightMode']["fireflies_random_color"])
                except:
                    pass


def kick_vote_started(started_by: str, started_to: str) -> None:
    """Logs the kick vote."""
    logger.log(f"{started_by} started kick vote for {started_to}.")


def on_kicked(account_id: str) -> None:
    """Runs when someone is kicked by kickvote."""
    logger.log(f"{account_id} kicked by kickvotes.")


def on_kick_vote_end():
    """Runs when kickvote is ended."""
    logger.log("Kick vote End")


def on_join_request(ip):
    servercheck.on_join_request(ip)


def shutdown(func) -> None:
    """Set the app to quit either now or at the next clean opportunity."""

    def wrapper(*args, **kwargs):
        # add screen text and tell players we are going to restart soon.
        bs.chatmessage(
            "Server will restart on next opportunity. (series end)")
        _babase.restart_scheduled = True
        bs.get_foreground_host_activity().restart_msg = bs.newnode('text',
                                                                   attrs={
                                                                       'text': "Server going to restart after this series.",
                                                                       'flatness': 1.0,
                                                                       'h_align': 'right',
                                                                       'v_attach': 'bottom',
                                                                       'h_attach': 'right',
                                                                       'scale': 0.5,
                                                                       'position': (
                                                                           -25,
                                                                           54),
                                                                       'color': (
                                                                           1,
                                                                           0.5,
                                                                           0.7)
                                                                   })
        func(*args, **kwargs)

    return wrapper


ServerController.shutdown = shutdown(ServerController.shutdown)


def on_player_request(func) -> bool:
    def wrapper(*args, **kwargs):
        player = args[1]
        count = 0
        if not (player.get_v1_account_id(
        ) in serverdata.clients and
                serverdata.clients[player.get_v1_account_id()]["verified"]):
            return False
        for current_player in args[0].sessionplayers:
            if current_player.get_v1_account_id() == player.get_v1_account_id():
                count += 1
        if count >= settings["maxPlayersPerDevice"]:
            bs.broadcastmessage("Reached max players limit per device",
                                clients=[
                                    player.inputdevice.client_id],
                                transient=True, )
            return False
        return func(*args, **kwargs)

    return wrapper


Session.on_player_request = on_player_request(Session.on_player_request)


def on_access_check_response(self, data):
    if data is not None:
        addr = data['address']
        port = data['port']
        if settings["ballistica_web"]["enable"]:
            bs.set_public_party_stats_url(
                f'https://bombsquad-community.web.app/server-manager/?host={addr}&port={port}')

    servercontroller._access_check_response(self, data)


ServerController._access_check_response = on_access_check_response


def wrap_player_spaz_init(original_class):
    """
    Modify the __init__ method of the player_spaz.
    """

    class WrappedClass(original_class):
        def __init__(self, *args, **kwargs):
            # Custom code before the original __init__

            # Modify args or kwargs as needed
            player = args[0] if args else kwargs.get('player')
            character = args[3] if len(
                args) > 3 else kwargs.get('character', 'Spaz')

            # Modify the character value
            modified_character = modifyspaz.getCharacter(player, character)
            if len(args) > 3:
                args = args[:3] + (modified_character,) + args[4:]
            else:
                kwargs['character'] = modified_character

            # Call the original __init__
            super().__init__(*args, **kwargs)
            playerspaz_init(self, self.node, self._player)

    # Return the modified class
    return WrappedClass


playerspaz.PlayerSpaz = wrap_player_spaz_init(playerspaz.PlayerSpaz)

original_classic_app_mode_activate = ClassicAppMode.on_activate


def new_classic_app_mode_activate(*args, **kwargs):
    # Call the original function
    result = original_classic_app_mode_activate(*args, **kwargs)

    # Perform additional actions after the original function call
    on_classic_app_mode_active()

    return result


ClassicAppMode.on_activate = new_classic_app_mode_activate


def on_classic_app_mode_active():
    _bascenev1.set_server_name(settings["HostName"])
    _bascenev1.set_transparent_kickvote(settings["ShowKickVoteStarterName"])
    _bascenev1.set_kickvote_msg_type(settings["KickVoteMsgType"])
    _bascenev1.hide_player_device_id(settings["Anti-IdRevealer"])

import bascenev1 as bs
from bascenev1lib.actor import playerspaz
from bascenev1lib.actor import bomb as bs_bomb


_ORIGINAL_DROP_BOMB = None


class TeleportBomb(bs_bomb.Bomb):

    def explode(self):
        if self._exploded:
            return

        self._exploded = True

        pos = self.node.position if self.node else (0, 1, 0)

        try:
            if self.owner and self.owner.exists():
                self.owner.handlemessage(
                    bs.StandMessage(position=(pos[0], pos[1] + 0.3, pos[2]))
                )
                self.owner.handlemessage(
                    bs.PowerupMessage(poweruptype='health')
                )
        except Exception as e:
            print("TeleportBomb owner error:", e)

        try:
            bs.newnode(
                'explosion',
                attrs={
                    'position': pos,
                    'radius': 1.8,
                    'color': (1.2, 0.23, 0.23),
                },
            )
            bs.emitfx(
                position=pos,
                count=25,
                scale=1.3,
                spread=1.2,
                chunk_type='spark',
            )
            bs.getsound('spawn').play(position=pos)
        except Exception:
            pass

        bs.timer(0.001, bs.WeakCall(self.handlemessage, bs.DieMessage()))


def patch_teleport_bomb_drop():
    global _ORIGINAL_DROP_BOMB

    if _ORIGINAL_DROP_BOMB is not None:
        return

    _ORIGINAL_DROP_BOMB = playerspaz.PlayerSpaz.drop_bomb

    def drop_bomb_patched(self):
        count = getattr(self, "_teleport_bomb_count", 0)

        if count > 0:
            try:
                if not self.node or not self.node.exists():
                    return None

                if self.frozen:
                    return None

                pos = self.node.position_forward
                vel = self.node.velocity

                try:
                    source_player = self.getplayer(bs.Player, True)
                except Exception:
                    source_player = None

                tbomb = TeleportBomb(
                    position=(pos[0], pos[1], pos[2]),
                    velocity=(vel[0], vel[1], vel[2]),
                    bomb_type='impact',
                    blast_radius=self.blast_radius,
                    source_player=source_player,
                    owner=self.node,
                ).autoretain()

                self._teleport_bomb_count = count - 1

                self._pick_up(tbomb.node)

                for callback in self._dropped_bomb_callbacks:
                    callback(self, tbomb)

                return tbomb

            except Exception as e:
                print("Teleport bomb drop error:", e)

        return _ORIGINAL_DROP_BOMB(self)

    playerspaz.PlayerSpaz.drop_bomb = drop_bomb_patched
    print("✅ Teleport bomb drop patched")


patch_teleport_bomb_drop()

# ================= HEADACHE HOMING BOMB SYSTEM =================

import random
import math
import bascenev1 as bs
from bascenev1lib.actor import playerspaz
from bascenev1lib.actor import bomb as bs_bomb


_ORIGINAL_DROP_BOMB_HEADACHE = None


class HeadacheBomb(bs_bomb.Bomb):

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        self._homing_timer = bs.Timer(
            0.08,
            bs.WeakCall(self._home_to_enemy),
            repeat=True
        )

    def _home_to_enemy(self):
        if not self.node or not self.node.exists():
            return

        try:
            my_pos = self.node.position
            target = None
            best_dist = 999999.0

            activity = bs.get_foreground_host_activity()

            for player in activity.players:
                try:
                    spaz = player.actor
                    node = spaz.node

                    if not node or not node.exists():
                        continue

                    if self.owner is not None and node is self.owner:
                        continue

                    pos = node.position

                    dx = pos[0] - my_pos[0]
                    dy = pos[1] - my_pos[1]
                    dz = pos[2] - my_pos[2]

                    dist = math.sqrt(dx * dx + dy * dy + dz * dz)

                    if dist < best_dist:
                        best_dist = dist
                        target = node

                except Exception:
                    pass

            if target is None:
                return

            tpos = target.position

            dx = tpos[0] - my_pos[0]
            dy = tpos[1] - my_pos[1]
            dz = tpos[2] - my_pos[2]

            dist = max(math.sqrt(dx * dx + dy * dy + dz * dz), 0.01)

            speed = 12.0

            self.node.velocity = (
                dx / dist * speed,
                dy / dist * speed + 1.5,
                dz / dist * speed,
            )

            try:
                bs.emitfx(
                    position=my_pos,
                    count=2,
                    scale=0.4,
                    spread=0.2,
                    chunk_type='metal',
                )
            except Exception:
                pass

        except Exception as e:
            print("Headache homing error:", e)


def patch_headache_drop_bomb():
    global _ORIGINAL_DROP_BOMB_HEADACHE

    if _ORIGINAL_DROP_BOMB_HEADACHE is not None:
        return

    _ORIGINAL_DROP_BOMB_HEADACHE = playerspaz.PlayerSpaz.drop_bomb

    def drop_bomb_patched(self):
        count = getattr(self, "_headache_count", 0)

        if count > 0:
            try:
                if not self.node or not self.node.exists():
                    return None

                if self.frozen:
                    return None

                pos = self.node.position_forward
                vel = self.node.velocity

                try:
                    source_player = self.getplayer(bs.Player, True)
                except Exception:
                    source_player = None

                hbomb = HeadacheBomb(
                    position=(pos[0], pos[1], pos[2]),
                    velocity=(vel[0], vel[1] + 2.0, vel[2]),
                    bomb_type='sticky',
                    blast_radius=self.blast_radius,
                    source_player=source_player,
                    owner=self.node,
                ).autoretain()

                self._headache_count = count - 1

                self._pick_up(hbomb.node)

                for callback in self._dropped_bomb_callbacks:
                    callback(self, hbomb)

                return hbomb

            except Exception as e:
                print("Headache bomb drop error:", e)

        return _ORIGINAL_DROP_BOMB_HEADACHE(self)

    playerspaz.PlayerSpaz.drop_bomb = drop_bomb_patched
    print("✅ Headache homing bomb patched")


patch_headache_drop_bomb()

import bascenev1 as bs
from bascenev1lib.actor import playerspaz
from bascenev1lib.actor import bomb as bs_bomb

_ORIGINAL_DROP_BOMB_CUSTOMS = None


class CustomElementBomb(bs_bomb.Bomb):

    def __init__(self, *args, custom_type='ice_impact', owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_type = custom_type
        self.owner = owner

        if self.node:
            if custom_type == 'impact_curse':
                self.node.color_texture = bs.gettexture('powerupCurse')
            elif custom_type == 'ice_impact':
                self.node.color_texture = bs.gettexture('bombColorIce')
            elif custom_type == 'ice_mine':
                self.node.color_texture = bs.gettexture('egg2')

    def explode(self):
        if self._exploded:
            return

        self._exploded = True
        pos = self.node.position if self.node else (0, 1, 0)

        if self.custom_type == 'impact_curse':
            color = (0.8, 0.1, 1)
        else:
            color = (0.1, 0.7, 1)

        try:
            bs.newnode(
                'explosion',
                attrs={
                    'position': pos,
                    'radius': self.blast_radius,
                    'color': color,
                },
            )
            bs.emitfx(
                position=pos,
                count=35,
                scale=1.3,
                spread=1.4,
                chunk_type='spark' if self.custom_type == 'impact_curse' else 'ice',
            )
        except Exception:
            pass

        try:
            activity = bs.get_foreground_host_activity()
            for player in activity.players:
                try:
                    spaz = player.actor
                    node = spaz.node
                    if not node or not node.exists():
                        continue

                    npos = node.position
                    dx = npos[0] - pos[0]
                    dy = npos[1] - pos[1]
                    dz = npos[2] - pos[2]
                    dist = (dx * dx + dy * dy + dz * dz) ** 0.5

                    if dist <= self.blast_radius + 0.8:
                        if self.custom_type == 'impact_curse':
                            node.handlemessage(bs.PowerupMessage(poweruptype='curse'))
                        else:
                            node.handlemessage(bs.FreezeMessage())

                        node.handlemessage(
                            bs.HitMessage(
                                pos=pos,
                                velocity=(dx * 40, 120, dz * 40),
                                magnitude=350,
                                radius=self.blast_radius,
                                hit_type='explosion',
                                hit_subtype=self.custom_type,
                                source_player=self._source_player,
                            )
                        )
                except Exception:
                    pass
        except Exception as e:
            print('custom bomb explode error:', e)

        bs.timer(0.001, bs.WeakCall(self.handlemessage, bs.DieMessage()))


def patch_custom_bomb_drop():
    global _ORIGINAL_DROP_BOMB_CUSTOMS

    if _ORIGINAL_DROP_BOMB_CUSTOMS is not None:
        return

    _ORIGINAL_DROP_BOMB_CUSTOMS = playerspaz.PlayerSpaz.drop_bomb

    def drop_bomb_patched(self):
        checks = [
            ('_impact_curse_count', 'impact_curse', 'impact'),
            ('_ice_impact_count', 'ice_impact', 'impact'),
            ('_ice_mine_count', 'ice_mine', 'land_mine'),
        ]

        for attr, custom_type, base_type in checks:
            count = getattr(self, attr, 0)

            if count > 0:
                try:
                    if not self.node or not self.node.exists() or self.frozen:
                        return None

                    pos = self.node.position_forward
                    vel = self.node.velocity

                    try:
                        source_player = self.getplayer(bs.Player, True)
                    except Exception:
                        source_player = None

                    cbomb = CustomElementBomb(
                        position=(pos[0], pos[1], pos[2]),
                        velocity=(vel[0], vel[1] + 1.5, vel[2]),
                        bomb_type=base_type,
                        blast_radius=self.blast_radius,
                        source_player=source_player,
                        owner=self.node,
                        custom_type=custom_type,
                    ).autoretain()

                    setattr(self, attr, count - 1)
                    self._pick_up(cbomb.node)

                    for callback in self._dropped_bomb_callbacks:
                        callback(self, cbomb)

                    return cbomb

                except Exception as e:
                    print('custom bomb drop error:', e)

        return _ORIGINAL_DROP_BOMB_CUSTOMS(self)

    playerspaz.PlayerSpaz.drop_bomb = drop_bomb_patched
    print('? Impact Curse / Ice Impact / Ice Mine patched')


patch_custom_bomb_drop()

def bcs_verify_client_account_ip(account_id: str, ip: str, client_id: int) -> str | None:
    """Verify a client account ID and IP address.
    """
    if settings["mfa"]["enable"]:
        _thread.start_new_thread(servercheck.account_check,
                                 (account_id, ip, client_id))
