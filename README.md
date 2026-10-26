# Cache Hierarchy Performance Analysis: Normalized Cache Gain and Pareto-Optimal Design

BEVD207L Computer Architecture project. Team: Arrnav Trisal (24BVD0064), Gavin Fernandez (24BVD0083), Ashutosh (24BVD0065), Varun V Nair (24BVD0061). Supervisor: Vikas Vijayvargiya.

We used gem5 to study how L1, L2 and L3 cache **size** and **set associativity** affect IPC, CPI, miss rate, miss latency and execution time.
The project adds two analysis tools:

- **Normalized Cache Gain (NCG)** = ΔIPC / ΔCacheSize (IPC per KB): the performance gained for each kilobyte of cache added.
- **Pareto frontier** of IPC against total cache area (L1+L2+L3). Its knee is the most cost-efficient design.

The submitted report is in [`report/Cache_Hierarchy_NCG_Pareto_Report.pdf`](report/Cache_Hierarchy_NCG_Pareto_Report.pdf).
The team's raw gem5 output is in [`original/stats/`](original/).
This repo also contains a full, scripted re-run of the study. Results are in [`results/`](results/) and the comparison with the report is in [`docs/RESULTS.md`](docs/RESULTS.md).

## Setup

| | |
|---|---|
| Simulator | gem5 v25.1, ARM ISA, Syscall-Emulation mode |
| CPU | TimingSimpleCPU @ 1 GHz, exactly 50M instructions per run |
| Memory | DDR4-2400 (8x8), 512 MiB |
| L1I / L1D | 32 KiB, 2-way, 2-cycle tag/data, 4 MSHRs |
| L2 | 256 KiB, 8-way, 10 cycles, 16 MSHRs |
| L3 | 8 MiB, 16-way, 20 cycles, 32 MSHRs |

| Benchmark | What it does |
|---|---|
| `benchmarks/cache_size_sweep.c` | Sequential `sum += arr[i]` over working sets from 4 KiB to 64 MiB (doubling), 20 passes each. Isolates capacity misses. |
| `benchmarks/assoc_conflict.c` | Round-robin over `FIXED_ASSOC + 4 = 8` lines spaced `L1_SIZE / FIXED_ASSOC` apart, so they share one L1 set. Gives a sharp threshold at 8-way. |

Experiments (24 runs) vary one level at a time while the others stay at baseline:

- **L1 size:** 16 / 32 / 64 / 128 KiB
- **L2 size:** 128 / 256 / 512 / 1024 KiB
- **L3 size:** 4 / 8 / 16 / 32 MiB
- **L1 associativity:** 1 / 2 / 4 / 8 / 16-way
- **L2 associativity:** 1 / 2 / 4 / 8 / 16-way
- **L3 associativity:** 1 / 2 / 4 / 8 / 16 / 32-way

## Run it

```bash
cd ~/Downloads/compArchProj

# 1. One time: Arm cross compiler (no sudo), gem5 ARM build (~1 h), benchmark binaries
bash scripts/build_gem5_arm.sh                 # gem5 checkout defaults to ~/gem5
python3 -m venv --without-pip .venv && python3 -m pip --python .venv/bin/python install matplotlib

# 2. Simulate all 24 configurations in parallel (a few minutes on 16 cores)
.venv/bin/python scripts/run_sweep.py          # --only size_l2_  /  --force  /  --gem5 PATH

# 3. Metrics, NCG and Pareto frontier -> results/rerun/{summary,ncg,pareto}.csv, tables.md
.venv/bin/python scripts/parse_ncg.py
.venv/bin/python scripts/parse_ncg.py --source original    # same analysis on the report's raw data

# 4. Figures -> results/rerun/figures, results/original/figures, results/comparison
.venv/bin/python scripts/plot_results.py
.venv/bin/python scripts/plot_results.py --source original
.venv/bin/python scripts/plot_results.py --compare
```

A single configuration by hand:

```bash
~/gem5/build/ARM/gem5.opt --outdir=m5out configs/three_level.py \
    --binary benchmarks/bin/cache_size_sweep --l2-size 512KiB --l1-assoc 8
```

## Layout

```
report/       submitted report (PDF)
original/     the team's original gem5 stats.txt dumps + file-to-experiment map
benchmarks/   cache_size_sweep.c, assoc_conflict.c, Makefile (static AArch64)
configs/      three_level.py - gem5 system: TimingSimpleCPU, L1I/L1D, L2, L3, DDR4
scripts/      experiments.py (the 24 runs), run_sweep.py, parse_ncg.py, plot_results.py, build_gem5_arm.sh
results/      runs/<name>/ raw gem5 output of the re-run; rerun/, original/, comparison/ tables and figures
docs/         RESULTS.md - re-run vs. report
```
