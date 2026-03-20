import datetime
import json
import os
import shutil
import threading
import urllib.request

import _babase
import setting

damage_data = {}
ranks = []
top3Name = []

our_settings = setting.get_settings_data()

base_path = os.path.join(_babase.env()['python_directory_user'], "stats" + os.sep)
statsfile = base_path + 'stats.json'
cached_stats = {}
statsDefault = {
    "pb-IF4VAk4a": {
        "rank": 65,
        "name": "pb-IF4VAk4a",
        "scores": 0,
        "total_damage": 0.0,
        "kills": 0,
        "deaths": 0,
        "games": 18,
        "kd": 0.0,
        "avg_score": 0.0,
        "aid": "pb-IF4VAk4a",
        "last_seen": "2022-04-26 17:01:13.715014"
    }
}

seasonStartDate = None

def get_all_stats():
    global seasonStartDate
    if os.path.exists(statsfile):
        with open(statsfile, 'r', encoding='utf8') as f:
            try:
                jsonData = json.loads(f.read())
            except:
                f = open(statsfile + ".backup", encoding='utf-8')
                jsonData = json.load(f)
            try:
                stats = jsonData["stats"]
                seasonStartDate = datetime.datetime.strptime(jsonData["startDate"], "%d-%m-%Y")
                _babase.season_ends_in_days = our_settings["statsResetAfterDays"] - (datetime.datetime.now() - seasonStartDate).days
                if (datetime.datetime.now() - seasonStartDate).days >= our_settings["statsResetAfterDays"]:
                    backupStatsFile()
                    seasonStartDate = datetime.datetime.now()
                    return statsDefault
                return stats
            except OSError as e:
                print(e)
                return jsonData
    else:
        return {}

def backupStatsFile():
    shutil.copy(statsfile, statsfile.replace(".json", "") + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ".json")

def dump_stats(s: dict):
    global seasonStartDate
    if seasonStartDate == None:
        seasonStartDate = datetime.datetime.now()
    s = {"startDate": seasonStartDate.strftime("%d-%m-%Y"), "stats": s}
    if os.path.exists(statsfile):
        shutil.copyfile(statsfile, statsfile + ".backup")
        with open(statsfile, 'w', encoding='utf8') as f:
            f.write(json.dumps(s, indent=4, ensure_ascii=False))
    else:
        print('Stats file not found!')

def get_stats_by_id(account_id: str):
    a = get_cached_stats()
    if account_id in a:
        return a[account_id]
    return None

def get_cached_stats():
    return cached_stats

def get_sorted_stats(stats):
    entries = [(a['scores'], a['kills'], a['deaths'], a['games'], a['name'], a['aid']) for a in stats.values()]
    entries.sort(key=lambda x: x[0] or 0, reverse=True) # Changed to sort by score for better accuracy
    return entries

def refreshStats():
    global cached_stats
    pStats = get_all_stats()
    cached_stats = pStats
    entries = get_sorted_stats(pStats)
    rank = 0
    toppersIDs = []
    _ranks = []
    for entry in entries:
        rank += 1
        scores, kills, deaths, games, name, aid = entry
        if rank < 6: toppersIDs.append(aid)
        
        try: p_kd = float(kills) / float(deaths) if int(deaths) > 0 else float(kills)
        except: p_kd = 0.0
        try: p_avg_score = float(scores) / float(games) if int(games) > 0 else float(scores)
        except: p_avg_score = 0.0
        
        _ranks.append(aid)
        pStats[str(aid)]["rank"] = int(rank)
        pStats[str(aid)]["scores"] = int(scores)
        pStats[str(aid)]["kills"] = int(kills)
        pStats[str(aid)]["deaths"] = int(deaths)
        pStats[str(aid)]["kd"] = round(p_kd, 3)
        pStats[str(aid)]["avg_score"] = round(p_avg_score, 3)

    global ranks
    ranks = _ranks
    dump_stats(pStats)
    updateTop3Names(toppersIDs[0:3])
    from playersdata import pdata
    pdata.update_toppers(toppersIDs)

def update_stats(account_id, changes):
    """Custom function to add/subtract scores manually for the coin system."""
    data_all = {"startDate": seasonStartDate.strftime("%d-%m-%Y") if seasonStartDate else "01-01-2024", "stats": get_all_stats()}
    stats_dict = data_all["stats"]
    if account_id in stats_dict:
        for key, value in changes.items():
            if key in stats_dict[account_id]:
                stats_dict[account_id][key] += value
        dump_stats(stats_dict)
        refreshStats()

def update(score_set):
    account_kills, account_deaths, account_scores = {}, {}, {}
    for p_entry in score_set.get_records().values():
        account_id = p_entry.player.get_v1_account_id()
        if account_id:
            account_kills[account_id] = account_kills.get(account_id, 0) + p_entry.accum_kill_count
            account_deaths[account_id] = account_deaths.get(account_id, 0) + p_entry.accum_killed_count
            account_scores[account_id] = account_scores.get(account_id, 0) + p_entry.accumscore
    if account_scores:
        UpdateThread(account_kills, account_deaths, account_scores).start()

class UpdateThread(threading.Thread):
    def __init__(self, account_kills, account_deaths, account_scores):
        threading.Thread.__init__(self)
        self._kills, self._deaths, self._scores = account_kills, account_deaths, account_scores
    def run(self):
        stats = get_all_stats()
        for aid, kill_count in self._kills.items():
            if aid not in stats:
                stats[aid] = {'rank':0, 'name':"???", 'scores':0, 'total_damage':0, 'kills':0, 'deaths':0, 'games':0, 'kd':0, 'avg_score':0, 'last_seen':str(datetime.datetime.now()), 'aid':str(aid)}
                try:
                    url = "http://bombsquadgame.com/bsAccountInfo?buildNumber=20258&accountID=" + aid
                    data = urllib.request.urlopen(url)
                    stats[aid]['name'] = json.loads(data.read())["profileDisplayString"]
                except: pass
            stats[aid]['kills'] += kill_count
            stats[aid]['deaths'] += self._deaths[aid]
            stats[aid]['scores'] += self._scores[aid]
            stats[aid]['games'] += 1
            stats[aid]['last_seen'] = str(datetime.datetime.now())
        dump_stats(stats)
        refreshStats()

def getRank(acc_id):
    global ranks
    if not ranks: refreshStats()
    return ranks.index(acc_id) + 1 if acc_id in ranks else None

def updateTop3Names(ids):
    global top3Name
    names = []
    for id in ids:
        try:
            url = "http://bombsquadgame.com/bsAccountInfo?buildNumber=20258&accountID=" + id
            names.append(json.loads(urllib.request.urlopen(url).read())["profileDisplayString"] or "???")
        except: names.append("???")
    top3Name = names