"""Pickles: perro, copa, vitrina y atrezzo."""
import math, random
from PIL import Image, ImageDraw
from hscene import Ctx, ellpts, rotp, lerp, clamp, mixc, INK, W, H
from kit2 import *
from art2 import shade, sparkle, limb

DOGB = (46, 42, 56)
DOGW = (250, 248, 242)

def dog(c, x, gy, s=1.0, t=0.0, walk=None, flip=False, head=(0.0, 0.0), sit=0.0, emo="happy", mouth=0.0, tongue=False,
        wag=1.0, ears=0.0, hat=False, f=1.0, look=(0.0, 0.0), collar=(206, 52, 58), body_bob=True, sniff=0.0, outline_only=False):
    """Perro collie blanco y negro de perfil (mira a la derecha). Devuelve puntos clave (mundo)."""
    d = -1 if flip else 1
    tilt = -34 * sit
    piv = (-70, -105)
    bob = 0.0
    if walk is not None and body_bob: bob = -abs(math.sin(walk)) * 7
    elif sniff > 0: bob = math.sin(t * 22) * 2.5 * sniff
    def T(px, py, rot=True):
        if rot and tilt:
            (px, py), = rotp([(px, py)], tilt, *piv)
        return (x + px * s * d, gy + (py + bob) * s)
    out = {}
    # ---- patas
    def leg(top, foot, near, white=True):
        k = (top[0] + (foot[0] - top[0]) * .5, top[1] + (foot[1] - top[1]) * .5)
        colb = DOGB if near else shade(DOGB, .7)
        colw = DOGW if near else shade(DOGW, .82)
        limb(c, [top, k], 30 * s, colb, f, 6)
        limb(c, [k, foot], 24 * s, colw if white else colb, f, 6)
        c.ell(foot[0] + 8 * s * d, foot[1] - 4 * s, 19 * s, 11 * s, colw, 5, f=f)
    sw = lambda ph: (math.sin(walk + ph) if walk is not None else 0.0)
    lift = lambda ph: (max(0.0, math.cos(walk + ph)) * 16 if walk is not None else 0.0)
    legs = [  # (top local, phase, front?, near?)
        ((55, -112), math.pi, True, False), ((-62, -108), 0.0, False, False),
        ((70, -112), 0.0, True, True), ((-48, -108), math.pi, False, True)]
    for near_pass in (False, True):
        for (tl, ph, front, near) in legs:
            if near != near_pass: continue
            if sit > .5 and not front:
                thigh = T(tl[0] + 6, tl[1] + 18)
                c.ell(thigh[0], thigh[1], 46 * s, 40 * s, DOGB if near else shade(DOGB, .7), 6, f=f)
                fp = (x + (tl[0] + 48) * s * d, gy - 4 * s)
                c.ell(fp[0], fp[1], 24 * s, 11 * s, DOGW if near else shade(DOGW, .82), 5, f=f)
                continue
            top = T(*tl)
            fx = tl[0] + sw(ph) * 26 + (-12 if front and sit > .5 else 0)
            foot = (x + fx * s * d, gy - lift(ph) * s)
            if sit > .5 and front: foot = (x + (tl[0] + 4) * s * d, gy - 2 * s)
            leg(top, foot, near)
    # ---- cola
    wa = math.sin(t * 13 * wag) * 22 * clamp(wag)
    tp = [(-104, -142)]
    for i in range(1, 5):
        a = math.radians(176 + i * 17 + wa * (i / 4) - (14 if sit > .5 else 0))
        px_, py_ = tp[-1]
        tp.append((px_ + math.cos(a) * 24, py_ + math.sin(a) * 24))
    tw = [T(*p) for p in tp]
    limb(c, tw[:3], 34 * s, DOGB, f, 6)
    limb(c, tw[2:], 26 * s, DOGB, f, 6)
    c.ell(tw[-1][0], tw[-1][1], 17 * s, 15 * s, DOGW, 5, f=f)
    # ---- cuerpo
    body = [T(*p) for p in ellpts(-8, -128, 108, 50, 26)]
    c.poly(body, DOGB, 7, f=f)
    c.poly([T(*p) for p in ellpts(30, -100, 60, 24, 16, 0, 180)], DOGW, 0, f=f)
    # ---- cuello y cabeza
    nb = (62, -150)
    H0 = (nb[0] + 62 + head[0] * 1.0, nb[1] - 70 + head[1])
    Hd = T(*H0, rot=False) if tilt == 0 else (T(*nb)[0] + (62 + head[0]) * s * d, T(*nb)[1] + (-70 + head[1] - 0) * s)
    hx, hy = Hd
    out["head"] = Hd
    neck = [T(nb[0] - 34, nb[1] + 12), T(nb[0] + 30, nb[1] + 18), (hx + 10 * s * d, hy + 30 * s), (hx - 34 * s * d, hy + 4 * s)]
    c.poly(neck, DOGB, 7, f=f)
    c.poly([T(nb[0] + 8, nb[1] + 26), T(nb[0] + 34, nb[1] + 18), (hx + 14 * s * d, hy + 34 * s), (hx - 8 * s * d, hy + 30 * s)], DOGW, 0, f=f)
    zz = []
    a0 = T(nb[0] + 2, nb[1] + 22); a1 = T(80, -98)
    for i in range(9):
        u_ = i / 8
        px_ = lerp(a0[0], a1[0], u_); py_ = lerp(a0[1], a1[1], u_)
        off = (14 if i % 2 else -2) * s * d
        zz.append((px_ + off, py_))
    zz += [T(40, -96), T(30, -130)]
    c.poly(zz, DOGW, 0, f=f)
    # collar
    c.line([(hx - 30 * s * d, hy + 22 * s), (hx + 22 * s * d, hy + 40 * s)], 13 * s, collar, f)
    c.ell(hx + 2 * s * d, hy + 50 * s, 9 * s, 9 * s, (240, 200, 80), 3, f=f)
    P = lambda a, b: (hx + a * s * d, hy + b * s)
    # orejas
    perk = clamp(ears)
    for (ex, col_) in ((-28, shade(DOGB, .75)), (-6, DOGB)):
        tip = P(ex - 4 + 6 * perk, -86 - 16 * perk)
        c.poly([P(ex - 22, -30), P(ex + 18, -38), tip], col_, 6, f=f)
        if ex == -6:
            c.poly([P(ex - 10, -40), P(ex + 8, -44), (lerp(P(ex - 1, -42)[0], tip[0], .72), lerp(P(ex - 1, -42)[1], tip[1], .72))], (226, 150, 166), 0, f=f)
        if perk < .7:
            fold = P(ex + 10, -70 - 10 * perk)
            c.poly([tip, fold, P(ex + 2, -66 - 12 * perk)], shade(col_, 1.5), 4, f=f)
    # cabeza
    c.ell(hx, hy, 52 * s, 46 * s, DOGB, 7, f=f)
    c.poly([P(-50, 0), P(-62, 16), P(-44, 14), P(-52, 32), P(-34, 26), P(-36, 44), P(-18, 34), P(-6, 40)], DOGB, 6, f=f)
    # hocico blanco + franja
    c.poly([P(-6, -46), P(8, -46), P(20, 0), P(-4, 2)], DOGW, 0, f=f)
    c.ell(*P(46, 16), 42 * s, 26 * s, DOGW, 6, f=f)
    c.poly([P(-4, -44), P(10, -44), P(22, 4), P(8, 8)], DOGW, 0, f=f)
    nose = P(84, 6)
    out["nose"] = nose; out["mouth"] = P(70, 30)
    # boca
    mo = clamp(mouth)
    if mo > .05:
        c.poly([P(24, 26), P(86, 22), P(80, 22 + 34 * mo), P(34, 30 + 22 * mo)], (120, 34, 50), 5, f=f)
        if tongue or mo > .4: c.ell(*P(54, 34 + 20 * mo), 18 * s, 12 * s * (.6 + mo), (240, 120, 140), 4, f=f)
    elif tongue:
        c.line([P(30, 30), P(56, 34), P(78, 28)], 5, INK, f)
        c.poly([P(52, 32), P(68, 32), P(66, 58), P(54, 60)], (240, 120, 140), 4, f=f)
    else:
        c.line([P(30, 30), P(56, 34), P(80, 26)], 5, INK, f)
    c.ell(nose[0], nose[1], 14 * s, 11 * s, (24, 20, 28), 4, f=f)
    c.ell(nose[0] - 3 * s * d, nose[1] - 4 * s, 4 * s, 3 * s, (200, 200, 210), 0, f=f)
    # ojo
    big = 1.25 if emo in ("surprised", "alert") else 1.0
    e0 = P(18, -10)
    blink = ((t * 1.0 + .7) % 3.1) < .1 and emo not in ("surprised", "alert")
    if emo == "closed" or blink:
        c.line([P(6, -8), P(18, -2), P(30, -8)], 6, (250, 250, 250), f)
    else:
        c.ell(e0[0], e0[1], 17 * s * big, 19 * s * big, (255, 255, 255), 5, f=f)
        px_ = e0[0] + (look[0] * 6 + 3) * s * d; py_ = e0[1] + look[1] * 7 * s
        c.ell(px_, py_, 9 * s, 11 * s, (28, 22, 36), 0, f=f)
        c.ell(px_ - 3 * s * d, py_ - 4 * s, 3.4 * s, 3.4 * s, (255, 255, 255), 0, f=f)
        if emo == "sad":
            c.poly([P(-2, -34), P(36, -24), P(36, -14), P(-2, -16)], DOGB, 0, f=f)
        if emo == "happy":
            c.line([P(2, -2), P(18, 8), P(34, -2)], 4, DOGB, f) if False else None
    # ceja
    if emo == "alert": c.line([P(2, -40), P(34, -44)], 6, (250, 250, 250), f)
    elif emo == "sad": c.line([P(2, -30), P(34, -40)], 6, (250, 250, 250), f)
    else: c.line([P(4, -38), P(32, -40)], 5, (250, 250, 250), f)
    if hat:
        hp = P(-12, -40)
        c.poly([P(-44, -36), P(20, -48), P(-22, -136)], (90, 160, 230), 6, f=f)
        for k in range(3): c.line([P(-36 + k * 8, -60 - k * 22), P(4 + k * 3, -66 - k * 22)], 6, (255, 220, 80), f)
        c.ell(*P(-22, -138), 12 * s, 12 * s, (255, 120, 120), 4, f=f)
    return out

