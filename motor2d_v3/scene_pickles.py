"""El perro que salvó el Mundial — 30 planos. 1080x1920 @ 30 fps."""
import math, random
import numpy as np
from PIL import Image, ImageDraw
from hscene import Ctx, ellpts, rotp, lerp, clamp, mixc, INK, W, H, FPS
from kit2 import *
from kit3 import *
from art2 import person2, shade, sparkle, briefcase, coin, rays, poof
from art3 import *
from env2 import Plate, put, GY, skyline_sil, clouds, street, lamp_post, tree_plane
from env3 import *

DUR = 52.3
NFR = int(round(DUR * FPS))

# ------------------------------------------------------------------ reparto
SK = [(240, 200, 164), (226, 176, 136), (206, 150, 112), (244, 210, 176), (176, 124, 92)]
THIEF = dict(build="slim", suit=(46, 46, 60), shirt=(226, 226, 232), tie=(46, 46, 60), hat="flat", hatcol=(36, 36, 48), hair=(40, 30, 30),
             stache=None, mask=True, skin=SK[0])
THIEF2 = dict(build="avg", suit=(60, 40, 50), shirt=(220, 220, 226), tie=(60, 40, 50), hat="flat", hatcol=(30, 30, 40), hair=(30, 24, 24),
              stache=None, mask=True, skin=SK[2])
BOBBY = dict(build="avg", suit=(30, 36, 72), hat="bobby", hatcol=(26, 30, 60), hair=(70, 50, 40), stache="big", skin=SK[3], plain=True,
             buttons=(214, 218, 230), collar=(26, 30, 60), cravat=False, pants=(26, 30, 60))
INSP = dict(build="slim", suit=(184, 156, 108), shirt=(240, 236, 226), tie=(130, 40, 46), hat="fedora", hatcol=(96, 76, 58), hair=(60, 44, 36),
            stache="thin", skin=SK[1], leg=1.08)
OWNER = dict(build="avg", suit=(120, 96, 70), shirt=(236, 232, 218), tie=(46, 70, 110), hat="flat", hatcol=(150, 130, 100), hair=(70, 46, 32),
             stache=None, skin=SK[0], vest=(200, 180, 140))
OFFS = [dict(build="portly", suit=(50, 56, 70), tie=(150, 30, 40), hat="bowler", hatcol=(30, 28, 36), hair=(80, 70, 60), stache="handle", skin=SK[3]),
        dict(build="slim", suit=(70, 64, 60), tie=(40, 60, 110), hat="top", hatcol=(30, 28, 36), hair=(150, 150, 160), stache="big", skin=SK[1], leg=1.1),
        dict(build="stout", suit=(90, 80, 96), tie=(200, 160, 60), hat="bowler", hatcol=(60, 44, 40), hair=(40, 30, 30), stache="beard", skin=SK[2], glasses=True)]
def PLAYER(hair=(80, 56, 36), skin=SK[0], stache=None, hairstyle="slick"):
    return dict(build="avg", suit=(246, 246, 246), shirt=(246, 246, 246), plain=True, collar=(200, 40, 52), shorts=(28, 36, 86),
                socks=(246, 246, 246), sleeves="short", hair=hair, skin=skin, stache=stache, hairstyle=hairstyle, cravat=False, hat=None)
PLAYERS = [PLAYER((60, 40, 30)), PLAYER((200, 160, 90), SK[3]), PLAYER((40, 30, 30), SK[2], "thin"), PLAYER((120, 70, 40), SK[1]), PLAYER((30, 24, 24), SK[4])]

# ------------------------------------------------------------------ cámara
def cam(t, keys, sway=1.0, seed=0):
    if t <= keys[0][0]: k = keys[0][1:]
    elif t >= keys[-1][0]: k = keys[-1][1:]
    else:
        for i in range(len(keys) - 1):
            if keys[i][0] <= t <= keys[i + 1][0]:
                u = (t - keys[i][0]) / (keys[i + 1][0] - keys[i][0]); u = u * u * (3 - 2 * u)
                k = tuple(lerp(keys[i][j], keys[i + 1][j], u) for j in (1, 2, 3)); break
    cx, cy, z = k
    cx += math.sin(t * 1.3 + seed) * 5 * sway / z; cy += math.sin(t * 1.9 + seed * 2) * 4 * sway / z
    return cx, cy, z

def shk(t, hits):
    sx = sy = 0.0
    for (th, a) in hits:
        u = t - th
        if 0 <= u < .6:
            e = math.exp(-u * 8) * a
            sx += math.sin(u * 55) * e; sy += math.cos(u * 47) * e * .8
    return (sx, sy)

def ui(sc): return Ctx(sc.fg.img, W / 2, H / 2, 1.0, sc.SS, (0, 0))
def pop(sc, text, x, y, px, t, t0, col=(255, 226, 70), t1=None, rot=0.0, stroke=11):
    title_text(ui(sc), text, x, y, px, t, t0, col, FONT_TITLE, stroke, t1, rot)
def ph(t, a, b): return clamp((t - a) / (b - a))

# ------------------------------------------------------------------ planchas
_P = {}
def plate(name):
    if name in _P: return _P[name]
    if name == "expo": _P[name] = Plate(lambda c: expo_room(c, 1000, GY), -900, 2900, -300, 2800, 1.15)
    elif name == "lon_far":
        def fn(c):
            clouds(c, 3, GY - 1700, GY - 1100, -1500, 3500, (250, 246, 240), 16)
            skyline_sil(c, -1500, 3500, GY - 30, 7, (176, 170, 186), 360, 700)
            big_ben(c, 430, GY - 40, 1500, (150, 140, 160))
        _P[name] = Plate(fn, -1500, 3500, -900, 1700, .8)
    elif name == "hall":
        def fn(c):
            terrace(c, -1500, 430, GY, 2); terrace(c, 1570, 3600, GY, 5)
            central_hall(c, 1000, GY)
        _P[name] = Plate(fn, -1500, 3600, -500, 1700, 1.0)
    elif name == "lstreet":
        def fn(c):
            street(c, -1500, 3600, GY)
            for x in (-400, 400, 1600, 2600): lamp_post(c, x, GY + 24, 1.0)
            phone_box(c, 1900, GY + 30, 1.0)
        _P[name] = Plate(fn, -1500, 3600, 700, 2900, 1.0)
    elif name == "terr":
        def fn(c):
            terrace(c, -1500, 3700, GY - 20, 3, lit=.0)
            hedge(c, -1500, 3700, GY, 150, (70, 120, 60), 7)
            for x in (-200, 900, 2000, 3100): tree_plane(c, x, GY - 10, 1.05, (78, 120, 66))
        _P[name] = Plate(fn, -1600, 3800, -500, 1700, 1.0)
    elif name == "lskyday":
        def fn(c):
            clouds(c, 9, GY - 1800, GY - 900, -1500, 3500, (255, 252, 246), 18)
            skyline_sil(c, -1500, 3600, GY - 120, 12, (186, 188, 204), 300, 560)
        _P[name] = Plate(fn, -1500, 3600, -900, 1700, .8)
    elif name in ("stad0", "stad1"):
        _P[name] = Plate(lambda c: stadium(c, 1000, GY, cheer=(name == "stad1")), -1300, 3300, -500, 1600, .95)
    elif name == "pitch": _P[name] = Plate(lambda c: pitch(c, 1000, GY), -1300, 3300, 1300, 2900, 1.0)
    elif name == "interrog": _P[name] = Plate(lambda c: interrog_room(c, 1000, GY), -900, 2900, -300, 2800, 1.1)
    elif name == "banquet": _P[name] = Plate(lambda c: banquet_room(c, 1000, GY), -900, 2900, -300, 2800, 1.1)
    elif name == "rio_far": _P[name] = Plate(lambda c: rio_far(c, 1000, GY), -1100, 3100, -900, 1700, .8)
    elif name == "rio_mid": _P[name] = Plate(lambda c: rio_mid(c, 1000, GY), -1100, 3100, -500, 2900, 1.0)
    elif name == "museum": _P[name] = Plate(lambda c: museum_room(c, 1000, GY), -900, 2900, -300, 2800, 1.1)
    return _P[name]

SKIES = {
    "expo": [(0, (20, 40, 38)), (1, (30, 56, 52))],
    "day": [(0, (96, 150, 214)), (.55, (170, 206, 236)), (1, (236, 238, 236))],
    "lon": [(0, (120, 150, 196)), (.5, (196, 210, 226)), (1, (246, 230, 206))],
    "stad": [(0, (70, 136, 220)), (.6, (160, 206, 240)), (1, (236, 240, 240))],
    "night": [(0, (10, 14, 40)), (.6, (30, 36, 80)), (1, (70, 60, 110))],
    "museum": [(0, (14, 18, 34)), (1, (24, 30, 52))],
}
def sky(name, SS, sun=None): return sky_img(SKIES[name], SS, sun)
def flat_sky(SS, top, bot): return sky_img([(0, top), (1, bot)], SS)

