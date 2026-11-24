# Motor 2D (locosclips)
Dibujo vectorial con Pillow (1080x1920, 30 fps), ~0,3 s/fotograma: un vídeo de 38 s ≈ 3 min con 2 procesos.
- `scene_ejemplo_hannibal.py`: escena completa del vídeo de ejemplo (personajes, fondo, cámara, efectos). Cada vídeo nuevo = una escena nueva copiando este archivo y cambiando línea de tiempo (SEG, CAM), personajes y fondo.
- `render_all.py`: renderiza todos los fotogramas en paralelo a `frames2/`.
- `subs3.py`: subtítulos palabra por palabra sobre los fotogramas.
- `audio_ejemplo.py`: música + SFX sintetizados y mezcla bajo la voz.
Reglas: voz del usuario sin tocar; música al 50 % de la voz; SFX ≤ 50 %; historias y personajes originales; subtítulos palabra por palabra.
