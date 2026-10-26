"""Run every experiment through gem5 in parallel and keep each run's stats.

    python scripts/run_sweep.py                     # all 24 runs
    python scripts/run_sweep.py --only size_l2_     # name prefix filter
    python scripts/run_sweep.py --jobs 8 --force    # re-run existing results

Outputs results/runs/<name>/{stats.txt,config.ini,simout.txt}.
"""
import argparse
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from experiments import all_experiments

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "results" / "runs"
CONFIG = ROOT / "configs" / "three_level.py"
BIN = ROOT / "benchmarks" / "bin"
DEFAULT_GEM5 = Path.home() / "gem5" / "build" / "ARM" / "gem5.opt"


def run(exp, gem5, force):
    out = RUNS / exp.name
    if (out / "stats.txt").exists() and not force:
        return exp.name, "cached", 0.0
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    cmd = [str(gem5), f"--outdir={out}", str(CONFIG), "--binary", str(BIN / exp.binary), *exp.gem5_args()]
    t0 = time.time()
    with open(out / "simout.txt", "w") as log:
        log.write(" ".join(cmd) + "\n\n")
        log.flush()
        rc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT).returncode
    for junk in ("config.json", "citations.bib", "fs"):
        p = out / junk
        shutil.rmtree(p) if p.is_dir() else p.unlink(missing_ok=True)
    return exp.name, "ok" if rc == 0 else f"FAILED rc={rc}", time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gem5", type=Path, default=Path(os.environ.get("GEM5", DEFAULT_GEM5)))
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--only", default="", help="run only experiments whose name starts with this")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if not args.gem5.exists():
        raise SystemExit(f"gem5 not found at {args.gem5} (build it with scripts/build_gem5_arm.sh)")
    for b in ("cache_size_sweep", "assoc_conflict"):
        if not (BIN / b).exists():
            raise SystemExit(f"missing {BIN / b}: run `make -C benchmarks`")

    exps = [e for e in all_experiments() if e.name.startswith(args.only)]
    print(f"{len(exps)} experiments, {args.jobs} parallel gem5 processes")
    failed = 0
    with ThreadPoolExecutor(args.jobs) as pool:
        for name, status, secs in pool.map(lambda e: run(e, args.gem5, args.force), exps):
            print(f"  {name:22s} {status:10s} {secs:6.1f}s", flush=True)
            failed += status.startswith("FAILED")
    if failed:
        raise SystemExit(f"{failed} run(s) failed; see results/runs/<name>/simout.txt")


if __name__ == "__main__":
    main()
