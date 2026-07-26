# Data dictionary

This document describes the compact result files included in the
`results/` directory of the Memory-Plastic Cellular Automata repository.

The original production campaign was executed on the Digital Research Alliance
of Canada Nibi cluster. Raw dense trajectories, videos, scheduler logs, and
other large intermediate files are not included.

## Directory organization

Each simulation profile has its own directory:

```text
results/
├── calibration/
├── primary/
├── secondary/
├── sensitivity/
├── ablation/
└── sequential_exact/
````

A profile directory may contain:

```text
data/merged/
tables/
summaries/
```

## Profile definitions

### Calibration

Parameter-search runs used to select shared production defaults.

### Primary

Main comparison of classical and quantum-like models across geometries, task
conditions, schedules, plasticity settings, and random seeds.

### Secondary

Runs involving intrinsic adaptation, structural plasticity, and repeated-lesion
conditions.

### Sensitivity

Parameter perturbations around the calibrated defaults.

### Ablation

Controls in which transverse quantum-like state components or selected adaptive
mechanisms are removed.

### Exact sequential

One-site-at-a-time random-sequential update controls.

## Common identifiers

The exact columns may differ between files. The following names describe the
main identifiers used throughout the outputs.

| Column                  | Meaning                                                                                      |
| ----------------------- | -------------------------------------------------------------------------------------------- |
| `run_id`                | Unique identifier for a simulation run.                                                      |
| `config_id`             | Stable identifier derived from the complete simulation configuration.                        |
| `profile`               | Experimental profile, such as `primary`, `secondary`, or `ablation`.                         |
| `geometry`              | Interaction geometry used in the cellular automaton.                                         |
| `formalism`             | Local-state formalism, typically classical/Markov or quantum-like.                           |
| `task`                  | Experimental task, such as baseline, imprinting, lesion, order reversal, or repeated lesion. |
| `schedule`              | Update schedule, such as asynchronous, sequential, or exact sequential.                      |
| `seed`                  | Random seed used for matched stochastic comparisons.                                         |
| `plasticity`            | Whether adaptive weight plasticity is active.                                                |
| `intrinsic_plasticity`  | Whether intrinsic adaptation is active.                                                      |
| `structural_plasticity` | Whether structural rewiring is active.                                                       |
| `ablation`              | Ablation condition, when applicable.                                                         |

## Geometry labels

| Label               | Meaning                                                |
| ------------------- | ------------------------------------------------------ |
| `square_vn`         | Square lattice with von Neumann neighbourhood.         |
| `square_moore`      | Square lattice with Moore neighbourhood.               |
| `honeycomb`         | Honeycomb lattice with nearest-neighbour interactions. |
| `honeycomb_nnn`     | Honeycomb lattice including next-nearest neighbours.   |
| `hex_cells`         | Hexagonal-cell geometry.                               |
| `extended_moore_r2` | Extended Moore neighbourhood with radius 2.            |
| `extended_hex_r2`   | Extended hexagonal neighbourhood with radius 2.        |

## Formalism labels

| Label    | Meaning                                                |
| -------- | ------------------------------------------------------ |
| `markov` | Classical scalar-state or Markov reference model.      |
| `ql`     | Classically simulated quantum-like hidden-state model. |

The quantum-like model uses a larger hidden-state representation but is
implemented entirely with classical computation.

## Task labels

| Label             | Meaning                                            |
| ----------------- | -------------------------------------------------- |
| `baseline`        | No imposed memory or lesion challenge.             |
| `imprint`         | Pattern-imprinting task.                           |
| `lesion`          | Single lesion applied after the pre-lesion period. |
| `repeated_lesion` | More than one lesion applied during the run.       |
| `order_ab`        | Pattern A is presented before pattern B.           |
| `order_ba`        | Pattern B is presented before pattern A.           |

## Main outcome variables

| Column                 | Meaning                                                                                              |
| ---------------------- | ---------------------------------------------------------------------------------------------------- |
| `late_activity`        | Mean activity over the defined late analysis window.                                                 |
| `binary_entropy`       | Binary entropy of the activity field over the defined analysis window or final state.                |
| `late_target_corr`     | Spatial Pearson correlation between the final or late activity field and the imposed target pattern. |
| `prelesion_similarity` | Similarity between a later activity field and the exact activity field immediately before lesion.    |
| `repair_gain`          | Increase in exact pre-lesion similarity after lesion relative to the immediate post-lesion value.    |
| `target_corr`          | Spatial correlation with the imposed target pattern.                                                 |
| `mean_activity`        | Mean scalar activity over sites.                                                                     |
| `entropy`              | Activity-field entropy.                                                                              |

Exact column names should be interpreted using the headers of the included CSV
files. Some files may use closely related names for profile-specific summaries.

## Paired differences

Matched model contrasts are generally reported as:

```text
quantum-like value minus classical value
```

Positive values therefore indicate a larger value in the quantum-like model,
while negative values indicate a smaller value.

Pairs are matched on the relevant combination of:

* geometry;
* task;
* update schedule;
* plasticity condition;
* random seed;
* timing;
* shared parameter values.

## Calibration outputs

Calibration tables may include:

| Column            | Meaning                                                            |
| ----------------- | ------------------------------------------------------------------ |
| `rank`            | Rank of a candidate parameter set.                                 |
| `score`           | Calibration objective or aggregate ranking score.                  |
| `alpha`           | Update or mixing parameter.                                        |
| `memory_strength` | Strength of the memory contribution.                               |
| `plasticity_rate` | Weight-plasticity learning rate.                                   |
| `selected`        | Whether the parameter set was promoted to the production defaults. |

The selected defaults are also stored in:

```text
configs/calibrated_defaults.json
```

## Representative-condition outputs

Representative-condition tables may include:

| Column           | Meaning                                                                      |
| ---------------- | ---------------------------------------------------------------------------- |
| `selection_type` | Reason for selection, such as median, visual, divergence, or recovery audit. |
| `source_profile` | Profile from which the condition was selected.                               |
| `source_run_id`  | Identifier of the original coarse run.                                       |
| `dense_run_id`   | Identifier of the dense rerun, when available.                               |
| `media_id`       | Short identifier used in media filenames.                                    |

## Missing and excluded data

The repository does not include:

* raw dense state arrays;
* complete trajectory archives;
* MP4 or WebM animations;
* cluster scheduler logs;
* temporary analysis files;
* large intermediate arrays.

These were excluded because of size or because they are specific to the original
cluster environment.

## Units and scales

Most activity, entropy, correlation, and similarity variables are
dimensionless.

Time is represented in simulation steps unless a file explicitly defines
another unit.

## Provenance

The result files were produced by the simulation and analysis code in `src/`
using the configuration files in `configs/`.

The main analysis code is:

```text
src/mpa_analysis.py
```

The main simulation code is:

```text
src/memory_plastic_automata.py
src/sim_core.py
```

Calibration and selection utilities include:

```text
src/promote_calibration.py
src/make_calibrated_configs.py
src/promote_dense_reruns.py
```

## Notes on interpretation

Late target correlation measures resemblance to the imposed target pattern. It
does not measure exact reconstruction of the pre-lesion state.

Exact recovery was assessed separately using similarity to the activity field
recorded immediately before lesion.

````

Do not invent additional exact column names beyond those actually present in the CSV headers. After opening the files, remove any row from the dictionary that does not correspond to a real column or documented derived metric.



