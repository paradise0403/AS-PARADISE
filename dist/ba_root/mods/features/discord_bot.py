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
from playersdata import pdata 

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

dc = settings.get("discordbot", {})

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

    # 1. Basic Cleaning
    msg = clean(msg)

    # 2. Extract after garbage symbols
    if ">" in msg:
        msg = msg.split(">")[-1]

    # 3. Normalize to colon format
    msg = msg.replace(" - ", ":").strip()

    if ":" not in msg:
        return

    # 4. Use rsplit to get the last colon (ignores v2: IDs)
    try:
        parts = msg.rsplit(":", 1)
        text = parts[1].strip()
        
        # Get name from what's left
        remaining = parts[0].strip()
        if ":" in remaining:
            name = remaining.rsplit(":", 1)[-1].strip()
        else:
            name = remaining.strip()
            
        # Clean specific trash characters from name
        name = name.replace("", "").replace("**", "").strip()
        
        # If name is still weird, take last word
        if " " in name:
            name = name.split(" ")[-1]

    except:
        return

    if not name or not text:
        return

    # 5. Strong Duplicate Filter
    key = f"{name.lower()}:{text.lower()}"
    if key == last_chat:
        return

    last_chat = key

    # 6. Display Output
    display = f"{name}: {text}"

    with chat_lock:
        chat_buffer.append(display)


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
BOT_PREFIX = dc.get("prefix", "a!")
CMD_PREFIX = dc.get("cmd_prefix", "at")

client = Bot(command_prefix=BOT_PREFIX, intents=discord.Intents.all())

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

class TopListView(View):
    def __init__(self, pages):
        super().__init__(timeout=120)
        self.pages = pages
        self.index = 0

    async def update(self, interaction):
        await interaction.response.edit_message(
            embed=self.pages[self.index],
            view=self
        )

    @discord.ui.button(label=":arrow_backward:", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: Button):
        if self.index > 0:
            self.index -= 1
        await self.update(interaction)

    @discord.ui.button(label=":arrow_forward:", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: Button):
        if self.index < len(self.pages) - 1:
            self.index += 1
        await self.update(interaction)

class ChatHistoryView(View):
    def __init__(self, pages):
        super().__init__(timeout=120)
        self.pages = pages
        self.index = 0

    async def update(self, interaction):
        await interaction.response.edit_message(
            embed=self.pages[self.index],
            view=self
        )

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: Button):
        if self.index > 0:
            self.index -= 1
        await self.update(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: Button):
        if self.index < len(self.pages) - 1:
            self.index += 1
        await self.update(interaction)

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
    embed = discord.Embed(title="** LIVE IN GAME CHAT **", color=discord.Color.blurple())
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

    msg_id = load_stats_msg_id()
    if msg_id:
        try:
            old_msg = await ch.fetch_message(int(msg_id))
            await old_msg.delete()
        except: pass
    try:
        async for msg in ch.history(limit=10):
            if msg.author.id == client.user.id:
                await msg.delete()
    except: pass

    stats_message = await ch.send(embed=build_stats(), view=ChatBtn())
    save_stats_msg_id(stats_message.id)


@client.event
async def on_message(message):
    if message.author.bot or not message.content:
        return
    
    if message.channel.id == LOGS_CHANNEL_ID:
        try:
            formatted_msg = f"{message.author.name}: {message.content}"

            bs.pushcall(lambda: bs.chatmessage(formatted_msg), from_other_thread=True)
        except Exception as e:
            print(f"Chat Error: {e}")
            
    await client.process_commands(message)

@client.event
async def on_ready():
    print("Bot Ready")
    await prepare_message()
    client.loop.create_task(stats_loop())
    client.loop.create_task(chat_loop())
    client.loop.create_task(log_loop())


# ================= COMMANDS ================= #

@client.command(name="sc")
async def server_code(ctx):
    server_name = get_config("party_name", "SERVER")
    await ctx.send(f">>> {CMD_PREFIX} - {server_name}")


