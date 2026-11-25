import math, random, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 38.191
N = round(DUR * FPS)
INK = (52, 28, 64)
GY = 1500.0           # ground line (world y)
ROCK_X = 3400.0
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fc = {}
def font(px):
    px = max(6, int(px))
    if px not in _fc:
        _fc[px] = ImageFont.truetype(FONT, px)
    return _fc[px]

def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def sm(x):
    x = clamp(x); return x * x * (3 - 2 * x)
def smr(x):
    x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)
def lerp(a, b, u): return a + (b - a) * u
def mixc(a, b, u): return tuple(int(lerp(a[i], b[i], u)) for i in range(3))

# ---------------------------------------------------------------- timeline
# speech segments (s) detected in the voice: aligned to the 11 script sentences
SEG = [(0.0,3.51),(4.10,6.78),(7.33,10.83),(11.32,12.73),(13.18,16.06),(16.64,20.46),
       (21.10,21.72),(21.97,25.06),(25.63,26.59),(26.94,29.04),(29.55,31.18),
       (31.71,32.87),(33.19,34.39),(34.93,38.19)]

def xh(t):
    if t < 21.4: return 1500 + 70 * t
    if t < 33.3: return 1500 + 70 * 21.4
    u = t - 33.3
    return 1500 + 70 * 21.4 + 150 * (u - 0.3 * (1 - math.exp(-u / 0.3)) * 0 ) * 1.0

CAM = [(0.0,-430,1207,.85),(3.6,-340,1237,.95),(4.6,-30,1300,1.25),(7.0,20,1300,1.32),
       (7.8,230,1240,1.0),(10.8,300,1240,1.05),(11.3,89,640,1.6),(12.7,70,640,1.7),
       (13.2,-1350,1230,1.1),(16.0,-1320,1230,1.25),(16.64,-650,1330,1.0),(18.8,-700,1330,.95),
       (19.1,-1200,1250,.85),(20.9,-1200,1250,.85),(21.35,100,700,.55),(22.6,330,1150,.9),
       (25.0,330,1150,.95),(25.63,250,1200,1.2),(29.0,250,1220,1.25),(29.55,150,1150,1.0),
       (31.3,170,1130,1.0),(31.7,400,1100,.75),(33.0,360,1130,.72),(34.4,360,1130,.7),
       (34.93,70,1310,1.55),(38.2,95,1290,1.8)]

def camera(t):
    cx, cy, z = _cam(t)
    z *= 1.12
    return cx, cy - 0.09 * H / z, z

def _cam(t):
    if t <= CAM[0][0]: k = CAM[0]; return xh(t) + k[1], k[2], k[3]
    for i in range(len(CAM) - 1):
        a, b = CAM[i], CAM[i + 1]
        if a[0] <= t <= b[0]:
            u = smr((t - a[0]) / (b[0] - a[0]))
            return xh(t) + lerp(a[1], b[1], u), lerp(a[2], b[2], u), lerp(a[3], b[3], u)
    k = CAM[-1]; return xh(t) + k[1], k[2], k[3]

def shake(t):
    a = 0.0
    if 22.05 < t < 22.8: a = 16 * (1 - (t - 22.05) / 0.75)
    if 32.9 < t < 33.9: a = 11 * (1 - (t - 32.9) / 1.0)
    if a <= 0: return 0, 0
    return a * math.sin(t * 95), a * 0.7 * math.cos(t * 83)

# ---------------------------------------------------------------- context
class Ctx:
    def __init__(self, img, cx, cy, z, SS, sh=(0, 0)):
        self.img, self.d = img, ImageDraw.Draw(img)
        self.cx, self.cy, self.z, self.SS, self.sh = cx, cy, z, SS, sh
    def pt(self, x, y, f=1.0):
        s = self.SS
        return ((x - self.cx * f) * self.z + W / 2 + self.sh[0]) * s, ((y - self.cy) * self.z + H / 2 + self.sh[1]) * s
    def lw(self, w):
        return max(1, int(round(w * self.z * self.SS)))
    def poly(self, pts, fill, ow=8, out=INK, f=1.0):
        P = [self.pt(x, y, f) for x, y in pts]
        self.d.polygon(P, fill=fill)
        if ow: self.d.line(P + [P[0]], fill=out, width=max(2, self.lw(ow)), joint="curve")
    def ell(self, x, y, rx, ry, fill, ow=8, f=1.0, out=INK):
        a = self.pt(x - rx, y - ry, f); b = self.pt(x + rx, y + ry, f)
        self.d.ellipse([a, b], fill=fill, outline=out if ow else None, width=max(2, self.lw(ow)) if ow else 0)
    def line(self, pts, w, col, f=1.0):
        P = [self.pt(x, y, f) for x, y in pts]
        self.d.line(P, fill=col, width=max(1, self.lw(w)), joint="curve")
        r = max(1, self.lw(w)) / 2
        for p in (P[0], P[-1]):
            self.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
    def text(self, x, y, s, px, col, anchor="mm"):
        p = self.pt(x, y)
        self.d.text(p, s, font=font(px * self.z * self.SS), fill=col, anchor=anchor)

