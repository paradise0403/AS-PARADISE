# Released under the MIT License. See LICENSE for details.

""" 
Position Fixed: Watermark at Bottom-Left, Title at Top-Center
Edited for ASHX SCRIPT 2026 - API 9 Optimized
"""

import random
import _babase
import setting
from stats import mystats
import babase
import bascenev1 as bs
import math

setti = setting.get_settings_data()

class textonmap:

    def __init__(self):
        data = setti['textonmap']
        left = data['bottom left watermark']
        top = data['top watermark']
        nextMap = ""
        try:
            nextMap = bs.get_foreground_host_session().get_next_game_description().evaluate()
        except:
            pass
        try:
            top = top.replace("@IP", _babase.our_ip).replace("@PORT",
                                                             str(_babase.our_port))
        except:
            pass

        self.index = 0
        self.highlights = data['center highlights']["msg"]
        self._anim_time = 0.0

        # Initialize All Components
        self.left_watermark()
        self.top_message("ASHX SCRIPT 2026")
        self.nextGame(nextMap)
        self.restart_msg()

        if hasattr(_babase, "season_ends_in_days"):
            if _babase.season_ends_in_days < 9:
                self.season_reset(_babase.season_ends_in_days)

        # Start Fading Leaderboard if enabled
        if setti["leaderboard"]["enable"]:
            self.leaderBoard()

        # Global animation timer for gradients
        bs.timer(0.016, self._animate, repeat=True)
        
        # Highlights timer
        self.timer = bs.timer(8, babase.Call(self.highlights_), repeat=True)

    def _animate(self):
        self._anim_time += 0.03
        
        # Animate Watermark Gradients
        if hasattr(self, '_owner_name_nodes'):
            self.smooth_gradient(self._owner_name_nodes, (0.4, 1.0, 0.4), (1.0, 1.0, 0.0), speed=1.2)
        if hasattr(self, '_script_name_nodes'):
            self.smooth_gradient(self._script_name_nodes, (1.0, 0.5, 0.0), (1.0, 0.2, 0.2), speed=1.2)

    def smooth_gradient(self, nodes, c1, c2, speed=0.6):
        for i, node in enumerate(nodes):
            wave = (math.sin(self._anim_time * speed + i * 0.4) + 1) / 2
            r = c1[0] + (c2[0] - c1[0]) * wave
            g = c1[1] + (c2[1] - c1[1]) * wave
            b = c1[2] + (c2[2] - c1[2]) * wave
            node.color = (r, g, b)

    def left_watermark(self):
        """ Boxed style watermark moved back to Bottom-Left """
        start_x = 25
        base_y = 67
        spacing = 10
        
        # --- BORDER BOX (Green Lines) ---
        bs.newnode('text', attrs={
            'text': '__________________________________',
            'h_align': 'left', 'v_attach': 'bottom', 'h_attach': 'left',
            'scale': 0.5, 'position': (start_x, base_y + 35), 'color': (0.2, 1.0, 0.2)
        })
        bs.newnode('text', attrs={
            'text': '__________________________________',
            'h_align': 'left', 'v_attach': 'bottom', 'h_attach': 'left',
            'scale': 0.5, 'position': (start_x, base_y - 15), 'color': (0.2, 1.0, 0.2)
        })

        # --- OWNER LINE ---
        bs.newnode('text', attrs={
            'text': " [👑] OWNER: ",
            'flatness': 1.0, 'h_align': 'left', 'v_attach': 'bottom', 'h_attach': 'left',
            'scale': 0.6, 'position': (start_x + 5, base_y + 15), 'color': (1, 1, 1)
        })
        self._owner_name_nodes = []
        for i, ch in enumerate("ASHX & SEHU"):
            n = bs.newnode('text', attrs={
                'text': ch, 'flatness': 1.0, 'h_align': 'left', 'v_attach': 'bottom', 'h_attach': 'left',
                'scale': 0.6, 'position': (start_x + 105 + i * spacing, base_y + 15)
            })
            self._owner_name_nodes.append(n)

        # --- SCRIPT LINE ---
        bs.newnode('text', attrs={
            'text': " [📝] SCRIPT BY:",
            'flatness': 1.0, 'h_align': 'left', 'v_attach': 'bottom', 'h_attach': 'left',
            'scale': 0.6, 'position': (start_x + 5, base_y - 5), 'color': (1, 1, 1)
        })
        self._script_name_nodes = []
        for i, ch in enumerate("ASHX"):
            n = bs.newnode('text', attrs={
                'text': ch, 'flatness': 1.0, 'h_align': 'left', 'v_attach': 'bottom', 'h_attach': 'left',
                'scale': 0.6, 'position': (start_x + 135 + i * spacing, base_y - 5)
            })
            self._script_name_nodes.append(n)

    def top_message(self, text_val):
        """ Title reset to Top-Center"""
        # Shadow
        bs.newnode('text', attrs={
            'text': text_val, 'flatness': 1.0, 'h_align': 'center', 'v_attach': 'top',
            'scale': 1.3, 'position': (2, -72), 'color': (0.1, 0.1, 0.1), 'opacity': 0.8
        })
        # Main Text
        self.top_text = bs.newnode('text', attrs={
            'text': text_val, 'flatness': 1.0, 'h_align': 'center', 'v_attach': 'top',
            'scale': 1.3, 'position': (0, -70), 'color': (0.9, 0.9, 0.9) # Clean White-ish
        })

    def leaderBoard(self):
        if len(mystats.top3Name) < 3: return
        self.title_node = bs.newnode('text', attrs={
            'text': "👑 LEADERBOARD 👑",
            'flatness': 1.0, 'h_align': 'center', 'h_attach': 'right', 'v_attach': 'top',
            'position': (-120, -110), 'scale': 0.8, 'color': (1, 0.8, 0)
        })
        self.rank_node = bs.newnode('text', attrs={
            'text': "", 'flatness': 1.0, 'h_align': 'center', 'h_attach': 'right', 'v_attach': 'top',
            'position': (-120, -140), 'scale': 0.75, 'opacity': 0.0
        })
        self.current_rank_index = 0
        self.cycle_timer = bs.timer(3.5, self._cycle_ranks, repeat=True)
        self._cycle_ranks()

    def _cycle_ranks(self):
        bs.animate(self.rank_node, 'opacity', {0.0: 1.0, 0.5: 0.0})
        def update_and_fade_in():
            names = mystats.top3Name
            idx = self.current_rank_index
            colors = [(0.3, 0.6, 1.0), (1.0, 0.2, 0.2), (0.2, 0.8, 0.3)]
            self.rank_node.text = f"{idx+1}. {names[idx][:10]}"
            self.rank_node.color = colors[idx]
            bs.animate(self.rank_node, 'opacity', {0.0: 0.0, 0.5: 1.0})
            self.current_rank_index = (self.current_rank_index + 1) % 3
        bs.timer(0.5, update_and_fade_in)

    def nextGame(self, text):
        bs.newnode('text', attrs={
            'text': "Next : " + text,
            'flatness': 1.0, 'h_align': 'right', 'v_attach': 'bottom', 'h_attach': 'right',
            'scale': 0.7, 'position': (-25, 16), 'color': (0.5, 0.5, 0.5)
        })

    def highlights_(self):
        if setti["textonmap"]['center highlights']["randomColor"]:
            color = (random.random(), random.random(), random.random())
        else:
            color = tuple(setti["textonmap"]["center highlights"]["color"])
        node = bs.newnode('text', attrs={
            'text': self.highlights[self.index], 'flatness': 1.0, 'h_align': 'center',
            'v_attach': 'bottom', 'scale': 1, 'position': (0, 138), 'color': color
        })
        self.delt = bs.timer(7, node.delete)
        self.index = int((self.index + 1) % len(self.highlights))

    def season_reset(self, text):
        bs.newnode('text', attrs={
            'text': "Season ends in: " + str(text) + " days",
            'flatness': 2.0, 'h_align': 'right', 'v_attach': 'bottom', 'h_attach': 'right',
            'scale': 0.5, 'position': (-25, 34), 'color': (0.6, 0.5, 0.7)
        })

    def restart_msg(self):
        if hasattr(_babase, 'restart_scheduled'):
            _babase.get_foreground_host_activity().restart_msg = bs.newnode('text', attrs={
                'text': "Server going to restart after this series.",
                'flatness': 1.0, 'h_align': 'right', 'v_attach': 'bottom', 'h_attach': 'right',
                'scale': 0.5, 'position': (-25, 54), 'color': (1, 0.5, 0.7)
            })
 
