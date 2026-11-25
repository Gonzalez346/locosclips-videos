"""Banda sonora original por actos + efectos sincronizados + mezcla (voz intacta, música 50%, SFX <=50% pico)."""
import numpy as np, subprocess, wave
from scipy.signal import butter, lfilter, fftconvolve
SR = 44100
rng = np.random.default_rng(5)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", "voice.mp3", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
vy = np.frombuffer(raw, np.float32).copy()
DUR = 52.3
N = int(DUR * SR) + SR // 4
def mf(m): return 440 * 2 ** ((m - 69) / 12)
def tt(d): return np.arange(max(1, int(d * SR))) / SR
def noise(d): return rng.standard_normal(max(1, int(d * SR)))
def lp(x, fc, o=2): b, a = butter(o, min(.99, fc / (SR / 2))); return lfilter(b, a, x)
def hp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), "high"); return lfilter(b, a, x)
def bp(x, f1, f2, o=2): b, a = butter(o, [f1 / (SR / 2), min(.99, f2 / (SR / 2))], "band"); return lfilter(b, a, x)
def put(buf, x, t0, g=1.0, pan=0.0):
    i = int(t0 * SR)
    if i < 0: x = x[-i:]; i = 0
    if i >= len(buf) or len(x) == 0: return
    n = min(len(x), len(buf) - i)
    buf[i:i + n, 0] += x[:n] * g * (1 - max(0, pan)); buf[i:i + n, 1] += x[:n] * g * (1 + min(0, pan))
def env(d, a=.005, r=.05):
    t = tt(d); return np.minimum(1, t / a) * np.minimum(1, np.maximum(0, (d - t) / r))

# ---------------------------------------------------------------- instrumentos
def pluck(f, d=.5, br=1.0, dec=5):
    t = tt(d); x = np.zeros_like(t)
    for k in range(1, 9): x += np.sin(2 * np.pi * f * k * t + k) / k ** (1.3 / br) * np.exp(-t * (dec * .8 + k * 4))
    return x * np.minimum(1, t * 800) * .5
def reed(f, d=.6, vib=5.3, bright=1.0):
    t = tt(d); ph = 2 * np.pi * f * t + .003 * np.sin(2 * np.pi * vib * t) * f / 30
    x = sum(np.sin(k * ph) / k ** (1.1 / bright) * (1 if k % 2 else .55) for k in range(1, 8))
    return x * env(d, .03, .07) * .3
def organ(f, d=.5):
    t = tt(d); x = sum(a * np.sin(2 * np.pi * f * k * t) for k, a in ((1, 1), (2, .7), (3, .45), (4, .3), (6, .18), (8, .1)))
    return x * env(d, .008, .04) * .22
def brass(f, d=.5, bright=1.0):
    t = tt(d); x = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 12))
    sw = np.minimum(1, t / .06)
    y = lp(x * sw, 900 + 2600 * bright)
    return y * env(d, .03, .08) * .28
def bell(f, d=1.4, k=4.0):
    t = tt(d)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * k) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * k * 1.8) + .25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * k * 3)
    return x * np.minimum(1, t * 2000) * .35
def pad(f, d=2.0, a=.3):
    t = tt(d); x = np.zeros_like(t)
    for det in (-.006, 0, .007):
        ph = 2 * np.pi * f * (1 + det) * t
        x += sum(np.sin(k * ph) / k for k in range(1, 7))
    return lp(x, 1800) * env(d, a, .4) * .12
def kick(g=1.0):
    t = tt(.3); return np.sin(2 * np.pi * (48 + 110 * np.exp(-t * 28)) * t) * np.exp(-t * 11) * g
def snare(g=1.0):
    t = tt(.2); return (bp(noise(.2), 1200, 6000) * .8 + np.sin(2 * np.pi * 190 * t) * .5) * np.exp(-t * 22) * g
def hat(g=1.0, d=.05):
    return hp(noise(d), 7000) * np.exp(-tt(d) * 80) * g
