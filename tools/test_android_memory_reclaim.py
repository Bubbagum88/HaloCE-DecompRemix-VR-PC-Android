"""Exercise the Build 176 pagemap-denied fallback with real host mappings."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "port/android/host/host_memory.c").read_text()
start = source.index("enum\n{\n\t_range_unused")
end = source.index("\nstatic int reclaim_art_overlap", start)
helpers = source[start:end]
assert "PAGEMAP_DISABLED ? -1" in helpers
assert "range_usage_mincore(mapping_start, from, to, usage)" in helpers
assert "usage_result != _range_unused" in source

code = r'''#define _GNU_SOURCE
#define HALO_MEMORY_RECLAIM_TEST
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#define PAGE 0x1000ULL
#define HOST_LOG_WARN 1
#define HOST_LOG_ERROR 2
static uint64_t test_resident_address, test_failed_address;
static int test_mincore(void *address, size_t length, unsigned char *residency) {
    uint64_t first = (uint64_t)address;
    size_t pages = length / PAGE, index;
    if (first == test_failed_address) { errno = ENOMEM; return -1; }
    for (index = 0; index < pages; index++)
        residency[index] = first + index * PAGE == test_resident_address ? 1 : 0;
    return 0;
}
#define mincore test_mincore
static void host_logf(int level, const char *format, ...) { (void)level; (void)format; }
''' + helpers + r'''
int main(void) {
    const size_t size = 4 * PAGE;
    unsigned char *memory = mmap(NULL, size, PROT_READ | PROT_WRITE,
        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    struct range_usage usage;
    assert(memory != MAP_FAILED);
    assert(madvise(memory, size, MADV_DONTNEED) == 0);

    /* Untouched ART-like pages are identified as unused via mincore/smaps. */
    int result = range_usage((uint64_t)memory, (uint64_t)memory,
        (uint64_t)memory + size, &usage);
    assert(result == _range_unused);
    assert(strcmp(usage.method, "mincore/smaps") == 0);

    /* A resident page must be retained even when pagemap is unavailable. */
    memory[PAGE + 8] = 0x5a;
    test_resident_address = (uint64_t)memory + PAGE;
    assert(range_usage((uint64_t)memory, (uint64_t)memory + PAGE,
        (uint64_t)memory + 2 * PAGE, &usage) == _range_in_use);
    assert(usage.pages_in_use > 0);

    /* An uninspectable/unmapped range is UNKNOWN, never eligible to reclaim. */
    assert(munmap(memory, size) == 0);
    test_failed_address = (uint64_t)memory;
    assert(range_usage((uint64_t)memory, (uint64_t)memory,
        (uint64_t)memory + PAGE, &usage) == _range_unknown);
    return 0;
}
'''

with tempfile.TemporaryDirectory() as directory:
    c_file = Path(directory) / "memory_reclaim.c"
    exe = Path(directory) / "memory_reclaim"
    c_file.write_text(code)
    subprocess.run(["clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-fsanitize=address,undefined", str(c_file), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)

print("Android ART reclaim fallback retains resident and unknown ranges (ASan/UBSan)")