@client.command(name=CMD_PREFIX)
async def server_cmd(ctx, subcommand: str = None, *, arg: str = None):

    # ===== PERMISSION CHECK ===== #
    admin_ids = settings.get("discordbot", {}).get("adminUsers", [])

    if ctx.author.id not in admin_ids:
        await ctx.send(">>> You don't have permission to use this bot ✨")
        return

    try:
        global stats

        if not subcommand:
            await ctx.send(
                f"Use: `{BOT_PREFIX}{CMD_PREFIX} info` or "
                f"`{BOT_PREFIX}{CMD_PREFIX} stats <pbid>`"
            )
            return

        subcommand = subcommand.lower()

        # ================= INFO ================= #
        if subcommand == "info":
            server_name = get_config("party_name", "Unknown Server")
            ip = get_public_ip()
            port = get_config("port", 43210)

            roster = stats.get("roster", {})
            current_players = len(roster)
            max_players = get_config("max_party_size", 16)

            playlist = stats.get("playlist", {})
            current_map = playlist.get("current", "-")
            next_map = playlist.get("next", "-")

            embed = discord.Embed(
                title="🎮 Server Info",
                color=discord.Color.green()
            )
            embed.add_field(name="Server Name", value=server_name, inline=False)
            embed.add_field(name="IP", value=f"`{ip}`", inline=True)
            embed.add_field(name="Port", value=f"`{port}`", inline=True)
            embed.add_field(name="Players", value=f"`{current_players}/{max_players}`", inline=False)
            embed.add_field(name="Current Map", value=current_map, inline=True)
            embed.add_field(name="Next Map", value=next_map, inline=True)
            embed.set_footer(text=f"Use {BOT_PREFIX}{CMD_PREFIX} stats <pbid>")

            await ctx.send(embed=embed)
            return

        # ================= STATS ================= #
        elif subcommand == "stats":
            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} stats <pbid>`")
                return

            pbid = arg.strip()

            try:
                with open(STATS_JSON_PATH) as f:
                    data = json.load(f)
                if "stats" in data:
                    data = data["stats"]
            except Exception as e:
                await ctx.send("Stats file not found ❌")
                print("Stats error:", e)
                return

            if pbid not in data:
                await ctx.send("Player not found ❌")
                return

            p = data[pbid]
            name = clean(p.get("name", "Unknown"))
            rank = p.get("rank", "-")
            score = p.get("scores", 0)
            kills = p.get("kills", 0)
            deaths = p.get("deaths", 0)
            kd = p.get("kd", 0)

            coins = 0
            try:
                COIN_PATH = os.path.join(BASE_DIR, "..", "..", "..", "coin_data.json")
                if os.path.exists(COIN_PATH):
                    with open(COIN_PATH) as f:
                        coin_data = json.load(f)
                    if pbid in coin_data:
                        coins = coin_data[pbid].get("coins", 0)
            except Exception as e:
                print("Coin error:", e)

            server_name = get_config("party_name", "SERVER")
            embed = discord.Embed(
                title=server_name,
                description=(
                    f"Name - {name}\n"
                    f"Pb - {pbid}\n"
                    f"Rank - {rank}\n"
                    f"Score - {score}\n"
                    f"Kills - {kills}\n"
                    f"Death - {deaths}\n"
                    f"Kd - {kd}\n"
                    f"Coins - {coins}"
                ),
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed)
            return

        # ================= TOPLIST ================= #
        elif subcommand == "toplist":
            try:
                with open(STATS_JSON_PATH) as f:
                    data = json.load(f)
                if "stats" in data:
                    data = data["stats"]
            except Exception as e:
                await ctx.send("Stats file not found ❌")
                print("Toplist error:", e)
                return

            players = []
            for pbid, p in data.items():
                players.append({
                    "name": clean(p.get("name", "Unknown")),
                    "pbid": pbid,
                    "score": int(p.get("scores", 0)),
                    "kills": int(p.get("kills", 0)),
                    "deaths": int(p.get("deaths", 0))
                })

            players.sort(key=lambda x: x["score"], reverse=True)

            per_page = 5
            pages = []
            server_name = get_config("party_name", "SERVER")
            total_players = min(len(players), 10)
            total_pages = (total_players + per_page - 1) // per_page

            for i in range(0, total_players, per_page):
                chunk = players[i:i + per_page]
                desc = ""
                for idx, p in enumerate(chunk, start=i + 1):
                    desc += (
                        f"Top {idx} - {p['name']}\n"
                        f"Pb - {p['pbid']}\n"
                        f"Kills - {p['kills']} | Score - {p['score']} | Death - {p['deaths']}\n\n"
                    )

                page_num = (i // per_page) + 1
                embed = discord.Embed(
                    title=f"{server_name} | Page {page_num}/{total_pages}",
                    description=desc,
                    color=discord.Color.gold()
                )
                pages.append(embed)

            if not pages:
                await ctx.send("No data ❌")
                return

            view = TopListView(pages)
            await ctx.send(embed=pages[0], view=view)
            return

        # ================= GET ROLES ================= #
        elif subcommand == "getroles":
            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} getroles <pbid>`")
                return

            pbid = arg.strip()
            roles = pdata.get_player_roles(pbid)

            if not roles:
                await ctx.send("No roles found ❌")
                return

            name = "Unknown"
            try:
                with open(STATS_JSON_PATH) as f:
                    stats_data = json.load(f)
                if "stats" in stats_data:
                    stats_data = stats_data["stats"]
                if pbid in stats_data:
                    name = clean(stats_data[pbid].get("name", "Unknown"))
            except Exception:
                pass

            server_name = get_config("party_name", "SERVER")
            await ctx.send(f">>> {name} ({pbid}) has **{', '.join(r.upper() for r in roles)}** in {server_name}")
            return

