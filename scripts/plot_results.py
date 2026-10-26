"""Draw the report figures from results/<source>/summary.json.

    python scripts/plot_results.py                      # rerun data
    python scripts/plot_results.py --source original
    python scripts/plot_results.py --compare            # original vs rerun overlays

Figures go to results/<source>/figures/ (or results/comparison/ with --compare).
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import ScalarFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LEVELS = ("l1", "l2", "l3")

# (key, label, scale) - per-level metrics read from the level being swept
METRICS = [
    ("ipc", "IPC", 1),
    ("cpi", "CPI", 1),
    ("{lvl}_miss_rate", "Miss rate (%)", 100),
    ("{lvl}_miss_latency_cycles", "Avg. miss latency (cycles)", 1),
    ("sim_seconds", "Simulated time (s)", 1),
    ("cycles", "Simulated cycles", 1),
    ("{lvl}_replacements", "Replacements", 1),
    ("host_seconds", "Host time (s)", 1),
]


def load(source):
    return json.loads((ROOT / "results" / source / "summary.json").read_text())


def series(runs, sweep, lvl, key, scale):
    xkey = f"{lvl}_kb" if sweep == "size" else f"{lvl}_assoc"
    pts = sorted((r[xkey], r[key.format(lvl=lvl)]) for r in runs
                 if r["sweep"] == sweep and r["level"] in (None, lvl) and r[key.format(lvl=lvl)] is not None)
    return [x for x, _ in pts], [y * scale for _, y in pts]


def sweep_figure(datasets, sweep, key, label, scale, path):
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
    for ax, lvl in zip(axes, LEVELS):
        for name, runs, style in datasets:
            xs, ys = series(runs, sweep, lvl, key, scale)
            ax.plot(xs, ys, style, label=name, markersize=5)
        ax.set_xscale("log", base=2)
        ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.set_xlabel(f"{lvl.upper()} {'size (KB)' if sweep == 'size' else 'associativity (ways)'}")
        ax.set_title(f"{lvl.upper()}: {label}")
        ax.grid(alpha=0.3)
        ax.ticklabel_format(axis="y", useOffset=False, style="plain")
    axes[0].set_ylabel(label)
    if len(datasets) > 1:
        axes[0].legend()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def ncg_figure(datasets, path):
    fig, ax = plt.subplots(figsize=(8, 4))
    width = 0.8 / len(datasets)
    for i, (name, data, _) in enumerate(datasets):
        labels = [f"{n['level']} {n['from_kb']}->{n['to_kb']}" for n in data["ncg"]]
        ax.bar([j + i * width for j in range(len(labels))], [n["ncg_ipc_per_kb"] for n in data["ncg"]],
               width, label=name)
    ax.set_xticks([j + width * (len(datasets) - 1) / 2 for j in range(len(labels))], labels, rotation=40, ha="right")
    ax.set_yscale("symlog", linthresh=1e-8)
    ax.set_ylabel("NCG (IPC per KB)")
    ax.set_title("Normalized Cache Gain per transition")
    ax.grid(alpha=0.3, axis="y")
    if len(datasets) > 1:
        ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def pareto_figure(datasets, path):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for name, data, style in datasets:
        pts = data["pareto_points"]
        front = data["pareto_frontier"]
        color = ax.plot([f["total_kb"] for f in front], [f["ipc"] for f in front], style,
                        label=f"{name} frontier")[0].get_color()
        dom = [p for p in pts if p["status"] == "dominated"]
        ax.scatter([p["total_kb"] for p in dom], [p["ipc"] for p in dom], marker="x", color=color)
        for p in pts:
            ax.annotate(p["name"].replace("size_", ""), (p["total_kb"], p["ipc"]), fontsize=7,
                        xytext=(3, 3), textcoords="offset points")
        if data["knee"]:
            k = next(p for p in pts if p["name"] == data["knee"]["knee"])
            ax.scatter([k["total_kb"]], [k["ipc"]], s=160, facecolors="none", edgecolors=color, linewidths=2)
    ax.set_xscale("log", base=2)
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.set_xlabel("Total cache area L1+L2+L3 (KB)")
    ax.set_ylabel("IPC")
    ax.set_title("IPC vs total cache area: Pareto frontier (circle = knee, x = dominated)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["rerun", "original"], default="rerun")
    ap.add_argument("--compare", action="store_true")
    args = ap.parse_args()

    if args.compare:
        datasets = [("original", load("original"), "o--"), ("rerun", load("rerun"), "s-")]
        out = ROOT / "results" / "comparison"
    else:
        datasets = [(args.source, load(args.source), "o-")]
        out = ROOT / "results" / args.source / "figures"
    out.mkdir(parents=True, exist_ok=True)

    plotted = [(n, d["runs"], s) for n, d, s in datasets]
    for sweep in ("size", "assoc"):
        for key, label, scale in METRICS:
            slug = key.replace("{lvl}_", "").replace("_cycles", "")
            sweep_figure(plotted, sweep, key, label, scale, out / f"{sweep}_{slug}.png")
    ncg_figure(datasets, out / "ncg.png")
    pareto_figure(datasets, out / "pareto.png")
    print(f"figures written to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
