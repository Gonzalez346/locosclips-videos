// "Aníbal y el vinagre" — shot plan timed to the 38.19 s Spanish voice-over, 30 fps, 1146 frames.
export const FPS = 30, TOTAL = 1146, DECK = 0;
export const SHOTS = [
  { id: 'hook', a: 0, b: 122, light: 'snow', snow: 0.35 },
  { id: 'year', a: 123, b: 219, light: 'snow', snow: 0.4 },
  { id: 'point', a: 220, b: 285, light: 'snow', snow: 0.4 },
  { id: 'rome', a: 286, b: 339, light: 'snow', snow: 0.3 },
  { id: 'laugh', a: 340, b: 394, light: 'snow', snow: 0.3 },
  { id: 'doubt', a: 395, b: 498, light: 'snow', snow: 0.8 },
  { id: 'freeze', a: 499, b: 560, light: 'snow', snow: 1.0 },
  { id: 'slip', a: 561, b: 632, light: 'snow', snow: 1.0 },
  { id: 'rockfall', a: 633, b: 700, light: 'snow', snow: 0.6 },
  { id: 'react', a: 701, b: 768, light: 'snow', snow: 0.5 },
  { id: 'fire', a: 769, b: 885, light: 'dusk', snow: 0.3 },
  { id: 'pour', a: 886, b: 950, light: 'dusk', snow: 0.2 },
  { id: 'crack', a: 951, b: 1047, light: 'dusk', snow: 0.15 },
  { id: 'twist', a: 1048, b: 1145, light: 'dusk', snow: 0.2 },
  { id: 'brandA', a: 2000, b: 2000, light: 'snow', snow: 0 },
  { id: 'brandB', a: 2001, b: 2001, light: 'snow', snow: 0 },
];
export const shotAt = (f) => SHOTS.find((s) => f >= s.a && f <= s.b) || SHOTS[SHOTS.length - 1];
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const smooth = (t) => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
const lerp = (a, b, t) => a + (b - a) * t;
const lerp3 = (a, b, t) => a.map((v, i) => lerp(v, b[i], t));
const ramp = (f, a, b) => clamp((f - a) / (b - a));
const q = (x, n = 2) => Math.round(x * 10 ** n) / 10 ** n;

export const LIGHTS = {
  snow: { az: 140, el: 40, sky: '#cfe0f5', ground: '#a3afc2', hemi: 1.3, sun: '#fff4e6', sunI: 2.2, fog: '#dce8f5', fogNear: 70, fogFar: 800,
    skyTop: '#4a86d0', skyHor: '#d9e7f6', sat: 1.12, vig: 0.2, shadowExt: 22, waterDeep: '#000', waterShal: '#000', glint: '#fff' },
  dusk: { az: 20, el: 12, sky: '#c4b4dc', ground: '#a8929e', hemi: 1.7, sun: '#ffc48a', sunI: 2.6, fog: '#f2c09a', fogNear: 60, fogFar: 700,
    skyTop: '#6f6eb0', skyHor: '#ffc682', sunDisc: '#fff0c8', sunSize: 0.0035, sat: 1.15, gain: '#fff1e0', vig: 0.28, shadowExt: 22, waterDeep: '#000', waterShal: '#000', glint: '#fff' },
};
export const lightFor = (S, f) => ({ ...LIGHTS[S.light] });

// group march: x of the leader (Hannibal)
export const march = (f) => (f < 340 ? -7 + f * 0.037 : f < 769 ? 5.6 : 12.6);
const walking = (f) => f < 340;
const HY = 1.62; // head height of the 2.25 m cards (m)

