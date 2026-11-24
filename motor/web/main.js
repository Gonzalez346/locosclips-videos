import * as THREE from './lib/three.module.js';
import * as T from './toon.js';
import * as P from './paint.js';
import { SHOTS, TOTAL, shotAt, camAt, dofAt, LIGHTS, lightFor, actorsAt, worldAt, fxAt } from './story.js';

const W = 1080, H = 1920;
const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H, false);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, W / H, 0.08, 1500);
const rx = (a) => a * Math.PI / 180;

// ---------- materials ----------
const grad = (() => { const d = new Uint8Array([90, 90, 90, 255, 255, 255, 255, 255]); const t = new THREE.DataTexture(d, 2, 1); t.minFilter = t.magFilter = THREE.NearestFilter; t.needsUpdate = true; return t; })();
const toon = (opts) => new THREE.MeshToonMaterial({ gradientMap: grad, ...opts });
const texM = (c, rx_ = 1, ry_ = 1, color = '#ffffff') => toon({ map: P.tex(c, rx_, ry_), color });
const M = {
  plank: texM(P.planks(1), 1, 6), beam: texM(P.beam(2), 1, 2), beamDark: texM(P.beam(3, [28, 36, 30]), 1, 2),
  rot: texM(P.rotten(4), 1, 1), rotB: texM(P.rotten(14), 1, 1),
  stone: texM(P.stone(4), 1, 1), stoneMoss: texM(P.mossy(P.stone(4), 5, 1.2), 1, 1),
  grass: texM(P.grass(6), 40, 40), dirt: texM(P.dirt(7), 6, 30), plaster: texM(P.plaster(8), 1, 1), plaster2: texM(P.plaster(18, 28), 1, 1),
  roof: texM(P.roof(9), 2, 2), marble: texM(P.marble(10), 1, 1), marbleTop: toon({ color: '#ece2cf' }),
  trunk: toon({ color: '#6a4a32' }), cypress: toon({ color: '#3f6b36' }), pine: toon({ color: '#5c8a3c' }), bush: toon({ color: '#6c9a42' }),
  hill: toon({ color: '#7aa64c' }), hillFar: toon({ color: '#86ad60' }), mount: toon({ color: '#8fa7b8' }), snow: toon({ color: '#f4f6fa' }),
  iron: toon({ color: '#5c5a57' }), bronze: toon({ color: '#b08a4a' }), wood: toon({ color: '#7a5434' }), door: toon({ color: '#5a3a24' }),
  window: toon({ color: '#2b2430' }), red: toon({ color: '#b8282b' }),
};
M.banner = new THREE.MeshToonMaterial({ gradientMap: grad, map: P.tex(P.banner()), alphaTest: 0.5, side: THREE.DoubleSide });
// helmet
const helmetIn = P.tex(P.helmetInside()); helmetIn.wrapS = helmetIn.wrapT = THREE.ClampToEdgeWrapping;
M.helmIn = new THREE.MeshToonMaterial({ gradientMap: grad, map: helmetIn, side: THREE.BackSide });
M.helmOut = toon({ color: '#8f8a7e' });

// ---------- ink / normal-depth contract ----------
const NOINK = 'noink'; // userData flag: never outlined (cards, fx, water handled specially)
const ndMat = new THREE.ShaderMaterial({
  vertexShader: `varying vec3 vN; varying float vD; void main(){ vN = normalize(normalMatrix*normal); vec4 mv = modelViewMatrix*vec4(position,1.); vD = -mv.z; gl_Position = projectionMatrix*mv; }`,
  fragmentShader: `varying vec3 vN; varying float vD; void main(){ vec3 n = normalize(vN); if(!gl_FrontFacing) n = -n; gl_FragColor = vec4(n*.5+.5, vD); }`,
  side: THREE.DoubleSide,
});
const cardNd = (map) => new THREE.ShaderMaterial({
  uniforms: { map: { value: map } },
  vertexShader: `varying vec2 vUv; varying float vD; void main(){ vUv=uv; vec4 mv = modelViewMatrix*vec4(position,1.); vD=-mv.z; gl_Position=projectionMatrix*mv; }`,
  fragmentShader: `uniform sampler2D map; varying vec2 vUv; varying float vD; void main(){ if(texture2D(map,vUv).a<.5) discard; gl_FragColor=vec4(0.,0.,0.,vD); }`,
  side: THREE.DoubleSide,
});
const waterNd = new THREE.ShaderMaterial({
  vertexShader: `varying float vD; void main(){ vec4 mv = modelViewMatrix*vec4(position,1.); vD=-mv.z; gl_Position=projectionMatrix*mv; }`,
  fragmentShader: `varying float vD; void main(){ gl_FragColor=vec4(.5,1.,.5,vD); }`,
});

