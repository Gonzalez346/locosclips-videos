"""El hombre que vendió la Torre Eiffel — 21 planos. 1080x1920, 30 fps."""
import math, random, sys
import numpy as np
from PIL import Image, ImageDraw
from hscene import Ctx, ellpts, rotp, lerp, clamp, mixc, INK, W, H, FPS, sm
from kit2 import *
from art2 import *
from env2 import *

DUR = 43.729
NFR = int(round(DUR * FPS))
SKIN = {"lus": (240, 200, 160), "a": (226, 176, 136), "b": (244, 206, 170), "c": (206, 150, 112), "d": (236, 188, 146)}
LUS = dict(build="slim", suit=(44, 52, 92), shirt=(248, 244, 232), tie=(196, 52, 60), hat="fedora", hatcol=(52, 48, 64),
           hair=(36, 28, 28), stache="thin", skin=SKIN["lus"], vest=(130, 90, 70), leg=1.12, hairstyle="slick")
BIZ = [
    dict(build="portly", suit=(96, 70, 60), tie=(40, 80, 120), hat="bowler", hatcol=(40, 36, 44), hair=(80, 60, 50), stache="handle", skin=SKIN["a"], vest=(210, 190, 140)),
    dict(build="slim", suit=(60, 80, 72), tie=(180, 120, 40), hat="top", hatcol=(36, 34, 40), hair=(120, 120, 130), stache="big", skin=SKIN["b"], leg=1.1),
    dict(build="stout", suit=(110, 100, 92), tie=(150, 40, 60), hat="flat", hatcol=(90, 84, 76), hair=(60, 40, 30), stache="beard", skin=SKIN["c"]),
    dict(build="avg", suit=(70, 60, 96), tie=(220, 200, 90), hat="bowler", hatcol=(60, 44, 40), hair=(30, 30, 40), stache="thin", skin=SKIN["d"], glasses=True),
    dict(build="portly", suit=(52, 96, 110), tie=(180, 50, 60), hat="fedora", hatcol=(96, 70, 56), hair=(90, 80, 60), stache="big", skin=SKIN["a"], vest=(230, 220, 190)),
    dict(build="avg", suit=(120, 62, 70), tie=(40, 70, 110), hat="top", hatcol=(60, 56, 64), hair=(40, 30, 28), stache="handle", skin=SKIN["b"], leg=.95),
]
BOLSA = dict(build="portly", suit=(140, 96, 66), tie=(36, 84, 130), hat="bowler", hatcol=(44, 38, 48), hair=(70, 50, 40), stache="handle", skin=SKIN["a"], vest=(226, 206, 150), leg=.9)
GEND = dict(build="avg", suit=(40, 60, 120), tie=(40, 60, 120), hat="kepi", hatcol=(40, 60, 120), hair=(50, 40, 36), stache="big", skin=SKIN["d"], cravat=False, badge=True, pants=(34, 50, 100))

def cam(t, keys, sway=1.0, seed=0):
    """keys: [(t, cx, cy, z)] interpolación suave + micro-movimiento de cámara."""
    if t <= keys[0][0]: k = keys[0][1:]
    elif t >= keys[-1][0]: k = keys[-1][1:]
    else:
        for i in range(len(keys) - 1):
            if keys[i][0] <= t <= keys[i + 1][0]:
                u = (t - keys[i][0]) / (keys[i + 1][0] - keys[i][0]); u = u * u * (3 - 2 * u)
                k = tuple(lerp(keys[i][j], keys[i + 1][j], u) for j in (1, 2, 3)); break
    cx, cy, z = k
    cx += math.sin(t * 1.3 + seed) * 5 * sway; cy += math.sin(t * 1.9 + seed * 2) * 4 * sway
    return cx, cy, z

def shk(t, hits):
    sx = sy = 0.0
    for (th, a) in hits:
        u = t - th
        if 0 <= u < .6:
            e = math.exp(-u * 8) * a
            sx += math.sin(u * 55) * e; sy += math.cos(u * 47) * e * .8
    return (sx, sy)

def ui(sc):
    return Ctx(sc.fg.img, W / 2, H / 2, 1.0, sc.SS, (0, 0))

def seq(t, t0, dur=.4): return clamp((t - t0) / dur)

# =============================================================== plates
_P = {}
def tone_mix(col, tone):
    if tone == "gray": return mixc(col, (150, 154, 164), .38)
    if tone == "dusk": return mixc(col, (170, 120, 140), .25)
    return col

def plate(name, tone="gold"):
    key = (name, tone)
    if key in _P: return _P[key]
    T = lambda c_: tone_mix(c_, tone)
    if name == "far":
        def fn(c):
            haze = {"gold": (196, 176, 186), "gray": (170, 176, 188), "dusk": (170, 120, 150), "day": (176, 190, 214)}[tone]
            skyline_sil(c, -1500, 3900, GY - 40, 5, haze, 420, 760)
            skyline_sil(c, -1500, 3900, GY - 10, 9, mixc(haze, (120, 120, 150), .25), 300, 560, 150, 300)
        _P[key] = Plate(fn, -1600, 4000, -500, 1700, .9)
    elif name == "tower":
        def fn(c):
            col = {"gold": (132, 98, 104), "gray": (120, 124, 136), "dusk": (120, 70, 100), "day": (122, 110, 120)}[tone]
            eiffel(c, 0, GY, 1700, col=col, hi=mixc(col, (255, 214, 160), .5))
        _P[key] = Plate(fn, -700, 700, -600, 1700, 1.0)
    elif name == "mid":
        def fn(c):
            x = -1400; seed = 1
            stones = [(236, 216, 184), (228, 206, 176), (240, 224, 196), (222, 200, 172)]
            while x < 3700:
                w = 300 + (seed * 53) % 170
                haussmann(c, x, GY, w, 3 + seed % 3, seed, stone=T(stones[seed % 4]), roof=T((86, 98, 132)), lit=.0)
                x += w - 3; seed += 1
        _P[key] = Plate(fn, -1500, 3800, -500, 1700, 1.0)
    elif name == "street":
        def fn(c):
            street(c, -1500, 3800, GY)
            for x in (-300, 520, 1900, 2800): lamp_post(c, x, GY + 20, 1.0)
            tree_plane(c, 120, GY + 10, 1.0, T((84, 118, 70))); tree_plane(c, 2250, GY + 10, 1.1, T((84, 118, 70)))
        _P[key] = Plate(fn, -1500, 3800, 700, 2500, 1.0)
    elif name == "hotel":
        def fn(c):
            hotel_facade(c, 1000, GY)
        _P[key] = Plate(fn, -700, 2700, -300, 2500, 1.0)
    elif name == "suite":
        def fn(c): suite_room(c, 1000, GY)
        _P[key] = Plate(fn, -800, 2800, -300, 2500, 1.0)
    elif name == "station":
        def fn(c): station(c, 1000, GY)
        _P[key] = Plate(fn, -1000, 3000, -400, 2500, 1.0)
    elif name == "police":
        def fn(c): police_post(c, 1000, GY)
        _P[key] = Plate(fn, -700, 2700, -300, 2500, 1.0)
    return _P[key]

def hotel_facade(c, x, gy):
    stone = (240, 224, 192); W_ = 1300
    c.poly([(x - W_ / 2, gy), (x + W_ / 2, gy), (x + W_ / 2, gy - 1200), (x - W_ / 2, gy - 1200)], stone, 8)
    for i in range(7):
        yy = gy - i * 150 - 40
        c.line([(x - W_ / 2, yy), (x + W_ / 2, yy)], 3, shade(stone, .86))
    for fl in range(6):
        for i in range(6):
            wx = x - W_ / 2 + 110 + i * 216
            if abs(wx - x) < 90 and fl == 0: continue
            yy = gy - 190 - fl * 150
            c.poly([(wx - 52, yy), (wx + 52, yy), (wx + 52, yy - 120), (wx - 52, yy - 120)], shade(stone, .8), 5)
            c.poly([(wx - 42, yy - 4), (wx + 42, yy - 4), (wx + 42, yy - 112), (wx - 42, yy - 112)], (255, 224, 140) if (i + fl) % 3 else (120, 150, 180), 4)
            c.line([(wx, yy - 4), (wx, yy - 112)], 4, shade(stone, .7))
            c.line([(wx - 60, yy + 4), (wx + 60, yy + 4)], 6, (50, 50, 60))
    c.poly([(x - W_ / 2 - 10, gy - 1200), (x + W_ / 2 + 10, gy - 1200), (x + W_ / 2 - 60, gy - 1340), (x - W_ / 2 + 60, gy - 1340)], (88, 100, 134), 7)
    # entrada
    c.poly([(x - 170, gy), (x + 170, gy), (x + 170, gy - 380), (x - 170, gy - 380)], (70, 52, 60), 8)
    c.poly([(x - 140, gy), (x + 140, gy), (x + 140, gy - 340), (x - 140, gy - 340)], (255, 232, 160), 0)
    c.line([(x, gy), (x, gy - 340)], 5, (110, 80, 50))
    c.poly([(x - 250, gy - 380), (x + 250, gy - 380), (x + 210, gy - 450), (x - 210, gy - 450)], (60, 100, 90), 8)
    for k in range(-4, 5): c.line([(x + k * 52, gy - 380), (x + k * 50, gy - 450)], 3, (230, 220, 190))
    for k in (-1, 1):
        for j in range(2):
            px_ = x + k * (230 + j * 80)
            c.poly([(px_ - 26, gy), (px_ + 26, gy), (px_ + 22, gy - 380), (px_ - 22, gy - 380)], (248, 238, 214), 6)
    c.d.text(c.pt(x, gy - 520), "GRAND HÔTEL", font=fnt(FONT_TITLE, 80 * c.z * c.SS), fill=(240, 196, 80), anchor="mm", stroke_width=int(5 * c.SS), stroke_fill=INK)
    c.poly([(x - 100, gy + 20), (x + 100, gy + 20), (x + 190, gy + 700), (x - 190, gy + 700)], (170, 36, 48), 6)