const CAMS = {
  hook: [
    { f: 0, pos: [-6.75, 1.7, 2.7], look: [-6.7, 1.65, 0], fov: 32 },
    { f: 28, pos: [-5.9, 1.7, 2.9], look: [-5.95, 1.65, 0], fov: 31 },
    { f: 68, pos: [-9.0, 2.4, 15], look: [-8.0, 1.3, 0], fov: 50 },
    { f: 122, pos: [-6.4, 2.4, 16], look: [-6.0, 1.3, 0], fov: 50 },
  ],
  year: [
    { f: 123, pos: [-3.3, 1.9, 6.0], look: [-2.2, 1.9, 0], fov: 38 },
    { f: 219, pos: [0.2, 1.9, 6.4], look: [1.3, 1.9, 0], fov: 38 },
  ],
  point: [
    { f: 220, pos: [0.4, 1.5, 4.2], look: [2.4, 1.7, 0], fov: 36 },
    { f: 285, pos: [0.6, 1.5, 3.8], look: [2.8, 1.75, 0], fov: 32 },
  ],
  rome: [
    { f: 286, pos: [4.0, 2.4, 3.0], look: [118, 14, -34], fov: 25 },
    { f: 339, pos: [4.0, 2.4, 3.0], look: [118, 14.5, -34], fov: 21 },
  ],
  laugh: [
    { f: 340, pos: [32, 5.5, 8.5], look: [41.2, 9.2, -8], fov: 30 },
    { f: 394, pos: [34, 6.0, 7.5], look: [41.4, 9.2, -8], fov: 25 },
  ],
  doubt: [
    { f: 395, pos: [1.0, 1.6, 8.5], look: [1.6, 1.7, 0], fov: 46 },
    { f: 450, pos: [1.6, 1.9, 7.6], look: [1.8, 1.9, 0], fov: 40 },
    { f: 498, pos: [1.9, 1.9, 7.2], look: [1.9, 1.9, 0], fov: 38 },
  ],
  freeze: [
    { f: 499, pos: [1.5, 1.4, 5.0], look: [4.0, 1.5, 0.2], fov: 38 },
    { f: 560, pos: [2.5, 1.4, 4.6], look: [4.3, 1.5, 0.2], fov: 36 },
  ],
  slip: [
    { f: 561, pos: [1.5, 1.8, 8.6], look: [1.6, 1.9, 0], fov: 46 },
    { f: 632, pos: [1.6, 1.8, 8.4], look: [1.6, 1.9, 0], fov: 44 },
  ],
  rockfall: [
    { f: 633, pos: [8.0, 2.4, 13.0], look: [14.0, 4.5, 0], fov: 44 },
    { f: 662, pos: [8.5, 2.5, 12.5], look: [14.5, 3.0, 0], fov: 42 },
    { f: 700, pos: [10.5, 2.4, 10.0], look: [15.0, 2.0, 0], fov: 40 },
  ],
  react: [
    { f: 701, pos: [8.2, 1.7, 3.6], look: [5.8, 1.8, 0], fov: 34 },
    { f: 768, pos: [7.4, 1.7, 3.3], look: [5.7, 1.8, 0], fov: 30 },
  ],
  fire: [
    { f: 769, pos: [9.8, 1.5, 6.8], look: [14.2, 1.3, 0], fov: 40 },
    { f: 885, pos: [11.4, 1.5, 6.2], look: [14.6, 1.4, 0], fov: 36 },
  ],
  pour: [
    { f: 886, pos: [11.0, 2.0, 5.6], look: [13.4, 1.9, 0], fov: 38 },
    { f: 950, pos: [11.4, 2.0, 5.2], look: [13.8, 1.9, 0], fov: 34 },
  ],
  crack: [
    { f: 951, pos: [12.5, 1.8, 9.5], look: [15.5, 2.0, 0], fov: 38 },
    { f: 989, pos: [13.0, 1.8, 9.0], look: [16.0, 2.0, 0], fov: 33 },
    { f: 1047, pos: [11.5, 2.4, 11.5], look: [14.5, 1.8, 0], fov: 44 },
  ],
  twist: [
    { f: 1048, pos: [12.2, 1.7, 3.2], look: [12.7, 1.7, 0], fov: 32 },
    { f: 1100, pos: [12.5, 1.7, 2.9], look: [12.7, 1.68, 0], fov: 28 },
    { f: 1145, pos: [12.55, 1.7, 2.7], look: [12.7, 1.68, 0], fov: 25 },
  ],
};
CAMS.brandA = [{ f: 2000, pos: [-0.5, 1.5, 2.6], look: [-0.5, 1.58, 0], fov: 30 }];
CAMS.brandB = [{ f: 2001, pos: [0, 2.3, 6.0], look: [0, 1.5, 0], fov: 40 }];
const KICKS = [{ f: 582, a: 0.04 }, { f: 663, a: 0.07 }, { f: 990, a: 0.08 }, { f: 1010, a: 0.03 }];
export const camAt = (f) => {
  const S = shotAt(f), K = CAMS[S.id];
  let c;
  if (f <= K[0].f) c = { ...K[0] };
  else if (f >= K[K.length - 1].f) c = { ...K[K.length - 1] };
  else for (let i = 0; i < K.length - 1; i++) if (f >= K[i].f && f <= K[i + 1].f) {
    const t = smooth((f - K[i].f) / (K[i + 1].f - K[i].f)), a = K[i], b = K[i + 1];
    c = { pos: lerp3(a.pos, b.pos, t), look: lerp3(a.look, b.look, t), fov: lerp(a.fov, b.fov, t), roll: lerp(a.roll || 0, b.roll || 0, t) };
  }
  c = { ...c, pos: [...c.pos], look: [...c.look] };
  for (const k of KICKS) { const d = f - k.f; if (d >= 0 && d < 7) { const s = (d % 2 ? -1 : 1) * k.a * (1 - d / 7); c.look[1] += s * 3; c.look[2] += s * 2; c.roll = (c.roll || 0) + s * 20; } }
  c.flash = [[123, 4, 0.5], [286, 4, 0.5], [340, 4, 0.5], [633, 4, 0.5], [769, 6, 0.9], [951, 4, 0.5], [1048, 5, 0.9]].reduce((m, [a, n, v]) => (f >= a && f < a + n ? Math.max(m, v * (1 - (f - a) / n)) : m), 0);
  c.shadowAt = S.id === 'rome' ? [4, 0, 0] : S.id === 'laugh' ? [42, 7, -8] : c.look;
  return c;
};
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
export const dofAt = (f) => {
  const S = shotAt(f), C = camAt(f);
  switch (S.id) {
    case 'brandA': return { focus: 2.5, cinf: 8 };
    case 'brandB': return { focus: 8.5, cinf: 2 };
    case 'rome': return { focus: dist(C.pos, [118, 13, -34]), cinf: 0 };
    case 'hook': return { focus: dist(C.pos, [march(f), 1.65, 0]), cinf: lerp(12, 3, smooth(ramp(f, 40, 90))) };
    case 'doubt': case 'slip': return { focus: dist(C.pos, [1.8, 1.9, 0]), cinf: 7 };
    case 'rockfall': return { focus: dist(C.pos, [14.5, 2.5, 0]), cinf: 4 };
    case 'crack': return { focus: dist(C.pos, [16, 1.8, 0]), cinf: 5 };
    case 'laugh': return { focus: dist(C.pos, [42, 8, -8]), cinf: 6 };
    case 'twist': return { focus: dist(C.pos, [12.7, 1.65, 0]), cinf: 10 };
    default: return { focus: dist(C.pos, C.look), cinf: 9 };
  }
};
export const worldAt = (f) => ({ snow: shotAt(f).snow, helmet: null, ledge: shotAt(f).id !== 'rome', brand: shotAt(f).id.startsWith('brand') });

