from pathlib import Path
import pandas as pd
r=Path(__file__).resolve().parent
p=r/'combined'
d=pd.read_csv(p/'derived_by_case.csv')
s=d.groupby(['geometry','area_mode','formalism']).agg(n=('seed','size'),D0=('initial_damage_mae_local','mean'),Dlocal=('damage_mae_local','mean'),Dglobal=('damage_mae_global','mean'),Tcorr=('target_corr_lesion','mean'),Act=('mean_activity_lesion','mean'),shamPre=('sham_pre_mae_local','mean')).reset_index()
names={'square_vn':'Square von Neumann','honeycomb':'Honeycomb'}
models={'markov':'Scalar','box':'4-var. box','ql':'4-var. unit-ball'}
rows=[]
for geo in ('square_vn','honeycomb'):
 for formalism in ('markov','box','ql'):
  x=s.query('geometry==@geo and formalism==@formalism and area_mode=="nominal"').iloc[0]
  rows.append(f"{names[geo]} & {models[formalism]} & {x.Act:.3f} & {x.Tcorr:+.3f} & {x.D0:.3f} & {x.Dlocal:.3f} & {x.Dglobal:.3f} \\\\")
rows8=[]
for geo in ('square_vn','honeycomb'):
 for formalism in ('markov','box','ql'):
  x=s.query('geometry==@geo and formalism==@formalism and area_mode=="eight_percent"').iloc[0]
  rows8.append(f"{names[geo]} & {models[formalism]} & {x.Dlocal:.3f} & {x.Dglobal:.3f} & {x.Tcorr:+.3f} \\\\")
tex=r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=22mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern,microtype,amsmath,amssymb,booktabs,array,graphicx,xcolor,hyperref}
\usepackage{caption}
\hypersetup{colorlinks=true,urlcolor=blue}
\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}
\title{Focused Computational Controls for the Cellular-Automata Reviewer Report}
\author{Computational verification supplement (draft for author review)}
\date{23 November 2026}
\begin{document}
\maketitle
\section*{Scope and source verification}
We ran a focused reimplementation of the archived \emph{Memory-Plastic Cellular Automata} v1.1.0 primary update equations, with a counterfactual lesion/sham fork and an equal-dimensional classical alternative. The unmodified scalar and unit-ball algorithms were first checked against eight archived primary-profile summaries (two geometries, two plasticity settings, two model types, five seeds). Late activity and final target-correlation averages reproduce the released results with maximum absolute discrepancy below $9\times10^{-17}$ (\texttt{archived\_parity.csv}). This is a verified local reproduction of the selected source workflow, not a new cluster campaign or a replacement for the full archived release.

\section*{Methods}
Each case uses $L=72$, $T=500$, the calibrated primary defaults $\gamma=0.68$, $\mu=0.20$, $\eta_w=0.016$ (for plastic conditions), $\tau_m=30$, and $\alpha$-asynchronous site selection with $\alpha=0.5$. Geometries are square von Neumann and honeycomb, with fixed and plastic weights and seeds 1--5. The first pattern is imposed at sweeps 100--149; lesion occurs at $t=300$, after the state and memory updates but before the event-sweep weight update, as in the source. The state, memory, bias, edge weights, and utility are identical at the branch point. Future random site-selection masks have the same seed and sweep index in both branches. The lesion branch is reset on the mask; the sham branch receives no intervention. Both then undergo the same update rule independently until sweep 499.

Three observation models are compared: (i) scalar activity plus memory, (ii) the original unit-ball hidden state $x,y,z,m$, and (iii) an equal-dimensional classical box control with the \emph{same} four variables, provisional equations, feedback and common parameters as model (ii), replacing only radial projection by componentwise clipping of $x,y,z$ to $[-1,1]$. The box control isolates the bounding architecture under shared parameters; it does not establish a quantum mechanism or equal model quality after independent tuning.

There are $2\times2\times5\times3\times2=120$ independently specified model/severity cases, each with two matched continuation branches. The original lesion parameter $f=0.08$ yields 32/5184 (0.617\%) masked square sites and 38/5184 (0.733\%) honeycomb sites. A separate severity check masks the 415 sites closest to the center (8.005\% of the lattice). These are two distinct interventions, not equivalent uses of $f$.