G_EXPO = dict(bloom=.55, tint=(1.04, 1.0, .93), contrast=1.08, grain=3, vig=1.5)
G_ALARM = dict(bloom=.5, tint=(1.08, .94, .92), contrast=1.1, grain=3, vig=1.5)
G_LON = dict(bloom=.3, tint=(1.02, 1.0, .98), contrast=1.04, grain=2.5, vig=1.05)
G_DAY = dict(bloom=.32, tint=(1.03, 1.01, .97), contrast=1.05, grain=2.5, vig=1.0)
G_PANIC = dict(bloom=.4, tint=(1.06, .97, .94), contrast=1.1, grain=3, vig=1.3)
G_STAD = dict(bloom=.45, tint=(1.05, 1.0, .94), contrast=1.06, grain=2.5, vig=.95)
G_INT = dict(bloom=.45, tint=(.97, 1.0, 1.04), contrast=1.08, grain=3.2, vig=1.6)
G_WARM = dict(bloom=.5, tint=(1.06, 1.0, .92), contrast=1.06, grain=2.5, vig=1.1)
G_NIGHT = dict(bloom=.55, tint=(.94, .98, 1.08), contrast=1.06, grain=3, vig=1.35)
G_SAD = dict(bloom=.45, tint=(.9, .96, 1.1), contrast=1.03, grain=3.5, vig=1.7, lift=-5, sat=.85)

SHOTS = []
def shot(t0, t1, name=""):
    def deco(fn):
        SHOTS.append((t0, t1, fn, name)); return fn
    return deco

# =================================================================== SET A: sala de exposición
CASE_X = 1000
TROPHY_S = .72
def thief_state(t):
    """posición, pose y manos del ladrón (tiempo absoluto)."""
    st = dict(x=1600, flip=False, walk=None, armL=None, armR=None, emo="sly", look=(-.6, 0), lean=0.0, vis=False)
    if t < 3.6 or t > 6.4: return st
    st["vis"] = True
    if t < 4.0:
        st["x"] = lerp(1650, 1190, eout(ph(t, 3.6, 4.0))); st["walk"] = t * 11; st["look"] = (-1, 0) if (t * 3) % 1 < .5 else (.4, 0)
    elif t < 4.72:
        st["x"] = 1190
        door = ph(t, 4.0, 4.2); reach = ph(t, 4.2, 4.42); lift = ph(t, 4.45, 4.7)
        if t < 4.2: st["armL"] = (-100 + 0, -370)
        elif t < 4.45: st["armL"] = (lerp(-100, -186, eout(reach)), lerp(-370, -400, eout(reach)))
        else: st["armL"] = (lerp(-186, -70, eout(lift)), lerp(-400, -330, eout(lift)))
        st["armR"] = (90, -260) if t < 4.45 else (60, -300)
        st["look"] = (-1, .3); st["emo"] = "sly" if t < 4.45 else "happy"
    else:
        st["flip"] = True
        r = ph(t, 4.78, 6.05)
        st["x"] = lerp(1190, -250, r ** 1.25); st["walk"] = t * 17; st["lean"] = -.45
        st["armR"] = (-70, -330); st["armL"] = (-30, -300); st["emo"] = "worried" if t > 5.2 else "happy"; st["look"] = (1, 0)
    return st

def door_open(t): return eout(ph(t, 4.0, 4.2)) if t >= 4.0 else 0.0

def glass_door(c, x, gy, k, s=1.0, h=330, w=170):
    y0 = gy - 358 * s
    xl = x - w / 2 * s
    ang = k * 75
    wx = w * s * math.cos(math.radians(ang))
    skew = 30 * s * math.sin(math.radians(ang))
    pts = [(xl, y0), (xl + wx, y0 + skew * .3), (xl + wx, y0 - h * s - skew * .3), (xl, y0 - h * s)]
    c.line(pts + [pts[0]], 7, (214, 238, 250))
    c.line([(xl + 26 * s, y0 - 50 * s), (xl + wx * .55, y0 - h * s + 40 * s)], 6, (240, 250, 255))
    c.line([(xl + 46 * s, y0 - 50 * s), (xl + wx * .4, y0 - 130 * s)], 4, (240, 250, 255))
    c.poly([(x - (w / 2 + 8) * s, y0 - h * s), (x + (w / 2 + 8) * s, y0 - h * s), (x + (w / 2 + 8) * s, y0 - (h + 18) * s), (x - (w / 2 + 8) * s, y0 - (h + 18) * s)], (236, 196, 90), 5)
    if k < .99:
        c.line([(x + w / 2 * s, y0), (x + w / 2 * s, y0 - h * s)], 6, (190, 220, 236))
    c.line([(xl, y0), (xl, y0 - h * s)], 7, (214, 238, 250))

def setA(sc, t, people=True, visitors=False, police=False):
    put(sc, "stage", plate("expo"), 1.0)
    S = sc.stage
    top = glass_case(S, CASE_X, GY + 40, 1.0)
    st = thief_state(t)
    have = t < 4.45
    out = {}
    if have: trophy(S, CASE_X, GY - 318, TROPHY_S)
    out["trophy"] = (CASE_X, GY - 318 - 120) if have else None
    glass_door(S, CASE_X, GY + 40, door_open(t))
    if st["vis"]:
        o = person2(S, st["x"], GY + 70, 1.0, t, walk=st["walk"], flip=st["flip"], armL=st["armL"], armR=st["armR"], emo=st["emo"],
                    look=st["look"], lean=st["lean"], **THIEF)
        sc.shadow(st["x"], GY + 80, 120, 18)
        if not have:
            hx, hy = o["R"] if st["flip"] else o["L"]
            trophy(S, hx, hy + 26, TROPHY_S)
            out["trophy"] = (hx, hy - 90)
        out["thief"] = o
    if police:
        bt = t
        mag = (150 + math.sin(bt * 2.2) * 60, -380 + math.cos(bt * 1.7) * 40)
        ob = person2(S, 760, GY + 150, 1.0, t, emo="focus", armR=mag, armL=(-130, -250), look=(.7, .2), lean=.25, **BOBBY)
        magnifier(S, ob["R"][0] + 30, ob["R"][1] - 60, .9, -30)
        sc.shadow(760, GY + 160, 120, 18)
        scr_arm = (-70, -560) if (t * 2.6) % 1 < .5 else (-50, -540)
        oi = person2(S, 1260, GY + 150, 1.0, t, emo="worried", armL=scr_arm, armR=(140, -230), look=(-.5, -.2), **INSP)
        sc.shadow(1260, GY + 160, 110, 18)
        out["bobby"] = ob; out["insp"] = oi
    for sx in (620, 1380): stanchion(S, sx, GY + 300, 1.0)
    rope(S, 620, 1380, GY + 300 - 244, 46)
    if visitors:
        for i, (vx, sp, d) in enumerate(((300, 70, OFFS[0]), (1650, -60, OFFS[1]))):
            x = vx + sp * t
            person2(sc.fgb, x, GY + 1100, 1.9, t, walk=t * 5 + i, flip=sp < 0, emo="neutral", **d)
    return out

def expo_meta(sc, t, alarm=False, tro=None):
    gl = []
    if tro:
        p = sc.scr(*tro); gl.append((p[0], p[1], 170 * sc.cam[2], (255, 214, 120), .32))
    if alarm and t > 4.85:
        on = (t * 4) % 1 < .5
        gl.append((540, 200, 700, (255, 40, 40), .38 if on else .12))
    return gl

@shot(0.00, 1.70, "hero")
def s01(t, u, SS):
    cx, cy, z = cam(t, [(0, 1000, GY - 450, 2.3), (1.7, 1000, GY - 500, 1.6)], .6, 1)
    sc = Scene3(cx, cy, z, SS)
    o = setA(sc, t)
    light_cone(sc, 1000, GY - 1700, 1000, GY + 60, 120, 360, .16)
    dust(sc.fg, t, 820, 1180, GY - 1100, GY - 200, 26, 3)
    for i in range(5):
        a = t * 1.7 + i * 1.3
        sparkle(sc.stage, 1000 + math.cos(a) * 110, GY - 470 + math.sin(a * 1.3) * 130, 10 + 16 * abs(math.sin(a * 2.1)))
    pop(sc, "1966", 540, 360, 300, t, .12, (255, 222, 90), 3.55)
    pop(sc, "LONDRES", 540, 590, 110, t, .42, (255, 255, 255), 3.55)
    p = sc.scr(1000, GY - 560)
    return sc, sky("expo", SS), dict(grade=G_EXPO, glows=expo_meta(sc, t, tro=o["trophy"]), streaks=[(p[0], p[1], 260, (255, 220, 150), .45 + .15 * math.sin(t * 3))])

@shot(1.70, 3.60, "sala")
def s02(t, u, SS):
    cx, cy, z = cam(t, [(1.7, 1000, GY - 560, .86), (3.6, 1000, GY - 560, 1.0)], .8, 2)
    sc = Scene3(cx, cy, z, SS)
    o = setA(sc, t, visitors=True)
    light_cone(sc, 1000, GY - 1700, 1000, GY + 60, 120, 380, .15)
    dust(sc.fg, t, 780, 1220, GY - 1300, GY - 200, 34, 4)
    pop(sc, "1966", 540, 360, 300, t, 0, (255, 222, 90), 3.55)
    pop(sc, "LONDRES", 540, 590, 110, t, 0, (255, 255, 255), 3.55)
    return sc, sky("expo", SS), dict(grade=G_EXPO, glows=expo_meta(sc, t, tro=o["trophy"]))

