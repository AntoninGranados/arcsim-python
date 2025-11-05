# Python interface for ARCSim 0.3.1

> This is a work in progress

This repository provides a small Python interface and utilities to run and visualize cloth simulations using ARCSim 0.3.1. It includes helper scripts to create JSON configuration files, launch offline simulations with the bundled `arcsim` binary, and generate per-frame OBJ meshes and visualization images.

## Key scripts
- `simulation.py` — programmatic config builder and simulation runner. It builds a temporary JSON config (using `config.py`), calls `arcsim simulateoffline` and `arcsim generate`, and writes OBJ.
- `config.py` — small typed helpers for building ARCSim JSON configs (`Vec3`, `Cloth`, `Remesh`, ...), plus `upload_config()` and `cleanup_config()` utilities.

## Prerequisites
- ARCSim 0.3.1 (fixes for the original scripts can be found in : https://github.com/kaist-silab/arcsim)
- Python 3.8+ (recommended). The scripts use the following packages:
	- tqdm

You can install Python dependencies with pip:
```bash
python -m pip install -r requirements.txt
```

## Quick start
1. Build ARCSim or copy a working `arcsim` binary to `arcsim/bin/arcsim`.
2. Test the build: Run the simulation script to generate `out/` and OBJ frames:
    ```bash
    python simulation.py
    ```
    It should run a simulation similar to the one described in `conf/flag.json` (one of the exemples given by the authors)

## Notes on configuration
- The `config.py` module provides lightweight classes that produce JSON-ready
	dictionaries. `simulation.py` demonstrates writing a temporary config file
	with `upload_config()` and cleaning it up with `cleanup_config()`.
- You can also inspect or reuse example JSON templates in your ARCSim build at `arcsim/conf/`.
