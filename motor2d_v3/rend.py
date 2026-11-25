import sys, os, time
import numpy as np
from PIL import Image
import scene_pickles as S
from kit3 import compose3, finish3
from hscene import FPS
WHIPS = {3.60: 38, 6.05: 50, 8.35: 40, 11.24: 50, 13.56: 50, 16.38: 40, 18.12: 44, 22.46: 30, 24.78: 30, 27.77: 26, 30.74: 50, 36.0: 50, 39.72: 44, 42.53: 50, 43.92: 50}
CAPFN = None
def shots(): return sorted(S.SHOTS, key=lambda s: s[0])
def shot_at(t):
    L = shots()
    for a, b, fn, nm in L:
        if a <= t < b: return a, b, fn, nm
    return L[-1]
def render(fi, SS=1.5):
    t = fi / FPS
    a, b, fn, nm = shot_at(t)
    sc, sky, meta = fn(t, t - a, SS)
    img = compose3(sc, sky, blur=meta.get("blur", 0), shade=meta.get("shade", True), fgblur=meta.get("fgblur", 14))
    whip = 0.0
    for tb, k in WHIPS.items():
        dd = abs(t - tb)
        if dd < .09: whip = max(whip, k * (1 - dd / .09))
    img = finish3(img, meta.get("grade", S.G_DAY), fi, whip, meta.get("flash", 0), meta.get("glows", ()), meta.get("streaks", ()), meta.get("fade", 0))
    if CAPFN: img = CAPFN(img, t)
    return img
if __name__ == "__main__":
    out = sys.argv[1]; ts = [float(x) for x in sys.argv[2:]]
    ims = [render(int(round(t * FPS)), 1.0) for t in ts]
    sw, sh = 360, 640
    sheet = Image.new("RGB", (sw * len(ims), sh))
    for k, im in enumerate(ims): sheet.paste(im.resize((sw, sh), Image.LANCZOS), (k * sw, 0))
    sheet.save(out)
