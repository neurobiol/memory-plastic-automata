# Memory-Plastic Cellular Automata

This repository contains the simulation, analysis, configuration, and media-rendering code used for the memory-plastic cellular automata project.

The project compares classical Markov cellular automata with a classically simulated quantum-like local-state model across different interaction geometries, update schemes, memory conditions, plasticity mechanisms, and perturbation tasks.

## Repository Structure

```text
memory-plastic-automata/
├── configs/
├── src/
├── CITATION.cff
├── LICENSE
└── README.md
````

## Source Code

The `src/` directory contains the seven Python files used to construct and analyse the simulation pipeline.

* `memory_plastic_automata.py`
  Main simulation entry point. It reads a configuration file, generates the requested experimental conditions, and runs the cellular automata simulations.

* `sim_core.py`
  Core model implementation, including lattice geometries, classical and quantum-like local states, update rules, memory traces, plasticity, perturbations, and outcome calculations.

* `mpa_analysis.py`
  Calculates summary statistics and comparisons from completed simulation outputs.

* `render_media.py`
  Produces trajectory figures, animations, and video files from saved simulation data.

* `make_calibrated_configs.py`
  Generates experiment configurations using parameter values selected during calibration.

* `promote_calibration.py`
  Selects calibrated parameter sets for subsequent simulation stages.

* `promote_dense_reruns.py`
  Selects simulation conditions for densely sampled trajectory reruns and media generation.

The `.gitkeep` file in `src/` may be deleted because the directory already contains source files.

## Configuration Files

The `configs/` directory contains seven JSON files defining the simulation campaigns.

* `config_quick_smoke.json`
  Small test configuration used to confirm that the pipeline runs correctly.

* `config_calibration.json`
  Defines the parameter-calibration campaign.

* `config_primary.json`
  Defines the main comparison between classical and quantum-like models across geometries and experimental conditions.

* `config_secondary.json`
  Defines additional experiments involving plasticity, adaptation, and related model variants.

* `config_sensitivity.json`
  Defines parameter-sensitivity tests for the principal findings.

* `config_ablation.json`
  Defines controls that remove selected quantum-like state components to identify their contribution.

* `config_sequential_exact.json`
  Defines exact random-sequential update controls.

## Model Components

The code supports:

* seven periodic interaction geometries;
* classical scalar-state and quantum-like hidden-state models;
* exponentially filtered local memory;
* fixed or activity-dependent interactions;
* intrinsic and structural plasticity options;
* synchronous, approximate asynchronous, and exact sequential updating;
* baseline, imprinting, lesion, repeated-lesion, and ordered-input tasks;
* activity, entropy, target-correlation, and recovery-related outcomes.

## Usage

The simulation entry point accepts a JSON configuration file. A small pipeline check can be performed with:

```bash
python src/memory_plastic_automata.py --config configs/config_quick_smoke.json
```

The exact command-line options available in the current version can be displayed with:

```bash
python src/memory_plastic_automata.py --help
```

Large simulation campaigns may require substantial computational time and storage.

## Data and Videos

Raw trajectories, simulation outputs, cluster logs, and video files are not included in this repository because of their size.

## Citation

Citation metadata are provided in `CITATION.cff`.

## License

Copyright © 2026 Yashine H. Goolam Hossen. All rights reserved.

The source code is provided for academic inspection. Reuse, reproduction, modification, or redistribution requires prior written permission from the copyright holder.


