import _thread
import _babase
import _bascenev1
import babase
import bascenev1 as bs
import random
import asyncio
import os
import json
import sys
import importlib.util
from datetime import datetime, timedelta
from babase._general import Call

# Internal imports
from .handlers import send
from stats import mystats

# Commands & Aliases
Commands = [
    'me', 'list', 'uniqeid', 'ping', 'wallet', 'daily', 'pay', 
    'topcasher', 'scoretocash', 'cashtoscore', 'pet', 'custompet', 
    'comp', 'help', 'shop', 'buytag'
]

CommandAliases = [
    'stats', 'score', 'rank', 'myself', 'l', 'id', 'pb-id', 
    'pb', 'accountid', 'coins', 'cash', 'top', 'stoc', 'ctos', 'p', 'h', 'cmds'
]

def ExcelCommand(command, arguments, clientid, accountid):
    """Main Entry Point for Commands"""
    
    # 0. Help Command
    if command in ['help', 'h', 'cmds']:
        handle_help_cmd(arguments, clientid)

    # 1. Stats & Info Commands
    elif command in ['me', 'stats', 'score', 'rank', 'myself']:
        fetch_send_stats(accountid, clientid)
    
    elif command in ['list', 'l']:
        list_players(clientid)
    
    elif command in ['uniqeid', 'id', 'pb-id', 'pb', 'accountid']:
        accountid_request(arguments, clientid, accountid)
    
    elif command in ['ping']:
        get_ping(arguments, clientid)

    # 2. Economy / Coin System Commands
    elif command in ['daily']:
        import coin_system
        send(f"🪙 {coin_system.claim_daily(accountid)[1]}", clientid)
    
    elif command in ['pay']:
        handle_pay(arguments, clientid, accountid)
    
    elif command in ['topcasher', 'top']:
        handle_top_cashers(clientid)
    
    elif command in ['scoretocash', 'stoc']:
        handle_score_to_cash(arguments, accountid, clientid)
    
    elif command in ['cashtoscore', 'ctos']:
        handle_cash_to_score(arguments, accountid, clientid)

    # 3. Shop System Commands (FORCED PATH LOADING)
    elif command in ['shop', 'buytag']:
        try:
            mod_dir = os.path.dirname(os.path.abspath(__file__))
            shop_path = os.path.join(mod_dir, "shop.py")
            
            # This bypasses the "no known parent package" error entirely
            spec = importlib.util.spec_from_file_location("shop_module", shop_path)
            shop = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(shop)
            
            if command == 'shop':
                shop.handle_shop_command(arguments, clientid)
            else:
                shop.handle_buy_tag(arguments, clientid, accountid)
        except Exception as e:
            print(f"CRITICAL SHOP ERROR: {e}")
            send(f"\ue043 Shop Load Fail: {str(e)}", clientid)

    # 4. Pet System
    elif command in ['pet', 'custompet', 'p']:
        try:
            from spazmod import ashx_pets
            target_id = int(arguments[0]) if (arguments and arguments[0].isdigit()) else clientid
            def do_pet():
                try: ashx_pets.handle_pet_command([f'/{command}'] + arguments, target_id)
                except Exception as e: print(f"Pet Logic Error: {e}")
            babase.pushcall(do_pet)
            send("🐾 Processing Pet...", clientid)
        except Exception as e:
            send(f"Pet Error: {e}", clientid)

    # 5. Complaint System
    elif command in ['comp']:
        submit_complaint_cmd(arguments, clientid, accountid)

# --- HELPER FUNCTIONS ---

def handle_help_cmd(args, cid):
    help_list = [
        ("/me", "View your stats/rank"),
        ("/shop", "Open the server shop"),
        ("/buytag", "Buy Tag: /buytag <text> <num>"),
        ("/daily", "Claim daily coins"),
        ("/pay", "Pay: /pay <amt> <id>"),
        ("/top", "Shows Richest players"),
        ("/stoc", "Score to Cash"),
        ("/ctos", "Cash to Score"),
        ("/pet", "Spawn pet: /pet <id>"),
        ("/comp", "Complaint /comp <id> <reason>")
    ]
    try: page = int(args[0]) if (args and args[0].isdigit()) else 1
    except: page = 1
    total_pages = (len(help_list) + 4) // 5
    if page > total_pages or page < 1:
        send(f"\ue043 Invalid page! 1-{total_pages}", cid)
        return
    start = (page - 1) * 5
    msg = f"\ue043 --- HELP PAGE {page}/{total_pages} ---\n"
    for cmd, desc in help_list[start:start+5]:
        msg += f"\ue043 {cmd} : {desc}\n"
    send(msg, cid)

