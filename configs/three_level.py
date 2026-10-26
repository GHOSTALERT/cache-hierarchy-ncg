"""gem5 SE-mode system with a three-level cache hierarchy (ARM, TimingSimpleCPU).

    gem5.opt configs/three_level.py --binary benchmarks/bin/cache_size_sweep \
        --l1-size 32KiB --l2-size 256KiB --l3-size 8MiB

Baseline (report Table 1): 1 GHz TimingSimpleCPU, DDR4-2400 (8x8), 512 MiB,
L1I/L1D 32 KiB 2-way (2/2 cycles, 4 MSHRs), L2 256 KiB 8-way (10/10, 16),
L3 8 MiB 16-way (20/20, 32). The run stops after --max-insts instructions.
"""
import argparse

import m5
from m5.objects import *

p = argparse.ArgumentParser()
p.add_argument("--binary", required=True)
p.add_argument("--l1-size", default="32KiB")
p.add_argument("--l2-size", default="256KiB")
p.add_argument("--l3-size", default="8MiB")
p.add_argument("--l1-assoc", type=int, default=2)
p.add_argument("--l2-assoc", type=int, default=8)
p.add_argument("--l3-assoc", type=int, default=16)
p.add_argument("--max-insts", type=int, default=50_000_000)
args = p.parse_args()


def cache(size, assoc, latency, mshrs, tgts):
    return Cache(
        size=size,
        assoc=assoc,
        tag_latency=latency,
        data_latency=latency,
        response_latency=latency,
        mshrs=mshrs,
        tgts_per_mshr=tgts,
    )


system = System()
system.clk_domain = SrcClockDomain(clock="1GHz", voltage_domain=VoltageDomain())
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]

system.cpu = ArmTimingSimpleCPU()
system.cpu.max_insts_any_thread = args.max_insts

# L1 instruction and data caches (the "L1" sweep changes both together)
system.cpu.icache = cache(args.l1_size, args.l1_assoc, 2, 4, 20)
system.cpu.dcache = cache(args.l1_size, args.l1_assoc, 2, 4, 20)
system.cpu.icache.cpu_side = system.cpu.icache_port
system.cpu.dcache.cpu_side = system.cpu.dcache_port

system.l2bus = L2XBar()
system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports

system.l2 = cache(args.l2_size, args.l2_assoc, 10, 16, 12)
system.l2.cpu_side = system.l2bus.mem_side_ports

system.l3bus = L2XBar()
system.l2.mem_side = system.l3bus.cpu_side_ports

system.l3 = cache(args.l3_size, args.l3_assoc, 20, 32, 12)
system.l3.cpu_side = system.l3bus.mem_side_ports

system.membus = SystemXBar()
system.l3.mem_side = system.membus.cpu_side_ports

system.cpu.createInterruptController()
system.system_port = system.membus.cpu_side_ports

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR4_2400_8x8(range=system.mem_ranges[0])
system.mem_ctrl.port = system.membus.mem_side_ports

system.workload = SEWorkload.init_compatible(args.binary)
system.cpu.workload = Process(cmd=[args.binary])
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
