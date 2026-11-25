import sys, os, time
from multiprocessing import Pool
import scene_lustig as S
from capt import Caps
S.CAPFN = Caps()
SS = 1.4
os.makedirs("frames", exist_ok=True)
def work(fi):
    p = "frames/f%05d.jpg" % fi
    if os.path.exists(p): return fi
    S.render(fi, SS).save(p, quality=93, subsampling=0)
    return fi
if __name__ == "__main__":
    a = sys.argv[1:]
    lo, hi = (int(a[0]), int(a[1])) if a else (0, S.NFR)
    t0 = time.time()
    with Pool(2) as p:
        for k, _ in enumerate(p.imap(work, range(lo, hi), chunksize=4)):
            if k % 50 == 0: print(k, time.time() - t0, flush=True)
    print("done", time.time() - t0, flush=True)
