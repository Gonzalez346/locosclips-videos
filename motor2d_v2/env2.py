"""Entornos v2: plates (capas pre-renderizadas con parallax), Torre Eiffel, París, hotel, estación..."""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from hscene import Ctx, ellpts, rotp, lerp, clamp, mixc, INK, W, H
from kit2 import *
from art2 import shade

GY = 1500.0

class Plate:
    def __init__(self, fn, x0, x1, y0, y1, k=1.0):
        self.x0, self.y0, self.k = x0, y0, k
        img = Image.new("RGBA", (int((x1 - x0) * k), int((y1 - y0) * k)), (0, 0, 0, 0))
        c = Ctx(img, x0 + W / 2, y0 + H / 2, 1.0, k, (0, 0))
        fn(c)
        self.img = img.convert("RGBa")
    def render(self, cx, cy, z, SS, f=1.0, sh=(0, 0), dy=0.0, dx=0.0):
        xl = cx * f - (W / 2 + sh[0]) / z - dx; xr = cx * f + (W / 2 - sh[0]) / z - dx
        yt = cy - (H / 2 + sh[1]) / z + dy; yb = cy + (H / 2 - sh[1]) / z + dy
        k = self.k
        box = ((xl - self.x0) * k, (yt - self.y0) * k, (xr - self.x0) * k, (yb - self.y0) * k)
        out = self.img.transform((int(W * SS), int(H * SS)), Image.EXTENT, box, Image.BILINEAR)
        return out.convert("RGBA")

def put(sc, layer, plate, f=1.0, dy=0.0, dx=0.0):
    cx, cy, z = sc.cam
    tgt = getattr(sc, layer)
    tgt.img.alpha_composite(plate.render(cx, cy, z, sc.SS, f, tgt.sh, dy, dx))

# ------------------------------------------------------------------ cielos
SKY = {
    "gold": [(0, (92, 130, 186)), (.38, (160, 196, 214)), (.62, (252, 214, 168)), (.82, (255, 190, 140)), (1, (250, 170, 130))],
    "day": [(0, (70, 130, 214)), (.5, (150, 204, 240)), (1, (232, 240, 244))],
    "dusk": [(0, (36, 40, 96)), (.4, (110, 76, 130)), (.7, (232, 120, 110)), (1, (252, 176, 116))],
    "dawn": [(0, (84, 110, 180)), (.5, (190, 190, 214)), (.85, (255, 214, 170)), (1, (255, 226, 190))],
    "gray": [(0, (120, 130, 150)), (.6, (176, 184, 196)), (1, (214, 216, 220))],
    "night": [(0, (14, 18, 48)), (.6, (36, 38, 84)), (1, (92, 70, 110))],
}

def clouds(c, seed, y0, y1, x0, x1, col=(255, 250, 244), n=14):
    r = random.Random(seed)
    for i in range(n):
        x = r.uniform(x0, x1); y = r.uniform(y0, y1); s = r.uniform(.7, 1.5)
        for j in range(5):
            c.ell(x + (j - 2) * 70 * s + r.uniform(-14, 14), y + r.uniform(-18, 18) - abs(j - 2) * -8, 90 * s - abs(j - 2) * 14, 40 * s, col, 0)

# ------------------------------------------------------------------ Torre Eiffel
def _half(u, base=.205, top=.006):
    return top + base * (1 - u) ** 3.1