def handle_top_cashers(clientid):
    import coin_system
    top = coin_system.get_top_cashers(8)
    msg, session = "\ue043 --- RICH LIST --- \ue043\n", bs.get_foreground_host_session()
    for i, (aid, info) in enumerate(top):
        name = next((p.getname(icon=False) for p in session.sessionplayers if p.get_v1_account_id() == aid), aid[:10])
        msg += f"{i+1}. {name} : {info['coins']} \ue01d\n"
    send(msg, clientid)

def handle_score_to_cash(args, aid, cid):
    import coin_system
    try: amt = int(args[0]) if args else 500
    except: amt = 500
    s_data = mystats.get_stats_by_id(aid)
    if not s_data or s_data.get('scores', 0) < amt:
        send(f"\ue043 Need {amt} score!", cid)
        return
    coin_system.add_coins(aid, int(amt/10))
    mystats.update_stats(aid, {'scores': -amt})
    send(f"\ue043 Cut {amt} Score -> Added {int(amt/10)} \ue01d!", cid)

def handle_cash_to_score(args, aid, cid):
    import coin_system
    try: amt = int(args[0]) if args else 50
    except: amt = 50
    if coin_system.get_coins(aid) < amt:
        send(f"\ue043 Need {amt} \ue01d!", cid)
        return
    coin_system.add_coins(aid, -amt)
    mystats.update_stats(aid, {'scores': amt*10})
    send(f"\ue043 Cut {amt} \ue01d -> Added {amt*10} Score!", cid)

def handle_pay(args, cid, aid):
    import coin_system
    if len(args) < 2:
        send("Usage: /pay [amount] [id]", cid)
        return
    try: amt, tid = int(args[0]), int(args[1])
    except: return
    if coin_system.get_coins(aid) < amt or amt <= 0:
        send("\ue043 Invalid amount!", cid)
        return
    session = bs.get_foreground_host_session()
    target_aid = next((p.get_v1_account_id() for p in session.sessionplayers if p.inputdevice.client_id == tid), None)
    if target_aid:
        coin_system.add_coins(aid, -amt)
        coin_system.add_coins(target_aid, amt)
        send(f"\ue043 Paid {amt} \ue01d to ID {tid}!", cid)
    else: send("\ue043 Player not found!", cid)

def stats_func(ac_id, clientid):
    import coin_system
    d, c = mystats.get_stats_by_id(ac_id), coin_system.get_coins(ac_id)
    if d: reply = f"\ue043| Name: {d['name']}\n\ue043| ID: {d['aid']}\n\ue043| Coins: {c} \ue01d\n\ue043| Rank: {d['rank']}\n\ue043| Score: {d['scores']}\n\ue043| Kills: {d['kills']}\n\ue043| Deaths: {d['deaths']}"
    else: reply = f"\ue043| Balance: {c} \ue01d\n\ue043| No stats yet!"
    _babase.pushcall(Call(send, reply, clientid), from_other_thread=True)

def fetch_send_stats(ac_id, clientid):
    _thread.start_new_thread(stats_func, (ac_id, clientid,))

def get_ping(args, cid):
    if not args or args == ['']: send(f"Ping: {bs.get_client_ping(cid)}ms", cid)
    elif args[0] == 'all':
        session, msg = bs.get_foreground_host_session(), "--- PINGS ---\n"
        for p in session.sessionplayers: msg += f"{p.getname(icon=True)}: {bs.get_client_ping(int(p.inputdevice.client_id))}ms\n"
        send(msg, cid)

def list_players(cid):
    session, msg = bs.get_foreground_host_session(), "Name | Client ID\n"
    for p in session.sessionplayers: msg += f"{p.getname(icon=False)} | {p.inputdevice.client_id}\n"
    send(msg, cid)

def accountid_request(args, cid, aid):
    if not args or args == ['']: send(f"Your ID: {aid}", cid)
    else:
        try:
            session = bs.get_foreground_host_session()
            target_id = int(args[0])
            for p in session.sessionplayers:
                if p.inputdevice.client_id == target_id:
                    send(f"{p.getname()}: {p.get_v1_account_id()}", cid)
                    return
        except: pass 

def submit_complaint_cmd(arguments, clientid, accountid):
    try:
        from features.complaint_system import submit_complaint
        if len(arguments) < 2:
            send("Usage: /comp <id> <reason>", clientid)
            return
        target_cid = int(arguments[0])
        reason = " ".join(arguments[1:])
        success, msg_text = submit_complaint(clientid, target_cid, reason)
        send(msg_text, clientid)
    except Exception as e:
        send(f"Complaint System Error: {e}", clientid) 