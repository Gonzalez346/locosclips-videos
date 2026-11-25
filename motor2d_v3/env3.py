"""Escenarios: Londres 1966, sala de exposición, estadio, comisaría, banquete, Río de noche, museo vacío."""
import math, random
from PIL import Image
from hscene import Ctx, ellpts, rotp, lerp, clamp, mixc, INK, W, H
from kit2 import *
from art2 import shade, sparkle
from art3 import *
from env2 import Plate, put, GY, skyline_sil, clouds, tree_plane, street

def terrace(c, x0, x1, gy, seed=1, bricks=((172, 86, 66), (160, 96, 74), (184, 104, 80)), lit=0.0):
    r = random.Random(seed); x = x0; i = 0
    doors = [(30, 60, 110), (170, 40, 50), (40, 110, 80), (230, 190, 70), (30, 30, 40)]
    while x < x1:
        w = 300; br = bricks[i % len(bricks)]
        c.poly([(x, gy), (x + w, gy), (x + w, gy - 640), (x, gy - 640)], br, 6)
        for k in range(12):
            yy = gy - 40 - k * 50
            for j in range(3):
                bx = x + 20 + ((k % 2) * 40 + j * 100 + r.uniform(0, 20)) % (w - 50)
                c.line([(bx, yy), (bx + 34, yy)], 3, shade(br, .82))
        # tejado + chimenea
        c.poly([(x - 6, gy - 640), (x + w + 6, gy - 640), (x + w - 30, gy - 740), (x + 30, gy - 740)], (92, 96, 112), 6)
        cx_ = x + w - 60
        c.poly([(cx_ - 30, gy - 700), (cx_ + 30, gy - 700), (cx_ + 30, gy - 810), (cx_ - 30, gy - 810)], shade(br, .9), 5)
        for k in (-14, 14): c.poly([(cx_ + k - 8, gy - 810), (cx_ + k + 8, gy - 810), (cx_ + k + 6, gy - 846), (cx_ + k - 6, gy - 846)], (190, 110, 80), 3)
        # ventana de arriba
        for wx in (x + 70, x + 200):
            c.poly([(wx - 46, gy - 360), (wx + 46, gy - 360), (wx + 46, gy - 540), (wx - 46, gy - 540)], (250, 248, 240), 6)
            c.poly([(wx - 36, gy - 370), (wx + 36, gy - 370), (wx + 36, gy - 530), (wx - 36, gy - 530)], (255, 226, 150) if r.random() < lit else (150, 184, 206), 0)
            c.line([(wx - 36, gy - 450), (wx + 36, gy - 450)], 6, (250, 248, 240))
            c.poly([(wx - 54, gy - 354), (wx + 54, gy - 354), (wx + 54, gy - 340), (wx - 54, gy - 340)], (236, 232, 224), 4)
        # mirador
        c.poly([(x + 20, gy - 20), (x + 170, gy - 20), (x + 160, gy - 280), (x + 30, gy - 280)], (250, 248, 240), 6)
        for k in range(3):
            wx = x + 44 + k * 44
            c.poly([(wx, gy - 70), (wx + 34, gy - 70), (wx + 34, gy - 250), (wx, gy - 250)], (255, 226, 150) if r.random() < lit else (150, 184, 206), 3)
        c.poly([(x + 14, gy - 280), (x + 176, gy - 280), (x + 160, gy - 300), (x + 30, gy - 300)], (236, 232, 224), 4)
        # puerta
        dc = doors[(seed + i) % len(doors)]
        c.poly([(x + 200, gy - 20), (x + 270, gy - 20), (x + 270, gy - 250), (x + 200, gy - 250)], dc, 6)
        c.poly([(x + 200, gy - 250), (x + 270, gy - 250), (x + 235, gy - 290)], (250, 248, 240), 4)
        c.ell(x + 258, gy - 130, 6, 6, (240, 200, 80), 2)
        c.poly([(x + 190, gy), (x + 280, gy), (x + 280, gy - 20), (x + 190, gy - 20)], (220, 216, 206), 4)
        x += w; i += 1