def suite_room(c, x, gy):
    wall = (122, 44, 58)
    c.poly([(x - 1700, gy - 1500), (x + 1700, gy - 1500), (x + 1700, gy), (x - 1700, gy)], wall, 0)
    r = random.Random(4)
    for i in range(-30, 31):
        c.poly([(x + i * 58, gy - 1500), (x + i * 58 + 26, gy - 1500), (x + i * 58 + 26, gy), (x + i * 58, gy)], shade(wall, 1.12), 0)
    for i in range(-30, 31):
        for j in range(14):
            c.poly([(x + i * 58 + 13, gy - 90 - j * 100 - 14), (x + i * 58 + 22, gy - 90 - j * 100), (x + i * 58 + 13, gy - 90 - j * 100 + 14), (x + i * 58 + 4, gy - 90 - j * 100)], (176, 100, 90), 0)
    # zócalo madera
    c.poly([(x - 1700, gy - 330), (x + 1700, gy - 330), (x + 1700, gy), (x - 1700, gy)], (92, 58, 42), 0)
    for i in range(-14, 15):
        c.poly([(x + i * 120 + 12, gy - 300), (x + i * 120 + 108, gy - 300), (x + i * 120 + 108, gy - 40), (x + i * 120 + 12, gy - 40)], (110, 70, 50), 5)
    c.poly([(x - 1700, gy - 346), (x + 1700, gy - 346), (x + 1700, gy - 330), (x - 1700, gy - 330)], (232, 190, 90), 3)
    c.poly([(x - 1700, gy - 1180), (x + 1700, gy - 1180), (x + 1700, gy - 1150), (x - 1700, gy - 1150)], (232, 190, 90), 3)
    # ventanas con torre al fondo
    for wx in (x - 430, x + 430):
        c.poly([(wx - 150, gy - 380), (wx + 150, gy - 380), (wx + 150, gy - 1060), (wx, gy - 1130), (wx - 150, gy - 1060)], (214, 190, 140), 8)
        c.poly([(wx - 128, gy - 400), (wx + 128, gy - 400), (wx + 128, gy - 1050), (wx, gy - 1110), (wx - 128, gy - 1050)], (250, 206, 160), 0)
        # cielo+torre
        for i, (a, b) in enumerate([(-400, (252, 214, 170)), (-700, (236, 190, 160)), (-900, (190, 170, 190))]): pass
        eiffel(c, wx + (30 if wx < x else -30), gy - 400, 560, col=(150, 108, 110), hi=(250, 200, 150))
        c.poly([(wx - 150, gy - 380), (wx + 150, gy - 380), (wx + 150, gy - 372), (wx - 150, gy - 372)], (214, 190, 140), 0)
        c.line([(wx, gy - 400), (wx, gy - 1110)], 6, (214, 190, 140)); c.line([(wx - 128, gy - 760), (wx + 128, gy - 760)], 6, (214, 190, 140))
        # cortinas
        for k in (-1, 1):
            c.poly([(wx + k * 130, gy - 1080), (wx + k * 230, gy - 1080), (wx + k * 250, gy - 300), (wx + k * 150, gy - 300)], (200, 150, 70), 7)
            for j in range(4): c.line([(wx + k * (150 + j * 22), gy - 1070), (wx + k * (160 + j * 22), gy - 320)], 3, (236, 196, 110))
        c.poly([(wx - 270, gy - 1110), (wx + 270, gy - 1110), (wx + 270, gy - 1150), (wx - 270, gy - 1150)], (232, 190, 90), 5)
    # alfombra y suelo
    c.poly([(x - 1700, gy), (x + 1700, gy), (x + 1700, gy + 900), (x - 1700, gy + 900)], (150, 100, 66), 0)
    for i in range(-30, 30):
        c.line([(x + i * 90, gy), (x + i * 90 - 130, gy + 900)], 3, (126, 80, 52))
    for j in range(8): c.line([(x - 1700, gy + 60 + j * 110), (x + 1700, gy + 60 + j * 110)], 3, (126, 80, 52))
    c.poly([(x - 900, gy + 90), (x + 900, gy + 90), (x + 1050, gy + 600), (x - 1050, gy + 600)], (150, 40, 54), 6)
    c.poly([(x - 840, gy + 120), (x + 840, gy + 120), (x + 970, gy + 570), (x - 970, gy + 570)], (176, 60, 70), 4)
    # araña
    for dx in (-0,):
        c.line([(x, gy - 1500), (x, gy - 1180)], 6, (60, 50, 50))
        c.poly([(x - 140, gy - 1170), (x + 140, gy - 1170), (x + 90, gy - 1090), (x - 90, gy - 1090)], (236, 196, 100), 6)
        for k in range(-3, 4):
            c.line([(x + k * 44, gy - 1090), (x + k * 40, gy - 1030)], 4, (250, 240, 200))
            c.ell(x + k * 40, gy - 1022, 10, 14, (255, 236, 160), 3)

def station(c, x, gy):
    c.poly([(x - 2200, gy - 1500), (x + 2200, gy - 1500), (x + 2200, gy), (x - 2200, gy)], (170, 176, 192), 0)
    for i in range(-5, 6):
        ax = x + i * 460
        c.line([(ax - 230, gy - 130)] + [(ax + math.cos(math.radians(a)) * 230, gy - 130 - math.sin(math.radians(a)) * 880) for a in range(180, -1, -10)] + [(ax + 230, gy - 130)], 14, (60, 70, 86))
        c.poly([(ax - 40, gy), (ax + 40, gy), (ax + 34, gy - 160), (ax - 34, gy - 160)], (60, 70, 86), 5)
    for k in range(-6, 7):
        c.line([(x + k * 220, gy - 1000), (x + k * 220 - 60, gy - 130)], 3, (130, 150, 170))
    c.poly([(x - 1700, gy - 1010), (x + 1700, gy - 1010), (x + 1700, gy - 920), (x - 1700, gy - 920)], (230, 224, 206), 0)
    c.ell(x, gy - 1160, 120, 120, (250, 244, 224), 8)
    c.line([(x, gy - 1160), (x, gy - 1236)], 8, INK); c.line([(x, gy - 1160), (x + 52, gy - 1130)], 8, INK)
    c.poly([(x - 2200, gy), (x + 2200, gy), (x + 2200, gy + 260), (x - 2200, gy + 260)], (190, 170, 150), 0)
    c.poly([(x - 2200, gy), (x + 2200, gy), (x + 2200, gy + 28), (x - 2200, gy + 28)], (240, 220, 80), 0)
    c.poly([(x - 2200, gy + 260), (x + 2200, gy + 260), (x + 2200, gy + 1300), (x - 2200, gy + 1300)], (76, 70, 76), 0)
    for i in range(-40, 40):
        c.poly([(x + i * 60, gy + 380), (x + i * 60 + 28, gy + 380), (x + i * 60 + 28, gy + 392), (x + i * 60, gy + 392)], (120, 90, 70), 0)
    c.line([(x - 2200, gy + 340), (x + 2200, gy + 340)], 9, (150, 150, 166)); c.line([(x - 2200, gy + 440), (x + 2200, gy + 440)], 9, (150, 150, 166))