// ---------- actors ----------
const blinkAt = (f, seed) => { const per = 38 + (seed * 17) % 31, ph = (f + seed * 13) % per; return ph < 2 ? 0.5 : ph < 4 ? 1 : 0; };
const R = (T, who, o, pos, extra = {}) => ({ key: who + JSON.stringify(o), draw: (p) => T.romanFront(p, who, o), x: pos[0], y: pos[1], z: pos[2], ...extra });
const ELE = (T, o, pos, extra = {}) => ({ key: 'ele' + JSON.stringify(o), draw: (p) => T.elephantSide(p, o), x: pos[0], y: pos[1], z: pos[2], s: 2.6, ...extra });

export const actorsAt = (f, T) => {
  const S = shotAt(f), out = [], M0 = march(f), mv = walking(f);
  const ph = q((f * 0.034) % 1, 2), cold = S.light === 'snow' ? '#e6f0ff' : '#ffe2c8', tint = S.light === 'snow' ? '#f2f6ff' : '#ffe2c8';
  if (S.id === 'brandA') { out.push(R(T, 'civA', { seed: 5, expr: 'grin', R: 'up', blink: 0, look: 0.2, headTilt: -4 }, [-0.5, 0, 0], { tint: '#ffffff' })); return out; }
  if (S.id === 'brandB') {
    out.push(R(T, 'civA', { seed: 5, expr: 'grin', R: 'up', blink: 0, look: 0.3 }, [-1.5, 0, 0.3], {}));
    out.push(R(T, 'civB', { seed: 12, expr: 'laugh', R: 'wave', blink: 0, facing: -1 }, [0.4, 0, -0.4], {}));
    out.push(R(T, 'civC', { seed: 32, expr: 'shock', L: 'cheek', blink: 0, facing: -1 }, [2.0, 0, 0.2], {}));
    out.push(ELE(T, { step: 0, hold: true, worry: 0, snow: 0, blink: 0 }, [-3.0, 0, -1.6], { tint: '#ffffff' }));
    return out; }
  const sn = (S.snow || 0), worryLvl = f >= 395 && f < 700 ? 1 : 0;
  // --- Hannibal ---
  let H = { expr: 'stern', seed: 3, blink: blinkAt(f, 3), step: mv ? ph : 0, look: 0.3 };
  if (S.id === 'hook') H.expr = f < 40 ? 'stern' : 'grin';
  if (S.id === 'point') { H = { ...H, R: f > 235 ? 'point' : 'hang', expr: 'stubborn', look: 0.8 }; }
  if (S.id === 'rome') H = null;
  if (S.id === 'laugh') H = null;
  if (S.id === 'doubt') H = { ...H, expr: 'worried', R: 'cheek' };
  if (S.id === 'freeze' || S.id === 'slip') H = { ...H, expr: 'nervous', tilt: q(1.5 * Math.sin(f * 1.6), 1) };
  if (S.id === 'rockfall') H = { ...H, expr: f > 664 ? 'shock' : 'neutral', look: 0.4, R: f > 664 ? 'up' : 'hang', blink: f > 664 ? 0 : H.blink };
  if (S.id === 'react') H = { ...H, expr: 'shock', R: 'cheek', L: 'cheek', look: 0.5, blink: 0 };
  if (S.id === 'fire') H = { ...H, expr: f < 800 ? 'grin' : 'stubborn', R: 'point', look: 0.6 };
  if (S.id === 'pour') H = { ...H, expr: 'grin', R: 'up', jar: true, look: 0.5, headTilt: q(4 * Math.sin(f * 0.1), 1) };
  if (S.id === 'crack') H = { ...H, expr: f < 990 ? 'stubborn' : 'grin', R: f < 990 ? 'hip' : 'up', L: f < 990 ? 'hip' : 'hang', jar: false, look: 0.5, bob: f >= 990 && f < 996 ? 0.02 : 0 };
  if (S.id === 'twist') { const wink = f >= 1106 && f < 1119; H = { ...H, expr: 'smile', R: 'up', jar: true, look: 0.1, blink: wink ? 1 : 0, headTilt: wink ? -6 : 0, seed: 3, step: 0 }; if (f > 1119) H.expr = 'grin'; }
  const hx = S.id === 'twist' || S.id === 'pour' ? 12.6 : M0;
  if (H) out.push(R(T, 'hannibal', H, [hx, 0, 0], { tint, order: 3 }));
  // --- soldiers ---
  const shiver = (S.id === 'freeze' || S.id === 'slip' || S.id === 'doubt') ? q(2.2 * Math.sin(f * 1.9), 1) : 0;
  if (!['rome', 'laugh', 'twist', 'pour'].includes(S.id)) {
    const sx = [[M0 - 2.2, 1.0, 'carth', 51], [M0 - 3.4, -0.9, 'carthB', 52]];
    sx.forEach(([x, z, who, sd], i) => {
      const o = { seed: sd, expr: S.id === 'freeze' ? 'worried' : (S.id === 'react' || S.id === 'rockfall') ? (f > 664 ? 'shock' : 'neutral') : S.id === 'crack' && f > 990 ? 'grin' : 'stern',
        step: mv ? q((f * 0.034 + i * 0.4) % 1, 2) : 0, tilt: shiver * (i ? -1 : 1), blink: blinkAt(f, sd), R: S.id === 'crack' && f > 995 ? 'up' : 'spear', L: S.id === 'freeze' ? 'cross' : 'hang', facing: i ? -1 : 1 };
      if (S.id === 'freeze' || S.id === 'doubt') o.R = 'cross';
      out.push(R(T, who, o, [x, 0, z], { tint: S.id === 'freeze' || S.id === 'slip' ? '#cfe4ff' : tint, order: 2 }));
    });
  }
  // --- elephants (lead + column) ---
  if (!['rome', 'laugh', 'twist', 'pour'].includes(S.id)) {
    const n = S.id === 'doubt' || S.id === 'slip' || S.id === 'freeze' ? 3 : 5;
    for (let i = 0; i < n; i++) {
      const x = M0 - 5.0 - i * 6.2, z = i % 2 ? -1.1 : -0.4;
      let o = { step: mv ? q((f * 0.034 + i * 0.37) % 1, 2) : 0, hold: !mv, worry: worryLvl ? 1 : 0, snow: q(Math.min(1, sn), 1), blink: blinkAt(f, 60 + i) };
      let ex = { tint, order: 2 + (i % 2 ? -0.1 : 0) };
      if (i === 0 && S.id === 'slip' || (i === 0 && f >= 575 && f < 632)) {
        const a = clamp((f - 574) / 8), r = f < 582 ? -0.0 : 0;
        const wob = f >= 575 && f < 632 ? Math.sin((f - 575) * 0.9) * Math.exp(-(f - 575) / 22) : 0;
        ex.roll = q((f < 582 ? -0.6 * smooth((f - 574) / 8) : -0.6 * Math.exp(-(f - 582) / 14)) * 1 + wob * 0.12, 3);
        o.hold = true; o.worry = 1;
      }
      out.push(ELE(T, o, [x, 0, z], ex));
    }
  }
  // --- Romans on the ledge ---
  if (S.id === 'laugh') {
    const lb = (s) => q(Math.abs(Math.sin((f + s) * 0.55)) * 0.03, 3);
    [[38.4, -7.2, 71], [41.4, -8.6, 72], [44.6, -7.4, 73]].forEach(([x, z, sd], i) => out.push(R(T, 'legion', { seed: sd, L: i === 1 ? 'point' : 'belly', R: 'belly', expr: 'laugh', facing: i === 1 ? 1 : -1, bob: lb(i * 5), tilt: q(4 * Math.sin((f + i * 7) * 0.5), 1), blink: 0 }, [x, 7.45, z], { tint, s: 1.5 })));
  }
  return out;
};

