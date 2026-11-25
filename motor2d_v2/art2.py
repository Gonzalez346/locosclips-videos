"""Personajes y atrezzo v2."""
import math, random
from PIL import Image, ImageDraw
from hscene import ellpts, rotp, lerp, clamp, mixc, INK, W, H
from kit2 import *

def shade(col, k): return tuple(int(clamp(v * k, 0, 255)) for v in col)

def ik(S, Hd, l1, l2, side):
    dx, dy = Hd[0] - S[0], Hd[1] - S[1]
    D = math.hypot(dx, dy) or 1e-3
    d = max(1e-3, min(D, l1 + l2 - 1))
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0, l1 * l1 - a * a))
    ux, uy = dx / D, dy / D
    best = None
    for b in (1, -1):
        e = (S[0] + ux * a - uy * b * h, S[1] + uy * a + ux * b * h)
        sc = side * (e[0] - (S[0] + Hd[0]) / 2) + .9 * (e[1] - (S[1] + Hd[1]) / 2)
        if best is None or sc > best[0]: best = (sc, e)
    return best[1]

def limb(c, pts, w, col, f=1.0, ow=7):
    c.line(pts, w + 2 * ow, INK, f); c.line(pts, w, col, f)

BUILD = {"slim": (80, 70, 68), "avg": (94, 90, 80), "portly": (106, 138, 104), "stout": (112, 124, 96)}