def shaker(g=1.0): d = .07; return bp(noise(d), 5000, 12000) * np.sin(np.pi * tt(d) / d) * g
def surdo(g=1.0):
    t = tt(.5); return np.sin(2 * np.pi * (62 + 30 * np.exp(-t * 18)) * t) * np.exp(-t * 6) * g
def timp(f=73.4, d=1.6): t = tt(d); return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 1.5 * t)) * np.exp(-t * 2.2) * .7
def crash(g=1.0): d = 2.0; return hp(noise(d), 3000) * np.exp(-tt(d) * 2.5) * g

MAJ = (0, 4, 7); MIN = (0, 3, 7); DOM = (0, 4, 7, 10)
mus = np.zeros((N, 2))
def bars(t0, t1, bpm):
    beat = 60 / bpm; t = t0; b = 0
    while t < t1 - 1e-3:
        yield b, t, beat
        t += beat; b += 1

def sec_intro(t0, t1):
    for o in (0, 7, 12, 16): put(mus, pad(mf(45 + o), t1 - t0 + .3, .8), t0, .5, (o % 2 - .5) * .4)
    for i, tb in enumerate(np.arange(t0 + .1, t1, .3)):
        put(mus, bell(mf([81, 84, 88, 86, 84, 88, 91, 88, 86, 84, 83, 81][i % 12]), 1.0, 5), tb, .25, (i % 3 - 1) * .5)
    for b, tb, bt in bars(t0, t1, 120): put(mus, kick(.35 + .15 * (tb - t0)), tb)
    r = tt(t1 - t0); put(mus, hp(noise(t1 - t0), 2500) * (r / (t1 - t0)) ** 3 * .18, t0)

def sec_sneak(t0, t1, root=45):
    walk = [0, 0, 3, 2, 1, 0, -2, -1]
    for b, tb, bt in bars(t0, t1, 112):
        put(mus, lp(pluck(mf(root - 12 + walk[b % 8] + 12), .3, .7, 9), 900), tb, .9, -.2)
        if b % 2 == 1:
            for k, o in enumerate(MIN): put(mus, pluck(mf(root + 12 + o), .15, 1.3, 14), tb + bt / 2 + k * .006, .3, .3)
        put(mus, hat(.25), tb + bt / 2, 1, .4)

def sec_alarm(t0, t1, root=45):
    for b, tb, bt in bars(t0, t1, 160):
        put(mus, kick(.8), tb) if b % 2 == 0 else put(mus, snare(.6), tb)
        put(mus, hat(.3), tb + bt / 2)
        put(mus, lp(pluck(mf(root - 12 + (0 if b % 4 < 2 else 1)), .2, .8, 10), 800), tb, 1.0)
        if b % 4 == 0:
            for o in (0, 3, 6): put(mus, brass(mf(root + 12 + o), .22, 1.2), tb, .55)

