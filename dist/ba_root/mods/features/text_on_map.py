# Released under the MIT License. See LICENSE for details.

""" 
Position Fixed: Watermark at Bottom-Left, Title at Top-Center
Edited for ASHX SCRIPT 2026 - API 9 Optimized
Staff: Luffy (Sky Blue), Electron (Yellow), Ghost (Grey)
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

        # --- Features Sequence Data ---
        self._feature_msgs = [
            ("TOP 2 - ADMIN", (1, 1, 1)),
            ("TOP 5 - VIP", (1, 1, 1)),
            ("TOP 10 - EFFECTS + TAG", (1, 1, 1)),
            ("TOP 20 - TAG", (1, 1, 1)),
            ("JOIN DISCORD", (1, 1, 1)),
            ("🔱ASHX VS SEHU🔱" , (1, 1, 0)),
            ("BY TEAM PARADISE" , (1, 0, 1)),
            ("❣️AS PARADISE❣️" , (0, 1, 1))
        ]
        self._feature_index = 0

        # Initialize All Components
        self.left_watermark()
        self.bottom_text()
        self.nextGame(nextMap)
        self.restart_msg()
        self.clay_text()
        self.init_feature_cycle()

        if hasattr(_babase, "season_ends_in_days"):
            if _babase.season_ends_in_days < 99:
                self.season_reset(_babase.season_ends_in_days)

        if setti["leaderboard"]["enable"]:
            self.leaderBoard()
            self.staff_cycle() # Start Official Staff Cycle

        bs.timer(0.016, self._animate, repeat=True)
        self.timer = bs.timer(8, babase.Call(self.highlights_), repeat=True)

    # ================= STAFF SECTION =================
    def staff_cycle(self):
        # Create the "OFFICIAL STAFF" Title below Leaderboard
        self.staff_title = bs.newnode('text', attrs={
            'text': u"✨ OFFICIAL OGS ✨",
            'flatness': 1.0, 'h_align': 'center', 'h_attach': 'right', 'v_attach': 'top',
            'position': (-120, -185), 'scale': 0.6, 'color': (1, 1, 1)
        })
        
        # Create the cycling name node
        self.staff_node = bs.newnode('text', attrs={
            'text': "", 'flatness': 1.0, 'h_align': 'center', 'h_attach': 'right', 'v_attach': 'top',
            'position': (-120, -210), 'scale': 0.7, 'opacity': 0.0
        })
        
        # Staff Names: Luffy, Electron, Ghost
        self.staff_names = ["SEHU", "ODX", "NICK"] 
        self.current_staff_index = 0
        self.staff_timer = bs.timer(4.0, self._cycle_staff, repeat=True)
        self._cycle_staff()

    def _cycle_staff(self):
        bs.animate(self.staff_node, 'opacity', {0.0: 1.0, 0.5: 0.0})
        
        def update_staff():
            # Colors: Sky Blue, Yellow, Grey
            colors = [(0.5, 0.8, 1.0), (1.0, 1.0, 0.0), (0.6, 0.6, 0.6)] 
            
            idx = self.current_staff_index
            self.staff_node.text = self.staff_names[idx]
            self.staff_node.color = colors[idx]
            
            bs.animate(self.staff_node, 'opacity', {0.0: 0.0, 0.5: 1.0})
            self.current_staff_index = (self.current_staff_index + 1) % len(self.staff_names)
            
        bs.timer(0.5, update_staff)

    # ================= FEATURE TEXT =================
    def init_feature_cycle(self):
        self._feature_text = bs.newnode('text', attrs={
            'text': "",
            'flatness': 1.0,
            'h_align': 'right',
            'v_attach': 'bottom',
            'h_attach': 'right',
            'scale': 0.65,
            'position': (-25, 40),
            'opacity': 0.0
        })
        self._feature_timer = bs.timer(4.0, self._update_feature_cycle, repeat=True)
        self._update_feature_cycle()

    def _update_feature_cycle(self):
        bs.animate(self._feature_text, 'opacity', {0.0: 1.0, 0.5: 0.0})

        def change_text():
            msg, color = self._feature_msgs[self._feature_index]
            self._feature_text.text = msg
            self._feature_text.color = color
            bs.animate(self._feature_text, 'opacity', {0.0: 0.0, 0.5: 1.0})
            self._feature_index = (self._feature_index + 1) % len(self._feature_msgs)

        bs.timer(0.5, change_text)

    # ================= MAIN ANIMATION =================
    def _animate(self):
        self._anim_time += 0.04

        # 🔴 BROOKLYN → RED ↔ GOLD
        if hasattr(self, '_owner_name_nodes'):
            self.smooth_gradient(
                self._owner_name_nodes,
                (1.0, 0.0, 0.0),
                (1.0, 0.84, 0.0),
                speed=1.3
            )

        # 💜 ASHX → NEON PURPLE ↔ WHITE
        if hasattr(self, '_script_name_nodes'):
            self.smooth_gradient(
                self._script_name_nodes,
                (0.7, 0.0, 1.0),
                (1.0, 1.0, 1.0),
                speed=1.4
            )

        if hasattr(self, '_top_message'):
            self.smooth_gradient(self._top_message, (0.5, 0.5, 1.0), (1.0, 1.0, 1.0), speed=1.0)

    def smooth_gradient(self, nodes, c1, c2, speed=1.0):
        for i, node in enumerate(nodes):
            wave = (math.sin(self._anim_time * speed + i * 0.5) + 1) / 2

            r = c1[0] + (c2[0] - c1[0]) * wave
            g = c1[1] + (c2[1] - c1[1]) * wave
            b = c1[2] + (c2[2] - c1[2]) * wave

            node.color = (r, g, b)

    # ================= CLAY TEXT =================
    def clay_text(self):
        self.display_text = u"🔱 ✨ AS PARADISE ✨ 🔱"
        self.display_position = (0, 200)
        scale_val = 0.4
        spacing = 20
        self.nodes = []
        start_x = self.display_position[0] - (len(self.display_text) * spacing) / 2
        for i, char in enumerate(self.display_text):
            node = bs.newnode('text', attrs={
                'position': (start_x + i * spacing, self.display_position[1]),
                'big': True, 'text': char, 'trail': True,
                'shadow': 0.5, 'scale': scale_val,
                'h_align': 'center', 'v_align': 'center',
                'color': (1, 0.1, 0.1),
            })
            delay = i * 0.15
            bs.animate_array(node, 'color', 3, {
                0.0 + delay: (1.0, 0.7, 0.7),
                4.0 + delay: (0.75, 0.8, 1.0),
                7.2 + delay: (1.0, 0.7, 0.7)
            }, loop=True)
            self.nodes.append(node)

    # ================= LEFT WATERMARK =================
    def left_watermark(self):
        start_x = 25
        base_y = 67
        spacing = 10

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

        bs.newnode('text', attrs={
            'text': u" 👑 OWNER: ",
            'flatness': 1.0, 'h_align': 'left',
            'v_attach': 'bottom', 'h_attach': 'left',
            'scale': 0.6, 'position': (start_x + 5, base_y + 15),
            'color': (1, 1, 1)
        })

        self._owner_name_nodes = []
        for i, ch in enumerate("SEHU"):
            n = bs.newnode('text', attrs={
                'text': ch,
                'flatness': 1.0,
                'h_align': 'left',
                'v_attach': 'bottom',
                'h_attach': 'left',
                'scale': 0.6,
                'position': (start_x + 105 + i * spacing, base_y + 15)
            })
            self._owner_name_nodes.append(n)

        bs.newnode('text', attrs={
            'text': u" 📝 SCRIPT BY:",
            'flatness': 1.0, 'h_align': 'left',
            'v_attach': 'bottom', 'h_attach': 'left',
            'scale': 0.6,
            'position': (start_x + 5, base_y - 5),
            'color': (1, 1, 1)
        })

        self._script_name_nodes = []
        for i, ch in enumerate("ASHX"):
            n = bs.newnode('text', attrs={
                'text': ch,
                'flatness': 1.0,
                'h_align': 'left',
                'v_attach': 'bottom',
                'h_attach': 'left',
                'scale': 0.6,
                'position': (start_x + 135 + i * spacing, base_y - 5)
            })
            self._script_name_nodes.append(n)

    # ================= REST SAME =================
    def bottom_text(self):
        text = "Thanks For Playing In Our Server"
        spacing = 12
        base_y = 20
        self._bottom_text = []
        start_x = -(len(text) * spacing) / 2
        for i, ch in enumerate(text):
            n = bs.newnode('text', attrs={
                'text': ch, 'flatness': 1.0, 'h_align': 'center', 'v_attach': 'bottom',
                'scale': 0.6, 'position': (start_x + i * spacing, base_y), 'color': (1, 0, 0)
            })
            delay = i * 0.08
            bs.animate_array(n, 'color', 3, {
                0.0 + delay: (0.85, 0.85, 0.85),
                3.0 + delay: (0.65, 0.35, 0.28),
                6.0 + delay: (0.85, 0.85, 0.85),
            }, loop=True)
            self._bottom_text.append(n)

    def leaderBoard(self):
        if len(mystats.top3Name) < 3:
            return
        self.title_node = bs.newnode('text', attrs={
            'text': u"\U0001F451 LEADERBOARD \U0001F451",
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
            'scale': 0.7, 'position': (-25, 16), 'color': (1.0, 1.0, 1.0)
        })

    def highlights_(self):
        if not self.highlights:
            return
        color = (random.random(), random.random(), random.random()) if setti["textonmap"]['center highlights']["randomColor"] else tuple(setti["textonmap"]["center highlights"]["color"])
        node = bs.newnode('text', attrs={
            'text': self.highlights[self.index],
            'flatness': 1.0, 'h_align': 'center', 'v_attach': 'bottom',
            'scale': 1, 'position': (0, 138), 'color': color
        })
        bs.timer(7, node.delete)
        self.index = int((self.index + 1) % len(self.highlights))

    def season_reset(self, text):
        bs.newnode('text', attrs={
            'text': "Season ends in: " + str(text) + " days",
            'flatness': 5.0, 'h_align': 'right', 'v_attach': 'bottom', 'h_attach': 'right',
            'scale': 0.7, 'position': (-25, 65), # Shifted up to avoid overlap
            'color': (1.0, 1.0, 1.0)
        })

    def restart_msg(self):
        if hasattr(_babase, 'restart_scheduled'):
            bs.get_foreground_host_activity().restart_msg = bs.newnode('text', attrs={
                'text': "Server going to restart after this series.",
                'flatness': 1.0, 'h_align': 'right', 'v_attach': 'bottom', 'h_attach': 'right',
                'scale': 0.5, 'position': (-25, 90), # Shifted up
                'color': (1, 0.5, 0.7)
            })
 
