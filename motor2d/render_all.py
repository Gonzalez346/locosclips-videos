import sys, os
from multiprocessing import Pool
import scene_ejemplo_hannibal as scene
def job(fi):
    scene.render(fi, 1.5).save(f"frames2/f{fi:04d}.jpg", quality=94)
    return fi
if __name__ == "__main__":
    os.makedirs("frames2", exist_ok=True)
    todo = [i for i in range(scene.N) if not os.path.exists(f"frames2/f{i:04d}.jpg")]
    with Pool(2) as p:
        for k, _ in enumerate(p.imap_unordered(job, todo, chunksize=6)):
            if k % 100 == 0: print(k, len(todo), flush=True)
    print("DONE", flush=True)