# ================= ADD ROLE ================= #
        elif subcommand == "addrole":
            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} addrole <pbid> <rolename>`")
                return

            parts = arg.split()
            if len(parts) < 2:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} addrole <pbid> <rolename>`")
                return

            pbid = parts[0]
            input_role = parts[1]

            roles = pdata.get_roles()

            # -------- CASE INSENSITIVE ROLE MATCH -------- #
            role_name = None
            for r in roles:
                if r.lower() == input_role.lower():
                    role_name = r
                    break

            if role_name is None:
                await ctx.send("Role not found ❌")
                return

            if pbid in roles[role_name]["ids"]:
                await ctx.send("Already has role ⚠️")
                return

            pdata.add_player_role(role_name, pbid)

            server_name = get_config("party_name", "SERVER")
            await ctx.send(f">>> Added **{role_name.upper()}** to {pbid} in {server_name}")
            return

        # ================= REMOVE ROLE ================= #
        elif subcommand == "removerole":
            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} removerole <pbid> <rolename>`")
                return

            parts = arg.split()
            if len(parts) < 2:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} removerole <pbid> <rolename>`")
                return

            pbid = parts[0]
            role_name = parts[1].lower()
            roles = pdata.get_roles()

            if role_name not in roles:
                await ctx.send("Role not found ❌")
                return
            if pbid not in roles[role_name]["ids"]:
                await ctx.send("Player doesn't have this role ⚠️")
                return

            pdata.remove_player_role(role_name, pbid)
            server_name = get_config("party_name", "SERVER")
            await ctx.send(f">>> Removed **{role_name.upper()}** from {pbid} in {server_name}")
            return

        # ================= ADD TAG ================= #
        elif subcommand == "addtag":
            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} addtag <pbid> <anim> <tag>`")
                return

            parts = arg.split(maxsplit=2)
            if len(parts) < 3:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} addtag <pbid> <anim> <tag>`")
                return

            pbid = parts[0]
            try:
                anim = int(parts[1])
            except Exception:
                await ctx.send("Anim must be number ❌")
                return
            tag = parts[2]

            try:
                pdata.set_tag(tag, pbid, anim)
            except Exception as e:
                await ctx.send(f"Error saving tag ❌: {e}")
                return

            name = "Unknown"
            try:
                with open(STATS_JSON_PATH) as f:
                    stats_data = json.load(f)
                if "stats" in stats_data:
                    stats_data = stats_data["stats"]
                if pbid in stats_data:
                    name = clean(stats_data[pbid].get("name", "Unknown"))
            except Exception:
                pass

            server_name = get_config("party_name", "SERVER")
            await ctx.send(f">>> Tag **{tag}** (anim {anim}) added to {name} ({pbid}) in {server_name}")
            return

        # ================= REMOVE TAG ================= #
        elif subcommand == "removetag":
            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} removetag <pbid>`")
                return

            pbid = arg.strip()
            custom = pdata.get_custom()

            if "customtag" not in custom:
                custom["customtag"] = {}
            if pbid not in custom["customtag"]:
                await ctx.send("Player doesn't have custom tag ⚠️")
                return

            old_tag = custom["customtag"][pbid]
            if isinstance(old_tag, dict):
                old_tag = old_tag.get("tag", "Unknown")

            custom["customtag"].pop(pbid, None)
            pdata.CacheData.custom = custom
            pdata.commit_c()

            name = "Unknown"
            try:
                with open(STATS_JSON_PATH) as f:
                    stats_data = json.load(f)
                if "stats" in stats_data:
                    stats_data = stats_data["stats"]
                if pbid in stats_data:
                    name = clean(stats_data[pbid].get("name", "Unknown"))
            except Exception:
                pass

            server_name = get_config("party_name", "SERVER")
            await ctx.send(f">>> Removed tag **{old_tag}** from {name} ({pbid}) in {server_name}")
            return

        # ================= EFFECT LIST ================= #
        elif subcommand == "effectlist":
            try:
                from spazmod import spaz_effects
                cls = spaz_effects.NewPlayerSpaz
                effects = [m.replace("_add_", "") for m in dir(cls) if m.startswith("_add_")]

                if not effects:
                    await ctx.send("No effects found ❌")
                    return

                effects = sorted(set(effects))
                per_line = 5
                lines = []
                for i in range(0, len(effects), per_line):
                    lines.append(" | ".join(effects[i:i + per_line]))

                server_name = get_config("party_name", "SERVER")
                embed = discord.Embed(
                    title=f"{server_name} Effects List",
                    description="\n".join(lines),
                    color=discord.Color.purple()
                )
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send("Error loading effects ❌")
                print("EffectList Error:", e)
            return

        # ================= ADD EFFECT ================= #
        elif subcommand == "addeffect":
            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} addeffect <pbid> <effectname>`")
                return

            parts = arg.split()
            if len(parts) < 2:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} addeffect <pbid> <effectname>`")
                return

            pbid = parts[0]
            effect_name = parts[1].lower()

            try:
                pdata.set_effect(effect_name, pbid)
                pdata.CacheData.custom = {}
            except Exception as e:
                await ctx.send(f"Error adding effect ❌: {e}")
                return

            name = "Unknown"
            try:
                with open(STATS_JSON_PATH) as f:
                    stats_data = json.load(f)
                if "stats" in stats_data:
                    stats_data = stats_data["stats"]
                if pbid in stats_data:
                    name = clean(stats_data[pbid].get("name", "Unknown"))
            except Exception:
                pass

            server_name = get_config("party_name", "SERVER")
            await ctx.send(f">>> Successfully added **{effect_name}** effect to {name} ({pbid}) in {server_name}")
            return

        # ================= REMOVE EFFECT ================= #
        elif subcommand == "removeeffect":
            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} removeeffect <pbid> <effectname>`")
                return

            parts = arg.split()
            if len(parts) < 2:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} removeeffect <pbid> <effectname>`")
                return

            pbid = parts[0]
            effect_name = parts[1].lower()

            try:
                custom = pdata.get_custom()
                if "customeffects" not in custom:
                    custom["customeffects"] = {}
                effects = custom.get("customeffects", {}).get(pbid, [])
                if isinstance(effects, str):
                    effects = [effects]

                if effect_name not in effects:
                    await ctx.send("Player doesn't have this effect ⚠️")
                    return

                effects.remove(effect_name)
                if effects:
                    custom["customeffects"][pbid] = effects
                else:
                    custom["customeffects"].pop(pbid, None)

                pdata.CacheData.custom = custom
                pdata.commit_c()
            except Exception as e:
                await ctx.send(f"Error removing effect ❌: {e}")
                return

            name = "Unknown"
            try:
                with open(STATS_JSON_PATH) as f:
                    stats_data = json.load(f)
                if "stats" in stats_data:
                    stats_data = stats_data["stats"]
                if pbid in stats_data:
                    name = clean(stats_data[pbid].get("name", "Unknown"))
            except Exception:
                pass

            server_name = get_config("party_name", "SERVER")
            await ctx.send(f">>> Successfully removed **{effect_name}** effect from {name} ({pbid}) in {server_name}")
            return

        # ================= ADD COIN ================= #
        elif subcommand == "addcoin":
            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} addcoin <pbid> <amount>`")
                return

            parts = arg.split()
            if len(parts) < 2:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} addcoin <pbid> <amount>`")
                return

            pbid = parts[0]
            try:
                amount = int(parts[1])
            except Exception:
                await ctx.send("Amount must be number ❌")
                return

            if amount <= 0:
                await ctx.send("Amount must be greater than 0 ❌")
                return

            COIN_PATH = os.path.join(BASE_DIR, "..", "..", "..", "coin_data.json")
            try:
                if os.path.exists(COIN_PATH):
                    with open(COIN_PATH) as f:
                        data = json.load(f)
                else:
                    data = {}
            except Exception:
                await ctx.send("Error loading coin file ❌")
                return

            if pbid not in data:
                data[pbid] = {"coins": 0}

            data[pbid]["coins"] = data[pbid].get("coins", 0) + amount

            with open(COIN_PATH, "w") as f:
                json.dump(data, f, indent=4)

            name = "Unknown"
            try:
                with open(STATS_JSON_PATH) as f:
                    stats_data = json.load(f)
                if "stats" in stats_data:
                    stats_data = stats_data["stats"]
                if pbid in stats_data:
                    name = clean(stats_data[pbid].get("name", "Unknown"))
            except Exception:
                pass

            server_name = get_config("party_name", "SERVER")
            await ctx.send(f">>> Added **{amount} coins** to {name} ({pbid}) in {server_name}")
            return

        # ================= REMOVE COIN ================= #
        elif subcommand == "removecoin":
            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} removecoin <pbid> <amount>`")
                return

            parts = arg.split()
            if len(parts) < 2:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} removecoin <pbid> <amount>`")
                return

            pbid = parts[0]
            try:
                amount = int(parts[1])
            except Exception:
                await ctx.send("Amount must be number ❌")
                return

            if amount <= 0:
                await ctx.send("Amount must be greater than 0 ❌")
                return

            COIN_PATH = os.path.join(BASE_DIR, "..", "..", "..", "coin_data.json")
            try:
                if os.path.exists(COIN_PATH):
                    with open(COIN_PATH) as f:
                        data = json.load(f)
                else:
                    data = {}
            except Exception:
                await ctx.send("Error loading coin file ❌")
                return

            if pbid not in data:
                await ctx.send("Player has no coins ❌")
                return

            data[pbid]["coins"] = max(0, data[pbid].get("coins", 0) - amount)

            with open(COIN_PATH, "w") as f:
                json.dump(data, f, indent=4)

            name = "Unknown"
            try:
                with open(STATS_JSON_PATH) as f:
                    stats_data = json.load(f)
                if "stats" in stats_data:
                    stats_data = stats_data["stats"]
                if pbid in stats_data:
                    name = clean(stats_data[pbid].get("name", "Unknown"))
            except Exception:
                pass

            server_name = get_config("party_name", "SERVER")
            await ctx.send(f">>> Removed **{amount} coins** from {name} ({pbid}) in {server_name}")
            return

        # ================= QUIT ================= #
        elif subcommand == "quit":
            server_name = get_config("party_name", "SERVER")
            await ctx.send(f">>> SUCCESSFULLY RESTRATED {server_name}")
            try:
                os._exit(0)
            except Exception:
                return

# ================= BAN PLAYER ================= #
        elif subcommand == "ban":

            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} ban <pbid>`")
                return

            pbid = arg.strip()

            try:
                # Ban for 999 days (you can change)
                pdata.ban_player(pbid, 999, "Banned via Discord")

            except Exception as e:
                await ctx.send(f"Ban failed ❌ {e}")
                return

            # -------- GET NAME -------- #
            name = "Unknown"
            try:
                with open(STATS_JSON_PATH) as f:
                    stats_data = json.load(f)

                if "stats" in stats_data:
                    stats_data = stats_data["stats"]

                if pbid in stats_data:
                    name = clean(stats_data[pbid].get("name", "Unknown"))
            except:
                pass

            server_name = get_config("party_name", "SERVER")

            await ctx.send(f">>> Successfully banned {name} ({pbid}) in {server_name}")
            return

        # ================= UNBAN PLAYER ================= #
        elif subcommand == "unban":

            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} unban <pbid>`")
                return

            pbid = arg.strip()

            try:
                pdata.unban_player(pbid)

            except Exception as e:
                await ctx.send(f"Unban failed ❌ {e}")
                return

            # -------- GET NAME -------- #
            name = "Unknown"
            try:
                with open(STATS_JSON_PATH) as f:
                    stats_data = json.load(f)

                if "stats" in stats_data:
                    stats_data = stats_data["stats"]

                if pbid in stats_data:
                    name = clean(stats_data[pbid].get("name", "Unknown"))
            except:
                pass

            server_name = get_config("party_name", "SERVER")

            await ctx.send(f">>> Successfully unbanned {name} ({pbid}) in {server_name}")
            return

# ================= ONLINE PLAYERS ================= #
        elif subcommand == "players":

            server_name = get_config("party_name", "SERVER")
            roster = stats.get("roster", {})

            if not roster:
                await ctx.send("No players online ❌")
                return

            try:
                with open(STATS_JSON_PATH) as f:
                    stats_data = json.load(f)
                if "stats" in stats_data:
                    stats_data = stats_data["stats"]
            except:
                stats_data = {}

            lines = []
            for pbid, info in roster.items():
                name = clean(info.get("name", "Unknown"))
                cid = info.get("client_id", "-")
                rank = stats_data.get(pbid, {}).get("rank", "-")

                lines.append(
                    f"{name}\n"
                    f"Pb - {pbid}\n"
                    f"CID - {cid}\n"
                    f"Rank - {rank}"
                )

            embed = discord.Embed(
                title=server_name,
                description="\n\n".join(lines),
                color=discord.Color.green()
            )

            await ctx.send(embed=embed)
            return


        # ================= RECENT PLAYERS ================= #
        elif subcommand == "recents":

            server_name = get_config("party_name", "SERVER")

            lines = []
            try:
                from serverdata import serverdata

                roster = stats.get("roster", {})

                for p in serverdata.recents[-15:]:
                    pbid = p.get("pbid", "Unknown")
                    client_id = p.get("client_id", "-")
                    name = p.get("name", "Unknown")

                    if name == "Unknown" and pbid in roster:
                        name = clean(roster[pbid].get("name", "Unknown"))

                    lines.append(f"{name} | {pbid} | ClientID: {client_id}")

            except Exception as e:
                await ctx.send(f"Error getting recents ❌: {e}")
                return

            if not lines:
                lines = ["No recent players"]

            embed = discord.Embed(
                title=server_name,
                description="\n".join(lines),
                color=discord.Color.gold()
            )

            await ctx.send(embed=embed)
            return

# ================= KICK / MUTE / UNMUTE ================= #
        elif subcommand in ("kick", "mute", "unmute"):

            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} {subcommand} <pbid/clientid>`")
                return

            target = arg.strip()
            roster = stats.get("roster", {})

            pbid = None
            cid = None
            name = "Unknown"

            # -------- FIND BY PBID OR CID -------- #
            for r_pbid, info in roster.items():
                r_cid = str(info.get("client_id", "-"))

                if target == r_pbid or target == r_cid:
                    pbid = r_pbid
                    cid = info.get("client_id", None)
                    name = clean(info.get("name", "Unknown"))
                    break

            # if only pbid given (offline player)
            if pbid is None and target.startswith("pb-"):
                pbid = target

            if pbid is None:
                await ctx.send("Player not found ❌")
                return

            server_name = get_config("party_name", "SERVER")

            # ================= KICK ================= #
            if subcommand == "kick":

                if cid is None or cid == "-":
                    await ctx.send("Player is not online, cannot kick ❌")
                    return

                try:
                    bs.pushcall(
                        lambda: bs.disconnect_client(int(cid)),
                        from_other_thread=True
                    )
                except Exception as e:
                    await ctx.send(f"Kick failed ❌: {e}")
                    return

                await ctx.send(f">>> Successfully kicked {name} ({pbid}) in {server_name}")
                return

            # ================= MUTE ================= #
            if subcommand == "mute":
                try:
                    pdata.mute(pbid, 999, "Muted via Discord")
                except Exception as e:
                    await ctx.send(f"Mute failed ❌: {e}")
                    return

                await ctx.send(f">>> Successfully muted {name} ({pbid}) in {server_name}")
                return

            # ================= UNMUTE ================= #
            if subcommand == "unmute":
                try:
                    pdata.unmute(pbid)
                except Exception as e:
                    await ctx.send(f"Unmute failed ❌: {e}")
                    return

                await ctx.send(f">>> Successfully unmuted {name} ({pbid}) in {server_name}")
                return

