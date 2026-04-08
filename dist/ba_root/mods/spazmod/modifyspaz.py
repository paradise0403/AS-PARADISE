from random import randint
import babase
import bascenev1 as bs

import setting
from spazmod import tag

_setting = setting.get_settings_data()

if _setting.get('enableeffects', False):
    try:
        from spazmod import spaz_effects
        spaz_effects.apply()
    except ImportError:
        pass

def update_name():
    from stats import mystats
    stat = mystats.get_all_stats()
    ros = bs.get_game_roster()
    for i in ros:
        # API 9 uses 'account_id' in roster
        aid = i.get('account_id')
        if aid:
            name = i.get('display_string', 'Player')
            if aid in stat:
                stat[aid]['name'] = name
    mystats.dump_stats(stat)

def main(spaz, node, player):
    """Modified Spaz logic for API 9."""
    
    # 1. Health Display
    if _setting.get('enablehptag', False):
        tag.addhp(node, spaz)

    # 2. Custom Animated Tags
    if _setting.get('enabletags', True):
        tag.addtag(node, player)

    # 3. STATS ROTATION (This is the change you needed)
    # We use 'enablestats' from settings to trigger the new loop in tag.py
    if _setting.get('enablestats', True):
        tag.addstats(node, player)
    
    # Fallback for old 'enablerank' setting if someone still uses it
    elif _setting.get('enablerank', False):
        tag.addrank(node, player)

    # 4. Player Equipment Mods
    pmod = _setting.get('playermod', {})
    if pmod.get('default_boxing_gloves', False):
        spaz.equip_boxing_gloves()
    if pmod.get('default_shield', False):
        spaz.equip_shields()
        
    spaz.bomb_type = pmod.get('default_bomb', 'normal')
    spaz.bomb_count = pmod.get('default_bomb_count', 3)

def getCharacter(player, character):
    if _setting.get("sameCharacterForTeam", False):
        if "character" in player.team.sessionteam.customdata:
            return player.team.sessionteam.customdata["character"]
    return character

def getRandomCharacter(otherthen):
    # API 9 path for appearances
    characters = list(babase.app.classic.spaz_appearances.keys())
    invalid_characters = ["Snake Shadow", "Lee", "Zola", "Butch", "Witch",
                          "Middle-Man", "Alien", "OldLady", "Wrestler",
                          "Gretel", "Robot"]

    while True:
        val = randint(0, len(characters) - 1)
        ch = characters[val]
        if ch not in invalid_characters and ch not in otherthen:
            return ch

def setTeamCharacter():
    if not _setting.get("sameCharacterForTeam", False):
        return
    used = []
    session = bs.get_foreground_host_session()
    if session:
        teams = session.sessionteams
        for team in teams:
            character = getRandomCharacter(used)
            used.append(character)
            # In API 9, setting team.name directly works
            team.name = character
            team.customdata["character"] = character