def police_post(c, x, gy):
    c.poly([(x - 1700, gy), (x + 1700, gy), (x + 1700, gy - 900), (x - 1700, gy - 900)], (176, 170, 178), 0)
    skyline_sil(c, x - 1800, x + 1800, gy - 40, 6, (150, 150, 168), 500, 800)
    c.poly([(x - 560, gy), (x + 560, gy), (x + 560, gy - 780), (x - 560, gy - 780)], (216, 206, 188), 8)
    c.poly([(x - 590, gy - 780), (x + 590, gy - 780), (x + 520, gy - 900), (x - 520, gy - 900)], (70, 84, 120), 8)
    for k in (-1, 1):
        for fl in range(2):
            wx = x + k * 380; yy = gy - 330 - fl * 210
            c.poly([(wx - 70, yy), (wx + 70, yy), (wx + 70, yy - 150), (wx - 70, yy - 150)], (255, 226, 150) if fl == 0 else (130, 160, 190), 6)
            c.line([(wx, yy), (wx, yy - 150)], 4, (90, 80, 80))
    c.poly([(x - 140, gy), (x + 140, gy), (x + 140, gy - 380), (x - 140, gy - 380)], (82, 64, 70), 8)
    c.poly([(x - 100, gy), (x + 100, gy), (x + 100, gy - 340), (x - 100, gy - 340)], (255, 226, 150), 0)
    c.poly([(x - 330, gy - 500), (x + 330, gy - 500), (x + 330, gy - 600), (x - 330, gy - 600)], (36, 60, 130), 7)
    c.d.text(c.pt(x, gy - 550), "POLICE", font=fnt(FONT_TITLE, 92 * c.z * c.SS), fill=(250, 244, 230), anchor="mm")
    c.ell(x - 440, gy - 440, 34, 40, (90, 170, 250), 5); c.ell(x + 440, gy - 440, 34, 40, (90, 170, 250), 5)
    for i in range(4): c.poly([(x - 220 - i * 6, gy + i * 24), (x + 220 + i * 6, gy + i * 24), (x + 220 + i * 6, gy + 24 + i * 24), (x - 220 - i * 6, gy + 24 + i * 24)], (190, 180, 170), 5)
    c.poly([(x - 1700, gy + 100), (x + 1700, gy + 100), (x + 1700, gy + 1000), (x - 1700, gy + 1000)], (130, 120, 120), 0)

# =============================================================== utilidades de plano
G_WARM = dict(bloom=.45, tint=(1.05, 1.0, .93), contrast=1.05, grain=2.5, vig=1.0)
G_INT = dict(bloom=.4, tint=(1.04, .98, .94), contrast=1.06, grain=2.5, vig=1.1)
G_COOL = dict(bloom=.2, tint=(.94, .98, 1.06), contrast=1.05, grain=3, vig=1.25)
G_GRAY = dict(bloom=.08, tint=(.97, .98, 1.0), contrast=.98, grain=3, vig=1.4, lift=-4)
G_HOT = dict(bloom=.55, tint=(1.08, .98, .9), contrast=1.08, grain=2.5, vig=1.2)
SUN_PX = (780, 760)

def bg_paris(sc, tone="gold", tx=500, f_far=.3, f_tw=.5, f_mid=.8):
    put(sc, "far", plate("far", tone), f_far)
    put(sc, "far", plate("tower", tone), f_tw, 0, tx)
    put(sc, "mid", plate("mid", tone), f_mid)
    put(sc, "stage", plate("street", tone), 1.0)

def sky_for(tone, SS, sun=True):
    return sky_img(SKY[tone], SS, sun=((SUN_PX[0], SUN_PX[1], 70, (255, 244, 205)) if sun and tone in ("gold", "day", "dusk") else None))

def birds(c_ui, t, n=7, seed=1, x0=-200, speed=160, y0=340):
    r = random.Random(seed)
    for i in range(n):
        x = (x0 + i * 90 + speed * t + r.uniform(0, 60)) % 1400 - 150; y = y0 + r.uniform(-120, 120) + math.sin(t * 2 + i) * 12
        fl = math.sin(t * 14 + i * 2) * 10
        c_ui.line([(x - 20, y - 6 + fl), (x, y), (x + 20, y - 6 + fl)], 4, (60, 50, 70))

def coin_arc(c, p0, p1, u, h=220, r=26, f=1.0, spin=0.0):
    x = lerp(p0[0], p1[0], u); y = lerp(p0[1], p1[1], u) - math.sin(u * math.pi) * h
    coin(c, x, y, r * (1 - .25 * u), f, sq=abs(math.cos(spin + u * 9)) * .8 + .2)

def pop_text(sc, text, x, y, px, t, t0, col=(255, 226, 70), t1=None, rot=0.0, stroke=10):
    title_text(ui(sc), text, x, y, px, t, t0, col, FONT_TITLE, stroke, t1, rot)

SHOTS = []
def shot(t0, t1, name=""):
    def deco(fn):
        SHOTS.append((t0, t1, fn, name)); return fn
    return deco

# --------------------------------------------------------------- 1. París 1925
@shot(0.00, 1.91, "paris")
def s1(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, 1160, 1.45), (1.91, 1000, 880, .82)], 1.0, 1)
    sc = Scene(cx, cy, z, SS)
    bg_paris(sc, "gold")
    # coche que cruza
    xcar = lerp(-100, 1900, clamp(t / 1.91) ** .9); car(sc.stage, xcar, GY + 130, 1.15, (176, 52, 60), wheel=-t * 20); sc.shadow(xcar, GY + 140, 220, 22)
    # peatón
    person2(sc.stage, 1500 + t * 30, GY + 230, .62, t, walk=t * 7, build="portly", suit=(96, 80, 70), hat="bowler", hatcol=(50, 44, 50), stache="big", flip=True)
    sc.shadow(1500 + t * 30, GY + 240, 70, 14)
    person2(sc.stage, 420 - t * 24, GY + 260, .66, t + 1, walk=t * 6.4, build="slim", suit=(60, 100, 96), hat="fedora", hatcol=(110, 70, 56), stache="thin")
    sc.shadow(420 - t * 24, GY + 270, 70, 14)
    birds(ui(sc), t, 8, 3)
    pop_text(sc, "PARÍS", 540, 330, 250, t, .12, (255, 232, 110), t1=1.9)
    pop_text(sc, "1925", 540, 560, 210, t, .32, (255, 255, 255), t1=1.9, stroke=10)
    return sc, sky_for("gold", SS), dict(blur=3.2, grade=G_WARM, glows=[(SUN_PX[0], SUN_PX[1], 340, (255, 190, 110), .22)])

# --------------------------------------------------------------- 2. SE VENDE
@shot(1.91, 4.43, "sevende")
def s2(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, 700, 1.0), (2.52, 1000, 1000, 1.22)], 1.0, 2)
    hits = [(.78, 14)]
    sc = Scene(cx, cy, z, SS, shk(u, hits))
    put(sc, "far", plate("far", "gold"), .3)
    put(sc, "mid", plate("mid", "gold"), .8)
    eiffel(sc.far, 1000, GY, 2500, col=(128, 94, 100), hi=(255, 214, 160), f=.95)
    put(sc, "stage", plate("street", "gold"), 1.0)
    d = u - .5
    fall = 0.0
    if d < 0: fall = -1200
    elif d < .28: fall = -1200 * (1 - eout(d / .28) ** 1.0) ** 2 + 0
    else:
        b = d - .28
        fall = -90 * math.exp(-b * 7) * abs(math.sin(b * 14))
    rot = 6 * math.exp(-max(0, d - .28) * 2.5) * math.sin(max(0, d - .28) * 9)
    sign_post(sc.stage, 1000, GY + 230 + fall, "SE VENDE", 1.35, (176, 40, 52), px=84, rot=rot)
    sc.shadow(1000, GY + 240, 130, 16, k=clamp(1 + fall / 800) * .8)
    if u > .78: poof(sc.stage, 1000, GY + 215, 120, (u - .78) / .7, 1.0)
    if u > .78 and u < .86: pass
    pop_text(sc, "¡SE VENDE!", 540, 300, 190, t, 1.91 + 1.0, (255, 226, 70), t1=4.4, rot=-4)
    for i in range(9):
        a = i * .7 + 1; p = clamp((u - .8) / .9)
        if p > 0: sparkle(sc.stage, 1000 + math.cos(a) * 280 * p, GY - 40 - abs(math.sin(a)) * 260 * p, 18 * (1 - p), 1.0)
    return sc, sky_for("gold", SS), dict(blur=2.4, grade=G_WARM, flash=(.45 if .78 <= u < .86 else 0), glows=[(SUN_PX[0], SUN_PX[1], 340, (255, 190, 110), .2)])

