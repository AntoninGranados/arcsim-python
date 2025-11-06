# Python interface for ARCSim 0.3.1

> ⚠️ This is a work in progress

A lightweight Python interface to run and visualize cloth simulations using ARCSim 0.3.1. Generate JSON configurations, run offline simulations, and produce per-frame OBJ meshes and visualization images.

## Key Components
- `arcsim_config.py` — helper classes for building ARCSim JSON configs
- `arcsim_runner.py` — handles simulation execution and OBJ generation
- `mesh.py` — `Mesh` class for OBJ file manipulation (import/export)
- `simulation_state.py` — class for simulation state (.obj generating by ARCSim) parsing/loading/saving

## Prerequisites
- ARCSim 0.3.1 (see https://github.com/kaist-silab/arcsim for fixes on the original scipts)
- Python 3.8+ with dependencies:
	- tqdm
	- numpy
	- scipy
```bash
python -m pip install -r requirements.txt
```

## Quick Start
1. Place the `arcsim` binary in `arcsim/bin/arcsim` (you can also provide another path when instancing `ARCSimRunner`)
2. Run the demo simulation:
```bash
python arcsim_runner.py
```

## Configuration
JSON configuration files can be created using the helper classes in `config.py` or reused from the examples in `arcsim/conf/`. The `arcsim_runner.py` script demonstrates how to generate config structs and run basic simulations (the simulation is a reproduction of `arcsim/conf/flag.json`).
