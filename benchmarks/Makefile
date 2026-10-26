# Static AArch64 binaries for gem5 SE mode.
# Uses the Arm GNU toolchain in ../.tools/aarch64 (scripts/build_gem5_arm.sh fetches it),
# else the distro cross compiler (sudo apt install gcc-aarch64-linux-gnu).
LOCAL_CC := $(abspath ../.tools/aarch64/bin/aarch64-none-linux-gnu-gcc)
CC      := $(if $(wildcard $(LOCAL_CC)),$(LOCAL_CC),aarch64-linux-gnu-gcc)
CFLAGS  ?= -O1 -static -Wall -Wextra
BINS    := bin/cache_size_sweep bin/assoc_conflict

all: $(BINS)

bin/%: %.c
	@mkdir -p bin
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -rf bin

.PHONY: all clean