# ================= PLAYLIST ================= #
        elif subcommand == "playlist":

            server_name = get_config("party_name", "SERVER")
            playlist_code = get_config("playlist_code", "-")

            pl = stats.get("playlist", {})
            items = pl.get("items", [])

            if items:
                playlist_text = "\n".join(items[:25])
            else:
                playlist_text = (
                    f"Current Map - {pl.get('current', '-')}\n"
                    f"Next Map - {pl.get('next', '-')}"
                )

            embed = discord.Embed(
                title=server_name,
                description=(
                    f">>> Playlist - {playlist_code}\n\n"
                    f"{playlist_text}"
                ),
                color=discord.Color.gold()
            )

            await ctx.send(embed=embed)
            return

# ================= SET SERVER NAME ================= #
        elif subcommand == "setname":

            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} setname <new server name>`")
                return

            old_name = get_config("party_name", "SERVER")
            new_name = arg.strip()

            try:
                server_config["party_name"] = new_name

                with open(CONFIG_PATH, "w") as f:
                    json.dump(server_config, f, indent=4)

            except Exception as e:
                await ctx.send(f"Failed to change server name ❌: {e}")
                return

            await ctx.send(f">>> Successfully changed server name from **{old_name}** to **{new_name}**")
            return


        # ================= CHANGE PLAYLIST ================= #
        elif subcommand == "changepl":

            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} changepl <playlist_code>`")
                return

            try:
                playlist_code = int(arg.strip())
            except:
                await ctx.send("Playlist code must be a number ❌")
                return

            old_code = get_config("playlist_code", "-")

            try:
                server_config["playlist_code"] = playlist_code

                with open(CONFIG_PATH, "w") as f:
                    json.dump(server_config, f, indent=4)

            except Exception as e:
                await ctx.send(f"Failed to change playlist ❌: {e}")
                return

            server_name = get_config("party_name", "SERVER")
            await ctx.send(f">>> Successfully changed playlist for **{server_name}** from **{old_code}** to **{playlist_code}**")
            return

