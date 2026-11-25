import sys, os, time
from multiprocessing import Pool
import rend
from capt2 import Caps
rend.CAPFN = Caps()
import scene_pickles as S
SS = 1.5
os.makedirs("frames", exist_ok=True)
def work(fi):
    p = "frames/f%05d.jpg" % fi
    if os.path.exists(p): return fi
    rend.render(fi, SS).save(p, quality=94, subsampling=0)
    return fi
if __name__ == "__main__":
    a = sys.argv[1:]
    lo, hi = (int(a[0]), int(a[1])) if a else (0, S.NFR)
    t0 = time.time()
    with Pool(2) as p:
        for k, _ in enumerate(p.imap(work, range(lo, hi), chunksize=3)):
            if k % 60 == 0: print(k, round(time.time() - t0), flush=True)
    print("done", round(time.time() - t0), flush=True)