# --------------------------------------------------------------- 3. Víctor Lustig
@shot(4.43, 6.80, "lustig")
def s3(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY - 330, 1.55), (2.37, 1000, GY - 380, 1.8)], 1.0, 3)
    sc = Scene(cx, cy, z, SS)
    bg_paris(sc, "gold", tx=700)
    tip = clamp((u - 1.15) / .35) * (1 - clamp((u - 1.9) / .3))
    hat_dy = -26 * elastic(clamp((u - 1.2) / .5)) * (1 - clamp((u - 1.95) / .3))
    arm = (62, -520 + 20 * (1 - tip)) if tip > .01 else None
    if tip > .01: arm = (lerp(150, 64, eout(tip)), lerp(-250, -535, eout(tip)))
    person2(sc.stage, 1000, GY + 60, 1.35, t, emo="smug" if u < 1.2 else "happy", armR=arm, hoff=hat_dy, look=(.5, 0), **LUS)
    sc.shadow(1000, GY + 80, 150, 22)
    ui_c = ui(sc)
    lowerthird(ui_c, "VÍCTOR LUSTIG", "Estafador · Checoslovaquia", u, .55, 2.3, y=1190)
    sparkle(sc.fg, 1000, 1000, 1, 1.0) if False else None
    if 1.5 < u < 1.9:
        p = (u - 1.5) / .4; sparkle(ui_c, 790, 640 - p * 30, 34 * math.sin(p * math.pi) + 4)
    return sc, sky_for("gold", SS), dict(blur=5, grade=G_WARM, glows=[(SUN_PX[0], SUN_PX[1], 340, (255, 190, 110), .22)])

# --------------------------------------------------------------- 4. El coste
@shot(6.80, 9.85, "coste")
def s4(t, u, SS):
    cx, cy, z = cam(u, [(0, 760, GY - 380, 1.0), (3.05, 900, GY - 420, 1.18)], 1.0, 4)
    sc = Scene(cx, cy, z, SS)
    put(sc, "far", plate("far", "gold"), .3)
    put(sc, "mid", plate("mid", "gold"), .8)
    eiffel(sc.mid, 470, GY, 2000, col=(128, 94, 100), hi=(255, 214, 160), f=.95)
    put(sc, "stage", plate("street", "gold"), 1.0)
    # pintor colgado de la torre
    py = GY - 760 + math.sin(u * 2.2) * 90; px_ = 560 + math.sin(u * 3.0) * 30
    sc.stage.line([(px_ + 40, GY - 1500), (px_ + 40, py - 120)], 5, (90, 70, 60))
    person2(sc.stage, px_, py + 270, .5, t, build="slim", suit=(70, 110, 170), hat="flat", hatcol=(210, 200, 190), stache="thin",
            armR=(70, -160 + math.sin(u * 8) * 30), armL=(-60, -90), emo="focus", leg=.7)
    sc.stage.poly([(px_ + 100, py + 80), (px_ + 170, py + 80), (px_ + 160, py + 140), (px_ + 110, py + 140)], (190, 60, 60), 5)
    # funcionario con bolsillos vacíos
    fx = 1250
    person2(sc.stage, fx, GY + 90, 1.05, t, emo="worried", armL=(-170, -250), armR=(170, -250), **dict(BIZ[0], hat="top", hatcol=(40, 36, 46)))
    sc.shadow(fx, GY + 100, 130, 20)
    for k in (-1, 1):
        sc.stage.poly([(fx + k * 150, GY - 140), (fx + k * 150 + k * 40, GY - 140), (fx + k * 150 + k * 20, GY - 60)], (250, 246, 236), 5)
    # monedas volando hacia la torre
    for i in range(14):
        p = ((u * 1.4 - i * .2) % 2.8) / 2.8
        if u * 1.4 - i * .2 < 0: continue
        coin_arc(sc.stage, (fx - 150, GY - 170), (540, GY + 50), p, 340 + (i % 3) * 60, 30, 1.0, i)
    for i, tx in enumerate((.9, 1.5, 2.1, 2.6)):
        if u > tx: pop_text(sc, "-5.000 F", 760 + (i % 2) * 160 - i * 40, 520 - 80 * clamp((u - tx) / 1.0) - i * 110, 110, t, 6.8 + tx, (255, 110, 90), t1=6.8 + tx + .9, rot=(-6 if i % 2 else 6))
    return sc, sky_for("gold", SS), dict(blur=2.6, grade=G_WARM, glows=[(SUN_PX[0], SUN_PX[1], 340, (255, 190, 110), .2)])

# --------------------------------------------------------------- 5. La idea
@shot(9.85, 11.70, "idea")
def s5(t, u, SS):
    z = 2.15 + .35 * clamp(u / 1.85)
    cx, cy, z = cam(u, [(0, 1000, GY - 430, 2.1), (1.85, 1000, GY - 460, 2.35)], 1.0, 5)
    sc = Scene(cx, cy, z, SS, shk(u, [(.62, 10)]))
    # rayos radiales de fondo
    bgc = Ctx(sc.far.img, W / 2, H / 2, 1.0, SS, (0, 0))
    for i in range(18):
        a = i / 18 * 6.283 + u * .35
        bgc.poly([(540, 900), (540 + math.cos(a) * 2200, 900 + math.sin(a) * 2200), (540 + math.cos(a + .17) * 2200, 900 + math.sin(a + .17) * 2200)], (255, 204, 110) if i % 2 else (250, 170, 80), 0)
    emo = "neutral" if u < .45 else ("surprised" if u < .9 else "smug")
    person2(sc.stage, 1000, GY + 60, 1.35, t, emo=emo, look=(0, -.6) if u > .5 else (.5, 0), armR=(150, -420) if u > .9 else None, **LUS)
    # bombilla
    k = elastic(clamp((u - .6) / .5))
    if u > .6:
        bulb(sc.stage, 1030, GY - 820 - 20 * math.sin(u * 5), 1.2 * k, 1.0, on=1.0)
        rays(sc.stage, 1030, GY - 820, 120 * k, 190 * k, 12, u, (255, 244, 150), 12)
    return sc, SKY["day"] and sky_img([(0, (255, 214, 120)), (1, (250, 170, 90))], SS), dict(blur=0, grade=G_HOT, flash=(.5 if .6 <= u < .68 else 0), glows=[(540, 560, 380, (255, 230, 150), .35 if u > .6 else 0)])

# --------------------------------------------------------------- 6. Seis empresarios
@shot(11.70, 14.14, "seis")
def s6(t, u, SS):
    sc = Scene(540, 960, 1.0, SS)
    bgc = Ctx(sc.far.img, W / 2, H / 2, 1.0, SS, (0, 0))
    for i in range(-3, 14):
        for j in range(-1, 20):
            x = 100 * i + (50 if j % 2 else 0); y = 100 * j
            bgc.poly([(x, y - 22), (x + 16, y), (x, y + 22), (x - 16, y)], (28, 120, 120), 0)
    pos = [(300, 640, 0), (790, 640, 1), (300, 1020, 2), (790, 1020, 3), (300, 1400, 4), (790, 1400, 5)]
    for i, (px_, py, k) in enumerate(pos):
        t0 = .12 + i * .3
        if u < t0: continue
        e = eback(clamp((u - t0) / .35), 2.4) if u - t0 < .35 else 1 + .03 * math.sin((u - t0) * 9) * math.exp(-(u - t0) * 2)
        sc.stage.poly([(px_ - 170, py + 30), (px_ + 170, py + 30), (px_ + 150, py + 62), (px_ - 150, py + 62)], (212, 168, 80), 6)
        sc.shadow(px_, py + 40, 130 * e, 16)
        arm = None
        if u > t0 + .45: arm = (80, -160 * .55 + math.sin(u * 5 + i) * 5)
        person2(sc.stage, px_, py + 34, .6 * max(.05, e), t + i, emo="happy" if u > t0 + .45 else "neutral", armR=arm, **BIZ[k])
        # sobre
        ue = clamp((u - t0 - .22) / .38)
        if ue > 0:
            ex = lerp(px_ + 340, px_ + 100, eout(ue)); ey = lerp(py - 520, py - 176, ue ** 1.4) - math.sin(ue * 3.14) * 80
            envelope(sc.stage, ex, ey, .55, rot=(1 - ue) * 40, f=1.0)
        # número
        if u > t0 + .5:
            n = clamp((u - t0 - .5) / .25)
            sc.stage.ell(px_ - 150, py - 330, 40 * elastic(n), 40 * elastic(n), (240, 196, 80), 6)
            sc.stage.d.text(sc.stage.pt(px_ - 150, py - 330), str(i + 1), font=fnt(FONT_TITLE, 60 * elastic(n) * sc.SS), fill=INK, anchor="mm") if elastic(n) > .1 else None
    return sc, sky_img([(0, (12, 70, 78)), (1, (8, 40, 56))], SS), dict(blur=0, grade=G_INT, shade=True, glows=[])