def hedge(c, x0, x1, gy, h=240, col=(74, 128, 62), seed=1, shake=0.0, t=0.0):
    r = random.Random(seed)
    c.poly([(x0, gy), (x1, gy), (x1, gy - h + 30), (x0, gy - h + 30)], col, 0)
    n = int((x1 - x0) / 60) + 1
    for i in range(n):
        x = x0 + i * 60 + r.uniform(-10, 10)
        sh = shake * math.sin(t * 40 + i) * 8
        c.ell(x + sh, gy - h + 30 + r.uniform(-10, 10), 52, 46, col, 6)
    c.poly([(x0, gy), (x1, gy), (x1, gy - h + 34), (x0, gy - h + 34)], col, 0)
    c.line([(x0, gy), (x1, gy)], 6, INK)
    for i in range(int((x1 - x0) / 22)):
        x = x0 + r.uniform(0, x1 - x0); y = gy - r.uniform(10, h - 10)
        c.ell(x, y, 9, 6, shade(col, 1.25 if r.random() < .5 else .78), 0)

def bus(c, x, gy, s=1.0, wheel=0.0, col=(206, 40, 46)):
    P = lambda a, b: (x + a * s, gy + b * s)
    c.poly([P(-300, -40), P(300, -40), P(300, -520), P(-280, -520), P(-300, -500)], col, 8)
    for row, (y0, y1) in enumerate(((-260, -170), (-470, -370))):
        for k in range(6):
            wx = -270 + k * 92
            c.poly([P(wx, y1), P(wx + 76, y1), P(wx + 76, y0), P(wx, y0)], (190, 224, 240), 5)
    c.poly([P(-300, -310), P(300, -310), P(300, -330), P(-300, -330)], (250, 230, 150), 4)
    c.poly([P(-120, -306), P(120, -306), P(120, -276), P(-120, -276)], (40, 40, 50), 0)
    c.d.text(c.pt(*P(0, -291)), "LONDON", font=fnt(FONT_TITLE, 26 * s * c.z * c.SS), fill=(255, 230, 120), anchor="mm")
    for wx in (-190, 190):
        c.ell(*P(wx, -40), 50 * s, 50 * s, (36, 32, 40), 7)
        c.ell(*P(wx, -40), 22 * s, 22 * s, (190, 190, 200), 4)
        c.line([P(wx, -40), P(wx + math.cos(wheel) * 20, -40 + math.sin(wheel) * 20)], 4, (90, 90, 100))
    c.ell(*P(296, -110), 14 * s, 18 * s, (255, 240, 170), 4)

def phone_box(c, x, gy, s=1.0):
    P = lambda a, b: (x + a * s, gy + b * s)
    red = (206, 40, 46)
    c.poly([P(-70, 0), P(70, 0), P(70, -420), P(-70, -420)], red, 7)
    c.poly([P(-80, -420), P(80, -420), P(70, -460), P(-70, -460)], red, 7)
    c.poly([P(-50, -400), P(50, -400), P(50, -372), P(-50, -372)], (250, 248, 240), 4)
    c.d.text(c.pt(*P(0, -386)), "TELEPHONE", font=fnt(FONT_TITLE, 18 * s * c.z * c.SS), fill=(40, 30, 30), anchor="mm")
    for j in range(5):
        for k in range(3):
            c.poly([P(-46 + k * 31, -350 + j * 56), P(-22 + k * 31, -350 + j * 56), P(-22 + k * 31, -302 + j * 56), P(-46 + k * 31, -302 + j * 56)], (200, 224, 236), 3)

def big_ben(c, x, gy, h=1200, col=(150, 140, 150)):
    w = h * .09
    c.poly([(x - w, gy), (x + w, gy), (x + w, gy - h * .72), (x - w, gy - h * .72)], col, 0)
    c.poly([(x - w * 1.15, gy - h * .72), (x + w * 1.15, gy - h * .72), (x + w * 1.15, gy - h * .8), (x - w * 1.15, gy - h * .8)], col, 0)
    c.ell(x, gy - h * .66, w * .72, w * .72, mixc(col, (255, 250, 220), .55), 0)
    c.line([(x, gy - h * .66), (x, gy - h * .66 - w * .5)], 4, shade(col, .6))
    c.line([(x, gy - h * .66), (x + w * .35, gy - h * .66)], 4, shade(col, .6))
    c.poly([(x - w * 1.05, gy - h * .8), (x + w * 1.05, gy - h * .8), (x, gy - h)], col, 0)
    for k in range(5): c.line([(x - w + k * w / 2, gy - 40), (x - w + k * w / 2, gy - h * .6)], 3, shade(col, .88))

