from PIL import Image, ImageDraw
import DmoParser

NPIXELS = 512

def lerp(x0,y0, x1,y1, x):
    return float(float(y1)-y0) / float(float(x1)-x0) * (float(x)-float(x0)) + y0

def heatmap(positions):
    # Find the limits
    xvals = [p[0] for p in positions]
    yvals = [p[1] for p in positions]
    xvals.sort()
    yvals.sort()
    minimums = [xvals[5], yvals[5]]
    maximums = [xvals[-5], yvals[-5]]

    # Build the heatmap
    grid = []
    for x in range(NPIXELS):
        col = []
        for y in range(NPIXELS):
            col.append(0)
            pass
        grid.append(col)

    # Fill in the grid
    for p in positions:
        x = int(lerp(minimums[0], 0, maximums[0], NPIXELS-1, p[0]))
        y = int(lerp(minimums[1], 0, maximums[1], NPIXELS-1, p[1]))
        #print(x,y,p)
        if x < 0 or y < 0 or x >= NPIXELS or y >= NPIXELS:
            continue #print(p)
        grid[x][y] += 1
    most = max([max(col) for col in grid])

    # Create an image
    im = Image.new('L', (NPIXELS, NPIXELS))
    #d = ImageDraw.Draw(im)
    for x in range(NPIXELS):
        for y in range(NPIXELS):
            v = float(grid[x][y]) / most
            im.putpixel((x,y), int(pow(v, 0.25)*255))
            #d.ellipse([x-BRUSH_SIZE,y-BRUSH_SIZE, x+BRUSH_SIZE,y+BRUSH_SIZE], fill=(255,255,255,int(float(grid[x][y]) * 255 / most)))
            pass
    #print(len(positions))
    return im

class PlayerTracker:
    def __init__(self):
        self.players = {}
        pass

    def consume(self, r):
        if r['type'] == 'welcome':
            for cid,player in r['playernames'].items():
                self.players[cid] = (0,0)
            pass
        if r['type'] == 'position':
            self.players[r['cn']] = (r['x'], r['y'])
        pass

    def getPlayerPos(self, cid):
        return self.players[cid]

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 3:
        acdr = DmoParser.AssaultCubeDmoReader()
        lr = acdr.consumeFile(sys.argv[1])
        pt = PlayerTracker()
        positions = []
        for r in lr:
            pt.consume(r)
            if sys.argv[3] == 'position':
                if r['type'] == 'position' and r['gametime'] < 480000:
                    positions.append(pt.getPlayerPos(r['cn']))
            elif sys.argv[3] == 'death':
                if r['type'] == 'damage' and r['killed'] and r['gametime'] < 480000:
                    #positions.append((r['x'], r['y']))
                    positions.append(pt.getPlayerPos(r['target']))
            else:
                print("Unknown heatmap type '%s'"%sys.argv[3])
            pass
        heatmap(positions).save(sys.argv[2])
    else:
        print("I need a DMO file and a PNG file and a heatmap type!")
        print("Usage: %s <DMO file> <output PNG file> <heatmap type>")
        print("Heatmap type can be one of: position or death")
