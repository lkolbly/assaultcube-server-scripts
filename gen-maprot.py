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

TEAM_PROB = 0.35

# Compute statistics of previous games
#sqlite_conn, cursor = stats.loadDemosToSqlite()
sqlite_conn = sqlite3.connect('test.db')
cursor = sqlite_conn.cursor()
sqlite_conn.commit()

# Compute stats about the maps
maps = maputils.maps

for mapname in maps.keys():
    cursor.execute("SELECT count(1) FROM gamestats WHERE mapname='%s'"%mapname)
    map_cnt = cursor.fetchone()[0]
    maps[mapname]['playcnt'] = map_cnt

# Assume that a high # of kills is desirable.
# Assume # of kills is proportional to two things: The map and the game mode.
# Also assume that the map and the game mode are independent.
# Find map and game mode coefficients such that numshots = (map coef.) + (game mode coef.)

# Find all of the map/mode combinations and average the kills for each combination
map_coefs = {}
mode_coefs = {}
samples = []
for row in cursor.execute("select mapname,smode,sum(nkills),count(1),sum(nkills)/count(1) from gamestats group by mapname,smode order by sum(numshots)/count(1)"):
    samples.append((row[0], row[1], row[4]))
    map_coefs[row[0]] = 0.0
    mode_coefs[row[1]] = 0.0

# Do an iterative linear regression to find the coefficients
learning_rate = 0.1
for iteration in range(100):
    avg_diff = 0
    for i in range(len(samples)):
        sample = samples[i%len(samples)]
        est = map_coefs[sample[0]] + mode_coefs[sample[1]]
        actual = sample[2]
        #print("//",est-actual)
        avg_diff += math.pow(est-actual,2.0)
        map_coefs[sample[0]] -= (est - actual) * learning_rate
        mode_coefs[sample[1]] -= (est - actual) * learning_rate
    print("//",math.sqrt(avg_diff))
    learning_rate *= 0.95
    pass

# Check to see whether there are maps we have no data about. If so, rank them highly (so we get data).
for mapname in maps.keys():
    if mapname not in map_coefs:
        print("// No data about map '%s', setting coef to max"%mapname)
        map_coefs[mapname] = max(list(map_coefs.values())+[0])

# Print out what we learned
l = []
for k,v in map_coefs.items():
    l.append((v,k))
l.sort()
print("//")
print("//","\n//".join(["%s: %s"%(x[1], x[0]) for x in l]))

l = []
for k,v in mode_coefs.items():
    l.append((v,modeIdToName(k)))
l.sort()
print("//")
print("//"+"\n//".join(["%s: %s"%(x[1], x[0]) for x in l]))

# Weight each map (taking into account the fun coefficient and the play count
tot_prob = 0.0
for mapname in maps.keys():
    maps[mapname]["relprob"] = math.pow(2.0, map_coefs[mapname]/3.0) / (maps[mapname]['playcnt']+3)
    tot_prob += maps[mapname]["relprob"]

# Convert the weight to a (percentage) probability (for easier reading)
for mapname in maps.keys():
    maps[mapname]["relprob"] *= 100.0/tot_prob

# Sort them and print the maps
sm = sorted(maps.keys(), key=lambda a: -maps[a]["relprob"])
for mapname in sm:
    print("//", mapname, maps[mapname]['playcnt'], maps[mapname]["relprob"])
for mapname in sm:
    print("//%s,%s,%s,%s"%(mapname, maps[mapname]['playcnt'], maps[mapname]["relprob"], map_coefs[mapname]))

# Choose an element randomly from a list of weighted choices.
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
    mapname = weighted_sample(list(map(lambda mapname: (maps[mapname]["relprob"], mapname), maps.keys())))

    # After we play a map, reduce the probability that it's chosen
    maps[mapname]["relprob"] *= 0.25

    # Pick an appropriate gamemode (not all maps support CTF)
    if not maps[mapname]["ctf"]:
        mode = weighted_sample(list(map(lambda mode: (mode[4], mode), filter(lambda mode: not mode[3], modes))))
    else:
        mode = weighted_sample(list(map(lambda mode: (mode[4], mode), modes)))

    # Decrease the probability of choosing this mode in the future
    for i in range(len(modes)):
        if modes[i][0] == mode:
            modes[i] = (modes[i][0], modes[i][1], modes[i][2], modes[i][3], modes[i][4]*0.5)
            break

    # Pick whether it's a team game
    # If it is a team game, reduce the chances of a team game in the future - otherwise increase the odds.
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

    # Decide how long the game will be
    minutes = 8

    # Send the output
    print("%s:%s:%s:%s:%s:%s:%s //%s mode, teams=%s"%(mapname, modeid, minutes, 1, players[0], players[1], 0, mode[0], teams))
    return mapname, mode, teams

#
# Generate a few rounds for the rotation
#

map_counts = {}
mode_counts = {}
nteams = 0
for i in range(20):
    mapname, mode, teams = pick_round()
    mode_counts[mode[0]] = mode_counts.get(mode[0], 0) + 1
    map_counts[mapname] = map_counts.get(mapname, 0) + 1
    if teams:
        nteams += 1

# Generate some diagnostic statistics about the rounds

map_count_counts = [0, 0, 0, 0, 0]
for i in range(len(map_count_counts)):
    map_count_counts[i] = list(map_counts.values()).count(i+1)

nflagmaps = sum(map(lambda m: 1 if m["ctf"] else 0, maps.values()))

print("//%s"%mode_counts)
print("//%s team games"%nteams)
print("//%s of %s maps support flags"%(nflagmaps, len(maps)))
print("//map count counts: %s"%(map_count_counts))

sqlite_conn.close()