def central_hall(c, x, gy):
    stone = (226, 214, 190)
    c.poly([(x - 560, gy), (x + 560, gy), (x + 560, gy - 640), (x - 560, gy - 640)], stone, 8)
    # cúpula
    c.poly([(x - 330, gy - 640), (x + 330, gy - 640), (x + 300, gy - 760), (x - 300, gy - 760)], shade(stone, .94), 7)
    c.poly([(x + px_, gy - 760 + py_) for px_, py_ in ellpts(0, 0, 300, 290, 30, 180, 360)], (96, 118, 116), 8)
    for k in range(-3, 4):
        c.line([(x + k * 70, gy - 760), (x + k * 40, gy - 1030)], 4, (80, 100, 98))
    c.poly([(x - 40, gy - 1040), (x + 40, gy - 1040), (x + 40, gy - 1130), (x - 40, gy - 1130)], stone, 6)
    c.poly([(x - 50, gy - 1130), (x + 50, gy - 1130), (x, gy - 1190)], (96, 118, 116), 6)
    # columnas y ventanas
    for k in range(-4, 5):
        px_ = x + k * 118
        c.poly([(px_ - 22, gy - 120), (px_ + 22, gy - 120), (px_ + 18, gy - 560), (px_ - 18, gy - 560)], (244, 236, 216), 5)
    for k in range(-4, 4):
        wx = x + k * 118 + 59
        c.poly([(wx - 34, gy - 250), (wx + 34, gy - 250), (wx + 34, gy - 470), (wx - 34, gy - 470)], (120, 150, 176), 5)
        c.poly([(wx + px_, gy - 470 + py_) for px_, py_ in ellpts(0, 0, 34, 34, 10, 180, 360)], (120, 150, 176), 5)
    c.poly([(x - 590, gy - 560), (x + 590, gy - 560), (x + 590, gy - 600), (x - 590, gy - 600)], shade(stone, .9), 6)
    c.poly([(x - 590, gy - 120), (x + 590, gy - 120), (x + 590, gy - 150), (x - 590, gy - 150)], shade(stone, .9), 5)
    # escalinata + puerta
    c.poly([(x - 150, gy), (x + 150, gy), (x + 150, gy - 220), (x - 150, gy - 220)], (70, 52, 50), 7)
    c.poly([(x - 120, gy), (x + 120, gy), (x + 120, gy - 196), (x - 120, gy - 196)], (255, 224, 150), 0)
    for i in range(4): c.poly([(x - 260 - i * 20, gy + i * 22), (x + 260 + i * 20, gy + i * 22), (x + 260 + i * 20, gy + 22 + i * 22), (x - 260 - i * 20, gy + 22 + i * 22)], (206, 196, 180), 5)
    # pancarta
    c.poly([(x - 330, gy - 330), (x + 330, gy - 330), (x + 330, gy - 440), (x - 330, gy - 440)], (30, 60, 140), 7)
    c.d.text(c.pt(x, gy - 400), "EXPOSICIÓN DE SELLOS", font=fnt(FONT_TITLE, 52 * c.z * c.SS), fill=(255, 240, 200), anchor="mm")
    c.d.text(c.pt(x, gy - 352), "1966", font=fnt(FONT_TITLE, 34 * c.z * c.SS), fill=(255, 210, 90), anchor="mm")

def london_street(c, x0, x1, gy, grass=False):
    street(c, x0, x1, gy)