def person2(c, x, gy, s=1.0, t=0.0, build="avg", skin=(238, 192, 152), suit=(60, 72, 112), shirt=(246, 242, 228),
            tie=(176, 40, 52), hat=None, hatcol=(40, 36, 48), hair=(40, 30, 30), stache=None, glasses=False,
            emo="neutral", look=(0, 0), armL=None, armR=None, walk=None, flip=False, leg=1.0, vest=None,
            f=1.0, talk=0.0, blinkph=0.0, pants=None, shoe=(36, 28, 34), lean=0.0, hairstyle="slick", cravat=True,
            skirt=False, apron=None, badge=False, hoff=0.0, hrot=0.0, wink=0.0):
    """Devuelve dict con posiciones de las manos y la cabeza (mundo)."""
    d = -1 if flip else 1
    shw, bel, hip = BUILD[build]
    L = 175 * leg
    pants = pants or shade(suit, .92)
    ph = (walk if walk is not None else 0.0)
    bob = abs(math.sin(ph)) * 9 if walk is not None else math.sin(t * 2.1 + blinkph) * 2.2
    gy0 = gy
    gy = gy - bob * s
    def P(dx, dy, lx=0.0): return (x + (dx + lean * (-dy - L) * .0) * s * d + lean * s * max(0, -(dy + L)) * .22 * d * 0 + 0, gy + dy * s)
    def PL(dx, dy):  # con inclinación del torso
        k = lean * max(0.0, (-dy - L)) / 300.0
        return (x + (dx + k * 60) * s * d, gy + dy * s)
    hipY, shY = -L, -L - 175
    out = {}
    # ---- piernas
    for k in (-1, 1):
        lift = 0.0; sw = 0.0
        if walk is not None:
            v = math.sin(ph + (0 if k < 0 else math.pi)); lift = max(0, v) * 24; sw = v * 14
        hx = k * hip * .5; ax = k * (hip * .5 + 8) + sw
        ay = -24 - lift
        pts = [PL(hx - 33, hipY - 10), PL(hx + 33, hipY - 10), PL(ax + 27, ay), PL(ax - 27, ay)]
        c.poly(pts, pants, 7, f=f)
        # raya
        c.line([PL(hx, hipY + 10), PL(ax, ay - 4)], 3, shade(pants, .8), f)
        sx = ax + k * 8
        c.ell(*PL(sx, -14 - lift), 44 * s, 21 * s, shoe, 6, f=f)
        c.ell(*PL(sx - 8 * k, -22 - lift), 22 * s, 8 * s, shade(shoe, 1.7), 0, f=f)
    # ---- torso (chaqueta)
    sY = shY; hm = hipY + 36
    jk = [(-34, sY - 6), (34, sY - 6), (shw, sY + 20), (shw + 4, sY + 70), (bel + 4, hipY - 70), (hip + 6, hm), (-hip - 6, hm),
          (-bel - 4, hipY - 70), (-shw - 4, sY + 70), (-shw, sY + 20)]
    if skirt:
        jk = [(-34, sY - 6), (34, sY - 6), (shw, sY + 20), (shw + 4, sY + 70), (bel + 20, hipY - 20), (hip + 40, hm + 50), (-hip - 40, hm + 50), (-bel - 20, hipY - 20), (-shw - 4, sY + 70), (-shw, sY + 20)]
    c.poly([PL(*p) for p in jk], suit, 8, f=f)
    c.poly([PL(8, sY - 4), PL(shw, sY + 20), PL(shw + 4, sY + 70), PL(bel + 4, hipY - 70), PL(hip + 6, hm), PL(24, hm)], shade(suit, .84), 0, f=f)
    # camisa en V
    vy = sY + (150 if not vest else 150)
    c.poly([PL(-32, sY - 6), PL(32, sY - 6), PL(0, vy)], shirt, 5, f=f)
    if vest:
        c.poly([PL(-30, sY + 70), PL(30, sY + 70), PL(bel * .78, hipY - 30), PL(0, hipY + 4), PL(-bel * .78, hipY - 30)], vest, 5, f=f)
        c.poly([PL(-32, sY - 6), PL(32, sY - 6), PL(0, sY + 80)], shirt, 4, f=f)
    # corbata
    if cravat:
        c.poly([PL(-9, sY + 2), PL(9, sY + 2), PL(7, sY + 22), PL(-7, sY + 22)], tie, 4, f=f)
        c.poly([PL(-7, sY + 22), PL(7, sY + 22), PL(15, sY + 100), PL(0, sY + 122), PL(-15, sY + 100)], tie, 5, f=f)
        c.line([PL(0, sY + 40), PL(0, sY + 108)], 3, shade(tie, 1.4), f)
    # solapas
    lap = shade(suit, 1.22)
    c.poly([PL(-34, sY - 6), PL(-3, vy - 20), PL(-22, vy + 14), PL(-shw + 22, sY + 52), PL(-shw + 6, sY + 22)], lap, 5, f=f)
    c.poly([PL(34, sY - 6), PL(3, vy - 20), PL(22, vy + 14), PL(shw - 22, sY + 52), PL(shw - 6, sY + 22)], lap, 5, f=f)
    for by in (vy + 30, vy + 74):
        c.ell(*PL(0, by), 7 * s, 7 * s, shade(suit, .6), 3, f=f)
    c.line([PL(0, vy + 14), PL(0, hipY + 30)], 3, shade(suit, .75), f)
    if apron:
        c.poly([PL(-bel * .8, sY + 90), PL(bel * .8, sY + 90), PL(hip + 8, hm + 6), PL(-hip - 8, hm + 6)], apron, 6, f=f)
    # pañuelo de bolsillo
    c.poly([PL(-shw * .62, sY + 78), PL(-shw * .62 + 34, sY + 76), PL(-shw * .62 + 30, sY + 100), PL(-shw * .62 + 4, sY + 100)], (255, 250, 240), 4, f=f)
    if badge:
        c.ell(*PL(shw * .5, sY + 90), 15 * s, 15 * s, (240, 200, 80), 4, f=f)
    # ---- brazos
    sh_pts = {-1: PL(-shw + 10, sY + 40), 1: PL(shw - 10, sY + 40)}
    rest = {-1: PL(-shw - 26, sY + 230), 1: PL(shw + 26, sY + 230)}
    for k, arm in ((-1, armL), (1, armR)):
        S = sh_pts[k]
        if arm is None:
            sw = (math.sin(ph + (0 if k > 0 else math.pi)) * 30 * s) if walk is not None else math.sin(t * 1.7 + k) * 3 * s
            Hd = (rest[k][0] + sw * 0.2, rest[k][1] - abs(sw) * .3 + (sw if walk is not None else 0) * .6 * 0)
        else:
            Hd = (x + arm[0] * s, gy + arm[1] * s)
        bend = -k * d * (1 if True else 1)
        E = ik(S, Hd, 118 * s, 112 * s, k)
        limb(c, [S, E, Hd], 44 * s, suit, f)
        c.line([E, Hd], 3, shade(suit, .75), f)
        # puño
        cu = (Hd[0] + (E[0] - Hd[0]) * .12, Hd[1] + (E[1] - Hd[1]) * .12)
        c.ell(cu[0], cu[1], 21 * s, 21 * s, shirt, 4, f=f)
        c.ell(Hd[0], Hd[1], 22 * s, 22 * s, skin, 5, f=f)
        out["L" if k < 0 else "R"] = Hd
    # ---- cabeza
    neck = PL(0, sY - 6)
    hy = shY - 104; hxx = 0
    nx, ny = PL(0, hy + 70)
    c.poly([PL(-22, sY - 40), PL(22, sY - 40), PL(26, sY + 4), PL(-26, sY + 4)], shade(skin, .86), 5, f=f)
    hc = PL(hxx, hy)
    out["head"] = hc
    R = lambda dx, dy: PL(hxx + dx, hy + dy)
    c.ell(*R(-77, 6), 15 * s, 22 * s, skin, 5, f=f); c.ell(*R(77, 6), 15 * s, 22 * s, skin, 5, f=f)
    c.ell(hc[0], hc[1], 77 * s, 87 * s, skin, 7, f=f)
    # pelo
    if hair is not None and hat not in ("beret",):
        if hairstyle == "bald":
            pass
        else:
            top = [R(*p) for p in ellpts(0, -6, 80, 92, 18, 180, 360)]
            line = [R(70, -18), R(46, -46), R(8, -60), R(-30, -48), R(-70, -18)]
            if hairstyle == "slick":
                line = [R(70, -16), R(50, -44), R(14, -66), R(-18, -50), R(-40, -34), R(-70, -14)]
            c.poly(top + line, hair, 6, f=f)
            if hairstyle == "slick": c.line([R(-30, -60), R(0, -72), R(34, -66)], 3, shade(hair, 1.8), f)
    # sombrero
    hc2 = hatcol
    R0 = R
    R = lambda dx, dy: R0(dx, dy + hoff)
    if hat == "bowler":
        c.poly([R(*p) for p in ellpts(0, -50, 68, 70, 16, 180, 360)], hc2, 7, f=f)
        c.ell(*R(0, -48), 108 * s, 15 * s, hc2, 7, f=f)
        c.poly([R(-66, -52), R(66, -52), R(64, -64), R(-64, -64)], shade(hc2, 1.8), 4, f=f)
    elif hat == "top":
        c.ell(*R(0, -52), 112 * s, 16 * s, hc2, 7, f=f)
        c.poly([R(-62, -52), R(62, -52), R(56, -178), R(-56, -178)], hc2, 7, f=f)
        c.ell(*R(0, -178), 56 * s, 12 * s, shade(hc2, 1.25), 6, f=f)
        c.poly([R(-62, -56), R(62, -56), R(60, -80), R(-60, -80)], shade(hc2, 2.1), 4, f=f)
    elif hat == "fedora":
        c.ell(*R(0, -46), 118 * s, 20 * s, hc2, 7, f=f)
        c.poly([R(*p) for p in ellpts(0, -58, 66, 62, 16, 180, 360)], hc2, 7, f=f)
        c.poly([R(-65, -58), R(65, -58), R(62, -74), R(-62, -74)], (150, 40, 50), 4, f=f)
    elif hat == "kepi":
        c.poly([R(-72, -54), R(72, -54), R(60, -112), R(-60, -112)], hc2, 7, f=f)
        c.ell(*R(0, -112), 60 * s, 12 * s, shade(hc2, 1.2), 6, f=f)
        c.poly([R(-76, -52), R(76, -52), R(84, -34), R(-84, -34)], shade(hc2, .7), 6, f=f)
        c.poly([R(-72, -54), R(72, -54), R(70, -66), R(-70, -66)], (236, 196, 70), 4, f=f)
        c.ell(*R(0, -72), 11 * s, 11 * s, (236, 196, 70), 3, f=f)
    elif hat == "flat":
        c.poly([R(*p) for p in ellpts(0, -50, 80, 42, 16, 180, 360)], hc2, 7, f=f)
        c.poly([R(-70, -50), R(80, -50), R(86, -40), R(-60, -34)], shade(hc2, .8), 5, f=f)
    R = R0
    # cejas / ojos
    EM = {"neutral": (0, 0, 0), "happy": (-.15, 0, 0), "sly": (.3, .4, 0), "surprised": (-.5, 0, 0), "worried": (-.55, .1, 0),
          "angry": (.8, .1, 0), "smug": (.25, .25, 0), "focus": (.35, .0, 0)}
    bk, lidk, _ = EM.get(emo, EM["neutral"])
    blink = 0.0
    bt = (t + blinkph * 2.3) % 3.4
    if bt < .12: blink = 1 - abs(bt - .06) / .06
    for k in (-1, 1):
        ex, ey = 31 * k, -6
        big = 1.18 if emo == "surprised" else 1.0
        c.ell(*R(ex, ey), 19 * s * big, 23 * s * big, (255, 255, 255), 5, f=f)
        px = ex + look[0] * 7 * d; py = ey + look[1] * 8
        c.ell(*R(px, py), 9 * s, 10.5 * s, (30, 24, 40), 0, f=f)
        c.ell(*R(px - 3, py - 4), 3.2 * s, 3.2 * s, (255, 255, 255), 0, f=f)
        lid = max(blink, lidk)
        if wink and k == 1: lid = max(lid, wink)
        if lid > 0.02:
            yy = ey - 23 * big + 46 * big * lid
            c.poly([R(ex - 21, ey - 26), R(ex + 21, ey - 26), R(ex + 21, yy), R(ex - 21, yy)], skin, 0, f=f)
            c.line([R(ex - 20, yy), R(ex + 20, yy)], 4, INK, f)
        # cejas
        by = ey - 36 - (10 if emo in ("surprised", "worried") else 0) + (6 if emo == "angry" else 0)
        inner = by + bk * 14; outer = by - bk * 10 * (1 if emo != "worried" else -1)
        if emo == "worried": inner = by - 12; outer = by + 4
        c.line([R(ex - k * 20, outer), R(ex + k * 0 + 0, by - 3), R(ex + k * 20 * -1 * -1, inner)] if False else [R(k * 50, outer), R(k * 14, inner)], 7 * 1, shade(hair or (40, 30, 30), 1.0) if hair else INK, f)
        if glasses:
            c.line([R(*p) for p in ellpts(ex, ey, 27, 29, 20)], 4, (40, 40, 50), f)
    if glasses: c.line([R(-6, -8), R(6, -8)], 4, (40, 40, 50), f)
    # nariz
    c.ell(*R(3 * d, 24), 10 * s, 12 * s, shade(skin, .94), 3, f=f)
    # mejillas
    if emo in ("happy", "smug", "sly"):
        for k in (-1, 1): c.ell(*R(k * 52, 36), 16 * s, 10 * s, mixc(skin, (240, 120, 120), .35), 0, f=f)
    # boca
    mo = clamp(talk)
    my = 56
    if emo in ("happy",):
        c.poly([R(-30, my - 6), R(30, my - 6)] + [R(*p) for p in ellpts(0, my - 6, 30, 26 + 10 * mo, 12, 0, 180)][::-1], (120, 36, 46), 5, f=f)
        c.poly([R(-26, my - 5), R(26, my - 5), R(22, my + 4), R(-22, my + 4)], (252, 250, 245), 0, f=f)
    elif emo == "surprised":
        c.ell(*R(0, my + 6), 15 * s, 20 * s, (110, 30, 44), 5, f=f)
    elif emo == "worried":
        c.line([R(*p) for p in ellpts(0, my + 18, 24, 14, 12, 200, 340)], 6, INK, f)
    elif emo == "angry":
        c.poly([R(-24, my), R(24, my), R(20, my + 20), R(-20, my + 20)], (110, 30, 44), 5, f=f)
        c.poly([R(-20, my + 1), R(20, my + 1), R(18, my + 8), R(-18, my + 8)], (252, 250, 245), 0, f=f)
    elif emo in ("smug", "sly"):
        c.line([R(*p) for p in [(-22,my+8),(-8,my+12),(10,my+10),(24,my+2),(32,my-8)]], 6, INK, f)
        c.line([R(30,my-6),R(36,my-14)], 5, INK, f)
    else:
        if mo > .1:
            c.ell(*R(0, my + 4), 17 * s, (6 + 14 * mo) * s, (110, 30, 44), 5, f=f)
        else:
            c.line([R(-20, my + 4), R(0, my + 7), R(20, my + 4)], 6, INK, f)
    # bigote
    if stache == "thin":
        c.poly([R(-34, 42), R(0, 38), R(34, 42), R(32, 46), R(0, 43), R(-32, 46)], hair or INK, 3, f=f)
    elif stache == "big":
        c.poly([R(-46, 46), R(-20, 36), R(0, 40), R(20, 36), R(46, 46), R(34, 58), R(0, 48), R(-34, 58)], hair or INK, 4, f=f)
    elif stache == "handle":
        c.poly([R(-30, 40), R(0, 38), R(30, 40), R(52, 26), R(64, 14), R(56, 38), R(32, 54), R(0, 46), R(-32, 54), R(-56, 38), R(-64, 14), R(-52, 26)], hair or INK, 4, f=f)
    elif stache == "beard":
        c.poly([R(-66, 30)] + [R(*p) for p in ellpts(0, 36, 66, 62, 14, 0, 180)][::-1] + [R(66, 30)], hair or INK, 5, f=f)
    return out

