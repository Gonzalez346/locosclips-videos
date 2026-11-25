import re, subprocess, numpy as np
from scipy.ndimage import uniform_filter1d
from kit2 import draw_caption

CL = [(0.05,3.39,"Cuatro meses antes del Mundial de 1966,"),(3.80,5.66,"alguien robó la Copa del Mundo."),(6.45,8.20,"Estaba en una exposición de Londres,"),(8.51,10.90,"y la policía no tenía ni una pista."),(11.57,13.29,"Inglaterra entró en pánico:"),(13.82,15.94,"iban a organizar un Mundial sin trofeo."),(16.83,17.76,"Pasó una semana."),(18.48,20.37,"Un hombre salió a pasear con su perro,"),(20.68,21.12,"Pickles."),(21.78,22.30,"De pronto,"),(22.63,24.57,"el perro empezó a olfatear un seto,"),(24.98,27.47,"y encontró un paquete envuelto en periódicos."),(28.07,28.60,"Dentro"),(28.78,30.40,"estaba la Copa del Mundo."),(31.07,31.77,"Al principio,"),(31.91,33.55,"la policía sospechó del dueño,"),(34.01,34.79,"pero la historia"),(34.91,35.62,"era cierta."),(36.40,37.51,"Cuatro meses después,"),(37.81,39.53,"Inglaterra ganó el Mundial,"),(39.90,42.11,"y Pickles celebró con los campeones."),(42.95,43.75,"Años más tarde,"),(44.09,45.70,"la copa fue robada otra vez,"),(45.92,46.55,"en Brasil,"),(46.96,48.53,"y nunca volvió a aparecer."),(49.22,49.81,"Esta vez,"),(50.09,51.60,"no había ningún perro.")]
HOT = {"mundial","1966","robó","copa","londres","policía","pista","pánico","trofeo","semana","perro","pickles","pronto","seto","paquete","periódicos","dentro","sospechó","cierta","ganó","campeones","brasil","nunca","ningún"}
SPOKEN = {"1966,": "mil novecientos sesenta y seis"}

def load_voice(path="voice.mp3", sr=16000):
    raw = subprocess.run(["ffmpeg","-v","error","-i",path,"-ac","1","-ar",str(sr),"-f","f32le","-"],capture_output=True).stdout
    return np.frombuffer(raw, np.float32), sr

def syl(w):
    if w in SPOKEN: return sum(syl(x) for x in SPOKEN[w].split())
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