def eiffel(c, x, gy, h, col=(98, 74, 66), hi=None, detail=1.0, f=1.0, lights=0.0):
    """Torre: silueta con celosía real (huecos transparentes + diagonales)."""
    S = c.SS
    tmp = Image.new("RGBA", c.img.size, (0, 0, 0, 0))
    tc = Ctx(tmp, c.cx, c.cy, c.z, c.SS, c.sh)
    wx = lambda u: _half(u) * h
    wy = lambda u: gy - u * h
    N = 60
    left = [(x - wx(i / N), wy(i / N)) for i in range(N + 1)]
    right = [(x + wx(i / N), wy(i / N)) for i in range(N + 1)]
    tc.poly(left + right[::-1], col, 0, f=f)
    # huecos entre tramos
    secs = [(0.0, .17, 4), (.17, .40, 5), (.40, .64, 4), (.64, .90, 4)]
    bw = max(0.9, h * .0105)
    holes = []
    for (u0, u1, nb) in secs:
        for b in range(nb):
            a0 = u0 + (u1 - u0) * b / nb; a1 = u0 + (u1 - u0) * (b + 1) / nb
            inset = h * .0085
            def hole_poly(a0=a0, a1=a1, inset=inset):
                pts = []
                for a in (a0 + .004, a1 - .004):
                    pts.append((x - wx(a) + inset * 1.2, wy(a)))
                pts2 = [(x + wx(a) - inset * 1.2, wy(a)) for a in (a1 - .004, a0 + .004)]
                return pts + pts2
            hp = hole_poly()
            if hp[1][0] < hp[2][0] - 1:
                tc.poly(hp, (0, 0, 0, 0), 0, f=f)
                holes.append((a0, a1))
    # diagonales (X) en cada hueco
    for (a0, a1) in holes:
        for sgn in (1, -1):
            xa = x - sgn * (wx(a0) - h * .008); xb = x + sgn * (wx(a1) - h * .008)
            tc.line([(xa, wy(a0)), (xb, wy(a1))], bw * 1.1, col, f)
        tc.line([(x - wx(a0) + h * .004, wy(a0)), (x + wx(a0) - h * .004, wy(a0))], bw * 1.0, col, f)
    # arco inferior
    aw = wx(0) * .62
    arch = [(x + math.cos(math.radians(a)) * aw, gy - math.sin(math.radians(a)) * h * .12) for a in range(0, 181, 8)]
    tc.poly([(x - aw, gy)] + arch[::-1] + [(x + aw, gy)] if False else arch + [(x - aw, gy), (x + aw, gy)], (0, 0, 0, 0), 0, f=f)
    tc.line(arch, bw * 1.5, col, f)
    # plataformas
    for u, wmul, th in ((.175, 1.12, .016), (.405, 1.15, .012), (.64, 1.2, .009)):
        tc.poly([(x - wx(u) * wmul, wy(u) - h * th), (x + wx(u) * wmul, wy(u) - h * th), (x + wx(u) * wmul, wy(u) + h * th * .5), (x - wx(u) * wmul, wy(u) + h * th * .5)], col, 0, f=f)
        tc.line([(x - wx(u) * wmul, wy(u) - h * th), (x + wx(u) * wmul, wy(u) - h * th)], bw * .9, shade(col, 1.45) if hi is None else hi, f)
    # remate + antena
    tc.poly([(x - h * .012, wy(.93)), (x + h * .012, wy(.93)), (x + h * .004, wy(.985)), (x - h * .004, wy(.985))], col, 0, f=f)
    tc.line([(x, wy(.97)), (x, wy(1.045))], max(1.0, h * .0035), col, f)
    # luz lateral (borde iluminado a la izquierda)
    if hi is not None or True:
        hc = hi or shade(col, 1.55)
        tc.line([(x - wx(i / N) + bw * .4, wy(i / N)) for i in range(2, 58)], bw * .55, hc, f)
    if lights > 0:
        r = random.Random(3)
        for i in range(70):
            u = r.uniform(.03, .9)
            tc.ell(x + r.uniform(-1, 1) * wx(u) * .85, wy(u), h * .0045, h * .0045, (255, 224, 140), 0, f=f)
    c.img.alpha_composite(tmp)

# ------------------------------------------------------------------ edificios
def mansard(c, x0, x1, y, hgt, col, ridge=None):
    sl = hgt * .55
    c.poly([(x0 - 8, y), (x1 + 8, y), (x1 - sl * .6, y - hgt), (x0 + sl * .6, y - hgt)], col, 6)
    c.poly([(x0 + sl * .6 - 6, y - hgt), (x1 - sl * .6 + 6, y - hgt), (x1 - sl * .6, y - hgt - 14), (x0 + sl * .6, y - hgt - 14)], shade(col, .78), 4)