# ------------------------------------------------------------------ atrezzo
def briefcase(c, x, y, s=1.0, col=(120, 64, 40), f=1.0, rot=0):
    pts = [(-70, -48), (70, -48), (70, 48), (-70, 48)]
    pts = [(x + px * s, y + py * s) for px, py in rotp(pts, rot, 0, 0)]
    c.poly(pts, col, 7, f=f)
    h = rotp([(-24, -48), (-24, -66), (24, -66), (24, -48)], rot, 0, 0)
    c.line([(x + a * s, y + b * s) for a, b in h], 8, INK, f)
    c.line([(x + a * s, y + b * s) for a, b in rotp([(-70, -4), (70, -4)], rot, 0, 0)], 4, shade(col, .65), f)
    c.ell(x, y - 4 * s, 12 * s, 9 * s, (240, 200, 80), 3, f=f)

def banknote(c, x, y, s=1.0, rot=0, f=1.0, col=(150, 205, 140)):
    pts = [(-46, -24), (46, -24), (46, 24), (-46, 24)]
    P = [(x + a * s, y + b * s) for a, b in rotp(pts, rot, 0, 0)]
    c.poly(P, col, 4, f=f)
    c.ell(x, y, 13 * s, 13 * s, shade(col, 1.2), 3, f=f)
    for k in (-1, 1): c.ell(x + k * 30 * s * math.cos(math.radians(rot)), y + k * 30 * s * math.sin(math.radians(rot)), 4 * s, 4 * s, shade(col, .6), 0, f=f)