def sec_beat60(t0, t1, root=48):
    prog = [(0, MAJ), (9, MIN), (5, MAJ), (7, DOM)]
    for b, tb, bt in bars(t0, t1, 132):
        r, q = prog[(b // 4) % 4]
        bn = [0, 7, 12, 7][b % 4]
        put(mus, lp(pluck(mf(root - 12 + r + bn), .3, .8, 7), 1000), tb, .8, -.15)
        if b % 2 == 1:
            for o in q[:3]: put(mus, organ(mf(root + 12 + r + o), bt * .45), tb, .5, .2)
            put(mus, snare(.5), tb)
        else: put(mus, kick(.7), tb)
        for k in range(2): put(mus, shaker(.35), tb + k * bt / 2, 1, .5)

def sec_detective(t0, t1, root=43):
    walk = [0, 3, 5, 6, 7, 6, 5, 3]
    for b, tb, bt in bars(t0, t1, 98):
        put(mus, lp(pluck(mf(root - 12 + walk[b % 8]), .45, .6, 6), 700), tb, 1.0, -.1)
        put(mus, hat(.18, .08), tb + bt * .66, 1, .4)
        if b % 4 == 2:
            for o in (0, 3, 7, 10): put(mus, pluck(mf(root + 12 + o), .2, 1.4, 12), tb + o * .004, .28, .25)

def sec_panic(t0, t1, root=46):
    for b, tb, bt in bars(t0, t1, 172):
        put(mus, kick(.7), tb) if b % 2 == 0 else put(mus, snare(.55), tb)
        for k in range(2): put(mus, reed(mf(root + 24 + (0 if (b * 2 + k) % 2 == 0 else 1)), bt / 2 * .95, 9, 1.4), tb + k * bt / 2, .35, .1)
        put(mus, lp(pluck(mf(root - 12), .2, .7), 700), tb, .8)

def sec_stadium(t0, t1, root=48):
    for b, tb, bt in bars(t0, t1, 120):
        if b % 2 == 0:
            for o in MAJ: put(mus, brass(mf(root + o + 12), bt * 1.6, .9), tb, .4)
        put(mus, snare(.25), tb + bt / 2)

def sec_clock(t0, t1):
    for o in (0, 4, 7): put(mus, pad(mf(57 + o), t1 - t0, .4), t0, .35)

def sec_walk(t0, t1, root=48):
    prog = [(0, MAJ), (5, MAJ), (7, DOM), (0, MAJ)]
    mel = [12, 16, 19, 16, 14, 17, 21, 17, 11, 14, 19, 14, 12, 16, 19, 24]
    for b, tb, bt in bars(t0, t1, 120):
        r, q = prog[(b // 4) % 4]
        put(mus, lp(pluck(mf(root - 12 + r + (0 if b % 2 == 0 else 7)), .28, .8, 8), 900), tb, .9, -.15)
        for k, o in enumerate(q[:3]): put(mus, pluck(mf(root + 12 + r + o), .18, 1.6, 12), tb + bt / 2 + k * .008, .26, .25)
        if b % 2 == 0: put(mus, bell(mf(root + 12 + r + mel[b % 16] - (r if b % 4 else 0)), .6, 6), tb, .3, .1)
        put(mus, kick(.45), tb) if b % 2 == 0 else put(mus, hat(.4, .03), tb)

def sec_tiptoe(t0, t1, root=45):
    notes = [0, 3, 7, 3, 1, 4, 7, 4, 0, 3, 8, 7]
    for b, tb, bt in bars(t0, t1, 104):
        for k in range(2):
            n = notes[(b * 2 + k) % 12]
            put(mus, pluck(mf(root + 12 + n), .14, 1.2, 14), tb + k * bt / 2, .45, (k - .5) * .5)
        if b % 2 == 0: put(mus, lp(pluck(mf(root - 12), .3, .6), 600), tb, .8)

def sec_riser(t0, t1):
    d = t1 - t0; t = tt(d)
    f = 200 * 2 ** (t / d * 3)
    put(mus, np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2 * .18, t0)
    put(mus, bp(noise(d), 800, 6000) * (t / d) ** 3 * .25, t0)
    for i, tb in enumerate(np.arange(t0, t1, .09)): put(mus, timp(73.4, .25) * .3 * (tb - t0) / d, tb)

def sec_reveal(t0, t1, root=48):
    d = t1 - t0
    for o in (0, 7, 12, 16, 19, 24): put(mus, pad(mf(root + o), d, .05), t0, .7, (o % 2 - .5) * .5)
    for o in (0, 4, 7, 12): put(mus, brass(mf(root + 12 + o), 1.6, 1.3), t0, .45)
    put(mus, timp(65.4, 2.0), t0, 1.0); put(mus, crash(.5), t0)
    for i, tb in enumerate(np.arange(t0 + .05, t1, .12)): put(mus, bell(mf(84 + [0, 4, 7, 12, 16, 12, 7, 4][i % 8]), .8, 5), tb, .22, (i % 2 - .5) * .7)

def sec_tense(t0, t1, root=33):
    d = t1 - t0
    put(mus, pad(mf(root), d, .3), t0, 1.0); put(mus, pad(mf(root + 1 + 12), d, .5), t0, .35)
    for b, tb, bt in bars(t0, t1, 90): put(mus, lp(pluck(mf(root + 12), .25, .5), 400), tb, 1.0)

def sec_relief(t0, t1, root=53):
    for o in (0, 4, 7, 12): put(mus, pad(mf(root + o), t1 - t0, .05), t0, .7)
    for i, o in enumerate((12, 16, 19, 24)): put(mus, bell(mf(root + 12 + o), 1.2, 3), t0 + i * .08, .35)

def sec_anthem(t0, t1, root=48):
    prog = [(0, MAJ), (7, MAJ), (9, MIN), (5, MAJ)]
    for b, tb, bt in bars(t0, t1, 116):
        r, q = prog[(b // 4) % 4]
        for o in q: put(mus, brass(mf(root + 12 + r + o), bt * .9, 1.1), tb, .32)
        put(mus, lp(pluck(mf(root - 12 + r), .4, .7), 800), tb, .9)
        put(mus, kick(.8), tb) if b % 2 == 0 else put(mus, snare(.7), tb)
        for k in range(3): put(mus, snare(.18), tb + bt * (k + 1) / 4)
        if b % 8 == 0: put(mus, crash(.35), tb)
        if b % 2 == 0: put(mus, bell(mf(root + 24 + r + q[(b // 2) % 3]), .7, 4), tb, .3)

def sec_timewarp(t0, t1):
    d = t1 - t0; t = tt(d)
    f = 1200 * 2 ** (-t / d * 3)
    put(mus, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, .05, .2) * .12, t0)
    for tb in np.arange(t0, t1, .07): put(mus, hp(noise(.02), 3000) * np.exp(-tt(.02) * 200) * .3, tb, 1, .3)

def sec_rio(t0, t1, root=45):
    for b, tb, bt in bars(t0, t1, 104):
        put(mus, surdo(.9 if b % 2 else .6), tb)
        for k in range(4): put(mus, shaker(.4 if k % 2 else .2), tb + k * bt / 4, 1, .4)
        if b % 2 == 1: put(mus, bp(noise(.05), 2000, 6000) * np.exp(-tt(.05) * 60), tb + bt * .75, .5, -.4)
        q = MIN if b % 4 < 2 else (0, 4, 7)
        rr = 0 if b % 4 < 2 else 7
        for k, o in enumerate(q): put(mus, pluck(mf(root + 12 + rr + o), .18, 1.4, 12), tb + bt * .5 + k * .006, .3, .2)

def sec_musicbox(t0, t1, root=57):
    prog = [(0, MIN), (-4, MAJ), (-9, MAJ), (-5, MAJ)]
    d = t1 - t0
    for b, tb, bt in bars(t0, t1, 76):
        r, q = prog[(b // 4) % 4]
        if b % 4 == 0: put(mus, pad(mf(root - 12 + r), bt * 4.2, .5), tb, .55)
        for k in range(2):
            n = [0, 7, 12, 7][(b * 2 + k) % 4]
            put(mus, bell(mf(root + 12 + r + (q[1] if n == 7 and k == 1 else n)), 1.6, 2.5), tb + k * bt / 2, .32, (k - .5) * .6)

for fn, a, b in ((sec_intro, 0.0, 3.6), (sec_sneak, 3.6, 4.95), (sec_alarm, 4.95, 6.05), (sec_beat60, 6.05, 8.35), (sec_detective, 8.35, 11.24),
                 (sec_panic, 11.24, 13.56), (sec_stadium, 13.56, 15.45), (sec_clock, 16.38, 18.12), (sec_walk, 18.12, 21.6), (sec_tiptoe, 22.46, 27.77),
                 (sec_riser, 27.77, 28.85), (sec_reveal, 28.85, 30.74), (sec_tense, 30.74, 34.95), (sec_relief, 34.95, 36.0), (sec_anthem, 36.0, 42.53),
                 (sec_timewarp, 42.53, 43.92), (sec_rio, 43.92, 46.75), (sec_musicbox, 46.75, 52.3)):
    seg = np.zeros((N, 2)); bak = mus.copy(); mus[:] = 0
    fn(a, b)
    i0 = int(a * SR); i1 = min(N, int((b + .35) * SR))
    w = np.zeros(N); w[i0:i1] = 1
    fo = int(.3 * SR); w[max(i0, i1 - fo):i1] *= np.linspace(1, 0, i1 - max(i0, i1 - fo))
    mus[:] = bak + mus * w[:, None]
mus[int(51.6 * SR):] *= np.linspace(1, 0, N - int(51.6 * SR))[:, None]
ir = np.stack([noise(1.4) * np.exp(-tt(1.4) * 3.5), noise(1.4) * np.exp(-tt(1.4) * 3.5)], 1)
wet = np.stack([fftconvolve(mus[:, c], ir[:, c])[:N] for c in range(2)], 1)
mus = mus + .22 * wet / (np.abs(wet).max() + 1e-9) * np.abs(mus).max()

# ---------------------------------------------------------------- efectos
sfx = np.zeros((N, 2))
def whoosh(t0, d=.35, g=.6, pan=0.0):
    x = noise(d); tx = tt(d); e = np.sin(np.pi * np.minimum(1, tx / d)) ** 2
    lo = bp(x, 300, 1500) * e; hi = bp(x, 1500, 7000) * e * (tx / d)
    put(sfx, lo + hi, t0 - d / 2, g, pan)
def boom(t0, g=1.0): put(sfx, np.sin(2 * np.pi * (40 + 70 * np.exp(-tt(.8) * 9)) * tt(.8)) * np.exp(-tt(.8) * 4), t0, g); put(sfx, lp(noise(.4), 1500) * np.exp(-tt(.4) * 9), t0, g * .5)
def hit(t0, g=.8): put(sfx, kick(1.0), t0, g); put(sfx, snare(.5), t0, g)
def popfx(t0, g=.5, f=500): d = .14; put(sfx, np.sin(2 * np.pi * (f + 900 * np.exp(-tt(d) * 40)) * tt(d)) * np.exp(-tt(d) * 26), t0, g)
def ting(t0, f=2093, g=.4, d=1.0, pan=0.0): put(sfx, bell(f, d, 4) * 2, t0, g, pan)
def boing(t0, g=.4):
    d = .45; t = tt(d); f = 300 + 250 * np.sin(2 * np.pi * 7 * t) * np.exp(-t * 4) + 200 * t
    put(sfx, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5), t0, g)
def step(t0, g=.2, pan=0.0, soft=False): d = .07; put(sfx, lp(noise(d), 700 if soft else 1200) * np.exp(-tt(d) * 50), t0, g, pan)
def paw(t0, g=.12): d = .04; put(sfx, bp(noise(d), 1500, 5000) * np.exp(-tt(d) * 90), t0, g, .2)
def creak(t0, d=.35, g=.25, f0=600, f1=900):
    t = tt(d); f = np.linspace(f0, f1, len(t)) + 40 * np.sin(2 * np.pi * 30 * t)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * .3; put(sfx, bp(x, 400, 3000) * env(d, .03, .08), t0, g)
def alarm(t0, d):
    t = tt(d); am = (np.sin(2 * np.pi * 22 * t) > 0).astype(float)
    x = (np.sin(2 * np.pi * 2100 * t) + .6 * np.sin(2 * np.pi * 2900 * t)) * am * env(d, .01, .1); put(sfx, x, t0, .25)
def bark(t0, g=.8, f0=560, pan=.2):
    d = .18; t = tt(d); f = f0 * (1 - .35 * t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(k * ph) / k for k in range(1, 12)) + .5 * noise(d)
    y = bp(x, 500, 3000) * np.exp(-t * 14) * np.minimum(1, t * 300)
    put(sfx, y, t0, g, pan)
def sniff(t0, g=.35): d = .09; put(sfx, bp(noise(d), 2500, 8000) * np.sin(np.pi * tt(d) / d) ** 2, t0, g, .3)
def rustle(t0, d=.4, g=.3): x = bp(noise(d), 1500, 9000) * (np.abs(lp(noise(d), 30)) * 3) * env(d, .02, .1); put(sfx, x, t0, g, .4)
def paperfx(t0, d=.25, g=.3): x = bp(noise(d), 2000, 10000) * (np.abs(lp(noise(d), 60)) * 4) * env(d, .01, .05); put(sfx, x, t0, g)
def tear(t0, d=.8, g=.4):
    t = tt(d); cr = (rng.random(len(t)) < (.002 + .02 * t / d)).astype(float)
    x = bp(noise(d) * .3 + cr * 3, 1500, 9000) * env(d, .05, .1) * (.4 + t / d); put(sfx, x, t0, g)
def horn(t0):
    for k, o in enumerate((0, .2)):
        d = .16; x = np.sign(np.sin(2 * np.pi * 400 * tt(d))) * .3 + np.sign(np.sin(2 * np.pi * 500 * tt(d))) * .3
        put(sfx, lp(x, 2500) * env(d, .01, .03), t0 + o, .35, -.3)
def engine(t0, d, pan0=.8, pan1=-.8):
    t = tt(d); x = lp(noise(d), 180) * 6 + np.sin(2 * np.pi * 42 * t) * .4
    e = np.sin(np.pi * t / d) ** 1.5
    n = len(x); half = n // 2
    put(sfx, x[:half] * e[:half], t0, .35, pan0); put(sfx, x[half:] * e[half:], t0 + half / SR, .35, pan1)
def chirp(t0, g=.08): d = .12; t = tt(d); put(sfx, np.sin(2 * np.pi * (3200 + 1500 * np.sin(2 * np.pi * 18 * t)) * t) * env(d, .01, .03), t0, g, rng.uniform(-.7, .7))
def crickets(t0, d):
    for tb in np.arange(t0, t0 + d, .55):
        for k in range(3):
            x = np.sin(2 * np.pi * 4400 * tt(.025)) * np.sin(np.pi * tt(.025) / .025); put(sfx, x, tb + k * .04, .1, .5)
            put(sfx, x, tb + .27 + k * .04, .07, -.5)
def tick(t0, g=.15): put(sfx, hp(noise(.015), 3000) * np.exp(-tt(.015) * 300), t0, g, .4)
def rainfx(t0, d, g=.08): put(sfx, hp(noise(d), 2500) * env(d, .3, .3), t0, g)
def crowd(t0, d, g=.15, cheer=0.0):
    t = tt(d); x = bp(noise(d), 300, 3500) * (1 + .3 * lp(noise(d), 3))
    e = env(d, .3, .3) * (1 + cheer * np.clip((t - .0) / max(.1, d), 0, 1))
    put(sfx, x * e, t0, g)
def cheer(t0, g=.6):
    d = 2.5; t = tt(d); x = bp(noise(d), 400, 4000) * (1 + .5 * np.sin(2 * np.pi * 3 * t)) * np.exp(-t * .8) * np.minimum(1, t / .08)
    put(sfx, x, t0, g)
    for k in range(6):
        f = rng.uniform(500, 900); dd = .7; tw = tt(dd); y = np.sin(2 * np.pi * np.cumsum(f * (1 + .25 * tw)) / SR) * env(dd, .05, .2) * .15
        put(sfx, y, t0 + rng.uniform(0, .4), 1, rng.uniform(-.8, .8))
def popper(t0, g=.5): put(sfx, bp(noise(.08), 800, 6000) * np.exp(-tt(.08) * 40), t0, g, rng.uniform(-.6, .6))
def clap(t0, g=.15): put(sfx, bp(noise(.04), 900, 4000) * np.exp(-tt(.04) * 70), t0, g, rng.uniform(-.7, .7))
def chatter(t0, d, g=.06): x = bp(noise(d), 300, 2500) * (.6 + .4 * np.abs(lp(noise(d), 6)) * 4) * env(d, .2, .2); put(sfx, x, t0, g)
def slurp(t0, g=.35): d = .22; t = tt(d); x = bp(noise(d), 600, 3500) * (np.sin(2 * np.pi * 12 * t) ** 2) * env(d, .01, .05); put(sfx, x, t0, g, .1)
def stamp(t0): boom(t0, 1.0); put(sfx, snare(1.2), t0, .8)
def switch(t0): put(sfx, hp(noise(.03), 1500) * np.exp(-tt(.03) * 120), t0, .5); boom(t0 + .01, .25)
def hum(t0, d): put(sfx, (np.sin(2 * np.pi * 100 * tt(d)) + .3 * np.sin(2 * np.pi * 200 * tt(d))) * env(d, .1, .5) * .06, t0, 1)
def wind(t0, d, g=.12): x = lp(bp(noise(d), 200, 1200), 800) * (1 + .5 * np.sin(2 * np.pi * .3 * tt(d))) * env(d, .8, .8); put(sfx, x, t0, g)
def whimper(t0, g=.25):
    d = .7; t = tt(d); f = 950 - 300 * t / d + 25 * np.sin(2 * np.pi * 6 * t)
    put(sfx, np.sin(2 * np.pi * np.cumsum(f) / SR) * env(d, .08, .25) * .6, t0, g, .3)
def shimmer(t0, d=1.0, g=.25):
    for i in range(8): ting(t0 + i * d / 8, [2093, 2637, 3136, 4186][i % 4], g * (.5 + .5 * i / 8), .9, (i % 2 - .5) * .8)
def scratch(t0): d = .25; t = tt(d); f = 900 + 700 * np.sin(2 * np.pi * 6 * t); put(sfx, bp(noise(d), 500, 4000) * np.abs(np.sin(2 * np.pi * np.cumsum(f) / SR / 40)) * env(d, .01, .05), t0, .5)

# 1. héroe / sala
whoosh(.05, .5, .5); shimmer(.1, 1.2, .25); hit(.12, .5); popfx(.42, .35, 600)
whoosh(1.7, .3, .3)
# 2. robo
whoosh(3.6, .35, .5); boom(3.6, .35)
for k in range(5): step(3.62 + k * .09, .1, .3, True)
creak(4.0, .25, .25, 700, 1000); whoosh(4.45, .2, .35, -.2)
alarm(4.95, 1.15); hit(5.05, .7)
for k in range(12): step(4.98 + k * .09, .2, -.2 - k * .05)
# 3. Londres
whoosh(6.05, .4, .55); engine(6.05, 2.3); horn(7.0); hit(6.2, .4); popfx(6.45, .3, 700)
for k in range(8): chirp(6.2 + k * .27)
# 4. policía
whoosh(8.35, .3, .5); boing(8.4, .25); boing(10.0, .3); boing(10.35, .3); popfx(10.75, .45, 420)
# 5. pánico
whoosh(11.24, .45, .7, .3); boom(11.62, .7); paperfx(11.62, .35, .5); chatter(12.3, 1.26, .1); hit(12.62, .6)
# 6. estadio
whoosh(13.56, .4, .5); crowd(13.56, 1.9, .14); scratch(15.42); crickets(15.5, .88); boing(15.62, .35); hit(15.45, .45)
# 7. semana
whoosh(16.38, .3, .45); rainfx(16.38, 1.74, .07)
for tb in np.arange(16.4, 18.1, .12): tick(tb, .14)
for i in range(7): paperfx(16.55 + i * .15, .12, .25)
hit(17.5, .5)
# 8. paseo
whoosh(18.12, .35, .5)
for tb in np.arange(18.2, 21.6, .36): step(tb, .14, -.3)
for tb in np.arange(18.15, 21.6, .17): paw(tb, .08)
for k in range(5): chirp(18.4 + k * .5)
whoosh(20.58, .25, .3, -.6); bark(20.74, .9); bark(20.92, .8, 600)
scratch(21.58); whoosh(21.66, .2, .5); ting(21.74, 2637, .5); hit(21.74, .5)
for tb in np.arange(22.62, 24.7, .21): sniff(tb, .4)
rustle(22.7, 1.8, .12); boing(23.85, .3)
rustle(24.8, .55, .45); popfx(25.3, .5, 380); paperfx(25.3, .3, .35); hit(25.4, .4)
for tb in np.arange(25.35, 26.1, .14): paw(tb, .1)
paperfx(26.25, .4, .3); paperfx(26.9, .3, .2)
tear(27.95, .88, .5)
# 9. revelación
boom(28.85, 1.0); shimmer(28.88, 1.4, .35); paperfx(28.86, .4, .5); hit(29.15, .5)
bark(29.3, .9); bark(29.5, .8, 620)
# 10. comisaría
whoosh(30.74, .4, .55)
for tb in np.arange(30.8, 34.9, 1.65): creak(tb, .5, .08, 300, 380)
hit(31.95, .55)
for tb in (32.5, 32.95, 33.4): ting(tb, 1400, .15, .3)
paperfx(33.85, .2, .25); stamp(34.95); bark(35.15, .8); bark(35.4, .7, 600)
# 11. final
whoosh(36.0, .45, .6); crowd(36.0, 2.5, .16, 1.5); hit(36.2, .45); popfx(36.4, .3, 600)
boom(38.5, .8); cheer(38.5, .8)
for k in range(6): popper(38.52 + k * .07, .4)
crowd(38.5, 1.3, .2)
hit(38.6, .5)
# 12. banquete
whoosh(39.72, .4, .5); chatter(39.72, 2.8, .08)
for k in range(4): popper(39.75 + k * .1, .35)
for tb in np.arange(39.8, 41.1, .2): clap(tb, .12)
for tb in np.arange(41.15, 42.5, .22): slurp(tb, .3)
hit(41.35, .35)
# 13. años
whoosh(42.53, .5, .6); ting(43.56, 3136, .4)
# 14. Brasil
whoosh(43.92, .45, .55)
for k in range(24): step(43.98 + k * .1, .18, -.6 + k * .05)
hit(45.05, .6); hit(45.9, .5)
# 15. final triste
boom(46.75, .4); wind(46.75, 5.5, .1)
shimmer(47.0, 1.0, .12)
switch(49.27); hum(49.3, 2.7)
shimmer(50.85, .6, .1); whimper(51.25, .22)

# ---------------------------------------------------------------- mezcla
V = np.zeros((N, 2)); V[:len(vy), 0] = vy[:N]; V[:len(vy), 1] = vy[:N]
vr = np.abs(V[:, 0])
voiced = lp(vr, 8, 2) > np.percentile(vr[vr > 0], 50) * .5
rms_v = np.sqrt(np.mean(V[voiced, 0] ** 2))
envv = lp(np.abs(V[:, 0]), 6, 2); envv = np.clip(envv / (np.percentile(envv, 95) + 1e-9), 0, 1)
mus = mus * (1 - .4 * envv)[:, None]
rms_m = np.sqrt(np.mean(mus[voiced, 0] ** 2)); mus *= .5 * rms_v / (rms_m + 1e-9)
pk_v = np.abs(V).max()
sfx = np.tanh(sfx / (np.abs(sfx).max() + 1e-9) * 2.0)
sfx *= .5 * pk_v / (np.abs(sfx).max() + 1e-9)
mix = V + mus + sfx
mix *= 10 ** (1.5 / 20)
pk = np.abs(mix).max()
if pk > .95: mix = np.tanh(mix / .95 * 1.0) * .95
print("pico voz %.3f  rms voz %.4f  rms música %.4f (%.0f%%)  pico sfx %.3f  pico mezcla %.3f" % (pk_v, rms_v, np.sqrt(np.mean(mus[voiced, 0] ** 2)), 100 * np.sqrt(np.mean(mus[voiced, 0] ** 2)) / rms_v, np.abs(sfx).max(), np.abs(mix).max()))
w = wave.open("mix.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes()); w.close()
