import babase
import bascenev1 as bs
import os
import json
import random
from bascenev1lib.actor.spaz import Spaz

# --- STORAGE SETUP ---
try:
    BASE_PATH = babase.env().get('python_directory_user', '.')
    DATA_DIR = os.path.join(BASE_PATH, 'playersData')
    DATA_FILE = os.path.join(DATA_DIR, 'pets.json')
except:
    DATA_DIR = 'mods/playersData'
    DATA_FILE = 'mods/playersData/pets.json'

def ensure_storage():
    if not os.path.exists(DATA_DIR):
        try: os.makedirs(DATA_DIR, exist_ok=True)
        except: pass
    if not os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump({}, f)
        except: pass

def save_pet_owner(aid):
    if not aid: return
    ensure_storage()
    try: 
        data = {}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
        data[aid] = True
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except: pass

# --- PET SPAZ ACTOR ---
class Pet(bs.Actor):
    def __init__(self, target_node: bs.Node, color=(1,1,1), highlight=(1,1,1)):
        super().__init__()
        self.target_node = target_node
        self._activations = []
        
        # Spawning a mini Spaz as a pet (Like Ender Bot but smaller)
        self.spaz = Spaz(
            color=color,
            highlight=highlight,
            character='Agent Johnson' # You can change this to any character
        )
        
        self.node = self.spaz.node
        if self.node.exists():
            # Making it small and ghost-like
            self.node.model_scale = 0.35
            self.node.gravity_scale = 0.0 # Floating
            self.node.invincible = True
            self.node.can_be_activated = False
            self.node.name = "🐾"

        # Update timer
        self._activations.append(
            bs.Timer(0.03, babase.Call(self._update), repeat=True)
        )

    def _update(self):
        if not self.target_node or not self.target_node.exists() or not self.node or not self.node.exists():
            self.handlemessage(bs.DieMessage())
            return
        
        try:
            t_pos = self.target_node.position
            # Follow position (slightly above and behind)
            dest = (t_pos[0] - 0.6, t_pos[1] + 1.3, t_pos[2])
            curr = self.node.position
            
            # Smooth interpolation
            self.node.position = (
                curr[0] + (dest[0] - curr[0]) * 0.12,
                curr[1] + (dest[1] - curr[1]) * 0.12,
                curr[2] + (dest[2] - curr[2]) * 0.12
            )
            
            # Make the pet face the same direction as player
            self.node.handlemessage(bs.StandMessage(self.node.position, 0))
            
        except:
            self.handlemessage(bs.DieMessage())

    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            if self.spaz:
                self.spaz.handlemessage(bs.DieMessage())
            self._activations = []
        else:
            super().handlemessage(msg)

# --- LOGIC ---
def do_spawn(client_id: int):
    activity = bs.get_foreground_host_activity()
    if not activity: return

    for player in activity.players:
        try:
            if player.sessionplayer.inputdevice.client_id == client_id:
                if player.actor and player.actor.node.exists():
                    with activity.context:
                        attr_name = f'_pet_{client_id}'
                        
                        # Cleanup old
                        old = getattr(activity, attr_name, None)
                        if old:
                            try: old.handlemessage(bs.DieMessage())
                            except: pass
                        
                        # New Pet with player colors
                        new_pet = Pet(
                            player.actor.node, 
                            color=player.color, 
                            highlight=player.highlight
                        )
                        setattr(activity, attr_name, new_pet)
                        
                        # Save
                        aid = player.sessionplayer.get_v1_account_id()
                        if aid: save_pet_owner(aid)
                        return
        except: continue

def handle_pet_command(arguments, client_id):
    activity = bs.get_foreground_host_activity()
    if not activity: return
    try:
        target_id = int(arguments[1]) if (len(arguments) > 1 and arguments[1].isdigit()) else client_id
        with activity.context:
            babase.pushcall(babase.Call(do_spawn, target_id))
    except: pass

def auto_spawn_check():
    activity = bs.get_foreground_host_activity()
    if not activity or not os.path.exists(DATA_FILE): return
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except: return

    for player in activity.players:
        try:
            aid = player.sessionplayer.get_v1_account_id()
            if aid and aid in data:
                cid = player.sessionplayer.inputdevice.client_id
                if not hasattr(activity, f'_pet_{cid}'):
                    with activity.context:
                        babase.pushcall(babase.Call(do_spawn, cid))
        except: continue

bs.AppTimer(10.0, babase.Call(auto_spawn_check), repeat=True)