Various AssaultCube DMO File Utilities
======================================

Welcome to my assorted pack of DMO file utilities for the game AssaultCube! I use them to help run AC LAN parties, hopefully you find them (or some subset of them) useful as well.

Their current development state is largely "they do what I need them to," but if you need/want them to do something else then feel free to open an issue (or submit a PR).

All of the code is written for Python 3.5, and much of it won't work on Python 2.

DmoParser.py
------------

This is a Python module that you can use to parse .DMO files.

You can call it from Python code, like so:

```python
acdr = AssaultCubeDmoReader()
lr = acdr.consumeFile('example.dmo')
for r in lr:
    print(r)
```

The AssaultCubeDmoReader converts the file into a sequence of dictionaries, which look like:

```
{'shooting': 0, 'yaw': 149.0625, 'x': 2593, 'scoping': 0, 'y': 1290, 'pitch': -17.007874015748033, 'type': 'position', 'gametime': 489994, 'cn': 1, 'z': -16}
```

Each one has a field 'type' that identifies what type of packet it is.

You can convert an entire file from the command line, like this:

```
$ python3 DmoParser.py ../demos/20161227_2006_local_ac_rattrap_8min_LSS.dmo > foo.json
```

maputils.py
-----------

This is just a list of the default maps for AC 1.2.0.2, and whether or not they support Capture The Flag (CTF) (i.e. whether or not they have flags defined).

heatmap.py
----------

This is the start of a heatmap generator for DMO files. It requires the Pillow (PIL) Python library.

It parses a DMO file and generates an image with points where the selected events occur. You can currently select between two different events to plot: position and death.

To run it, you must pass a DMO filename, an image filename, and which event you want to draw:

```
$ python3 heatmap.py ../demos/20161227_2006_local_ac_rattrap_8min_LSS.dmo tmp.png position
```

to show player positions over the course of the game, or

```
$ python3 heatmap.py ../demos/20161227_2006_local_ac_rattrap_8min_LSS.dmo tmp.png death
```

To show where players died in the game.

Currently, the output image is square and doesn't include any imagery from the underlying map, so you have to manually line up the heatmap with a map image.

stats.py
--------

This file processes a bunch of DMO files and dumps statistics into a sqlite database in preparation for gen-maprot (or any other sqlite analysis).

To run it, you must specify a path to DMO files:

```
$ python3 stats.py ../demos/
```

It can take several minutes, so be patient.

It creates a sqlite database in test.db, with two tables: 'games' and 'gamestats'. 'games' contains information about every player in every game, whereas 'gamestats' contains averaged information about each game.

```
CREATE TABLE games (
  gameid text,     # A game identifier
  mapname text,
  smode int,       # The mode number
  gamelimit int,   # Game time limit, ms
  duration int,    # Actual duration of the game, ms
  playerid int,    # Connection ID of this player
  playername text, # Player name
  nkills int,      # Number of kills by this player
  npickups int,    # Number of items picked up by this player
  numshots int,    # Number of position updates during which this player was shooting
  nreloads int     # Number of times the player reloaded
);
CREATE TABLE gamestats(
  gameid TEXT,
  mapname TEXT,
  smode INT,
  gamelimit INT,
  duration INT,
  nkills,        # Average number of kills per player during the game (total kills / number of player)
  numshots,      # Average number of shots per player
  nplayers       # Total number of players in the game.
);
```

gen-maprot.py
-------------

This consumes a sqlite database and generates a map rotation with 20 maps.

It currently uses a convoluted algorithm that favors a) small maps and b) maps that have historically been played less often. It does Fancy Things to minimize the chances that the same map or gamemode will be played twice in a row.

The gamemode is chosen based on a set of probabilities specified at the top of the file ('modes' variable) combined with TEAM_PROB.

The algorithm is highly tuned for intense 3 person games and is also constantly changing.

To run it:

```
$ python3 gen-maprot.py
```

This script requires a test.db file to run. If you don't have any DMO files to populate the database with using stats, that's fine, stats.py should create an empty database and gen-maprot.py should handle that just fine (whenever there are maps without any DMO files about them, it will prioritize them so it can gather data).