# ------------------------------------------------------------------ interiores
def expo_room(c, x, gy, wall=(36, 76, 70), spot=True):
    c.poly([(x - 1800, gy - 1700), (x + 1800, gy - 1700), (x + 1800, gy), (x - 1800, gy)], wall, 0)
    for i in range(-30, 31):
        c.poly([(x + i * 60, gy - 1700), (x + i * 60 + 6, gy - 1700), (x + i * 60 + 6, gy), (x + i * 60, gy)], shade(wall, 1.08), 0)
    r = random.Random(5)
    for fx in (-1300, -900, 900, 1300, -1700, 1700):
        for fy in (-900, -560):
            c.poly([(x + fx - 150, gy + fy - 120), (x + fx + 150, gy + fy - 120), (x + fx + 150, gy + fy + 120), (x + fx - 150, gy + fy + 120)], (210, 170, 80), 8)
            c.poly([(x + fx - 126, gy + fy - 96), (x + fx + 126, gy + fy - 96), (x + fx + 126, gy + fy + 96), (x + fx - 126, gy + fy + 96)], (244, 236, 218), 0)
            for j in range(2):
                for k in range(3):
                    sx = x + fx - 90 + k * 90; sy = gy + fy - 44 + j * 88
                    col = [(200, 60, 70), (60, 100, 170), (80, 150, 90), (220, 160, 60)][r.randint(0, 3)]
                    c.poly([(sx - 32, sy - 34), (sx + 32, sy - 34), (sx + 32, sy + 34), (sx - 32, sy + 34)], (250, 250, 248), 3)
                    c.poly([(sx - 24, sy - 26), (sx + 24, sy - 26), (sx + 24, sy + 26), (sx - 24, sy + 26)], col, 0)
    c.poly([(x - 1800, gy - 260), (x + 1800, gy - 260), (x + 1800, gy), (x - 1800, gy)], shade(wall, .7), 0)
    c.poly([(x - 1800, gy - 270), (x + 1800, gy - 270), (x + 1800, gy - 256), (x - 1800, gy - 256)], (210, 170, 80), 0)
    c.poly([(x - 1800, gy), (x + 1800, gy), (x + 1800, gy + 1200), (x - 1800, gy + 1200)], (120, 84, 64), 0)
    for i in range(-30, 31):
        c.line([(x + i * 120, gy), (x + i * 160, gy + 1200)], 3, (100, 68, 52))
    c.poly([(x - 700, gy + 60), (x + 700, gy + 60), (x + 900, gy + 1200), (x - 900, gy + 1200)], (150, 36, 52), 0)
    if spot:
        c.poly([(x - 150, gy - 1700), (x + 150, gy - 1700), (x + 420, gy + 120), (x - 420, gy + 120)], (255, 250, 220, 0), 0)

def light_cone(sc, x_top, y_top, x_bot, y_bot, w_top, w_bot, k=.16, col=(255, 244, 200)):
    """Haz de luz semitransparente en la capa de primer plano."""
    tmp = Image.new("RGBA", sc.fg.img.size, (0, 0, 0, 0))
    c = Ctx(tmp, sc.fg.cx, sc.fg.cy, sc.fg.z, sc.SS, sc.fg.sh)
    c.poly([(x_top - w_top, y_top), (x_top + w_top, y_top), (x_bot + w_bot, y_bot), (x_bot - w_bot, y_bot)], col + (int(255 * k),), 0)
    tmp = tmp.filter(ImageFilter.GaussianBlur(14 * sc.SS))
    sc.fg.img.alpha_composite(tmp)