def haussmann(c, x, gy, w, floors, seed, stone=(236, 218, 184), roof=(92, 106, 140), floor_h=118, warm=0.0, lit=0.0):
    r = random.Random(seed)
    base_h = 150
    h = base_h + floors * floor_h
    y_top = gy - h
    c.poly([(x, gy), (x + w, gy), (x + w, y_top), (x, y_top)], stone, 6)
    # franjas de piedra
    for i in range(floors + 1):
        yy = gy - base_h - i * floor_h
        c.poly([(x, yy), (x + w, yy), (x + w, yy - 12), (x, yy - 12)], shade(stone, .9), 3)
    # planta baja: tienda
    shop = r.choice([(176, 54, 60), (44, 96, 92), (200, 150, 60), (60, 70, 120)])
    c.poly([(x + 10, gy), (x + w - 10, gy), (x + w - 10, gy - base_h + 20), (x + 10, gy - base_h + 20)], shop, 5)
    nw = max(1, int((w - 40) // 130))
    for i in range(nw):
        wx0 = x + 24 + i * (w - 48) / nw; ww = (w - 48) / nw - 14
        c.poly([(wx0, gy - 8), (wx0 + ww, gy - 8), (wx0 + ww, gy - base_h + 40), (wx0, gy - base_h + 40)], (250, 226, 150) if lit > .5 else (150, 190, 200), 4)
    # ventanas
    n = max(2, int(w // 100))
    for fl in range(floors):
        yy = gy - base_h - fl * floor_h - 12
        for i in range(n):
            wx = x + (i + .5) * w / n; ww = 30; hh = floor_h - 34
            c.poly([(wx - ww - 8, yy), (wx + ww + 8, yy), (wx + ww + 8, yy - hh - 8), (wx - ww - 8, yy - hh - 8)], shade(stone, .85), 3)
            glass = (250, 226, 150) if (lit > 0 and r.random() < lit) else (118, 150, 176)
            c.poly([(wx - ww, yy - 2), (wx + ww, yy - 2), (wx + ww, yy - hh), (wx - ww, yy - hh)], glass, 3)
            c.line([(wx, yy - 2), (wx, yy - hh)], 4, shade(stone, .7))
            c.line([(wx - ww, yy - hh * .55), (wx + ww, yy - hh * .55)], 3, shade(stone, .7))
            for k in (-1, 1):
                c.poly([(wx + k * (ww + 4), yy), (wx + k * (ww + 22), yy), (wx + k * (ww + 22), yy - hh), (wx + k * (ww + 4), yy - hh)], (88, 120, 110), 3)
        if fl in (1, floors - 1) or fl == 0:
            c.line([(x + 6, yy + 4), (x + w - 6, yy + 4)], 6, (40, 40, 52))
    # mansarda
    mh = 150
    mansard(c, x, x + w, y_top, mh, roof)
    for i in range(max(1, int(w // 170))):
        dx = x + (i + .5) * w / max(1, int(w // 170))
        c.poly([(dx - 28, y_top - 10), (dx + 28, y_top - 10), (dx + 28, y_top - 78), (dx, y_top - 104), (dx - 28, y_top - 78)], shade(roof, 1.15), 4)
        c.poly([(dx - 16, y_top - 18), (dx + 16, y_top - 18), (dx + 16, y_top - 70), (dx - 16, y_top - 70)], (250, 226, 150) if lit > .3 and r.random() < .6 else (130, 160, 184), 3)
    for i in range(r.randint(2, 3)):
        cx_ = x + r.uniform(.12, .88) * w
        c.poly([(cx_ - 14, y_top - mh * .8), (cx_ + 14, y_top - mh * .8), (cx_ + 14, y_top - mh - 62), (cx_ - 14, y_top - mh - 62)], (150, 96, 80), 4)
        c.poly([(cx_ - 18, y_top - mh - 62), (cx_ + 18, y_top - mh - 62), (cx_ + 18, y_top - mh - 76), (cx_ - 18, y_top - mh - 76)], (110, 70, 62), 3)
    return y_top - mh

def skyline_sil(c, x0, x1, gy, seed, col, hmin=300, hmax=620, wmin=120, wmax=260, roof_col=None):
    r = random.Random(seed)
    x = x0
    while x < x1:
        w = r.uniform(wmin, wmax); h = r.uniform(hmin, hmax)
        c.poly([(x, gy + 30), (x + w, gy + 30), (x + w, gy - h), (x, gy - h)], col, 0)
        rc = roof_col or shade(col, .9)
        c.poly([(x - 4, gy - h), (x + w + 4, gy - h), (x + w - 34, gy - h - 80), (x + 34, gy - h - 80)], rc, 0)
        if r.random() < .6:
            cx_ = x + r.uniform(.2, .8) * w
            c.poly([(cx_ - 10, gy - h - 60), (cx_ + 10, gy - h - 60), (cx_ + 10, gy - h - 120), (cx_ - 10, gy - h - 120)], col, 0)
        x += w - 2

def tree_plane(c, x, gy, s=1.0, col=(86, 120, 72)):
    c.poly([(x - 12 * s, gy), (x + 12 * s, gy), (x + 8 * s, gy - 260 * s), (x - 8 * s, gy - 260 * s)], (92, 70, 62), 5)
    for dx, dy, r_ in ((-70, -310, 90), (60, -330, 100), (0, -390, 110), (-100, -380, 70), (100, -392, 76), (0, -300, 100)):
        c.ell(x + dx * s, gy + dy * s, r_ * s, r_ * .82 * s, col, 0)
    for dx, dy, r_ in ((-50, -350, 40), (40, -400, 46), (80, -330, 36)):
        c.ell(x + dx * s, gy + dy * s, r_ * s, r_ * .8 * s, shade(col, 1.2), 0)

def lamp_post(c, x, gy, s=1.0):
    col = (46, 52, 64)
    c.poly([(x - 9 * s, gy), (x + 9 * s, gy), (x + 6 * s, gy - 420 * s), (x - 6 * s, gy - 420 * s)], col, 4)
    c.poly([(x - 22 * s, gy), (x + 22 * s, gy), (x + 14 * s, gy - 40 * s), (x - 14 * s, gy - 40 * s)], col, 4)
    c.ell(x, gy - 440 * s, 26 * s, 34 * s, (255, 238, 170), 5)
    c.poly([(x - 30 * s, gy - 468 * s), (x + 30 * s, gy - 468 * s), (x + 14 * s, gy - 496 * s), (x - 14 * s, gy - 496 * s)], col, 4)

def cafe(c, x, gy, w=520, awn=((176, 40, 52), (250, 244, 230))):
    c.poly([(x, gy), (x + w, gy), (x + w, gy - 330), (x, gy - 330)], (232, 210, 170), 6)
    c.poly([(x + 40, gy), (x + w - 40, gy), (x + w - 40, gy - 250), (x + 40, gy - 250)], (96, 62, 52), 5)
    c.poly([(x + 60, gy - 20), (x + w - 60, gy - 20), (x + w - 60, gy - 230), (x + 60, gy - 230)], (255, 226, 156), 0)
    n = 10
    for i in range(n):
        x0 = x - 20 + (w + 40) * i / n; x1 = x - 20 + (w + 40) * (i + 1) / n
        c.poly([(x0 - 6 + (0), gy - 330), (x1 + 0, gy - 330), (x1 + 16, gy - 250), (x0 + 16 - 16, gy - 250)], awn[i % 2], 3)
    c.d.text(c.pt(x + w / 2, gy - 372), "CAFÉ", font=fnt(FONT_TITLE, 74 * c.z * c.SS), fill=(250, 236, 200), anchor="mm", stroke_width=int(5 * c.z * c.SS), stroke_fill=INK)

def bistro_table(c, x, gy, s=1.0):
    c.ell(x, gy - 130 * s, 58 * s, 14 * s, (240, 236, 224), 5)
    c.poly([(x - 6 * s, gy - 130 * s), (x + 6 * s, gy - 130 * s), (x + 6 * s, gy), (x - 6 * s, gy)], (40, 40, 48), 3)
    c.poly([(x - 36 * s, gy), (x + 36 * s, gy), (x + 6 * s, gy - 8 * s), (x - 6 * s, gy - 8 * s)], (40, 40, 48), 3)
    for k in (-1, 1):
        c.poly([(x + k * 100 * s - 28 * s, gy - 100 * s), (x + k * 100 * s + 28 * s, gy - 100 * s), (x + k * 100 * s + 28 * s, gy - 112 * s), (x + k * 100 * s - 28 * s, gy - 112 * s)], (130, 80, 56), 4)
        c.line([(x + k * 100 * s - 22 * s, gy - 100 * s), (x + k * 100 * s - 22 * s, gy)], 5, (50, 40, 44))
        c.line([(x + k * 100 * s + 22 * s, gy - 100 * s), (x + k * 100 * s + 22 * s, gy)], 5, (50, 40, 44))
        c.poly([(x + k * 100 * s - 24 * s + (18 * s if k > 0 else -18 * s), gy - 112 * s), (x + k * 100 * s + (36 * s if k > 0 else -36 * s), gy - 112 * s), (x + k * 100 * s + (36 * s if k > 0 else -36 * s), gy - 190 * s), (x + k * 100 * s - 24 * s + (18 * s if k > 0 else -18 * s), gy - 190 * s)], (130, 80, 56), 4)

def car(c, x, gy, s=1.0, col=(46, 76, 120), flip=False, wheel=0.0):
    d = -1 if flip else 1
    P = lambda a, b: (x + a * s * d, gy + b * s)
    for wx in (-120, 120):
        c.ell(*P(wx, -46), 48 * s, 48 * s, (40, 36, 44), 7)
        c.ell(*P(wx, -46), 26 * s, 26 * s, (236, 226, 200), 4)
        for k in range(6):
            a = wheel + k * math.pi / 3
            c.line([P(wx, -46), P(wx + math.cos(a) * 24, -46 + math.sin(a) * 24)], 3, (90, 80, 70))
    c.poly([P(-190, -60), P(-190, -140), P(-110, -150), P(-70, -150), P(-60, -250), P(70, -250), P(90, -150), P(180, -146), P(196, -100), P(196, -60)], col, 8)
    c.poly([P(-50, -238), P(-50, -156), P(78, -156), P(62, -238)], (170, 210, 224), 5)
    c.line([P(14, -238), P(14, -156)], 5, col)
    c.ell(*P(190, -108), 18 * s, 18 * s, (255, 240, 170), 5)
    c.poly([P(-200, -50), P(210, -50), P(210, -64), P(-200, -64)], shade(col, .6), 5)
    c.poly([P(-150, -84), P(-120, -84), P(-120, -132), P(-150, -132)], shade(col, .8), 3)

def street(c, x0, x1, gy, kind="paris", depth=1100):
    c.poly([(x0, gy), (x1, gy), (x1, gy + depth), (x0, gy + depth)], (140, 124, 120), 0)
    c.poly([(x0, gy), (x1, gy), (x1, gy + 36), (x0, gy + 36)], (206, 190, 170), 0)
    c.poly([(x0, gy + 36), (x1, gy + 36), (x1, gy + 46), (x0, gy + 46)], (96, 84, 84), 0)
    r = random.Random(11)
    for i in range(int((x1 - x0) / 70)):
        xx = x0 + i * 70 + r.uniform(-10, 10)
        c.line([(xx, gy + 64), (xx + 50, gy + 64)], 3, (118, 102, 100))
    for i in range(int((x1 - x0) / 62)):
        xx = x0 + i * 62 + (31 if (i % 2) else 0)
        c.line([(xx, gy + 110), (xx + 40, gy + 110)], 3, (118, 102, 100))
        c.line([(xx - 31, gy + 160), (xx + 9, gy + 160)], 3, (118, 102, 100))
