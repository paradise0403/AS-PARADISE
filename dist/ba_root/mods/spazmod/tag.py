import babase
import bascenev1 as bs
import math
import random
import os
import json
import re
from _bascenev1 import get_client_ping as _get_ping  

try:
    from playersdata import pdata
    from stats import mystats
    import setting
    sett = setting.get_settings_data()
except ImportError:
    pdata = None
    mystats = None
    sett = {}

# -------------------- PING SYSTEM --------------------

class PingDisplay:
    def __init__(self, owner, player):
        self.node = owner
        try:
            self.client_id = player.sessionplayer.inputdevice.client_id
        except Exception:
            self.client_id = None

        m = bs.newnode('math', owner=self.node,
                       attrs={'input1': (0, -1.0, 0), 'operation': 'add'})
        self.node.connectattr('torso_position', m, 'input2')

        self.txt = bs.newnode('text', owner=self.node, attrs={
            'text': '',
            'in_world': True,
            'shadow': 1.0,
            'flatness': 1.0,
            'scale': 0.009,
            'h_align': 'center'
        })
        m.connectattr('output', self.txt, 'position')
        self._update()

    def _update(self):
        if not self.node.exists(): return
        try:
            ping = _get_ping(self.client_id) if self.client_id is not None else 0
        except Exception: ping = 0

        if ping < 80: col = (0, 1, 0)
        elif ping < 150: col = (1, 1, 0)
        else: col = (1, 0, 0)

        self.txt.text = f"{ping} ms"
        self.txt.color = col
        bs.timer(1.0, self._update)

# -------------------- MAIN FUNCTIONS --------------------

def addtag(node, player):
    session_player = player.sessionplayer
    account_id = session_player.get_v1_account_id()
    tag, anim_id = None, 0
    spawn_colors = [(0.5, 1, 1), (0.5, 1, 0.5), (1, 0.5, 1)] 
    col = random.choice(spawn_colors)

    if pdata:
        custom_data = pdata.get_custom().get('customtag', {})
        if account_id in custom_data:
            data = custom_data[account_id]
            if isinstance(data, dict):
                tag = data.get('tag', 'Player')
                anim_id = data.get('anim', 1)
            else: tag = data
        
        if not tag:
            p_roles = pdata.get_player_roles(account_id)
            roles = pdata.get_roles()
            for role in roles:
                if role in p_roles:
                    tag = roles[role]['tag']
                    col = roles[role].get('tagcolor', col)
                    anim_id = roles[role].get('anim', 0)
                    break

    if tag: Tag(node, tag, col, anim_id)
    PingDisplay(node, player)

def addrank(node, player):
    if not mystats: return
    rank = mystats.getRank(player.sessionplayer.get_v1_account_id())
    if rank: Rank(node, rank)

def addstats(node, player):
    StatLooper(node, player.sessionplayer.get_v1_account_id())

def addhp(node, spaz):
    spaz.hp_display = HitPoint(owner=node, prefix=str(int(spaz.hitpoints)), position=(0, 1.75, 0))
    def refresh_hp():
        if not spaz.node.exists() or not hasattr(spaz, 'hp_display'): return
        hp_val = int(spaz.hitpoints) / 10
        txt_node = spaz.hp_display._Text
        if txt_node.exists():
            txt_node.text = f"\ue047{hp_val}\ue047"
            txt_node.color = (1, 1, 0)
            def restore():
                if txt_node.exists(): txt_node.color = (1, 1, 1) if hp_val >= 20 else (1.0, 0.2, 0.2)
            bs.timer(0.2, restore)

    old_handle_message = spaz.handlemessage
    def new_handle_message(msg):
        if isinstance(msg, bs.HitMessage): bs.timer(0.01, refresh_hp)
        return old_handle_message(msg)
    spaz.handlemessage = new_handle_message

# -------------------- CLASSES --------------------

