/*
 * assoc_conflict.c - conflict-miss stress test for set associativity.
 *
 * Touches N_LINES = FIXED_ASSOC + 4 = 8 cache lines spaced STRIDE bytes apart,
 * round-robin, over and over. With STRIDE = L1_SIZE / FIXED_ASSOC every line
 * lands in the same L1 set once the cache is 4-way or wider (and in at most
 * four sets below that), so:
 *
 *   assoc < 8  -> the set cannot hold all 8 lines; with LRU every access
 *                 evicts the line that is needed next (conflict misses)
 *   assoc >= 8 -> all 8 lines fit and conflict misses disappear
 *
 * This gives a sharp, controllable threshold at 8-way.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FIXED_ASSOC 4
#define N_LINES     (FIXED_ASSOC + 4)        /* = 8 conflicting lines */
#define L1_SIZE     (32 * 1024)              /* baseline L1D size     */
#define LINE        64
#define STRIDE      (L1_SIZE / FIXED_ASSOC)  /* 8 KiB                 */
#define ROUNDS      100000000L               /* far more than gem5 runs */

static volatile long sink;

int main(void)
{
    /* Line-aligned so every line maps to a predictable set. */
    char *buf = aligned_alloc(L1_SIZE, (size_t)N_LINES * STRIDE);
    if (!buf) {
        perror("aligned_alloc");
        return 1;
    }
    /* Caches are physically indexed and gem5 SE mode hands out physical pages
     * in first-touch order. Touching the whole buffer front to back keeps the
     * physical layout contiguous, so the 8 lines really share one set. */
    memset(buf, 0, (size_t)N_LINES * STRIDE);
    for (int k = 0; k < N_LINES; k++)
        for (int b = 0; b < LINE; b += sizeof(long))
            *(long *)(buf + (size_t)k * STRIDE + b) = k + b;

    long sum = 0;
    for (long r = 0; r < ROUNDS; r++)
        for (int k = 0; k < N_LINES; k++)
            sum += *(volatile long *)(buf + (size_t)k * STRIDE);
    sink = sum;
    printf("sum=%ld\n", sum);

    free(buf);
    return 0;
}