# ------------------------------------------------------------------ copa (trofeo alado)
GOLD = (242, 196, 62); GOLDL = (255, 236, 150); GOLDD = (176, 126, 36)

def trophy(c, x, gy, s=1.0, f=1.0, base_col=(46, 76, 170)):
    P = lambda a, b: (x + a * s, gy + b * s)
    # base octogonal azul
    c.poly([P(-62, 0), P(62, 0), P(56, -22), P(-56, -22)], shade(base_col, .8), 6, f=f)
    c.poly([P(-56, -22), P(56, -22), P(46, -96), P(-46, -96)], base_col, 6, f=f)
    c.poly([P(-20, -22), P(20, -22), P(16, -96), P(-16, -96)], shade(base_col, 1.25), 0, f=f)
    c.poly([P(-50, -96), P(50, -96), P(46, -110), P(-46, -110)], GOLD, 5, f=f)
    # cuerpo de la figura
    c.poly([P(-28, -110), P(28, -110), P(16, -200), P(22, -240), P(-22, -240), P(-16, -200)], GOLD, 6, f=f)
    c.line([P(-6, -116), P(-10, -226)], 5, GOLDL, f)
    c.line([P(10, -118), P(8, -228)], 4, GOLDD, f)
    # alas
    for k in (-1, 1):
        w = [P(k * 14, -214), P(k * 40, -238), P(k * 70, -290), P(k * 78, -340), P(k * 60, -318), P(k * 46, -290), P(k * 26, -250)]
        c.poly(w, GOLD, 6, f=f)
        for j in range(3): c.line([P(k * (30 + j * 12), -244 - j * 22), P(k * (52 + j * 9), -282 - j * 18)], 4, GOLDD, f)
    # brazos y copa
    for k in (-1, 1): c.line([P(k * 18, -232), P(k * 30, -276)], 14, GOLD, f)
    c.ell(*P(0, -250), 22 * s, 22 * s, GOLD, 6, f=f)
    c.poly([P(-50, -300), P(50, -300), P(36, -268), P(-36, -268)], GOLD, 6, f=f)
    c.poly([P(-36, -268), P(36, -268), P(10, -256), P(-10, -256)], GOLDD, 4, f=f)
    c.ell(*P(0, -300), 50 * s, 10 * s, GOLDL, 5, f=f)
    c.line([P(-30, -290), P(-22, -272)], 5, GOLDL, f)

