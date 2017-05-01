import gzip
import math
import random
import os.path

maps = {
    "ac_aqueous": {"ctf": True},
    "ac_arabian": {"ctf": True},
    "ac_arctic": {"ctf": False},
    "ac_arid": {"ctf": False},
    "ac_avenue": {"ctf": True},
    "ac_cavern": {"ctf": True},
    "ac_complex": {"ctf": False},
    "ac_depot": {"ctf": True},
    "ac_desert": {"ctf": False},
    "ac_desert2": {"ctf": True},
    "ac_desert3": {"ctf": True},
    "ac_douze": {"ctf": False},
    "ac_edifice": {"ctf": True},
    "ac_elevation": {"ctf": True},
    "ac_gothic": {"ctf": True},
    "ac_iceroad": {"ctf": True},
    "ac_industrial": {"ctf": True},
    "ac_ingress": {"ctf": True},
    "ac_keller": {"ctf": True},
    "ac_lainio": {"ctf": True},
    "ac_mines": {"ctf": True},
    "ac_outpost": {"ctf": True},
    "ac_power": {"ctf": True},
    "ac_rattrap": {"ctf": False},
    "ac_scaffold": {"ctf": False},
    "ac_shine": {"ctf": True},
    "ac_snow": {"ctf": False},
    "ac_stellar": {"ctf": True},
    "ac_sunset": {"ctf": True},
    "ac_swamp": {"ctf": True},
    "ac_terros": {"ctf": True},
    "ac_toxic": {"ctf": False},
    "ac_urban": {"ctf": False},
    "ac_venison": {"ctf": True},
    "ac_wasteland": {"ctf": False},
    "ac_werk": {"ctf": True},
}

# Figure out the size of each map
totsize = 0
for mapname in maps.keys():
    mapfile = os.path.abspath("./packages/maps/official/%s.cgz"%mapname)
    size = len(gzip.GzipFile(mapfile).read())
    #maps[mapname]["size"] = os.path.getsize(mapfile)
    maps[mapname]["size"] = size
    totsize += maps[mapname]["size"]
