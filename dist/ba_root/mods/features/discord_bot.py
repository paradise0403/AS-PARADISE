import asyncio
import logging
from threading import Thread
from datetime import datetime, timezone

import discord
from discord.ext.commands import Bot

import babase
import bascenev1 as bs
from collections import deque
import threading

# ---------------- UTILS ----------------

def push_log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"

    # Deduplicate: skip if the last log entry has the same message content
    if logs and logs[-1].split("] ", 1)[-1] == msg:
        return

    logs.append(entry)

def clean_bs_text(text: str) -> str:
    # Remove BombSquad private-use unicode chars (cause □ in Discord)
    return ''.join(
        ch for ch in text
        if not (0xE000 <= ord(ch) <= 0xF8FF)
    )

# ---------------- DATA ----------------

chat_buffer = deque(maxlen=15)
player_info = {}
chat_lock = threading.Lock()

stats = {}
logs = []

stats_message = None
chat_message = None

# Track last embed content to skip unnecessary edits
_last_stats_content = None
_last_chat_content = None

# ---------------- BASIC SETUP ----------------

logging.getLogger('asyncio').setLevel(logging.WARNING)

intents = discord.Intents.all()
client = Bot(command_prefix='!', intents=intents)

TOKEN = "MTQ2MjA0ODUxNTAxNzY3NDg1Mw.GN9Wwu.ZgeHzutuksg6ME2e7of-kytEI4RY4va4tghrUU"
LOGS_CHANNEL_ID = 1476067914535932047
STATS_CHANNEL_ID = 1475343168563052634

# ============================================================
# ⏱️  INTERVAL SETTINGS — edit these to your liking
#
# REFRESH_INTERVAL: How often (seconds) the stats & chat
#   embeds are updated in Discord.
#   ⚠️  Minimum recommended: 12s
#       Discord rate-limits edits to ~5/min per channel.
#       Going below 12s risks getting rate-limited.
#
# LOG_FLUSH_INTERVAL: How often (seconds) buffered logs are
#   sent as a message to the logs channel.
#   Lower = more frequent log messages in Discord.
#   Recommended: 20–60s
# ============================================================
REFRESH_INTERVAL = 12       # seconds  (recommended: 12–60)
LOG_FLUSH_INTERVAL = 20     # seconds  (recommended: 20–60)

# ---------------- DISCORD INIT ----------------

def init():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(client.start(TOKEN))
    Thread(target=loop.run_forever, daemon=True).start()

# ---------------- DISCORD EVENTS ----------------

@client.event
async def on_ready():
    print(f"[Discord] Logged in as {client.user}")
    await prepare_messages()
    client.loop.create_task(update_loop())
    client.loop.create_task(send_logs_loop())
    # --- complaint system ---
    from features.complaint_system import setup_views
    await setup_views()
    
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

# ---------------- EMBEDS ----------------

def build_stats_embed():
    embed = discord.Embed(
        title="🎮 BombSquad Live Stats",
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc)
    )

    # 👥 Players
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

    # 🗺️ Map
    playlist = stats.get("playlist", {})
    embed.add_field(
        name="🗺️ Map",
        value=f"**Current:** {playlist.get('current', '-')}\n"
              f"**Next:** {playlist.get('next', '-')}",
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

def build_logs_embed(log_text: str):
    return discord.Embed(
        title="📜 Server Logs",
        description=log_text,
        color=discord.Color.orange(),
        timestamp=datetime.now(timezone.utc)
    )

# ---------------- EMBED CONTENT HASH ----------------

def _embed_key(embed: discord.Embed) -> str:
    """Returns a simple string fingerprint of embed content for change detection."""
    fields = "".join(f.value for f in embed.fields)
    return f"{embed.description}|{fields}"

# ---------------- DISCORD LOOPS ----------------

async def update_loop():
    global stats_message, chat_message, _last_stats_content, _last_chat_content

    while not client.is_closed():
        try:
            # --- Stats embed: only edit if content actually changed ---
            stats_embed = build_stats_embed()
            stats_key = _embed_key(stats_embed)
            if stats_key != _last_stats_content:
                await stats_message.edit(embed=stats_embed)
                _last_stats_content = stats_key

            # Small sleep between edits to avoid per-resource bucket exhaustion
            await asyncio.sleep(2)

            # --- Chat embed: only edit if content changed ---
            with chat_lock:
                has_chat = bool(chat_buffer)

            channel = client.get_channel(STATS_CHANNEL_ID)

            if has_chat:
                chat_embed = build_chat_embed()
                chat_key = _embed_key(chat_embed)
                if chat_message is None:
                    chat_message = await channel.send(embed=chat_embed)
                    _last_chat_content = chat_key
                elif chat_key != _last_chat_content:
                    await chat_message.edit(embed=chat_embed)
                    _last_chat_content = chat_key
            else:
                if chat_message is not None:
                    await chat_message.delete()
                    chat_message = None
                    _last_chat_content = None

        except discord.HTTPException as e:
            if e.status == 429:
                # Respect retry_after from Discord on rate limit
                retry_after = getattr(e, 'retry_after', 10)
                await asyncio.sleep(retry_after)
            # Other HTTP errors: just wait and retry next cycle
        except Exception:
            pass

        await asyncio.sleep(REFRESH_INTERVAL)

async def send_logs_loop():
    channel = client.get_channel(LOGS_CHANNEL_ID)

    while not client.is_closed():
        # Wait first so we batch up logs before flushing
        await asyncio.sleep(LOG_FLUSH_INTERVAL)

        if logs:
            # Deduplicate consecutive repeated lines before sending
            seen = []
            prev = None
            for entry in logs[:20]:
                if entry != prev:
                    seen.append(entry)
                    prev = entry

            text = "\n".join(seen)
            logs.clear()

            try:
                await channel.send(embed=build_logs_embed(text))
            except discord.HTTPException as e:
                if e.status == 429:
                    retry_after = getattr(e, 'retry_after', 10)
                    await asyncio.sleep(retry_after)
            except Exception:
                pass

# ---------------- BOMBSQUAD DATA THREAD ----------------

class BsDataThread:
    def __init__(self):
        self.timer = bs.AppTimer(
            5, babase.Call(self.refresh_stats), repeat=True
        )
        babase.apptimer(5.0, self.refresh_stats)

    def refresh_stats(self):
        global stats

        roster = {}
        for p in bs.get_game_roster():
            try:
                roster[p['account_id']] = {
                    'name': p['players'][0]['name_full'],
                    'device_id': p['display_string']
                }
            except Exception:
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
        except Exception:
            pass

        stats['roster'] = roster
        stats['playlist'] = {
            'current': current_map,
            'next': next_map
        }