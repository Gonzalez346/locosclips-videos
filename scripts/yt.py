"""Publica en YouTube los vídeos de cola/ cuya hora ya llegó (API oficial, OAuth de escritorio)."""
import os, sys, json, glob, subprocess, time, datetime, urllib.request, urllib.parse

KEY = os.environ.get("YT_KEY", "")
def log(*a): print(*a, flush=True)
def dec(path):
    return subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-d", "-a", "-A", "-pass", "env:YT_KEY", "-in", path], capture_output=True, check=True).stdout.decode()
def enc(text, path):
    subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-a", "-A", "-pass", "env:YT_KEY", "-out", path], input=text.encode(), check=True)
def post(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST")
    with urllib.request.urlopen(req) as r: return json.load(r)
def api(method, url, token, body=None, headers=None):
    h = {"Authorization": "Bearer " + token}
    if headers: h.update(headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode(); h["Content-Type"] = "application/json; charset=UTF-8"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req) as r:
        return r.headers, r.read()

def status(msg):
    with open("auth/estado.txt", "w") as f: f.write(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC") + " — " + msg + "\n")
    log(msg)

if not KEY:
    log("Falta el secreto YT_KEY en GitHub. No hago nada."); sys.exit(0)
if not os.path.exists("auth/client.enc"):
    log("Faltan las credenciales de Google (auth/client.enc)."); sys.exit(0)
client = json.loads(dec("auth/client.enc"))
REDIRECT = "http://127.0.0.1:8080"

# 1) Autorización (una sola vez): canjear el código por un token permanente
if os.path.exists("auth/code.txt"):
    code = open("auth/code.txt").read().strip()
    if "code=" in code:
        code = urllib.parse.parse_qs(urllib.parse.urlparse(code).query).get("code", [""])[0]
    os.remove("auth/code.txt")
    try:
        tok = post("https://oauth2.googleapis.com/token", dict(code=code, client_id=client["client_id"], client_secret=client["client_secret"],
                                                               redirect_uri=REDIRECT, grant_type="authorization_code"))
        if "refresh_token" not in tok:
            status("ERROR: Google no devolvió un token permanente. Repite la autorización."); sys.exit(0)
        enc(tok["refresh_token"], "auth/token.enc")
        _, b = api("GET", "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true", tok["access_token"])
        ch = json.loads(b).get("items", [{}])[0].get("snippet", {}).get("title", "?")
        status("AUTORIZADO. Canal conectado: " + ch)
    except urllib.error.HTTPError as e:
        status("ERROR al autorizar: %s %s" % (e.code, e.read()[:300].decode(errors="ignore"))); sys.exit(0)

if not os.path.exists("auth/token.enc"):
    log("Todavía no hay autorización."); sys.exit(0)
tok = post("https://oauth2.googleapis.com/token", dict(refresh_token=dec("auth/token.enc"), client_id=client["client_id"],
                                                       client_secret=client["client_secret"], grant_type="refresh_token"))
AT = tok["access_token"]

# 2) Comprobar el estado de los últimos publicados (por si YouTube los bloquea en privado)
if os.path.exists("publicados.json"):
    pub = json.load(open("publicados.json"))
    ids = [p["id"] for p in pub[-10:]]
    if ids:
        _, b = api("GET", "https://www.googleapis.com/youtube/v3/videos?part=status&id=" + ",".join(ids), AT)
        st = {i["id"]: i["status"] for i in json.loads(b).get("items", [])}
        for p in pub:
            if p["id"] in st: p["privacidad_actual"] = st[p["id"]].get("privacyStatus"); p["estado_subida"] = st[p["id"]].get("uploadStatus")
        json.dump(pub, open("publicados.json", "w"), ensure_ascii=False, indent=1)
else:
    pub = []

# 3) Configuración de subida (según la guía: oculto primero, público a la hora buena)
ADELANTO = datetime.timedelta(minutes=90)   # se sube en OCULTO 90 min antes para que YouTube lo analice
LISTAS = {
    "Historias reales increíbles": "Historias reales tan raras que parecen inventadas: robos, soldados olvidados, supervivientes y personajes que cambiaron la historia. Un vídeo nuevo cada día.",
    "Récords y casos insólitos": "Récords imposibles y casos insólitos de la vida real y del deporte: lo que pasó de verdad, contado en menos de un minuto. Un vídeo nuevo cada día.",
}
def jload(p, d):
    return json.load(open(p)) if os.path.exists(p) else d
def jsave(p, o):
    json.dump(o, open(p, "w"), ensure_ascii=False, indent=1)
def estado_video(privacy, m):
    return {"privacyStatus": privacy, "selfDeclaredMadeForKids": False, "containsSyntheticMedia": bool(m.get("ia", False)),
            "embeddable": True, "publicStatsViewable": True, "license": "youtube"}
def snippet(m):
    return {"title": m["title"], "description": m.get("description", ""), "tags": m.get("tags", []), "categoryId": m.get("categoria", "24"),
            "defaultLanguage": "es", "defaultAudioLanguage": "es"}
listas = jload("auth/listas.json", {})
def lista_id(nombre):
    if nombre in listas: return listas[nombre]
    _, b = api("GET", "https://www.googleapis.com/youtube/v3/playlists?part=snippet&mine=true&maxResults=50", AT)
    for it in json.loads(b).get("items", []):
        if it["snippet"]["title"] == nombre: listas[nombre] = it["id"]
    if nombre not in listas:
        _, b = api("POST", "https://www.googleapis.com/youtube/v3/playlists?part=snippet,status", AT,
                   {"snippet": {"title": nombre, "description": LISTAS.get(nombre, ""), "defaultLanguage": "es"}, "status": {"privacyStatus": "public"}})
        listas[nombre] = json.loads(b)["id"]
    jsave("auth/listas.json", listas); return listas[nombre]
def a_lista(video_id, nombre):
    if not nombre: return
    try:
        api("POST", "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet", AT,
            {"snippet": {"playlistId": lista_id(nombre), "resourceId": {"kind": "youtube#video", "videoId": video_id}}})
    except urllib.error.HTTPError as e:
        log("No pude añadir a la lista:", e.code, e.read()[:200])

# 3a) Ajustes puntuales a vídeos ya subidos (auth/ajustes.json)
aj = jload("auth/ajustes.json", [])
if aj:
    for a in aj:
        try:
            parts = "status" + (",snippet" if "title" in a else "")
            body = {"id": a["id"], "status": estado_video(a.get("privacy", "public"), a)}
            if "title" in a: body["snippet"] = snippet(a)
            api("PUT", "https://www.googleapis.com/youtube/v3/videos?part=" + parts, AT, body)
            a_lista(a["id"], a.get("lista"))
            log("Ajustado", a["id"])
        except urllib.error.HTTPError as e:
            status("ERROR ajustando %s: %s %s" % (a["id"], e.code, e.read()[:300].decode(errors="ignore")))
    os.remove("auth/ajustes.json")

now = datetime.datetime.now(datetime.timezone.utc)

# 3b) Pasar a PÚBLICO los ocultos cuya hora llegó
ocultos = jload("ocultos.json", [])
quedan = []
for o in ocultos:
    if datetime.datetime.fromisoformat(o["publicar"]) > now:
        quedan.append(o); continue
    try:
        api("PUT", "https://www.googleapis.com/youtube/v3/videos?part=status", AT, {"id": o["id"], "status": estado_video("public", o)})
    except urllib.error.HTTPError as e:
        status("ERROR pasando a público %s: %s %s" % (o["id"], e.code, e.read()[:300].decode(errors="ignore"))); quedan.append(o); continue
    pub.append({"id": o["id"], "titulo": o["title"], "url": "https://www.youtube.com/watch?v=" + o["id"], "privacidad_pedida": "public",
                "subido_oculto_utc": o.get("subido_utc"), "publicado_utc": now.isoformat()})
    jsave("publicados.json", pub)
    status("Publicado (oculto → público): %s → %s" % (o["title"], o["id"]))
jsave("ocultos.json", quedan)

# 3c) Subir en OCULTO lo que se publica en los próximos 90 min
for mf in sorted(glob.glob("cola/*.json")):
    m = json.load(open(mf))
    when = datetime.datetime.fromisoformat(m.get("publicar", "2000-01-01T00:00:00+00:00"))
    if when - ADELANTO > now:
        log("Pendiente:", mf, "a las", when.isoformat()); continue
    vid = os.path.join("cola", m["video"])
    privacy = "unlisted" if when > now else m.get("privacy", "public")
    meta = {"snippet": snippet(m), "status": estado_video(privacy, m)}
    size = os.path.getsize(vid)
    try:
        h, _ = api("POST", "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status&notifySubscribers=true",
                   AT, meta, {"X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
        loc = h["Location"]
        req = urllib.request.Request(loc, data=open(vid, "rb").read(), method="PUT", headers={"Authorization": "Bearer " + AT, "Content-Type": "video/mp4"})
        with urllib.request.urlopen(req, timeout=900) as r: res = json.load(r)
    except urllib.error.HTTPError as e:
        status("ERROR subiendo %s: %s %s" % (mf, e.code, e.read()[:400].decode(errors="ignore"))); continue
    a_lista(res["id"], m.get("lista"))
    if privacy == "unlisted":
        quedan.append({"id": res["id"], "title": m["title"], "publicar": when.isoformat(), "ia": m.get("ia", False),
                       "subido_utc": now.isoformat(), "privacidad_devuelta": res.get("status", {}).get("privacyStatus")})
        jsave("ocultos.json", quedan)
        status("Subido en OCULTO: %s → %s (público a las %s UTC)" % (m["title"], res["id"], when.strftime("%H:%M")))
    else:
        pub.append({"id": res["id"], "titulo": m["title"], "url": "https://www.youtube.com/watch?v=" + res["id"], "privacidad_pedida": privacy,
                    "privacidad_devuelta": res.get("status", {}).get("privacyStatus"), "publicado_utc": now.isoformat()})
        jsave("publicados.json", pub)
        status("Publicado: %s → %s" % (m["title"], res["id"]))
    os.remove(vid); os.remove(mf)
