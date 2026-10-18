import sys, json
from PIL import Image, ImageDraw
W,H=72,40
def blank(): return [['.']*W for _ in range(H)]
def put(g,x0,y0,rows,ch=None):
    for y,r in enumerate(rows):
        for x,c in enumerate(r):
            if c!='.' and 0<=y0+y<H and 0<=x0+x<W: g[y0+y][x0+x]= ch or c
def clear(g,x0,y0,w,h):
    for y in range(y0,y0+h):
        for x in range(x0,x0+w):
            if 0<=y<H and 0<=x<W: g[y][x]='.'
BALL=['..ooo..','.oo+oo.','o+o+o+o','oo+++oo','o+o+o+o','.oo+oo.','..ooo..']
STRIKER=['#.......#','#..###..#','.#.###.#.','..#.#.#..','...###...','...###...','...###...','...#.#...','..#...#..','..#...#..','.#.....#.']
KEEPER=['...............###.','..............#####','#.............#####','##...#######..###..','.##.##########.....','..###....###.......','..........##.......']
def scene(n):
    g=blank()
    for x in range(W): g[37][x]='#'
    # net mesh inside the goal mouth
    for y in range(10,37):
        for x in range(16,56):
            if (x+y)%4==0 or (x-y)%4==0: g[y][x]='+'
    # posts and crossbar, two dots thick
    for y in range(8,37):
        for x in (14,15,56,57): g[y][x]='#'
    for x in range(14,58):
        for y in (8,9): g[y][x]='#'
    spots=[(46,11),(19,12),(32,24)][:n]
    # the newest ball's flight: a dotted arc from the striker's boot
    bx,by=spots[-1]; sx,sy=61,36
    for t in [i/14 for i in range(1,13)]:
        x=round(sx+(bx+3-sx)*t); y=round(sy+(by+3-sy)*t-10*t*(1-t)*2)
        if 0<=y<H and 0<=x<W and (16<=x<56 or x>57): g[y][x]='*'
    for bx,by in spots: clear(g,bx-1,by-1,9,9); put(g,bx,by,BALL)
    clear(g,60,25,11,12); put(g,61,26,STRIKER)
    return [''.join(r) for r in g]
def png(rows,path,s=8):
    im=Image.new('RGB',(W*s,H*s),(7,19,12)); d=ImageDraw.Draw(im)
    col={'#':(92,240,154),'+':(52,140,92),'o':(240,255,245),'*':(200,255,220)}
    for y,r in enumerate(rows):
        for x,c in enumerate(r):
            cc=col.get(c,(18,40,26)) if c!='-' else (18,40,26); rad=s*0.4
            d.ellipse((x*s+s/2-rad,y*s+s/2-rad,x*s+s/2+rad,y*s+s/2+rad),fill=cc)
    im.save(path)
if __name__=='__main__':
    for n in (1,2,3): png(scene(n),f'scene{n}.png')
    json.dump({n:scene(n) for n in (1,2,3)},open('scenes.json','w'))