# ================= FIND PLAYER ================= #
        elif subcommand == "findplayer":

            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} findplayer <name>`")
                return

            query = arg.lower()

            try:
                with open(STATS_JSON_PATH) as f:
                    data = json.load(f)
                if "stats" in data:
                    data = data["stats"]
            except:
                await ctx.send("Stats file not found ❌")
                return

            results = []
            for pbid, p in data.items():
                name = clean(p.get("name", "Unknown"))
                if query in name.lower():
                    results.append((pbid, p))

            if not results:
                await ctx.send("Player not found ❌")
                return

            pbid, p = results[0]

            name = clean(p.get("name", "Unknown"))
            rank = p.get("rank", "-")
            score = p.get("scores", 0)
            kills = p.get("kills", 0)
            deaths = p.get("deaths", 0)
            kd = p.get("kd", 0)

            coins = 0
            try:
                COIN_PATH = os.path.join(BASE_DIR, "..", "..", "..", "coin_data.json")
                if os.path.exists(COIN_PATH):
                    with open(COIN_PATH) as f:
                        coin_data = json.load(f)
                    if pbid in coin_data:
                        coins = coin_data[pbid].get("coins", 0)
            except:
                pass

            server_name = get_config("party_name", "SERVER")

            embed = discord.Embed(
                title=server_name,
                description=(
                    f"Name - {name}\n"
                    f"Pb - {pbid}\n"
                    f"Rank - {rank}\n"
                    f"Score - {score}\n"
                    f"Kills - {kills}\n"
                    f"Death - {deaths}\n"
                    f"Kd - {kd}\n"
                    f"Coins - {coins}"
                ),
                color=discord.Color.gold()
            )

            await ctx.send(embed=embed)
            return


        # ================= MESSAGE / BROADCAST ================= #
        elif subcommand == "msg":

            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} msg <message>`")
                return

            message = arg.strip()
            server_name = get_config("party_name", "SERVER")

            try:
                bs.pushcall(
                    lambda: bs.chatmessage(message),
                    from_other_thread=True
                )
            except Exception as e:
                await ctx.send(f"Failed to send message ❌: {e}")
                return

            await ctx.send(f">>> Successfully sent **{message}** to {server_name}")
            return