def banknote_stack(c, x, y, s=1.0, f=1.0, n=3):
    for i in range(n):
        c.poly([(x - 56 * s, y - i * 18 * s), (x + 56 * s, y - i * 18 * s), (x + 56 * s, y - 18 * s - i * 18 * s), (x - 56 * s, y - 18 * s - i * 18 * s)], (150, 205, 140), 4, f=f)
        c.poly([(x - 20 * s, y - i * 18 * s), (x + 20 * s, y - i * 18 * s), (x + 20 * s, y - 18 * s - i * 18 * s), (x - 20 * s, y - 18 * s - i * 18 * s)], (236, 220, 150), 2, f=f)

def coin(c, x, y, r=26, f=1.0, sq=1.0):
    c.ell(x, y, r * sq, r, (246, 204, 70), 5, f=f)
    c.ell(x, y, r * .62 * sq, r * .62, (252, 226, 120), 0, f=f)

def envelope(c, x, y, s=1.0, rot=0, f=1.0, seal=(176, 40, 52)):
    pts = [(-70, -46), (70, -46), (70, 46), (-70, 46)]
    P = [(x + a * s, y + b * s) for a, b in rotp(pts, rot, 0, 0)]
    c.poly(P, (250, 242, 220), 6, f=f)
    fl = [(-70, -46), (0, 8), (70, -46)]
    c.poly([(x + a * s, y + b * s) for a, b in rotp(fl, rot, 0, 0)], (236, 222, 190), 5, f=f)
    sx, sy = rotp([(0, 8)], rot, 0, 0)[0]
    c.ell(x + sx * s, y + sy * s, 14 * s, 14 * s, seal, 3, f=f)

