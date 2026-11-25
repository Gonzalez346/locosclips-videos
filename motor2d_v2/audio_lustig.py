import numpy as np, subprocess, sys
from scipy.signal import butter, lfilter, fftconvolve
from capt import load_voice
SR = 44100
rng = np.random.default_rng(7)
vy, _ = load_voice("voice.mp3", SR)
N = len(vy) + SR // 2
T = np.arange(N) / SR
def mf(m): return 440 * 2 ** ((m - 69) / 12)
def put(buf, x, t0, g=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= len(buf): return
    n = min(len(x), len(buf) - i)
    buf[i:i + n, 0] += x[:n] * g * (1 - max(0, pan)); buf[i:i + n, 1] += x[:n] * g * (1 + min(0, pan))
def lp(x, fc, o=2): b, a = butter(o, fc / (SR / 2)); return lfilter(b, a, x)
def hp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), "high"); return lfilter(b, a, x)
def bp(x, f1, f2): b, a = butter(2, [f1 / (SR / 2), f2 / (SR / 2)], "band"); return lfilter(b, a, x)
def tt(d): return np.arange(int(d * SR)) / SR
def pluck(f, d=.5, br=1.0):
    t = tt(d); x = np.zeros_like(t)
    for k in range(1, 8): x += np.sin(2 * np.pi * f * k * t) / k ** (1.2 / br) * np.exp(-t * (4 + k * 5))
    x *= np.minimum(1, t * 600); return x * .5
def reed(f, d=.6, vib=5.3):
    t = tt(d); ph = 2 * np.pi * f * t + .004 * np.sin(2 * np.pi * vib * t) * f / 40
    x = sum(np.sin(k * ph) / k * (1 if k % 2 else .6) for k in range(1, 7))
    return x * np.minimum(1, t / .05) * np.minimum(1, (d - t) / .08) * .3
def noise(d): return rng.standard_normal(int(d * SR))
def dec(x, k): t = np.arange(len(x)) / SR; return x * np.exp(-t * k)

# -------------------------------------------------------------- música
BPM = 116; BEAT = 60 / BPM
CH = {"C": (48, (0, 4, 7)), "Am": (45, (0, 3, 7)), "Dm": (50, (0, 3, 7)), "G7": (43, (0, 4, 7, 10)), "E7": (52, (0, 4, 7, 10)), "Em": (52, (0, 3, 7))}
SECT = [(0, 11.7, "A", ["C", "Am", "Dm", "G7"]), (11.7, 30.45, "B", ["C", "Am", "Dm", "G7"]), (30.45, 34.9, "C", ["Am", "Dm", "E7", "Am"]),
        (34.9, 40.04, "D", ["Am", "E7", "Dm", "E7"]), (40.04, 99, "E", ["C", "G7", "C", "C"])]
mus = np.zeros((N, 2))
t = 0.0; bar = 0
while t < N / SR:
    sec = next(s for s in SECT if s[0] <= t < s[1])
    name, chords = sec[2], sec[3]
    cn = chords[bar % 4]; root, iv = CH[cn]
    for b in range(4):
        tb = t + b * BEAT
        if tb >= N / SR: break
        # bajo
        if name == "C":
            if b in (0, 2): put(mus, lp(pluck(mf(root), 1.0, .6), 500), tb, .9, -.1)
        else:
            nb = root if b in (0, 2) else root + iv[2] if iv[2] < 12 else root + 7
            put(mus, lp(pluck(mf(nb), .45, .6), 600), tb, .8, -.15)
        # acorde "pah"
        if name in ("A", "B", "E") and b in (1, 3):
            for k, o in enumerate(iv):
                put(mus, pluck(mf(root + 24 + o), .3, 1.2), tb + k * .012, .26, .2)
        if name == "D":
            for k in range(2): put(mus, pluck(mf(root + 24 + iv[k % len(iv)] + (12 if k else 0)), .18, 1.4), tb + k * BEAT / 2, .3, .15)
        if name == "C" and b == 0:
            for o in iv: put(mus, reed(mf(root + 24 + o), 4 * BEAT * .98, 4.6), tb, .22, .0)
        # melodía acordeón
        if name in ("B", "E") or (name == "A" and bar > 1):
            rs = np.random.default_rng(bar * 13 + b)
            for e8 in range(2):
                if rs.random() < .72 or name == "E":
                    n_ = root + 36 + iv[rs.integers(0, len(iv))] + (12 if rs.random() < .3 else 0)
                    put(mus, reed(mf(n_), BEAT * .46, 5.8), tb + e8 * BEAT / 2, .2, -.05)
        if name == "D" and b % 2 == 0:
            put(mus, reed(mf(root + 36 + iv[1]), BEAT * .9, 7.5), tb, .18)
        # percusión suave
        if name in ("B", "E", "A") and t > 1.0:
            h = hp(noise(.05), 6000) * np.exp(-tt(.05) * 90); put(mus, h, tb + BEAT / 2, .05); put(mus, h, tb, .035)
            if b in (1, 3): s_ = bp(noise(.12), 1500, 5000) * np.exp(-tt(.12) * 28); put(mus, s_, tb, .08)
            if b in (0, 2): k_ = np.sin(2 * np.pi * (60 + 90 * np.exp(-tt(.2) * 30)) * tt(.2)) * np.exp(-tt(.2) * 18); put(mus, k_, tb, .22)
    t += 4 * BEAT; bar += 1
