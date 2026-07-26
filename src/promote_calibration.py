from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
import numpy as np


def main():
    p = argparse.ArgumentParser(); p.add_argument("--run-root", required=True); p.add_argument("--output", required=True); a = p.parse_args(); root = Path(a.run_root)
    df = pd.read_csv(root / "data/merged/results_all.csv")
    par_cols = [c for c in ["gamma", "memory_strength", "eta_weight"] if c in df.columns]
    if not par_cols:
        raise RuntimeError("Calibration table contains no parameter columns.")

    rows = []
    for keys, g in df.groupby(par_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        rec = dict(zip(par_cols, keys))
        activity = g["activity_late"].astype(float)
        entropy = g["entropy_late"].astype(float)
        repair = g["repair_reference_corr"].astype(float) if "repair_reference_corr" in g.columns else pd.Series(np.zeros(len(g)))
        formalism_gap = g.groupby("formalism")["activity_late"].mean()
        gap = float(abs(formalism_gap.get("markov", np.nan) - formalism_gap.get("ql", np.nan))) if len(formalism_gap) == 2 else 0.0
        collapse_pen = float(((activity < 0.05) | (activity > 0.95)).mean())
        mid_activity = float(np.mean((activity > 0.12) & (activity < 0.88)))
        rec["score"] = 1.2 * mid_activity + 0.6 * float(entropy.mean()) + 0.8 * float(repair.fillna(0).mean()) - 1.0 * collapse_pen - 0.6 * gap
        rec["collapse_penalty"] = collapse_pen
        rec["formalism_gap"] = gap
        rec["mean_activity"] = float(activity.mean())
        rows.append(rec)
    ranked = pd.DataFrame(rows).sort_values("score", ascending=False)
    best = ranked.iloc[0].to_dict()
    selected = {"gamma": float(best.get("gamma", 0.62)), "memory_strength": float(best.get("memory_strength", 0.30)), "eta_weight": float(best.get("eta_weight", 0.010))}
    out = {"selected_defaults": selected, "source_run": str(root), "rows": int(len(df)), "ranking_top10": ranked.head(10).to_dict(orient="records"), "status": "CALIBRATION_COMPLETED"}
    Path(a.output).write_text(json.dumps(out, indent=2))
    (root / "status/CALIBRATION_COMPLETED").write_text("CALIBRATION COMPLETED\n")
    (root / "tables/calibration_ranked_candidates.csv").write_text(ranked.to_csv(index=False))
    print("CALIBRATION COMPLETED")


if __name__ == "__main__":
    main()