def flag(c, x, y, t, w=170, h=110, mast=True, ph=0.0):
    if mast: c.line([(x, y + 40), (x, y - 330)], 9, (90, 70, 60))
    cols = [(40, 70, 170), (250, 250, 250), (220, 50, 56)]
    for i, col in enumerate(cols):
        pts = []
        for k in range(0, 9):
            xx = x + k * w / 8; yy = y - 330 + math.sin(t * 6 + k * .6 + ph) * 9 * (k / 8)
            pts.append((xx, yy))
        x0 = i * h / 3
        top = [(px_, py_ + x0) for px_, py_ in pts]; bot = [(px_, py_ + x0 + h / 3) for px_, py_ in pts]
        c.poly(top + bot[::-1], col, 0)
    c.poly([(x, y - 330), (x + w, y - 330 + math.sin(t * 6 + 3.0 + ph) * 9), (x + w, y - 330 + math.sin(t * 6 + 3.0 + ph) * 9 + h), (x, y - 330 + h)], (0, 0, 0, 0), 4, out=INK) if False else None

# --------------------------------------------------------------- 7. Hotel
@shot(14.14, 15.53, "hotel")
def s7(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY + 220, 1.0), (1.39, 1000, GY - 480, .95)], 1.0, 7)
    sc = Scene(cx, cy, z, SS)
    put(sc, "stage", plate("hotel"), 1.0)
    for k in (-1, 1): flag(sc.stage, 1000 + k * 520, GY - 1000, t, 190, 120, True, k)
    xc = lerp(-300, 640, eout(clamp(u / 1.0))); car(sc.stage, xc, GY + 560, 1.5, (30, 60, 100), wheel=-t * 18 * (1 - clamp(u / 1.0))); sc.shadow(xc, GY + 574, 300, 26)
    person2(sc.stage, 1230, GY + 70, 1.05, t, emo="happy", armR=(150, -400) if u % .6 < .3 else (160, -330), hat="top", hatcol=(120, 30, 50), suit=(130, 34, 52), tie=(240, 210, 100), stache="big", cravat=True, badge=True, build="avg", hair=(180, 180, 190), skin=SKIN["b"])
    sc.shadow(1230, GY + 80, 110, 16)
    for i in range(6):
        a = i * 1.7 + t * 2
        sparkle(sc.stage, 1000 + math.cos(a * .7) * 330, GY - 520 + math.sin(a) * 40, 12 + 12 * abs(math.sin(a * 2)), 1.0)
    return sc, sky_for("gold", SS, False), dict(blur=0, grade=G_WARM, glows=[(540, 420, 520, (255, 200, 120), .18)])

# --------------------------------------------------------------- 8. Funcionario
def badge_shield(c, x, y, s, f=1.0, rot=0):
    pts = [(-70, -80), (70, -80), (70, 10), (0, 90), (-70, 10)]
    c.poly([(x + a * s, y + b * s) for a, b in rotp(pts, rot, 0, 0)], (240, 196, 80), 8, f=f)
    pts2 = [(-52, -62), (52, -62), (52, 4), (0, 70), (-52, 4)]
    c.poly([(x + a * s, y + b * s) for a, b in rotp(pts2, rot, 0, 0)], (40, 70, 170), 4, f=f)
    sparkle(c, x, y - 6 * s, 34 * s, f)
    for k, col in enumerate(((40, 70, 170), (250, 250, 250), (220, 50, 56))):
        c.poly([(x + (-46 + k * 31) * s, y + 70 * s), (x + (-15 + k * 31) * s, y + 70 * s), (x + (-15 + k * 31) * s, y + 150 * s), (x + (-46 + k * 31) * s, y + 150 * s)], col, 4, f=f)

@shot(15.53, 18.19, "oficial")
def s8(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY - 330, 1.12), (2.66, 1000, GY - 400, 1.4)], 1.0, 8)
    sc = Scene(cx, cy, z, SS)
    put(sc, "stage", plate("suite"), 1.0)
    for i, (bx, k) in enumerate(((640, 0), (790, 1), (1220, 3), (1380, 4))):
        person2(sc.stage, bx, GY + 120, .62, t + i, emo="happy" if u > 1.4 else "neutral", look=(-.4 if bx > 1000 else .4, 0), **BIZ[k])
        sc.shadow(bx, GY + 128, 62, 10)
    k_ = elastic(clamp((u - .9) / .6))
    arm = (150, -430) if u > .85 else (-140, -300)
    person2(sc.stage, 1000, GY + 360, 1.12, t, emo="smug" if u < .9 else "happy", talk=abs(math.sin(t * 13)) * .9, armR=arm,
            armL=(-170, -250 + math.sin(t * 4) * 20), **LUS)
    sc.shadow(1000, GY + 372, 150, 22)
    if u > .9: badge_shield(sc.stage, 1000 + 150 * 1.12 + 6, GY + 360 - 430 * 1.12 - 20, 1.0 * k_, 1.0, math.sin(t * 5) * 4)
    return sc, sky_img([(0, (80, 30, 40)), (1, (120, 44, 58))], SS), dict(blur=0, grade=G_INT, glows=[(1000, 560, 500, (255, 210, 130), .12)])

# --------------------------------------------------------------- 9. Derribar
@shot(18.19, 20.10, "derribar")
def s9(t, u, SS):
    cx, cy, z = cam(u, [(0, 1050, GY - 230, 1.25), (1.91, 1050, GY - 200, 1.4)], 1.0, 9)
    sc = Scene(cx, cy, z, SS, shk(u, [(1.0, 16)]))
    put(sc, "stage", plate("suite"), 1.0)
    for i, bx in enumerate((1280, 1420, 1540)):
        person2(sc.stage, bx, GY + 70, .58, t + i, emo="surprised" if u > 1.0 else "neutral", **BIZ[i + 1])
    sc.stage.poly([(760, GY - 60), (1460, GY - 60), (1500, GY - 20), (720, GY - 20)], (120, 74, 48), 8)
    for lx in (800, 1420): sc.stage.poly([(lx - 18, GY - 20), (lx + 18, GY - 20), (lx + 14, GY + 250), (lx - 14, GY + 250)], (100, 60, 42), 6)
    sc.shadow(1100, GY - 10, 360, 20, .35)
    push = clamp((u - .45) / .25)
    ang = 0.0
    if u > .6: ang = 90 * ein((u - .6) / .42) if u < 1.02 else 90 - 8 * math.exp(-(u - 1.02) * 6) * abs(math.sin((u - 1.02) * 16))
    pivx = 1100
    tower_model(sc.stage, pivx - 0 * 1, GY - 62, 1.25, tilt=ang, f=1.0)
    ax = 780 + 130 * eout(push) * (1 - clamp((u - .8) / .3))
    person2(sc.stage, 760, GY + 250, 1.1, t, emo="smug", armR=(lerp(130, 255, eout(push)) if u < 1.1 else 190, -470 + 40 * push), armL=(-150, -230), look=(.7, 0), **LUS)
    sc.shadow(760, GY + 262, 140, 20)
    if u > 1.02: poof(sc.stage, 1230, GY - 40, 110, (u - 1.02) / .8)
    if u > 1.15: pop_text(sc, "DEMOLICIÓN", 540, 560, 150, t, 18.19 + 1.15, (255, 80, 70), t1=20.1, rot=-8, stroke=12)
    return sc, sky_img([(0, (80, 30, 40)), (1, (120, 44, 58))], SS), dict(blur=0, grade=G_INT, flash=(.4 if 1.0 <= u < 1.07 else 0), glows=[])

# --------------------------------------------------------------- 10. Subasta
@shot(20.10, 22.40, "subasta")
def s10(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY - 280, 1.0), (2.3, 1000, GY - 300, 1.16)], 1.0, 10)
    sc = Scene(cx, cy, z, SS, shk(u, [(2.0, 8)]))
    put(sc, "stage", plate("suite"), 1.0)
    # podio + Lustig
    sc.stage.poly([(900, GY + 40), (1100, GY + 40), (1120, GY + 260), (880, GY + 260)], (110, 70, 48), 8)
    person2(sc.stage, 1000, GY + 40, .92, t, emo="smug", armR=(150, -360 + (140 * abs(math.sin(u * 8)) * -1 if u > 1.6 else 0)), armL=(-120, -260), **LUS)
    gavel(sc.stage, 1000 + 150 * .92, GY + 40 - 360 * .92, .9, rot=(40 if u < 1.9 else (-10 if u < 2.05 else 40)), f=1.0)
    sc.stage.poly([(880, GY + 60), (1120, GY + 60), (1120, GY + 260), (880, GY + 260)], (110, 70, 48), 8)
    nums = [50, 80, 120, 200]
    for i, (bx, k) in enumerate(((560, 0), (1000, 4), (1440, 5))):
        raise_ = abs(math.sin((u * 1.55 + i * .33) * math.pi)) > .55
        arm = (110, -480) if raise_ else (130, -260)
        person2(sc.stage, bx, GY + 520, .78, t + i, emo="happy" if raise_ else "neutral", armR=arm, **BIZ[k])
        sc.shadow(bx, GY + 530, 90, 14)
        if raise_:
            px_ = bx + 110 * .78; py = GY + 520 - 480 * .78
            sc.stage.line([(px_, py), (px_, py - 90)], 8, (110, 70, 48))
            sc.stage.ell(px_, py - 130, 54, 54, (250, 244, 226), 7)
            sc.stage.d.text(sc.stage.pt(px_, py - 130), str(i * 2 + 3), font=fnt(FONT_TITLE, 70 * sc.cam[2] * sc.SS), fill=INK, anchor="mm")
    n = min(3, int(u / .55))
    p = (u - n * .55) / .55
    pop_text(sc, f"{nums[n]}.000 F", 540, 420, 210, t, 20.10 + n * .55, (255, 226, 70), t1=20.10 + n * .55 + .6, rot=(-5 if n % 2 else 5))
    return sc, sky_img([(0, (80, 30, 40)), (1, (120, 44, 58))], SS), dict(blur=0, grade=G_INT, glows=[])

