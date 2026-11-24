#!/usr/bin/env bash
# Comprueba que una sesión nueva puede renderizar en 2D. Escribe pruebas/informe.txt
set -u
mkdir -p pruebas; OUT=$PWD/pruebas/informe.txt; : > $OUT
log(){ echo "$*" | tee -a $OUT; }
log "fecha: $(date -u +%FT%TZ)"
for b in python3 ffmpeg; do log "$b: $(command -v $b || echo FALTA)"; done
python3 -c "import PIL,numpy;print('PIL/numpy ok')" 2>&1 | tee -a $OUT
log "nproc: $(nproc)"
cd motor2d; mkdir -p /tmp/f2; S=$(date +%s)
python3 - <<'PY' 2>&1 | tee -a $OUT
import scene_ejemplo_hannibal as s
for f in range(100,105): s.render(f,1.5).save(f"/tmp/f2/f{f:04d}.jpg",quality=94)
print("render 5 fotogramas ok")
PY
log "seg=$(( $(date +%s)-S ))"
ffmpeg -v error -y -framerate 30 -start_number 100 -i /tmp/f2/f%04d.jpg -frames:v 5 -c:v libx264 -pix_fmt yuv420p /tmp/t2.mp4 2>>$OUT; log "ffmpeg exit=$? bytes=$(stat -c%s /tmp/t2.mp4 2>/dev/null)"
