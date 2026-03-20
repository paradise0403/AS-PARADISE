# complaint_system.py
# BombSquad Complaint System — compatible with discord_bot.py
# Place this file alongside discord_bot.py and import it in your plugin entry point.
# Command: /comp <client_id> <reason>

# ============================================================
# ⚙️  CONFIG — fill these in before running
# ============================================================

COMPLAINT_CHANNEL_ID = 1299597098492362752                          # Discord channel ID for complaints
ROLE_PING_1          = 1277625698634170388                          # First role ID to ping  (e.g. Complaint Staff)
ROLE_PING_2          = 1277625812170051696                         # Second role ID to ping (e.g. Moderators)
COOLDOWN_SECONDS     = 900                        # 15 minutes

# ============================================================

import asyncio
from datetime import datetime, timezone

import discord
from discord import ui

import babase
import bascenev1 as bs

# Import shared bot client and helpers from discord_bot.py
from features.discord_bot import client, clean_bs_text

# ---------------- SERVER NAME (auto-fetched) ----------------

def _get_server_name() -> str:
    """Reads party_name from config.json (the server's main config file)."""
    import json, os
    paths = [
        "config.json",
        os.path.join("ba_root", "mods", "defaults", "config.json"),
    ]
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("party_name")
            if name:
                return str(name)
        except Exception:
            pass
    return "BombSquad Server"

# ---------------- COOLDOWN TRACKER ----------------

_cooldowns: dict[str, datetime] = {}   # pbid -> last complaint time
_complaint_counter: int = 0            # increments with each complaint
_COUNTER_FILE = "ba_root/mods/serverdata/complaint_counter.txt"


def _load_counter() -> int:
    """Load complaint counter from file."""
    try:
        with open(_COUNTER_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def _save_counter(value: int):
    """Save complaint counter to file."""
    try:
        with open(_COUNTER_FILE, "w") as f:
            f.write(str(value))
    except Exception:
        pass


def reset_complaint_counter():
    """Call this to reset the complaint counter back to 0."""
    global _complaint_counter
    _complaint_counter = 0
    _save_counter(0)


_complaint_counter = _load_counter()


def _check_cooldown(pbid: str) -> int:
    """Returns remaining cooldown seconds, or 0 if player is free to complain."""
    if pbid not in _cooldowns:
        return 0
    elapsed = (datetime.now(timezone.utc) - _cooldowns[pbid]).total_seconds()
    remaining = COOLDOWN_SECONDS - elapsed
    return max(0, int(remaining))


def _set_cooldown(pbid: str):
    _cooldowns[pbid] = datetime.now(timezone.utc)


# ---------------- DISCORD VIEW (buttons) ----------------

def _has_complaint_permission(interaction) -> bool:
    """Check if the user has ROLE_PING_1, ROLE_PING_2, or admin."""
    member = interaction.user
    if not isinstance(member, discord.Member):
        return False
    if member.guild_permissions.administrator:
        return True
    role_ids = {r.id for r in member.roles}
    return ROLE_PING_1 in role_ids or ROLE_PING_2 in role_ids


class OpenComplaintView(ui.View):
    """Single Solved button — shown when complaint is OPEN."""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="✅ Solved",
        style=discord.ButtonStyle.success,
        custom_id="complaint:solved"
    )
    async def solved_button(self, interaction: discord.Interaction, button: ui.Button):
        if not _has_complaint_permission(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to use this button.",
                ephemeral=True
            )
            return

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.description = "<a:marked:1482486650289389658> SOLVED"

        # Respond first (Discord requires this within 3s)
        await interaction.response.edit_message(embed=embed, view=SolvedComplaintView())

        # Then lock the thread — fetch all active threads to find ours
        try:
            msg = interaction.message
            active = await interaction.guild.active_threads()
            thread = next((t for t in active if t.parent_id == msg.channel.id and t.id == msg.id), None)
            if thread is None:
                # fall back: thread ID == message ID for message-created threads
                thread = interaction.guild.get_thread(msg.id)
            if thread is None:
                thread = await interaction.client.fetch_channel(msg.id)
            if thread is not None:
                await thread.edit(locked=True, archived=False)
        except Exception:
            pass


