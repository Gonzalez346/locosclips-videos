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

# 3) Publicar lo que toque
now = datetime.datetime.now(datetime.timezone.utc)
for mf in sorted(glob.glob("cola/*.json")):
    m = json.load(open(mf))
    when = datetime.datetime.fromisoformat(m.get("publicar", "2000-01-01T00:00:00+00:00"))
    if when > now:
        log("Pendiente:", mf, "a las", when.isoformat()); continue
    vid = os.path.join("cola", m["video"])
    meta = {"snippet": {"title": m["title"], "description": m.get("description", ""), "tags": m.get("tags", []), "categoryId": "24",
                        "defaultLanguage": "es", "defaultAudioLanguage": "es"},
            "status": {"privacyStatus": m.get("privacy", "public"), "selfDeclaredMadeForKids": False}}
    size = os.path.getsize(vid)
    try:
        h, _ = api("POST", "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status&notifySubscribers=true",
                   AT, meta, {"X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
        loc = h["Location"]
        req = urllib.request.Request(loc, data=open(vid, "rb").read(), method="PUT", headers={"Authorization": "Bearer " + AT, "Content-Type": "video/mp4"})
        with urllib.request.urlopen(req, timeout=900) as r: res = json.load(r)
    except urllib.error.HTTPError as e:
        status("ERROR subiendo %s: %s %s" % (mf, e.code, e.read()[:400].decode(errors="ignore"))); continue
    pub.append({"id": res["id"], "titulo": m["title"], "url": "https://www.youtube.com/watch?v=" + res["id"], "privacidad_pedida": meta["status"]["privacyStatus"],
                "privacidad_devuelta": res.get("status", {}).get("privacyStatus"), "publicado_utc": now.isoformat()})
    json.dump(pub, open("publicados.json", "w"), ensure_ascii=False, indent=1)
    os.remove(vid); os.remove(mf)
    status("Publicado: %s → %s" % (m["title"], res["id"]))
