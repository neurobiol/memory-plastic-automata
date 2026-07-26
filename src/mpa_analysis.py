from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

BASE_GROUP = ["geometry", "formalism", "schedule", "task", "plasticity", "intrinsic_enabled", "structural_enabled"]
SENS_KEYS = ["gamma", "memory_strength", "eta_weight", "alpha_async", "sigma_birth", "sigma_survive", "diagonal_ablation"]


def maybe_add(cols, name):
    if name in cols and name not in cols:
        cols.append(name)


def summary_group_cols(df: pd.DataFrame):
    cols = BASE_GROUP.copy()
    for k in ["gamma", "memory_strength", "eta_weight", "alpha_async", "sigma_birth", "sigma_survive", "diagonal_ablation"]:
        if k in df.columns:
            cols.append(k)
    return cols


def select_representatives(df: pd.DataFrame) -> pd.DataFrame:
    reps = []
    by = summary_group_cols(df)
    for _, g in df.groupby(by, dropna=False):
        cols = [c for c in ["activity_late", "entropy_late", "neighbor_pattern_entropy_late", "spectral_peak_fraction_late"] if c in g.columns]
        z = g[cols].copy()
        for c in cols:
            sd = float(z[c].std())
            z[c] = 0 if sd < 1e-12 else (z[c] - float(z[c].median())) / sd
        score = np.sqrt((z.values ** 2).sum(1))
        i = int(np.argmin(score))
        r = g.iloc[i].copy(); r["selection_role"] = "median"; r["selection_score"] = float(score[i]); reps.append(r)
        if "neighbor_pattern_entropy_late" in g and "spectral_peak_fraction_late" in g:
            vis = g["neighbor_pattern_entropy_late"].fillna(0) - .5 * g["spectral_peak_fraction_late"].fillna(0) - .25 * g.get("orientation_anisotropy_late", 0)
            i = int(vis.argmax())
            r = g.iloc[i].copy(); r["selection_role"] = "visual"; r["selection_score"] = float(vis.iloc[i]); reps.append(r)
        if "repair_reference_corr" in g and g["repair_reference_corr"].notna().any():
            i = int(g["repair_reference_corr"].fillna(-999).argmax())
            r = g.iloc[i].copy(); r["selection_role"] = "high_repair"; r["selection_score"] = float(g.iloc[i]["repair_reference_corr"]); reps.append(r)
    return pd.DataFrame(reps).drop_duplicates(["config_id", "selection_role"])


def matched_divergence(df: pd.DataFrame) -> pd.DataFrame:
    key = [c for c in summary_group_cols(df) if c != "formalism"] + ["seed"]
    left = df[df.formalism == "markov"]
    right = df[df.formalism == "ql"]
    if left.empty or right.empty:
        return pd.DataFrame()
    m = left.merge(right, on=key, suffixes=("_markov", "_ql"))
    if m.empty:
        return m
    for col in ["activity_late", "entropy_late", "repair_reference_corr", "neighbor_pattern_entropy_late"]:
        if f"{col}_markov" not in m or f"{col}_ql" not in m:
            m[f"d_{col}"] = 0.0
        else:
            m[f"d_{col}"] = (m[f"{col}_markov"].fillna(0) - m[f"{col}_ql"].fillna(0)).abs()
    m["divergence_score"] = m[[c for c in m.columns if c.startswith("d_")]].sum(1)
    out = []
    group_cols = [c for c in summary_group_cols(df) if c != "formalism"]
    for _, g in m.groupby(group_cols, dropna=False):
        out.append(g.sort_values("divergence_score", ascending=False).iloc[0].copy())
    return pd.DataFrame(out)


def main():
    p = argparse.ArgumentParser(); p.add_argument("--run-root", required=True); a = p.parse_args(); root = Path(a.run_root)
    files = sorted((root / "data/raw").glob("job_*.csv")); assert files, "No raw CSVs"
    frames = [pd.read_csv(f) for f in files if f.stat().st_size > 0]
    df = pd.concat(frames, ignore_index=True).drop_duplicates("config_id")
    df.to_csv(root / "data/merged/results_all.csv", index=False)
    by = summary_group_cols(df)
    mets = [c for c in ["activity_late", "entropy_late", "repair_reference_corr", "corr_A_late", "corr_B_late", "neighbor_pattern_entropy_late", "spectral_peak_fraction_late", "coherence_late", "structural_link_fraction_late", "structural_additions_total", "structural_removals_total"] if c in df.columns]
    s = df.groupby(by, dropna=False)[mets].agg(["mean", "std", "median", "count"])
    s.columns = ["__".join(x) for x in s.columns]
    s.reset_index().to_csv(root / "tables/summary_by_condition.csv", index=False)

    reps = select_representatives(df)
    reps.to_csv(root / "tables/representative_conditions.csv", index=False)
    md = matched_divergence(df)
    md.to_csv(root / "tables/matched_divergence.csv", index=False)

    for met in ["activity_late", "entropy_late", "repair_reference_corr"]:
        if met not in df:
            continue
        q = df.groupby(["geometry", "formalism"])[met].mean().unstack()
        ax = q.plot(kind="bar", figsize=(9, 5))
        ax.set_title(met); plt.tight_layout()
        plt.savefig(root / "figures/png" / f"{met}.png", dpi=600)
        plt.savefig(root / "figures/pdf" / f"{met}.pdf")
        plt.savefig(root / "figures/svg" / f"{met}.svg")
        plt.close()
    txt = [
        "# Analysis complete",
        f"- Rows: {len(df)}",
        f"- Unique configurations: {df['config_id'].nunique()}",
        f"- Geometries: {', '.join(sorted(df.geometry.astype(str).unique()))}",
        f"- Representative rows: {len(reps)}",
        f"- Matched divergence rows: {len(md)}",
        "- Status: COMPLETED",
    ]
    (root / "summaries/run_summary.md").write_text("\n".join(txt) + "\n")
    (root / "status/ANALYSIS_COMPLETED").write_text("COMPLETED\n")
    print("ANALYSIS COMPLETED")


if __name__ == "__main__":
    main()