# final: acorde de victoria
for o in (0, 4, 7, 12, 16):
    put(mus, reed(mf(48 + o), 2.4, 5), 42.16, .3); put(mus, pluck(mf(60 + o), 2.0, 1.2), 42.16, .3)
tim = bp(noise(.5), 200, 600) * np.exp(-tt(.5) * 7); put(mus, tim, 42.16, .5)
# reverb
ir = np.stack([noise(1.1) * np.exp(-tt(1.1) * 4.2), noise(1.1) * np.exp(-tt(1.1) * 4.2)], 1)
wet = np.stack([fftconvolve(mus[:, c], ir[:, c])[:N] for c in range(2)], 1)
mus = mus + .18 * wet / (np.abs(wet).max() + 1e-9) * np.abs(mus).max()

# -------------------------------------------------------------- SFX
sfx = np.zeros((N, 2))
def whoosh(t0, d=.35, g=.5, up=False):
    x = noise(d); tx = tt(d); env = np.sin(np.pi * np.minimum(1, tx / d)) ** 2
    y = bp(x, 400, 5000) * env
    put(sfx, y, t0 - d / 2, g, -.3 if not up else .3)
def thud(t0, g=.9, f0=90):
    x = np.sin(2 * np.pi * (f0 * np.exp(-tt(.3) * 8) + 35) * tt(.3)) * np.exp(-tt(.3) * 13); put(sfx, x, t0, g)
def bang(t0, g=1.0):
    thud(t0, g * .9, 120); put(sfx, lp(noise(.25), 4000) * np.exp(-tt(.25) * 20), t0, g * .6)
def ting(t0, f=2093, g=.4, d=.9):
    x = (np.sin(2 * np.pi * f * tt(d)) + .5 * np.sin(2 * np.pi * f * 2.76 * tt(d))) * np.exp(-tt(d) * 5.5); put(sfx, x, t0, g, .1)
def pop(t0, g=.5, f=520):
    d = .12; x = np.sin(2 * np.pi * (f + 900 * np.exp(-tt(d) * 40)) * tt(d)) * np.exp(-tt(d) * 30); put(sfx, x, t0, g)
def clink(t0, g=.3, pan=0.0):
    f = rng.uniform(2800, 4200); d = .35
    x = (np.sin(2 * np.pi * f * tt(d)) + .6 * np.sin(2 * np.pi * f * 1.51 * tt(d))) * np.exp(-tt(d) * 14); put(sfx, x, t0, g, pan)
def clang(t0, g=.5):
    d = .7; f = rng.uniform(380, 520); x = sum(np.sin(2 * np.pi * f * k * tt(d)) * np.exp(-tt(d) * (6 + 3 * k)) / k for k in (1, 2.4, 3.9)); put(sfx, x, t0, g)
def step(t0, g=.18, pan=0.0):
    d = .08; put(sfx, lp(noise(d), 900) * np.exp(-tt(d) * 45), t0, g, pan)
def whistle(t0, d=.6, g=.35, f=2900):
    tx = tt(d); fm = f + 160 * np.sin(2 * np.pi * 28 * tx)
    x = np.sin(2 * np.pi * np.cumsum(fm) / SR) * np.minimum(1, tx / .03) * np.minimum(1, (d - tx) / .05); put(sfx, x, t0, g)
def horn(t0):
    d = .32
    for f, o in ((330, 0), (415, .0)):
        x = np.sign(np.sin(2 * np.pi * f * tt(d))) * .25 * np.minimum(1, tt(d) / .01) * np.minimum(1, (d - tt(d)) / .03); put(sfx, lp(x, 2200), t0 + o, .5, .3)
def paper(t0, g=.18): d = .18; put(sfx, bp(noise(d), 2500, 9000) * np.sin(np.pi * tt(d) / d), t0, g)
def siren(t0, d=1.6, g=.18):
    tx = tt(d); f = 700 + 350 * np.sign(np.sin(2 * np.pi * 1.6 * tx)); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, tx / .1) * np.minimum(1, (d - tx) / .2); put(sfx, x, t0, g)
def chuff(t0, g=.3): d = .16; put(sfx, lp(noise(d), 1800) * np.exp(-tt(d) * 20), t0, g, .2)
def rain(t0, d, g=.06): x = hp(noise(d), 2500) * np.minimum(1, tt(d) / .4) * np.minimum(1, (d - tt(d)) / .4); put(sfx, x, t0, g)
def wah(t0):
    d = 1.0; tx = tt(d); f = 330 * np.exp(-tx * .55)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (.6 + .4 * np.sin(2 * np.pi * 6 * tx)) * np.minimum(1, (d - tx) / .1)
    put(sfx, x + .4 * np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * .3, t0, .28)
