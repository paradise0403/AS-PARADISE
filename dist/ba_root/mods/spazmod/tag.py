import babase
import bascenev1 as bs
import math
import random
import os
import json

# Note: Make sure these files exist in your mods folder
try:
    from playersdata import pdata
    from stats import mystats
    import setting
    sett = setting.get_settings_data()
except ImportErrors:
    # Fallback for missing custom modules
    pdata = None
    mystats = None
    sett = {}

def addtag(node, player):
    session_player = player.sessionplayer
    account_id = session_player.get_v1_account_id()
    
    tag = None
    anim_id = 0
    spawn_colors = [(0.5, 1, 1), (0.5, 1, 0.5), (1, 0.5, 1)] 
    col = random.choice(spawn_colors)

    if pdata:
        custom_data = pdata.get_custom().get('customtag', {})
        if account_id in custom_data:
            data = custom_data[account_id]
            if isinstance(data, dict):
                tag = data.get('tag', 'Player')
                anim_id = data.get('anim', 1)
            else:
                tag = data
        
        if not tag:
            p_roles = pdata.get_player_roles(account_id)
            roles = pdata.get_roles()
            for role in roles:
                if role in p_roles:
                    tag = roles[role]['tag']
                    col = roles[role].get('tagcolor', col)
                    anim_id = roles[role].get('anim', 0)
                    break

    if tag:
        Tag(node, tag, col, anim_id)

def addrank(node, player):
    if not mystats: return
    session_player = player.sessionplayer
    account_id = session_player.get_v1_account_id()
    rank = mystats.getRank(account_id)
    if rank:
        Rank(node, rank)

def addhp(node, spaz):
    """Real-time HP system with Yellow Flash on damage."""
    # Create the initial HP text
    spaz.hp_display = HitPoint(owner=node, prefix=str(int(spaz.hitpoints)), position=(0, 1.75, 0))

    def refresh_hp():
        if not spaz.node.exists() or not hasattr(spaz, 'hp_display'):
            return
            
        hp_val = int(spaz.hitpoints) / 10
        txt_node = spaz.hp_display._Text
        
        if txt_node.exists():
            txt_node.text = f"\ue047{hp_val}\ue047"
            # Damage Effect: Flash Yellow
            txt_node.color = (1, 1, 0)
            
            # Restore normal color after a short delay (0.2s)
            def restore():
                if txt_node.exists():
                    # Red if low HP, White if healthy
                    txt_node.color = (1, 1, 1) if hp_val >= 20 else (1.0, 0.2, 0.2)
            bs.timer(0.2, restore)

    # Hook into handlemessage to catch damage (HitMessage) instantly
    old_handle_message = spaz.handlemessage
    def new_handle_message(msg):
        if isinstance(msg, bs.HitMessage):
            # Check HP immediately after the hit is processed
            bs.timer(0.01, refresh_hp)
        return old_handle_message(msg)
    
    spaz.handlemessage = new_handle_message

