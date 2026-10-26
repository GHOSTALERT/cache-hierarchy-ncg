"""The 24 experiments of the study and the original stats file for each.

Size sweep (cache_size_sweep): one level varied at a time, others at baseline.
Associativity sweep (assoc_conflict): one level's associativity varied at a time.
"""
from dataclasses import dataclass, field

BASE_SIZE = {"l1": 32, "l2": 256, "l3": 8192}  # KiB
BASE_ASSOC = {"l1": 2, "l2": 8, "l3": 16}

SIZE_SWEEP = {"l1": [16, 32, 64, 128], "l2": [128, 256, 512, 1024], "l3": [4096, 8192, 16384, 32768]}
ASSOC_SWEEP = {"l1": [1, 2, 4, 8, 16], "l2": [1, 2, 4, 8, 16], "l3": [1, 2, 4, 8, 16, 32]}


@dataclass
class Experiment:
    name: str
    sweep: str            # "size" or "assoc"
    level: str | None     # level being varied (None for the baseline)
    size: dict = field(default_factory=lambda: dict(BASE_SIZE))
    assoc: dict = field(default_factory=lambda: dict(BASE_ASSOC))
    original: str | None = None  # file in original/stats/

    @property
    def binary(self):
        return "cache_size_sweep" if self.sweep == "size" else "assoc_conflict"

    @property
    def total_kb(self):
        return sum(self.size.values())

    def gem5_args(self):
        def fmt(kb):
            return f"{kb // 1024}MiB" if kb % 1024 == 0 else f"{kb}KiB"
        out = []
        for lvl in ("l1", "l2", "l3"):
            out += [f"--{lvl}-size", fmt(self.size[lvl]), f"--{lvl}-assoc", str(self.assoc[lvl])]
        return out


def _fmt_kb(kb):
    return f"{kb // 1024}m" if kb >= 1024 else f"{kb}k"


ORIGINAL_SIZE = {
    None: "L1-32kb-EXP1.txt",
    ("l1", 16): "L1-16kb-EXP2.txt", ("l1", 64): "l1-64kb-EXP3.txt", ("l1", 128): "l1-128kb-EXP4.txt",
    ("l2", 128): "l2-128KB-EXP5.txt", ("l2", 512): "l2-512KB-EXP6.txt", ("l2", 1024): "l2-1MB-EXP7.txt",
    ("l3", 4096): "l3-4MB-EXP8.txt", ("l3", 16384): "l3-16MB-EXP9.txt", ("l3", 32768): "l3-32MB-EXP10.txt",
}
ORIGINAL_ASSOC = {
    None: "SA-BASE-EXP1L1-2L2-8L3-16.txt",
    ("l1", 1): "SA-EXP2L1-1.txt", ("l1", 4): "SA-EXP3L1-4.txt",
    ("l1", 8): "SA-EXP4L1-8.txt", ("l1", 16): "SA-EXP5L1-16.txt",
    ("l2", 1): "SA-EXP6-L2-1.txt", ("l2", 2): "SA-EXP6-L2-2.txt",
    ("l2", 4): "SA-EXP8-L2-4.txt", ("l2", 16): "SA-EXP9-L2-16.txt",
    ("l3", 1): "SA-EXP10-L3-1.txt", ("l3", 2): "SA-EXP11-L3-2.txt", ("l3", 4): "SA-EXP12-L3-4.txt",
    ("l3", 8): "SA-EXP13-L3-8.txt", ("l3", 32): "SA-EXP14-L3-32.txt",
}


def all_experiments():
    exps = [Experiment("size_base", "size", None, original=ORIGINAL_SIZE[None])]
    for lvl, values in SIZE_SWEEP.items():
        for kb in values:
            if kb != BASE_SIZE[lvl]:
                e = Experiment(f"size_{lvl}_{_fmt_kb(kb)}", "size", lvl, original=ORIGINAL_SIZE[(lvl, kb)])
                e.size[lvl] = kb
                exps.append(e)
    exps.append(Experiment("assoc_base", "assoc", None, original=ORIGINAL_ASSOC[None]))
    for lvl, values in ASSOC_SWEEP.items():
        for ways in values:
            if ways != BASE_ASSOC[lvl]:
                e = Experiment(f"assoc_{lvl}_{ways}way", "assoc", lvl, original=ORIGINAL_ASSOC[(lvl, ways)])
                e.assoc[lvl] = ways
                exps.append(e)
    return exps