# ================= ADD / REMOVE DISCORD USER ================= #
        elif subcommand in ("adduser", "removeuser"):

            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} {subcommand} <@user/userid>`")
                return

            # get discord user id from mention or raw id
            raw = arg.strip().replace("<@", "").replace("!", "").replace(">", "")

            try:
                user_id = int(raw)
            except:
                await ctx.send("Invalid user id ❌")
                return

            server_name = get_config("party_name", "SERVER")

            if "adminUsers" not in dc:
                dc["adminUsers"] = []

            # get user name
            user_name = str(user_id)
            try:
                user = await client.fetch_user(user_id)
                user_name = user.name
            except:
                pass

            # ================= ADD USER ================= #
            if subcommand == "adduser":

                if user_id in dc["adminUsers"]:
                    await ctx.send("User is already admin ⚠️")
                    return

                dc["adminUsers"].append(user_id)
                settings["discordbot"] = dc

                with open(SETTINGS_PATH, "w") as f:
                    json.dump(settings, f, indent=4)

                await ctx.send(f">>> Successfully added **{user_name}** as admin in {server_name}")
                return

            # ================= REMOVE USER ================= #
            if subcommand == "removeuser":

                if user_id not in dc["adminUsers"]:
                    await ctx.send("User is not admin ⚠️")
                    return

                dc["adminUsers"].remove(user_id)
                settings["discordbot"] = dc

                with open(SETTINGS_PATH, "w") as f:
                    json.dump(settings, f, indent=4)

                await ctx.send(f">>> Successfully removed **{user_name}** from admin in {server_name}")
                return

# ================= ROLE LIST ================= #
        elif subcommand == "rolelist":

            try:
                roles = pdata.get_roles()
            except Exception as e:
                await ctx.send(f"Error loading roles ❌: {e}")
                return

            if not roles:
                await ctx.send("No roles found ❌")
                return

            server_name = get_config("party_name", "SERVER")

            lines = []
            for role_name, role_info in roles.items():
                ids = role_info.get("ids", [])
                commands = role_info.get("commands", [])

                lines.append(
                    f"**{role_name.upper()}**\n"
                    f"Players - {len(ids)} | Cmds - {len(commands)}"
                )

            embed = discord.Embed(
                title=f"{server_name} Role List",
                description="\n\n".join(lines),
                color=discord.Color.gold()
            )

            await ctx.send(embed=embed)
            return

# ================= ROLE INFO ================= #
        elif subcommand == "roleinfo":

            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} roleinfo <rolename>`")
                return

            input_role = arg.strip()
            roles = pdata.get_roles()

            role_name = None
            for r in roles:
                if r.lower() == input_role.lower():
                    role_name = r
                    break

            if role_name is None:
                await ctx.send("Role not found ❌")
                return

            role = roles[role_name]
            players_count = len(role.get("ids", []))
            commands = role.get("commands", [])

            cmd_text = ", ".join(commands) if commands else "No commands"

            embed = discord.Embed(
                title=f"{role_name.upper()} INFO",
                description=(
                    f"Players - {players_count}\n"
                    f"Commands - {cmd_text}"
                ),
                color=discord.Color.blue()
            )

            await ctx.send(embed=embed)
            return


        # ================= WHO IS ROLE ================= #
        elif subcommand == "whoisrole":

            if not arg:
                await ctx.send(f"Use: `{BOT_PREFIX}{CMD_PREFIX} whoisrole <rolename>`")
                return

            input_role = arg.strip()
            roles = pdata.get_roles()

            role_name = None
            for r in roles:
                if r.lower() == input_role.lower():
                    role_name = r
                    break

            if role_name is None:
                await ctx.send("Role not found ❌")
                return

            ids = roles[role_name].get("ids", [])

            if not ids:
                await ctx.send("No players in this role ❌")
                return

            try:
                with open(STATS_JSON_PATH) as f:
                    stats_data = json.load(f)
                if "stats" in stats_data:
                    stats_data = stats_data["stats"]
            except:
                stats_data = {}

            lines = []
            for pbid in ids:
                name = stats_data.get(pbid, {}).get("name", "Unknown")
                name = clean(name)
                lines.append(f"{name} ({pbid})")

            embed = discord.Embed(
                title=f"{role_name.upper()} PLAYERS",
                description="\n".join(lines),
                color=discord.Color.green()
            )

            await ctx.send(embed=embed)
            return