// ---------- effects ----------
const FX = (key, draw, pos, s, extra = {}) => ({ key, draw, x: pos[0], y: pos[1], z: pos[2], s, blob: false, shadow: false, order: 5, ...extra });
export const fxAt = (f, T) => {
  const S = shotAt(f), out = [], M0 = march(f);
  if (S.id === 'year') {
    const k = q(clamp((f - 150) / 8), 2);
    if (k > 0) out.push(FX('yr' + k, (p) => { const g = p.g; g.save(); g.translate(300, 560); g.scale(0.4 + 0.6 * k, 0.4 + 0.6 * k); g.font = '900 150px Arial Black, Arial'; g.textAlign = 'center'; g.lineJoin = 'round'; g.lineWidth = 30; g.strokeStyle = '#1a1220'; g.strokeText('218', 0, 0); g.fillStyle = '#ffd23a'; g.fillText('218', 0, 0); g.font = '900 78px Arial Black, Arial'; g.lineWidth = 20; g.strokeText('a. C.', 0, 100); g.fillStyle = '#ffffff'; g.fillText('a. C.', 0, 100); g.restore(); }, [M0 + 0.5, 1.3, 0.8], 1.9));
  }
  if (S.id === 'rockfall' || S.id === 'react') {
    if (f >= 663 && f < 693) { const t = q((f - 663) / 30, 2); [[0, 1.0], [-2.2, 0.4], [2.2, 0.4], [0, -1.2]].forEach(([dx, dz], i) => out.push(FX('dust' + t + i, (p) => T.fxDust(p, t, '#f2f4f8'), [16 + dx, 0.3, dz + 0.8], 2.4 + i * 0.3, { tint: '#ffffff' }))); }
    if (f >= 668 && f < 710) { const t = q((f - 668) / 14); out.push(FX('bang' + t, (p) => T.fxBang(p, t), [12.6, 2.2, 0.4], 1.0)); }
  }
  if (S.id === 'fire' || S.id === 'pour' || (S.id === 'crack' && f < 990)) {
    const t = q(f / 30, 2);
    const grow = clamp((f - 775) / 30);
    [[14.0, 1.4, 1.0], [15.6, 1.9, 1.2], [17.2, 1.4, 1.0]].forEach(([x, z, s], i) => out.push(FX('fl' + i + q(t + i * 0.13, 1), (p) => { p.g.translate(0, 330); T.fxFlame(p, t + i * 0.37); }, [x - 0.7 + i * 0.1, 0.0, z * 0.5 + 0.9], 0.95 * s * (0.4 + 0.6 * grow), { order: 6 })));
  }
  if (S.id === 'pour' || (S.id === 'crack' && f < 960)) {
    const t = q((f * 0.02) % 1, 2);
    if (S.id === 'pour' && f >= 900) for (let i = 0; i < 4; i++) { const k = ((f - 900) * 0.07 + i / 4) % 1; out.push(FX('dr' + q(k), (p) => T.fxDrip(p), [13.9 + k * 0.5, 1.9 - k * 1.8, 0.4], 0.12 + 0.02 * i, { order: 7 })); }
    if (f >= 905) out.push(FX('st' + t, (p) => { p.g.translate(0, 120); T.fxSteam(p, t); }, [14.5, 0.1, 1.4], 1.4, { alpha: 0.9 }));
  }
  if (S.id === 'crack') {
    const k = q(clamp((f - 960) / 30), 2);
    if (k > 0 && f < 990) out.push(FX('cr' + k, (p) => { p.g.translate(0, -30); T.fxCrack(p, k); }, [ROCK_FACE, 0.3, 1.9], 1.6));
    if (f >= 990 && f < 1030) { const t = q((f - 990) / 40, 2); [[0, 1.2], [-2, 0.2], [2, 0.2], [0, -0.8]].forEach(([dx, dz], i) => out.push(FX('dust2' + t + i, (p) => T.fxDust(p, t, '#f0f2f6'), [16.4 + dx, 0.3, dz + 0.6], 2.6 + i * 0.3, { tint: '#fff' }))); }
  }
  if (S.id === 'twist' && f >= 1106 && f < 1126) { const t = q((f - 1108) / 14); out.push(FX('sp' + t, (p) => T.fxSparkle(p, t), [12.35, 1.95, 0.5], 0.5, { order: 8 })); }
  return out;
};
const ROCK_FACE = 16;