def poof(t0, g=.35): d = .35; put(sfx, lp(noise(d), 1800) * np.exp(-tt(d) * 9), t0, g)
def stamp(t0): bang(t0, 1.0); poof(t0, .3)

for tb in (1.91, 4.43, 6.80, 11.70, 14.14, 15.53, 20.10, 22.40, 25.40, 27.90): whoosh(tb, .3, .55)
horn(.8); whoosh(2.41, .3, .4); bang(2.69, .9); poof(2.72)
whoosh(4.98, .4, .4); ting(6.03, 2637, .35)
for i, tp in enumerate((7.7, 8.3, 8.9, 9.4)): pop(tp, .4, 440 + i * 60)
for k in range(15): clink(7.2 + k * .2, .22, (k % 3 - 1) * .3)
pop(10.45, .6, 700); ting(10.5, 2349, .45); ting(10.62, 3136, .3)
for i in range(6): pop(11.82 + i * .3 + .2, .35, 380 + i * 40); paper(11.82 + i * .3 + .2, .15)
for k in range(6): put(sfx, bp(noise(.08), 800, 3000) * np.exp(-tt(.08) * 30), 14.14 + .1 * k, .0)
ting(14.62, 3520, .4); ting(14.66, 4186, .2); horn(14.5)
pop(16.43, .5, 600); ting(16.5, 2637, .4); ting(16.62, 3136, .35); ting(16.75, 3951, .3)
thud(18.64, .35, 70); thud(19.21, .9, 80); bang(19.34, 1.0); poof(19.25)
for i, tp in enumerate((20.10, 20.65, 21.20, 21.75)): pop(tp, .45, 500 + i * 80); ting(tp + .02, 2000 + i * 300, .3)
for k in range(3): bang(22.1 - 0.0 + k * 0, .0)
bang(22.1, .85)
for idx in range(9): clang(22.4 + .36 + idx * .1, .22 + .02 * idx)
pop(23.2, .5, 700); ting(23.2, 2637, .4)
for k in range(10): clink(22.9 + k * .1, .2, (k % 2 - .5) * .6)
thud(24.6, .5, 70); 
for k in range(10): paper(24.7 + k * .05, .06)
ting(25.1, 3136, .3)
pop(25.8, .45, 560)
for k in range(24): step(25.45 + k * .105, .14, .0)
whistle(28.6, .5, .3); 
for k in range(26): chuff(28.6 + k * (.2 - k * .004), .22 * (.6 + k / 26 * .6))
for k in range(12): step(27.95 + k * .1, .14)
wah(30.7); rain(30.45, 2.7)
pop(33.79, .5, 480); thud(34.0, .0)
pop(35.05, .45, 420)
for k in range(14): step(35.2 + k * .17, .1, -.3 + .05 * k)
pop(37.74, .5, 460); put(sfx, np.sin(2 * np.pi * (180 + 700 * np.minimum(1, tt(.9) / .9)) * tt(.9)) * np.minimum(1, (.9 - tt(.9)) / .05) * .12, 37.54, .5)
bang(38.57, .9); whistle(38.55, .6, .35); whistle(38.9, .5, .3, 3100); siren(38.6, 1.6, .14)
for k in range(16): step(38.6 + k * .1, .22, (k % 2 - .5) * .6)
ting(40.54, 3951, .45); ting(40.6, 5274, .25)
stamp(42.16); ting(42.2, 1568, .3, 1.4)
for tb in (42.16,): put(sfx, lp(noise(.9), 3000) * np.exp(-tt(.9) * 5), tb, .25)

# -------------------------------------------------------------- mezcla
V = np.stack([np.pad(vy, (0, N - len(vy)))] * 2, 1)
vr = np.abs(V[:, 0])
voiced = lp(vr, 8, 2) > np.percentile(vr, 55) * .5
rms_v = np.sqrt(np.mean(V[voiced, 0] ** 2))
# sidechain
envv = lp(np.abs(V[:, 0]), 6, 2); envv = np.clip(envv / (np.percentile(envv, 95) + 1e-9), 0, 1)
duck = 1 - .45 * envv
mus = mus * duck[:, None]
rms_m = np.sqrt(np.mean(mus[voiced, 0] ** 2)); mus *= .5 * rms_v / (rms_m + 1e-9)
pk_v = np.abs(V).max()
sfx *= min(1.0, .5 * pk_v / (np.abs(sfx).max() + 1e-9))
mix = V + mus + sfx
mix *= 10 ** (2 / 20)
mix = np.tanh(mix * .9) / .9 if np.abs(mix).max() > .95 else mix
mix = np.clip(mix, -.95, .95)
print("peak voz", pk_v, "rms voz", rms_v, "rms mus", np.sqrt(np.mean(mus[voiced, 0] ** 2)), "peak sfx", np.abs(sfx).max(), "mix peak", np.abs(mix).max())
import wave
w = wave.open("mix.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((mix * 32767).astype("<i2").tobytes()); w.close()