# ================= LAST CHAT ================= #
        elif subcommand == "lastchat":

            server_name = get_config("party_name", "SERVER")

            with chat_lock:
                chats = list(chat_buffer)

            if not chats:
                await ctx.send("No chat found ❌")
                return

            per_page = 10
            pages = []

            for i in range(0, len(chats), per_page):
                chunk = chats[i:i + per_page]

                desc = ""
                for idx, msg in enumerate(chunk, start=i + 1):
                    desc += f"Chat {idx} - {msg}\n"

                page_num = (i // per_page) + 1
                total_pages = (len(chats) + per_page - 1) // per_page

                embed = discord.Embed(
                    title=f"{server_name} | Chat Page {page_num}/{total_pages}",
                    description=desc,
                    color=discord.Color.blurple()
                )

                pages.append(embed)

            view = ChatHistoryView(pages)
            await ctx.send(embed=pages[0], view=view)
            return


        # ================= END GAME ================= #
        elif subcommand == "endgame":

            server_name = get_config("party_name", "SERVER")

            pl = stats.get("playlist", {})
            current_map = pl.get("current", "-")
            next_map = pl.get("next", "-")

            try:
                bs.pushcall(
                    lambda: bs.get_foreground_host_activity().end_game(),
                    from_other_thread=True
                )
            except Exception as e:
                await ctx.send(f"Failed to end game ❌: {e}")
                return

            embed = discord.Embed(
                title=server_name,
                description=(
                    f"Ended - {current_map}\n"
                    f"Started - {next_map}"
                ),
                color=discord.Color.red()
            )

            await ctx.send(embed=embed)
            return

# ================= CREATOR ================= # Dont change
        elif subcommand == "creator":

            DISCORD_LINK = "https://discord.gg/UN42ck7FCY"
            SCRIPT_LINK = "https://github.com/paradise0403/AS-PARADISE.git"
            WEBSITE_LINK = "http://65.1.65.75:3000/"

            THUMBNAIL_URL = "https://cdn.discordapp.com/attachments/1285299569474928754/1499608486193926247/Mui.jpg?ex=69f56abc&is=69f4193c&hm=3053093f1af3f3e85bad18baf0d8249e0228a650b3bf976cdcc9493abdcf90a2&"
            BANNER_URL = "https://cdn.discordapp.com/attachments/1285299569474928754/1499608553579614278/Wallpaper_programmer.jpg?ex=69f56acc&is=69f4194c&hm=4e6faecd9a0499a6c6d18c3cd746dd8b04562d698a92381c318e5a176eac420c&"

            class CreatorView(View):
                def __init__(self):
                    super().__init__(timeout=None)

                    self.add_item(discord.ui.Button(
                        label="Discord Server",
                        style=discord.ButtonStyle.link,
                        url=DISCORD_LINK
                    ))

                    self.add_item(discord.ui.Button(
                        label="Script",
                        style=discord.ButtonStyle.link,
                        url=SCRIPT_LINK
                    ))

                    self.add_item(discord.ui.Button(
                        label="Website",
                        style=discord.ButtonStyle.link,
                        url=WEBSITE_LINK
                    ))

            embed = discord.Embed(
                title="AS-PARADISE Creator",
                description=(
                    "**Creator** - paradise0403 (ASHX)\n"
                    "**Language** - Python\n"
                    "**Created on** - April 2026\n\n"
                    "Thanks for using my **AS-PARADISE** script.\n"
                    "If you got any error, join our support Discord server.\n\n"
                    f"**Discord Link** - {DISCORD_LINK}\n"
                    f"**Script Link** - {SCRIPT_LINK}\n"
                    f"**Website Link** - {WEBSITE_LINK}"
                ),
                color=discord.Color.gold()
            )

            embed.set_thumbnail(url=THUMBNAIL_URL)
            embed.set_image(url=BANNER_URL)
            embed.set_footer(text="AS-PARADISE • Made by paradise0403")

            await ctx.send(embed=embed, view=CreatorView())
            return

# ================= HELP ================= #
        elif subcommand == "help":

            p = f"{BOT_PREFIX}{CMD_PREFIX}"

            embed = discord.Embed(
                title="**AS PARADISE HELP PANEL**",
                description=(
                    f"**{p} info**\n"
                    f"• Shows server information\n\n"

                    f"**{p} stats <pbid>**\n"
                    f"• Shows player stats\n\n"

                    f"**{p} toplist**\n"
                    f"• Shows top leaderboard\n\n"

                    f"**{p} getroles <pbid>**\n"
                    f"• Shows player roles\n\n"

                    f"**{p} addrole <pbid> <role>**\n"
                    f"• Adds role to player pbid\n\n"

                    f"**{p} removerole <pbid> <role>**\n"
                    f"• Removes role from player pbid\n\n"

                    f"**{p} rolelist**\n"
                    f"• Shows all server roles\n\n"

                    f"**{p} roleinfo <role>**\n"
                    f"• Shows role information\n\n"

                    f"**{p} whoisrole <role>**\n"
                    f"• Shows players in a role\n\n"

                    f"**{p} addtag <pbid> <anim> <tag>**\n"
                    f"• Adds custom tag to player\n\n"

                    f"**{p} removetag <pbid>**\n"
                    f"• Removes custom tag from player\n\n"

                    f"**{p} effectlist**\n"
                    f"• Shows available effects\n\n"

                    f"**{p} addeffect <pbid> <effect>**\n"
                    f"• Adds effect to player\n\n"

                    f"**{p} removeeffect <pbid> <effect>**\n"
                    f"• Removes effect from player\n\n"

                    f"**{p} addcoin <pbid> <amount>**\n"
                    f"• Adds coins to player\n\n"

                    f"**{p} removecoin <pbid> <amount>**\n"
                    f"• Removes coins from player\n\n"

                    f"**{p} ban <pbid>**\n"
                    f"• Bans player from server\n\n"

                    f"**{p} unban <pbid>**\n"
                    f"• Unbans player from server\n\n"

                    f"**{p} kick <pbid/clientid>**\n"
                    f"• Kicks online player\n\n"

                    f"**{p} mute <pbid/clientid>**\n"
                    f"• Mutes player\n\n"

                    f"**{p} unmute <pbid/clientid>**\n"
                    f"• Unmutes player\n\n"

                    f"**{p} players**\n"
                    f"• Shows online players\n\n"

                    f"**{p} recents**\n"
                    f"• Shows recent joined players\n\n"

                    f"**{p} playlist**\n"
                    f"• Shows current playlist\n\n"

                    f"**{p} setname <name>**\n"
                    f"• Changes server name\n\n"

                    f"**{p} changepl <playlistcode>**\n"
                    f"• Changes playlist code\n\n"

                    f"**{p} findplayer <name>**\n"
                    f"• Finds player by name\n\n"

                    f"**{p} msg <message>**\n"
                    f"• Sends message in game\n\n"

                    f"**{p} lastchat**\n"
                    f"• Shows recent game chats\n\n"

                    f"**{p} endgame**\n"
                    f"• Ends current game\n\n"

                    f"**{p} creator**\n"
                    f"• Shows creator information\n\n"

                    f"**{p} quit**\n"
                    f"• Restarts your running server\n\n"

                    f"**{p} adduser <@user/id>**\n"
                    f"• Adds Discord admin user\n\n"

                    f"**{p} removeuser <@user/id>**\n"
                    f"• Removes Discord admin user"
                ),
                color=discord.Color.gold()
            )

            embed.set_footer(text="AS PARADISE • Help Panel")
            await ctx.send(embed=embed)
            return

        # ================= INVALID ================= #
        else:
            await ctx.send("Unknown subcommand ❌")
            return

    except Exception as e:
        await ctx.send(f"Error: {e}")


# ---------------- BS THREAD ----------------
class BsDataThread:
    def __init__(self):
        self.old_roster = {}
        self._last_msg_raw = None
        self.timer = bs.AppTimer(2.0, babase.Call(self.update), repeat=True)

    def update(self):
        global stats

        # ROSTER
        roster = {}
        for p in bs.get_game_roster():
            try: roster[p['account_id']] = {
    'name': p['players'][0]['name_full'],
    'client_id': p.get('client_id', '-')
}
            except: pass

        # JOIN / LEFT
        new_ids, old_ids = set(roster.keys()), set(self.old_roster.keys())
        for p in new_ids - old_ids: push_log(f" JOIN: {roster[p]['name']}")
        for p in old_ids - new_ids: push_log(f" LEFT: {self.old_roster[p]['name']}")
        self.old_roster = roster

        # CHAT (FIXED DUPLICATES)
        try:
            msgs = bs.get_chat_messages()
            if msgs:
                current_last = msgs[-1]
                if current_last != self._last_msg_raw:
                    add_chat(current_last)
                    self._last_msg_raw = current_last
        except: pass

        # MAP INFO
        cm, nm = "-", "-"
        playlist_items = []

        try:
            s = bs.get_foreground_host_session()
            nm = s.get_next_game_description().evaluate()
            cm = s._current_game_spec['resolved_type'].get_settings_display_string(
                s._current_game_spec
            ).evaluate()

            try:
                pl = getattr(s, "_playlist", [])
                for i, spec in enumerate(pl, 1):
                    try:
                        game_name = spec["resolved_type"].get_settings_display_string(spec).evaluate()
                    except:
                        game_name = str(spec)
                    playlist_items.append(f"{i}. {game_name}")
            except:
                playlist_items = []

        except:
            pass

        stats['roster'] = roster
        stats['playlist'] = {
            'current': cm,
            'next': nm,
            'items': playlist_items
        }

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
        self.data_handler = BsDataThread()
