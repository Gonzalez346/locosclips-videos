"""Motor v3: capa de primer plano desenfocada, textura de papel, destellos anamórficos, líneas de velocidad."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from hscene import Ctx, W, H, INK, clamp, lerp, mixc, ellpts, rotp
from kit2 import *
from kit2 import vignette

class Scene3(Scene):
    def __init__(self, cx, cy, z, SS, sh=(0, 0)):
        super().__init__(cx, cy, z, SS, sh)
        self.fgb = Ctx(Image.new("RGBA", (int(W * SS), int(H * SS)), (0, 0, 0, 0)), cx, cy, z, SS, sh)
    def scr(self, x, y):
        cx, cy, z = self.cam
        return ((x - cx) * z + W / 2 + self.stage.sh[0], (y - cy) * z + H / 2 + self.stage.sh[1])

def compose3(sc, sky, blur=0.0, shade=True, fgblur=7.0):
    SS = sc.SS
    base = sky.convert("RGBA")
    base = Image.alpha_composite(base, sc.far.img)
    base = Image.alpha_composite(base, sc.mid.img).convert("RGB")
    if blur > 0: base = base.filter(ImageFilter.GaussianBlur(blur * SS))
    if sc.shadows:
        m = Image.new("L", base.size, 0); d = ImageDraw.Draw(m)
        for x, y, rx, ry, k in sc.shadows:
            a = sc.stage.pt(x - rx, y - ry); b = sc.stage.pt(x + rx, y + ry)
            d.ellipse([a, b], fill=int(255 * k))
        m = m.filter(ImageFilter.GaussianBlur(9 * SS))
        arr = np.asarray(base).astype(np.float32); mm = np.asarray(m).astype(np.float32) / 255
        arr *= (1 - .55 * mm[..., None]) * np.array([1.0, .95, 1.05], np.float32)
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    base = base.convert("RGBA")
    st = edge_shade(sc.stage.img, SS) if shade else sc.stage.img
    base = Image.alpha_composite(base, st)
    if sc.fgb.img.getbbox():
        fb = edge_shade(sc.fgb.img, SS).filter(ImageFilter.GaussianBlur(fgblur * SS))
        base = Image.alpha_composite(base, fb)
    base = Image.alpha_composite(base, sc.fg.img)
    return base.convert("RGB").resize((W, H), Image.LANCZOS)

_TEX = None
def paper_tex():
    global _TEX
    if _TEX is None:
        rng = np.random.default_rng(11)
        n = rng.standard_normal((H // 24 + 2, W // 24 + 2)).astype(np.float32)
        im = Image.fromarray(((n * 30) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        fine = rng.standard_normal((H // 3, W // 3)).astype(np.float32)
        im2 = Image.fromarray(((fine * 30) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
        _TEX = 1 + (np.asarray(im).astype(np.float32) - 128) / 128 * .035 + (np.asarray(im2).astype(np.float32) - 128) / 128 * .018
    return _TEX

_YY = None
def finish3(img, grade, fi, whip=0.0, flash=0.0, glows=(), streaks=(), fade=0.0, speed=None):
    global _YY
    if _YY is None: _YY = np.mgrid[0:H, 0:W].astype(np.float32)
    yy, xx = _YY
    arr = np.asarray(img).astype(np.float32)
    g = grade
    if g.get("bloom", 0) > 0:
        sm_ = img.resize((W // 8, H // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
        bl = np.asarray(sm_).astype(np.float32)
        arr += np.clip((bl - 160) / 90, 0, 1) * g["bloom"] * 95
    for (gx, gy, r, col, k) in glows:
        if k <= 0: continue
        arr += np.exp(-(((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * r * r)))[..., None] * np.array(col, np.float32) * k
    for (sx, sy, ln, col, k) in streaks:
        if k <= 0: continue
        e = np.exp(-((yy - sy) ** 2) / (2 * 5.0 ** 2)) * np.exp(-((xx - sx) ** 2) / (2 * ln ** 2))
        e2 = np.exp(-(((xx - sx) ** 2 + (yy - sy) ** 2) / (2 * 60 ** 2)))
        arr += (e[..., None] * 1.0 + e2[..., None] * .5) * np.array(col, np.float32) * k
    tint = np.array(g.get("tint", (1, 1, 1)), np.float32)
    arr = (arr * tint - 128) * g.get("contrast", 1.0) + 128 + g.get("lift", 0)
    if g.get("sat", 1.0) != 1.0:
        lum = arr.mean(2, keepdims=True); arr = lum + (arr - lum) * g["sat"]
    arr *= vignette()[..., None] ** g.get("vig", 1.0)
    arr *= paper_tex()[..., None]
    if whip > 0:
        n = 9; acc = np.zeros_like(arr)
        for k in range(n): acc += np.roll(arr, int((k - n // 2) * whip / n * 2), axis=1)
        arr = acc / n
    if g.get("grain", 0) > 0:
        rng = np.random.default_rng(fi * 7 + 1)
        arr += rng.standard_normal((H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1) * g["grain"]
    if flash > 0: arr = arr * (1 - flash) + 255 * flash
    if fade > 0: arr *= (1 - clamp(fade))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def speed_lines(c_ui, t, cx=540, cy=900, n=36, r0=420, r1=1400, k=1.0, seed=2, col=(255, 255, 255)):
    r = random.Random(seed + int(t * 24))
    for i in range(n):
        a = r.uniform(0, 6.283); rr = r.uniform(r0, r0 + 200)
        w = r.uniform(3, 9) * k
        c_ui.poly([(cx + math.cos(a) * rr, cy + math.sin(a) * rr), (cx + math.cos(a + .012) * r1, cy + math.sin(a + .012) * r1),
                   (cx + math.cos(a - .012) * r1, cy + math.sin(a - .012) * r1)], col, 0)

def ray_burst(layer_img, SS, cx, cy, n=16, r=1600, rot=0.0, col=(255, 230, 150), alpha=.35, width=.11):
    tmp = Image.new("RGBA", layer_img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
    for i in range(n):
        a = rot + i / n * 6.283
        d.polygon([(cx * SS, cy * SS), ((cx + math.cos(a - width) * r) * SS, (cy + math.sin(a - width) * r) * SS),
                   ((cx + math.cos(a + width) * r) * SS, (cy + math.sin(a + width) * r) * SS)], fill=col + (int(255 * alpha),))
    tmp = tmp.filter(ImageFilter.GaussianBlur(6 * SS))
    layer_img.alpha_composite(tmp)

def dust(c, t, x0, x1, y0, y1, n=40, seed=1, col=(255, 248, 220), r=3.0):
    rr = random.Random(seed)
    for i in range(n):
        x = x0 + (rr.uniform(0, x1 - x0) + math.sin(t * .4 + i) * 30) % (x1 - x0)
        y = y0 + (rr.uniform(0, y1 - y0) - t * rr.uniform(6, 20)) % (y1 - y0)
        k = .5 + .5 * math.sin(t * 2 + i * 1.7)
        c.ell(x, y, r * (.6 + k), r * (.6 + k), col, 0)

def rain(c_ui, t, n=70, seed=4, col=(200, 214, 236), ang=.18, speed=2200, ln=70):
    r = random.Random(seed)
    for i in range(n):
        x0 = r.uniform(-200, 1280); y0 = r.uniform(0, 2100); v = speed * r.uniform(.8, 1.2)
        y = (y0 + t * v) % 2100 - 100; x = x0 + y * ang
        c_ui.line([(x, y), (x + ln * ang, y + ln)], r.uniform(2, 4), col)

def exclaim(c_ui, x, y, s, t, t0, col=(255, 214, 64), t1=None):
    u = t - t0
    if u < 0 or (t1 and t > t1): return
    k = eback(clamp(u / .22), 2.6)
    if k <= .05: return
    c_ui.poly([(x - 26 * s * k, y - 150 * s * k), (x + 26 * s * k, y - 150 * s * k), (x + 12 * s * k, y - 30 * s * k), (x - 12 * s * k, y - 30 * s * k)], col, 8)
    c_ui.ell(x, y + 8 * s * k, 20 * s * k, 20 * s * k, col, 8)

def qmark(c_ui, x, y, px, t, t0, col=(255, 214, 64), t1=None, rot=0):
    title_text(c_ui, "?", x, y, px, t, t0, col, FONT_TITLE, 10, t1, rot)