def interrog_room(c, x, gy):
    wall = (84, 96, 110)
    c.poly([(x - 1800, gy - 1700), (x + 1800, gy - 1700), (x + 1800, gy), (x - 1800, gy)], wall, 0)
    for j in range(16):
        for i in range(-16, 17):
            bx = x + i * 120 + (60 if j % 2 else 0); by = gy - 60 - j * 100
            c.poly([(bx - 56, by - 44), (bx + 56, by - 44), (bx + 56, by + 44), (bx - 56, by + 44)], shade(wall, 1.06), 0)
    c.poly([(x + 420, gy - 1200), (x + 860, gy - 1200), (x + 860, gy - 700), (x + 420, gy - 700)], (60, 66, 80), 8)
    for k in range(10): c.line([(x + 430, gy - 1180 + k * 48), (x + 850, gy - 1180 + k * 48)], 10, (200, 196, 170))
    c.poly([(x - 1800, gy), (x + 1800, gy), (x + 1800, gy + 1200), (x - 1800, gy + 1200)], (70, 74, 86), 0)
    for i in range(-16, 17):
        for j in range(8):
            if (i + j) % 2: c.poly([(x + i * 120, gy + j * 120), (x + i * 120 + 120, gy + j * 120), (x + i * 120 + 120, gy + j * 120 + 120), (x + i * 120, gy + j * 120 + 120)], (82, 86, 98), 0)
    c.poly([(x - 560, gy - 900), (x - 200, gy - 900), (x - 200, gy - 500), (x - 560, gy - 500)], (240, 236, 220), 8)
    c.d.text(c.pt(x - 380, gy - 845), "SE BUSCA", font=fnt(FONT_TITLE, 60 * c.z * c.SS), fill=(40, 30, 30), anchor="mm")
    trophy(c, x - 380, gy - 530, .72)

def table(c, x, gy, w=520, h=230, col=(120, 80, 56), cloth=None):
    if cloth:
        c.poly([(x - w / 2 - 20, gy - h), (x + w / 2 + 20, gy - h), (x + w / 2 + 40, gy - h + 160), (x - w / 2 - 40, gy - h + 160)], cloth, 7)
        for k in range(-6, 7): c.line([(x + k * w / 13, gy - h + 20), (x + k * w / 12, gy - h + 150)], 3, shade(cloth, .9))
        return
    c.poly([(x - w / 2, gy - h), (x + w / 2, gy - h), (x + w / 2, gy - h + 34), (x - w / 2, gy - h + 34)], col, 7)
    for k in (-1, 1): c.poly([(x + k * (w / 2 - 40) - 14, gy - h + 34), (x + k * (w / 2 - 40) + 14, gy - h + 34), (x + k * (w / 2 - 40) + 14, gy), (x + k * (w / 2 - 40) - 14, gy)], shade(col, .8), 6)

def hanging_lamp(c, x, y_top, length, ang, on=1.0):
    ex = x + math.sin(math.radians(ang)) * length; ey = y_top + math.cos(math.radians(ang)) * length
    c.line([(x, y_top), (ex, ey)], 5, (40, 40, 46))
    pts = rotp([(-70, 0), (70, 0), (30, -50), (-30, -50)], -ang, 0, 0)
    c.poly([(ex + a, ey + b + 50) for a, b in pts], (60, 90, 70), 6)
    c.ell(ex, ey + 54, 22, 16, mixc((200, 200, 180), (255, 246, 190), on), 4)
    return ex, ey + 54