def dashed(c, pts, w, col, dash=22, gap=14, f=1.0, closed=True):
    P = pts + ([pts[0]] if closed else [])
    acc = 0.0; on = True; cur = [P[0]]
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1]); pos = 0.0
        while pos < L:
            lim = (dash if on else gap) - acc
            step = min(lim, L - pos)
            pos += step; acc += step
            p = (a[0] + (b[0] - a[0]) * pos / L, a[1] + (b[1] - a[1]) * pos / L)
            if on: cur.append(p)
            if acc >= (dash if on else gap) - 1e-6:
                if on and len(cur) > 1: c.line(cur, w, col, f)
                on = not on; acc = 0.0; cur = [p]
    if on and len(cur) > 1: c.line(cur, w, col, f)

def trophy_ghost(c, x, gy, s=1.0, col=(240, 240, 255), f=1.0, w=6):
    P = lambda a, b: (x + a * s, gy + b * s)
    sil = [(-62, 0), (62, 0), (46, -96), (50, -110), (28, -110), (16, -200), (24, -232), (52, -290), (78, -340), (46, -300), (50, -300),
           (0, -312), (-50, -300), (-46, -300), (-78, -340), (-52, -290), (-24, -232), (-16, -200), (-28, -110), (-50, -110), (-46, -96)]
    dashed(c, [P(*p) for p in sil], w, col, 20, 14, f)

