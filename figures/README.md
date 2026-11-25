# Manuscript figures

This directory contains figures accompanying *Geometry, Plasticity, and Memory in Cellular Automata with Quantum-Like Hidden States*.

## Revised figures

- `fig3_recreated.pdf`: revised Figure 3, covering transverse-state contributions and the pre-lesion-state analysis.
- `control_square_vn.pdf`: additional computational controls for the square von Neumann geometry.
- `control_honeycomb.pdf`: additional computational controls for the honeycomb geometry.

## Reproducibility

Figure 3 can be regenerated using:

```bash
python src/regenerate_fig3.py
```

Run this command from the repository root. The script uses the rounded numerical values reported in the manuscript and saves its output in this directory.

The additional computational controls, including their simulation scripts, numerical results, and analysis procedures, are documented in `reviewer_controls/README.md`. Their numerical results are available in `reviewer_controls/combined/`.

The original simulation and figure-generation scripts remain available in `src/`.

