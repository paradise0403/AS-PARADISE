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
        "rank": 0,
        "name": "Player",
        "scores": 0,
        "total_damage": 0.0,
        "kills": 0,
        "deaths": 0,
        "games": 0,
        "kd": 0.0,
        "avg_score": 0.0,
        "aid": "pb-IF4VAk4a",
        "last_seen": str(datetime.datetime.now())
    }
}

seasonStartDate = None


# ---------------- LOAD ---------------- #
def get_stats_by_id(account_id: str):
    a = get_cached_stats()
    if account_id in a:
        return a[account_id]
    else:
        return None

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
                seasonStartDate = datetime.datetime.strptime(
                    jsonData["startDate"], "%d-%m-%Y")
                _babase.season_ends_in_days = our_settings[
                                                  "statsResetAfterDays"] - (
                                                  datetime.datetime.now() - seasonStartDate).days
                if (datetime.datetime.now() - seasonStartDate).days >= \
                    our_settings["statsResetAfterDays"]:
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
    shutil.copy(statsfile, statsfile.replace(
        ".json", "") + str(
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + ".json")


# ---------------- SAVE ---------------- #

def dump_stats(s: dict):
    global seasonStartDate

    if seasonStartDate is None:
        seasonStartDate = datetime.datetime.now()

    data = {
        "startDate": seasonStartDate.strftime("%d-%m-%Y"),
        "stats": s
    }

    if os.path.exists(statsfile):
        shutil.copyfile(statsfile, statsfile + ".backup")

    with open(statsfile, 'w', encoding='utf8') as f:
        f.write(json.dumps(data, indent=4, ensure_ascii=False))


# ---------------- SORT ---------------- #

def get_sorted_stats(stats):
    entries = [(a['scores'], a['kills'], a['deaths'], a['games'], a['name'], a['aid'])
               for a in stats.values()]

    entries.sort(key=lambda x: x[0] or 0, reverse=True)
    return entries


# ---------------- REFRESH ---------------- #

def refreshStats():
    global cached_stats, ranks

    stats = get_all_stats()
    cached_stats = stats

    entries = get_sorted_stats(stats)

    rank = 0
    _ranks = []
    toppers = []

    for entry in entries:
        rank += 1

        scores, kills, deaths, games, name, aid = entry

        scores = int(scores)
        kills = int(kills)
        deaths = int(deaths)
        games = int(games)

        # ✅ KD FIX
        kd = round(kills / deaths, 2) if deaths > 0 else float(kills)

        # ✅ AVG SCORE FIX
        avg_score = round(scores / games, 2) if games > 0 else 0.0

        dmg = float(damage_data.get(aid, 0))

        stats[aid]["rank"] = rank
        stats[aid]["scores"] = scores
        stats[aid]["kills"] = kills
        stats[aid]["deaths"] = deaths
        stats[aid]["games"] = games
        stats[aid]["kd"] = kd
        stats[aid]["avg_score"] = avg_score
        stats[aid]["total_damage"] += dmg

        _ranks.append(aid)

        if rank <= 3:
            toppers.append(aid)

    ranks = _ranks

    dump_stats(stats)
    updateTop3Names(toppers)


# ---------------- UPDATE ---------------- #

def update(score_set):
    kills = {}
    deaths = {}
    scores = {}

    for p in score_set.get_records().values():
        aid = p.player.get_v1_account_id()

        if aid:
            kills[aid] = kills.get(aid, 0) + p.accum_kill_count
            deaths[aid] = deaths.get(aid, 0) + p.accum_killed_count
            scores[aid] = scores.get(aid, 0) + p.accumscore

    if scores:
        UpdateThread(kills, deaths, scores).start()


class UpdateThread(threading.Thread):
    def __init__(self, kills, deaths, scores):
        super().__init__()
        self.kills = kills
        self.deaths = deaths
        self.scores = scores

    def run(self):
        stats = get_all_stats()

        for aid in self.kills:

            if aid not in stats:
                stats[aid] = {
                    'rank': 0,
                    'name': "Player",
                    'scores': 0,
                    'total_damage': 0,
                    'kills': 0,
                    'deaths': 0,
                    'games': 0,
                    'kd': 0,
                    'avg_score': 0,
                    'last_seen': str(datetime.datetime.now()),
                    'aid': aid
                }

                # fetch name
                try:
                    url = f"http://bombsquadgame.com/bsAccountInfo?buildNumber=20258&accountID={aid}"
                    data = urllib.request.urlopen(url)
                    name = json.loads(data.read())["profileDisplayString"]
                    stats[aid]['name'] = name if name else "???"
                except:
                    stats[aid]['name'] = "???"

            stats[aid]['kills'] += self.kills[aid]
            stats[aid]['deaths'] += self.deaths[aid]
            stats[aid]['scores'] += self.scores[aid]
            stats[aid]['games'] += 1
            stats[aid]['last_seen'] = str(datetime.datetime.now())

        dump_stats(stats)
        refreshStats()


# ---------------- GETTERS (IMPORTANT) ---------------- #

def get_cached_stats():
    return cached_stats


def getRank(acc_id):
    if not ranks:
        refreshStats()
    return ranks.index(acc_id) + 1 if acc_id in ranks else 0


get_rank = getRank  # alias


def get_score(acc_id):
    return cached_stats.get(acc_id, {}).get('scores', 0)


def get_kills(acc_id):
    return cached_stats.get(acc_id, {}).get('kills', 0)


def get_deaths(acc_id):
    return cached_stats.get(acc_id, {}).get('deaths', 0)


def get_kd(acc_id):
    k = get_kills(acc_id)
    d = get_deaths(acc_id)
    return round(k / d, 2) if d > 0 else float(k)


# ---------------- TOP 3 ---------------- #

def updateTop3Names(ids):
    global top3Name

    names = []
    for aid in ids:
        try:
            url = f"http://bombsquadgame.com/bsAccountInfo?buildNumber=20258&accountID={aid}"
            data = urllib.request.urlopen(url)
            name = json.loads(data.read())["profileDisplayString"]
            names.append(name if name else "???")
        except:
            names.append("???")

    top3Name = names