class SolvedComplaintView(ui.View):
    """Single Reopen button — shown when complaint is SOLVED."""

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="🔓 Reopen",
        style=discord.ButtonStyle.danger,
        custom_id="complaint:reopen"
    )
    async def reopen_button(self, interaction: discord.Interaction, button: ui.Button):
        if not _has_complaint_permission(interaction):
            await interaction.response.send_message(
                "❌ You don't have permission to use this button.",
                ephemeral=True
            )
            return

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.from_rgb(255, 0, 0)
        embed.description = "<a:hourglassgif:1482485838511083670> PENDING"

        await interaction.response.edit_message(embed=embed, view=OpenComplaintView())

        try:
            msg = interaction.message
            active = await interaction.guild.active_threads()
            thread = next((t for t in active if t.parent_id == msg.channel.id and t.id == msg.id), None)
            if thread is None:
                thread = interaction.guild.get_thread(msg.id)
            if thread is None:
                thread = await interaction.client.fetch_channel(msg.id)
            if thread is not None:
                await thread.edit(locked=False, archived=False)
        except Exception:
            pass


ComplaintView = OpenComplaintView


# ---------------- EMBED BUILDER ----------------

def _build_complaint_embed(
    complainer_name: str,
    complainer_v2: str,
    complainer_pbid: str,
    offender_name: str,
    offender_v2: str,
    offender_pbid: str,
    reason: str,
    submitted_at: str,
    linked_accounts: list,
) -> discord.Embed:

    server_name = _get_server_name()

    embed = discord.Embed(
        title=server_name,
        description="<a:hourglassgif:1482485838511083670> PENDING",
        color=discord.Color.from_rgb(255, 0, 0),
        timestamp=datetime.now(timezone.utc)
    )

    embed.add_field(
        name="**<:time:1482457321195045086> Submission**",
        value=f"<a:Animated_Arrow_Bluelight:1482481151368233010> `{submitted_at}`",
        inline=False
    )
    embed.add_field(
        name="**<:complainer:1482451785129005186> Complainer**",
        value=(
            f"<a:Animated_Arrow_Greenlight:1482481588997591141> Name : `{complainer_name}`\n"
            f"<a:Animated_Arrow_Greenlight:1482481588997591141> V2-ID : `{complainer_v2}`\n"
            f"<a:Animated_Arrow_Greenlight:1482481588997591141> PB-ID : `{complainer_pbid}`"
        ),
        inline=False
    )
    embed.add_field(
        name="**<:offender:1482451685849960691> Offender**",
        value=(
            f"<a:Animated_Arrow_Redlight:1482481346495516743> Name : `{offender_name}`\n"
            f"<a:Animated_Arrow_Redlight:1482481346495516743> V2-ID : `{offender_v2}`\n"
            f"<a:Animated_Arrow_Redlight:1482481346495516743> PB-ID : `{offender_pbid}`"
        ),
        inline=False
    )
    embed.add_field(
        name="**<:Description:1482451979191189646> Description**",
        value=f"<a:Animated_Arrow_Yellowlight:1482481886705221856> `{reason}`",
        inline=False
    )

    # Linked accounts — always include offender + any others on same IP
    all_linked = [offender_v2] + linked_accounts
    linked_str = ", ".join(f"`{v2}`" for v2 in all_linked)
    embed.add_field(
        name=f"**<:Linked_accounts:1482451882420211826> Linked Accounts ({len(all_linked)})**",
        value=f"<a:purple_arrow:1482483001702092800> {linked_str}",
        inline=False
    )


    return embed


# ---------------- CORE HANDLER ----------------