def ellpts(cx, cy, rx, ry, n=28, a0=0, a1=360):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def rotp(pts, ang, px, py):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(px + (x - px) * c - (y - py) * s, py + (x - px) * s + (y - py) * c) for x, y in pts]

# ---------------------------------------------------------------- background
_grad = {}
def sky(SS):
    if SS not in _grad:
        h = int(H * SS); w = int(W * SS)
        top = np.array([36, 78, 196], float); mid = np.array([104, 196, 234], float); low = np.array([255, 205, 188], float)
        v = np.linspace(0, 1, h)[:, None]
        col = np.where(v < .55, top + (mid - top) * (v / .55), mid + (low - mid) * ((v - .55) / .45))
        arr = np.repeat(col[:, None, :], w, axis=1)
        yy_, xx_ = np.mgrid[0:h, 0:w]
        r2 = ((xx_ - 800 * SS) ** 2 + (yy_ - 470 * SS) ** 2) / (SS * SS)
        glow = np.exp(-r2 / (2 * 230 ** 2))[:, :, None] * np.array([255, 190, 110]) * 0.55
        arr = arr * (1 - 0.5 * np.exp(-r2 / (2 * 230 ** 2))[:, :, None]) + glow
        disc = (r2 < 70 ** 2)[:, :, None]
        arr = np.where(disc, np.array([255, 244, 205]), arr)
        _grad[SS] = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return _grad[SS].copy()

def ridge(x, seed, amp, base):
    r = random.Random(seed)
    y = base
    for k in range(5):
        f = 0.0012 * (k + 1) * 1.7; p = r.random() * 6.28
        y -= amp * (0.55 ** k) * (0.5 + 0.5 * math.sin(f * x + p))
    return y

def mountains(c, t):
    layers = [(0.10, 11, 900, 1330, (150, 150, 222), (255, 244, 250)),
              (0.25, 23, 700, 1400, (120, 112, 200), (252, 240, 250)),
              (0.45, 37, 520, 1470, (92, 86, 176), (248, 238, 250))]
    for f, seed, amp, base, col, snow in layers:
        x0 = c.cx * f - (W / 2) / c.z - 200; x1 = c.cx * f + (W / 2) / c.z + 200
        xs = np.arange(math.floor(x0 / 60) * 60, x1 + 60, 60)
        top = [(x, ridge(x, seed, amp, base)) for x in xs]
        poly = top + [(xs[-1], 1700), (xs[0], 1700)]
        P = [c.pt(x, y, f) for x, y in poly]
        c.d.polygon(P, fill=col)
        c.d.line([c.pt(x, y, f) for x, y in top], fill=INK, width=max(2, c.lw(6)), joint="curve")
        # snow caps: where ridge is high
        lim = base - amp * 0.50
        for i in range(len(top) - 1):
            (xa, ya), (xb, yb) = top[i], top[i + 1]
            if ya < lim or yb < lim:
                cap = [(xa, ya), (xb, yb), (xb, min(yb + 60 + 25 * math.sin(xb * .05), yb + 110)), ((xa + xb) / 2, yb + 38), (xa, min(ya + 100, ya + 60 + 25 * math.sin(xa * .05)))]
                c.d.polygon([c.pt(x, y, f) for x, y in cap], fill=snow)