def banquet_room(c, x, gy):
    wall = (232, 214, 170)
    c.poly([(x - 1800, gy - 1700), (x + 1800, gy - 1700), (x + 1800, gy), (x - 1800, gy)], wall, 0)
    for i in range(-30, 31): c.poly([(x + i * 80, gy - 1700), (x + i * 80 + 30, gy - 1700), (x + i * 80 + 30, gy), (x + i * 80, gy)], shade(wall, 1.05), 0)
    for row in (-1250, -1000):
        pts = [(x - 1800 + i * 60, gy + row + math.sin(i * .5) * 30) for i in range(61)]
        c.line(pts, 4, (90, 80, 80))
        for i in range(0, 60, 2):
            px_, py_ = pts[i]; col = [(206, 40, 50), (250, 250, 250), (40, 70, 160)][(i // 2) % 3]
            c.poly([(px_, py_), (px_ + 60, py_ + 2), (px_ + 30, py_ + 80)], col, 4)
    c.poly([(x - 1800, gy), (x + 1800, gy), (x + 1800, gy + 1200), (x - 1800, gy + 1200)], (150, 104, 70), 0)
    for i in range(-30, 30): c.line([(x + i * 100, gy), (x + i * 140, gy + 1200)], 3, (126, 84, 56))

def rio_far(c, x, gy):
    r = random.Random(8)
    for i in range(140):
        sx = x + r.uniform(-2000, 2000); sy = gy - r.uniform(900, 2000)
        c.ell(sx, sy, r.uniform(2, 5), r.uniform(2, 5), (255, 250, 220), 0)
    c.ell(x + 700, gy - 1500, 90, 90, (250, 244, 214), 0)
    c.ell(x + 740, gy - 1530, 80, 80, (30, 36, 78), 0)
    hill = (34, 44, 74)
    pts = [(x - 2000, gy)] + [(x - 2000 + i * 100, gy - 260 - 160 * math.sin(i * .37) ** 2 - 90 * math.sin(i * 1.1) ** 2) for i in range(41)] + [(x + 2000, gy)]
    c.poly(pts, mixc(hill, (60, 60, 100), .3), 0)
    c.poly([(x - 1100 + px_, gy - 200 + py_) for px_, py_ in ellpts(0, 0, 230, 820, 30, 180, 360)] , hill, 0)
    c.poly([(x - 750 + px_, gy - 200 + py_) for px_, py_ in ellpts(0, 0, 200, 420, 24, 180, 360)], hill, 0)
    c.poly([(x + 300 + px_, gy - 150 + py_) for px_, py_ in ellpts(0, 0, 500, 640, 30, 180, 360)], shade(hill, 1.1), 0)

def rio_mid(c, x, gy):
    r = random.Random(9); xx = x - 2000
    while xx < x + 2000:
        w = r.uniform(140, 300); h = r.uniform(300, 900)
        c.poly([(xx, gy), (xx + w, gy), (xx + w, gy - h), (xx, gy - h)], (40, 46, 76), 0)
        for j in range(int(h / 70)):
            for k in range(int(w / 50)):
                if r.random() < .38: c.poly([(xx + 14 + k * 50, gy - 40 - j * 70), (xx + 40 + k * 50, gy - 40 - j * 70), (xx + 40 + k * 50, gy - 70 - j * 70), (xx + 14 + k * 50, gy - 70 - j * 70)], (255, 214, 120), 0)
        xx += w + r.uniform(10, 40)
    for px_ in (-1500, -700, 500, 1400):
        c.line([(x + px_, gy), (x + px_ + 30, gy - 300), (x + px_ + 50, gy - 520)], 18, (24, 30, 50))
        for a in range(0, 360, 45):
            ex = x + px_ + 50 + math.cos(math.radians(a)) * 150; ey = gy - 520 + math.sin(math.radians(a)) * 60 + 40
            c.line([(x + px_ + 50, gy - 520), ((x + px_ + 50 + ex) / 2, gy - 560), (ex, ey)], 14, (24, 30, 50))
    c.poly([(x - 2000, gy), (x + 2000, gy), (x + 2000, gy + 1300), (x - 2000, gy + 1300)], (40, 40, 60), 0)
    c.poly([(x - 2000, gy), (x + 2000, gy), (x + 2000, gy + 40), (x - 2000, gy + 40)], (90, 90, 110), 0)
    for i in range(-30, 30): c.poly([(x + i * 140, gy + 380), (x + i * 140 + 70, gy + 380), (x + i * 140 + 70, gy + 392), (x + i * 140, gy + 392)], (220, 210, 120), 0)

def museum_room(c, x, gy):
    wall = (26, 34, 58)
    c.poly([(x - 1800, gy - 1700), (x + 1800, gy - 1700), (x + 1800, gy), (x - 1800, gy)], wall, 0)
    for i in range(-14, 15):
        c.poly([(x + i * 130 - 4, gy - 1700), (x + i * 130 + 4, gy - 1700), (x + i * 130 + 4, gy), (x + i * 130 - 4, gy)], shade(wall, 1.2), 0)
    c.poly([(x - 380, gy - 1500), (x + 380, gy - 1500), (x + 380, gy - 1080), (x - 380, gy - 1080)], (40, 50, 80), 7)
    c.d.text(c.pt(x, gy - 1290), "CBF", font=fnt(FONT_TITLE, 160 * c.z * c.SS), fill=(70, 160, 90), anchor="mm")
    c.poly([(x - 1800, gy), (x + 1800, gy), (x + 1800, gy + 1200), (x - 1800, gy + 1200)], (34, 38, 56), 0)
    for i in range(-20, 20):
        c.line([(x + i * 120, gy), (x + i * 170, gy + 1200)], 3, (44, 48, 70))
    # zona iluminada en el suelo
    c.poly([(x + px_, gy + 60 + py_) for px_, py_ in ellpts(0, 0, 420, 90, 30)], (70, 76, 100), 0)

CROWD_COLS = [(206, 40, 50), (250, 250, 250), (40, 70, 160), (230, 190, 70), (120, 130, 150), (200, 80, 60)]
def stadium(c, x, gy, cheer=0, seed=4):
    r = random.Random(seed)
    stand = (120, 116, 130)
    c.poly([(x - 2200, gy - 1120), (x + 2200, gy - 1120), (x + 2200, gy - 60), (x - 2200, gy - 60)], stand, 0)
    c.poly([(x - 2200, gy - 1180), (x + 2200, gy - 1180), (x + 2200, gy - 1100), (x - 2200, gy - 1100)], (70, 70, 84), 0)
    for k in range(-11, 12): c.line([(x + k * 200, gy - 1180), (x + k * 200 + 100, gy - 1100)], 6, (110, 110, 124))
    for j in range(14):
        yy = gy - 130 - j * 68
        c.line([(x - 2200, yy + 30), (x + 2200, yy + 30)], 4, shade(stand, .85))
        i = 0
        xx = x - 2200 + (j % 2) * 26
        while xx < x + 2200:
            col = CROWD_COLS[r.randint(0, len(CROWD_COLS) - 1)]
            skin = [(240, 200, 160), (220, 170, 130), (190, 140, 100)][r.randint(0, 2)]
            up = cheer and r.random() < .7
            jy = -12 if (cheer and r.random() < .5) else 0
            c.poly([(xx - 22, yy + 28), (xx + 22, yy + 28), (xx + 18, yy - 4 + jy), (xx - 18, yy - 4 + jy)], col, 3)
            c.ell(xx, yy - 20 + jy, 15, 16, skin, 3)
            if up:
                c.line([(xx - 16, yy + jy), (xx - 30, yy - 50 + jy)], 6, skin); c.line([(xx + 16, yy + jy), (xx + 30, yy - 50 + jy)], 6, skin)
            xx += 52 + r.uniform(-4, 6)
    # vallas publicitarias
    c.poly([(x - 2200, gy - 120), (x + 2200, gy - 120), (x + 2200, gy - 20), (x - 2200, gy - 20)], (30, 40, 90), 0)
    for k in range(-9, 10):
        c.d.text(c.pt(x + k * 240, gy - 70), "1966", font=fnt(FONT_TITLE, 60 * c.z * c.SS), fill=(250, 220, 90) if k % 2 else (250, 250, 250), anchor="mm")
    # torres de focos
    for px_ in (-1500, 1500):
        c.poly([(x + px_ - 20, gy - 1100), (x + px_ + 20, gy - 1100), (x + px_ + 14, gy - 1600), (x + px_ - 14, gy - 1600)], (60, 60, 70), 4)
        c.poly([(x + px_ - 140, gy - 1600), (x + px_ + 140, gy - 1600), (x + px_ + 140, gy - 1720), (x + px_ - 140, gy - 1720)], (60, 60, 70), 5)
        for a in range(4):
            for b in range(2): c.ell(x + px_ - 100 + a * 66, gy - 1630 - b * 56, 22, 20, (255, 250, 220), 3)

def pitch(c, x, gy):
    for k in range(-10, 10):
        c.poly([(x + k * 260, gy - 20), (x + k * 260 + 260, gy - 20), (x + k * 400 + 400, gy + 1400), (x + k * 400, gy + 1400)], (86, 160, 76) if k % 2 else (100, 176, 88), 0)
    c.line([(x - 2200, gy + 300), (x + 2200, gy + 300)], 10, (240, 250, 240))