@shot(3.60, 4.20, "ojos")
def s03(t, u, SS):
    st = thief_state(t)
    hx = st["x"]
    cx, cy, z = cam(t, [(3.6, hx - 20, GY - 400, 2.5), (4.2, 1190 - 40, GY - 400, 2.65)], .5, 3)
    cx = lerp(hx, 1150, ph(t, 3.6, 4.0))
    sc = Scene3(cx, cy, z, SS)
    o = setA(sc, t)
    light_cone(sc, 1000, GY - 1700, 1000, GY + 60, 120, 380, .1)
    return sc, sky("expo", SS), dict(grade=dict(G_EXPO, tint=(.96, .98, 1.06), vig=1.8), glows=[])

@shot(4.20, 4.95, "manos")
def s04(t, u, SS):
    cx, cy, z = cam(t, [(4.2, 1080, GY - 360, 2.3), (4.95, 1110, GY - 390, 2.0)], .7, 4)
    sc = Scene3(cx, cy, z, SS, shk(t, [(4.47, 6)]))
    o = setA(sc, t)
    light_cone(sc, 1000, GY - 1700, 1000, GY + 60, 120, 380, .12)
    p = sc.scr(*(o["trophy"] or (1000, GY - 400)))
    return sc, sky("expo", SS), dict(grade=G_EXPO, glows=expo_meta(sc, t, tro=o["trophy"]), streaks=[(p[0], p[1], 200, (255, 220, 150), .5)] if t < 4.6 else [])

@shot(4.95, 6.05, "huida")
def s05(t, u, SS):
    st = thief_state(t)
    cx, cy, z = cam(t, [(4.95, 1050, GY - 420, 1.18), (6.05, 620, GY - 420, 1.05)], 1.6, 5)
    sc = Scene3(cx, cy, z, SS, shk(t, [(5.0, 8)]))
    o = setA(sc, t)
    sp = sc.scr(1000, GY - 1150)
    on = (t * 4) % 1 < .5
    sc.stage.ell(1000, GY - 1150, 40, 40, (255, 60, 60) if on else (150, 30, 40), 7)
    ray_burst(sc.fg.img, SS, sp[0], sp[1], 6, 900, t * 7, (255, 60, 60), .22 if on else .08, .16)
    pop(sc, "¡ROBADA!", 540, 430, 230, t, 5.05, (255, 70, 70), 6.05, rot=-6, stroke=12)
    return sc, sky("expo", SS), dict(grade=G_ALARM, glows=expo_meta(sc, t, True), flash=.45 if 4.95 <= t < 5.02 else 0)

@shot(8.35, 9.60, "lupa")
def s07(t, u, SS):
    cx, cy, z = cam(t, [(8.35, 760, GY - 330, 2.4), (9.6, 760, GY - 340, 2.7)], .6, 7)
    sc = Scene3(cx, cy, z, SS)
    S = sc.stage
    put(sc, "stage", plate("expo"), 1.0)
    glass_case(S, CASE_X, GY + 40, 1.0); glass_door(S, CASE_X, GY + 40, 1.0)
    ob = person2(S, 700, GY + 150, 1.0, t, emo="focus", armR=(150, -470), armL=(-130, -250), look=(.8, 0), **BOBBY)
    hx, hy = ob["head"]
    ex, ey = hx + 31, hy - 6
    mx = ex + math.sin(t * 2.4) * 14; my = ey + math.cos(t * 2.0) * 8
    S.line([(ob["R"][0], ob["R"][1]), (mx + 20, my + 50)], 16, (110, 70, 44))
    S.ell(mx, my, 62, 62, (196, 226, 240), 10)
    S.ell(mx, my, 46, 52, (255, 255, 255), 5)
    S.ell(mx + 14, my + 2, 22, 26, (40, 30, 60), 0)
    S.ell(mx + 6, my - 10, 8, 8, (255, 255, 255), 0)
    blink = ((t - 8.35) % 1.2) < .08
    if blink: S.poly([(mx - 48, my - 54), (mx + 48, my - 54), (mx + 48, my + 10), (mx - 48, my + 10)], SK[3], 0)
    S.line([(mx - 44, my - 64), (mx + 40, my - 74)], 10, (70, 50, 40))
    S.line([(mx - 34, my - 30), (mx - 16, my - 46)], 6, (255, 255, 255))
    light_cone(sc, 1000, GY - 1700, 1000, GY + 60, 120, 380, .08)
    return sc, sky("expo", SS), dict(grade=G_EXPO, glows=[])

@shot(9.60, 11.24, "pistas")
def s08(t, u, SS):
    cx, cy, z = cam(t, [(9.6, 1000, GY - 470, 1.12), (11.24, 1000, GY - 480, 1.25)], .8, 8)
    sc = Scene3(cx, cy, z, SS)
    o = setA(sc, t, police=True)
    light_cone(sc, 1000, GY - 1700, 1000, GY + 60, 120, 380, .14)
    trophy_ghost(sc.stage, CASE_X, GY - 318, TROPHY_S, (200, 220, 230), w=5)
    uc = ui(sc)
    hb = sc.scr(*o["bobby"]["head"]); hi = sc.scr(*o["insp"]["head"])
    qmark(uc, hi[0] + 40, hi[1] - 240, 160, t, 10.0, (255, 214, 64), 11.24)
    qmark(uc, hb[0] - 20, hb[1] - 250, 140, t, 10.35, (255, 214, 64), 11.24)
    qmark(uc, 540, 380, 260, t, 10.75, (255, 255, 255), 11.24)
    return sc, sky("expo", SS), dict(grade=G_EXPO, glows=[])

# =================================================================== SET B: Londres exterior
def setB(sc, t):
    put(sc, "far", plate("lon_far"), .35)
    put(sc, "mid", plate("hall"), .82)
    put(sc, "stage", plate("lstreet"), 1.0)
    S = sc.stage
    for i, (x0, sp, d) in enumerate(((600, 90, OFFS[1]), (1500, -70, OFFS[0]), (2100, -80, INSP))):
        x = x0 + sp * (t - 6.05)
        person2(S, x, GY + 160, .62, t, walk=t * 6 + i * 2, flip=sp < 0, emo="neutral", **d)
        sc.shadow(x, GY + 168, 70, 12)
    bx = lerp(2600, -500, ph(t, 6.05, 8.35))
    bus(S, bx, GY + 380, 1.0, wheel=-t * 9)
    sc.shadow(bx, GY + 390, 330, 26)
    lamp_post(sc.fgb, 1000 + (sc.cam[0] - 1000) * 1.0 - 600 / sc.cam[2], GY + 900, 2.3) if False else None
    birds = random.Random(4)
    for i in range(7):
        x = (birds.uniform(0, 1400) + (t - 6.05) * 180) % 1600 - 200 + sc.cam[0] - 540
        y = GY - 1300 + birds.uniform(-200, 200) + math.sin(t * 2 + i) * 14
        fl = math.sin(t * 15 + i * 2) * 12
        S.line([(x - 22, y - 6 + fl), (x, y), (x + 22, y - 6 + fl)], 5, (60, 56, 72))

@shot(6.05, 7.20, "londres")
def s06(t, u, SS):
    cx, cy, z = cam(t, [(6.05, 1350, GY - 1050, .9), (7.2, 1150, GY - 640, .86)], .8, 6)
    sc = Scene3(cx, cy, z, SS)
    setB(sc, t)
    pop(sc, "LONDRES", 540, 300, 230, t, 6.2, (255, 226, 90), 8.3)
    pop(sc, "MARZO DE 1966", 540, 480, 90, t, 6.45, (255, 255, 255), 8.3)
    return sc, sky("lon", SS, sun=(880, 520, 60, (255, 246, 214))), dict(grade=G_LON, blur=2.2, glows=[(880, 520, 300, (255, 220, 160), .2)])

@shot(7.20, 8.35, "hall")
def s06b(t, u, SS):
    cx, cy, z = cam(t, [(7.2, 1000, GY - 430, 1.02), (8.35, 1000, GY - 420, 1.22)], .8, 61)
    sc = Scene3(cx, cy, z, SS)
    setB(sc, t)
    pop(sc, "LONDRES", 540, 300, 230, t, 6.2, (255, 226, 90), 8.3)
    pop(sc, "MARZO DE 1966", 540, 480, 90, t, 6.45, (255, 255, 255), 8.3)
    return sc, sky("lon", SS, sun=(880, 520, 60, (255, 246, 214))), dict(grade=G_LON, blur=1.2, glows=[(880, 520, 300, (255, 220, 160), .2)])

