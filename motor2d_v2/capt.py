import re, subprocess, numpy as np
from scipy.ndimage import uniform_filter1d
from kit2 import draw_caption

CL = [(0.00,1.76,"En mil novecientos veinticinco,"),(2.05,4.12,"un estafador vendió la Torre Eiffel."),(4.75,6.45,"Se llamaba Víctor Lustig."),(7.17,9.68,"París gastaba mucho dinero en mantener la torre,"),(10.01,11.36,"y eso le dio una idea."),(12.03,14.08,"Invitó a seis empresarios del metal"),(14.20,15.23,"a un hotel de lujo."),(15.83,18.08,"Les dijo que era un funcionario del gobierno,"),(18.30,19.82,"y que iban a derribar la torre."),(20.38,21.75,"Quien ofreciera más dinero,"),(21.98,22.61,"se llevaría"),(22.77,23.52,"todo el hierro."),(24.20,25.23,"Uno de ellos pagó,"),(25.52,27.58,"convencido de que hacía un gran negocio."),(28.18,30.17,"Lustig desapareció con el dinero."),(30.73,32.98,"Pero el engañado sintió tanta vergüenza,"),(33.18,34.61,"que nunca fue a la policía."),(35.23,37.36,"Lo intentó otra vez con otros empresarios,"),(37.73,38.37,"pero esta vez"),(38.54,39.78,"llamaron a la policía."),(40.30,41.04,"Así que sí:"),(41.59,43.49,"un hombre vendió la Torre Eiffel.")]
HOT = {"torre","eiffel","estafador","lustig","dinero","idea","policía","vendió","hierro","vergüenza","veinticinco","fortuna","pagó","desapareció","sí","derribar"}

def load_voice(path="voice.mp3", sr=16000):
    raw = subprocess.run(["ffmpeg","-v","error","-i",path,"-ac","1","-ar",str(sr),"-f","f32le","-"],capture_output=True).stdout
    return np.frombuffer(raw, np.float32), sr

def syl(w):
    w = re.sub(r"[^a-záéíóúüñ]", "", w.lower())
    n = len(re.findall(r"[aeiouáéíóú]+", w)); return max(1, n) + .25 * len(w) / 4

def words_timed(y, sr):
    hop = int(sr * .005)
    e = np.sqrt(uniform_filter1d(y[:len(y)//hop*hop].reshape(-1, hop).__pow__(2).mean(1), 5))
    out = []
    for (a, b, txt) in CL:
        ws = txt.split(); wts = np.array([syl(w) for w in ws]); cum = np.concatenate([[0], np.cumsum(wts)]) / wts.sum()
        bnd = [a + (b - a) * c for c in cum]
        for i in range(1, len(ws)):
            lo = int((bnd[i] - .08) / .005); hi = int((bnd[i] + .08) / .005)
            seg = e[max(0, lo):min(len(e), hi)]
            if len(seg): bnd[i] = (max(0, lo) + int(np.argmin(seg))) * .005
        for i, w in enumerate(ws): out.append((bnd[i], bnd[i + 1], w))
    return out

SMALL = {"en","un","la","el","de","y","a","que","se","les","lo","por","con","su","al","uno","ellos","era","iba","más","del","mil","dijo","hacía","pero","así","sí:","gran","otra","vez","ya","me","te"}
def chunks(wt):
    ch = []; i = 0
    while i < len(wt):
        a, b, w = wt[i]
        grp = [wt[i]]
        if (w.strip(",.:").lower() in SMALL or len(w.strip(",.:")) <= 3) and i + 1 < len(wt) and wt[i + 1][0] - b < .25 and not w.endswith((",", ".", ":")):
            grp.append(wt[i + 1]); i += 1
        ch.append((grp[0][0], grp[-1][1], [g[2] for g in grp])); i += 1
    return ch

class Caps:
    def __init__(self):
        y, sr = load_voice(); self.wt = words_timed(y, sr); self.ch = chunks(self.wt)
        self.starts = np.array([c[0] for c in self.ch])
    def __call__(self, img, t):
        i = int(np.searchsorted(self.starts, t + .03, side="right")) - 1
        if i < 0: return img
        a, b, ws = self.ch[i]
        nxt = self.ch[i + 1][0] if i + 1 < len(self.ch) else 99
        if t > b + .22 and t < nxt: return img
        return draw_caption(img, ws, t, a, HOT)
if __name__ == "__main__":
    c = Caps()
    for x in c.ch[:14]: print("%.2f %.2f %s" % x)
