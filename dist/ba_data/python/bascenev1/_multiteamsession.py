# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to teams sessions."""
from __future__ import annotations

import copy
import random
import logging
from typing import TYPE_CHECKING, override

import babase
import _bascenev1
from bascenev1._session import Session

# NOTE: coin_system import removed from here to prevent native stack trace crash.

if TYPE_CHECKING:
    from typing import Any, Sequence
    import bascenev1

DEFAULT_TEAM_COLORS = ((0.1, 0.25, 1.0), (1.0, 0.25, 0.2))
DEFAULT_TEAM_NAMES = ('Blue', 'Red')

class MultiTeamSession(Session):
    """Common base for DualTeamSession and FreeForAllSession."""

    _playlist_selection_var = 'UNSET Playlist Selection'
    _playlist_randomize_var = 'UNSET Playlist Randomize'
    _playlists_var = 'UNSET Playlists'

    def __init__(self) -> None:
        from bascenev1 import _playlist
        from bascenev1lib.activity.multiteamjoin import MultiTeamJoinActivity

        app = babase.app
        classic = app.classic
        assert classic is not None
        cfg = app.config

        if self.use_teams:
            team_names = cfg.get('Custom Team Names', DEFAULT_TEAM_NAMES)
            team_colors = cfg.get('Custom Team Colors', DEFAULT_TEAM_COLORS)
        else:
            team_names = None
            team_colors = None

        depsets: Sequence[bascenev1.DependencySet] = []

        super().__init__(
            depsets,
            team_names=team_names,
            team_colors=team_colors,
            min_players=1,
            max_players=self.get_max_players(),
        )

        self._series_length: int = int(cfg.get('Teams Series Length', 7))
        self._ffa_series_length: int = int(cfg.get('FFA Series Length', 24))
        
        show_tutorial = cfg.get('Show Tutorial', True)
        if classic.stress_test_update_timer is not None:
            show_tutorial = False

        self._tutorial_activity_instance: bascenev1.Activity | None
        if show_tutorial:
            from bascenev1lib.tutorial import TutorialActivity
            self._tutorial_activity_instance = _bascenev1.newactivity(TutorialActivity)
        else:
            self._tutorial_activity_instance = None

        self._playlist_name = cfg.get(self._playlist_selection_var, '__default__')
        self._playlist_randomize = cfg.get(self._playlist_randomize_var, False)
        self._game_number = 0
        playlists = cfg.get(self._playlists_var, {})

        if self._playlist_name != '__default__' and self._playlist_name in playlists:
            playlist = copy.deepcopy(playlists[self._playlist_name])
        else:
            playlist = _playlist.get_default_teams_playlist() if self.use_teams else _playlist.get_default_free_for_all_playlist()

        playlist_resolved = _playlist.filter_playlist(
            playlist, sessiontype=type(self), add_resolved_type=True,
            name='default teams' if self.use_teams else 'default ffa')
        
        if not playlist_resolved:
            playlist_resolved = _playlist.filter_playlist(
                _playlist.get_default_teams_playlist(), sessiontype=type(self), 
                add_resolved_type=True, name='fallback')

        self._playlist = ShuffleList(playlist_resolved, shuffle=self._playlist_randomize)
        self._current_game_spec: dict[str, Any] | None = None
        self._next_game_spec: dict[str, Any] = self._playlist.pull_next()
        self._next_game: type[bascenev1.GameActivity] = self._next_game_spec['resolved_type']

        self._instantiate_next_game()
        self.setactivity(_bascenev1.newactivity(MultiTeamJoinActivity))

    def get_next_game_description(self) -> babase.Lstr:
        """Returns a description of the next game on deck."""
        from bascenev1._gameactivity import GameActivity
        gametype: type[GameActivity] = self._next_game_spec['resolved_type']
        return gametype.get_settings_display_string(self._next_game_spec)

    def get_ffa_series_length(self) -> int: return self._ffa_series_length
    def get_series_length(self) -> int: return self._series_length
    def get_game_number(self) -> int: return self._game_number

    @override
    def on_team_join(self, team: bascenev1.SessionTeam) -> None:
        team.customdata['previous_score'] = team.customdata['score'] = 0

    def get_max_players(self) -> int:
        val = babase.app.config.get('Team Game Max Players' if self.use_teams else 'Free-for-All Max Players', 8)
        return int(val)

    def _instantiate_next_game(self) -> None:
        self._next_game_instance = _bascenev1.newactivity(
            self._next_game_spec['resolved_type'], self._next_game_spec['settings'])

    @override
    def on_activity_end(self, activity: bascenev1.Activity, results: Any) -> None:
        from bascenev1lib.tutorial import TutorialActivity
        from bascenev1lib.activity.multiteamvictory import TeamSeriesVictoryScoreScreenActivity
        from bascenev1._activitytypes import TransitionActivity, JoinActivity, ScoreScreenActivity

        if self._tutorial_activity_instance is not None:
            self.setactivity(self._tutorial_activity_instance)
            self._tutorial_activity_instance = None
        elif isinstance(activity, TutorialActivity):
            self.setactivity(_bascenev1.newactivity(TransitionActivity))
        elif isinstance(activity, (JoinActivity, TransitionActivity, ScoreScreenActivity)):
            if isinstance(activity, TeamSeriesVictoryScoreScreenActivity):
                self.stats.reset()
                self._game_number = 0
                for team in self.sessionteams: team.customdata['score'] = 0
            else:
                self.stats.reset_accum()

            next_game = self._next_game_instance
            self._current_game_spec = self._next_game_spec
            self._next_game_spec = self._playlist.pull_next()
            self._game_number += 1
            self._instantiate_next_game()

            for player in self.sessionplayers:
                try: has_team = player.sessionteam is not None
                except babase.NotFoundError: has_team = False
                if has_team: self.stats.register_sessionplayer(player)
            self.stats.setactivity(next_game)
            self.setactivity(next_game)
        else:
            self._switch_to_score_screen(results)

    def _switch_to_score_screen(self, results: Any) -> None:
        logging.error('This should be overridden.', stack_info=True)

    def announce_game_results(
        self, activity: bascenev1.GameActivity, results: bascenev1.GameResults,
        delay: float, announce_winning_team: bool = True,
    ) -> None:
        from bascenev1._gameutils import cameraflash
        from bascenev1._freeforallsession import FreeForAllSession
        from bascenev1._messages import CelebrateMessage

        _bascenev1.timer(delay, _bascenev1.getsound('boxingBell').play)

        if announce_winning_team:
            winning_sessionteam = results.winning_sessionteam
            if winning_sessionteam is not None:
                
                # --- DELAYED PAYOUT TRIGGER ---
                try:
                    import coin_system
                    coin_system.reward_by_score(self, winning_sessionteam)
                except Exception as e:
                    print(f"Coin System Error: {e}")
                # -----------------------------

                celebrate_msg = CelebrateMessage(duration=10.0)
                assert winning_sessionteam.activityteam is not None
                for player in winning_sessionteam.activityteam.players:
                    if player.actor: player.actor.handlemessage(celebrate_msg)
                cameraflash()

                wins_resource = 'winsPlayerText' if isinstance(self, FreeForAllSession) else 'winsTeamText'
                wins_text = babase.Lstr(resource=wins_resource, subs=[('${NAME}', winning_sessionteam.name)])
                activity.show_zoom_message(wins_text, scale=0.85, color=babase.normalized_color(winning_sessionteam.color))

class ShuffleList:
    def __init__(self, items: list[dict[str, Any]], shuffle: bool = True):
        self.source_list = items
        self.shuffle = shuffle
        self.shuffle_list: list[dict[str, Any]] = []
        self.last_gotten: dict[str, Any] | None = None

    def pull_next(self) -> dict[str, Any]:
        if not self.shuffle_list: self.shuffle_list = list(self.source_list)
        index = 0
        if self.shuffle:
            for _i in range(4):
                index = random.randrange(0, len(self.shuffle_list))
                test_obj = self.shuffle_list[index]
                if len(self.shuffle_list) > 1 and self.last_gotten is not None:
                    if test_obj['settings']['map'] == self.last_gotten['settings']['map']: continue
                    if test_obj['type'] == self.last_gotten['type']: continue
                break
        obj = self.shuffle_list.pop(index)
        self.last_gotten = obj
        return obj
 