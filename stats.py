import DmoParser, os, maputils, sqlite3, sys

def processFile(filename):
    players = {}
    mapname = ""
    gamelimit = 0
    mode = 0
    acdr = DmoParser.AssaultCubeDmoReader()
    welcome = None
    time = 0
    for r in acdr.consumeFile(filename):
        if r['type'] == 'welcome':
            #print r
            mapname = r['mapname']
            r['mapsize'] = maputils.maps[mapname]['size']
            mode = r['smode']
            gamelimit = r['gamelimit']
            for cn, p in r['playernames'].items():
                players[cn] = {'name': p['cname']}
                players[cn].update(r['players'][cn])
                players[cn]['numshots'] = 0
                players[cn]['nkills'] = 0
                players[cn]['nreloads'] = 0
                players[cn]['npickups'] = 0
                #print players[cn]
            welcome = r
            pass
        elif r['type'] == 'newplayer':
            r['numshots'] = 0
            r['nkills'] = 0
            r['nreloads'] = 0
            r['points'] = 0
            r['npickups'] = 0
            players[r['cn']] = r
        elif r['type'] == 'position':
            if r['shooting'] == 1:
                players[r['cn']]['numshots'] += 1
            if r['gametime'] > time:
                time = r['gametime']
        elif r['type'] == 'damage':
            if r['killed']:
                players[r['shooter']]['nkills'] += 1
        elif r['type'] == 'reload':
            players[r['cn']]['nreloads'] += 1
        elif r['type'] == 'weapon_change':
            #players[r['client_id']][
            pass
        elif r['type'] == 'points':
            for cn,pnts in r['points'].items():
                players[cn]['points'] += pnts
        elif r['type'] == 'itemacc':
            players[r['cn']]['npickups'] += 1
            pass
        elif r['type'] == 'itemspawn':
            # Ignore
            pass
        else:
            print(r)
        pass

    for cn,p in players.items():
        print(p['name'], p['numshots'], p['nkills'], p['nreloads'], p['points'])
    welcome['game_length'] = time
    return welcome, players

def tolit(v):
    try:
        return int(v)
    except:
        return "'%s'"%v

def dmoFileToSqlite(filename, gameid, cursor, game_fields, player_fields):
    try:
        welcome, players = processFile(filename)
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        print(filename)
        #raise e
        return 2
    gfs = []
    for gf in game_fields:
        gfs.append(tolit(welcome[gf]))
    gfs = list(map(lambda g: str(g), gfs))
    pfs = []
    for i in players.keys():
        player = []
        for pf in player_fields:
            player.append(tolit(players[i][pf]))
        player = map(lambda p: str(p), player)
        q = "INSERT INTO games VALUES ('%s', %s, %s, %s)"%(gameid, ",".join(gfs), i, ",".join(player))
        print(q)
        cursor.execute(q)
    return 0

def loadDemosToSqlite(dbname=':memory:'):
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE games (gameid text, mapname text, mapsize int, smode int, gamelimit int, duration int, playerid int, playername text, nkills int, npickups int, numshots int, nreloads int)''')
    except:
        pass

    fails = []
    nfails = 0
    ndemos = 0
    for fname in os.listdir('demos'):
        ndemos += 1
        c.execute('''DELETE FROM games WHERE gameid = "%s"'''%fname)
        ret = dmoFileToSqlite('demos/%s'%fname, fname, c, ['mapname', 'mapsize', 'smode', 'gamelimit', 'game_length'], ['name', 'nkills', 'npickups', 'numshots', 'nreloads'])
        if ret == 1:
            break
        elif ret == 2:
            fails.append(fname)
            nfails += 1

    try:
        c.execute("drop table gamestats")
    except:
        pass
    c.execute('''create table gamestats as select gameid,mapname,mapsize,smode,gamelimit,duration,sum(nkills)/count(1) as nkills,sum(numshots)/count(1) as numshots,count(1) as nplayers from games group by gameid;''')
    print("Failed %s times out of %s"%(nfails, ndemos))
    for f in fails:
        print(f)
    return conn

if __name__ == '__main__':
    conn = loadDemosToSqlite('test.db')
    conn.commit()
    conn.close()
