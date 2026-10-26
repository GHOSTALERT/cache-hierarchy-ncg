# Re-run results vs. the submitted report

All 24 experiments were re-run with the scripted pipeline in this repo:
gem5 v25.1 ARM SE, TimingSimpleCPU @ 1 GHz, 50M instructions, the Table 1 cache baseline.
Full tables: [`results/rerun/tables.md`](../results/rerun/tables.md) (rerun) and [`results/original/tables.md`](../results/original/tables.md) (the team's original stats, put through the same parser).
Overlay figures are in [`results/comparison/`](../results/comparison/).

**Why absolute numbers differ.** The original benchmark sources were not kept, so `benchmarks/*.c` were rewritten from the report's description.
The original size-sweep binary was store-heavy: 8.4M stores to 4.1M loads in 50M instructions, and a 12.3% L1D miss rate.
That suggests most of its instructions went into initialising a large array.
The rewritten benchmark spends its instructions in the `sum += arr[i]` read loop the report describes.
That roughly doubles IPC (0.344 vs 0.166 at baseline).
The trends and the design conclusions are what to compare.

## Headline findings

| Finding (report) | Original data | Re-run | Reproduced? |
|---|---|---|---|
| L2 gives the best NCG of any level | L2 peak 1.1512e-5 IPC/KB (256→512 KB) | L2 peak 5.2855e-5 IPC/KB (256→512 KB) | Yes, same transition |
| L1 NCG is second, L3 is negligible | L1 4.97e-6, L3 ~5e-8 | L1 3.23e-5, L3 0 | Yes. The re-run's working set never outgrows the 4 MiB L3 within 50M instructions, so L3 size has no effect at all |
| Pareto knee = L1 32 KB / L2 512 KB / L3 8 MiB | 98.2% of peak IPC at 26.4% of max area | 93.7% of peak IPC at 26.4% of max area | Yes, same knee |
| L2 miss rate falls steeply with L2 size | 96.0% → 69.2% (128 KB → 1 MB) | 90.8% → 4.4% | Yes, stronger |
| "Miss latency paradox": L2 miss latency rises with L2 size | 100.2 → 122.4 cycles (+22%) | 45.6 → 96.0 cycles (+110%) | Yes |
| Sharp L1 threshold at 8-way | IPC 0.190 → 0.406, miss rate 87.3% → 0.02% | IPC 0.201 → 0.421, miss rate 99.8% → 0.02% | Yes |
| L1 replacements collapse at 8-way | 9.97M → 1,487 | 9.29M → 1,439 | Yes |
| L2/L3 associativity has no effect on this benchmark | identical IPC 0.190288 for all 9 runs | identical IPC 0.200961 for all 9 runs | Yes |
| 1-way L1 slightly faster than 2/4-way | 0.206 vs 0.190 | 0.201 vs 0.201 | No: the re-run benchmark keeps all 8 lines in one set at every associativity, so 1-way behaves like 2/4-way |

## Corrections to the submitted report

1. **Miss latency units.** gem5 reports latencies in ticks, and 1 tick = 1 ps.
   At 1 GHz, 1 cycle = 1000 ticks.
   Tables 5, 10 and 16 label tick values as cycles, so "90,190 → 112,370 cycles" is really about 90 → 112 cycles.
   The paradox itself still holds, because it is a relative trend.
   `parse_ncg.py` converts to cycles.
2. **Which latency stat.** Table 5's L2 values match `system.l2.overallAvgMshrMissLatency` (90,190 for L2 = 128 KB), not `overallAvgMissLatency` (100,2xx).
   The re-run reports `overallAvgMissLatency` for every level.
3. **Table 16 optimal column.** In `l2-512KB-EXP6.txt`, the L2 = 512 KB configuration has simulated time 0.295719 s (report: 0.296411 s) and CPI 5.914 (report: 5.915).
4. **Physical indexing in SE mode.** In gem5 SE mode, physical pages are handed out in first-touch order and caches are physically indexed.
   A conflict test whose lines sit on separate, untouched pages therefore lands on consecutive physical pages and spreads across sets.
   `assoc_conflict.c` touches its whole buffer in order first, so that the 8 lines really share one set.
   Without that, the re-run showed no threshold.