async def _send_complaint(
    complainer_name: str,
    complainer_v2: str,
    complainer_pbid: str,
    offender_name: str,
    offender_v2: str,
    offender_pbid: str,
    reason: str,
    linked_accounts: list,
):
    channel = client.get_channel(COMPLAINT_CHANNEL_ID)
    if channel is None:
        return

    from datetime import timedelta
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = datetime.now(timezone.utc) + ist_offset
    submitted_at = now_ist.strftime("%d/%m/%Y %I:%M %p IST")
    server_name  = _get_server_name()

    embed = _build_complaint_embed(
        complainer_name, complainer_v2, complainer_pbid,
        offender_name, offender_v2, offender_pbid,
        reason, submitted_at, linked_accounts
    )

    # Fetch guild icon and set as thumbnail
    guild = channel.guild
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    # Build role ping string
    pings = []
    if ROLE_PING_1:
        pings.append(f"<@&{ROLE_PING_1}>")
    if ROLE_PING_2:
        pings.append(f"<@&{ROLE_PING_2}>")
    ping_str = " ".join(pings)

    view = ComplaintView()

    # Send the embed message with pings
    msg = await channel.send(content=ping_str, embed=embed, view=view)

    # Create a thread on the message
    global _complaint_counter
    _complaint_counter += 1
    _save_counter(_complaint_counter)
    thread_name = f"COMPLAINT NO-{_complaint_counter}"
    thread = await msg.create_thread(name=thread_name, auto_archive_duration=10080)

    await msg.edit(embed=embed)


def submit_complaint(
    complainer_client_id: int,
    offender_client_id: int,
    reason: str,
):
    """
    Called from your chatcommands / handlechat when /comp is used.
    Looks up both players from the roster and fires the Discord send.
    Returns a tuple: (success: bool, message: str)
    """

    roster = bs.get_game_roster()

    complainer_name = "Unknown"
    complainer_v2   = "Unknown"
    complainer_pbid = "Unknown"
    offender_name   = "Unknown"
    offender_v2     = "Unknown"
    offender_pbid   = "Unknown"

    found_complainer = False
    found_offender   = False

    for p in roster:
        cid = p.get('client_id')

        if cid == complainer_client_id:
            complainer_pbid = p.get('account_id', 'Unknown')
            complainer_v2   = clean_bs_text(p.get('display_string', 'Unknown'))
            try:
                complainer_name = clean_bs_text(p['players'][0]['name_full'])
            except Exception:
                complainer_name = complainer_v2
            found_complainer = True

        if cid == offender_client_id:
            offender_pbid = p.get('account_id', 'Unknown')
            offender_v2   = clean_bs_text(p.get('display_string', 'Unknown'))
            try:
                offender_name = clean_bs_text(p['players'][0]['name_full'])
            except Exception:
                offender_name = offender_v2
            found_offender = True

    if not found_complainer:
        return False, "Could not find your account info. Please try again."

    if not found_offender:
        return False, "Player not found. Make sure the client ID is correct."

    # Find how many accounts share the offender's current IP
    linked_accounts = []  # list of (v2_display, pbid) tuples
    try:
        from serverdata import serverdata
        offender_ip = serverdata.clients.get(offender_pbid, {}).get("lastIP")
        if offender_ip:
            for pbid, data in serverdata.clients.items():
                if pbid != offender_pbid and data.get("lastIP") == offender_ip:
                    v2 = data.get("display_string", pbid)
                    linked_accounts.append(v2)
    except Exception:
        pass

    if complainer_client_id == offender_client_id:
        return False, "You can't file a complaint against yourself."

    # Cooldown check
    remaining = _check_cooldown(complainer_pbid)
    if remaining > 0:
        mins = remaining // 60
        secs = remaining % 60
        return False, f"You're on cooldown. Please wait {mins}m {secs}s before submitting another complaint."

    _set_cooldown(complainer_pbid)

    # Schedule the async Discord send on the bot's event loop
    asyncio.run_coroutine_threadsafe(
        _send_complaint(
            complainer_name, complainer_v2, complainer_pbid,
            offender_name, offender_v2, offender_pbid,
            reason, linked_accounts
        ),
        client.loop
    )

    return True, f"✅ Your complaint against {offender_name} has been submitted!"


# ---------------- REGISTER PERSISTENT VIEW ----------------

async def setup_views():
    """Call this once after bot is ready to register the persistent button views."""
    client.add_view(OpenComplaintView())
    client.add_view(SolvedComplaintView())