# --------------------------------------------------------------- 11. Todo el hierro
def beam(c, x, y, w, rot, f=1.0, col=(112, 118, 134)):
    P = lambda pts: [(x + a, y + b) for a, b in rotp(pts, rot, 0, 0)]
    c.poly(P([(-w / 2, -16), (w / 2, -16), (w / 2, 16), (-w / 2, 16)]), col, 6, f=f)
    c.poly(P([(-w / 2, -16), (w / 2, -16), (w / 2, -6), (-w / 2, -6)]), shade(col, 1.35), 0, f=f)
    for k in range(-3, 4): c.ell(*P([(k * w / 8, 6)])[0], 4, 4, shade(col, .55), 0, f=f)

@shot(22.40, 24.00, "hierro")
def s11(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY - 150, 1.0), (1.6, 1000, GY - 230, 1.28)], 1.0, 11)
    sc = Scene(cx, cy, z, SS, shk(u, [(.55, 9), (.95, 8)]))
    put(sc, "far", plate("far", "gold"), .3)
    put(sc, "mid", plate("mid", "gold"), .8)
    put(sc, "stage", plate("street", "gold"), 1.0)
    rows = [(0, 4), (1, 3), (2, 2)]
    idx = 0
    for r_, nrow in rows:
        for j in range(nrow):
            tl = .08 + idx * .1
            tx = 1000 + (j - (nrow - 1) / 2) * 190
            ty = GY + 200 - r_ * 40
            land = clamp((u - tl) / .28)
            yy = lerp(-400, ty, ein(land)) if u - tl < .28 else ty - 14 * math.exp(-(u - tl - .28) * 9) * abs(math.sin((u - tl - .28) * 20))
            if u > tl: beam(sc.stage, tx + (r_ % 2) * 20, yy, 360, (1 - land) * 18 + (j - 1) * 2, 1.0, (112 + 6 * idx, 118, 134))
            idx += 1
        # nada
    sc.shadow(1000, GY + 230, 480, 26, .5)
    person2(sc.stage, 420, GY + 280, 1.0, t, emo="happy", armL=(-100, -330) if u > .9 else None, armR=(120, -310), **BOLSA)
    if u > .8:
        k = elastic(clamp((u - .8) / .4))
        sc.stage.d.text(sc.stage.pt(420 - 6, GY + 280 - 470), "$", font=fnt(FONT_TITLE, 190 * k * sc.cam[2] * sc.SS), fill=(250, 214, 70), anchor="mm", stroke_width=int(9 * sc.SS * sc.cam[2]), stroke_fill=INK)
    for i in range(8):
        a = i * 1.1 + t * 2.0
        if u > .5: sparkle(sc.stage, 1000 + math.cos(a) * 340, GY + 80 + math.sin(a * 1.3) * 90, 10 + 14 * abs(math.sin(a * 3)))
    pop_text(sc, "7.000 TONELADAS", 540, 420, 118, t, 22.4 + .35, (255, 255, 255), t1=24.0, rot=3)
    return sc, sky_for("gold", SS), dict(blur=2.6, grade=G_WARM, glows=[(SUN_PX[0], SUN_PX[1], 340, (255, 190, 110), .2)])

# --------------------------------------------------------------- 12. Pago
@shot(24.00, 25.40, "pago")
def s12(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY - 330, 1.3), (1.4, 1000, GY - 350, 1.5)], 1.0, 12)
    sc = Scene(cx, cy, z, SS)
    put(sc, "stage", plate("suite"), 1.0)
    p = clamp((u - .2) / .8)
    person2(sc.stage, 800, GY + 180, 1.0, t, emo="happy", armR=(lerp(120, 210, eout(clamp(u / .6))), -290), armL=(-140, -240), look=(.8, 0), **BOLSA)
    person2(sc.stage, 1260, GY + 180, 1.0, t, emo="smug", armL=(lerp(-120, -210, eout(clamp(u / .6))), -290 + 20 * p), armR=(150, -250), look=(-.8, 0), flip=True, **LUS)
    sc.shadow(800, GY + 192, 130, 20); sc.shadow(1260, GY + 192, 110, 20)
    bx = lerp(800 + 215, 1260 - 215, eout(p)); by = GY + 180 - 290 - math.sin(p * math.pi) * 90
    briefcase(sc.stage, bx, by + 40, .9, rot=-p * 8)
    for i in range(7):
        q = clamp((u - .45 - i * .06) / .6)
        if 0 < q < 1: banknote(sc.stage, lerp(bx, 1060, q) + math.sin(i * 2.3) * 70, by - q * 260 + math.sin(q * 6 + i) * 30, .7, rot=q * 220 * (1 if i % 2 else -1))
    if u > 1.0: sparkle(sc.stage, 1090, GY + 180 - 290 - 60, 40 * math.sin(clamp((u - 1.0) / .4) * math.pi) + 2)
    return sc, sky_img([(0, (80, 30, 40)), (1, (120, 44, 58))], SS), dict(blur=0, grade=G_INT, glows=[])

# --------------------------------------------------------------- 13. Bolsa feliz
@shot(25.40, 27.90, "feliz")
def s13(t, u, SS):
    cx, cy, z = cam(u, [(0, 850, GY - 340, 1.2), (2.5, 1250, GY - 360, 1.2)], 1.0, 13)
    sc = Scene(cx, cy, z, SS)
    bg_paris(sc, "gold", tx=700)
    bx = lerp(780, 1280, clamp(u / 2.5))
    person2(sc.stage, bx, GY + 200, 1.0, t, walk=u * 8.5, emo="happy", armL=(-90 + math.sin(u * 17) * 14, -260), armR=(90 - math.sin(u * 17) * 14, -260), **BOLSA)
    sc.shadow(bx, GY + 212, 130, 20)
    k = elastic(clamp((u - .35) / .5))
    ub = ui(sc)
    # burbuja de pensamiento con la torre
    sx = (bx - cx) * z + 540 + 120; sy = (GY + 200 - 560 - cy) * z + 960 - 330
    ub.ell(sx - 110, sy + 180, 20 * k, 20 * k, (255, 255, 255), 5); ub.ell(sx - 60, sy + 120, 30 * k, 30 * k, (255, 255, 255), 5)
    ub.ell(sx + 40, sy - 40, 230 * k, 190 * k, (255, 252, 244), 8)
    if k > .5:
        tower_model(ub, sx + 20, sy + 90, .55 * k, 0, 1.0, (150, 110, 80))
        for i in range(4):
            coin(ub, sx - 120 + i * 60, sy + 100 - (i % 2) * 40 + math.sin(t * 4 + i) * 8, 24 * k, 1.0, abs(math.cos(t * 5 + i)) * .7 + .3)
    for i in range(10):
        a = i * 1.4 + t * 1.5
        sparkle(sc.stage, bx + math.cos(a) * 230, GY - 100 + math.sin(a * 1.1) * 250, 8 + 10 * abs(math.sin(a * 2)))
    return sc, sky_for("gold", SS), dict(blur=3.2, grade=G_WARM, glows=[(SUN_PX[0], SUN_PX[1], 340, (255, 190, 110), .22)])

# --------------------------------------------------------------- 14. Tren
def train_car(c, x, gy, col, label="", w=520):
    c.poly([(x - w / 2, gy - 60), (x + w / 2, gy - 60), (x + w / 2, gy - 360), (x - w / 2, gy - 360)], col, 8)
    c.poly([(x - w / 2 - 6, gy - 360), (x + w / 2 + 6, gy - 360), (x + w / 2 - 24, gy - 400), (x - w / 2 + 24, gy - 400)], shade(col, .7), 6)
    for i in range(4):
        wx = x - w / 2 + 70 + i * (w - 140) / 3
        c.poly([(wx - 36, gy - 150), (wx + 36, gy - 150), (wx + 36, gy - 300), (wx - 36, gy - 300)], (255, 226, 150), 6)
    c.poly([(x - w / 2, gy - 120), (x + w / 2, gy - 120), (x + w / 2, gy - 110), (x - w / 2, gy - 110)], (236, 196, 80), 0)
    if label: c.d.text(c.pt(x, gy - 335), label, font=fnt(FONT_TITLE, 40 * c.z * c.SS), fill=(250, 236, 200), anchor="mm")
    for dx in (-w * .32, w * .32):
        c.ell(x + dx, gy - 36, 38, 38, (40, 36, 44), 6); c.ell(x + dx, gy - 36, 18, 18, (180, 170, 150), 4)

