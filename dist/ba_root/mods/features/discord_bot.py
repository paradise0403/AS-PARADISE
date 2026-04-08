# ba_meta require api 9
# ba_meta export babase.Plugin

# ---------------- AUDIOOP FIX ----------------
import sys
from types import ModuleType

if 'audioop' not in sys.modules:
    mock_audioop = ModuleType('audioop')
    mock_audioop.mul = lambda cp, size, factor: cp
    mock_audioop.tomono = lambda cp, size, fac1, fac2: cp
    sys.modules['audioop'] = mock_audioop

# ---------------- IMPORTS ----------------

import os
import json
import asyncio
import logging
from threading import Thread
from datetime import datetime, timezone
from collections import deque
import threading

import discord
from discord.ext.commands import Bot

import babase
import bascenev1 as bs

# ---------------- LOAD SETTINGS ----------------

SETTINGS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "setting.json"
)

with open(SETTINGS_PATH, "r") as f:
    settings = json.load(f)

dc = settings.get("discordbot", {})

ENABLE = dc.get("enable", False)
TOKEN = dc.get("token")
LOGS_CHANNEL_ID = dc.get("logsChannelID")
STATS_CHANNEL_ID = dc.get("liveStatsChannelID")

# ---------------- LOAD CONFIG ----------------

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..",
    "config.json"
)

server_config = {}

try:
    with open(CONFIG_PATH, "r") as f:
        server_config = json.load(f)
except Exception as e:
    print("[CONFIG ERROR]", e)

def get_config(key, default):
    return server_config.get(key, default)

# ---------------- WEBSITE API ----------------

API_URL = "http://65.1.65.75:3000/api/update"
API_KEY = "ASHX_SECRET"
_cached_ip = None

def get_public_ip():
    global _cached_ip
    if _cached_ip:
        return _cached_ip
    try:
        import requests
        ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
        _cached_ip = ip
        return ip
    except:
        return "127.0.0.1"

def update_web_server(player_count, current_map, next_map):
    def task():
        try:
            import requests
            requests.post(API_URL, json={
                "name": get_config("party_name", "SERVER"),
                "ip": get_public_ip(),
                "port": get_config("port", 43210),
                "players": player_count,
                "currentMap": current_map,
                "nextMap": next_map,
                "status": "online",
                "key": API_KEY
            }, timeout=3)
        except Exception as e:
            print("[WEB ERROR]", e)

    Thread(target=task, daemon=True).start()

# ---------------- UTILS ----------------

def push_log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"

    if logs and logs[-1].split("] ", 1)[-1] == msg:
        return

    logs.append(entry)

def clean_bs_text(text: str) -> str:
    return ''.join(ch for ch in text if not (0xE000 <= ord(ch) <= 0xF8FF))

# ---------------- DATA ----------------

chat_buffer = deque(maxlen=15)
player_info = {}
chat_lock = threading.Lock()

stats = {}
logs = []

stats_message = None
chat_message = None

_last_stats_content = None
_last_chat_content = None

# ---------------- DISCORD ----------------

logging.getLogger('asyncio').setLevel(logging.WARNING)

intents = discord.Intents.all()
client = Bot(command_prefix='!', intents=intents)

REFRESH_INTERVAL = 12
LOG_FLUSH_INTERVAL = 20

# ---------------- INIT ----------------

def init():
    if not ENABLE:
        print("[Discord] Disabled")
        return
    if not TOKEN:
        print("[Discord] Token missing")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(client.start(TOKEN))
    Thread(target=loop.run_forever, daemon=True).start()

# ---------------- EVENTS ----------------

@client.event
async def on_ready():
    print(f"[Discord] Logged in as {client.user}")
    await prepare_messages()
    client.loop.create_task(update_loop())
    client.loop.create_task(send_logs_loop())

# ---------------- MESSAGE SETUP ----------------

async def prepare_messages():
    global stats_message, chat_message
    channel = client.get_channel(STATS_CHANNEL_ID)

    bot_msgs = []
    async for msg in channel.history(limit=10):
        if msg.author.id == client.user.id:
            bot_msgs.append(msg)

    if bot_msgs:
        stats_message = bot_msgs[0]
        await stats_message.edit(embed=build_stats_embed())
        chat_message = bot_msgs[1] if len(bot_msgs) > 1 else None
    else:
        stats_message = await channel.send(embed=build_stats_embed())
        chat_message = None

