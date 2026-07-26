from __future__ import annotations
import argparse, base64, json, subprocess, tempfile, os
from io import BytesIO
from pathlib import Path
import numpy as np, matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
from matplotlib.collections import LineCollection
from sim_core import cell_coordinates, geometry_family, precompute_neighbors


def cfg(n):
    return json.loads(str(n["config_json"]))


def edges(L, g):
    nr, nc = precompute_neighbors(L, g); X, Y = cell_coordinates(L, g); e = []
    for r in range(L):
        for c in range(L):
            for k in range(nr.shape[0]):
                rr, cc = int(nr[k, r, c]), int(nc[k, r, c])
                if (r, c) < (rr, cc):
                    e.append(((X[r, c], Y[r, c]), (X[rr, cc], Y[rr, cc])))
    return e


def draw(ax, p, g, f, title, les=None, coh=None):
    fam = geometry_family(g); X, Y = cell_coordinates(p.shape[0], g); cmap = "viridis" if f == "markov" else "plasma"
    ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title, color="#0f766e" if f == "markov" else "#7e22ce")
    if fam == "square":
        ax.imshow(p, cmap=cmap, vmin=0, vmax=1, origin="lower", interpolation="nearest")
        if les is not None: ax.contour(les, levels=[.5], colors="red", linewidths=.8, origin="lower")
    elif fam == "hex":
        cm = plt.get_cmap(cmap)
        for r in range(p.shape[0]):
            for c in range(p.shape[1]):
                ax.add_patch(RegularPolygon((X[r, c], Y[r, c]), 6, radius=.57, orientation=np.pi/6, facecolor=cm(float(p[r, c])), edgecolor=(0, 0, 0, .08), linewidth=.2))
        ax.set_xlim(X.min() - 1, X.max() + 1); ax.set_ylim(Y.min() - 1, Y.max() + 1)
    else:
        ax.add_collection(LineCollection(edges(p.shape[0], g), colors=(.6, .6, .6, .18), linewidths=.5))
        ax.scatter(X, Y, c=p, s=20, cmap=cmap, vmin=0, vmax=1, edgecolors="black", linewidths=.1)
        ax.set_xlim(X.min() - 1, X.max() + 1); ax.set_ylim(Y.min() - 1, Y.max() + 1)
    if coh is not None:
        ax.text(.02, .02, f"coherence={coh.mean():.3f}", transform=ax.transAxes, color="#7e22ce", fontsize=7, bbox=dict(fc="white", ec="none", alpha=.65))


def img(p, c, les=None, coh=None):
    fig, ax = plt.subplots(figsize=(6, 6), dpi=120)
    draw(ax, p, c["geometry"], c["formalism"], f"{c['geometry']} | {c['formalism']} | {c['schedule']} | {c['task']}", les, coh)
    fig.tight_layout(); buf = BytesIO(); fig.savefig(buf, format="png", dpi=120); plt.close(fig)
    return buf.getvalue()


def has_webm_encoder() -> bool:
    try:
        out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True, check=False)
        return "libvpx-vp9" in out.stdout
    except Exception:
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-root", required=True)
    p.add_argument("--job-index", type=int, default=int(os.environ.get("SLURM_ARRAY_TASK_ID", 0)))
    p.add_argument("--num-jobs", type=int, default=int(os.environ.get("NUM_JOBS", 1)))
    a = p.parse_args(); root = Path(a.run_root)
    files = sorted((root / "data/trajectories_dense").glob("*.npz"))
    files = [f for i, f in enumerate(files) if i % a.num_jobs == a.job_index]
    webm_ok = has_webm_encoder()
    notes = []
    for f in files:
        n = np.load(f, allow_pickle=True); c = cfg(n); P = n["p"]; times = n["times"]; les = n["lesion1"]; coh = np.sqrt(n["x"] ** 2 + n["y"] ** 2) if "x" in n and "y" in n else None
        idx = sorted(set([0, len(P) // 3, 2 * len(P) // 3, len(P) - 1])); fig, axs = plt.subplots(2, 2, figsize=(8, 7))
        for ax, i in zip(axs.ravel(), idx):
            draw(ax, P[i], c["geometry"], c["formalism"], f"t={times[i]}", les, coh[i] if coh is not None else None)
        fig.suptitle(f.stem); fig.tight_layout()
        fig.savefig(root / "figures/png" / f"{f.stem}.png", dpi=600)
        fig.savefig(root / "figures/pdf" / f"{f.stem}.pdf")
        fig.savefig(root / "figures/svg" / f"{f.stem}.svg")
        plt.close(fig)
        frames = []
        with tempfile.TemporaryDirectory() as td0:
            td = Path(td0)
            for i in range(len(P)):
                b = img(P[i], c, les, coh[i] if coh is not None else None)
                (td / f"f_{i:04d}.png").write_bytes(b)
                frames.append("data:image/png;base64," + base64.b64encode(b).decode())
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "8", "-i", str(td / "f_%04d.png"), "-pix_fmt", "yuv420p", str(root / "videos" / f"{f.stem}.mp4")], check=True)
            if webm_ok:
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "8", "-i", str(td / "f_%04d.png"), "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "32", str(root / "videos" / f"{f.stem}.webm")], check=True)
            else:
                notes.append(f"WEBM_SKIPPED {f.stem}")
        data = json.dumps({"frames": frames, "times": times.tolist(), "title": f.stem})
        html = f'''<!doctype html><meta charset="utf-8"><title>{f.stem}</title><style>body{{font-family:Arial;background:#111;color:#eee;text-align:center}}img{{max-width:85vw;max-height:75vh}}input{{width:80vw}}</style><h2 id=t></h2><img id=i><br><button onclick="play()">Play/Pause</button><input id=s type=range min=0 max={len(frames)-1} value=0><script>const D={data};let k=0,timer=null;const im=document.getElementById('i'),s=document.getElementById('s'),t=document.getElementById('t');function show(){{k=+s.value;im.src=D.frames[k];t.textContent=D.title+' | t='+D.times[k]}}s.oninput=show;function play(){{if(timer){{clearInterval(timer);timer=null}}else timer=setInterval(()=>{{k=(k+1)%D.frames.length;s.value=k;show()}},125)}}show()</script>'''
        (root / "html" / f"{f.stem}.html").write_text(html)
    (root / "status" / f"MEDIA_JOB_{a.job_index:03d}.done").write_text(f"MEDIA COMPLETED {len(files)}\n" + ("\n".join(notes) + "\n" if notes else ""))
    print(f"MEDIA COMPLETED {len(files)}")


if __name__ == "__main__":
    main()