class StatLooper:
    def __init__(self, owner, account_id):
        self.node, self.account_id, self.index = owner, account_id, 0
        self.textnode = bs.newnode('text', owner=self.node, attrs={
            'text': '', 'in_world': True, 'shadow': 1.0, 'flatness': 1.0,
            'color': (1, 1, 1), 'scale': 0.008, 'h_align': 'center'
        })
        m = bs.newnode('math', owner=self.node, attrs={'input1': (0, 1.25, 0), 'operation': 'add'})
        self.node.connectattr('torso_position', m, 'input2')
        m.connectattr('output', self.textnode, 'position')
        self._loop()

    def _loop(self):
        if not self.textnode.exists(): return
        aid = self.account_id
        try:
            stats = [f"\ue043 Rank: {mystats.get_rank(aid)}", f"\ue047 Score: {mystats.get_score(aid)}",
                     f"\ue047 Kills: {mystats.get_kills(aid)}", f"\ue047 Deaths: {mystats.get_deaths(aid)}",
                     f"\ue047 KD: {mystats.get_kd(aid)}"]
        except: stats = ["Stats Error"]
        
        self.textnode.text = stats[self.index]
        bs.animate(self.textnode, 'opacity', {0.0: 0.0, 0.3: 1.0, 1.8: 1.0, 2.1: 0.0})
        self.index = (self.index + 1) % len(stats)
        bs.timer(2.3, self._loop)

class Tag:
    def __init__(self, owner, tag, col, anim_id):
        self.node, self.anim_id = owner, anim_id
        icons = {'\\d': '\ue048', '\\c': '\ue043', '\\h': '\ue049', '\\s': '\ue046', '\\n': '\ue04b', '\\t': '\ue01f'}
        for k, v in icons.items(): tag = tag.replace(k, v)

        if anim_id in range(2, 12): self._build_multi_node_tag(tag, col, anim_id)
        else: self._build_standard_tag(tag, col)

    def _build_standard_tag(self, tag, col):
        mnode = bs.newnode('math', owner=self.node, attrs={'input1': (0, 1.5, 0), 'operation': 'add'})
        self.node.connectattr('torso_position', mnode, 'input2')
        txt = bs.newnode('text', owner=self.node, attrs={'text': tag, 'in_world': True, 'shadow': 1.0, 'flatness': 1.0, 'color': tuple(col), 'scale': 0.01, 'h_align': 'center'})
        mnode.connectattr('output', txt, 'position')
        if self.anim_id == 1: bs.animate_array(txt, 'color', 3, {0.0:(1,0,0), 0.5:(1,1,1), 1.0:(0,0,1), 2.0:(1,0,0)}, loop=True)

    def _build_multi_node_tag(self, tag, col, anim_id):
        char_spacing, total_chars = 0.15, len(tag)
        start_x = -((total_chars - 1) * char_spacing) / 2
        for i, char in enumerate(tag):
            curr_x = start_x + (i * char_spacing)
            m = bs.newnode('math', owner=self.node, attrs={'input1': (curr_x, 1.5, 0), 'operation': 'add'})
            self.node.connectattr('torso_position', m, 'input2')
            
            char_col = col
            if anim_id == 6: char_col = (random.random(), random.random(), random.random())
            
            t = bs.newnode('text', owner=self.node, attrs={'text': char, 'in_world': True, 'shadow': 1.0, 'flatness': 1.0, 'color': tuple(char_col), 'scale': 0.01, 'h_align': 'center'})
            m.connectattr('output', t, 'position')
            delay = i * 0.15
            
            if anim_id == 2:
                bs.animate_array(t, 'color', 3, {0.0:(1,0,0), 0.5:(1,1,0), 1.0:(1,0,0)}, loop=True, offset=delay)
                bs.animate_array(m, 'input1', 3, {0.0:(curr_x,1.5,0), 0.5:(curr_x,1.58,0), 1.0:(curr_x,1.5,0)}, loop=True, offset=delay)
            elif anim_id == 3:
                bs.animate(t, 'opacity', {0.0:0.3, 0.5:1.0, 1.0:0.3}, loop=True, offset=delay)
            elif anim_id == 4:
                bs.animate(t, 'opacity', {0.0:1.0, 0.2:0.0, 0.4:1.0}, loop=True, offset=delay)
            elif anim_id == 5:
                bs.animate_array(t, 'color', 3, {0.0:(1,0,0), 0.5:(0,1,0), 1.0:(0,0,1), 1.5:(1,0,0)}, loop=True, offset=delay)
            elif anim_id == 6: # Rainbow Wave
                bs.animate_array(t, 'color', 3, {0.0:(1,0,0), 0.2:(0,1,0), 0.4:(0,0,1), 0.6:(1,1,0), 0.8:(0,1,1), 1.0:(1,0,0)}, loop=True, offset=delay)
            elif anim_id == 7: # Golden Sweep (Smooth Shine)
                bs.animate_array(t, 'color', 3, {0.0:(1,0.8,0), 0.2:(1,1,0.6), 0.4:(1,0.8,0)}, loop=True, offset=delay)

            elif anim_id == 8: # Neon Pulse
                bs.animate_array(t, 'color', 3, {0.0:char_col, 0.5:(1,1,1), 1.0:char_col}, loop=True, offset=delay)
            elif anim_id == 9: # Vertical Bounce
                bs.animate_array(m, 'input1', 3, {0.0:(curr_x,1.5,0), 0.5:(curr_x,1.65,0), 1.0:(curr_x,1.5,0)}, loop=True, offset=delay)

            elif anim_id == 10:
                # Indian Flag logic: Divide name into 3 parts
                idx_ratio = i / total_chars
                if idx_ratio < 0.33:
                    base_color = (1.0, 0.5, 0.0) # Saffron
                elif idx_ratio < 0.66:
                    base_color = (1.0, 1.0, 1.0) # White
                else:
                    base_color = (0.0, 0.5, 0.0) # Green
                
                # Ashoka Chakra Blue Pulse in the middle
                bs.animate_array(t, 'color', 3, {
                    0.0: base_color, 
                    0.5: (0.0, 0.0, 0.5), # Navy Blue
                    1.0: base_color
                }, loop=True, offset=delay)

            elif anim_id == 11:
                # First: Red & White -> Then: Blue & Sky Blue
                bs.animate_array(t, 'color', 3, {
                    0.0: (1, 0, 0),    # Red
                    0.25: (1, 1, 1),  # White
                    0.5: (0, 0, 1),    # Blue
                    0.75: (0, 0.8, 1),# Sky Blue
                    1.0: (1, 0, 0)     # Back to Red
                }, loop=True, offset=delay)
                # Adding a slight movement to make it look like it's "moving"
                bs.animate_array(m, 'input1', 3, {
                    0.0: (curr_x, 1.5, 0),
                    0.5: (curr_x, 1.55, 0),
                    1.0: (curr_x, 1.5, 0)
                }, loop=True, offset=delay)

            elif anim_id == 12:
                # White to Yellow moving loop
                # 1.0, 1.0, 1.0 is White | 1.0, 1.0, 0.0 is Yellow
                bs.animate_array(t, 'color', 3, {
                    0.0: (1, 1, 1),   # White
                    0.49: (1, 1, 1),
                    0.5: (1, 1, 0),   # Yellow
                    0.99: (1, 1, 0),
                    1.0: (1, 1, 1)    # Back to White
                }, loop=True, offset=delay)
                
                # Optional: Agar letters ko thoda up-down move karwana hai loop ke saath
                bs.animate_array(m, 'input1', 3, {
                    0.0: (curr_x, 1.5, 0),
                    0.5: (curr_x, 1.55, 0),
                    1.0: (curr_x, 1.5, 0)
                }, loop=True, offset=delay)


