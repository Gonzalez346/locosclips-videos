#!/usr/bin/env bash
# Comprueba que una sesión nueva puede renderizar. Escribe pruebas/informe.txt
set -u
mkdir -p pruebas; OUT=pruebas/informe.txt; : > $OUT
log(){ echo "$*" | tee -a $OUT; }
log "fecha: $(date -u +%FT%TZ)"
export NODE_PATH=$(npm root -g 2>/dev/null):/opt/npm-tools/node_modules
for b in node python3 ffmpeg google-chrome; do log "$b: $(command -v $b || echo FALTA)"; done
log "playwright: $(ls -d /opt/npm-tools/node_modules/playwright $(npm root -g 2>/dev/null)/playwright 2>/dev/null | head -1 || echo FALTA)"
log "nproc: $(nproc)"
cd motor
mkdir -p /tmp/f && S=$(date +%s)
timeout 600 node render.mjs /tmp/f "100-104" >/tmp/render.log 2>&1; log "render exit=$? frames=$(ls /tmp/f | wc -l) seg=$(( $(date +%s)-S ))"
tail -3 /tmp/render.log | tee -a ../$OUT
ffmpeg -v error -y -framerate 30 -i /tmp/f/f01%02d.jpg -frames:v 5 -c:v libx264 -pix_fmt yuv420p /tmp/t.mp4 2>>../$OUT; log "ffmpeg exit=$? bytes=$(stat -c%s /tmp/t.mp4 2>/dev/null)"