def loco(c, x, gy, t, rotw=0.0):
    c.poly([(x - 200, gy - 60), (x + 220, gy - 60), (x + 220, gy - 300), (x - 200, gy - 300)], (46, 52, 66), 8)
    c.poly([(x - 200, gy - 300), (x + 20, gy - 300), (x + 20, gy - 500), (x - 200, gy - 500)], (60, 66, 82), 8)
    c.poly([(x - 214, gy - 500), (x + 34, gy - 500), (x + 34, gy - 530), (x - 214, gy - 530)], (190, 50, 56), 6)
    c.poly([(x + 120, gy - 300), (x + 190, gy - 300), (x + 176, gy - 440), (x + 134, gy - 440)], (46, 52, 66), 7)
    c.poly([(x + 110, gy - 440), (x + 200, gy - 440), (x + 214, gy - 490), (x + 96, gy - 490)], (46, 52, 66), 7)
    c.ell(x + 224, gy - 180, 22, 40, (255, 240, 170), 5)
    for dx, r_ in ((-110, 60), (30, 60), (160, 42)):
        c.ell(x + dx, gy - r_, r_, r_, (40, 36, 44), 7); c.ell(x + dx, gy - r_, r_ * .45, r_ * .45, (200, 190, 170), 4)
        c.line([(x + dx, gy - r_), (x + dx + math.cos(rotw) * r_ * .8, gy - r_ + math.sin(rotw) * r_ * .8)], 5, (200, 190, 170))
    c.line([(x - 110, gy - 60 + math.sin(rotw) * 30), (x + 30, gy - 60 + math.sin(rotw) * 30)], 9, (150, 150, 160))

@shot(27.90, 30.45, "tren")
def s14(t, u, SS):
    ox = 1500 * (clamp((u - .7) / 1.85)) ** 2
    cx, cy, z = cam(u, [(0, 800, GY - 140, 1.0), (1.2, 900, GY - 170, 1.05), (2.55, 1700, GY - 190, 1.0)], 1.0, 14)
    sc = Scene(cx, cy, z, SS, shk(u, [(1.3, 6)]))
    put(sc, "stage", plate("station"), 1.0)
    gyt = GY + 400
    carc = ((SS and (0, 0, 0)))
    train_car(sc.stage, 700 + ox, gyt, (176, 52, 60), "VIENA")
    train_car(sc.stage, 1240 + ox, gyt, (176, 52, 60), "VIENA")
    loco(sc.stage, 1770 + ox, gyt, t, -t * 12 * (1 + ox / 400))
    for i in range(6):
        q = ((t * .9 + i * .17) % 1.0)
        sc.stage.ell(1770 + 140 + ox + q * 120 - 160 * q, gyt - 520 - q * 420, 40 + q * 70, 34 + q * 60, (246, 246, 250), 0)
    run = clamp(u / 1.25)
    lx = lerp(120, 480, run) if u < 1.25 else 480 + ox * 0 + (ox - 1500 * (clamp((1.25 - .7) / 1.85)) ** 2)
    if u < 1.25:
        person2(sc.stage, lx, GY + 520, 1.0, t, walk=u * 15, emo="worried" if False else "smug", armR=(150, -300), armL=(-130, -280), look=(1, 0), **dict(LUS, hat="fedora"), lean=.6)
        briefcase(sc.stage, lx - 190, GY + 520 - 150, .55)
    else:
        w_ = elastic(clamp((u - 1.3) / .4))
        person2(sc.stage, 520 + ox - 1500 * (clamp((1.25 - .7) / 1.85)) ** 2 * 0 + 0, gyt + 30 - 40 * math.sin(clamp((u - 1.25) / .5) * math.pi), 1.0, t, emo="happy", armR=(140, -520), armL=(-120, -250), hoff=-24, **LUS)
        briefcase(sc.stage, 520 + ox - 210, gyt - 100, .55)
    for i in range(10):
        a = (t * 2 + i * .7)
        if u > 1.2: sc.stage.line([(1000 + (i * 190 + t * 900) % 1600 - 400 + ox * .2, GY + 180 + i * 50), (1000 + (i * 190 + t * 900) % 1600 + 100 + ox * .2, GY + 180 + i * 50)], 4, (255, 255, 255)) if False else None
    return sc, sky_img([(0, (176, 186, 214)), (1, (230, 216, 206))], SS), dict(blur=0, grade=G_WARM, whip=0, glows=[(540, 300, 500, (255, 214, 160), .14)])


# --------------------------------------------------------------- 15. Vergüenza
def bench(c, x, gy, s=1.0):
    c.poly([(x - 260 * s, gy - 220 * s), (x + 260 * s, gy - 220 * s), (x + 260 * s, gy - 160 * s), (x - 260 * s, gy - 160 * s)], (120, 84, 60), 7)
    c.poly([(x - 270 * s, gy - 120 * s), (x + 270 * s, gy - 120 * s), (x + 270 * s, gy - 80 * s), (x - 270 * s, gy - 80 * s)], (140, 96, 66), 7)
    c.poly([(x - 270 * s, gy - 80 * s), (x + 270 * s, gy - 80 * s), (x + 270 * s, gy - 40 * s), (x - 270 * s, gy - 40 * s)], (120, 84, 60), 7)
    for k in (-1, 1): c.poly([(x + k * 230 * s - 14 * s, gy - 40 * s), (x + k * 230 * s + 14 * s, gy - 40 * s), (x + k * 230 * s + 14 * s, gy), (x + k * 230 * s - 14 * s, gy)], (40, 40, 52), 5)

@shot(30.45, 33.07, "verguenza")
def s15(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY - 240, 1.15), (2.62, 1000, GY - 300, 1.5)], .6, 15)
    sc = Scene(cx, cy, z, SS)
    bg_paris(sc, "gray", tx=700)
    red = clamp(u / 1.0)
    skin = mixc(SKIN["a"], (236, 120, 104), red * .8)
    head_dn = clamp(u / .8)
    person2(sc.stage, 1000, GY + 120, 1.05, t, emo="worried", look=(0, .9), armL=(-60, -170), armR=(60, -170), hoff=18 * head_dn, lean=.5 * head_dn, **dict(BOLSA, leg=.9, skin=skin))
    bench(sc.stage, 1000, GY + 110, 1.05)
    sc.shadow(1000, GY + 125, 300, 22)
    for i in range(3):
        q = ((u * .9 + i * .33) % 1.0)
        sc.stage.ell(1030 + i * 38 - 40, GY - 440 + q * 200, 7, 11, (150, 200, 250), 3)
    k = elastic(clamp((u - .6) / .5))
    ub = ui(sc)
    ub.ell(790, 520, 130 * k, 100 * k, (255, 255, 255), 7)
    if k > .5:
        coin(ub, 790, 520, 52 * k, 1.0)
        ub.line([(750, 480), (830, 560)], 14, (226, 50, 56)); ub.line([(830, 480), (750, 560)], 14, (226, 50, 56))
    rc = Ctx(sc.fg.img, W / 2, H / 2, 1.0, SS, (0, 0))
    for i in range(46):
        x = (i * 97 + u * 260) % 1300 - 100; y = (i * 211 + u * 1500) % 2000 - 60
        rc.line([(x, y), (x - 20, y + 60)], 3, (214, 226, 240))
    return sc, sky_for("gray", SS, False), dict(blur=3.0, grade=G_GRAY, glows=[])

# --------------------------------------------------------------- 16. Comisaría
@shot(33.07, 34.90, "comisaria")
def s16(t, u, SS):
    cx, cy, z = cam(u, [(0, 800, GY - 260, 1.05), (1.83, 1000, GY - 280, 1.0)], 1.0, 16)
    sc = Scene(cx, cy, z, SS)
    put(sc, "stage", plate("police"), 1.0)
    person2(sc.stage, 1000, GY + 20, 1.0, t, walk=None, emo="neutral", look=(-.3, 0), armR=(150, -250), **GEND)
    sc.shadow(1000, GY + 32, 100, 16)
    if u < .85: bx = lerp(260, 720, eout(clamp(u / .85))); wk = u * 9; fl = False
    else: bx = lerp(720, 330, clamp((u - .9) / .9)); wk = u * 12; fl = True
    st = u > .72 and u < .95
    person2(sc.stage, bx, GY + 330, 1.0, t, walk=(None if st else wk), emo="worried", flip=fl, look=(.6, 0), hoff=0, **dict(BOLSA, leg=.9))
    sc.shadow(bx, GY + 342, 120, 18)
    if st:
        pop_text(sc, "?", 540, 560, 280, t, 33.07 + .72, (255, 226, 70), t1=33.07 + .96)
    return sc, sky_img([(0, (140, 150, 176)), (1, (200, 196, 204))], SS), dict(blur=0, grade=G_COOL, glows=[])

