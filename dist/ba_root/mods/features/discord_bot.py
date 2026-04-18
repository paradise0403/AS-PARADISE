# ba_meta require api 9
# ba_meta export babase.Plugin

import sys
from types import ModuleType
if 'audioop' not in sys.modules:
    m = ModuleType('audioop')
    m.mul = lambda *a: a[0]
    m.tomono = lambda *a: a[0]
    sys.modules['audioop'] = m

import os, json, asyncio, logging, hashlib
from threading import Thread
from datetime import datetime, timezone
from collections import deque
import threading

import discord
from discord.ext.commands import Bot
from discord.ui import View, Button

import babase
import bascenev1 as bs

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(__file__)
SETTINGS_PATH = os.path.join(BASE_DIR, "..", "setting.json")
STATS_JSON_PATH = os.path.join(BASE_DIR, "..", "stats", "stats.json")
STATS_MSG_PATH = os.path.join(BASE_DIR, "..", "stats_message.json")

# ---------------- SETTINGS ----------------
with open(SETTINGS_PATH) as f:
    settings = json.load(f)

dc = settings.get("discordbot", {})
ENABLE = dc.get("enable", False)
TOKEN = dc.get("token")
LOGS_CHANNEL_ID = dc.get("logsChannelID")
STATS_CHANNEL_ID = dc.get("liveStatsChannelID")

# ---------------- CONFIG ----------------
CONFIG_PATH = os.path.join(BASE_DIR, "..", "..", "..", "..", "config.json")
try:
    with open(CONFIG_PATH) as f:
        server_config = json.load(f)
except:
    server_config = {}

def get_config(k, d): return server_config.get(k, d)

# ---------------- WEB ----------------
API_URL = "http://65.1.65.75:3000/api/update"
API_KEY = "ASHX_SECRET"
_cached_ip = None

def get_public_ip():
    global _cached_ip
    if _cached_ip: return _cached_ip
    try:
        import requests
        _cached_ip = requests.get("https://api.ipify.org").text.strip()
    except:
        _cached_ip = "127.0.0.1"
    return _cached_ip

def update_web(players, cm, nm):
    def t():
        try:
            import requests
            requests.post(API_URL, json={
                "name": get_config("party_name","SERVER"),
                "ip": get_public_ip(),
                "port": get_config("port",43210),
                "players": players,
                "currentMap": cm,
                "nextMap": nm,
                "status":"online",
                "key": API_KEY
            }, timeout=3)
        except: pass
    Thread(target=t, daemon=True).start()

# ---------------- UTILS ----------------
def clean(t): return ''.join(c for c in t if not (0xE000 <= ord(c) <= 0xF8FF))

def hash_msg(m): return hashlib.md5(m.encode()).hexdigest()

def push_log(msg):
    if logs and logs[-1] == msg:
        return
    logs.append(msg)

def add_chat(msg):
    global last_chat
    msg = clean(msg)
    if ">" in msg:
        msg = msg.split(">")[-1]
    msg = msg.replace(" - ", ":").strip()
    if ":" not in msg:
        return
    try:
        parts = msg.rsplit(":", 1)
        text = parts[1].strip()
        remaining = parts[0].strip()
        if ":" in remaining:
            name = remaining.rsplit(":", 1)[-1].strip()
        else:
            name = remaining.strip()
        name = name.replace("", "").replace("**", "").strip()
        if " " in name:
            name = name.split(" ")[-1]
    except:
        return
    if not name or not text:
        return
    key = f"{name.lower()}:{text.lower()}"
    if key == last_chat:
        return
    last_chat = key
    display = f"{name}: {text}"
    with chat_lock:
        chat_buffer.append(display)

def send_to_game(msg):
    """Safely send message to game chat."""
    try:
        if bs.get_foreground_host_session() is not None:
            bs.chatmessage(msg)
    except: pass

def save_stats_msg_id(mid):
    try:
        with open(STATS_MSG_PATH, "w") as f:
            json.dump({"message_id": mid}, f)
    except: pass

def load_stats_msg_id():
    try:
        with open(STATS_MSG_PATH) as f:
            return json.load(f).get("message_id")
    except: return None

# ---------------- DATA ----------------
chat_buffer = deque(maxlen=15)
chat_hashes = deque(maxlen=50)
chat_lock = threading.Lock()

stats = {}
logs = []
player_info = {}

stats_message = None
chat_message = None
_last_stats = ""
last_chat = ""

# ---------------- LEADERBOARD ----------------
def load_lb():
    try:
        with open(STATS_JSON_PATH) as f:
            data = json.load(f)
        if "stats" in data:
            data = data["stats"]
        players = []
        for p in data.values():
            players.append({
                "name": clean(p.get("name","Unknown")),
                "score": int(p.get("scores",0)),
                "kills": int(p.get("kills",0)),
                "deaths": int(p.get("deaths",0)),
                "kd": round(float(p.get("kd",0)),2)
            })
        players.sort(key=lambda x: x["score"], reverse=True)
        return players[:5]
    except: return []

# ---------------- DISCORD ----------------
client = Bot(command_prefix='s!', intents=discord.Intents.all())

class ChatBtn(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="LIVE CHAT", style=discord.ButtonStyle.primary, custom_id="chat_toggle_btn")
    async def toggle(self, interaction: discord.Interaction, button: Button):
        global chat_message
        await interaction.response.defer()
        if chat_message:
            try: await chat_message.delete()
            except: pass
            chat_message = None
            return
        chat_message = await interaction.channel.send(embed=build_chat())