class Rank:
    def __init__(self, owner=None, rank=99):
        self.node = owner
        mnode = bs.newnode('math', owner=self.node, attrs={'input1': (0, 1.2, 0), 'operation': 'add'})
        self.node.connectattr('torso_position', mnode, 'input2')
        rank_str = f"\ue01f#{rank}\ue01f" if rank <= 3 else f"#{rank}"
        self.rank_text = bs.newnode('text', owner=self.node, attrs={'text': rank_str, 'in_world': True, 'shadow': 1.0, 'flatness': 1.0, 'color': (1, 1, 1), 'scale': 0.01, 'h_align': 'center'})
        mnode.connectattr('output', self.rank_text, 'position')

class HitPoint:
    def __init__(self, position=(0, 1.5, 0), owner=None, prefix='0', shad=1.2):
        self.node = owner
        self.m = bs.newnode('math', owner=self.node, attrs={'input1': position, 'operation': 'add'})
        self.node.connectattr('torso_position', self.m, 'input2')
        hp_val = int(prefix) / 10
        self._Text = bs.newnode('text', owner=self.node, attrs={'text': f"\ue047{hp_val}\ue047", 'in_world': True, 'shadow': shad, 'flatness': 1.0, 'color': (1, 1, 1) if hp_val >= 20 else (1.0, 0.2, 0.2), 'scale': 0.01, 'h_align': 'center'})
        self.m.connectattr('output', self._Text, 'position')
  