def dog_ghost(c, x, gy, s=1.0, col=(240, 240, 255), f=1.0, flip=False, w=6):
    d = -1 if flip else 1
    P = lambda a, b: (x + a * s * d, gy + b * s)
    sil = [(-60, 0), (-48, -60), (-112, -110), (-150, -190), (-118, -150), (-100, -168), (-30, -178), (60, -174), (90, -230), (100, -290),
           (124, -250), (150, -236), (206, -214), (190, -186), (130, -180), (110, -120), (88, -60), (90, 0), (60, 0), (52, -70), (-10, -76), (-26, 0)]
    dashed(c, [P(*p) for p in sil], w, col, 20, 14, f)

def glass_case(c, x, gy, s=1.0, f=1.0, ped=(92, 56, 44), h=430, w=190, lid=0.0):
    P = lambda a, b: (x + a * s, gy + b * s)
    c.poly([P(-130, 0), P(130, 0), P(120, -40), P(-120, -40)], shade(ped, .8), 7, f=f)
    c.poly([P(-110, -40), P(110, -40), P(110, -330), P(-110, -330)], ped, 7, f=f)
    c.poly([P(-80, -70), P(80, -70), P(80, -300), P(-80, -300)], shade(ped, 1.15), 5, f=f)
    c.poly([P(-130, -330), P(130, -330), P(130, -358), P(-130, -358)], (236, 196, 90), 6, f=f)
    return P(0, -358)

