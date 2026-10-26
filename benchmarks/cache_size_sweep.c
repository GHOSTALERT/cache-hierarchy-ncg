/*
 * cache_size_sweep.c - sequential-read benchmark for capacity-miss analysis.
 *
 * Sweeps working-set sizes from 4 KiB to 64 MiB (doubling each step). For each
 * size the array is initialised once and then read sequentially ITERS times
 * (sum += arr[i]). The loop body is a pure streaming read, so changes in IPC
 * between cache configurations come from capacity misses and spatial locality,
 * not from program logic. gem5 stops the run after a fixed instruction count,
 * so every configuration executes exactly the same instructions.
 */
#include <stdio.h>
#include <stdlib.h>

#define MIN_BYTES (4UL * 1024)
#define MAX_BYTES (64UL * 1024 * 1024)
#define ITERS     20

static volatile long sink; /* keeps the compiler from removing the reads */

int main(void)
{
    int *arr = malloc(MAX_BYTES);
    if (!arr) {
        perror("malloc");
        return 1;
    }

    for (size_t bytes = MIN_BYTES; bytes <= MAX_BYTES; bytes *= 2) {
        size_t n = bytes / sizeof(int);
        for (size_t i = 0; i < n; i++)
            arr[i] = (int)i;

        long sum = 0;
        for (int it = 0; it < ITERS; it++)
            for (size_t i = 0; i < n; i++)
                sum += arr[i];
        sink = sum;
        printf("%8zu KiB  sum=%ld\n", bytes / 1024, sum);
    }

    free(arr);
    return 0;
}