# --------------------------------------------------------------- 17. Otra vez
@shot(34.90, 37.54, "otravez")
def s17(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY - 320, 1.12), (2.64, 1000, GY - 360, 1.3)], 1.0, 17)
    sc = Scene(cx, cy, z, SS)
    put(sc, "stage", plate("suite"), 1.0)
    for i, (bx, k) in enumerate(((620, 2), (780, 3), (1230, 5), (1390, 1))):
        t0 = .25 + i * .35
        x = lerp(bx + (700 if bx > 1000 else -700), bx, eout(clamp((u - t0) / .7)))
        mv = clamp((u - t0) / .7) < 1
        person2(sc.stage, x, GY + 120, .62, t + i, walk=(u * 10 if mv else None), emo="neutral", **BIZ[k])
        sc.shadow(x, GY + 128, 62, 10)
    person2(sc.stage, 1000, GY + 360, 1.12, t, emo="smug", talk=abs(math.sin(t * 12)) * .8, armR=(150, -300 + math.sin(t * 3) * 20), armL=(-150, -260), **LUS)
    sc.shadow(1000, GY + 372, 150, 22)
    e = clamp((u - 1.3) / 1.0)
    if e > 0: envelope(sc.stage, lerp(1160, 1480, eout(e)), GY - 170 - math.sin(e * 3.14) * 160, .6, rot=e * 40)
    pop_text(sc, "OTRA VEZ…", 540, 300, 150, t, 34.9 + .15, (255, 150, 90), t1=37.5, rot=-3)
    return sc, sky_img([(0, (60, 28, 44)), (1, (96, 40, 56))], SS), dict(blur=0, grade=G_COOL, glows=[(1000, 560, 500, (255, 190, 130), .1)])

# --------------------------------------------------------------- 18. Sospecha
@shot(37.54, 38.45, "sospecha")
def s18(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY - 430, 2.0), (.91, 1000, GY - 450, 2.45)], 1.0, 18)
    sc = Scene(cx, cy, z, SS, shk(u, [(.05, 6)]))
    person2(sc.stage, 1000, GY + 60, 1.35, t, emo="sly", look=(-1, .1), armR=(60, -380), **BIZ[3])
    pop_text(sc, "?", 800, 440, 360, t, 37.54 + .2, (255, 226, 70), t1=38.45)
    return sc, sky_img([(0, (60, 28, 44)), (1, (110, 44, 60))], SS), dict(blur=0, grade=G_COOL, glows=[])

# --------------------------------------------------------------- 19. Policía
@shot(38.45, 40.04, "policia")
def s19(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY - 320, 1.1), (1.59, 1000, GY - 340, 1.2)], 1.5, 19)
    sc = Scene(cx, cy, z, SS, shk(u, [(.12, 14)]))
    put(sc, "stage", plate("suite"), 1.0)
    lx = lerp(1050, -250, clamp((u - .25) / 1.2) ** 1.4)
    person2(sc.stage, lx, GY + 360, 1.12, t, walk=u * 17, emo="worried", flip=True, armL=(-150, -230), armR=(150, -300), lean=-.5, look=(-1, 0), **LUS)
    briefcase(sc.stage, lx + 170, GY + 360 - 170, .6)
    sc.shadow(lx, GY + 372, 130, 20)
    for i in range(2):
        gx = lerp(2300 + i * 220, 1380 + i * 150, eout(clamp((u - .02 - i * .08) / .5))) + max(0, u - .6) * (-420)
        person2(sc.stage, gx, GY + 300 + i * 40, 1.05, t, walk=u * 15 + i, emo="angry", flip=True, armL=(-150, -300), **GEND)
        sc.shadow(gx, GY + 312 + i * 40, 110, 16)
    ph = int(u * 10) % 2
    glow = [(260, 700, 700, (255, 50, 50) if ph else (60, 90, 255), .22), (820, 700, 700, (60, 90, 255) if ph else (255, 50, 50), .22)]
    if u < .35: pop_text(sc, "¡POLICÍA!", 540, 520, 190, t, 38.45 + .05, (255, 90, 80), t1=38.9, rot=5)
    return sc, sky_img([(0, (60, 28, 44)), (1, (110, 44, 60))], SS), dict(blur=0, grade=G_COOL, flash=(.5 if u < .06 else 0), glows=glow)

# --------------------------------------------------------------- 20. Guiño
@shot(40.04, 41.31, "guino")
def s20(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY - 455, 2.3), (1.27, 1000, GY - 470, 2.55)], .8, 20)
    sc = Scene(cx, cy, z, SS)
    w = clamp((u - .35) / .1)
    tip = clamp((u - .45) / .35)
    person2(sc.stage, 1000, GY + 60, 1.35, t, emo="happy", wink=w * (1 - clamp((u - 1.0) / .15)), look=(.3, 0), armR=(lerp(150, 62, eout(tip)), lerp(-250, -535, eout(tip))) if tip > 0 else None,
            hoff=-22 * elastic(clamp((u - .5) / .5)), **LUS)
    ub = ui(sc)
    if .5 < u < .9:
        p = (u - .5) / .4
        sparkle(ub, 590, 1020, 80 * math.sin(p * math.pi) + 6)
    return sc, sky_img([(0, (40, 12, 30)), (.5, (130, 34, 54)), (1, (60, 18, 40))], SS), dict(blur=0, grade=G_HOT, glows=[(540, 800, 420, (255, 180, 120), .22)])

# --------------------------------------------------------------- 21. Vendida
@shot(41.31, 43.73, "vendida")
def s21(t, u, SS):
    cx, cy, z = cam(u, [(0, 1000, GY - 350, .95), (2.42, 1000, GY - 800, .6)], .6, 21)
    sc = Scene(cx, cy, z, SS, shk(u, [(.85, 18)]))
    put(sc, "far", plate("far", "dusk"), .3)
    eiffel(sc.mid, 1000, GY, 2700, col=(120, 74, 100), hi=(255, 190, 140), f=1.0, lights=1.0)
    put(sc, "stage", plate("street", "dusk"), 1.0)
    person2(sc.stage, 1480, GY + 360, .9, t, emo="happy", armR=(140, -500 + math.sin(t * 8) * 30), hoff=-24, **LUS)
    briefcase(sc.stage, 1480 - 150 * .9 - 50, GY + 360 - 130, .6)
    sc.shadow(1480, GY + 372, 120, 18)
    if u > .85:
        s = elastic(clamp((u - .85) / .4))
        pop_text(sc, "VENDIDO", 540, 820, 300, t, 41.31 + .85, (226, 50, 56), t1=None, rot=-12, stroke=16)
    return sc, sky_for("dusk", SS), dict(blur=3, grade=G_HOT, flash=(.6 if .85 <= u < .93 else 0), glows=[(SUN_PX[0], SUN_PX[1], 340, (255, 150, 110), .25)])

# =============================================================== render
WHIPS = {4.43: 40, 6.80: 40, 11.70: 40, 14.14: 55, 15.53: 36, 20.10: 36, 22.40: 44, 25.40: 36, 27.90: 55}   # tiempo de corte -> intensidad
CAPFN = None
def shot_at(t):
    for i, (a, b, fn, nm) in enumerate(SHOTS):
        if a <= t < b: return i
    return len(SHOTS) - 1

def render(fi, SS=1.5):
    t = fi / FPS
    i = shot_at(t); a, b, fn, nm = SHOTS[i]
    sc, sky, meta = fn(t, t - a, SS)
    img = compose(sc, sky, blur=meta.get("blur", 0), shade=meta.get("shade", True))
    whip = 0.0
    for tb, k in WHIPS.items():
        dd = abs(t - tb)
        if dd < .09: whip = max(whip, k * (1 - dd / .09))
    img = finish(img, meta.get("grade", G_WARM), fi, whip, meta.get("flash", 0), meta.get("glows", ()))
    if CAPFN: img = CAPFN(img, t)
    return img

if __name__ == "__main__":
    import sys
    a = sys.argv[1:]
    SS = 1.0
    out = a[0]; ts = [float(x) for x in a[1:]]
    ims = [render(int(t * FPS), SS) for t in ts]
    sw, sh_ = 360, 640
    sheet = Image.new("RGB", (sw * len(ims), sh_))
    for k, im in enumerate(ims): sheet.paste(im.resize((sw, sh_), Image.LANCZOS), (k * sw, 0))
    sheet.save(out)