# =================================================================== SET C: pánico
@shot(11.24, 12.30, "periodico")
def s09(t, u, SS):
    sc = Scene3(540, 960, 1.0, SS, shk(t, [(11.62, 16)]))
    ray_burst(sc.far.img, SS, 540, 820, 14, 1800, t * .5, (255, 120, 90), .35, .1)
    k = eback(ph(t, 11.24, 11.62), 1.6)
    rot = (1 - eout(ph(t, 11.24, 11.62))) * 540 - 6 + math.sin(t * 2) * 1.5
    big_paper(sc.stage, 540, 860 + math.sin(t * 2.2) * 8, 1.35 * max(.05, k), rot)
    for i in range(10):
        q = ph(t, 11.62 + i * .02, 12.3)
        if q > 0:
            a = i * .63
            x = 540 + math.cos(a) * 560 * eout(q); y = 860 + math.sin(a) * 760 * eout(q)
            sc.stage.poly([(x - 30, y - 20), (x + 30, y - 24), (x + 26, y + 20), (x - 28, y + 18)], (240, 234, 216), 4)
    return sc, flat_sky(SS, (120, 20, 30), (60, 10, 20)), dict(grade=G_PANIC, flash=.4 if 11.6 <= t < 11.67 else 0, glows=[(540, 860, 520, (255, 200, 150), .18)])

def office_floor(sc):
    sc.stage.poly([(-600, GY + 40), (1700, GY + 40), (1700, GY + 1200), (-600, GY + 1200)], (110, 74, 56), 0)
    for i in range(-6, 20): sc.stage.line([(i * 120 - 300, GY + 40), (i * 170 - 600, GY + 1200)], 3, (92, 62, 46))

@shot(12.30, 13.56, "panico")
def s09b(t, u, SS):
    cx, cy, z = cam(t, [(12.3, 540, GY - 360, 1.05), (13.56, 540, GY - 380, 1.2)], 3.0, 9)
    sc = Scene3(cx, cy, z, SS, shk(t, [(12.4, 6)]))
    ray_burst(sc.far.img, SS, 540, 700, 14, 1800, -t * .6, (255, 90, 70), .3, .1)
    office_floor(sc)
    for i, (x, d) in enumerate(((200, OFFS[0]), (540, OFFS[1]), (880, OFFS[2]))):
        ph_ = t * 9 + i * 2
        up = math.sin(ph_) > 0
        jy = -abs(math.sin(t * 7 + i)) * 40
        arms = ((-160, -560), (160, -520)) if up else ((-170, -500), (170, -560))
        o = person2(sc.stage, x + math.sin(t * 5 + i) * 30, GY + 150 + jy, .95, t, emo="surprised" if i != 1 else "worried",
                    armL=arms[0], armR=arms[1], walk=t * 14 + i, hoff=-30 * abs(math.sin(t * 8 + i)), **d)
        sc.shadow(x, GY + 160, 100, 14)
        hx, hy = o["head"]
        for j in range(2):
            q = ((t * 2.2 + j * .5 + i * .3) % 1.0)
            sc.stage.ell(hx + (60 if j else -66) + q * 20 * (1 if j else -1), hy - 30 + q * 90, 9, 13, (150, 210, 250), 3)
    pop(sc, "¡PÁNICO!", 540, 380, 230, t, 12.62, (255, 230, 80), 13.56, rot=5, stroke=12)
    return sc, flat_sky(SS, (150, 30, 40), (80, 14, 26)), dict(grade=G_PANIC)

# =================================================================== SET D: estadio sin copa
def setD(sc, t, cheer=False):
    put(sc, "mid", plate("stad1" if cheer else "stad0"), .9, dy=(-6 * abs(math.sin(t * 10)) if cheer else 0))
    put(sc, "stage", plate("pitch"), 1.0)

@shot(13.56, 14.90, "estadio")
def s10(t, u, SS):
    cx, cy, z = cam(t, [(13.56, 1000, GY - 900, .78), (14.9, 1000, GY - 260, .86)], .6, 10)
    sc = Scene3(cx, cy, z, SS)
    setD(sc, t)
    for i, (x, gy_) in enumerate(((620, GY + 330), (1380, GY + 330), (1000, GY + 420))):
        person2(sc.stage, x, gy_, 1.0 if i < 2 else 1.15, t, emo="happy", armL=(-150, -260), armR=(150, -260), **PLAYERS[i])
        sc.shadow(x, gy_ + 10, 110, 16)
    return sc, sky("stad", SS, sun=(860, 300, 60, (255, 250, 220))), dict(grade=G_STAD, blur=1.6, glows=[(860, 300, 300, (255, 230, 170), .2)])

@shot(14.90, 16.38, "sintrofeo")
def s10b(t, u, SS):
    cx, cy, z = cam(t, [(14.9, 1000, GY - 120, 1.2), (16.38, 1000, GY - 140, 1.38)], .7, 11)
    sc = Scene3(cx, cy, z, SS)
    setD(sc, t)
    lift = eback(ph(t, 14.95, 15.25), 1.8)
    look = ph(t, 15.5, 15.7)
    for i, x in enumerate((640, 1360)):
        shr = ph(t, 15.6, 15.8)
        person2(sc.stage, x, GY + 330, 1.0, t, emo="worried" if t > 15.6 else "happy", armL=(-170 - 40 * shr, -300 - 120 * shr), armR=(170 + 40 * shr, -300 - 120 * shr), look=(.6 if i == 0 else -.6, 0), **PLAYERS[i])
        sc.shadow(x, GY + 340, 110, 16)
    armY = lerp(-260, -600, lift) + 90 * look
    person2(sc.stage, 1000, GY + 420, 1.15, t, emo="happy" if t < 15.5 else "surprised", armL=(-110 + 30 * look, armY), armR=(110 - 30 * look, armY), look=(0, -1 if t > 15.1 else 0), **PLAYERS[2])
    sc.shadow(1000, GY + 430, 120, 18)
    uc = ui(sc)
    qmark(uc, 540, 420, 220, t, 15.62, (255, 255, 255), 16.38)
    pop(sc, "SIN TROFEO", 540, 640, 150, t, 15.45, (255, 80, 80), 16.38, rot=-4, stroke=12)
    return sc, sky("stad", SS, sun=(860, 300, 60, (255, 250, 220))), dict(grade=dict(G_STAD, sat=.92), blur=2.2)

# =================================================================== SET E: una semana
@shot(16.38, 18.12, "semana")
def s11(t, u, SS):
    sc = Scene3(540, 960, 1.0, SS)
    F = sc.far
    for i in range(-2, 20):
        F.poly([(i * 70, 0), (i * 70 + 34, 0), (i * 70 + 34, 1920), (i * 70, 1920)], (226, 206, 170), 0)
    # ventana con lluvia
    F.poly([(30, 220), (330, 220), (330, 860), (30, 860)], (240, 236, 224), 10)
    F.poly([(52, 242), (308, 242), (308, 838), (52, 838)], (118, 134, 160), 0)
    r = random.Random(2)
    for i in range(26):
        x = 60 + r.uniform(0, 230); y0 = r.uniform(0, 600); y = 250 + (y0 + t * 900) % 580
        F.line([(x, y), (x + 6, min(830, y + 40))], 3, (200, 214, 236))
    F.line([(180, 242), (180, 838)], 10, (240, 236, 224)); F.line([(52, 540), (308, 540)], 10, (240, 236, 224))
    # reloj
    F.ell(900, 340, 120, 120, (250, 246, 236), 9)
    for k in range(12):
        a = k / 12 * 6.283
        F.line([(900 + math.cos(a) * 96, 340 + math.sin(a) * 96), (900 + math.cos(a) * 108, 340 + math.sin(a) * 108)], 5, INK)
    ah = t * 9; am = t * 40
    F.line([(900, 340), (900 + math.cos(ah) * 56, 340 + math.sin(ah) * 56)], 10, INK)
    F.line([(900, 340), (900 + math.cos(am) * 88, 340 + math.sin(am) * 88)], 6, INK)
    F.poly([(0, 1460), (1080, 1460), (1080, 1920), (0, 1920)], (150, 104, 74), 0)
    s_ = 1.02 + .08 * ph(t, 16.38, 18.12)
    flips = [16.55 + i * .15 for i in range(7)]
    day = 20 + sum(1 for f_ in flips if t >= f_ + .07)
    calendar(sc.stage, 560, 850, day, s=s_)
    for f_ in flips:
        q = ph(t, f_, f_ + .3)
        if 0 < q < 1:
            a = eout(q)
            pts = [(560 - 230 * s_, 850 - 150 * s_), (560 + 230 * s_, 850 - 150 * s_)]
            yb = 850 + 280 * s_ - a * 900
            sc.stage.poly(pts + [(560 + 230 * s_ - 120 * a, yb - 60 * a), (560 - 230 * s_ + 40 * a, yb)], (244, 240, 230), 6)
    pop(sc, "+7 DÍAS", 560, 1300, 170, t, 17.5, (255, 226, 70), 18.12, rot=-5)
    return sc, flat_sky(SS, (226, 206, 170), (210, 190, 156)), dict(grade=G_WARM)