// ---------- helpers ----------
const add = (geo, mat, x = 0, y = 0, z = 0, parent = scene, opts = {}) => {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = opts.cast ?? true; m.receiveShadow = true; parent.add(m); return m;
};
const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);
const uvScale = (geo, su, sv) => { const uv = geo.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * su, uv.getY(i) * sv); return geo; };
/** box with world-scaled UVs per face (texel density 1 tile per `t` metres) */
const tbox = (w, h, d, t = 2) => {
  const g = box(w, h, d), uv = g.attributes.uv;
  const dims = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++) for (let k = 0; k < 4; k++) { const i = f * 4 + k; uv.setXY(i, uv.getX(i) * dims[f][0] / t, uv.getY(i) * dims[f][1] / t); }
  return g;
};

// ---------- sky ----------
const skyU = { top: { value: new THREE.Color() }, hor: { value: new THREE.Color() }, sunDir: { value: new THREE.Vector3() }, sunCol: { value: new THREE.Color() }, sunSize: { value: 0 } };
const sky = new THREE.Mesh(new THREE.SphereGeometry(1200, 32, 16), new THREE.ShaderMaterial({
  uniforms: skyU, side: THREE.BackSide, depthWrite: false, fog: false,
  vertexShader: `varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
  fragmentShader: `uniform vec3 top, hor, sunDir, sunCol; uniform float sunSize; varying vec3 vP;
    void main(){ float h = clamp(vP.y,0.,1.); vec3 c = mix(hor, top, pow(h, .55)); if(vP.y<0.) c = hor;
      float s = dot(normalize(vP), normalize(sunDir)); c += sunCol * (smoothstep(1.-sunSize, 1.-sunSize*.6, s) + .35*pow(max(s,0.), 24.)*step(.001,sunSize));
      gl_FragColor = vec4(c,1.); }`,
}));
sky.userData.sky = true; scene.add(sky);

// ---------- lights ----------
const hemi = new THREE.HemisphereLight('#ffffff', '#ffffff', 1); scene.add(hemi);
const sun = new THREE.DirectionalLight('#ffffff', 2); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.03; sun.shadow.radius = 2;
scene.add(sun); scene.add(sun.target);
scene.fog = new THREE.Fog('#ffffff', 40, 600);

// ---------- world ----------
const DECK = 0;
const world = new THREE.Group(); scene.add(world);
const waterU = { t: { value: 0 }, deep: { value: new THREE.Color() }, shal: { value: new THREE.Color() }, glint: { value: new THREE.Color() } };
const SNOWC = '#f3f7fc';
M.snowG = toon({ color: SNOWC }); M.trail = toon({ color: '#b9a48c' }); M.rock = toon({ color: '#8a919c' }); M.rockD = toon({ color: '#6c7380' });
M.pineD = toon({ color: '#2f5c42' }); M.flesh = toon({ color: '#ffffff' });
const ground = add(new THREE.PlaneGeometry(1800, 1800), M.snowG, 0, 0, 0, world, { cast: false }); ground.rotation.x = -Math.PI / 2;
const trail = add(new THREE.PlaneGeometry(260, 5.2), M.trail, 20, 0.02, 0, world, { cast: false }); trail.rotation.x = -Math.PI / 2;
const rt = P.rng(44);
// snow mounds
for (let i = 0; i < 46; i++) { const x = -60 + rt() * 200, z = (rt() < 0.5 ? -1 : 1) * (7 + rt() * 70); const m = add(new THREE.SphereGeometry(2 + rt() * 5, 14, 8), M.snowG, x, -0.4, z, world, { cast: false }); m.scale.set(1.6, 0.5 + rt() * 0.3, 1.2); }
// boulders along the trail edges
for (let i = 0; i < 26; i++) { const x = -40 + rt() * 150, z = (rt() < 0.5 ? -1 : 1) * (4 + rt() * 3); const r = 0.5 + rt() * 0.9; const b = add(new THREE.DodecahedronGeometry(r, 0), M.rock, x, r * 0.4, z, world); b.rotation.set(rt() * 3, rt() * 3, rt() * 3); add(new THREE.SphereGeometry(r * 0.8, 8, 6), M.snowG, x, r * 0.85, z, world).scale.set(1, 0.4, 1); }
// rock wall behind the trail (the pass)
const wallRock = (x, z, w, h, d) => { const g = add(new THREE.DodecahedronGeometry(1, 1), rt() > 0.5 ? M.rock : M.rockD, x, h * 0.45, z, world); g.scale.set(w, h, d); g.rotation.y = rt() * 3;
  const c = add(new THREE.SphereGeometry(1, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2), M.snowG, x, h * 0.45 + h * 0.78, z, world); c.scale.set(w * 0.8, h * 0.28, d * 0.8); };
for (let x = -70; x < 100; x += 11) wallRock(x + rt() * 3, -24 - rt() * 5, 6 + rt() * 3, 5 + rt() * 3.5, 5 + rt() * 2);
// cliff ledge where the Romans stand (top at y = 7)
const LEDGE = new THREE.Vector3(42, 0, -8); const ledge = new THREE.Group(); world.add(ledge);
add(tbox(13, 7, 7, 3), M.rock, LEDGE.x, 3.5, LEDGE.z, ledge);
add(tbox(13.6, 0.5, 7.6, 3), M.snowG, LEDGE.x, 7.2, LEDGE.z, ledge);
for (const [dx, dz, h] of [[-4, 3.2, 3], [3, 3.4, 4.5], [6.8, 2.8, 2.4]]) add(new THREE.DodecahedronGeometry(1.3, 0), M.rockD, LEDGE.x + dx, h * 0.5, LEDGE.z + dz, ledge).scale.set(1, h / 2, 1);
// pines (snowy)
const pine = (x, z, h = 6) => { const g = new THREE.Group(); g.position.set(x, 0, z); world.add(g); add(new THREE.CylinderGeometry(0.2, 0.3, 1.4, 6), M.trunk, 0, 0.7, 0, g);
  for (let k = 0; k < 3; k++) { const r = (2.0 - k * 0.5) * h / 6, y = 1.2 + k * h * 0.2; add(new THREE.ConeGeometry(r, h * 0.34, 8), M.pineD, 0, y + h * 0.17, 0, g); add(new THREE.ConeGeometry(r * 0.72, h * 0.16, 8), M.snowG, 0, y + h * 0.3, 0, g); } return g; };
for (let i = 0; i < 70; i++) { const x = -70 + rt() * 230, z = (rt() < 0.5 ? -1 : 1) * (8 + rt() * 40); if (z < 0 && Math.abs(x - LEDGE.x) < 9 && z > -16) continue; pine(x, z, 5 + rt() * 5); }
// Rome: a small temple on a far hill (original little building)
const TEMPLE = new THREE.Vector3(118, 0, -34);
const hill = add(new THREE.SphereGeometry(30, 32, 16), M.snowG, TEMPLE.x + 4, -10, TEMPLE.z - 4, world, { cast: false }); hill.scale.set(1, 0.85, 0.8);
const temple = new THREE.Group(); temple.position.set(TEMPLE.x, 15.2, TEMPLE.z); temple.rotation.y = rx(-80); world.add(temple);
add(tbox(14, 1.6, 22, 2), M.marbleTop, 0, 0.8, 0, temple);
add(tbox(9, 7, 13, 2), M.plaster, 0, 5.1, -3.5, temple);
const colGeo = new THREE.CylinderGeometry(0.55, 0.62, 7, 14); colGeo.translate(0, 3.5, 0);
const colPos = []; for (let i = 0; i < 6; i++) colPos.push([-5.6 + i * 2.24, 9.5]); for (let i = 0; i < 5; i++) { colPos.push([-5.6, 7 - i * 3.6]); colPos.push([5.6, 7 - i * 3.6]); }
for (const [x, z] of colPos) add(colGeo, M.marble, x, 1.6, z, temple);
add(tbox(13, 1.1, 21, 2), M.marbleTop, 0, 9.15, -0.5, temple);
{ const pedShape = new THREE.Shape(); pedShape.moveTo(-6.8, 0); pedShape.lineTo(6.8, 0); pedShape.lineTo(0, 2.6); pedShape.closePath();
  const roofG = new THREE.Group(); roofG.position.set(0, 9.7, -0.5); temple.add(roofG);
  add(new THREE.ExtrudeGeometry(pedShape, { depth: 21.6, bevelEnabled: false }), M.marbleTop, 0, 0, -10.8, roofG);
  for (const s of [-1, 1]) { const rf = add(tbox(7.4, 0.35, 22.2, 2), M.roof, s * 3.35, 1.3, 0, roofG); rf.rotation.z = -s * Math.atan2(2.6, 6.8); } }
// far mountains
for (let i = 0; i < 16; i++) { const a = -0.2 - rt() * 2.8, d = 420 + rt() * 220, hh = 110 + rt() * 120, r_ = 100 + rt() * 70; const g = new THREE.Group(); g.position.set(Math.cos(a) * d + 40, -5, -Math.abs(Math.sin(a)) * d); world.add(g);
  add(new THREE.ConeGeometry(r_, hh, 7), M.mount, 0, hh / 2, 0, g, { cast: false }); add(new THREE.ConeGeometry(r_ * 0.42, hh * 0.42, 7), M.snow, 0, hh * 0.79, 0, g, { cast: false }); }
// the rock that blocks the pass (original prop): whole + two halves
const jitterGeo = (r, seed, sx = 1, sy = 1, sz = 1) => { const g = new THREE.IcosahedronGeometry(r, 2); const pa = g.attributes.position, rr = P.rng(seed), k = new Map();
  for (let i = 0; i < pa.count; i++) { const key = [pa.getX(i), pa.getY(i), pa.getZ(i)].map((v) => v.toFixed(3)).join(); if (!k.has(key)) k.set(key, 0.84 + rr() * 0.3); const j = k.get(key); pa.setXYZ(i, pa.getX(i) * j * sx, pa.getY(i) * j * sy, pa.getZ(i) * j * sz); }
  g.computeVertexNormals(); return g; };
const ROCK_X = 16;
const rock = add(jitterGeo(1.9, 5, 1.2, 1, 1.05), M.rock, ROCK_X, 1.8, 0, world); rock.visible = false;
const rockCap = add(new THREE.SphereGeometry(1.5, 12, 6, 0, Math.PI * 2, 0, Math.PI / 2), M.snowG, 0, 1.45, 0, rock); rockCap.scale.set(1, 0.3, 0.9);
const halfA = add(jitterGeo(1.9, 5, 1.2, 1, 0.55), M.rock, ROCK_X, 1.8, 0.9, world), halfB = add(jitterGeo(1.9, 5, 1.2, 1, 0.55), M.rockD, ROCK_X, 1.8, -0.9, world);
halfA.visible = halfB.visible = false;
// brand backdrop (sunburst) for channel art
const brandBack = (() => { const c = document.createElement('canvas'); c.width = c.height = 1024; const g = c.getContext('2d');
  const gr = g.createRadialGradient(512, 560, 40, 512, 560, 760); gr.addColorStop(0, '#ffd23a'); gr.addColorStop(0.45, '#ff8a3c'); gr.addColorStop(1, '#6a2fc0'); g.fillStyle = gr; g.fillRect(0, 0, 1024, 1024);
  g.fillStyle = 'rgba(255,255,255,0.13)'; for (let i = 0; i < 18; i++) { const a0 = i * Math.PI / 9, a1 = a0 + Math.PI / 18; g.beginPath(); g.moveTo(512, 560); g.arc(512, 560, 1500, a0, a1); g.closePath(); g.fill(); }
  const m_ = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), new THREE.MeshBasicMaterial({ map: P.tex(c), fog: false })); m_.position.set(0, 4, -2.6); m_.visible = false; scene.add(m_); return m_; })();
// falling snow
const NSNOW = 360;
const flakeG = new THREE.IcosahedronGeometry(0.05, 0), flakeM = new THREE.MeshBasicMaterial({ color: '#ffffff', fog: false });
const flakes = new THREE.InstancedMesh(flakeG, flakeM, NSNOW); flakes.userData.ndSkip = true; flakes.frustumCulled = false; scene.add(flakes);
const flakeSeed = []; { const r = P.rng(8); for (let i = 0; i < NSNOW; i++) flakeSeed.push([r(), r(), r(), 0.6 + r() * 0.8]); }
const dummy = new THREE.Object3D();

// clouds: painted billboards far away (no fog, no ink)
const clouds = [];
{ const r = P.rng(90);
  for (let i = 0; i < 14; i++) {
    const c = document.createElement('canvas'); c.width = 600; c.height = 400; const pen = new T.Pen(c.getContext('2d')); pen.ol = 0;
    pen.g.translate(300, 200); pen.g.scale(1.4, 1.2); pen.g.translate(-300, -200); T.fxCloud(pen, i + 1);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 0.667), new THREE.MeshBasicMaterial({ map: P.tex(c), transparent: true, fog: false, depthWrite: false }));
    const a = r() * Math.PI * 2, d = 650 + r() * 250; m.position.set(Math.cos(a) * d, 120 + r() * 160, Math.sin(a) * d); m.scale.setScalar(160 + r() * 140);
    m.userData.ndSkip = true; m.renderOrder = -1; scene.add(m); clouds.push(m);
  } }

// ---------- helmet prop (3D) ----------
const helmet = new THREE.Group(); scene.add(helmet); helmet.visible = false;
{
  const inGeo = new THREE.SphereGeometry(0.98, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2);
  const uv = inGeo.attributes.uv, pos = inGeo.attributes.position;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, 0.5 - pos.getX(i) / 2.1, 0.5 - pos.getZ(i) / 2.1);
  add(inGeo, M.helmIn, 0, 0, 0, helmet);
  add(new THREE.SphereGeometry(1.0, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2), M.helmOut, 0, 0, 0, helmet);
  const band = add(new THREE.TorusGeometry(1.0, 0.07, 8, 48), toon({ color: '#a88a4a' }), 0, 0.02, 0, helmet); band.rotation.x = Math.PI / 2;
  const crest = add(new THREE.CylinderGeometry(1.3, 1.3, 0.22, 32, 1, false, 0, Math.PI), toon({ color: '#8d4b3f' }), 0, 0.95, 0, helmet);
  crest.rotation.z = Math.PI / 2; crest.rotation.y = Math.PI / 2; crest.scale.set(1, 1, 0.6);
}

// ---------- cards ----------
const CW = 1200, CH = 2000, CM = 2.25; // canvas px, card height in metres (design 600x1000 -> 2.25 m)
const cardGeo = new THREE.PlaneGeometry(CM * 0.6, CM); cardGeo.translate(0, CM / 2 - CM * 0.025, 0);
const blobTex = P.tex(P.radial('20,14,30', 0.6));
class Card {
  constructor(scale = 1) {
    [this.c, this.g] = (() => { const c = document.createElement('canvas'); c.width = CW; c.height = CH; return [c, c.getContext('2d')]; })();
    this.t = new THREE.CanvasTexture(this.c); this.t.colorSpace = THREE.SRGBColorSpace; this.t.anisotropy = 4;
    this.mat = new THREE.MeshBasicMaterial({ map: this.t, transparent: true, alphaTest: 0.02, side: THREE.DoubleSide, fog: true });
    this.mesh = new THREE.Mesh(cardGeo, this.mat); this.mesh.userData.nd = cardNd(this.t); this.mesh.castShadow = true;
    this.mesh.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: this.t, alphaTest: 0.5 });
    this.blob = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: blobTex, transparent: true, depthWrite: false, fog: true }));
    this.blob.rotation.x = -Math.PI / 2; this.blob.userData.ndSkip = true; this.blob.renderOrder = 1;
    scene.add(this.mesh); scene.add(this.blob); this.key = ''; this.mesh.visible = this.blob.visible = false;
  }
  draw(key, fn) {
    if (key === this.key) return; this.key = key;
    const g = this.g; g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, CW, CH); g.setTransform(CW / 600, 0, 0, CH / 1000, 0, 0);
    const p = new T.Pen(g); fn(p); this.t.needsUpdate = true;
  }
}
const cards = []; const getCard = (i) => cards[i] || (cards[i] = new Card());

// ---------- render targets & post ----------
const rtColor = new THREE.WebGLRenderTarget(W, H, { samples: 4, type: THREE.HalfFloatType });
const rtNd = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });
const rtInk = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType });
const fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), fsGeo = new THREE.PlaneGeometry(2, 2);
const fs = (mat) => { const s = new THREE.Scene(); s.add(new THREE.Mesh(fsGeo, mat)); return s; };
const inkU = { col: { value: rtColor.texture }, nd: { value: rtNd.texture }, res: { value: new THREE.Vector2(W, H) }, px: { value: 1.6 }, fogCol: { value: new THREE.Color() },
  sat: { value: 1.08 }, lift: { value: new THREE.Color(0, 0, 0) }, gain: { value: new THREE.Color(1, 1, 1) }, vig: { value: 0.22 }, flash: { value: 0 } };
const inkScene = fs(new THREE.ShaderMaterial({ uniforms: inkU, vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }`,
  fragmentShader: `uniform sampler2D col, nd; uniform vec2 res; uniform float px, sat, vig, flash; uniform vec3 fogCol, lift, gain; varying vec2 vUv;
  float edgeAt(vec2 uv, float r){
    vec4 c = texture2D(nd, uv); if (dot(c.rgb,c.rgb) < .01) return 0.; float d = c.a; vec3 n = c.rgb*2.-1.;
    float e = 0.; float rr = r * clamp(7./d, .62, 1.25);
    for (int i=0;i<16;i++){ float a = float(i)*.785398 + (i>7 ? .39 : 0.); float k = i>7 ? .5 : 1.;
      vec2 o = vec2(cos(a), sin(a))*rr*k/res; vec4 s = texture2D(nd, uv+o);
      float ds = s.a; bool card = dot(s.rgb,s.rgb) < .01;
      if (card && ds > 0.) continue;            // character cards: never outlined by the world ink
      if (card) ds = 1e4;                        // sky
      vec3 ns = s.rgb*2.-1.;
      e = max(e, smoothstep(.006, .02, (ds - d)/d));                           // depth jump, near side only
      if (!card && abs(ds-d)/d < .06) e = max(e, smoothstep(.88, .72, dot(n, ns)) * .9); // crease
    }
    return e * (1. - smoothstep(140., 520., d)*.8);
  }
  void main(){
    vec3 c = texture2D(col, vUv).rgb;
    float e = edgeAt(vUv, px);
    c = mix(c, vec3(.012,.01,.014), e);
    if (flash < -0.5) c = vec3(e);
    float l = dot(c, vec3(.299,.587,.114)); c = mix(vec3(l), c, sat);
    c = c*gain + lift;
    vec2 q = vUv-.5; c *= 1. - vig*dot(q*vec2(1.,.75), q*vec2(1.,.75))*2.2;
    c = mix(c, vec3(1.), flash);
    gl_FragColor = vec4(c,1.); }` }));
