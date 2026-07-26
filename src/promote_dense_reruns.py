from __future__ import annotations
import argparse, json
from pathlib import Path
from dataclasses import fields
import pandas as pd
from sim_core import SimConfig

FIELD_NAMES = {f.name for f in fields(SimConfig)}


def row_to_cfg(r: pd.Series, snapshot_every: int) -> dict:
    d = {}
    for k in FIELD_NAMES:
        if k in r.index and pd.notna(r[k]):
            v = r[k]
            if k in {"intrinsic_enabled", "structural_enabled", "save_dense", "diagonal_ablation"}:
                d[k] = bool(v)
            elif k in {"seed", "L", "T", "snapshot_every", "metric_stride", "structural_interval", "structural_min_degree", "imprint_start", "imprint_duration", "second_imprint_start", "second_imprint_duration", "lesion_time", "second_lesion_time", "sensitivity_point"}:
                d[k] = int(v)
            elif isinstance(v, str):
                d[k] = v
            else:
                d[k] = float(v)
    d["snapshot_every"] = snapshot_every
    d["save_dense"] = True
    return d


def choose_rows(run_name: str, df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    if run_name == "primary":
        d = d[d["selection_role"].isin(["median", "visual", "high_repair"])]
        d = d[d["schedule"].isin(["alpha_async", "sequential"])]
        d = d[d["task"].isin(["baseline", "lesion", "order_ab", "order_ba"])]
        key = ["geometry", "formalism", "plasticity", "schedule", "task", "selection_role"]
        return d.sort_values("selection_role").drop_duplicates(key)
    if run_name == "secondary":
        d = d[d["selection_role"].isin(["median", "high_repair"])]
        d = d[d["schedule"].isin(["alpha_async"])]
        d = d[d["task"].isin(["lesion", "repeated_lesion"])]
        key = ["geometry", "formalism", "intrinsic_enabled", "structural_enabled", "task", "selection_role"]
        return d.drop_duplicates(key)
    if run_name == "sensitivity":
        d = d[d["selection_role"].isin(["median", "visual"])]
        key = ["geometry", "formalism", "gamma", "memory_strength", "eta_weight", "selection_role"]
        d = d.drop_duplicates(key)
        # keep one median and one visual per geometry-formalism, emphasizing central and nontrivial regimes
        out = []
        for _, g in d.groupby(["geometry", "formalism", "selection_role"], dropna=False):
            g = g.copy()
            if "gamma" in g and "memory_strength" in g and "eta_weight" in g:
                g["centrality"] = (g["gamma"] - 0.62).abs() + (g["memory_strength"] - 0.30).abs() + 20 * (g["eta_weight"] - 0.010).abs()
                out.append(g.sort_values("centrality").iloc[0])
            else:
                out.append(g.iloc[0])
        return pd.DataFrame(out)
    if run_name == "ablation":
        d = d[d["selection_role"].isin(["median", "visual", "high_repair"])]
        d = d[d["task"].isin(["lesion", "order_ab", "order_ba"])]
        key = ["geometry", "formalism", "task", "diagonal_ablation", "memory_strength", "selection_role"]
        return d.drop_duplicates(key)
    if run_name == "sequential_exact":
        d = d[d["selection_role"].isin(["median", "high_repair"])]
        key = ["geometry", "formalism", "plasticity", "task", "selection_role"]
        return d.drop_duplicates(key)
    return d.iloc[0:0]


def main():
    p = argparse.ArgumentParser(); p.add_argument("--runs-root", required=True); p.add_argument("--output", required=True); p.add_argument("--snapshot-every", type=int, default=5); a = p.parse_args(); rr = Path(a.runs_root)
    rows = []
    defaults = {}
    selected_counts = {}
    for run_name in ["primary", "secondary", "sensitivity", "ablation", "sequential_exact"]:
        repf = rr / run_name / "tables" / "representative_conditions.csv"
        if not repf.exists():
            continue
        d = pd.read_csv(repf)
        used = sorted((rr / run_name / "config").glob("used_*.json"))
        if used and not defaults:
            defaults = json.loads(used[0].read_text()).get("defaults", {})
        chosen = choose_rows(run_name, d)
        selected_counts[run_name] = int(len(chosen))
        for _, r in chosen.iterrows():
            row = row_to_cfg(r, a.snapshot_every)
            row["profile"] = "dense_media"
            rows.append(row)
    uniq = []
    seen = set()
    for r in rows:
        k = json.dumps(r, sort_keys=True)
        if k not in seen:
            seen.add(k); uniq.append(r)
    Path(a.output).write_text(json.dumps({"profile_name": "dense_media", "defaults": defaults, "explicit_conditions": uniq, "selected_counts": selected_counts}, indent=2))
    print(f"DENSE CONFIG COMPLETED: {len(uniq)}")


if __name__ == "__main__":
    main()
