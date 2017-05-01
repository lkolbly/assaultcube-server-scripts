import struct, gzip, io, binascii

FLAG_GAMES = [15, 14]
GUN_KNIFE = 0
GUN_PISTOL = 1
GUN_CARBINE = 2
GUN_SHOTGUN = 3
GUN_SUBGUN = 4
GUN_SNIPER = 5
GUN_ASSAULT = 6
GUN_CPISTOL = 7
GUN_GRENADE = 8
GUN_AKIMBO = 9
NUMGUNS = 10
GUN_NAMES = ['GUN_KNIFE', 'GUN_PISTOL', 'GUN_CARBINE', 'GUN_SHOTGUN', 'GUN_SUBGUN', 'GUN_SNIPER', 'GUN_ASSAULT', 'GUN_CPISTOL', 'GUN_GRENADE', 'GUN_AKIMBO']

DHDR_DESCCHARS = 80
DHDR_PLISTCHARS = 322
VERSION = 2
SERVER_PROTOCOL_VERSION = 1201

CTFF_INBASE = 0
CTFF_STOLEN = 1
CTFF_DROPPED = 2
CTFF_IDLE = 3

DMF = 16.0
DVELF = 4.0

class AssaultCubeDmoReader:
    def __init__(self):
        self.bits_cache = []
        self.players = {}

        self.PACKETS = {
            'SV_SERVINFO': {'id': 0, 'handler': None},
            'SV_WELCOME': {'id': 1, 'handler': self.readwelcomepacket},
            'SV_INITCLIENT': {'id': 2, 'handler': self.handle_initclient},
            'SV_POS': {'id': 3, 'handler': self.handle_pos},
            'SV_POSC': {'id': 4, 'handler': self.handle_posc},
            'SV_POSN': {'id': 5, 'handler': None},
            'SV_TEXT': {'id': 6, 'handler': None},
            'SV_TEAMTEXT': {'id': 7, 'handler': None},
            'SV_TEXTME': {'id': 8, 'handler': None},
            'SV_TEAMTEXTME': {'id': 9, 'handler': None},
            'SV_TEXTPRIVATE': {'id': 10, 'handler': None},
            'SV_SOUND': {'id': 11, 'handler': self.noop_handler},
            'SV_VOICECOM': {'id': 12, 'handler': self.noop_handler},
            'SV_VOICECOMTEAM': {'id': 13, 'handler': self.noop_handler},
            'SV_CDIS': {'id': 14, 'handler': None},
            'SV_SHOOT': {'id': 15, 'handler': None},
            'SV_EXPLODE': {'id': 16, 'handler': None},
            'SV_SUICIDE': {'id': 17, 'handler': None},
            'SV_AKIMBO': {'id': 18, 'handler': None},
            'SV_RELOAD': {'id': 19, 'handler': self.handle_reload},
            'SV_AUTHT': {'id': 20, 'handler': None},
            'SV_AUTHREQ': {'id': 21, 'handler': None},
            'SV_AUTHTRY': {'id': 22, 'handler': None},
            'SV_AUTHANS': {'id': 23, 'handler': None},
            'SV_AUTHCHAL': {'id': 24, 'handler': None},
            'SV_GIBDIED': {'id': 25, 'handler': self.handle_died},
            'SV_DIED': {'id': 26, 'handler': self.handle_died},
            'SV_GIBDAMAGE': {'id': 27, 'handler': self.handle_damage},
            'SV_DAMAGE': {'id': 28, 'handler': self.handle_damage},
            'SV_HITPUSH': {'id': 29, 'handler': None},
            'SV_SHOTFX': {'id': 30, 'handler': self.noop_handler},
            'SV_THROWNADE': {'id': 31, 'handler': self.handle_thrownade},
            'SV_TRYSPAWN': {'id': 32, 'handler': None},
            'SV_SPAWNSTATE': {'id': 33, 'handler': None},
            'SV_SPAWN': {'id': 34, 'handler': self.handle_spawn},
            'SV_SPAWNDENY': {'id': 35, 'handler': None},
            'SV_FORCEDEATH': {'id': 36, 'handler': None},
            'SV_RESUME': {'id': 37, 'handler': None},
            'SV_DISCSCORES': {'id': 38, 'handler': None},
            'SV_TIMEUP': {'id': 39, 'handler': self.handle_timeup},
            'SV_EDITENT': {'id': 40, 'handler': None},
            'SV_ITEMACC': {'id': 41, 'handler': self.handle_itemacc},
            'SV_MAPCHANGE': {'id': 42, 'handler': None},
            'SV_ITEMSPAWN': {'id': 43, 'handler': self.handle_itemspawn},
            'SV_ITEMPICKUP': {'id': 44, 'handler': None},
            'SV_PING': {'id': 45, 'handler': None},
            'SV_PONG': {'id': 46, 'handler': None},
            'SV_CLIENTPING': {'id': 47, 'handler': self.handle_clientping},
            'SV_GAMEMODE': {'id': 48, 'handler': None},
            'SV_EDITMODE': {'id': 49, 'handler': None},
            'SV_EDITH': {'id': 50, 'handler': None},
            'SV_EDITT': {'id': 51, 'handler': None},
            'SV_EDITS': {'id': 52, 'handler': None},
            'SV_EDITD': {'id': 53, 'handler': None},
            'SV_EDITE': {'id': 54, 'handler': None},
            'SV_NEWMAP': {'id': 55, 'handler': None},
            'SV_SENDMAP': {'id': 56, 'handler': None},
            'SV_RECVMAP': {'id': 57, 'handler': None},
            'SV_REMOVEMAP': {'id': 58, 'handler': None},
            'SV_SERVMSG': {'id': 59, 'handler': None},
            'SV_ITEMLIST': {'id': 60, 'handler': None},
            'SV_WEAPCHANGE': {'id': 61, 'handler': self.handle_weapchange},
            'SV_PRIMARYWEAP': {'id': 62, 'handler': None},
            'SV_FLAGACTION': {'id': 63, 'handler': None},
            'SV_FLAGINFO': {'id': 64, 'handler': None},
            'SV_FLAGMSG': {'id': 65, 'handler': None},
            'SV_FLAGCNT': {'id': 66, 'handler': None},
            'SV_ARENAWIN': {'id': 67, 'handler': self.handle_arenawin},
            'SV_SETADMIN': {'id': 68, 'handler': None},
            'SV_SERVOPINFO': {'id': 69, 'handler': self.noop_handler},
            'SV_CALLVOTE': {'id': 70, 'handler': None},
            'SV_CALLVOTESUC': {'id': 71, 'handler': None},
            'SV_CALLVOTEERR': {'id': 72, 'handler': None},
            'SV_VOTE': {'id': 73, 'handler': None},
            'SV_VOTERESULT': {'id': 74, 'handler': None},
            'SV_SETTEAM': {'id': 75, 'handler': None},
            'SV_TEAMDENY': {'id': 76, 'handler': None},
            'SV_SERVERMODE': {'id': 77, 'handler': None},
            'SV_IPLIST': {'id': 78, 'handler': None},
            'SV_LISTDEMOS': {'id': 79, 'handler': None},
            'SV_SENDDEMOLIST': {'id': 80, 'handler': None},
            'SV_GETDEMO': {'id': 81, 'handler': None},
            'SV_SENDDEMO': {'id': 82, 'handler': None},
            'SV_DEMOPLAYBACK': {'id': 83, 'handler': None},
            'SV_CONNECT': {'id': 84, 'handler': None},
            'SV_SWITCHNAME': {'id': 85, 'handler': None},
            'SV_SWITCHSKIN': {'id': 86, 'handler': None},
            'SV_SWITCHTEAM': {'id': 87, 'handler': None},
            'SV_CLIENT': {'id': 88, 'handler': self.handle_client},
            'SV_EXTENSION': {'id': 89, 'handler': None},
            'SV_MAPIDENT': {'id': 90, 'handler': self.handle_mapident},
            'SV_HUDEXTRAS': {'id': 91, 'handler': None},
            'SV_POINTS': {'id': 92, 'handler': self.handle_points}
        }

    def get(self, fmt, f):
        size = struct.calcsize(fmt)
        #print size
        s = f.read(size)
        #print(fmt, len(s))
        return struct.unpack(fmt, s)

    def add_to_bitscache(self, f):
        c, = self.get("b", f)
        for i in range(8):
            self.bits_cache.append((c >> (7-i)) & 1)
            #bits_cache.append((c >> i) & 1)

    def getbits(self, f, nbits):
        res = 0
        n = 0
        while nbits > 0:
            if len(self.bits_cache) == 0:
                self.add_to_bitscache(f)
            res = res | (self.bits_cache.pop() << n)
            nbits -= 1
            n += 1
        return res

    def rembits(self, ):
        return len(self.bits_cache)

    def finishgetbits(self, ):
        self.bits_cache = []

    def getint(self, f):
        b1, = self.get("b", f)
        #print(b1)
        if b1 == -127:
            i, = self.get("i", f)
            return i
        if b1 == -128:
            i, = self.get("h", f)
            return i
        return b1

    def getuint(self, f):
        b1, = self.get("B", f)
        if b1&0x80 != 0:
            b1 += (self.get("B", f)[0] << 7) - 0x80
        if b1&(1<<14) != 0:
            b1 += (self.get("B", f)[0] << 14) - (1<<14)
        if b1&(1<<21) != 0:
            b1 += (self.get("B", f)[0] << 21) - (1<<21)
        if b1&(1<<28) != 0:
            b1 |= 0xf0000000
        return b1

    def getstring(self, f):
        c = f.read(1)
        s = ""
        while c[0] != 0:
            s += chr(c[0])
            c = f.read(1)
        return s

    def get_fmt(self, f, fmt, *args, **kwargs):
        if len(args) != len(fmt):
            raise Exception("%s != %s"%(len(args), len(fmt)))
        res = {}
        for k,v in kwargs.items():
            res[k] = v
        for i in range(len(fmt)):
            v = None
            if fmt[i] == 'i':
                v = self.getint(f)
            elif fmt[i] == 's':
                v = self.getstring(f)
            elif fmt[i] == 'u':
                v = self.getuint(f)
            if v is not None:
                res[args[i]] = v
            else:
                raise Exception("Unknown format code %s"%fmt[i])
            #print("got ",v)
            pass
        return res

    def readdemo(self, f):
        stamp = self.get("ii", f)
        #print stamp
        data = f.read(stamp[1])
        return stamp,data

    def readheader(self, f):
        fmt = "16sii%ss%ssi"%(DHDR_DESCCHARS, DHDR_PLISTCHARS)
        print(fmt)
        magicbytes, version, protocol, desc, plist, nextplayback = self.get(fmt, f)
        if magicbytes != "ASSAULTCUBE_DEMO":
            return False
        if version != VERSION:
            return False
        if protocol != SERVER_PROTOCOL_VERSION:
            return False

        print("Game description: %s"%desc)
        print("Players: %s"%plist)
        print("Next playback for packet: %s"%nextplayback)
        #print binascii.hexlify(f.read(16))
        return True

    def get_flag_info(self, f):
        sv_flaginfo = self.getint(f)
        flag = self.getint(f)
        flagstate = self.getint(f)
        holder = None
        pos = None
        if flagstate == CTFF_STOLEN:
            holder = self.getint(f)
        elif flagstate == CTFF_DROPPED:
            pos = [self.getint(f), self.getint(f), self.getint(f)]
        elif flagstate == CTFF_INBASE:
            pass # Do nothing
        elif flagstate == CTFF_IDLE:
            pass # Do nothing
        else:
            print("Unknown flagstate '%s'"%flagstate)
        return flag,flagstate,holder,pos

    def get_item_list(self, f, flags):
        sv_itemlist = self.getint(f) # Magic number
        if sv_itemlist != 60:
            raise "Expected 60 got %s"%sv_itemlist
        sents = []
        sent = self.getint(f)
        while sent != -1:
            sents.append(sent)
            #print sent
            sent = self.getint(f)
        flags_out = None
        if flags:
            flags_out = []
            print("reading flags")
            for i in [0,1]:
                flags_out.append(self.get_flag_info(f))
        return sents, flags_out

    def readwelcomepacket(self, p, f):
        #magic = getint(f)
        numcl = self.getint(f)
        self.numcl = numcl
        #print ""%(magic, numcl)
        #if magic != SV_WELCOME:
        #    return False
        print("num clients: %s"%numcl)

        r = {
            'type': 'welcome'
        }

        if numcl >= 0:
            # Parse some map things
            r.update(self.get_fmt(f, "isiii", 'mapchange', 'mapname', 'smode', 'available', 'revision'))
            self.smode = r['smode']
            flags = self.smode in FLAG_GAMES
            #print mapname, smode, available, revision, flags
            print(self.smode, flags)

            # Assuming there are no local clients
            if self.smode > 1 or (self.smode == 0 and numcl > 0):
                sv_timeup = self.getint(f)
                millis = self.getint(f)
                r['gamelimit'] = self.getint(f)
                pass
            # Read out the sents list (the map items - pickups, perhaps?)
            sents = self.get_item_list(f, flags)
            print(sents)
            print(r)

        # Read the stats for each player
        sv_resume = self.getint(f)
        if sv_resume != 37:
            raise Exception("Expected 37 got %s"%sv_resume)
        r['players'] = {}
        for c in range(numcl):
            pl = {}
            cnum = self.getint(f)
            pl.update(self.get_fmt(f, "iiiiiiiiiii", 'state', 'lifeseq', 'primary', 'gunselect', 'flagscore', 'frags', 'deaths', 'health', 'armour', 'points', 'teamkills'))
            ammo = []
            for i in range(NUMGUNS):
                #ammo = self.getint(f)
                ammo.append(self.getint(f))
                #print "%s: ammo = %s"%(GUN_NAMES[i], ammo)
            mag = []
            for i in range(NUMGUNS):
                mag.append(self.getint(f))
            pl['ammo'] = ammo
            pl['mag'] = mag
            #self.players[cnum] = pl
            r['players'][cnum] = pl
        self.getint(f) # Should be -1

        # Init each client
        r['playernames'] = {}
        for c in range(numcl):
            sv_initclient = self.getint(f)
            p = {}
            cnum = self.getint(f)
            p.update(self.get_fmt(f, "siiii", 'cname', 'skin_cla', 'skin_rvsf', 'team', 'ip'))
            r['playernames'][cnum] = p
            #print cname, cnum, team, skin_cla, skin_rvsf
            pass

        sv_servermode = self.getint(f)
        sendservermode = self.getint(f)

        # TODO: How do we tell?
        #sv_text = getint(f)
        #motd = getstring(f)
        return r

    def handle_posc(self, p, f):
        cn = self.getbits(f, 5)
        #print cn

        usefactor = self.getbits(f, 2) + 7
        #print "usefactor:%s"%usefactor
        xt = self.getbits(f, usefactor+4)
        yt = self.getbits(f, usefactor+4)
        cly = (self.getbits(f, 9)*360)/512 # yaw
        clp = ((self.getbits(f,8)-128)*90)/127 # pitch
        #print xt, yt, cly, clp

        if self.getbits(f,1) == 0:
            self.getbits(f, 6) # Burn 6 bits
        if self.getbits(f,1) == 0:
            self.getbits(f, 12) # Burn 12 bits

        clf = self.getbits(f, 8)
        negz = self.getbits(f, 1)
        zfull = self.getbits(f, 1)
        #print negz, zfull

        s = self.rembits()
        #print "rembits %s"%s
        if s < 3:
            s += 8
        if zfull:
            s = 11
        zt = self.getbits(f, s)
        if negz:
            zt = -zt
        #print s, zt

        scoping = self.getbits(f, 1)
        shooting = self.getbits(f, 1)

        self.finishgetbits()
        return {
            'cn': cn,
            'type': 'position',
            'x': xt,
            'y': yt,
            'z': zt,
            'yaw': cly,
            'pitch': clp,
            'scoping': scoping,
            'shooting': shooting
        }

    def handle_pos(self, p, f):
        cn = self.getint(f)
        px = self.getuint(f) / DMF
        py = self.getuint(f) / DMF
        pz = self.getuint(f) / DMF
        yaw = float(self.getuint(f))
        pitch = float(self.getuint(f))
        g = self.getuint(f)
        if (g>>3)&1 != 0:
            roll = self.getint(f) * 20.0 / 125.0
        if g&1 != 0:
            vx = self.getint(f) / DVELF
        if g&2 != 0:
            vy = self.getint(f) / DVELF
        if g&4 != 0:
            vz = self.getint(f) / DVELF
        scoping = g&16 != 0
        shooting = g&32 != 0
        #getuint(f) # Unknown - part of seqcolor?
        return {
            'cn': cn,
            'type': 'position',
            'x': px,
            'y': py,
            'z': pz,
            'yaw': yaw,
            'pitch': pitch,
            'scoping': scoping,
            'shooting': shooting
        }

    def _get_packet(self, ptype):
        for pname, pmeta in self.PACKETS.items():
            if pmeta['id'] == ptype:
                return pname, pmeta
        return None,None

    def handle_client(self, p, f):
        #print "Got client packet"
        cn = self.getint(f)
        l = self.getuint(f)
        cnt = 0
        result = []
        #print "bar"
        while True:
            #print "foo"
            # If we can't read the type, we're done
            try:
                ptype = self.getint(f)
            except:
                break
            #print ptype

            pname, pmeta = self._get_packet(ptype)
            if pname == None:
                print("Could not find a packet for id %s"%ptype)
                break

            if pname == 'SV_CLIENT':
                #print "SV_CLIENT inside SV_CLIENT: Not supported!"
                break

            #print pname, pmeta['handler'] == self.noop_handler
            if pmeta['handler'] is not None and pmeta['handler'] != self.noop_handler:
                r = pmeta['handler'](pname, f)
                if r is not None:
                    if isinstance(r, dict):
                        #print pname, r
                        r['client_id'] = cn
                        #raise Exception('foo')
                        result.append(r)
                    else:
                        for r2 in r:
                            r2['client_id'] = cn
                            result.append(r2)
            elif pmeta['handler'] == self.noop_handler:
                # Silently stop reading
                #print "No handler for %s in SV_CLIENT"%pname
                break
            else:
                print("Oh no! Don't have a handler for %s in SV_CLIENT"%pname)
                break
            cnt += 1
        #print "Exiting: %s elements"%len(result)
        if len(result) == 0:
            #print "exiting, actually"
            return None
        return result
        #print "Found %s messages in SV_CLIENT for %s"%(cnt, cn)

    def handle_damage(self, p, f):
        return self.get_fmt(f, "iiiiii", 'target', 'shooter', 'gun', 'damage', 'armour', 'health', type='damage', killed=False, gib=(p=='SV_GIBDAMAGE'))

    def handle_points(self, p, f):
        count = self.getint(f)
        r = {
            'type': 'points',
            'points': {}
        }
        if count > 0:
            for i in range(count):
                cn = self.getint(f)
                score = self.getint(f)
                #print "%s has score %s"%(cn,score)
                r['points'][cn] = score
        else:
            nmedals = self.getint(f)
            if medals > 0:
                for i in range(nmedals):
                    cn = self.getint(f)
                    mtype = self.getint(f)
                    mitem = self.getint(f)
        return r

    def handle_died(self, p, f):
        return self.get_fmt(f, "iiii", 'target', 'shooter', 'frags', 'gun', type='damage', killed=True, gib=(p == 'SV_GIBDIED'))

    def handle_weapchange(self, p, f):
        newgun = self.getint(f)
        #print "New gun is %s"%GUN_NAMES[newgun]
        return {
            'type': 'weapon_change',
            'newgun': newgun
        }

    def handle_spawn(self, p, f):
        lifeseq = self.getint(f)
        health = self.getint(f)
        armour = self.getint(f)
        gun = self.getint(f)
        for i in range(NUMGUNS):
            ammo = self.getint(f)
        for i in range(NUMGUNS):
            mag = self.getint(f)

    def handle_thrownade(self, p, f):
        return self.get_fmt(f, "iiiiiii", 'x', 'y', 'z', 'vx', 'vy', 'vz', 'tm', type='thrownade')

    def handle_arenawin(self, p, f):
        alive_cn = self.getint(f)

    def handle_timeup(self, p, f):
        millis = self.getint(f)
        limit = self.getint(f)

    def handle_reload(self, p, f):
        return self.get_fmt(f, "ii", 'cn', 'gun', type='reload')

    def handle_mapident(self, p, f):
        self.getint(f)
        self.getint(f)

    def handle_initclient(self, p, f):
        return self.get_fmt(f, "isiii", 'cn', 'name', 'skin1', 'skin2', 'team', type='newplayer')

    def handle_itemacc(self, p, f):
        i = self.getint(f)
        cn = self.getint(f)
        return {
            'type': 'itemacc',
            'cn': cn,
            'item': i
        }

    def handle_itemspawn(self, p, f):
        i = self.getint(f)
        return {
            'type': 'itemspawn',
            'item': i
        }

    def handle_clientping(self, p, f):
        self.getint(f)

    # For things we know we don't care about
    def noop_handler(self, p, f):
        pass

    def handlepacket(self, millis, chan, f):
        ptype = self.getint(f)
        #print ptype
        result = []
        pname, pmeta = self._get_packet(ptype)
        if pmeta['handler'] is not None:
            #print "Handling packet %s"%pname
            r = pmeta['handler'](pname, f)
            if r is not None:
                if pname == 'SV_CLIENT':
                    for r2 in r:
                        if r2 is not None:
                            r2['gametime'] = millis[0]
                            result.append(r2)
                else:
                    r['gametime'] = millis[0]
                    result.append(r)
        else:
            print("Unhandled %s"%pname)
        return result

    def consumeFile(self, filename):
        f = gzip.GzipFile(filename, "rb")
        self.readheader(f)
        result = []

        # Now loop, eating packets
        cnt = 0
        next_millis = (0,)#self.get("i", f)
        while True:
            stamp, data = self.readdemo(f)
            #print(len(data))
            r = self.handlepacket(next_millis, stamp[0], io.BytesIO(data))
            if r is not None:
                lr = list(r)
                for rv in lr:
                    result.append(rv)
            cnt += 1
            try:
                next_millis = self.get("i", f)
            except Exception as e:
                print(e)
                break

        print("Got %s packets"%cnt)
        print("Finished successfully")
        return result

if __name__ == '__main__':
    import sys
    acdr = AssaultCubeDmoReader()
    if len(sys.argv) > 1:
        lr = acdr.consumeFile(sys.argv[1])
    else:
        lr = acdr.consumeFile("demos/20161015_2314_local_ac_ingress_8min_KTF.dmo")
    for r in lr:
        print(r)
    pass