const dofU = { src: { value: rtInk.texture }, nd: { value: rtNd.texture }, res: { value: new THREE.Vector2(W, H) }, focus: { value: 5 }, cinf: { value: 0 }, near: { value: 1 } };
const dofScene = fs(new THREE.ShaderMaterial({ uniforms: dofU, vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }`,
  fragmentShader: `uniform sampler2D src, nd; uniform vec2 res; uniform float focus, cinf, near; varying vec2 vUv;
  float coc(vec2 uv){ float d = texture2D(nd, uv).a; if (d <= 0.) d = 2000.; float k = 1. - focus/d; return k > 0. ? cinf*k : min(-k*cinf*near, cinf*1.4); }
  void main(){
    float c0 = coc(vUv);
    if (cinf < .5 || c0 < .6) { gl_FragColor = linearToOutputTexel(vec4(texture2D(src, vUv).rgb, 1.)); return; }
    vec3 acc = vec3(0.); float wsum = 0.;
    for (int i=0;i<48;i++){ float fi = float(i); float r = sqrt((fi+.5)/48.); float a = fi*2.39996;
      vec2 o = vec2(cos(a), sin(a))*r*c0/res; float cs = coc(vUv+o);
      float w = smoothstep(r*c0-1.5, r*c0+.5, cs + .5);
      acc += texture2D(src, vUv+o).rgb*w; wsum += w; }
    gl_FragColor = linearToOutputTexel(vec4(acc/max(wsum,1e-3), 1.)); }` }));
// final copy with sRGB handled by the renderer output (we render to screen with linear->sRGB in the shader chunk)
dofScene.children[0].material.toneMapped = false;

// ---------- per-frame state ----------
const tmpV = new THREE.Vector3();
function applyLight(L, f) {
  hemi.color.set(L.sky); hemi.groundColor.set(L.ground); hemi.intensity = L.hemi;
  sun.color.set(L.sun); sun.intensity = L.sunI;
  scene.fog.color.set(L.fog); scene.fog.near = L.fogNear; scene.fog.far = L.fogFar;
  skyU.top.value.set(L.skyTop); skyU.hor.value.set(L.skyHor); skyU.sunCol.value.set(L.sunDisc || '#000'); skyU.sunSize.value = L.sunSize || 0;
  inkU.sat.value = L.sat; inkU.gain.value.set(L.gain || '#ffffff'); inkU.lift.value.set(L.lift || '#000000');
  
}
function placeSun(L, focus) {
  // sun direction from azimuth/elevation in world space
  const az = rx(L.az), el = rx(L.el); tmpV.set(Math.cos(el) * Math.cos(az), Math.sin(el), Math.cos(el) * Math.sin(az));
  skyU.sunDir.value.copy(tmpV);
  sun.position.copy(focus).addScaledVector(tmpV, 80); sun.target.position.copy(focus);
  const ext = L.shadowExt || 30, sc = sun.shadow.camera; sc.left = -ext; sc.right = ext; sc.top = ext; sc.bottom = -ext; sc.near = 1; sc.far = 200; sc.updateProjectionMatrix();
}

function worldState(S, f, cam) {
  // rock: falls 648-663, whole until split at 990, then two halves roll apart
  const fall = Math.min(1, Math.max(0, (f - 648) / 15));
  const whole = f >= 648 && f < 990;
  rock.visible = whole;
  if (whole) { const y = 1.8 + (1 - fall * fall) * 17; const bounce = f >= 663 && f < 669 ? Math.abs(Math.sin((f - 663) / 6 * Math.PI)) * 0.35 : 0; rock.position.set(ROCK_X, y + bounce, 0); rock.rotation.set(fall < 1 ? (1 - fall) * 2.2 : 0, 0.3, fall < 1 ? (1 - fall) * 1.4 : 0);
    const hot = f >= 760 && f < 960 ? Math.min(1, (f - 760) / 40) : 0; rock.material = M.rock; rock.userData.hot = hot; }
  const sp = Math.min(1, Math.max(0, (f - 990) / 26)), se = 1 - (1 - sp) * (1 - sp);
  halfA.visible = halfB.visible = f >= 990;
  halfA.position.set(ROCK_X + 0.4 * se, 1.8 - 0.1 * se, 0.9 + 4.2 * se); halfA.rotation.set(0.5 * se, 0, 0.9 * se);
  halfB.position.set(ROCK_X + 0.4 * se, 1.8 - 0.1 * se, -0.9 - 4.2 * se); halfB.rotation.set(-0.5 * se, 0, -0.9 * se);
  ledge.visible = S.ledge !== false; brandBack.visible = !!S.brand;
  // snow
  const n = Math.round(NSNOW * S.snow);
  flakes.count = n;
  const fw = new THREE.Vector3(); camera.getWorldDirection(fw);
  const cx = cam.pos[0] + fw.x * 9, cy = cam.pos[1], cz = cam.pos[2] + fw.z * 9;
  for (let i = 0; i < n; i++) { const q = flakeSeed[i];
    const y = ((q[1] * 16 - f * 0.05 * q[3]) % 16 + 16) % 16 - 3 + Math.max(0, cy - 8);
    dummy.position.set(cx + (q[0] - 0.5) * 36 + Math.sin(f * 0.04 + i) * 0.5 + f * 0.01, y, cz + (q[2] - 0.5) * 22); dummy.scale.setScalar(q[3] * 1.4); dummy.updateMatrix(); flakes.setMatrixAt(i, dummy.matrix); }
  flakes.instanceMatrix.needsUpdate = true;
}

function drawActors(list, cam) {
  cards.forEach((c) => { c.mesh.visible = c.blob.visible = false; });
  list.forEach((a, i) => {
    const c = getCard(i);
    c.draw(a.key, a.draw);
    c.mesh.visible = true; c.mesh.position.set(a.x, a.y, a.z);
    const s = a.s || 1; c.mesh.scale.set(s * (a.flip ? -1 : 1), s, s);
    c.mesh.rotation.set(0, Math.atan2(cam.position.x - a.x, cam.position.z - a.z) + (a.yaw || 0), a.roll || 0);
    c.mat.color.set(a.tint || '#ffffff'); c.mat.opacity = a.alpha ?? 1;
    c.mesh.castShadow = a.shadow !== false;
    c.mesh.renderOrder = a.order || 2;
    if (a.blob !== false && a.y < DECK + 0.5) { c.blob.visible = true; c.blob.position.set(a.x, (a.ground ?? DECK) + 0.02, a.z); c.blob.scale.set(0.95 * s, 0.6 * s, 1); }
  });
}

const helmetState = (h) => {
  helmet.visible = !!h; if (!h) return;
  helmet.position.set(h.x, h.y, h.z); helmet.rotation.set(h.rx || 0, h.ry || 0, h.rz || 0); helmet.scale.setScalar(h.s || 0.17);
};

const swapForNd = (on) => {
  scene.traverse((o) => {
    if (!o.isMesh) return;
    if (on) {
      o.userData.mat0 = o.material;
      if (o.userData.ndSkip) { o.userData.vis0 = o.visible; o.visible = false; return; }
      if (o === sky || o.userData.sky) { o.userData.vis0 = o.visible; o.visible = false; return; }
      o.material = o.userData.nd || ndMat;
    } else {
      o.material = o.userData.mat0; if (o.userData.vis0 !== undefined) { o.visible = o.userData.vis0; delete o.userData.vis0; }
    }
  });
};

window.renderFrame = (f) => {
  const S = shotAt(f), L = lightFor(S, f), C = camAt(f);
  applyLight(L, f);
  camera.position.set(...C.pos); camera.up.set(0, 1, 0); camera.lookAt(...C.look); camera.rotateZ(rx(C.roll || 0));
  camera.fov = C.fov; camera.updateProjectionMatrix(); camera.updateMatrixWorld();
  const W_ = worldAt(f); worldState(W_, f, C);
  placeSun(L, new THREE.Vector3(...(C.shadowAt || C.look)));
  drawActors([...actorsAt(f, T), ...fxAt(f, T)], camera);
  helmetState(W_.helmet);
  sky.position.copy(camera.position);
  for (const c of clouds) c.quaternion.copy(camera.quaternion);
  // pass A: colour
  renderer.setRenderTarget(rtColor); renderer.setClearColor(0x000000, 1); renderer.clear(); renderer.render(scene, camera);
  // pass B: normal + depth
  const fog = scene.fog; scene.fog = null; const sm = renderer.shadowMap.enabled; renderer.shadowMap.enabled = false; renderer.shadowMap.autoUpdate = false;
  swapForNd(true); renderer.setRenderTarget(rtNd); renderer.setClearColor(0x000000, 0); renderer.clear(); renderer.render(scene, camera); swapForNd(false);
  scene.fog = fog; renderer.shadowMap.enabled = sm; renderer.shadowMap.autoUpdate = true;
  if (window.DEBUG_ND) { const dm = new THREE.MeshBasicMaterial({ map: rtNd.texture }); const ds = fs(dm); renderer.setRenderTarget(null); renderer.render(ds, fsCam); return true; }
  // ink + grade
  const D = dofAt(f);
  inkU.px.value = 2.5; inkU.flash.value = window.DEBUG_E ? -1 : (C.flash || 0); inkU.vig.value = L.vig ?? 0.22;
  renderer.setRenderTarget(rtInk); renderer.render(inkScene, fsCam);
  // lens
  dofU.focus.value = D.focus; dofU.cinf.value = D.cinf; dofU.near.value = D.near ?? 1;
  renderer.setRenderTarget(null); renderer.render(dofScene, fsCam);
  return true;
};
window.TOTAL = TOTAL;
window.ready = true;