def bulb(c, x, y, s=1.0, f=1.0, on=1.0):
    col = mixc((230, 226, 200), (255, 238, 120), on)
    c.ell(x, y, 54 * s, 60 * s, col, 7, f=f)
    c.poly([(x - 26 * s, y + 50 * s), (x + 26 * s, y + 50 * s), (x + 24 * s, y + 96 * s), (x - 24 * s, y + 96 * s)], (170, 170, 184), 6, f=f)
    for i in range(3): c.line([(x - 24 * s, y + (62 + i * 12) * s), (x + 24 * s, y + (62 + i * 12) * s)], 4, (110, 110, 130), f)
    c.line([(x - 14 * s, y + 20 * s), (x - 6 * s, y - 8 * s), (x + 6 * s, y + 14 * s), (x + 14 * s, y - 8 * s)], 4, (240, 150, 40) if on > .5 else (150, 150, 150), f)

def rays(c, x, y, r0, r1, n, t, col=(255, 232, 120), w=10, f=1.0, spin=0.4):
    for i in range(n):
        a = i / n * 2 * math.pi + t * spin
        c.line([(x + math.cos(a) * r0, y + math.sin(a) * r0), (x + math.cos(a) * r1, y + math.sin(a) * r1)], w, col, f)

def newspaper(c, x, y, s=1.0, rot=0, f=1.0, head="LA TORRE"):
    pts = [(-110, -140), (110, -140), (110, 140), (-110, 140)]
    P = [(x + a * s, y + b * s) for a, b in rotp(pts, rot, 0, 0)]
    c.poly(P, (240, 232, 206), 6, f=f)
    rr = lambda a, b: (x + rotp([(a, b)], rot, 0, 0)[0][0] * s, y + rotp([(a, b)], rot, 0, 0)[0][1] * s)
    c.d.text(c.pt(*rr(0, -100), f), head, font=fnt(FONT_SERIF, 34 * s * c.z * c.SS), fill=(40, 30, 30), anchor="mm")
    c.line([rr(-90, -76), rr(90, -76)], 4, (60, 50, 50), f)
    for i in range(7):
        yy = -50 + i * 26
        c.line([rr(-90, yy), rr(-6, yy)], 5, (120, 110, 100), f)
        c.line([rr(10, yy), rr(90, yy)], 5, (120, 110, 100), f)
    c.poly([rr(10, -60), rr(90, -60), rr(90, -4), rr(10, -4)], (190, 178, 150), 3, f=f)