# ---------------- EMBEDS (UNCHANGED STYLE) ----------------

def build_stats_embed():
    embed = discord.Embed(
        title=f"🎮 {get_config('party_name','SERVER')} Live Stats",
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc)
    )

    roster = stats.get("roster", {})

    if roster:
        lines = []
        for pbid, p in roster.items():
            v2 = clean_bs_text(p['device_id'])
            name = clean_bs_text(p['name'])

            if name == v2:
                line1 = f"👤{{<:v2:1462179402535272550>{v2}}}<:v2:1462179402535272550>{name}"
            else:
                line1 = f"👤{{<:v2:1462179402535272550>{v2}}}{name}"

            lines.append(line1)
            lines.append(f"📋 [{pbid}]")
            lines.append("")

        players = "\n".join(lines).strip()
    else:
        players = "No players online"

    embed.add_field(name="👥 Players", value=players, inline=False)

    playlist = stats.get("playlist", {})
    embed.add_field(
        name="🗺️ Map",
        value=f"**Current:** {playlist.get('current','-')}\n"
              f"**Next:** {playlist.get('next','-')}",
        inline=False
    )

    return embed

def build_chat_embed():
    embed = discord.Embed(
        title="💬 Live Chat",
        color=discord.Color.blurple(),
        timestamp=datetime.now(timezone.utc)
    )

    with chat_lock:
        embed.description = "\n".join(chat_buffer)

    return embed

# ---------------- LOOP ----------------

def _embed_key(embed):
    return str(embed.to_dict())

async def update_loop():
    global _last_stats_content, _last_chat_content

    while not client.is_closed():
        try:
            stats_embed = build_stats_embed()
            key = _embed_key(stats_embed)

            if key != _last_stats_content:
                await stats_message.edit(embed=stats_embed)
                _last_stats_content = key

            await asyncio.sleep(2)

            with chat_lock:
                has_chat = bool(chat_buffer)

            channel = client.get_channel(STATS_CHANNEL_ID)

            if has_chat:
                chat_embed = build_chat_embed()
                ckey = _embed_key(chat_embed)

                if chat_message is None:
                    chat_message = await channel.send(embed=chat_embed)
                    _last_chat_content = ckey
                elif ckey != _last_chat_content:
                    await chat_message.edit(embed=chat_embed)
                    _last_chat_content = ckey
            else:
                if chat_message:
                    await chat_message.delete()
                    chat_message = None
                    _last_chat_content = None

        except Exception:
            pass

        await asyncio.sleep(REFRESH_INTERVAL)

async def send_logs_loop():
    channel = client.get_channel(LOGS_CHANNEL_ID)

    while not client.is_closed():
        await asyncio.sleep(LOG_FLUSH_INTERVAL)

        if logs:
            text = "\n".join(logs[:20])
            logs.clear()

            try:
                await channel.send(f"```\n{text}\n```")
            except:
                pass

# ---------------- BOMBSQUAD ----------------

class BsDataThread:
    def __init__(self):
        self.timer = bs.AppTimer(5, babase.Call(self.refresh_stats), repeat=True)

    def refresh_stats(self):
        global stats

        roster = {}
        for p in bs.get_game_roster():
            try:
                roster[p['account_id']] = {
                    'name': p['players'][0]['name_full'],
                    'device_id': p['display_string']
                }
            except:
                roster[p['account_id']] = {
                    'name': "<in-lobby>",
                    'device_id': p['display_string']
                }

        current_map = "-"
        next_map = "-"

        try:
            session = bs.get_foreground_host_session()
            next_map = session.get_next_game_description().evaluate()

            spec = session._current_game_spec
            gtype = spec['resolved_type']
            current_map = gtype.get_settings_display_string(spec).evaluate()
        except:
            pass

        stats['roster'] = roster
        stats['playlist'] = {
            'current': current_map,
            'next': next_map
        }

        # 🌐 WEBSITE UPDATE
        update_web_server(len(roster), current_map, next_map)

# ---------------- PLUGIN ----------------

class DiscordBotPlugin(babase.Plugin):
    def on_app_running(self):
        init()
        BsDataThread()
