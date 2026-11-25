"""Motor 2D v2: capas con parallax, sombreado de bordes, sombras de contacto, desenfoque de fondo,
bloom, grano, transiciones y subtítulos cinéticos. 1080x1920 @ 30 fps."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from hscene import Ctx, ellpts, rotp, lerp, smr, sm, clamp, mixc, INK, W, H, FPS

FONT_TITLE = "/usr/share/fonts/truetype/google-fonts/ofl/anton/Anton-Regular.ttf"
FONT_SUB = "/usr/share/fonts/truetype/google-fonts/ofl/archivoblack/ArchivoBlack-Regular.ttf"
FONT_SERIF = "/usr/share/fonts/truetype/google-fonts/ofl/gelasio/Gelasio[wght].ttf"
_fc = {}
def fnt(path, px):
    px = max(6, int(px)); k = (path, px)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, px)
    return _fc[k]

def eback(x, s=1.9):
    x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def eout(x): return 1 - (1 - clamp(x)) ** 3
def ein(x): return clamp(x) ** 3
def elastic(x):
    x = clamp(x)
    return 1.0 if x >= 1 else 1 - math.exp(-7 * x) * math.cos(14 * x)

class Scene:
    def __init__(self, cx, cy, z, SS, sh=(0, 0)):
        self.SS = SS; self.cam = (cx, cy, z)
        mk = lambda: Image.new("RGBA", (int(W * SS), int(H * SS)), (0, 0, 0, 0))
        self.far = Ctx(mk(), cx, cy, z, SS, sh); self.mid = Ctx(mk(), cx, cy, z, SS, sh)
        self.stage = Ctx(mk(), cx, cy, z, SS, sh); self.fg = Ctx(mk(), cx, cy, z, SS, sh)
        self.shadows = []; self.glows = []
    def shadow(self, x, y, rx, ry, k=.5): self.shadows.append((x, y, rx, ry, k))
    def glow(self, x, y, r, col, k=.5): self.glows.append((x, y, r, col, k))

_VIG = None
def vignette():
    global _VIG
    if _VIG is None:
        yy, xx = np.mgrid[0:H, 0:W]
        _VIG = (1.0 - 0.30 * (((xx - W / 2) / (W / 2)) ** 2 * .55 + ((yy - H / 2) / (H / 2)) ** 2 * .75)).astype(np.float32)
    return _VIG

_sk = {}
def sky_img(stops, SS, sun=None):
    """stops: [(pos, (r,g,b)), ...] de arriba a abajo. sun=(x,y,radio,color) en píxeles de pantalla."""
    k = (tuple(stops), SS, sun)
    if k not in _sk:
        h, w = int(H * SS), int(W * SS)
        v = np.linspace(0, 1, h)
        col = np.zeros((h, 3), np.float32)
        for ch in range(3): col[:, ch] = np.interp(v, [p for p, _ in stops], [c[ch] for _, c in stops])
        arr = np.repeat(col[:, None, :], w, axis=1)
        if sun:
            sx, sy, sr, sc = sun
            yy, xx = np.mgrid[0:h, 0:w]
            r2 = ((xx - sx * SS) ** 2 + (yy - sy * SS) ** 2) / (SS * SS)
            g = np.exp(-r2 / (2 * (sr * 3.2) ** 2))[:, :, None]
            arr = arr * (1 - .5 * g) + g * np.array(sc, np.float32) * .6
            arr = np.where((r2 < sr ** 2)[:, :, None], np.array(sc, np.float32), arr)
        _sk[k] = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return _sk[k].copy()

def edge_shade(img, SS, d=9, dark=.30, light=.20):
    """Sombreado de borde (luz arriba-izquierda): oscurece bordes inferior-derecha, ilumina superior-izquierda."""
    half = (img.size[0] // 2, img.size[1] // 2)
    a = np.asarray(img.resize(half, Image.BILINEAR))[..., 3].astype(np.float32) / 255
    k = max(1, int(d * SS / 2))
    sh = a * (1 - np.roll(a, (-k, -k), (0, 1)))
    hi = a * (1 - np.roll(a, (k, k), (0, 1)))
    f = lambda m: np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(k * .55)).resize(img.size, Image.BILINEAR)).astype(np.float32) / 255
    sh, hi = f(sh), f(hi)
    arr = np.asarray(img).astype(np.float32)
    rgb = arr[..., :3]
    rgb = rgb * (1 - dark * sh[..., None]) + 255 * light * hi[..., None] * (1 - sh[..., None])
    arr[..., :3] = np.clip(rgb, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")

def compose(sc, sky, blur=0.0, shade=True):
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
        arr *= (1 - .55 * mm[..., None]) * np.array([1.0, .95, 1.05], np.float32) + .0
        base = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    base = base.convert("RGBA")
    st = edge_shade(sc.stage.img, SS) if shade else sc.stage.img
    base = Image.alpha_composite(base, st)
    base = Image.alpha_composite(base, sc.fg.img)
    return base.convert("RGB").resize((W, H), Image.LANCZOS)

def finish(img, grade, fi, whip=0.0, flash=0.0, glows=()):
    arr = np.asarray(img).astype(np.float32)
    g = grade
    if g.get("bloom", 0) > 0:
        sm_ = img.resize((W // 8, H // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
        bl = np.asarray(sm_).astype(np.float32)
        arr += np.clip((bl - 165) / 90, 0, 1) * g["bloom"] * 90
    for (gx, gy, r, col, k) in glows:
        yy, xx = np.mgrid[0:H, 0:W]
        arr += np.exp(-(((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * r * r)))[..., None] * np.array(col, np.float32) * k
    tint = np.array(g.get("tint", (1, 1, 1)), np.float32)
    arr = (arr * tint - 128) * g.get("contrast", 1.0) + 128 + g.get("lift", 0)
    arr *= vignette()[..., None] ** g.get("vig", 1.0)
    if whip > 0:
        n = 9; acc = np.zeros_like(arr)
        for k in range(n): acc += np.roll(arr, int((k - n // 2) * whip / n * 2), axis=1)
        arr = acc / n
    if g.get("grain", 0) > 0:
        rng = np.random.default_rng(fi * 7 + 1)
        arr += rng.standard_normal((H, W, 1)).astype(np.float32) * g["grain"]
    if flash > 0: arr = arr * (1 - flash) + 255 * flash
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ------------------------------------------------------------------ texto en pantalla
def title_text(c, text, x, y, px, t, t0, col=(255, 226, 70), font=FONT_TITLE, stroke=10, t1=None, rot=0.0, hold_scale=1.0):
    """Título con entrada elástica (coordenadas de pantalla, c = Ctx de capa de primer plano)."""
    u = t - t0
    if u < 0 or (t1 is not None and t > t1): return
    sc = eback(u / .28) * hold_scale
    if t1 is not None and t1 - t < .18: sc *= clamp((t1 - t) / .18)
    S = c.SS; f = fnt(font, px * max(.05, sc) * S)
    if rot:
        tmp = Image.new("RGBA", (int(W * S), int(px * 2.2 * S)), (0, 0, 0, 0)); d = ImageDraw.Draw(tmp)
        d.text((W * S / 2, px * 1.1 * S), text, font=f, fill=col, anchor="mm", stroke_width=int(stroke * S), stroke_fill=INK)
        tmp = tmp.rotate(rot, resample=Image.BICUBIC, center=(W * S / 2, px * 1.1 * S))
        c.img.alpha_composite(tmp, (0, int((y - px * 1.1) * S)) if False else (0, max(0, int((y - px * 1.1) * S))))
    else:
        sh = 6 * S
        c.d.text((x * S + sh, y * S + sh), text, font=f, fill=(0, 0, 0), anchor="mm", stroke_width=int(stroke * S), stroke_fill=(0, 0, 0))
        c.d.text((x * S, y * S), text, font=f, fill=col, anchor="mm", stroke_width=int(stroke * S), stroke_fill=INK)

def lowerthird(c, name, sub, t, t0, t1, y=1180):
    """Placa art déco de presentación de personaje."""
    u = t - t0
    if u < 0 or t > t1: return
    S = c.SS
    k = eout(u / .45) * (1 if t1 - t > .3 else clamp((t1 - t) / .3))
    x0 = -700 + 760 * k
    w, h = 760, 190
    c.d.polygon([((x0) * S, (y - 0) * S), ((x0 + w) * S, (y) * S), ((x0 + w - 40) * S, (y + h) * S), ((x0) * S, (y + h) * S)], fill=(22, 36, 70), outline=(240, 200, 90), width=int(6 * S)) if False else None
    pts = [(x0, y), (x0 + w, y), (x0 + w - 44, y + h), (x0, y + h)]
    c.d.polygon([(a * S, b * S) for a, b in pts], fill=(24, 38, 78))
    c.d.line([(a * S, b * S) for a, b in pts + [pts[0]]], fill=(240, 200, 90), width=int(7 * S))
    c.d.line([((x0 + 14) * S, (y + 14) * S), ((x0 + w - 52) * S, (y + 14) * S)], fill=(240, 200, 90), width=int(3 * S))
    c.d.text(((x0 + 46) * S, (y + 78) * S), name, font=fnt(FONT_TITLE, 92 * S), fill=(255, 244, 214), anchor="lm")
    c.d.text(((x0 + 48) * S, (y + 148) * S), sub, font=fnt(FONT_SERIF, 44 * S), fill=(240, 200, 90), anchor="lm")

# ------------------------------------------------------------------ subtítulos cinéticos
def draw_caption(img, words, t, t0, hot=(), y=1560, max_w=980, size=118):
    """words: lista de palabras del bloque. Palabra por palabra, con entrada elástica."""
    u = t - t0
    sc = .72 + .36 * elastic(u / .22) - .0
    if u < .22: sc = .6 + .5 * eback(u / .22)
    sc = clamp(sc, .5, 1.22)
    text = " ".join(words)
    px = size
    f = fnt(FONT_SUB, px)
    d0 = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    while d0.textlength(text, font=f) > max_w and px > 60: px -= 4; f = fnt(FONT_SUB, px)
    fs = fnt(FONT_SUB, px * sc)
    wtot = d0.textlength(text, font=fs)
    layer = Image.new("RGBA", (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    x = (W - wtot) / 2; cy = 130
    for ox, oy, col in ((0, 9, (0, 0, 0, 150)),):
        xx = x
        for w in words:
            d.text((xx + ox, cy + oy), w, font=fs, fill=col, anchor="lm", stroke_width=16, stroke_fill=col); xx += d0.textlength(w + " ", font=fs)
    xx = x
    for w in words:
        yel = w.strip(",.:¿?¡!").lower() in hot
        col = (255, 214, 64) if yel else (255, 255, 255)
        d.text((xx, cy), w, font=fs, fill=col, anchor="lm", stroke_width=13, stroke_fill=(18, 14, 36)); xx += d0.textlength(w + " ", font=fs)
    img = img.convert("RGBA"); img.alpha_composite(layer, (0, int(y - 130))); return img.convert("RGB")
