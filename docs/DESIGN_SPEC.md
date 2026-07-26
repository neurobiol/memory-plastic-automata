# Pipeline design

This repository contains the core simulation, calibration, analysis, selection,
and media-rendering code used for the memory-plastic cellular automata study.

## Workflow

The computational pipeline contains the following stages:

1. Quick smoke test
2. Parameter calibration
3. Calibration-based configuration generation
4. Primary experiment profile
5. Secondary adaptation profile
6. Sensitivity analysis
7. Transverse-state ablation
8. Exact random-sequential controls
9. Representative-condition selection
10. Dense trajectory reruns
11. Analysis and media rendering

## Calibration

The calibration profile scans the update rate, memory strength, and
weight-plasticity rate. Selected parameter values are then used to generate the
production configurations.

## Primary profile

The primary profile compares classical and quantum-like models across seven
periodic geometries, multiple update schedules, fixed and plastic weights, task
conditions, and random seeds.

## Secondary profile

The secondary profile evaluates intrinsic adaptation, structural rewiring, and
repeated-lesion conditions. It is separated from the primary profile because
these mechanisms introduce additional adaptive variables and timescales.

## Controls

The sensitivity profile perturbs parameters around the calibrated defaults.

The ablation profile removes the transverse quantum-like state variables and
tests the contribution of memory and weight plasticity.

The exact-sequential profile evaluates one-site-at-a-time updating.

## Dense reruns

Production profiles store compact summary outputs. Selected representative
conditions are rerun with dense state recording for trajectory analysis,
recovery auditing, figures, and animations.

## Matched comparisons

Classical and quantum-like conditions are matched on geometry, task, schedule,
plasticity setting, seed, timing, and shared parameters. Model contrasts are
computed only between matched conditions.

## Computing environment

The original full campaign was executed on the Digital Research Alliance of
Canada Nibi cluster. The GitHub repository contains the core Python code and
configuration files, but does not include the cluster submission scripts, raw
trajectories, videos, or complete production outputs.
