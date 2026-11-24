# locosclips-videos

Almacen de los videos de **locosclips** que Zapier publica solos en YouTube.

## Convencion
Por cada video programado:

- `videos/AAAA-MM-DD_N.mp4` — el video
- `schedule/AAAA-MM-DD_N.json` — datos del video:
  `{"title": "...", "description": "...", "tags": ["..."]}`

`N` es la franja (hora de Guinea Ecuatorial): **1 = 09:00**, **2 = 12:00**, **3 = 17:00**.

Cada dia a esa hora un flujo de Zapier busca el archivo de su fecha y franja y lo sube. Si no hay archivo, se salta ese dia.