# =================================================================== SET F: el paseo y el hallazgo
DS = .85
HEDGE_X = 1480
def package(c, x, y, s=1.0, rot=0.0, tear=0.0, f=1.0):
    R = lambda a, b: (lambda p: (x + p[0] * s, y + p[1] * s))(rotp([(a, b)], rot, 0, 0)[0])
    c.poly([R(-100, -66), R(100, -60), R(104, 64), R(-96, 68)], (234, 228, 206), 7, f=f)
    c.poly([R(-84, -50), R(-10, -48), R(-10, -24), R(-84, -26)], (60, 56, 60), 0, f=f)
    for i in range(5):
        c.line([R(4, -46 + i * 16), R(86, -44 + i * 16)], 4, (150, 142, 130), f)
        c.line([R(-84, -6 + i * 14), R(-14, -4 + i * 14)], 4, (150, 142, 130), f)
    c.poly([R(14, 30), R(80, 32), R(80, 56), R(14, 54)], (200, 190, 168), 3, f=f)
    c.line([R(-98, 2), R(102, 0)], 6, (150, 104, 60), f); c.line([R(2, -64), R(0, 66)], 6, (150, 104, 60), f)
    c.ell(*R(0, 0), 10 * s, 8 * s, (150, 104, 60), 3, f=f)
    if tear > 0:
        k = clamp(tear)
        zz = [R(-100 + i * 20, (-6 if i % 2 else 6) * 1.0) for i in range(11)]
        top = [(p[0], p[1] - 14 * k * s) for p in zz]; bot = [(p[0], p[1] + 14 * k * s) for p in zz]
        c.poly(top + bot[::-1], GOLD, 0, f=f)
        c.line(top, 4, INK, f); c.line(bot, 4, INK, f)
        c.line([(p[0], p[1]) for p in zz[3:7]], 4, GOLDL, f)

def dog_state(t):
    st = dict(x=1330, flip=False, walk=None, head=(0, 0), sit=0.0, emo="happy", mouth=0.0, tongue=True, ears=0.0, look=(0, 0), sniff=0.0, wag=1.0, pkg=False)
    if t < 21.6:
        st["x"] = 1330 - (21.6 - t) * 230; st["walk"] = t * 13
        if 20.72 < t < 21.05: st["mouth"] = .9 * abs(math.sin((t - 20.72) * 18)); st["tongue"] = False
    elif t < 22.6:
        st["emo"] = "alert"; st["ears"] = eback(ph(t, 21.65, 21.8)); st["tongue"] = False; st["look"] = (.8, .5); st["wag"] = .3
    elif t < 24.78:
        k = eout(ph(t, 22.6, 22.9))
        st["x"] = lerp(1330, 1385, k); st["head"] = (40 * k + math.sin(t * 25) * 3 * k, 95 * k); st["sniff"] = k; st["tongue"] = False
        st["emo"] = "closed" if (t * 3) % 1 < .55 else "alert"; st["ears"] = .6; st["wag"] = 1.4
    elif t < 25.3:
        st["x"] = 1395; st["head"] = (44 + math.sin(t * 40) * 10, 90 + math.cos(t * 33) * 8); st["emo"] = "closed"; st["tongue"] = False; st["wag"] = 1.6
    elif t < 25.85:
        st["x"] = lerp(1395, 1300, eout(ph(t, 25.3, 25.85))); st["head"] = (lerp(40, 0, ph(t, 25.3, 25.6)), lerp(90, 10, ph(t, 25.3, 25.6)))
        st["pkg"] = True; st["tongue"] = False; st["emo"] = "happy"; st["walk"] = -t * 10
    elif t < 26.1:
        st["flip"] = True; st["x"] = lerp(1300, 1200, ph(t, 25.85, 26.1)); st["walk"] = t * 12; st["pkg"] = True; st["tongue"] = False
    else:
        st["flip"] = True; st["x"] = 1270; st["sit"] = eout(ph(t, 26.1, 26.35)); st["look"] = (0, -.9); st["emo"] = "happy"; st["wag"] = 1.6
        if 29.25 < t < 29.75: st["mouth"] = .9 * abs(math.sin((t - 29.25) * 14)); st["tongue"] = False
    return st

def man_state(t):
    st = dict(x=1000, walk=None, armL=None, armR=(120, -290), emo="happy", look=(.6, 0), lean=0.0, hoff=0.0, pkg=None, trophy=None)
    if t < 21.6:
        st["x"] = dog_state(t)["x"] - 330; st["walk"] = t * 8.6
    elif t < 23.0:
        st["lean"] = .3 * math.exp(-(t - 21.6) * 4) * math.sin((t - 21.6) * 9); st["emo"] = "neutral"; st["look"] = (.8, .3)
    elif t < 26.2:
        st["emo"] = "focus" if t < 25.4 else "surprised"; st["look"] = (.9, .3); st["lean"] = .25
    elif t < 28.85:
        st["armR"] = (60, -300); st["armL"] = (-60, -300); st["emo"] = "focus"; st["look"] = (0, .8)
        if t > 27.77:
            j = math.sin(t * 40) * 6 * ph(t, 27.77, 28.85)
            st["armR"] = (70 + 20 * ph(t, 27.9, 28.8) + j, -300); st["armL"] = (-70 - 20 * ph(t, 27.9, 28.8) - j, -300)
        st["pkg"] = (1000, GY + 176 - 300 - 10)
    else:
        lift = eback(ph(t, 28.9, 29.3), 1.6)
        st["armR"] = (lerp(70, 165, lift), lerp(-300, -520, lift)); st["armL"] = (lerp(-70, -110, lift), lerp(-300, -470, lift))
        st["emo"] = "surprised" if t < 29.9 else "happy"; st["look"] = (.6, -.6); st["trophy"] = True
    return st

def leash(c, a, b, sag=40):
    pts = [(lerp(a[0], b[0], i / 10), lerp(a[1], b[1], i / 10) + math.sin(math.pi * i / 10) * sag) for i in range(11)]
    c.line(pts, 7, (150, 40, 50))

def near_hedge(c, t, shake=0.0):
    hedge(c, HEDGE_X, 2600, GY + 176, 300, (64, 118, 56), 11, shake, t)

def fg_bushes(sc, t):
    c = sc.fgb; r = random.Random(5)
    for i in range(12):
        x = -400 + i * 380 + r.uniform(-60, 60)
        for j in range(3):
            c.ell(x + j * 90 - 90, GY + 740 - j % 2 * 40, 150, 120, (54, 96, 50), 0, f=1.45)

def setF(sc, t, hedge_front=None, bushes=False):
    put(sc, "far", plate("lskyday"), .3)
    put(sc, "mid", plate("terr"), .78)
    put(sc, "stage", plate("lstreet"), 1.0)
    S = sc.stage
    ds = dog_state(t); ms = man_state(t)
    if hedge_front is None: hedge_front = (24.78 <= t < 25.3)
    shake = 1.0 if 22.6 <= t < 25.4 else 0.0
    if not hedge_front: near_hedge(S, t, shake * (.4 if t < 24.78 else 1))
    out = {}
    mo = person2(S, ms["x"], GY + 176, 1.0, t, walk=ms["walk"], armL=ms["armL"], armR=ms["armR"], emo=ms["emo"], look=ms["look"], lean=ms["lean"], **OWNER)
    sc.shadow(ms["x"], GY + 186, 120, 18)
    out["man"] = mo
    do = dog(S, ds["x"], GY + 176, DS, t, walk=ds["walk"], flip=ds["flip"], head=ds["head"], sit=ds["sit"], emo=ds["emo"], mouth=ds["mouth"],
             tongue=ds["tongue"], ears=ds["ears"], look=ds["look"], sniff=ds["sniff"], wag=ds["wag"])
    sc.shadow(ds["x"] + (0 if not ds["flip"] else 0), GY + 186, 150, 16)
    out["dog"] = do
    if hedge_front: near_hedge(S, t, 1.0)
    if t < 24.78 or (25.85 <= t < 26.1) or t < 26.1:
        hx, hy = do["head"]; d = -1 if ds["flip"] else 1
        if t < 26.0:
            leash(S, mo["R"], (hx - 6 * DS * d, hy + 38 * DS), 50 if t < 21.6 else 24)
    if ds["pkg"]:
        mx, my = do["mouth"]; d = -1 if ds["flip"] else 1
        package(S, mx + 18 * d, my + 22, .5, -10 * d)
    if 26.1 <= t < 26.2:
        package(S, 1120, GY + 140, .5, 8)
    if ms["pkg"]:
        tear = ph(t, 27.95, 28.8)
        package(S, ms["pkg"][0], ms["pkg"][1], .82, math.sin(t * 3) * 2, tear)
        out["pkg"] = ms["pkg"]
    if ms["trophy"]:
        hx, hy = mo["R"]
        trophy(S, hx, hy + 30, TROPHY_S)
        out["trophy"] = (hx, hy - 90)
        # papeles volando
        for i in range(9):
            q = ph(t, 28.85, 29.9)
            if 0 < q < 1:
                a = i * .7 + .3
                x = 1000 + math.cos(a) * 520 * eout(q); y = GY - 140 + math.sin(a) * 380 * eout(q) + 300 * q * q
                S.poly([(x - 34, y - 22), (x + 30, y - 26), (x + 34, y + 20), (x - 30, y + 24)], (236, 230, 208), 4)
    if bushes: fg_bushes(sc, t)
    return out