def gavel(c, x, y, s=1.0, rot=0, f=1.0):
    P = lambda pts: [(x + a * s, y + b * s) for a, b in rotp(pts, rot, 0, 0)]
    c.poly(P([(-8, -10), (8, -10), (8, 130), (-8, 130)]), (150, 96, 56), 5, f=f)
    c.poly(P([(-52, -50), (52, -50), (52, 10), (-52, 10)]), (120, 70, 44), 6, f=f)

def sign_post(c, x, gy, text, s=1.0, col=(176, 40, 52), tcol=(255, 250, 235), f=1.0, rot=0, px=70):
    c.poly([(x - 8 * s, gy), (x + 8 * s, gy), (x + 8 * s, gy - 330 * s), (x - 8 * s, gy - 330 * s)], (110, 76, 52), 5, f=f)
    P = [(x + a * s, gy - 330 * s + b * s) for a, b in rotp([(-170, -150), (170, -150), (170, 30), (-170, 30)], rot, 0, -60)]
    c.poly(P, col, 8, f=f)
    cx_ = sum(p[0] for p in P) / 4; cy_ = sum(p[1] for p in P) / 4
    c.d.text(c.pt(cx_, cy_, f), text, font=fnt(FONT_TITLE, px * s * c.z * c.SS), fill=tcol, anchor="mm")

def tower_model(c, x, y, s=1.0, tilt=0, f=1.0, col=(150, 110, 70)):
    """Maqueta pequeña de la torre (siluetas simples)."""
    pts = [(-70, 0), (-12, -300), (12, -300), (70, 0), (46, 0), (0, -120), (-46, 0)]
    P = [(x + a * s, y + b * s) for a, b in rotp(pts, tilt, 0, 0)]
    c.poly(P, col, 6, f=f)
    for yy, w in ((-110, 40), (-200, 22)):
        a = rotp([(-w, yy), (w, yy)], tilt, 0, 0)
        c.line([(x + p[0] * s, y + p[1] * s) for p in a], 7, shade(col, .6), f)

def sparkle(c, x, y, r, f=1.0, col=(255, 250, 200)):
    c.poly([(x, y - r), (x + r * .22, y - r * .22), (x + r, y), (x + r * .22, y + r * .22), (x, y + r), (x - r * .22, y + r * .22), (x - r, y), (x - r * .22, y - r * .22)], col, 0, f=f)

def poof(c, x, y, r, u, f=1.0, col=(255, 252, 244)):
    """Nube de polvo/humo en expansión (u 0..1)."""
    a = clamp(u)
    for i in range(7):
        ang = i / 7 * 6.283 + .4
        rr = r * (.4 + .9 * eout(a))
        c.ell(x + math.cos(ang) * rr * .8, y + math.sin(ang) * rr * .55, r * .5 * (1 - a * .5), r * .42 * (1 - a * .5), col, 0, f=f)
