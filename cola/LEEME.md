Cada vídeo programado son dos archivos en esta carpeta:
- `NOMBRE.mp4`
- `NOMBRE.json`: {"title", "description", "tags", "video": "NOMBRE.mp4", "publicar": "2026-11-26T16:00:00+00:00", "privacy": "public"}
El flujo de GitHub Actions revisa la cola cada 15 minutos y publica lo que ya toca. El resultado queda en publicados.json y auth/estado.txt.