def skyF(SS): return sky("day", SS, sun=(820, 360, 60, (255, 250, 226)))
GL_SUN = (820, 360, 280, (255, 232, 180), .18)

@shot(18.12, 20.52, "paseo")
def s12(t, u, SS):
    ds = dog_state(t); ms = man_state(t)
    mid = (ds["x"] + ms["x"]) / 2 + 30
    cx, cy, z = cam(t, [(18.12, mid, GY - 200, 1.18), (20.52, mid, GY - 200, 1.24)], .6, 12)
    cx = mid
    sc = Scene3(cx, cy, z, SS)
    setF(sc, t, bushes=True)
    return sc, skyF(SS), dict(grade=G_DAY, blur=2.4, glows=[GL_SUN])

@shot(20.52, 21.45, "pickles")
def s13(t, u, SS):
    ds = dog_state(t)
    hx = ds["x"] + 105; hy = GY + 176 - 190
    sc = Scene3(hx - 40, hy + 30, 2.05, SS)
    setF(sc, t)
    lowerthird(ui(sc), "PICKLES", "El perro protagonista", t, 20.58, 21.42, y=300)
    return sc, skyF(SS), dict(grade=G_DAY, blur=4.5, glows=[GL_SUN])

@shot(21.45, 22.46, "alerta")
def s14(t, u, SS):
    z = lerp(1.25, 1.95, eout(ph(t, 21.62, 21.76)))
    cx, cy = 1330 + 60, GY - 60
    sc = Scene3(cx, cy, z, SS, shk(t, [(21.7, 7)]))
    setF(sc, t)
    do_head = dog(Scene3(cx, cy, z, .1).stage, 1330, GY + 176, DS, t, emo="alert")["head"] if False else None
    hp = sc.scr(1330 + 105, GY + 176 - 230)
    if t > 21.62: speed_lines(ui(sc), t, hp[0], hp[1], 30, 380, 1500, 1.0) if t < 21.95 else None
    exclaim(ui(sc), hp[0] + 20, hp[1] - 190, 1.3, t, 21.74)
    return sc, skyF(SS), dict(grade=G_DAY, blur=3.5, glows=[GL_SUN], flash=.25 if 21.72 <= t < 21.78 else 0)

@shot(22.46, 23.60, "olfato")
def s15(t, u, SS):
    cx, cy, z = cam(t, [(22.46, 1560, GY + 20, 2.6), (23.6, 1575, GY + 30, 2.9)], .5, 15)
    sc = Scene3(cx, cy, z, SS)
    o = setF(sc, t)
    nx, ny = o["dog"]["nose"]
    uc = ui(sc); p = sc.scr(nx, ny)
    k = (t * 4.5) % 1.0
    for j in range(3):
        a = -.9 + j * .45
        r0 = 40 + 60 * k
        uc.line([(p[0] - math.cos(a) * r0 * 1.0 + 30, p[1] + math.sin(a) * r0), (p[0] - math.cos(a) * (r0 + 40) + 30, p[1] + math.sin(a) * (r0 + 40))], 8, (255, 255, 255))
    title_text(uc, "SNIFF", p[0] - 150, p[1] - 220, 130, t, 22.6, (255, 255, 255), FONT_TITLE, 9, 23.1, 0)
    title_text(uc, "SNIFF", p[0] + 40, p[1] - 360, 130, t, 23.0, (255, 255, 255), FONT_TITLE, 9, 23.6, 0)
    for i in range(6):
        q = ((t * 1.3 + i * .17) % 1.0)
        uc.ell(p[0] + 60 + i * 20 + q * 90, p[1] - 40 - q * 260 + math.sin(q * 9 + i) * 20, 12, 7, (90, 150, 70), 4)
    return sc, skyF(SS), dict(grade=G_DAY, blur=5.5, glows=[GL_SUN])

@shot(23.60, 24.78, "dueño")
def s16(t, u, SS):
    cx, cy, z = cam(t, [(23.6, 1090, GY - 250, 1.85), (24.78, 1100, GY - 260, 2.0)], .6, 16)
    sc = Scene3(cx, cy, z, SS)
    o = setF(sc, t)
    hp = sc.scr(*o["man"]["head"])
    qmark(ui(sc), hp[0] + 150, hp[1] - 170, 150, t, 23.85, (255, 214, 64), 24.78, rot=0)
    return sc, skyF(SS), dict(grade=G_DAY, blur=4.5, glows=[GL_SUN])

@shot(24.78, 26.20, "paquete")
def s17(t, u, SS):
    cx, cy, z = cam(t, [(24.78, 1280, GY - 180, 1.45), (26.2, 1200, GY - 200, 1.35)], .8, 17)
    sc = Scene3(cx, cy, z, SS, shk(t, [(25.3, 5)]))
    o = setF(sc, t)
    if 24.78 < t < 25.35:
        uc = ui(sc)
        for i in range(10):
            q = ((t * 2.6 + i * .1) % 1.0)
            p = sc.scr(1640 + math.cos(i) * 60, GY + 40)
            uc.ell(p[0] + math.cos(i * 2.3) * 300 * q, p[1] - math.sin(i * 1.1 + .4) * 300 * q - 200 * q + 400 * q * q, 14, 9, (90, 150, 70), 4)
    if t > 25.35: pop(sc, "¡UN PAQUETE!", 540, 380, 140, t, 25.4, (255, 255, 255), 26.2, rot=-3)
    return sc, skyF(SS), dict(grade=G_DAY, blur=3.0, glows=[GL_SUN])

@shot(26.20, 27.77, "periodicos")
def s18(t, u, SS):
    cx, cy, z = cam(t, [(26.2, 1010, GY - 170, 2.0), (27.77, 1005, GY - 165, 2.3)], .6, 18)
    sc = Scene3(cx, cy, z, SS)
    setF(sc, t)
    return sc, skyF(SS), dict(grade=G_DAY, blur=5.0, glows=[GL_SUN])

@shot(27.77, 28.70, "rasgar")
def s19(t, u, SS):
    cx, cy, z = cam(t, [(27.77, 1000, GY - 140, 2.7), (28.7, 1000, GY - 135, 3.0)], .5, 19)
    sc = Scene3(cx, cy, z, SS, shk(t, [(28.3, 3)]))
    o = setF(sc, t)
    p = sc.scr(1000, GY - 134)
    if t > 28.1:
        k = ph(t, 28.1, 28.7)
        ray_burst(sc.fg.img, SS, p[0], p[1], 10, 500 + 400 * k, t, (255, 230, 150), .22 * k, .07)
    return sc, skyF(SS), dict(grade=G_DAY, blur=5.5, glows=[(p[0], p[1], 160, (255, 214, 120), .35 * ph(t, 28.1, 28.7))])

@shot(28.70, 30.74, "revelacion")
def s20(t, u, SS):
    cx, cy, z = cam(t, [(28.7, 1100, GY - 330, 1.5), (29.0, 1110, GY - 360, 1.22), (30.74, 1110, GY - 380, 1.34)], .8, 20)
    sc = Scene3(cx, cy, z, SS, shk(t, [(28.88, 12)]))
    o = setF(sc, t)
    gl = [GL_SUN]; streaks = []
    if "trophy" in o:
        p = sc.scr(*o["trophy"])
        ray_burst(sc.mid.img, SS, p[0], p[1], 18, 1700, t * .5, (255, 236, 160), .45, .09)
        gl.append((p[0], p[1], 220, (255, 214, 120), .45)); streaks.append((p[0], p[1], 320, (255, 230, 160), .7))
        for i in range(7):
            a = t * 1.8 + i * .9
            sparkle(ui(sc), p[0] + math.cos(a) * 170, p[1] + math.sin(a * 1.2) * 170, 12 + 18 * abs(math.sin(a * 2)))
    pop(sc, "¡LA COPA!", 540, 1290, 220, t, 29.15, (255, 222, 80), 30.74, rot=-4, stroke=12)
    return sc, skyF(SS), dict(grade=G_WARM, blur=3.0, glows=gl, streaks=streaks, flash=.55 if 28.85 <= t < 28.95 else 0)

