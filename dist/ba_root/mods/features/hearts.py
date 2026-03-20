import random
from typing import Any, Sequence
import babase
import bascenev1 as bs

class PopupText(bs.Actor):
    """Text that pops up above a position to denote something special."""

    def __init__(
        self,
        text: str | babase.Lstr,
        position: Sequence[float] = (0.0, 0.0, 0.0),
        color: Sequence[float] = (1.0, 1.0, 1.0, 1.0),
        random_offset: float = 0.5,
        offset: Sequence[float] = (0.0, 0.0, 0.0),
        scale: float = 1.0,
    ):
        super().__init__()
        if len(color) == 3:
            color = (color[0], color[1], color[2], 1.0)
        
        pos = (
            position[0] + offset[0] + random_offset * (0.5 - random.random()),
            position[1] + offset[1] + random_offset * (0.5 - random.random()),
            position[2] + offset[2] + random_offset * (0.5 - random.random()),
        )

        self.node = bs.newnode(
            'text',
            attrs={
                'text': text,
                'in_world': True,
                'shadow': 1.0,
                'flatness': 1.0,
                'h_align': 'center',
            },
            delegate=self,
        )

        lifespan = 10.5

        # Animation: Scale/Pop effect
        bs.animate(
            self.node,
            'scale',
            {
                0: 0.0,
                lifespan * 0.11: 0.014 * scale,
                lifespan * 0.25: 0.011 * scale,
                lifespan * 0.95: 0.011 * scale,
            },
        )

        # Animation: Float Upward
        self._tcombine = bs.newnode(
            'combine',
            owner=self.node,
            attrs={'input0': pos[0], 'input2': pos[2], 'size': 3},
        )
        bs.animate(
            self._tcombine, 'input1', {0: pos[1], lifespan: pos[1] + 6.0}
        )
        self._tcombine.connectattr('output', self.node, 'position')

        # Animation: Color & Fade
        self._combine = bs.newnode(
            'combine',
            owner=self.node,
            attrs={
                'input0': color[0],
                'input1': color[1],
                'input2': color[2],
                'size': 4,
            },
        )
        bs.animate(
            self._combine,
            'input3',
            {
                0: 0,
                0.1 * lifespan: color[3],
                0.8 * lifespan: color[3],
                lifespan: 0,
            },
        )
        self._combine.connectattr('output', self.node, 'color')

        # Self-destruct timer
        self._die_timer = bs.Timer(
            lifespan, bs.WeakCall(self.handlemessage, bs.DieMessage())
        )

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
        else:
            super().handlemessage(msg)


def spawn_icons():
    """Spawns a random selection of icons across the map."""
    activity = bs.get_foreground_host_activity()
    if activity is None:
        return

    if not hasattr(activity, "spawned_nodes"):
        activity.spawned_nodes = []

    # The list of icons you requested: Heart, Star, Lightning
    icons = [u"\ue047", u"\ue048", u"\ue043"]
    
    if hasattr(activity, "map"):
        bounds = activity.map.get_def_bound_box("area_of_interest_bounds")
        
        # Spawn 4 random icons each time the timer hits
        for _ in range(4):
            position = (
                random.uniform(bounds[0], bounds[3]),
                random.uniform(bounds[1], bounds[4]), # Better height variety
                random.uniform(bounds[2], bounds[5])
            )
            
            chosen_icon = random.choice(icons)
            # Pick a random color for each icon
            rand_color = (random.random(), random.random(), random.random())

            with activity.context:
                node = PopupText(chosen_icon, position, color=rand_color)
                activity.spawned_nodes.append(node)

def start(activity):
    # Triggers every 7-8 seconds
    bs.timer(random.uniform(7, 8), spawn_icons, repeat=True)

# Patch it into the Activity class
bs._activity.Activity.hearts_generator = start