# ---------------- EMBEDS ----------------
def build_stats():
    embed = discord.Embed(
        title=f"  {get_config('party_name','SERVER')}",
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc)
    )
    pl = stats.get("playlist", {})
    embed.add_field(name=" Maps", value=f"**Current**: {pl.get('current','-')}\n**Next**: {pl.get('next','-')}", inline=False)
    embed.add_field(name=" Server", value=f"**IP**: `{get_public_ip()}`\n**Port**: `{get_config('port',43210)}`", inline=False)
    
    roster = stats.get("roster", {})
    embed.add_field(name=" Players", value=f"{len(roster)} Online", inline=False)
    
    if roster:
        txt = "\n".join([f" {clean(v['name'])} `[{k}]`" for k,v in roster.items()])
    else:
        txt = "*Server is empty...*"
    embed.add_field(name=" Player List", value=txt, inline=False)

    lb = load_lb()
    if lb:
        txt = ""
        for i, p in enumerate(lb, 1):
            txt += f"**{i}. {p['name']}**\n Score:{p['score']} | K:{p['kills']} | D:{p['deaths']} | KD:{p['kd']}\n\n"
    else:
        txt = "No data available"
    embed.add_field(name=" Leaderboard", value=txt, inline=False)
    return embed

def build_chat():
    embed = discord.Embed(title=" Live Game Chat", color=discord.Color.blurple())
    with chat_lock:
        lines = []
        for m in chat_buffer:
            if ":" in m:
                name, text = m.split(":", 1)
                lines.append(f" **{name.strip()}**: {text.strip()}")
            else:
                lines.append(f" {m}")
        embed.description = "\n".join(lines) if lines else "No chat yet..."
    return embed

# ---------------- LOOPS ----------------
async def stats_loop():
    global _last_stats
    while not client.is_closed():
        try:
            if stats_message:
                e = build_stats()
                k = str(e.to_dict())
                if k != _last_stats:
                    await stats_message.edit(embed=e)
                    _last_stats = k
        except: pass
        await asyncio.sleep(8)

async def chat_loop():
    while not client.is_closed():
        await asyncio.sleep(2)
        if chat_message:
            try: await chat_message.edit(embed=build_chat())
            except: pass

async def log_loop():
    ch = client.get_channel(LOGS_CHANNEL_ID)
    while not client.is_closed():
        await asyncio.sleep(4)
        if logs and ch:
            txt = "\n".join(logs[:20])
            logs.clear()
            try: await ch.send(embed=discord.Embed(title=" Live Logs", description=txt, color=0x2f3136))
            except: pass

async def prepare_message():
    global stats_message
    ch = client.get_channel(STATS_CHANNEL_ID)
    if not ch: return

    # 1. Delete Old Message from logic
    msg_id = load_stats_msg_id()
    if msg_id:
        try:
            old_msg = await ch.fetch_message(int(msg_id))
            await old_msg.delete()
        except: pass

    # 2. Cleanup channel history for safety
    try:
        async for msg in ch.history(limit=10):
            if msg.author.id == client.user.id:
                await msg.delete()
    except: pass

    # 3. Send Fresh Message
    stats_message = await ch.send(embed=build_stats(), view=ChatBtn())
    save_stats_msg_id(stats_message.id)

@client.event
async def on_message(message):
    if message.author.bot or message.channel.id != LOGS_CHANNEL_ID or not message.content:
        return
    try:
        formatted_msg = f"{message.author.name}: {message.content}"
        bs.pushcall(lambda: send_to_game(formatted_msg), from_other_thread=True)
    except Exception as e:
        print(f"Discord to Game Chat Error: {e}")
    await client.process_commands(message)

@client.event
async def on_ready():
    print("Bot Ready")
    await prepare_message()
    client.loop.create_task(stats_loop())
    client.loop.create_task(chat_loop())
    client.loop.create_task(log_loop())

# ---------------- BS THREAD ----------------
class BsDataThread:
    def __init__(self):
        self.old_roster = {}
        self._last_msg_raw = None
        self.timer = bs.AppTimer(2, babase.Call(self.update), repeat=True)

    def update(self):
        global stats
        roster = {}
        for p in bs.get_game_roster():
            try: roster[p['account_id']] = {'name': p['players'][0]['name_full']}
            except: pass
        new_ids, old_ids = set(roster.keys()), set(self.old_roster.keys())
        for p in new_ids - old_ids: push_log(f" JOIN: {roster[p]['name']}")
        for p in old_ids - new_ids: push_log(f" LEFT: {self.old_roster[p]['name']}")
        self.old_roster = roster
        try:
            msgs = bs.get_chat_messages()
            if msgs:
                raw_last = msgs[-1]
                if raw_last != self._last_msg_raw:
                    add_chat(raw_last)
                    self._last_msg_raw = raw_last
        except: pass
        cm, nm = "-", "-"
        try:
            s = bs.get_foreground_host_session()
            nm = s.get_next_game_description().evaluate()
            cm = s._current_game_spec['resolved_type'].get_settings_display_string(s._current_game_spec).evaluate()
        except: pass
        stats['roster'] = roster
        stats['playlist'] = {'current': cm, 'next': nm}
        update_web(len(roster), cm, nm)

def init():
    if not ENABLE or not TOKEN: return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(client.start(TOKEN))
    Thread(target=loop.run_forever, daemon=True).start()

class DiscordBotPlugin(babase.Plugin):
    def on_app_running(self):
        init()
        BsDataThread()
 