# =================================================================== SET G: comisaría
def setG(sc, t, mode="sospecha"):
    put(sc, "stage", plate("interrog"), 1.0)
    S = sc.stage
    ang = 10 * math.sin(t * 1.9)
    bulb = hanging_lamp(S, 1000, GY - 1700, 1000, ang)
    ok = t >= 34.95
    if not ok:
        ia = (260, -360 + math.sin(t * 6) * 10) if t > 31.8 else (180, -260)
        if t > 33.78: ia = (90, -330)
        oi = person2(S, 720, GY + 190, 1.0, t, emo="angry" if t < 33.78 else "focus", armR=ia, armL=(-150, -250) if t < 33.78 else (40, -330),
                     lean=.35 if t < 33.78 else 0, look=(.8, 0) if t < 33.78 else (.3, .6), talk=abs(math.sin(t * 11)) * .7 if 31.9 < t < 33.5 else 0, **INSP)
        if t > 33.78:
            S.poly([(oi["L"][0] - 10, oi["L"][1] - 70), (oi["L"][0] + 60, oi["L"][1] - 80), (oi["L"][0] + 66, oi["L"][1] + 10), (oi["L"][0] - 4, oi["L"][1] + 20)], (246, 242, 226), 5)
            for i in range(4): S.line([(oi["L"][0] + 4, oi["L"][1] - 50 + i * 16), (oi["L"][0] + 50, oi["L"][1] - 56 + i * 16)], 3, (120, 120, 140))
        om = person2(S, 1290, GY + 190, 1.0, t, emo="worried", armL=(-90, -250), armR=(90, -250), look=(-.7, 0), **OWNER)
    else:
        sh = ph(t, 35.05, 35.35)
        bob = math.sin(t * 18) * 10 * sh
        oi = person2(S, 720, GY + 190, 1.0, t, emo="happy", armR=(lerp(90, 275, sh), lerp(-330, -300, sh) + bob), armL=(-150, -250), look=(.8, 0), **INSP)
        om = person2(S, 1290, GY + 190, 1.0, t, emo="happy", armL=(lerp(-90, -285, sh), lerp(-250, -300, sh) + bob), armR=(90, -250), look=(-.8, 0), **OWNER)
    sc.shadow(720, GY + 200, 120, 18); sc.shadow(1290, GY + 200, 120, 18)
    table(S, 1000, GY + 190, 660, 240)
    trophy(S, 1000, GY - 50, .52)
    jump = abs(math.sin((t - 35.1) * 9)) * 60 if ok and t > 35.1 else 0
    dog(S, 1120, GY + 190 - jump, .62, t, sit=1.0 if not jump else 0, emo="happy" if ok else "sad", tongue=ok, mouth=(.8 * abs(math.sin(t * 12)) if ok and t > 35.1 else 0),
        ears=0.0, look=(0, -.5) if not ok else (0, 0), wag=1.6 if ok else .2, flip=True)
    if not ok and t > 31.9:
        hx, hy = om["head"]
        for j in range(3):
            q = ((t * 1.6 + j * .33) % 1.0)
            S.ell(hx + (-70 if j % 2 else 72) + (j - 1) * 6, hy - 50 + q * 120, 10, 15, (150, 210, 250), 3)
    return dict(bulb=bulb, man=om, insp=oi)

def lamp_glow(sc, o):
    p = sc.scr(*o["bulb"])
    light_cone(sc, o["bulb"][0], o["bulb"][1] + 10, 1000, GY + 260, 30, 520, .13, (255, 240, 190))
    return [(p[0], p[1], 120 * sc.cam[2], (255, 230, 160), .5)]

@shot(30.74, 32.30, "comisaria")
def s21(t, u, SS):
    cx, cy, z = cam(t, [(30.74, 1000, GY - 280, 1.25), (32.3, 1000, GY - 290, 1.38)], .7, 21)
    sc = Scene3(cx, cy, z, SS)
    o = setG(sc, t)
    gl = lamp_glow(sc, o)
    pop(sc, "¿FUISTE TÚ?", 540, 330, 180, t, 31.95, (255, 226, 70), 33.78, rot=4)
    return sc, sky("expo", SS), dict(grade=G_INT, glows=gl)

@shot(32.30, 33.78, "sudor")
def s22(t, u, SS):
    cx, cy, z = cam(t, [(32.3, 1240, GY - 260, 2.0), (33.78, 1250, GY - 270, 2.25)], .5, 22)
    sc = Scene3(cx, cy, z, SS)
    o = setG(sc, t)
    gl = lamp_glow(sc, o)
    pop(sc, "¿FUISTE TÚ?", 540, 330, 180, t, 31.95, (255, 226, 70), 33.78, rot=4)
    return sc, sky("expo", SS), dict(grade=dict(G_INT, vig=1.9), glows=gl)

@shot(33.78, 36.00, "verdad")
def s23(t, u, SS):
    cx, cy, z = cam(t, [(33.78, 1000, GY - 280, 1.28), (36.0, 1000, GY - 290, 1.4)], .7, 23)
    sc = Scene3(cx, cy, z, SS, shk(t, [(34.97, 14)]))
    o = setG(sc, t)
    gl = lamp_glow(sc, o)
    if t > 34.9:
        k = eout(ph(t, 34.9, 35.02))
        stamp_mark(ui(sc), 560, 520, "VERDAD", lerp(2.6, 1.0, k), -10, (60, 190, 90))
    return sc, sky("expo", SS), dict(grade=dict(G_INT, tint=(1.0, 1.02, 1.0)) if t > 34.95 else G_INT, glows=gl, flash=.35 if 34.95 <= t < 35.02 else 0)

# =================================================================== SET H: final del Mundial
def setH(sc, t, lift_t=38.5):
    cheer = int(t * 30 / 5) % 2 == 0 or t > lift_t
    setD(sc, t, cheer=cheer)
    S = sc.stage
    up = t > lift_t
    for i, (x, gy_) in enumerate(((560, GY + 300), (760, GY + 330), (1240, GY + 330), (1440, GY + 300))):
        j = abs(math.sin(t * 8 + i)) * 70 if up else 0
        arms = ((-160, -560), (160, -560)) if up else (((-40, -330), (40, -330)) if (t * 4 + i) % 1 < .5 else ((-150, -300), (150, -300)))
        person2(S, x, gy_ - j, .95, t, emo="happy", armL=arms[0], armR=arms[1], look=(-.6 if x > 1000 else .6, -.3), **PLAYERS[(i + 1) % 5])
        sc.shadow(x, gy_ + 8, 100, 14, .4 if j else .55)
    k = eback(ph(t, lift_t, lift_t + .35), 1.5)
    if t < lift_t:
        o = person2(S, 1000, GY + 420, 1.15, t, emo="happy", armR=(150, -300), armL=(-150, -300), **PLAYERS[0])
        hx, hy = o["R"]; tro = (hx, hy - 90)
        trophy(S, hx, hy + 30, .62)
    else:
        ay = lerp(-330, -650, k)
        o = person2(S, 1000, GY + 420, 1.15, t, emo="happy", armL=(-60, ay), armR=(60, ay), look=(0, -.6), **PLAYERS[0])
        hy = (o["L"][1] + o["R"][1]) / 2
        trophy(S, 1000, hy + 30, .62)
        tro = (1000, hy - 80)
    sc.shadow(1000, GY + 430, 130, 18)
    return dict(trophy=tro)

@shot(36.00, 37.70, "final")
def s24(t, u, SS):
    cx, cy, z = cam(t, [(36.0, 1000, GY - 1350, .9), (37.7, 1000, GY - 220, .92)], .6, 24)
    sc = Scene3(cx, cy, z, SS)
    o = setH(sc, t)
    pop(sc, "30 DE JULIO", 540, 300, 170, t, 36.2, (255, 226, 70), 37.7)
    pop(sc, "1966", 540, 470, 130, t, 36.4, (255, 255, 255), 37.7)
    return sc, sky("stad", SS, sun=(860, 300, 60, (255, 250, 220))), dict(grade=G_STAD, blur=1.6, glows=[(860, 300, 300, (255, 230, 170), .22)])

@shot(37.70, 39.72, "campeones")
def s25(t, u, SS):
    cx, cy, z = cam(t, [(37.7, 1000, GY - 150, 1.0), (38.5, 1000, GY - 180, 1.12), (39.72, 1000, GY - 230, 1.32)], .8, 25)
    sc = Scene3(cx, cy, z, SS, shk(t, [(38.52, 10)]))
    o = setH(sc, t)
    p = sc.scr(*o["trophy"])
    gl = [(860, 300, 300, (255, 230, 170), .22), (p[0], p[1], 200, (255, 214, 120), .45)]
    st = [(p[0], p[1], 300, (255, 230, 160), .7)] if t > 38.5 else []
    if t > 38.5:
        ray_burst(sc.mid.img, SS, p[0], p[1], 18, 1800, t * .4, (255, 240, 170), .3, .08)
        confetti(ui(sc), t, 38.5, 90, 5)
    pop(sc, "¡CAMPEONES!", 540, 1260, 190, t, 38.6, (255, 226, 70), 39.72, rot=-5, stroke=12)
    return sc, sky("stad", SS, sun=(860, 300, 60, (255, 250, 220))), dict(grade=G_STAD, blur=2.2, glows=gl, streaks=st, flash=.4 if 38.5 <= t < 38.58 else 0)