def glass_front(c, x, gy, s=1.0, f=1.0, h=430, w=190, lift=0.0, broken=False):
    P = lambda a, b: (x + a * s, gy + (b - lift) * s)
    y0 = -358
    pts = [P(-w / 2, y0), P(w / 2, y0), P(w / 2, y0 - h), P(-w / 2, y0 - h)]
    c.line(pts + [pts[0]], 7, (210, 236, 250), f)
    c.line([P(-w / 2 + 6, y0 - h + 6), P(w / 2 - 6, y0 - h + 6)], 4, (255, 255, 255), f)
    c.line([P(-w / 2 + 30, y0 - 60), P(-w / 2 + 90, y0 - h + 40)], 6, (240, 250, 255), f)
    c.line([P(-w / 2 + 54, y0 - 60), P(-w / 2 + 84, y0 - 140)], 4, (240, 250, 255), f)
    c.line([P(w / 2 - 40, y0 - 120), P(w / 2 - 20, y0 - 180)], 4, (240, 250, 255), f)
    c.poly([P(-w / 2 - 8, y0 - h), P(w / 2 + 8, y0 - h), P(w / 2 + 8, y0 - h - 18), P(-w / 2 - 8, y0 - h - 18)], (236, 196, 90), 5, f=f)

def stanchion(c, x, gy, s=1.0, f=1.0):
    c.poly([(x - 30 * s, gy), (x + 30 * s, gy), (x + 22 * s, gy - 14 * s), (x - 22 * s, gy - 14 * s)], (236, 196, 90), 5, f=f)
    c.poly([(x - 7 * s, gy - 14 * s), (x + 7 * s, gy - 14 * s), (x + 7 * s, gy - 240 * s), (x - 7 * s, gy - 240 * s)], (236, 196, 90), 5, f=f)
    c.ell(x, gy - 248 * s, 14 * s, 14 * s, (236, 196, 90), 5, f=f)

def rope(c, x0, x1, y, sag=50, f=1.0, col=(170, 30, 46)):
    pts = [(lerp(x0, x1, i / 12), y + math.sin(math.pi * i / 12) * sag) for i in range(13)]
    c.line(pts, 16, INK, f); c.line(pts, 10, col, f)

def magnifier(c, x, y, s=1.0, rot=-30, f=1.0):
    h = rotp([(0, 0), (0, 120)], rot, 0, 0)
    c.line([(x + h[0][0] * s, y + h[0][1] * s), (x + h[1][0] * s, y + h[1][1] * s)], 18 * s, (110, 70, 44), f)
    c.ell(x, y, 54 * s, 54 * s, (180, 220, 240), 9, f=f)
    c.line([(x - 26 * s, y - 20 * s), (x - 8 * s, y - 38 * s)], 6, (255, 255, 255), f)

