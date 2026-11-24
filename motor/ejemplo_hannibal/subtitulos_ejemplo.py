import os, glob
from PIL import Image, ImageDraw, ImageFont
FPS=30; W,H=1080,1920
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CAPS=[(0.0,3.51,"Un general cruzó los Alpes con treinta y siete elefantes."),
(4.10,6.78,"Era el año doscientos dieciocho antes de Cristo."),
(7.33,10.83,"Aníbal, de Cartago, quería atacar Roma por sorpresa."),
(11.32,12.73,"Los romanos se reían."),
(13.18,16.06,"Nadie creía que los elefantes sobrevivieran a la nieve."),
(16.64,20.46,"Los soldados se congelaban, y los animales resbalaban por el hielo."),
(21.10,25.06,"Entonces apareció una roca enorme, que bloqueaba el camino."),
(25.63,29.04,"Según la leyenda, Aníbal encendió fuego bajo la piedra."),
(29.55,31.18,"Luego la empapó con vinagre."),
(31.71,34.39,"La roca se partió, y el ejército siguió."),
(34.93,38.19,"Así que el gran secreto de Aníbal era vinagre.")]
HOT={"elefantes","roca","fuego","vinagre","Aníbal","Roma","congelaban","resbalaban","partió"}
def chunks(text):
    ws=text.split(); out=[]; i=0
    while i<len(ws):
        a=ws[i]
        if i+1<len(ws) and len(a)+len(ws[i+1])<=13 and not a.endswith(","): out.append([a,ws[i+1]]); i+=2
        else: out.append([a]); i+=1
    return out
EVENTS=[]
for a,b,text in CAPS:
    ch=chunks(text); wt=[sum(len(w)+1 for w in c) for c in ch]; tot=sum(wt); t=a
    for c,w in zip(ch,wt):
        d=(b-a)*w/tot; EVENTS.append((t,t+d,c)); t+=d
    EVENTS[-1]=(EVENTS[-1][0],b+0.12,EVENTS[-1][2])
d0=ImageDraw.Draw(Image.new("RGB",(10,10)))
def ev_at(t):
    for e in EVENTS:
        if e[0]<=t<e[1]: return e
def pop(u):  # u in seconds since chunk start
    if u>0.16: return 1.0
    x=u/0.16
    return 0.7+0.45*x if x<0.6 else 1.15-0.15*(x-0.6)/0.4
os.makedirs("frames3c",exist_ok=True)
for p in glob.glob("frames3c/*"): os.remove(p)
n=0
for fi in range(1146):
    t=fi/FPS; src=os.path.abspath(f"/root/shorts/hannibal3d/frames/f{fi:04d}.jpg"); dst=f"frames3c/f{fi:04d}.jpg"
    e=ev_at(t)
    if not e: os.symlink(src,dst); continue
    words=e[2]; text=" ".join(words)
    sz=124*pop(t-e[0]); f=ImageFont.truetype(FONT,int(sz))
    while d0.textlength(text,font=f)>990: sz-=4; f=ImageFont.truetype(FONT,int(sz))
    im=Image.open(src).convert("RGB"); d=ImageDraw.Draw(im)
    x=(W-d0.textlength(text,font=f))/2; y=1530
    for w in words:
        col=(255,224,60) if w.strip(",.").lower() in {h.lower() for h in HOT} else (255,255,255)
        d.text((x,y),w,font=f,fill=col,stroke_width=12,stroke_fill=(20,12,30),anchor="lm")
        x+=d0.textlength(w+" ",font=f)
    im.save(dst,quality=94); n+=1
print("captioned",n)
