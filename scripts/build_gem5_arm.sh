#!/usr/bin/env bash
# Build gem5 (ARM ISA) and the AArch64 benchmark binaries. No sudo needed for the
# cross compiler: Arm's prebuilt GNU toolchain is fetched into .tools/aarch64.
#   bash scripts/build_gem5_arm.sh [path-to-gem5-checkout]   (default ~/gem5)
# gem5's own build dependencies (Ubuntu/Debian, one time):
#   sudo apt install build-essential scons python3-dev m4 zlib1g-dev \
#        libprotobuf-dev protobuf-compiler libgoogle-perftools-dev
set -euo pipefail
GEM5=${1:-$HOME/gem5}
HERE=$(cd "$(dirname "$0")/.." && pwd)
TC=arm-gnu-toolchain-14.2.rel1-x86_64-aarch64-none-linux-gnu
TC_URL=https://developer.arm.com/-/media/Files/downloads/gnu/14.2.rel1/binrel/$TC.tar.xz
TC_SHA=47aeefc02b0ee39f6d4d1812110952975542d365872a7474b5306924bca4faa1

if [ ! -x "$HERE/.tools/aarch64/bin/aarch64-none-linux-gnu-gcc" ]; then
    mkdir -p "$HERE/.tools"
    curl -fL -o "$HERE/.tools/$TC.tar.xz" "$TC_URL"
    echo "$TC_SHA  $HERE/.tools/$TC.tar.xz" | sha256sum -c -
    tar -xf "$HERE/.tools/$TC.tar.xz" -C "$HERE/.tools"
    mv "$HERE/.tools/$TC" "$HERE/.tools/aarch64"
    rm "$HERE/.tools/$TC.tar.xz"
fi

if [ ! -d "$GEM5" ]; then
    git clone --depth 1 --branch v25.1.0.0 https://github.com/gem5/gem5.git "$GEM5"
fi
(cd "$GEM5" && scons build/ARM/gem5.opt -j"$(nproc)")
make -C "$HERE/benchmarks"
echo "gem5: $GEM5/build/ARM/gem5.opt"