def big_paper(c, x, y, s=1.0, rot=0.0, f=1.0, l1="¡ROBADA", l2="LA COPA!"):
    R = lambda a, b: (lambda p: (x + p[0] * s, y + p[1] * s))(rotp([(a, b)], rot, 0, 0)[0])
    c.poly([R(-230, -300), R(230, -300), R(230, 300), R(-230, 300)], (244, 238, 220), 8, f=f)
    c.poly([R(-200, -270), R(200, -270), R(200, -200), R(-200, -200)], (40, 36, 40), 0, f=f)
    S = c.SS * c.z * s
    def txt(a, b, t_, px, col):
        tmp = Image.new("RGBA", (int(460 * S), int(px * 1.6 * S)), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((230 * S, px * .8 * S), t_, font=fnt(FONT_TITLE, px * S), fill=col, anchor="mm")
        tmp = tmp.rotate(-rot, resample=Image.BICUBIC, expand=True)
        cx_, cy_ = c.pt(*R(a, b), f)
        c.img.alpha_composite(tmp, (int(cx_ - tmp.size[0] / 2), int(cy_ - tmp.size[1] / 2)))
    txt(0, -236, "LONDON NEWS", 50, (244, 238, 220))
    txt(0, -120, l1, 120, (30, 26, 30))
    txt(0, 10, l2, 120, (196, 36, 46))
    c.poly([R(-200, 90), R(-10, 90), R(-10, 250), R(-200, 250)], (200, 190, 168), 4, f=f)
    trophy(c, *R(-105, 236), .46 * s, f)
    for i in range(6):
        c.line([R(10, 100 + i * 28), R(200, 100 + i * 28)], 6, (140, 130, 120), f)

def calendar(c, x, y, day, month="MARZO 1966", s=1.0, f=1.0, flip=0.0):
    P = lambda a, b: (x + a * s, y + b * s)
    c.poly([P(-230, -280), P(230, -280), P(230, 280), P(-230, 280)], (250, 248, 240), 8, f=f)
    c.poly([P(-230, -280), P(230, -280), P(230, -150), P(-230, -150)], (206, 46, 56), 8, f=f)
    for k in (-1, 1): c.ell(*P(k * 120, -284), 18 * s, 18 * s, (60, 60, 70), 5, f=f)
    S = c.SS * c.z * s
    c.d.text(c.pt(*P(0, -214), f), month, font=fnt(FONT_TITLE, 70 * S), fill=(255, 250, 240), anchor="mm")
    c.d.text(c.pt(*P(0, 60), f), str(day), font=fnt(FONT_TITLE, 300 * S), fill=(40, 34, 44), anchor="mm")
    if flip > 0:
        a = flip
        pts = [P(-230, -150), P(230, -150), P(230 - 40 * a, -150 + 430 * (1 - a) - 300 * a), P(-230 + 60 * a, -150 + 430 * (1 - a) - 260 * a)]
        c.poly(pts, (236, 232, 222), 6, f=f)

def balloon(c, x, y, r, col, t, f=1.0, ph=0.0):
    yy = y + math.sin(t * 2 + ph) * 12
    c.line([(x, yy + r * 1.15), (x + math.sin(t * 3 + ph) * 12, yy + r * 1.15 + 140), (x, yy + r * 1.15 + 260)], 3, (90, 90, 100), f)
    c.ell(x, yy, r * .86, r, col, 6, f=f)
    c.poly([(x - 10, yy + r * 1.15), (x + 10, yy + r * 1.15), (x, yy + r * .96)], col, 4, f=f)
    c.ell(x - r * .3, yy - r * .4, r * .14, r * .22, shade(col, 1.5), 0, f=f)

CONF = [(240, 70, 80), (255, 210, 70), (80, 170, 240), (110, 210, 120), (250, 250, 250), (200, 110, 230)]
def confetti(c_ui, t, t0, n=70, seed=3, spread=1.0):
    r = random.Random(seed)
    u = t - t0
    if u < 0: return
    for i in range(n):
        x0 = r.uniform(-100, 1180); vy = r.uniform(240, 520); ph = r.uniform(0, 6.28)
        y = -60 + (u * vy + r.uniform(0, 1900)) % 2100 - 100 if u > 1.2 else -80 + u * vy * 1.5 + r.uniform(-600, 0) + 400
        x = x0 + math.sin(u * 3 + ph) * 50
        a = u * 6 + ph
        w = 14 * abs(math.cos(a)) + 3
        col = CONF[i % len(CONF)]
        c_ui.poly([(x - w, y - 7), (x + w, y - 7), (x + w, y + 7), (x - w, y + 7)], col, 0)

def stamp_mark(c, x, y, text, s, rot, col=(46, 160, 80), f=1.0):
    S = c.SS * c.z * s
    w = int(560 * S); h = int(200 * S)
    tmp = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], radius=int(26 * S), outline=col, width=int(16 * S))
    d.text((20 + w / 2, 20 + h / 2), text, font=fnt(FONT_TITLE, 140 * S), fill=col, anchor="mm")
    tmp = tmp.rotate(rot, resample=Image.BICUBIC, expand=True)
    px_, py_ = c.pt(x, y, f)
    c.img.alpha_composite(tmp, (int(px_ - tmp.size[0] / 2), int(py_ - tmp.size[1] / 2)))
