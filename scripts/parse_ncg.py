"""Parse gem5 stats, compute Normalized Cache Gain (NCG) and the Pareto frontier.

    python scripts/parse_ncg.py                    # rerun data: results/runs/*
    python scripts/parse_ncg.py --source original  # the team's original stats dumps

    NCG = dIPC / dCacheSize   (IPC per KB, between consecutive sizes of one level)

Pareto frontier: size-sweep configurations that no other configuration beats on
both total cache area (L1+L2+L3, KB) and IPC. The knee is the frontier step
with the highest IPC gain per KB added.

Writes results/<source>/{summary.json,summary.csv,ncg.csv,pareto.csv,tables.md}.
"""
import argparse
import csv
import json
import re
from pathlib import Path

from experiments import all_experiments

ROOT = Path(__file__).resolve().parent.parent
LEVELS = {"l1": "system.cpu.dcache", "l2": "system.l2", "l3": "system.l3"}
_LINE = re.compile(r"^(\S+)\s+(-?[\d.]+(?:e[-+]?\d+)?|nan|inf)\s")


def read_stats(path):
    """First stats dump of a gem5 stats.txt as {name: float}."""
    stats = {}
    for line in Path(path).read_text().splitlines():
        if line.startswith("---------- End"):
            break
        m = _LINE.match(line)
        if m:
            stats[m.group(1)] = float(m.group(2))
    return stats


def metrics(stats):
    tick_per_cycle = stats.get("system.clk_domain.clock", 1000.0)
    out = {
        "insts": stats["simInsts"],
        "ipc": stats["system.cpu.ipc"],
        "cpi": stats["system.cpu.cpi"],
        "cycles": stats["system.cpu.numCycles"],
        "sim_seconds": stats["simSeconds"],
        "host_seconds": stats["hostSeconds"],
    }
    for lvl, prefix in LEVELS.items():
        lat = stats.get(f"{prefix}.overallAvgMissLatency::total")
        out[f"{lvl}_accesses"] = stats.get(f"{prefix}.overallAccesses::total", 0.0)
        out[f"{lvl}_misses"] = stats.get(f"{prefix}.overallMisses::total", 0.0)
        out[f"{lvl}_miss_rate"] = stats.get(f"{prefix}.overallMissRate::total", 0.0)
        # gem5 reports latency in ticks (1 ps); convert to CPU cycles.
        out[f"{lvl}_miss_latency_cycles"] = lat / tick_per_cycle if lat is not None else None
        out[f"{lvl}_replacements"] = stats.get(f"{prefix}.replacements", 0.0)
    return out


def load(source):
    rows = []
    for e in all_experiments():
        path = (ROOT / "original" / "stats" / e.original if source == "original"
                else ROOT / "results" / "runs" / e.name / "stats.txt")
        if not path.exists():
            print(f"  missing {path.relative_to(ROOT)}")
            continue
        rows.append({"name": e.name, "sweep": e.sweep, "level": e.level,
                     **{f"{k}_kb": v for k, v in e.size.items()},
                     **{f"{k}_assoc": v for k, v in e.assoc.items()},
                     "total_kb": e.total_kb, **metrics(read_stats(path))})
    return rows


def sweep_points(rows, sweep, level):
    """Rows of one sweep for one level (baseline included), ordered by the swept value."""
    key = f"{level}_kb" if sweep == "size" else f"{level}_assoc"
    pts = [r for r in rows if r["sweep"] == sweep and r["level"] in (None, level)]
    return sorted(pts, key=lambda r: r[key]), key


def ncg_table(rows):
    table = []
    for lvl in LEVELS:
        pts, key = sweep_points(rows, "size", lvl)
        steps = [(a, b, (b["ipc"] - a["ipc"]) / (b[key] - a[key])) for a, b in zip(pts, pts[1:])]
        peak = max((s[2] for s in steps), default=None)
        for a, b, ncg in steps:
            table.append({"level": lvl.upper(), "from_kb": a[key], "to_kb": b[key],
                          "d_cache_kb": b[key] - a[key], "d_ipc": b["ipc"] - a["ipc"],
                          "ncg_ipc_per_kb": ncg, "peak": peak > 0 and ncg == peak})
    return table


