# How to run

Everything below is run from the repository root.

```bash
git clone https://github.com/GHOSTALERT/cache-hierarchy-ncg.git
cd cache-hierarchy-ncg
```

## Requirements

- Linux (tested on Ubuntu, 16 cores)
- Python 3.10+ with `matplotlib`
- gem5 v25.1 built for ARM, and an AArch64 cross compiler for the benchmarks. `scripts/build_gem5_arm.sh` sets up both without sudo.

## 1. One-time setup

Arm cross compiler, gem5 ARM build (about 1 hour), benchmark binaries:

```bash
bash scripts/build_gem5_arm.sh                 # gem5 checkout defaults to ~/gem5
python3 -m venv --without-pip .venv && python3 -m pip --python .venv/bin/python install matplotlib
```

## 2. Simulate all 24 configurations

Runs in parallel, a few minutes on 16 cores:

```bash
.venv/bin/python scripts/run_sweep.py          # --only size_l2_  /  --force  /  --gem5 PATH
```

## 3. Metrics, NCG and Pareto frontier

Writes `results/rerun/{summary,ncg,pareto}.csv` and `tables.md`:

```bash
.venv/bin/python scripts/parse_ncg.py
.venv/bin/python scripts/parse_ncg.py --source original    # same analysis on the report's raw data
```

## 4. Figures

Writes `results/rerun/figures`, `results/original/figures` and `results/comparison`:

```bash
.venv/bin/python scripts/plot_results.py
.venv/bin/python scripts/plot_results.py --source original
.venv/bin/python scripts/plot_results.py --compare
```

## A single configuration by hand

```bash
~/gem5/build/ARM/gem5.opt --outdir=m5out configs/three_level.py \
    --binary benchmarks/bin/cache_size_sweep --l2-size 512KiB --l1-assoc 8
```
