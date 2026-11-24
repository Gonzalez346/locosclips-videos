# Motor de render (locosclips)

Contenido de `motor/`:
- `web/` motor 3D (three.js, tarjetas toon) que se renderiza en Chrome sin pantalla. `story.js` es el plan de planos de UN vídeo (el de Aníbal, de ejemplo); cada vídeo nuevo necesita su propio `story.js`.
- `render.mjs` renderiza fotogramas: `node render.mjs <carpeta_salida> "<a-b>"` (RESUME=1 retoma).
- `timing.py` tiempos por palabra a partir de voz + guion.
- `ejemplo_hannibal/` audio (música + SFX) y subtítulos del vídeo de ejemplo, para copiar y adaptar.

## Entorno
- `export NODE_PATH=$(npm root -g):/opt/npm-tools/node_modules` (ahí está playwright). Chrome: `/usr/bin/google-chrome`.
- Tras editar `web/roman.js`: `cat web/toonbase.js web/roman.js > web/toon.js`.
- 1080x1920, 30 fps. Un fotograma 3D tarda ~2,2 s; 2 procesos en paralelo ≈ 1 fotograma/s.

## Reglas de producto
- Voz del usuario sin tocar. Música al 50 % del nivel de la voz, SFX ≤ 50 %.
- Subtítulos palabra por palabra. Personajes e historias originales.
- Salida: `videos/AAAA-MM-DD_N.mp4` + `schedule/AAAA-MM-DD_N.json` (ver README). N=1 (09:00), 2 (12:00), 3 (17:00), hora de Guinea Ecuatorial.
