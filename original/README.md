# Original gem5 output (submitted report)

Raw `stats.txt` dumps from the team's original runs. The report's tables were built from these files.
They were made with gem5 on ARM in SE mode, using a TimingSimpleCPU and 50M instructions per run.
`scripts/experiments.py` maps each file to its experiment, and
`python scripts/parse_ncg.py --source original` rebuilds the report's NCG and Pareto tables from them.
The results land in `results/original/`.

| File | Experiment |
|---|---|
| `L1-32kb-EXP1.txt` | size sweep baseline (L1 32 KiB, L2 256 KiB, L3 8 MiB) |
| `L1-16kb-EXP2.txt`, `l1-64kb-EXP3.txt`, `l1-128kb-EXP4.txt` | L1 size |
| `l2-128KB-EXP5.txt`, `l2-512KB-EXP6.txt`, `l2-1MB-EXP7.txt` | L2 size |
| `l3-4MB-EXP8.txt`, `l3-16MB-EXP9.txt`, `l3-32MB-EXP10.txt` | L3 size |
| `SA-BASE-EXP1L1-2L2-8L3-16.txt` | associativity baseline (L1 2-way, L2 8-way, L3 16-way) |
| `SA-EXP2L1-1.txt` … `SA-EXP5L1-16.txt` | L1 1/4/8/16-way |
| `SA-EXP6-L2-1.txt`, `SA-EXP6-L2-2.txt`, `SA-EXP8-L2-4.txt`, `SA-EXP9-L2-16.txt` | L2 1/2/4/16-way |
| `SA-EXP10-L3-1.txt` … `SA-EXP14-L3-32.txt` | L3 1/2/4/8/32-way |
| `summary_size_sweep.txt`, `summary_assoc_sweep.txt` | the team's hand-extracted metric summaries (the associativity summary labels ways as "KB") |

The benchmark C sources and gem5 config used for these runs were not kept. `benchmarks/` and `configs/` are rewritten from the report's description.