def pines(c):
    f = 0.8
    x0 = c.cx * f - (W / 2) / c.z - 200; x1 = c.cx * f + (W / 2) / c.z + 200
    k0 = int(x0 // 430)
    for k in range(k0, int(x1 // 430) + 2):
        r = random.Random(k * 7 + 3)
        x = k * 430 + r.random() * 200; s = 0.8 + r.random() * 0.7
        gy = GY - 6
        c.line([(x, gy), (x, gy - 60 * s)], 18 * s, (90, 62, 48), f)
        for j in range(3):
            w = (150 - j * 36) * s; y = gy - 40 * s - j * 85 * s
            c.poly([(x - w, y), (x + w, y), (x, y - 120 * s)], (28, 132, 112), 6, INK, f)
            c.poly([(x - w * .55, y - 52 * s), (x + w * .55, y - 52 * s), (x, y - 120 * s)], (236, 242, 250), 0, INK, f)

def ground(c, t):
    ys = c.pt(0, GY)[1]
    if ys < H * c.SS: c.d.rectangle([0, ys, W * c.SS, H * c.SS], fill=(238, 244, 255))
    # snow bumps
    xs = np.arange(math.floor((c.cx - 900 / c.z) / 70) * 70, c.cx + 900 / c.z, 70)
    pts = [(x, GY + 6 + 10 * math.sin(x * .013)) for x in xs]
    c.d.line([c.pt(x, y) for x, y in pts], fill=INK, width=max(2, c.lw(8)), joint="curve")
    # trail
    tr = [(x, GY + 70 + 8 * math.sin(x * .02)) for x in xs]
    c.d.polygon([c.pt(x, y) for x, y in tr] + [c.pt(xs[-1], GY + 190), c.pt(xs[0], GY + 190)], fill=(204, 188, 176))
    c.d.line([c.pt(x, y) for x, y in tr], fill=INK, width=max(2, c.lw(6)))
    r = random.Random(5)
    for x in range(int(xs[0]), int(xs[-1]), 130):
        rr = random.Random(x)
        c.ell(x + rr.random() * 60, GY + 120 + rr.random() * 50, 18 + rr.random() * 20, 7, (176, 160, 150), 0)

def snow(c, t, amount):
    n = int(amount)
    r = random.Random(99)
    for i in range(n):
        x0, y0, sp, sz = r.random(), r.random(), 0.12 + r.random() * 0.25, 4 + r.random() * 8
        sx = ((x0 + t * (0.05 + sp * .3) + math.sin(t * 1.5 + i) * .01) % 1.0) * W
        sy = ((y0 + t * sp) % 1.0) * H
        rr = sz * c.SS
        p = (sx * c.SS, sy * c.SS)
        c.d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=(255, 255, 255))

# ---------------------------------------------------------------- characters
def face_params(face):
    return {"calm": (0, 0, "line"), "smug": (-3, 0, "smile"), "worried": (-10, 0, "frown"),
            "shock": (-14, 0, "o"), "think": (6, 0, "line"), "grin": (0, 0, "grin"),
            "laugh": (-6, 0, "laugh"), "det": (5, 0, "smile")}[face]

def draw_person(c, x, gy, s, t, face="calm", skin=(206, 150, 110), tunic=(150, 40, 48), cape=(100, 40, 120),
                helmet=(176, 120, 60), crest=None, beard=None, pose=None, walk=0.0, look=1.0,
                banner=False, jar=None, laugh=0.0, shiver=0.0, wink=False, spear=False, ph=0.0, sweat=False):
    if pose is None: pose = {"R": (70, -135), "L": (-60, -135), "jar": 0.0}
    bob = abs(math.sin(t * 7 + ph)) * 8 * walk + math.sin(t * 2.3 + ph) * 2
    jx = math.sin(t * 60 + ph) * 4 * shiver
    X = lambda lx: x + jx + lx * s
    Y = lambda ly: gy + (ly - bob) * s
    P = lambda pts: [(X(a), Y(b)) for a, b in pts]
    sw = math.sin(t * 7 + ph) * 26 * walk
    # cape (behind)
    flut = math.sin(t * 5 + ph) * 12
    c.poly(P([(-54, -228), (56, -228), (92 + flut, -70), (-92 + flut, -70)]), cape, 8)
    # legs
    for sgn in (-1, 1):
        fx = sgn * 30 + sgn * sw * 0.5
        c.poly(P([(fx - 17, -100), (fx + 17, -100), (fx + 19, -8), (fx - 19, -8)]), (110, 70, 60), 7)
        c.ell(X(fx + sgn * 4), Y(-6), 30 * s, 13 * s, (84, 54, 48), 7)
    # tunic
    c.poly(P([(-60, -100), (60, -100), (66, -150), (54, -232), (-54, -232), (-66, -150)]), tunic, 8)
    c.line([(X(-62), Y(-150)), (X(62), Y(-150))], 14 * s, (232, 184, 70))
    c.poly(P([(-54, -232), (54, -232), (40, -214), (-40, -214)]), (232, 184, 70), 5)
    # pole / banner
    hands = {}
    if banner:
        px = -120
        c.line([(X(px), Y(-8)), (X(px), Y(-575))], 14 * s, (118, 82, 50))
        w1 = math.sin(t * 5) * 14 * s; w2 = math.sin(t * 5 + 1.5) * 14 * s
        cl = [(X(px), Y(-565)), (X(px - 230) + w1, Y(-560) + w1), (X(px - 215) + w2, Y(-410) + w2), (X(px), Y(-420))]
        c.poly(cl, (116, 44, 128), 8)
        c.poly([(cl[0][0], cl[0][1] + 6 * s), (cl[1][0], cl[1][1] + 6 * s), (cl[1][0], cl[1][1] + 22 * s), (cl[0][0], cl[0][1] + 22 * s)], (232, 184, 70), 0)
        c.ell((cl[0][0] + cl[2][0]) / 2 + 6 * s, (cl[0][1] + cl[2][1]) / 2 - 8 * s, 20 * s, 20 * s, (232, 184, 70), 4)
        c.text((cl[0][0] + cl[2][0]) / 2 + 6 * s, (cl[0][1] + cl[2][1]) / 2 + 38 * s, "218 a.C.", 24 * s, (244, 220, 150))
        c.ell(X(px), Y(-578), 11 * s, 11 * s, (232, 184, 70), 5)
    if spear:
        c.line([(X(-100), Y(-5)), (X(-100), Y(-420))], 9 * s, (118, 82, 50))
        c.poly(P([(-112, -420), (-100, -470), (-88, -420)]), (200, 205, 215), 5)
    # arms
    def arm(sh, hand, col):
        mx, my = (sh[0] + hand[0]) / 2, (sh[1] + hand[1]) / 2 + 20
        pts = [(X(sh[0]), Y(sh[1])), (X(mx), Y(my)), (X(hand[0]), Y(hand[1]))]
        c.line(pts, 34 * s, INK); c.line(pts, 22 * s, col)
        c.ell(X(hand[0]), Y(hand[1]), 15 * s, 15 * s, skin, 6)
    armc = tunic
    arm((-56, -214), pose["L"] if not banner else (-118, -205), armc)
    # jar (in right hand)
    rh = pose["R"]
    arm((56, -214), rh, armc)
    hands["R"] = (X(rh[0]), Y(rh[1]))
    if jar is not None:
        draw_jar(c, X(rh[0]), Y(rh[1]), s, jar)
    # head
    hc = (0, -295)
    tilt = laugh * 14 * math.sin(t * 14) if laugh else 0
    HS = 1.22
    def H_(pts): return [(X(a * HS), Y(-215 + (b + 215) * HS)) for a, b in rotp(pts, tilt, 0, -215)]
    he = H_(ellpts(0, -295, 78, 92, 30))
    c.poly(he, skin, 8)
    # helmet
    if helmet:
        cap = ellpts(0, -318, 84, 74, 22, 180, 360)
        c.poly(H_(cap + [(84, -318), (-84, -318)]), helmet, 8)
        c.poly(H_([(-86, -326), (86, -326), (86, -310), (-86, -310)]), (232, 184, 70), 5)
        if crest == "plume":
            c.poly(H_([(-14, -388), (10, -470), (62, -450), (70, -400), (36, -420), (22, -388)]), (190, 40, 50), 6)
        elif crest == "roman":
            c.poly(H_([(-70, -380), (-20, -430), (50, -430), (80, -380), (50, -400), (-20, -400)]), (190, 40, 50), 6)
    # beard
    if beard:
        bd = ellpts(0, -268, 66, 56, 20, 0, 180)
        c.poly(H_(bd), beard, 7)
    # eyes
    eb, _, mouth = face_params(face)
    for sgn in (-1, 1):
        ex = sgn * 30
        wk = wink and sgn == 1
        if wk:
            c.line(H_([(ex - 15, -300), (ex + 15, -300)]), 7 * s, INK)
        else:
            c.poly(H_(ellpts(ex, -300, 17, 22, 14)), (255, 255, 255), 3)
            px_ = ex + look * 8 + math.sin(t * 1.3) * 1.5
            c.poly(H_(ellpts(px_, -297, 8, 10, 10)), INK, 0)
        slope = eb * sgn * -0.0 + (eb)
        inner = -sgn * 14; outer = sgn * 14
        # worried: inner up (negative y); determined: inner down
        yi = -330 + (eb * 0.9); yo = -330 - (eb * 0.2)
        c.line(H_([(ex + inner, yi), (ex + outer, yo)]), 8 * s, INK)
    if sweat:
        for k in range(2):
            u = (t * 1.1 + ph + k * .5) % 1.0
            dx_, dy_ = (84 + k * 14, -338 + u * 46 + k * 10)
            pp = H_([(dx_, dy_ - 18), (dx_ + 10, dy_ + 2), (dx_, dy_ + 10), (dx_ - 10, dy_ + 2)])
            c.poly(pp, (130, 200, 255), 4)
    # nose
    c.poly(H_(ellpts(look * 6, -280, 9, 12, 10)), mixc(skin, (140, 90, 70), .35), 4)
    # mouth
    my = -250 if not beard else -254
    mpts = {"line": [(-14, my), (14, my)], "smile": [(-18, my - 4), (0, my + 8), (18, my - 4)],
            "frown": [(-14, my + 6), (0, my - 2), (14, my + 6)], "o": None, "grin": None, "laugh": None}[mouth]
    if mpts: c.line(H_(mpts), 6 * s, INK)
    elif mouth == "o": c.poly(H_(ellpts(0, my + 2, 10, 13, 12)), (110, 30, 50), 5)
    else:
        op = 14 if mouth == "grin" else 20 + 8 * math.sin(t * 22)
        c.poly(H_(ellpts(0, my, 24, op, 14, 0, 180) ), (255, 255, 255) if mouth == "grin" else (120, 30, 50), 5)
        if mouth == "laugh": c.poly(H_(ellpts(0, my + op * .65, 14, 8, 8, 180, 360)), (230, 110, 120), 0)
    return hands

def draw_jar(c, hx, hy, s, tilt):
    ang = tilt
    body = ellpts(0, -52, 36, 48, 20)
    neck = [(-14, -92), (14, -92), (18, -130), (-18, -130)]
    lip = [(-22, -130), (22, -130), (22, -142), (-22, -142)]
    hl = ellpts(-34, -88, 14, 20, 10, 90, 270); hr = ellpts(34, -88, 14, 20, 10, -90, 90)
    def T(pts): return [(hx + (px) * s * 1.25, hy + (py - 8) * s * 1.25) for px, py in rotp(pts, ang, 0, 0)]
    for h_ in (hl, hr): c.poly(T(h_), (176, 84, 52), 5)
    c.poly(T(body), (200, 100, 62), 7)
    c.poly(T(neck), (200, 100, 62), 6)
    c.poly(T(lip), (176, 84, 52), 5)
    c.poly(T([(-34, -70), (34, -70), (34, -48), (-34, -48)]), (236, 220, 170), 3)
    if abs(ang) < 12:
        c.text(hx, hy - 62 * s * 1.25, "VINAGRE", 11.5 * s * 1.25, (90, 40, 40))

def elephant(c, x, gy, t, tilt=0.0, face="calm", ph=0.0, walk=1.0):
    ph = ph
    piv = (150, 0)
    def tf(pts):
        r = rotp(pts, tilt, *piv) if tilt else pts
        return [(x + a, gy + b) for a, b in r]
    body_c = (142, 146, 170); dark = (112, 116, 140); ear_c = (176, 166, 190)
    bobv = math.sin(t * 5 + ph) * 5 * walk
    def sh(pts): return [(a, b - bobv) for a, b in pts]
    # back legs
    for i, lx in enumerate((-170, 90)):
        sw = math.sin(t * 5 + ph + i * 2.4) * 22 * walk
        c.poly(tf(sh([(lx - 36 + sw, -150), (lx + 36 + sw, -150), (lx + 40 + sw, -6), (lx - 40 + sw, -6)])), dark, 8)
        c.poly(tf(ellpts(lx + sw, -6, 46, 15, 14)), (96, 98, 120), 7)
    c.poly(tf(sh(ellpts(0, -215, 275, 150, 36))), body_c, 9)
    # blanket
    c.poly(tf(sh([(-150, -352), (70, -362), (140, -250), (-190, -240)])), (170, 44, 54), 8)
    c.line(tf(sh([(-190, -240), (140, -250)])), 12, (232, 184, 70))
    # front legs
    for i, lx in enumerate((-90, 150)):
        sw = math.sin(t * 5 + ph + 1.2 + i * 2.4) * 22 * walk
        c.poly(tf(sh([(lx - 38 + sw, -150), (lx + 38 + sw, -150), (lx + 42 + sw, -6), (lx - 42 + sw, -6)])), body_c, 8)
        c.poly(tf(ellpts(lx + sw, -6, 48, 15, 14)), (96, 98, 120), 7)
    # head
    c.poly(tf(sh(ellpts(245, -255, 108, 118, 28))), body_c, 9)
    # trunk (chain of circles)
    sway = math.sin(t * 3 + ph) * 18
    up = 1.0 if face == "shock" else 0.0
    tr = []
    for k in range(9):
        u = k / 8
        px = 318 + 70 * u + sway * u * u * (1 - up)
        py = -230 + (150 + up * -200) * u + (60 * up * math.sin(u * 3.1)) * 0
        if up: px = 318 + 70 * math.sin(u * 2.0) + 20 * u; py = -230 - 190 * u * 0.95 + 40 * u * u
        tr.append((px, py))
    ps = tf(sh(tr))
    for k, (px, py) in enumerate(ps):
        r = (40 - 17 * k / 8) * c.z * c.SS
        q = c.pt(px, py); c.d.ellipse([q[0] - r - c.lw(8) * .5, q[1] - r - c.lw(8) * .5, q[0] + r + c.lw(8) * .5, q[1] + r + c.lw(8) * .5], fill=INK)
    for k, (px, py) in enumerate(ps):
        r = (40 - 17 * k / 8) * c.z * c.SS
        q = c.pt(px, py); c.d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=body_c)
    # tusks
    for dy in (-12, 22):
        tk = [(300, -180 + dy), (360, -150 + dy), (415, -176 + dy), (430, -222 + dy)]
        pp = tf(sh(tk)); c.line(pp, 22, INK); c.line(pp, 12, (248, 244, 230))
    # ear
    flap = math.sin(t * 4 + ph) * 8
    c.poly(tf(sh(ellpts(190 + flap * .3, -255, 66 + flap, 104, 24))), ear_c, 8)
    # eye + brows
    ex, ey = 292, -292
    c.poly(tf(sh(ellpts(ex, ey, 15, 18, 12))), (255, 255, 255), 5)
    c.poly(tf(sh(ellpts(ex + 5, ey + 2, 7, 9, 10))), INK, 0)
    if face in ("worried", "shock"):
        c.line(tf(sh([(ex - 22, ey - 40), (ex + 18, ey - 26)])), 9, INK)
    # tail
    tw = math.sin(t * 4 + ph) * 14
    c.line(tf(sh([(-270, -250), (-310 + tw, -190), (-300 + tw * 1.5, -110)])), 12, INK)
    c.line(tf(sh([(-270, -250), (-310 + tw, -190), (-300 + tw * 1.5, -110)])), 7, dark)

# ---------------------------------------------------------------- set pieces
def cliff(c, t):
    pts = [(2000, GY), (2040, 1200), (2080, 880), (2190, 810), (2420, 800), (2640, 812), (2720, 900), (2760, 1250), (2800, GY)]
    c.poly(pts, (150, 118, 110), 9)
    c.poly([(2060, 890), (2190, 818), (2420, 808), (2640, 820), (2710, 900), (2700, 930), (2400, 880), (2100, 940)], (240, 244, 252), 6)
    for (a, b, w, h) in ((2150, 1080, 90, 38), (2400, 1160, 120, 44), (2600, 1040, 70, 30)):
        c.ell(a, b, w, h, (130, 100, 98), 0)

def romans(c, t):
    for i, x in enumerate((2200, 2390, 2580)):
        lau = 1.0 if 11.3 <= t <= 13.1 else 0.0
        draw_person(c, x, 812, 0.8, t, face="laugh" if lau else "smug", skin=(222, 170, 130), tunic=(180, 48, 52),
                    cape=(150, 36, 40), helmet=(196, 200, 214), crest="roman", pose={"R": (95, -150), "L": (-85, -150)} if lau else
                    {"R": (70, -135), "L": (-70, -135)}, laugh=lau, ph=i * 1.7, look=-1.0, walk=0.0)
        if lau:
            pass

def rock_pts():
    L = [(0, 0), (-80, 0), (-250, -10), (-330, -120), (-350, -300), (-300, -470), (-190, -580), (-70, -640), (0, -650)]
    R = [(0, -650), (90, -640), (210, -590), (310, -470), (350, -300), (320, -130), (250, -10), (80, 0), (0, 0)]
    C = [(0, -650), (-30, -560), (25, -470), (-35, -380), (20, -290), (-30, -190), (25, -100), (0, 0)]
    return L, R, C

def rock(c, t, X0):
    if t < 21.5: return
    fall = clamp((t - 21.5) / 0.6)
    yoff = -1900 * (1 - fall * fall) if fall < 1 else 0
    if t > 22.1: yoff = -26 * max(0, math.sin((t - 22.1) * 16)) * math.exp(-(t - 22.1) * 6)
    gap = 240 * smr((t - 33.0) / 1.5)
    prog = clamp((t - 32.0) / 1.0)
    L, R, C = rock_pts()
    base = (126, 124, 140)
    def place(pts, dx, ang=0, piv=(0, 0)):
        pp = rotp(pts, ang, *piv) if ang else pts
        return [(X0 + a + dx, GY + b + yoff) for a, b in pp]
    if gap <= 0:
        full = L + R[1:]
        c.poly(place(full, 0), base, 9)
        c.poly(place([(-300, -470), (-190, -580), (-70, -640), (0, -650), (90, -640), (210, -590), (150, -520), (20, -560), (-120, -500)], 0), (168, 166, 182), 0)
        c.poly(place([(-340, -280), (-250, -10), (-80, 0), (-120, -150), (-250, -220)], 0), (98, 96, 114), 0)
        c.line(place([(-60, -400), (-20, -300), (-70, -220)], 0), 8, (98, 96, 114))
        if prog > 0:
            n = max(2, int(prog * (len(C) - 1)) + 1)
            seg = C[:n]
            if n < len(C):
                f = prog * (len(C) - 1) - (n - 1)
                a, b = C[n - 1], C[n]
                seg = C[:n] + [(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)]
            c.line(place(seg, 0), 12, INK)
            if t > 32.6:
                c.line(place(seg, 0), 5, (255, 190, 90))
    else:
        left = L + C[1:]
        right = R[:-1] + C[::-1][:-1] if False else R[:-1] + C[::-1][:-1]
        # left half: L (bottom->top) then crack top->bottom ; right half: R (top->bottom) then crack bottom->top
        lp = L[:-1] + C
        rp = R[:-1] + C[::-1]
        a = 3.5 * smr((t - 33.0) / 1.5)
        c.poly(place(lp, -gap, -a, (-80, 0)), base, 9)
        c.poly(place(rp, gap, a, (80, 0)), (118, 116, 132), 9)

def dust(c, t):
    for k in range(10):
        age = t - 22.1
        if 0 < age < 1.4:
            ang = (k / 10) * math.pi
            d = 200 + 420 * sm(age / 1.2)
            x = ROCK_X + (d if k % 2 else -d) * (0.5 + 0.5 * (k / 10))
            r = (50 + 80 * sm(age / 1.2)) * (1 - age / 1.5)
            c.ell(x, GY - 20 - 110 * sm(age / 1.0) - (k % 3) * 30, r, r * .85, (240, 233, 226), 0)
    for k in range(8):
        age = t - 33.0
        if 0 < age < 1.8:
            x = ROCK_X + (k - 3.5) * 70
            r = (24 + 60 * sm(age / 1.4)) * (1 - age / 2.0)
            c.ell(x, GY - 30 - 180 * sm(age / 1.5) - k * 14, r, r * .85, (220, 214, 208), 5)

def fire(c, t):
    g = smr((t - 26.94) / 1.2) * (1 - smr((t - 30.4) / 1.0))
    if g <= 0: return
    for i in range(6):
        fx = ROCK_X - 350 + i * 56
        h = (150 + 70 * math.sin(t * 13 + i * 2)) * g * (0.85 if i in (0, 5) else 1.15)
        w = 46 * g
        sw = math.sin(t * 9 + i) * 14
        c.poly([(fx - w, GY + 12), (fx - w * .6, GY - h * .5), (fx + sw, GY - h), (fx + w * .7, GY - h * .45), (fx + w, GY + 12)], (240, 112, 36), 7)
        c.poly([(fx - w * .5, GY + 6), (fx + sw * .5, GY - h * .6), (fx + w * .5, GY + 6)], (255, 214, 82), 0)
    c.ell(ROCK_X - 240, GY + 22, 150 * g, 22 * g, (60, 40, 40), 0)

def steam(c, t):
    for k in range(14):
        b = 29.9 + k * 0.17
        age = t - b
        if 0 < age < 2.2:
            x = ROCK_X - 260 + (k % 4) * 90 + math.sin(age * 3 + k) * 20
            y = GY - 160 - 240 * sm(age / 2.0) - (k % 3) * 40
            r = (26 + 52 * sm(age / 1.4)) * (1 - 0.6 * sm((age - 1.2) / 1.0))
            c.ell(x, y, r, r * .86, (246, 246, 252), 5)

def stream(c, t, jar_pos):
    a = smr((t - 29.9) / 0.3) * (1 - smr((t - 31.15) / 0.3))
    if a <= 0 or jar_pos is None: return
    jx, jy = jar_pos
    tx, ty = ROCK_X - 255, GY - 190
    pts = []
    for i in range(11):
        u = i / 10
        pts.append((lerp(jx + 50, tx, u), lerp(jy + 10, ty, u) + 160 * u * u * 0 + (1 - (1 - u) ** 2) * 0))
    # arc: quadratic through a control point above
    cx_, cy_ = (jx + tx) / 2 + 40, min(jy, ty) + 30
    pts = [((1 - u) ** 2 * (jx + 50) + 2 * u * (1 - u) * cx_ + u * u * tx, (1 - u) ** 2 * (jy + 10) + 2 * u * (1 - u) * cy_ + u * u * ty) for u in [i / 12 for i in range(13)]]
    n = max(2, int(len(pts) * a))
    c.line(pts[:n], 20, INK); c.line(pts[:n], 12, (238, 228, 150))

def rome(c, t):
    a = sm((t - 7.5) / 0.6) * (1 - sm((t - 10.9) / 0.4))
    if a <= 0: return
    ox = 800; oy = 430 + (1 - a) * -300 + math.sin(t * 3) * 6
    s = c.SS
    def P(x, y): return ((ox + x) * s, (oy + y) * s)
    d = c.d
    d.polygon([P(-150, 0), P(150, 0), P(0, -90)], fill=(236, 224, 200), outline=INK)
    d.line([P(-150, 0), P(150, 0), P(0, -90), P(-150, 0)], fill=INK, width=int(9 * s), joint="curve")
    for i in range(-3, 4):
        d.rectangle([P(i * 40 - 11, 8)[0], P(0, 8)[1], P(i * 40 + 11, 8)[0], P(0, 130)[1]], fill=(246, 238, 220), outline=INK, width=int(6 * s))
    d.rectangle([P(-160, 130)[0], P(0, 130)[1], P(160, 130)[0], P(0, 156)[1]], fill=(236, 224, 200), outline=INK, width=int(8 * s))
    fnt = font(34 * s)
    d.text(P(0, 200), "ROMA", font=fnt, fill=(120, 30, 40), anchor="mm")

def arrow(c, t, hand):
    a = smr((t - 8.2) / 0.8) * (1 - sm((t - 10.9) / 0.4))
    if a <= 0 or hand is None: return
    hx, hy = c.pt(*hand); s = c.SS
    tx, ty = 800 * s, 560 * s
    n = 14
    for i in range(n):
        u = i / (n - 1)
        if u > a: break
        x = lerp(hx, tx, u); y = lerp(hy, ty, u) - math.sin(u * math.pi) * 90 * s
        r = (9 + 3 * math.sin(t * 6 + i)) * s
        c.d.ellipse([x - r, y - r, x + r, y + r], fill=(236, 70, 60), outline=INK, width=int(3 * s))

def breath(c, t, x, gy, s, ph):
    if not (16.6 < t < 21.2): return
    for k in range(3):
        age = (t * 0.9 + ph + k * .33) % 1.0
        r = (8 + 16 * age) * s
        c.ell(x + 36 * s + age * 50 * s, gy - 255 * s - age * 40 * s, r, r, (250, 250, 255), 3)

# ---------------------------------------------------------------- hannibal poses
POSES = [(0.0, "march"), (7.2, "point"), (10.9, "march"), (21.4, "stand"), (29.45, "pour"), (31.4, "hips"),
         (33.3, "march"), (34.7, "jarup")]
def hand_pose(name, t):
    sw = math.sin(t * 7)
    d = {"march": {"R": (70 + sw * 18, -135 - abs(sw) * 6), "L": (-60, -135), "jar": None},
         "point": {"R": (196, -262), "L": (-60, -135), "jar": None},
         "stand": {"R": (66, -132), "L": (-60, -135), "jar": None},
         "hips": {"R": (92, -150), "L": (-60, -135), "jar": None},
         "pour": {"R": (112, -300), "L": (-60, -135), "jar": 1},
         "jarup": {"R": (120, -350), "L": (-60, -135), "jar": 0}}
    return d[name]
def pose_at(t):
    idx = max(i for i, (tk, _) in enumerate(POSES) if tk <= t)
    cur = hand_pose(POSES[idx][1], t); tk = POSES[idx][0]
    if idx == 0: return cur
    prev = hand_pose(POSES[idx - 1][1], t)
    u = sm((t - tk) / 0.35)
    return {"R": (lerp(prev["R"][0], cur["R"][0], u), lerp(prev["R"][1], cur["R"][1], u)),
            "L": (lerp(prev["L"][0], cur["L"][0], u), lerp(prev["L"][1], cur["L"][1], u)), "jar": cur["jar"]}

def hface(t):
    for lim, f in ((4.1, "calm"), (7.3, "smug"), (11.3, "det"), (13.1, "calm"), (21.4, "worried"), (25.6, "shock"), (29.5, "think"),
                   (34.9, "smug")):
        if t < lim: return f
    return "grin"

def jar_tilt(t):
    if t < 29.55: return 0.0
    up = smr((t - 29.6) / 0.5) * (1 - smr((t - 31.0) / 0.5))
    return 78 * up

WHIPS = [(10.84, 11.30), (12.74, 13.18), (16.06, 16.62), (20.9, 21.4), (25.07, 25.62), (34.40, 34.92)]
def whip(t):
    for a, b in WHIPS:
        if a <= t <= b:
            u = (t - a) / (b - a)
            return 70 * math.sin(math.pi * u)
    return 0
# ---------------------------------------------------------------- frame
def render(fi, SS=1.5):
    t = fi / FPS
    cx, cy, z = camera(t)
    img = sky(SS)
    c = Ctx(img, cx, cy, z, SS, shake(t))
    mountains(c, t)
    pines(c)
    if z > 1.05:
        from PIL import ImageFilter
        c.img = img = img.filter(ImageFilter.GaussianBlur(radius=SS * min(9, (z - 1.0) * 9)))
        c.d = ImageDraw.Draw(img)
    ground(c, t)
    if 10.85 <= t < 21.45:
        cliff(c, t)
        romans(c, t)
    h = xh(t)
    walking = 1.0 if (t < 21.4 or t > 33.3) else 0.0
    # elephants (behind soldiers)
    slip = clamp((t - 19.4) / 0.9)
    sl = 16 * math.sin(math.pi * slip) if 0 < slip < 1 else 0
    efs = "shock" if 19.3 < t < 21.5 else ("worried" if 13.1 < t < 21.5 else "calm")
    for i in (2, 1, 0):
        elephant(c, h - 1400 - i * 760, GY + 8, t, tilt=sl if i == 0 else 0, face=efs, ph=i * 1.3, walk=walking)
    # soldiers
    shiv = 1.0 if 16.6 < t < 21.2 else 0.0
    for i in range(4):
        sx = h - 300 - i * 160
        draw_person(c, sx, GY + 20, 0.75, t, face="worried" if t > 13.1 else "calm", skin=(214, 160, 120), tunic=(150, 60, 50) if i % 2 else (60, 90, 140),
                    cape=(90, 70, 60), helmet=(150, 150, 164), pose={"R": (60, -135), "L": (-60, -135)} if not shiv else {"R": (40, -160), "L": (-40, -160)},
                    walk=walking, shiver=shiv, spear=(i % 2 == 0), ph=i * 0.9, look=1.0, sweat=(13.3 < t < 21.4))
        breath(c, t, sx, GY + 20, 0.75, i * .27)
    rock(c, t, ROCK_X)
    dust(c, t)
    fire(c, t)
    steam(c, t)
    # hannibal
    ps = pose_at(t)
    jar = None
    if ps["jar"] is not None:
        jar = jar_tilt(t) if ps["jar"] == 1 else 0.0
    if t >= 34.7: jar = 0.0
    hands = draw_person(c, h, GY + 24, 1.0, t, face=hface(t), pose={"R": ps["R"], "L": ps["L"]}, walk=walking, banner=True, jar=jar,
                        beard=(60, 38, 40), crest="plume", helmet=(176, 120, 60), wink=(36.85 < t < 37.3), ph=0.0, look=1.0, sweat=(13.3 < t < 29.4 and t not in ()))
    if 22.1 < t < 23.4:
        pop = 1 + 0.25 * math.sin((t - 22.1) * 14) * math.exp(-(t - 22.1) * 3)
        for ox, oy in ((-4, 4), (4, 4), (-4, -4), (4, -4)):
            c.text(h + 90 + ox, GY - 600 + oy, "!", 190 * pop, INK)
        c.text(h + 90, GY - 600, "!", 190 * pop, (255, 90, 70))
    stream(c, t, hands["R"] if jar is not None and ps["jar"] == 1 else None)
    rome(c, t)
    arrow(c, t, hands["R"] if 8.0 < t < 11.0 else None)
    # snow
    amt = 70 + 160 * sm((t - 13) / 3.0) * (1 - 0.6 * sm((t - 22) / 2))
    snow(c, t, amt)
    out = img.resize((W, H), Image.LANCZOS) if SS != 1 else img
    arr = np.asarray(out).astype(np.float32)
    wa = whip(t)
    if wa > 0:
        acc = np.zeros_like(arr)
        for k in range(7):
            acc += np.roll(arr, int((k - 3) * wa / 3), axis=1)
        arr = acc / 7
    arr *= VIG[:, :, None]
    if 22.05 < t < 22.15 or 32.95 < t < 33.05:
        arr = arr * 0.6 + 255 * 0.4
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

yy, xx = np.mgrid[0:H, 0:W]
VIG = 1.0 - 0.28 * (((xx - W / 2) / (W / 2)) ** 2 * .6 + ((yy - H / 2) / (H / 2)) ** 2 * .6)

if __name__ == "__main__":
    a = sys.argv
    if a[1] == "frames":
        out = a[2]; os.makedirs(out, exist_ok=True)
        SSv = float(a[3]); s0, s1, step = int(a[4]), int(a[5]), int(a[6]) if len(a) > 6 else 1
        for fi in range(s0, s1, step):
            render(fi, SSv).save(f"{out}/f{fi:04d}.jpg", quality=93)
