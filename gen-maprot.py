import math
import random
import os.path
import statistics
import maputils
import stats
import sqlite3

# (mode name, game ID, team game ID, requires ctf, relative probability)
modes = [
    ("dm", 2, 0, False, 1),
    ("pf", 6, 16, False, 0.1),
    ("ktf", 15, 14, True, 0.7),
    ("lss", 9, 17, False, 0.8),
    ("osok", 10, 11, False, 1),
    #("s", 3, 4, False, 0.7), # Why bother, when we have dm
    #("ctf", 5), # Too similar to ktf
    #("htf", 13), # Complicated for 3 people
]

def modeIdToName(smode):
    for m in modes:
        if smode == m[1]:
            return m[0]
        if smode == m[2]:
            return "team %s"%m[0]
    return None

#TEAM_PROB = 0.25
TEAM_PROB = 0.35

# Compute statistics of previous games
#sqlite_conn, cursor = stats.loadDemosToSqlite()
sqlite_conn = sqlite3.connect('test.db')
cursor = sqlite_conn.cursor()
sqlite_conn.commit()

# Compute stats about the maps
maps = maputils.maps
totsize = sum(map(lambda m: m['size'], maps.values()))

for mapname in maps.keys():
    cursor.execute("SELECT count(1) FROM gamestats WHERE mapname='%s'"%mapname)
    map_cnt = cursor.fetchone()[0]
    maps[mapname]['playcnt'] = map_cnt

# Compute the number of times that each map has been played for each mode
#cursor.execute("select mapname,smode,sum(numshots)/count(1),count(1),mapsize from games group by mapname,smode order by sum(numshots)")
#rows = cursor.fetchall()
#print(rows)

# Assume that a high # of kills is desirable.
# Assume # of kills is proportional to two things: The map and the game mode.
# Also assume that the map and the game mode are independent.
# Find map and game mode coefficients such that numshots = (map coef.) + (game mode coef.)
map_coefs = {}
mode_coefs = {}
samples = []
for row in cursor.execute("select mapname,smode,sum(nkills),count(1),sum(nkills)/count(1) from gamestats group by mapname,smode order by sum(numshots)/count(1)"):
    #print(row)
    samples.append((row[0], row[1], row[4]))
    map_coefs[row[0]] = 0.0
    mode_coefs[row[1]] = 0.0

def compute_estimate(mapname, mode):
    return map_coefs[mapname] + mode_coefs[mode]

learning_rate = 0.1
for iteration in range(100):
    avg_diff = 0
    for i in range(len(samples)):
        sample = samples[i%len(samples)]
        est = compute_estimate(sample[0], sample[1])
        actual = sample[2]
        #print("//",est-actual)
        avg_diff += math.pow(est-actual,2.0)
        map_coefs[sample[0]] -= (est - actual) * learning_rate
        mode_coefs[sample[1]] -= (est - actual) * learning_rate
    print("//",math.sqrt(avg_diff))
    learning_rate *= 0.95
    pass

l = []
for k,v in map_coefs.items():
    #print("//",k,v)
    l.append((v,k))
l.sort()
print("//")
print("//","\n//".join(["%s: %s"%(x[1], x[0]) for x in l]))

l = []
for k,v in mode_coefs.items():
    l.append((v,modeIdToName(k)))
    #print("//",modeIdToName(k),v)
l.sort()
print("//")
print("//"+"\n//".join(["%s: %s"%(x[1], x[0]) for x in l]))

# Print out the maps in order of size
print("//",totsize)
tot_prob = 0.0
for mapname in maps.keys():
    #maps[mapname]["relprob"] = math.pow(totsize/float(maps[mapname]["size"]), 0.5) / (maps[mapname]['playcnt']+3)
    maps[mapname]["relprob"] = math.pow(2.0, map_coefs[mapname]/3.0) / (maps[mapname]['playcnt']+3)
    tot_prob += maps[mapname]["relprob"]
for mapname in maps.keys():
    maps[mapname]["relprob"] *= 100.0/tot_prob

sm = sorted(maps.keys(), key=lambda a: -maps[a]["relprob"])
for mapname in sm:
    print("//", mapname, maps[mapname]['playcnt'], maps[mapname]["size"], maps[mapname]["relprob"])
for mapname in sm:
    print("//%s,%s,%s,%s,%s"%(mapname, maps[mapname]['playcnt'], maps[mapname]["size"], maps[mapname]["relprob"], map_coefs[mapname]))

# choices is a list of (weight, choice) tuples
def weighted_sample(choices):
    tot_weight = sum(map(lambda choice: choice[0], choices))
    val = random.random() * tot_weight
    for c in choices:
        val -= c[0]
        if val <= 0.0:
            return c[1]
    return choices[-1][1]

def pick_round():
    global TEAM_PROB

    # Pick a map
    #mapname = random.sample(maps.keys(), 1)[0]
    mapname = weighted_sample(list(map(lambda mapname: (maps[mapname]["relprob"], mapname), maps.keys())))
    #mapname = "ac_douze"

    # After we play a map, reduce the probability that it's chosen
    maps[mapname]["relprob"] *= 0.25

    # Pick an appropriate gamemode
    if not maps[mapname]["ctf"]:
        mode = weighted_sample(list(map(lambda mode: (mode[4], mode), filter(lambda mode: not mode[3], modes))))
    else:
        mode = weighted_sample(list(map(lambda mode: (mode[4], mode), modes)))

    # Decrease the probability of this mode in the future
    for i in range(len(modes)):
        if modes[i][0] == mode:
            modes[i] = (modes[i][0], modes[i][1], modes[i][2], modes[i][3], modes[i][4]*0.5)
            break

    # Pick whether it's a team game
    if random.random() < TEAM_PROB:
        teams = True
        modeid = mode[2]
        players = (3, 11)
        TEAM_PROB *= 0.5
    else:
        teams = False
        modeid = mode[1]
        players = (0, 11)
        TEAM_PROB = 1.0 - (1.0 - TEAM_PROB) / 2

    minutes = 8
    print("%s:%s:%s:%s:%s:%s:%s //%s mode, teams=%s"%(mapname, modeid, minutes, 1, players[0], players[1], 0, mode[0], teams))
    return mapname, mode, teams

map_counts = {}
mode_counts = {}
nteams = 0
for i in range(20):
    mapname, mode, teams = pick_round()
    mode_counts[mode[0]] = mode_counts.get(mode[0], 0) + 1
    map_counts[mapname] = map_counts.get(mapname, 0) + 1
    if teams:
        nteams += 1

map_count_counts = [0, 0, 0, 0, 0]
for i in range(len(map_count_counts)):
    map_count_counts[i] = list(map_counts.values()).count(i+1)

nflagmaps = sum(map(lambda m: 1 if m["ctf"] else 0, maps.values()))

print("//%s"%mode_counts)
print("//%s team games"%nteams)
print("//%s of %s maps support flags"%(nflagmaps, len(maps)))
print("//map count counts: %s"%(map_count_counts))

sqlite_conn.close()
