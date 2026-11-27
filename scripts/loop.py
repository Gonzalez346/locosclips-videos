"""Bucle de publicación puntual: ejecuta yt.py en cada momento clave (subida en oculto 90 min antes
y paso a público a la hora exacta), guardando cambios tras cada paso. Dura hasta ~5 h 30 min y,
si queda trabajo, lanza otra ejecución del workflow para seguir (no depende del cron de GitHub)."""
import json, glob, os, subprocess, time, datetime
UTC = datetime.timezone.utc
FIN = time.time() + 5.5 * 3600
ADEL = datetime.timedelta(minutes=90)
def sh(c): subprocess.run(c, shell=True)
def guardar():
    sh('git add -A && (git diff --cached --quiet || (git commit -qm "Publicación automática [skip ci]" && '
       'for i in 1 2 3; do git pull --rebase -q origin main && git push -q origin main && break; sleep 5; done))')
def proximo():
    ev = []
    for mf in glob.glob("cola/*.json"):
        w = datetime.datetime.fromisoformat(json.load(open(mf))["publicar"]); ev.append(w - ADEL)
    if os.path.exists("ocultos.json"):
        for o in json.load(open("ocultos.json")): ev.append(datetime.datetime.fromisoformat(o["publicar"]))
    return min(ev) if ev else None
while True:
    sh("git pull --rebase -q origin main"); sh("python3 scripts/yt.py"); guardar()
    nx = proximo()
    if nx is None: print("Cola vacía"); break
    espera = (nx - datetime.datetime.now(UTC)).total_seconds() + 20
    if time.time() + max(0, espera) > FIN:
        print("Siguiente evento", nx, "fuera de esta ejecución; encadeno otra"); open(".seguir", "w").write("1"); break
    print("Esperando hasta", nx, flush=True)
    time.sleep(min(max(0, espera), 600))  # revisa cambios cada 10 min como máximo