Let $M$ denote the mask ($\mathcal L$) or entire lattice ($\Lambda$), and let $p^{\mathrm{pre}}$ denote activity immediately before lesion. Errors are
\begin{align}
E_M(t)&=\frac{1}{|M|}\sum_{i\in M}\left|p_i^{\mathrm{lesion}}(t)-p_i^{\mathrm{pre}}\right|,\\
D_M(t)&=\frac{1}{|M|}\sum_{i\in M}\left|p_i^{\mathrm{lesion}}(t)-p_i^{\mathrm{sham}}(t)\right|.
\end{align}
The event-time snapshot $t=0$ means immediately \emph{after} the lesion, before the event-sweep weight update. Follow-ups are recorded after 1, 2, 5, 10, 25, 50, 100, 150 and 199 further sweeps. Site activity and target Pearson correlation are also recorded.\par
\section*{Main result: nominal-mask lesion}
Table~\ref{tab:nominal} combines two plasticity conditions and five matched seeds per geometry--model row ($n=10$ per row). All numbers refer to the final sweep, except $D_{\mathcal L}(0)$. Here $D$ compares damaged and undamaged continuations, not the old pre-lesion image.
\begin{table}[h]\centering\small
\caption{Final-sweep contrasts for the original, small circular lesion.}\label{tab:nominal}
\setlength{\tabcolsep}{4pt}\begin{tabular}{llrrrrr}\toprule
Geometry & Model & Activity & $\rho(p,A)$ & $D_{\mathcal L}(0)$ & $D_{\mathcal L}(199)$ & $D_{\Lambda}(199)$\\\midrule
__ROWS__
\bottomrule\end{tabular}\end{table}
The original unit-ball model has more late activity but substantially less retained correlation with imposed pattern $A$ than either comparison. Across ten matched nominal-mask pairs per geometry, unit-ball minus box activity is $+0.333$ (square) and $+0.307$ (honeycomb), whereas target-correlation differences are $-0.435$ and $-0.423$. Every one of those ten paired contrasts in each geometry has the stated sign. Thus extra state variables alone do not explain the outcome; the radial versus coordinatewise constraint changes the dynamics. This is not a claim of quantum advantage.

In the unit-ball model, $D_{\mathcal L}$ falls from $0.382$ to $0.311$ (square) and from $0.405$ to $0.299$ (honeycomb), but does not approach zero by 199 post-lesion sweeps. Whole-lattice lesion/sham disagreement grows to $0.306$ and $0.311$ respectively, despite the tiny original mask. This measures damage-associated trajectory divergence, and must not be conflated with failed return to the pre-lesion snapshot, which drifts even in the sham trajectory.

\begin{figure}[h]\centering
\includegraphics[width=.49\textwidth]{figures/square_vn_damage_mae_global.pdf}\hfill
\includegraphics[width=.49\textwidth]{figures/honeycomb_damage_mae_global.pdf}
\caption{Mean whole-lattice lesion/sham absolute difference versus post-lesion sweep, averaged over five seeds and two plasticity conditions for the nominal lesion. Starting disagreement is localized to the mask; differences subsequently spread and remain nonzero.}\label{fig:global}
\end{figure}

\section*{True 8\% severity check}
\begin{table}[h]\centering\small
\caption{Final outcome after a larger, 415-site central lesion ($8.005\%$). The mean is over 10 seeds/plasticity cases per geometry and model.}\label{tab:severity}
\begin{tabular}{llrrr}\toprule
Geometry & Model & $D_{\mathcal L}(199)$ & $D_{\Lambda}(199)$ & $\rho(p,A)$\\\midrule
__ROWS8__
\bottomrule\end{tabular}\end{table}
The unit-ball model's late whole-field disagreement remains near $0.31$ for both lesion sizes. This saturation-like result should not be interpreted as a universal lesion-size law: the test has two sizes, one central position, five reused primary seeds, and only one update schedule.

\section*{Limitations and editorial interpretation}
The pre-lesion field is not guaranteed to be a stable attractor. The sham itself typically drifts appreciably from that snapshot; therefore the previous Pearson-based ``exact reconstruction'' claim remains unwarranted. Our new counterfactual experiment instead supports a narrower conclusion: in these focused conditions, a central perturbation produces persistent lesion/sham discrepancies that spread beyond the initial mask. The equal-dimensional box control shows that the outcome depends on the specific bounding architecture under the chosen parameters, not simply on the number of state variables. All tested updates are classical computations.

The tests use only square von Neumann and honeycomb neighborhoods, a single $\alpha$-asynchronous schedule, previously used seeds 1--5, two weight settings, and the original calibrated parameters (without reoptimizing the box variant). They are a focused response to the reviewer's requested controls, not a complete cross-geometry or held-out-seed robustness campaign. Values are descriptive means without population-level significance claims.\par
\section*{Reproducibility files}
The accompanying bundle contains \texttt{run\_controls.py}, \texttt{validate.py}, \texttt{aggregate.py}, \texttt{figures.py}, all per-time CSV records, paired contrasts, the validation audit, and vector figures. To reproduce from scratch in a Python environment with NumPy, pandas and Matplotlib, run four batches using the \texttt{--geometries} and \texttt{--plasticities} flags, then run \texttt{aggregate.py}, \texttt{validate.py} and \texttt{figures.py}. The exact commands are in \texttt{README.md}. Raw arrays from the original HPC campaign are not used.
\end{document}
'''
tex=tex.replace('__ROWS__','\n'.join(rows)).replace('__ROWS8__','\n'.join(rows8))
(r/'control_report.tex').write_text(tex)