# =================================================================== SET I: banquete
def setI(sc, t):
    put(sc, "stage", plate("banquet"), 1.0)
    S = sc.stage
    for i, (bx, col) in enumerate(((420, (230, 60, 70)), (600, (70, 140, 230)), (1420, (250, 210, 70)), (1600, (230, 60, 70)))):
        balloon(S, bx, GY - 980 + (i % 2) * 90, 70, col, t, ph=i)
    for i, x in enumerate((560, 760, 1240, 1440)):
        clap = (t * 5 + i * .3) % 1 < .5
        if i == 3:
            o = person2(S, x, GY + 170, .92, t, emo="happy", armR=(120, -560), armL=(-140, -300), **PLAYERS[i])
            trophy(S, o["R"][0], o["R"][1] + 26, .5)
        else:
            person2(S, x, GY + 170, .92, t, emo="happy", armL=(-30, -330) if clap else (-150, -320), armR=(30, -330) if clap else (150, -320), look=(.5 if x < 1000 else -.5, 0), **PLAYERS[i])
    # silla del perro
    S.poly([(900, GY - 120), (1100, GY - 120), (1090, GY - 470), (910, GY - 470)], (130, 70, 50), 7)
    S.poly([(930, GY - 440), (1070, GY - 440), (1066, GY - 160), (934, GY - 160)], (170, 40, 56), 5)
    lick = 41.1 < t < 42.53
    lk = abs(math.sin(t * 9))
    d = dog(S, 940, GY - 120, 1.0, t, sit=1.0, hat=True, emo="closed" if lick and lk > .5 else "happy", tongue=True,
            mouth=(.35 + .3 * lk) if lick else 0, head=(10, 40 + 16 * lk) if lick else (0, 0), wag=1.6)
    table(S, 1000, GY + 170, 1160, 300, cloth=(250, 248, 242))
    for px_ in (620, 1380):
        S.ell(px_, GY - 120, 80, 18, (250, 250, 250), 5)
        S.line([(px_ - 4, GY - 160), (px_ - 4, GY - 210)], 5, (210, 210, 220))
    S.ell(1100, GY - 118, 96, 20, (250, 250, 250), 6)
    S.ell(1100, GY - 120, 60, 11, (236, 230, 220), 3)
    for k in (-1, 1):
        balloon(sc.fgb, 1000 + k * 700, GY - 300, 120, (230, 60, 70) if k < 0 else (70, 140, 230), t, ph=k)
    return dict(dog=d)

@shot(39.72, 41.10, "banquete")
def s26(t, u, SS):
    cx, cy, z = cam(t, [(39.72, 1000, GY - 380, 1.05), (41.1, 1000, GY - 400, 1.18)], .7, 26)
    sc = Scene3(cx, cy, z, SS)
    setI(sc, t)
    confetti(ui(sc), t, 39.2, 50, 7)
    return sc, flat_sky(SS, (232, 214, 170), (232, 214, 170)), dict(grade=G_WARM, glows=[(540, 300, 600, (255, 220, 160), .2)])

@shot(41.10, 42.53, "slurp")
def s26b(t, u, SS):
    cx, cy, z = cam(t, [(41.1, 1060, GY - 210, 2.2), (42.53, 1065, GY - 205, 2.45)], .6, 27)
    sc = Scene3(cx, cy, z, SS)
    setI(sc, t)
    confetti(ui(sc), t, 39.2, 40, 9)
    title_text(ui(sc), "¡SLURP!", 760, 420, 150, t, 41.35, (255, 255, 255), FONT_TITLE, 11, 42.53, 0)
    return sc, flat_sky(SS, (232, 214, 170), (232, 214, 170)), dict(grade=G_WARM, glows=[(540, 300, 600, (255, 220, 160), .2)])

# =================================================================== SET J: años después
@shot(42.53, 43.92, "anos")
def s27(t, u, SS):
    sc = Scene3(540, 960, 1.0, SS)
    ray_burst(sc.far.img, SS, 540, 760, 16, 1800, t * 1.5, (150, 170, 230), .35, .1)
    F = sc.stage
    r = random.Random(3)
    for i in range(10):
        q = ((t - 42.53) * 1.3 + i * .1) % 1.0
        x = -100 + q * 1300; y = r.uniform(200, 1700) + math.sin(q * 7 + i) * 60
        a = q * 400 + i * 30
        pts = rotp([(-60, -80), (60, -80), (60, 80), (-60, 80)], a, 0, 0)
        F.poly([(x + px_, y + py_) for px_, py_ in pts], (246, 242, 230), 5)
    F.ell(540, 720, 270, 270, (250, 246, 236), 12)
    for k in range(12):
        a = k / 12 * 6.283
        F.line([(540 + math.cos(a) * 220, 720 + math.sin(a) * 220), (540 + math.cos(a) * 248, 720 + math.sin(a) * 248)], 8, INK)
    ah = t * 14; am = t * 70
    F.line([(540, 720), (540 + math.cos(ah) * 130, 720 + math.sin(ah) * 130)], 18, INK)
    F.line([(540, 720), (540 + math.cos(am) * 200, 720 + math.sin(am) * 200)], 10, INK)
    F.ell(540, 720, 18, 18, INK, 0)
    yr = 1966 + int(round(17 * eout(ph(t, 42.65, 43.55))))
    bump = 1.0 + .1 * (1 - ((t * 20) % 1)) if t < 43.55 else 1.0
    F.d.text((540 * SS, 1190 * SS), str(yr), font=fnt(FONT_TITLE, 300 * bump * SS), fill=(255, 222, 90), anchor="mm", stroke_width=int(14 * SS), stroke_fill=INK)
    return sc, flat_sky(SS, (40, 50, 100), (20, 26, 60)), dict(grade=dict(G_NIGHT, bloom=.4), speed=None)

# =================================================================== SET K: Brasil 1983
@shot(43.92, 46.75, "brasil")
def s28(t, u, SS):
    tx = lerp(250, 2100, ph(t, 43.95, 46.3))
    cx, cy, z = cam(t, [(43.92, 600, GY - 150, 1.15), (46.75, 1800, GY - 180, 1.2)], 1.0, 28)
    sc = Scene3(cx, cy, z, SS)
    put(sc, "far", plate("rio_far"), .3)
    put(sc, "mid", plate("rio_mid"), .8)
    o = person2(sc.stage, tx, GY + 400, 1.05, t, walk=t * 16, emo="happy", armR=(80, -330), armL=(-130, -300), lean=.45, look=(1, 0), **THIEF2)
    trophy(sc.stage, o["R"][0], o["R"][1] + 26, TROPHY_S)
    sc.shadow(tx, GY + 410, 120, 16)
    for i in range(4):
        ps = sc.scr(-200 + i * 700, GY + 380)
    p = sc.scr(o["R"][0], o["R"][1] - 90)
    pop(sc, "¡OTRA VEZ!", 540, 380, 200, t, 45.05, (255, 90, 80), 45.85, rot=-5, stroke=12)
    pop(sc, "BRASIL, 1983", 540, 380, 170, t, 45.9, (120, 220, 120), 46.75, rot=3)
    return sc, sky("night", SS), dict(grade=G_NIGHT, blur=2.6, glows=[(p[0], p[1], 160, (255, 214, 120), .35), (860, 330, 300, (220, 220, 255), .18)])

# =================================================================== SET L: el museo vacío
def setL(sc, t):
    put(sc, "stage", plate("museum"), 1.0)
    S = sc.stage
    glass_case(S, CASE_X, GY + 40, 1.0, ped=(70, 56, 64))
    glass_door(S, CASE_X, GY + 40, 0.0)
    a = clamp(ph(t, 47.0, 47.5) - ph(t, 48.1, 48.6))
    if a > 0: trophy_ghost(S, CASE_X, GY - 318, TROPHY_S, mixc((40, 50, 80), (226, 234, 255), a), w=6)
    light_cone(sc, 1000, GY - 1700, 1000, GY + 60, 110, 380, .16, (220, 230, 255))
    dust(sc.fg, t, 760, 1240, GY - 1400, GY, 40, 6, (230, 236, 255))
    on2 = t > 49.25 and not (49.32 < t < 49.38)
    if on2:
        S.poly([(1560 + px_, GY + 60 + py_) for px_, py_ in ellpts(0, 0, 300, 70, 26)], (60, 66, 92), 0)
        light_cone(sc, 1560, GY - 1700, 1560, GY + 60, 100, 330, .13, (220, 230, 255))
        b = clamp(ph(t, 50.85, 51.15) - ph(t, 51.6, 51.95))
        if b > 0: dog_ghost(S, 1540, GY + 50, .95, mixc((50, 58, 90), (226, 234, 255), b), w=7)
    return on2

@shot(46.75, 48.88, "vacia")
def s29(t, u, SS):
    cx, cy, z = cam(t, [(46.75, 1000, GY - 470, 1.25), (48.88, 1000, GY - 470, 1.5)], .4, 29)
    sc = Scene3(cx, cy, z, SS)
    setL(sc, t)
    p = sc.scr(1000, GY - 450)
    return sc, sky("museum", SS), dict(grade=G_SAD, glows=[(p[0], p[1], 260 * sc.cam[2], (200, 214, 255), .12)], fade=1 - ph(t, 46.75, 47.1))

@shot(48.88, 52.30, "sinperro")
def s30(t, u, SS):
    cx, cy, z = cam(t, [(48.88, 1250, GY - 460, 1.0), (52.3, 1280, GY - 480, .86)], .4, 30)
    sc = Scene3(cx, cy, z, SS)
    on2 = setL(sc, t)
    p = sc.scr(1000, GY - 450); p2 = sc.scr(1560, GY - 200)
    gl = [(p[0], p[1], 240, (200, 214, 255), .12)]
    if on2: gl.append((p2[0], p2[1], 220, (200, 214, 255), .1))
    return sc, sky("museum", SS), dict(grade=G_SAD, glows=gl, fade=ph(t, 51.95, 52.3))