class Tag:
    def __init__(self, owner, tag, col, anim_id):
        self.node = owner
        self.anim_id = anim_id
        
        icons = {'\\d': '\ue048', '\\c': '\ue043', '\\h': '\ue049', '\\s': '\ue046', 
                 '\\n': '\ue04b', '\\t': '\ue01f', '\\bs': '\ue01e'}
        for k, v in icons.items():
            tag = tag.replace(k, v)

        if anim_id in [2, 3, 4, 5]: 
            self._build_multi_node_tag(tag, col, anim_id)
        else:
            self._build_standard_tag(tag, col)

    def _build_standard_tag(self, tag, col):
        mnode = bs.newnode('math', owner=self.node, attrs={'input1': (0, 1.5, 0), 'operation': 'add'})
        self.node.connectattr('torso_position', mnode, 'input2')
        
        txt = bs.newnode('text', owner=self.node, attrs={
            'text': tag, 'in_world': True, 'shadow': 1.0, 'flatness': 1.0,
            'color': tuple(col), 'scale': 0.01, 'h_align': 'center'
        })
        mnode.connectattr('output', txt, 'position')

        if self.anim_id == 1:
            bs.animate_array(txt, 'color', 3, {
                0.0: (1, 0, 0), 0.5: (1, 1, 1), 1.0: (0, 0, 1), 1.5: (1, 1, 1), 2.0: (1, 0, 0)
            }, loop=True)

    def _build_multi_node_tag(self, tag, col, anim_id):
        char_spacing = 0.15 
        total_chars = len(tag)
        start_x = -((total_chars - 1) * char_spacing) / 2

        for i, char in enumerate(tag):
            current_x = start_x + (i * char_spacing)
            m = bs.newnode('math', owner=self.node, attrs={'input1': (current_x, 1.5, 0), 'operation': 'add'})
            self.node.connectattr('torso_position', m, 'input2')
            
            t = bs.newnode('text', owner=self.node, attrs={
                'text': char, 'in_world': True, 'shadow': 1.0, 'flatness': 1.0,
                'color': tuple(col), 'scale': 0.01, 'h_align': 'center'
            })
            m.connectattr('output', t, 'position')
            
            delay = i * 0.15
            if anim_id == 2: # Wave Red/Yellow
                bs.animate_array(t, 'color', 3, {0.0:(1,0,0), 0.5:(1,1,0), 1.0:(1,0,0)}, loop=True, offset=delay)
                bs.animate_array(m, 'input1', 3, {0.0:(current_x,1.5,0), 0.5:(current_x,1.58,0), 1.0:(current_x,1.5,0)}, loop=True, offset=delay)
            elif anim_id == 3: # Smooth
                bs.animate(t, 'opacity', {0.0:0.3, 0.5:1.0, 1.0:0.3}, loop=True, offset=delay)
                bs.animate_array(m, 'input1', 3, {0.0:(current_x,1.5,0), 0.5:(current_x,1.55,0), 1.0:(current_x,1.5,0)}, loop=True, offset=delay)
            elif anim_id == 4: # Blink
                bs.animate(t, 'opacity', {0.0:1.0, 0.2:0.0, 0.4:1.0}, loop=True, offset=delay)
            elif anim_id == 5: # Rainbow
                bs.animate_array(t, 'color', 3, {0.0:(1,0,0), 0.5:(0,1,0), 1.0:(0,0,1), 1.5:(1,0,0)}, loop=True, offset=delay)

class Rank:
    def __init__(self, owner=None, rank=99):
        self.node = owner
        mnode = bs.newnode('math', owner=self.node, attrs={'input1': (0, 1.2, 0), 'operation': 'add'})
        self.node.connectattr('torso_position', mnode, 'input2')
        rank_str = f"\ue01f#{rank}\ue01f" if rank <= 3 else f"#{rank}"
        self.rank_text = bs.newnode('text', owner=self.node, attrs={
            'text': rank_str, 'in_world': True, 'shadow': 1.0, 'flatness': 1.0,
            'color': (1, 1, 1), 'scale': 0.01, 'h_align': 'center'
        })
        mnode.connectattr('output', self.rank_text, 'position')

class HitPoint:
    def __init__(self, position=(0, 1.5, 0), owner=None, prefix='0', shad=1.2):
        self.node = owner
        self.m = bs.newnode('math', owner=self.node, attrs={'input1': position, 'operation': 'add'})
        self.node.connectattr('torso_position', self.m, 'input2')
        hp_val = int(prefix) / 10
        self._Text = bs.newnode('text', owner=self.node, attrs={
            'text': f"\ue047{hp_val}\ue047", 'in_world': True, 'shadow': shad, 'flatness': 1.0,
            'color': (1, 1, 1) if hp_val >= 20 else (1.0, 0.2, 0.2),
            'scale': 0.01, 'h_align': 'center'
        })
        self.m.connectattr('output', self._Text, 'position')