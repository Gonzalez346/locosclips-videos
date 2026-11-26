#!/usr/bin/env python3
"""Publica el siguiente video pendiente de bubu/schedule en YouTube (hecho para niños, público).
Necesita los secretos YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN."""
import json, os, sys, glob
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

done_path = "bubu/published.json"
done = json.load(open(done_path)) if os.path.exists(done_path) else []
pending = [os.path.basename(p)[:-5] for p in sorted(glob.glob("bubu/schedule/*.json")) if os.path.basename(p)[:-5] not in done]
if not all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")):
    print("Faltan los secretos de YouTube; no se publica nada."); sys.exit(0)
if not pending:
    print("Nada pendiente."); sys.exit(0)
vid = pending[0]; meta = json.load(open(f"bubu/schedule/{vid}.json")); path = f"bubu/videos/{vid}.mp4"
if not os.path.exists(path):
    print("Falta el archivo", path); sys.exit(1)
creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], client_id=os.environ["YT_CLIENT_ID"],
                    client_secret=os.environ["YT_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token")
yt = build("youtube", "v3", credentials=creds)
body = {"snippet": {"title": meta["title"][:100], "description": meta["description"], "tags": meta.get("tags", []),
                    "categoryId": "27", "defaultLanguage": "es", "defaultAudioLanguage": "es"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": True, "embeddable": True, "publicStatsViewable": True}}
req = yt.videos().insert(part="snippet,status", body=body, notifySubscribers=True,
                         media_body=MediaFileUpload(path, mimetype="video/mp4", resumable=True, chunksize=4 * 1024 * 1024))
resp = None
while resp is None:
    st, resp = req.next_chunk()
    if st: print(f"{int(st.progress() * 100)}%")
print("Publicado:", resp["id"])
done.append(vid); json.dump(done, open(done_path, "w"), indent=1)