def pareto(rows):
    pts = [r for r in rows if r["sweep"] == "size"]
    frontier = [p for p in pts if not any(
        q["total_kb"] <= p["total_kb"] and q["ipc"] >= p["ipc"]
        and (q["total_kb"] < p["total_kb"] or q["ipc"] > p["ipc"]) for q in pts)]
    frontier.sort(key=lambda r: r["total_kb"])
    steps = []
    for prev, cur in zip([None] + frontier, frontier):
        eff = None if prev is None else (cur["ipc"] - prev["ipc"]) / (cur["total_kb"] - prev["total_kb"]) * 1000
        steps.append({"name": cur["name"], "total_kb": cur["total_kb"], "ipc": cur["ipc"],
                      "d_ipc": None if prev is None else cur["ipc"] - prev["ipc"],
                      "d_area_kb": None if prev is None else cur["total_kb"] - prev["total_kb"],
                      "ipc_per_1000kb": eff})
    effs = [s["ipc_per_1000kb"] for s in steps if s["ipc_per_1000kb"] is not None]
    knee = next((s for s in steps if effs and s["ipc_per_1000kb"] == max(effs)), None)
    on_front = {s["name"] for s in steps}
    points = [{"name": p["name"], "total_kb": p["total_kb"], "ipc": p["ipc"],
               "status": "knee" if knee and p["name"] == knee["name"]
               else "pareto-optimal" if p["name"] in on_front else "dominated"}
              for p in sorted(pts, key=lambda r: r["total_kb"])]
    summary = None
    if knee:
        summary = {"knee": knee["name"],
                   "pct_of_peak_ipc": 100 * knee["ipc"] / max(p["ipc"] for p in pts),
                   "pct_of_max_area": 100 * knee["total_kb"] / max(p["total_kb"] for p in pts)}
    return points, steps, summary


def write_csv(path, rows):
    if rows:
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


def tables_md(rows, ncg, points, steps, knee):
    md = ["| Experiment | IPC | CPI | L1D miss | L2 miss | L3 miss | L1D/L2/L3 miss lat. (cyc) | Sim. time (s) |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lat = "/".join("-" if r[f"{l}_miss_latency_cycles"] is None else f"{r[f'{l}_miss_latency_cycles']:.1f}"
                       for l in LEVELS)
        md.append(f"| {r['name']} | {r['ipc']:.6f} | {r['cpi']:.3f} | {100 * r['l1_miss_rate']:.2f}% | "
                  f"{100 * r['l2_miss_rate']:.2f}% | {100 * r['l3_miss_rate']:.2f}% | {lat} | {r['sim_seconds']:.6f} |")
    md += ["", "| Level | Transition (KB) | dIPC | NCG (IPC/KB) |", "|---|---|---|---|"]
    for n in ncg:
        md.append(f"| {n['level']} | {n['from_kb']} -> {n['to_kb']} | {n['d_ipc']:+.6f} | "
                  f"{n['ncg_ipc_per_kb']:.4e}{' (peak)' if n['peak'] else ''} |")
    md += ["", "| Config | Total area (KB) | IPC | Status |", "|---|---|---|---|"]
    md += [f"| {p['name']} | {p['total_kb']:,} | {p['ipc']:.6f} | {p['status']} |" for p in points]
    md += ["", "| Frontier step | Area (KB) | IPC | dIPC | dArea (KB) | IPC per 1000 KB |", "|---|---|---|---|---|---|"]
    for s in steps:
        md.append(f"| {s['name']} | {s['total_kb']:,} | {s['ipc']:.6f} | "
                  + (" - | - | - |" if s["d_ipc"] is None else
                     f"{s['d_ipc']:+.6f} | +{s['d_area_kb']:,} | {s['ipc_per_1000kb']:.6f} |"))
    if knee:
        md += ["", f"Knee: **{knee['knee']}**, {knee['pct_of_peak_ipc']:.1f}% of peak IPC "
                   f"at {knee['pct_of_max_area']:.1f}% of the largest tested cache area."]
    return "\n".join(md) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["rerun", "original"], default="rerun")
    args = ap.parse_args()

    rows = load(args.source)
    if not rows:
        raise SystemExit("no stats found")
    ncg = ncg_table(rows)
    points, steps, knee = pareto(rows)

    out = ROOT / "results" / args.source
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(
        {"runs": rows, "ncg": ncg, "pareto_points": points, "pareto_frontier": steps, "knee": knee}, indent=2))
    write_csv(out / "summary.csv", rows)
    write_csv(out / "ncg.csv", ncg)
    write_csv(out / "pareto.csv", points)
    md = tables_md(rows, ncg, points, steps, knee)
    (out / "tables.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
