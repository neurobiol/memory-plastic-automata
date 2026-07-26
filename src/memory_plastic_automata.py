from __future__ import annotations
import argparse, csv, itertools, json, os, hashlib
from pathlib import Path
from typing import Any, Dict, List
from dataclasses import asdict
import numpy as np
from sim_core import SimConfig, simulate


def expand(j: Dict[str, Any]) -> List[SimConfig]:
    defaults = dict(j.get("defaults", {}))
    profile = j.get("profile_name", "run")
    out: List[SimConfig] = []
    if "explicit_conditions" in j:
        for r in j["explicit_conditions"]:
            x = defaults | r
            x["profile"] = profile
            out.append(SimConfig(**x))
        return out
    sweep = j.get("sweep", {})
    keys = list(sweep)
    vals = [sweep[k] for k in keys]
    for combo in itertools.product(*vals):
        x = defaults | dict(zip(keys, combo))
        x["profile"] = profile
        out.append(SimConfig(**x))
    return out


def layout(root: Path):
    for r in ["config", "logs", "data/raw", "data/merged", "data/trajectories_dense", "tables", "figures/png", "figures/pdf", "figures/svg", "videos", "html", "summaries", "status"]:
        (root / r).mkdir(parents=True, exist_ok=True)


def cid(c: SimConfig) -> str:
    d = asdict(c).copy()
    digest = hashlib.blake2b(json.dumps(d, sort_keys=True).encode(), digest_size=5).hexdigest()
    base = [c.geometry, c.formalism, c.plasticity, f"intr{int(c.intrinsic_enabled)}", f"struct{int(c.structural_enabled)}", c.schedule, c.task, f"s{c.seed}"]
    return "__".join(base + [digest])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--output-root", default="runs")
    p.add_argument("--run-id", required=True)
    p.add_argument("--job-index", type=int, default=int(os.environ.get("SLURM_ARRAY_TASK_ID", 0)))
    p.add_argument("--num-jobs", type=int, default=int(os.environ.get("NUM_JOBS", 1)))
    p.add_argument("--dense", action="store_true")
    a = p.parse_args()

    j = json.loads(Path(a.config).read_text())
    root = Path(a.output_root) / a.run_id
    layout(root)
    (root / "config" / f"used_{Path(a.config).name}").write_text(json.dumps(j, indent=2))
    allc = expand(j)
    subset = [c for i, c in enumerate(allc) if i % a.num_jobs == a.job_index]
    records = []
    for c in subset:
        sim_summary, tr = simulate(c, a.dense or c.save_dense)
        rec = asdict(c)
        rec.update(sim_summary)
        rec["config_id"] = cid(c)
        records.append(rec)
        if tr is not None:
            np.savez_compressed(root / "data/trajectories_dense" / f"{rec['config_id']}.npz", **tr)
    if records:
        fields = sorted({k for r in records for k in r})
        with (root / "data/raw" / f"job_{a.job_index:04d}.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader(); w.writerows(records)
    else:
        (root / "data/raw" / f"job_{a.job_index:04d}.csv").write_text("")
    (root / "status" / f"job_{a.job_index:04d}.done").write_text(f"COMPLETED {len(records)}\n")
    print(f"COMPLETED {len(records)} configurations")


if __name__ == "__main__":
    main()
