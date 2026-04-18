"""Module to keep logs and send them as Discord Embeds via Bot."""

# ba_meta require api 8
from __future__ import annotations

import datetime
import fcntl
import json
import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse
import http.client
import _babase
import setting
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

SETTINGS = setting.get_settings_data()
SERVER_DATA_PATH = os.path.join(
    _babase.env()["python_directory_user"], "serverdata" + os.sep
)

if SETTINGS["discordbot"]["enable"]:
    from features import discord_bot

# Standard Webhook URL (kept for compatibility)
WEBHOOK_URL = SETTINGS["discordWebHook"]["webhookURL"]

@dataclass
class RecentLogs:
    """Saves the recent logs."""
    chats: list[str] = field(default_factory=list)
    joinlog: list[str] = field(default_factory=list)
    cmndlog: list[str] = field(default_factory=list)
    misclogs: list[str] = field(default_factory=list)

logs = RecentLogs()

def get_embed_color(mtype: str) -> int:
    """Returns color hex codes for the side strip of the embed."""
    colors = {
        "chat": 3066993,       # Green
        "playerjoin": 3447003, # Blue
        "chatcmd": 15105570,   # Orange
        "sys": 9807270         # Gray
    }
    return colors.get(mtype, 9807270)

def log(msg: str, mtype: str = "sys") -> None:
    """Cache and dumps the log. Sends Embeds to the bot."""

    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    full_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = msg.replace("||", "|")

    # --- DISCORD BOT EMBED LOGIC ---
    if SETTINGS["discordbot"]["enable"]:
        # We build a 'pseudo-embed' string or dict. 
        # Most custom BS bots use a specific push_log logic.
        # If your bot supports Dicts, use this:
        embed_data = {
            "title": f"MOD LOG - {mtype.upper()}",
            "description": message,
            "color": get_embed_color(mtype),
            "timestamp": full_date
        }
        
        # If your bot only accepts strings, we 'fake' the embed look using code blocks:
        embed_fallback = (
            f"```ansi\n"
            f"[1;34m[{current_time}][0m [1;33m**{mtype.upper()}**[0m\n"
            f"{message}\n"
            f"```"
        )
        
        # NOTE: If your discord_bot.push_log supports embeds, pass embed_data.
        # Otherwise, we use the fallback which looks much better than plain text.
        discord_bot.push_log(embed_fallback)

    # --- LOCAL FILE LOGGING ---
    file_msg = f"{full_date} + : {msg} \n"

    if mtype == "chat":
        logs.chats.append(file_msg)
        if len(logs.chats) > 1:
            dumplogs(logs.chats, "chat").start()
            logs.chats = []
    elif mtype == "playerjoin":
        logs.joinlog.append(file_msg)
        if len(logs.joinlog) > 3:
            dumplogs(logs.joinlog, "joinlog").start()
            logs.joinlog = []
    elif mtype == "chatcmd":
        logs.cmndlog.append(file_msg)
        if len(logs.cmndlog) > 3:
            dumplogs(logs.cmndlog, "cmndlog").start()
            logs.cmndlog = []
    else:
        logs.misclogs.append(file_msg)
        if len(logs.misclogs) > 5:
            dumplogs(logs.misclogs, "sys").start()
            logs.misclogs = []

class dumplogs(threading.Thread):
    """Dumps the logs in the server data."""
    def __init__(self, msg, mtype="sys"):
        super().__init__()
        self.msg = msg
        self.type = mtype

    def run(self):
        log_names = {
            "chat": "Chat Logs.log",
            "joinlog": "joining.log",
            "cmndlog": "cmndusage.log"
        }
        log_path = SERVER_DATA_PATH + log_names.get(self.type, "systemlogs.log")

        if os.path.exists(log_path) and os.stat(log_path).st_size > 1000000:
            suffix = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.copy_file(log_path, f"{log_path}_{suffix}")

        self.write_file(log_path, self.msg)

    def write_file(self, file_path, data):
        with open(file_path, "a+", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                for line in data:
                    f.write(line)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def copy_file(self, file_path, dest_path):
        try:
            shutil.copy(file_path, dest_path)
            os.remove(file_path)
        except Exception as e:
            print(f"Log error: {e}")
 
 