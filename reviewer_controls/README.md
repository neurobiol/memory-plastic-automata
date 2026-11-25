# Focused reviewer controls (23 Nov 2026)

## Scope
This folder contains a local, source-equivalent reproduction of the relevant update equations from `neurobiol/memory-plastic-automata` tag `v1.1.0`, plus two reviewer-directed extensions. The original source repository and archived release were not modified.

The comparison includes:
- Scalar classical state `markov` (p,m).
- Original unit-ball hidden state `ql` (x,y,z,m).
- Equal-dimensional box-bounded classical variant `box` (x,y,z,m), preserving all provisional update equations and common parameters, but clipping each coordinate to [-1,1] in place of radial projection.

For each case, a lesion branch and sham branch begin from the same complete state at the original event time (after state/memory update, before lesion and plastic update), use the same stochastic update masks, and continue independently. Error metrics are measured over the lesion mask and the entire lattice, including the immediate post-lesion baseline. The two severity modes are the original nominal f=0.08 mask (actual 32/5184 square or 38/5184 honeycomb sites) and a new nearest-central-site 415/5184 mask (~8%).

## Requirements
Python 3.10+ with `numpy`, `pandas`, `matplotlib`. LaTeX report requires `pdflatex` and common TeX packages.

## Reproduce the experiment
From the directory containing these scripts, run:

```bash
python run_controls.py --geometries square_vn --plasticities fixed --out batch_square_fixed
python run_controls.py --geometries square_vn --plasticities plastic --out batch_square_plastic
python run_controls.py --geometries honeycomb --plasticities fixed --out batch_honey_fixed
python run_controls.py --geometries honeycomb --plasticities plastic --out batch_honey_plastic
python aggregate.py
python validate.py
python audit_ablation.py
python figures.py
python make_report.py
pdflatex -interaction=nonstopmode -halt-on-error control_report.tex
pdflatex -interaction=nonstopmode -halt-on-error control_report.tex
```

All 120 model/severity cases (2 geometries × 2 plasticity settings × 5 seeds × 3 models × 2 mask severities) are in the four batch outputs. Each model/severity case generates matched lesion and sham continuations and 10 timepoint records. Full combined CSV tables are in `combined/`. The 16 additional diagonal-ablation numerical-precision cases are in `combined/ablation_precision_audit.csv`.

## Reproduction fidelity
`validate.py` checks eight primary release summaries (2 geometries × 2 plasticity settings × 2 source models, five seeds each) against the source's `results/primary/tables/summary_by_condition.csv`. It reproduces both mean late activity and mean final imposed-pattern correlation to within 8.4e-17 in this environment, with 1e-10 enforced as a conservative tolerance. The numerical source-equivalence check applies to the original `markov`/`ql` implementations for the selected primary-profile conditions. The new box and sham extensions have not been checked against a pre-existing archived reference, as no such reference exists.

The 16-case ablation precision audit uses the source-profile f=0.08 lesion, L=52, T=280, alpha-asynchronous schedule and two memory strengths. Algebraically identical scalar and transverse-ablated hidden-state equations differ by machine precision at first update, and numerical discrepancies are amplified over many nonlinear sweeps. This is an independent local precision audit, not a claim that the original historical comparison's row-level provenance was fully audited.

## Output organization
- `control_report.pdf`, `control_report.tex`: formal methods/results addendum.
- `submission_updated/response_to_editor_and_reviewer.{tex,pdf}`: revised formal rebuttal.
- `submission_updated/main.tex`, `submission_updated/references_complexsystems.bib`: updated marked manuscript and bibliography.
- `submission_updated/figures/*.pdf`: new manuscript figure assets. The journal's original class/style and pre-existing figures are *not* in this bundle; restore those assets when compiling the full manuscript. An isolated LaTeX syntax QA compilation with missing original figures stubbed passed, but the resulting placeholder PDF is intentionally not distributed as an authentic article.
- `combined/*.csv`: complete numerical metrics, controls, matched contrasts, validation, and ablation audit.
- `figures/*.pdf`/`*.png`: vector and raster plots generated from numerical results.
- `run_controls.py`, `aggregate.py`, `validate.py`, `audit_ablation.py`, `figures.py`, `make_report.py`: reproducible computational workflow.

## Scientific limits
These are focused reviewer controls: the two strongest-contrast geometries, alpha-asynchronous schedule, primary seeds 1–5, one central lesion location, and matched parameters rather than independent box-model tuning. They establish persistent lesion-related divergence from a matched sham trajectory under these conditions. They do not establish a stable attractor, exact pattern repair, a quantum mechanism, a general lesion-severity law, or model superiority across alternative parameter calibration regimes. The unchanged source release still supports the original 7-geometry primary campaign.
