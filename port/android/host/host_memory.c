/*
HOST_MEMORY.C

Guest address space for the Android port.

Everything the guest touches must lie below 4 GB, but an Android process
shares that range with ART, whose heap spaces use compressed 32-bit
references and so also live there. The host therefore claims only what the
guest needs, when it needs it:

- the Xbox contiguous window at 0x80000000 and the image's own range, at
  start-up (both at fixed addresses the guest was built for);
- pools of address space for the guest's other mappings (malloc arenas,
  thread stacks), reserved in free gaps below 4 GB as they fill up.

This file also implements guest memory write tracking (the interface of
port/linux/src/memory_watch.c): the renderer tracks writes to pages behind
cached textures. Most Android processes use page protection and this
SIGSEGV handler records writes; an ARM-translated guest uses page hashes
(host_watch_hash.c). Other faults are reported and passed to the previous
handler.
*/

#include "host.h"
#include "host_watch_hash.h"

#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <ucontext.h>
#include <unistd.h>

#ifndef MAP_FIXED_NOREPLACE
#define MAP_FIXED_NOREPLACE 0x100000
#endif

#define PAGE 0x1000ULL
#define LOW_LIMIT 0x100000000ULL
#define LOW_START 0x01000000ULL
#define POOL_SIZE (256ULL * 1024 * 1024)
#define POOL_PAGES (POOL_SIZE / PAGE)
#define MAXIMUM_POOLS 12

struct pool
{
	uint64_t base;
	uint32_t free_pages;
	uint8_t used[POOL_PAGES]; /* 1 for each page handed out */
};

static struct pool *pools[MAXIMUM_POOLS];
static int pool_count;
static pthread_mutex_t memory_lock = PTHREAD_MUTEX_INITIALIZER;

static uint64_t window_base, window_end;
static uint64_t image_base, image_end;
/* what stopped host_memory_initialize, for the player (host_main.c) */
const char *host_memory_failure;

/* the window Halo Custom Edition tag data are linked to, with room for
OpenSauce's memory upgrades (port/linux/game/cache_file_formats.h,
CUSTOM_EDITION_TAG_CACHE_ADDRESS and _BYTES_UPGRADED), held for the guest
from start-up so nothing else takes it before the game.custom_edition
setting has the guest map it (port/linux/src/xbox_memory.c); address space
only, until then */
#define CUSTOM_EDITION_WINDOW_BASE 0x40440000ULL
#define CUSTOM_EDITION_WINDOW_SIZE 0x02280000ULL
static uint64_t custom_edition_base, custom_edition_end;

static uint64_t round_up(uint64_t value)
{
	return (value + PAGE - 1) & ~(PAGE - 1);
}

static int in_range(uint64_t address, uint64_t size, uint64_t base, uint64_t end)
{
	return address >= base && address + size <= end && address + size >= address;
}

/* ---------- reserving address space below 4 GB */

/* the lowest free gap of at least size bytes at or above minimum, from
/proc/self/maps; 0 if none */
static uint64_t find_gap(uint64_t size, uint64_t minimum)
{
	FILE *maps = fopen("/proc/self/maps", "r");
	char line[512];
	uint64_t previous_end = minimum;
	uint64_t result = 0;

	if (!maps)
		return 0;
	while (fgets(line, sizeof(line), maps))
	{
		unsigned long long start, end;

		if (sscanf(line, "%llx-%llx", &start, &end) != 2)
			continue;
		if (end <= previous_end)
			continue;
		if (start > previous_end && start - previous_end >= size)
			break;
		previous_end = end > previous_end ? end : previous_end;
		if (previous_end >= LOW_LIMIT)
			break;
	}
	fclose(maps);
	previous_end = round_up(previous_end);
	if (previous_end + size <= LOW_LIMIT)
		result = previous_end;
	return result;
}

/* ART reserves its spaces (notably the free-list large object space) at
addresses chosen at zygote start; on some devices (for example the Retroid
Pocket Flip2, kernel 4.19) that reservation covers the fixed Xbox memory
window. That space commits pages lazily from its bottom, and the Java side
of this app hardly allocates large objects, so the slice over the window is
normally idle address space: unmap exactly the intersection (never more)
and let the caller retry. Only that space, and only a slice with no page in
use (present or swapped out, from /proc/self/pagemap): ART's other spaces
(its heap, bitmaps and card tables) are live, and unmapping them would
corrupt it where failing to start is at least clear. */
#define ART_LARGE_OBJECT_SPACE "[anon:dalvik-free list large object space]"

enum
{
	_range_unused,
	_range_in_use,
	_range_unknown,
};

#ifdef HALO_MEMORY_RECLAIM_TEST
/* Host-only tests force the same path as devices that deny pagemap access. */
int host_memory_reclaim_test_no_pagemap = 1;
int host_memory_reclaim_test_swap_kb = 0;
#define PAGEMAP_DISABLED host_memory_reclaim_test_no_pagemap
#else
#define PAGEMAP_DISABLED 0
#endif

struct range_usage
{
	uint64_t pages_in_use;
	uint64_t lowest_in_use, highest_in_use;
	const char *method;
};

static void range_note_in_use(struct range_usage *usage, uint64_t address)
{
	if (!usage->pages_in_use++)
		usage->lowest_in_use = address;
	usage->highest_in_use = address;
}

/* /proc/self/pagemap: bit 63 is present and bit 62 is swapped out. UNKNOWN
 * means the kernel or policy did not allow a complete read, so mincore and
 * smaps can be tried without treating an unreadable page as free. */
static int range_usage_pagemap(uint64_t from, uint64_t to, struct range_usage *usage)
{
	int descriptor = PAGEMAP_DISABLED ? -1 : open("/proc/self/pagemap", O_RDONLY | O_CLOEXEC);
	uint64_t entries[512];
	uint64_t page = from / PAGE;

	if (descriptor < 0)
	{
		if (PAGEMAP_DISABLED)
			errno = EACCES;
		host_logf(HOST_LOG_WARN, "ART memory check: cannot read /proc/self/pagemap (%s); trying mincore/smaps",
			strerror(errno));
		return _range_unknown;
	}
	usage->method = "pagemap";
	while (page < to / PAGE)
	{
		size_t wanted = (size_t)(to / PAGE - page);
		ssize_t bytes;
		size_t count, index;

		if (wanted > sizeof(entries) / sizeof(entries[0]))
			wanted = sizeof(entries) / sizeof(entries[0]);
		bytes = pread(descriptor, entries, wanted * sizeof(entries[0]), (off_t)(page * sizeof(entries[0])));
		if (bytes <= 0 || bytes % (ssize_t)sizeof(entries[0]))
		{
			int error = errno;
			close(descriptor);
			host_logf(HOST_LOG_WARN, "ART memory check: incomplete pagemap read at %08llx (%s); trying mincore/smaps",
				(unsigned long long)(page * PAGE), bytes == 0 ? "end of file" : strerror(error));
			return _range_unknown;
		}
		count = (size_t)bytes / sizeof(entries[0]);
		for (index = 0; index < count; index++)
		{
			if (entries[index] & (3ULL << 62))
				range_note_in_use(usage, (page + index) * PAGE);
		}
		page += count;
	}
	close(descriptor);
	return usage->pages_in_use ? _range_in_use : _range_unused;
}

/* The Swap: value from the smaps entry beginning at start, in kB. When end
 * is nonzero the entry must end there too. dont_dump reports MADV_DONTDUMP. */
static long mapping_swap_kb_ending(uint64_t start, uint64_t end, int *dont_dump)
{
	FILE *smaps = fopen("/proc/self/smaps", "r");
	char line[512];
	int inside = 0;
	long result = -1;

	if (dont_dump)
		*dont_dump = 0;
	if (!smaps)
		return -1;
	while (fgets(line, sizeof(line), smaps))
	{
		unsigned long long lo, hi;
		long kb;

		if (sscanf(line, "%llx-%llx ", &lo, &hi) == 2)
		{
			if (inside)
				break;
			inside = lo == start && (!end || hi == end);
			continue;
		}
		if (!inside)
			continue;
		if (sscanf(line, "Swap: %ld kB", &kb) == 1)
			result = kb;
		else if (dont_dump && !strncmp(line, "VmFlags:", 8))
			*dont_dump = strstr(line, " dd") != NULL;
	}
	fclose(smaps);
	return result;
}

static long mapping_swap_kb(uint64_t start)
{
#ifdef HALO_MEMORY_RECLAIM_TEST
	(void)start;
	return host_memory_reclaim_test_swap_kb;
#else
	return mapping_swap_kb_ending(start, 0, NULL);
#endif
}

/* smaps counts swap per mapping, not per range. Split only this page-aligned
 * range temporarily to read its Swap count; do not alter an ART mapping
 * already marked DONTDUMP. */
static long range_swap_kb(uint64_t mapping_start, uint64_t from, uint64_t to)
{
	int dont_dump;
	long kb;
	long mapping_swap = mapping_swap_kb_ending(mapping_start, 0, &dont_dump);

	if (mapping_swap < 0)
	{
		host_logf(HOST_LOG_WARN, "ART memory check: cannot inspect mapping %08llx in smaps; range remains mapped",
			(unsigned long long)mapping_start);
		return -1;
	}
	if (dont_dump)
	{
		host_logf(HOST_LOG_WARN, "ART memory check: mapping %08llx already has DONTDUMP; exact swap state is unknown",
			(unsigned long long)mapping_start);
		return -1;
	}
	if (madvise((void *)from, (size_t)(to - from), MADV_DONTDUMP) != 0)
	{
		host_logf(HOST_LOG_WARN, "ART memory check: cannot isolate swap for %08llx-%08llx (%s); range remains mapped",
			(unsigned long long)from, (unsigned long long)to, strerror(errno));
		return -1;
	}
	kb = mapping_swap_kb_ending(from, to, NULL);
	if (madvise((void *)from, (size_t)(to - from), MADV_DODUMP) != 0)
	{
		host_logf(HOST_LOG_ERROR, "ART memory check: could not restore dump flag for %08llx-%08llx (%s); range remains mapped",
			(unsigned long long)from, (unsigned long long)to, strerror(errno));
		return -1;
	}
	if (kb < 0)
		host_logf(HOST_LOG_WARN, "ART memory check: isolated range %08llx-%08llx has no readable smaps entry",
			(unsigned long long)from, (unsigned long long)to);
	return kb;
}

/* Fallback for kernels or policies that refuse pagemap. mincore reports
 * resident pages; smaps supplies the range's own swapped-page count. */
static int range_usage_mincore(uint64_t mapping_start, uint64_t from, uint64_t to,
	struct range_usage *usage)
{
	unsigned char residency[4096];
	uint64_t address = from;
	long swapped = mapping_swap_kb(mapping_start);

	usage->method = "mincore/smaps";
	if (swapped < 0)
	{
		host_logf(HOST_LOG_WARN, "ART memory check: cannot read smaps for mapping %08llx; range remains mapped",
			(unsigned long long)mapping_start);
		return _range_unknown;
	}
	if (swapped > 0)
	{
		long range_swapped = range_swap_kb(mapping_start, from, to);

		if (range_swapped < 0)
			return _range_unknown;
		if (range_swapped > 0)
		{
			usage->pages_in_use = ((uint64_t)range_swapped * 1024 + PAGE - 1) / PAGE;
			usage->lowest_in_use = from;
			usage->highest_in_use = to - PAGE;
			usage->method = "range swap in smaps";
			return _range_in_use;
		}
	}
	while (address < to)
	{
		uint64_t length = to - address;
		size_t index;

		if (length > sizeof(residency) * PAGE)
			length = sizeof(residency) * PAGE;
		if (mincore((void *)address, (size_t)length, residency) != 0)
		{
			host_logf(HOST_LOG_WARN, "ART memory check: mincore failed at %08llx (%s); range remains mapped",
				(unsigned long long)address, strerror(errno));
			return _range_unknown;
		}
		for (index = 0; index < length / PAGE; index++)
		{
			if (residency[index] & 1)
				range_note_in_use(usage, address + index * PAGE);
		}
		address += length;
	}
	return usage->pages_in_use ? _range_in_use : _range_unused;
}

/* Whether a page in the mapping range holds data. UNKNOWN always preserves
 * the mapping instead of reclaiming it. */
static int range_usage(uint64_t mapping_start, uint64_t from, uint64_t to, struct range_usage *usage)
{
	int result;

	memset(usage, 0, sizeof(*usage));
	result = range_usage_pagemap(from, to, usage);
	if (result == _range_unknown)
	{
		memset(usage, 0, sizeof(*usage));
		result = range_usage_mincore(mapping_start, from, to, usage);
	}
	return result;
}

static int reclaim_art_overlap(uint64_t address, uint64_t size)
{
	FILE *maps = fopen("/proc/self/maps", "r");
	char line[512];
	int reclaimed = 0;

	if (!maps)
		return 0;
	while (fgets(line, sizeof(line), maps))
	{
		unsigned long long lo, hi;
		uint64_t from, to;
		struct range_usage usage;
		int usage_result;
		char *name;
		int name_offset = 0;

		if (sscanf(line, "%llx-%llx %*s %*s %*s %*s %n", &lo, &hi, &name_offset) < 2 || !name_offset)
			continue;
		if (hi <= address || lo >= address + size)
			continue;
		name = line + name_offset;
		name[strcspn(name, "\n")] = '\0';
		from = lo > address ? lo : address;
		to = hi < address + size ? hi : address + size;
		if (strcmp(name, ART_LARGE_OBJECT_SPACE))
		{
			host_logf(HOST_LOG_ERROR, "a fixed guest range is overlapped by %08llx-%08llx (%s), which is not ART's large object space; left alone",
				lo, hi, name[0] ? name : "unnamed");
			continue;
		}
		usage_result = range_usage(lo, from, to, &usage);
		if (usage_result != _range_unused)
		{
			host_logf(HOST_LOG_ERROR,
				"ART's large object space over %08llx-%08llx %s (%llu pages, %s); left alone",
				(unsigned long long)from, (unsigned long long)to,
				usage_result == _range_in_use ? "is in use" : "could not be checked",
				(unsigned long long)usage.pages_in_use, usage.method ? usage.method : "no readable page map");
			continue;
		}
		if (munmap((void *)from, to - from) == 0)
		{
			host_logf(HOST_LOG_INFO,
				"reclaimed idle ART range %08llx-%08llx (%s)",
				(unsigned long long)from, (unsigned long long)to, name);
			reclaimed = 1;
		}
	}
	fclose(maps);
	return reclaimed;
}

/* reclaim_art: the fixed ranges the guest was built for may take ART's
idle large object space (reclaim_art_overlap); the pools, placed in free
gaps, never do: a mapping in the way there is one ART just made, maybe live */
/* test26: a kernel before 4.17 does not know MAP_FIXED_NOREPLACE and takes
the address as a hint, placing the mapping elsewhere when the range is in
use, without an error: that is the newer kernels' EEXIST. Taken as success,
it was refused with errno left as it was (the first Oculus Quest, Android 10:
"cannot reserve the Xbox memory window at 80000000 (No such file or
directory)"), and ART's idle space in the way was never reclaimed. */
static void *map_fixed_noreplace(uint64_t address, uint64_t size)
{
	void *result = mmap((void *)address, size, PROT_NONE,
		MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE | MAP_FIXED_NOREPLACE, -1, 0);

	if (result != MAP_FAILED && result != (void *)address)
	{
		munmap(result, size);
		errno = EEXIST;
		return MAP_FAILED;
	}
	return result;
}

static int reserve(uint64_t address, uint64_t size, int reclaim_art)
{
	void *result = map_fixed_noreplace(address, size);

	if (result == (void *)address)
		return 0;
	if (reclaim_art && errno == EEXIST)
	{
		int error = errno;

		/* (the caller reports the first failure if nothing was reclaimed) */
		if (!reclaim_art_overlap(address, size))
		{
			errno = error;
			return -1;
		}
		result = map_fixed_noreplace(address, size);
		if (result == (void *)address)
			return 0;
	}
	return -1;
}

static struct pool *pool_new(void)
{
	/* above the image first: ART allocates its own low-4 GB memory from
	the bottom up */
	uint64_t minimum = image_end ? image_end : LOW_START;
	struct pool *pool;
	int attempt;

	if (pool_count == MAXIMUM_POOLS)
		return NULL;
	for (attempt = 0; attempt < 64; attempt++)
	{
		uint64_t address = find_gap(POOL_SIZE, minimum);

		if (!address && minimum != LOW_START)
		{
			minimum = LOW_START;
			address = find_gap(POOL_SIZE, minimum);
		}
		if (!address)
			return NULL;
		if (reserve(address, POOL_SIZE, 0) == 0)
		{
			pool = calloc(1, sizeof(*pool));
			pool->base = address;
			pool->free_pages = POOL_PAGES;
			pools[pool_count++] = pool;
			host_logf(HOST_LOG_INFO, "guest memory pool %d at %08llx", pool_count - 1, (unsigned long long)address);
			return pool;
		}
		/* raced with another mapping; look further up */
		minimum = address + PAGE;
	}
	return NULL;
}

int host_memory_initialize(uint32_t base, uint32_t size)
{
	window_base = HALO_GUEST_WINDOW_BASE;
	window_end = window_base + HALO_GUEST_WINDOW_SIZE;
	if (reserve(window_base, HALO_GUEST_WINDOW_SIZE, 1) != 0)
	{
		host_logf(HOST_LOG_ERROR, "cannot reserve the Xbox memory window at %08llx (%s)",
			(unsigned long long)window_base, strerror(errno));
		host_memory_failure = "Android has already used the memory range the game needs on this device "
			"(the Xbox memory window at 0x80000000).";
		return -1;
	}
	image_base = base;
	image_end = base + round_up(size);
	if (reserve(image_base, image_end - image_base, 1) != 0)
	{
		host_logf(HOST_LOG_ERROR, "cannot reserve the guest image range at %08llx (%s)",
			(unsigned long long)image_base, strerror(errno));
		host_memory_failure = "Android has already used the memory range the game needs on this device "
			"(the game's code range).";
		return -1;
	}
	/* (without it, Custom Edition maps cannot run; the rest of the game can) */
	if (reserve(CUSTOM_EDITION_WINDOW_BASE, CUSTOM_EDITION_WINDOW_SIZE, 1) == 0)
	{
		custom_edition_base = CUSTOM_EDITION_WINDOW_BASE;
		custom_edition_end = CUSTOM_EDITION_WINDOW_BASE + CUSTOM_EDITION_WINDOW_SIZE;
	}
	else
	{
		host_logf(HOST_LOG_WARN, "cannot hold the Custom Edition tag window at %08llx (%s)",
			(unsigned long long)CUSTOM_EDITION_WINDOW_BASE, strerror(errno));
	}
	return 0;
}

/* ---------- page pools */

static void *pool_take(struct pool *pool, uint64_t pages)
{
	uint64_t run = 0, page;

	if (pool->free_pages < pages)
		return NULL;
	for (page = 0; page < POOL_PAGES; page++)
	{
		if (pool->used[page])
		{
			run = 0;
			continue;
		}
		if (++run == pages)
		{
			uint64_t first = page + 1 - pages;

			memset(&pool->used[first], 1, pages);
			pool->free_pages -= pages;
			return (void *)(pool->base + first * PAGE);
		}
	}
	return NULL;
}

void *host_low_map(size_t size, int protection)
{
	uint64_t pages = round_up(size) / PAGE;
	void *address = NULL;
	int index;

	if (!pages || pages > POOL_PAGES)
		return NULL;
	pthread_mutex_lock(&memory_lock);
	for (index = 0; index < pool_count && !address; index++)
		address = pool_take(pools[index], pages);
	if (!address)
	{
		struct pool *pool = pool_new();

		if (pool)
			address = pool_take(pool, pages);
	}
	pthread_mutex_unlock(&memory_lock);
	if (!address)
		return NULL;
	if (mmap(address, pages * PAGE, protection, MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED, -1, 0) != address)
	{
		host_low_unmap(address, pages * PAGE);
		return NULL;
	}
	return address;
}

static struct pool *pool_of(uint64_t address, uint64_t size)
{
	int index;

	for (index = 0; index < pool_count; index++)
	{
		if (in_range(address, size, pools[index]->base, pools[index]->base + POOL_SIZE))
			return pools[index];
	}
	return NULL;
}

void host_low_unmap(void *address, size_t size)
{
	uint64_t start = (uint64_t)address & ~(PAGE - 1);
	uint64_t length = round_up((uint64_t)address + size) - start;
	struct pool *pool;

	pthread_mutex_lock(&memory_lock);
	pool = pool_of(start, length);
	if (pool)
	{
		uint64_t first = (start - pool->base) / PAGE, count = length / PAGE, page;

		/* give the memory back but keep the address space */
		mmap((void *)start, length, PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE | MAP_FIXED, -1, 0);
		for (page = first; page < first + count; page++)
		{
			if (pool->used[page])
			{
				pool->used[page] = 0;
				pool->free_pages++;
			}
		}
	}
	pthread_mutex_unlock(&memory_lock);
}

int host_low_owns(uintptr_t address, size_t size)
{
	int result;

	if (in_range(address, size, window_base, window_end) || in_range(address, size, image_base, image_end) ||
		(custom_edition_end && in_range(address, size, custom_edition_base, custom_edition_end)))
	{
		return 1;
	}
	pthread_mutex_lock(&memory_lock);
	result = pool_of(address, size) != NULL;
	pthread_mutex_unlock(&memory_lock);
	return result;
}

/* ---------- the guest's memory system calls */

long host_guest_mmap(uint64_t address, uint64_t size, int protection, int flags, int fd, int64_t offset)
{
	uint64_t length = round_up(size);
	void *result;

	if (!length)
		return -EINVAL;
	if (flags & (MAP_FIXED | MAP_FIXED_NOREPLACE))
	{
		int fixed_flags = (flags & ~MAP_FIXED_NOREPLACE) | MAP_FIXED;

		if (address + length > LOW_LIMIT)
			return -ENOMEM;
		/* inside a range the host reserved for the guest, a "no replace"
		request replaces the reservation */
		if (!host_low_owns(address, length))
		{
			if (!(flags & MAP_FIXED_NOREPLACE))
				return -EINVAL;
			fixed_flags = flags;
		}
		result = mmap((void *)address, length, protection, fixed_flags, fd, offset);
		if (result == MAP_FAILED)
			return -errno;
		return (long)(uintptr_t)result;
	}
	result = host_low_map(length, PROT_NONE);
	if (!result)
		return -ENOMEM;
	if (mmap(result, length, protection, flags | MAP_FIXED, fd, offset) != result)
	{
		int error = errno;

		host_low_unmap(result, length);
		return -error;
	}
	return (long)(uintptr_t)result;
}

long host_guest_munmap(uint64_t address, uint64_t size)
{
	uint64_t length = round_up(size);

	if (address + length > LOW_LIMIT)
		return -EINVAL;
	if (in_range(address, length, window_base, window_end) ||
		(custom_edition_end && in_range(address, length, custom_edition_base, custom_edition_end)))
	{
		mmap((void *)address, length, PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE | MAP_FIXED, -1, 0);
		return 0;
	}
	if (in_range(address, length, image_base, image_end))
		return -EINVAL;
	if (host_low_owns(address, length))
	{
		host_low_unmap((void *)address, length);
		return 0;
	}
	return munmap((void *)address, length) ? -errno : 0;
}

long host_guest_mprotect(uint64_t address, uint64_t size, int protection)
{
	if (address + size > LOW_LIMIT)
		return -EINVAL;
	return mprotect((void *)address, size, protection) ? -errno : 0;
}

/* ---------- write tracking (port/linux/src/memory_watch.c) */

#define WATCH_PAGE_COUNT (HALO_GUEST_WINDOW_SIZE / PAGE)

/* (each page: 0 not watched, 1 watched and read-only, 2 made writable by a
watched write. A fault on a page at 2 is a write another thread made as
this one was making the page writable, and is made again; one on a page at
0, freed memory or none of the watch's, is a crash) */
static uint8_t page_protected[WATCH_PAGE_COUNT];
static uint32_t page_generation[WATCH_PAGE_COUNT];
static volatile uint32_t current_generation = 1;
static int watch_active;
static int watch_hashing;
static uint8_t page_hash_watched[WATCH_PAGE_COUNT];
static uint64_t page_hash[WATCH_PAGE_COUNT];
static uint32_t page_hashed_frame[WATCH_PAGE_COUNT];
static struct watch_hash page_hashes =
{
	.base = (const uint8_t *)(uintptr_t)HALO_GUEST_WINDOW_BASE,
	.page_count = WATCH_PAGE_COUNT,
	.watched = page_hash_watched,
	.hash = page_hash,
	.hashed_frame = page_hashed_frame,
	.generation = page_generation,
	.current_generation = &current_generation,
	.frame = 1,
};

static int in_window(uint64_t address)
{
	return address >= HALO_GUEST_WINDOW_BASE && address - HALO_GUEST_WINDOW_BASE < HALO_GUEST_WINDOW_SIZE;
}

static uint64_t watch_page(uint64_t address)
{
	return (address - HALO_GUEST_WINDOW_BASE) / PAGE;
}

static void mark_written(uint64_t page)
{
	page_generation[page] = __sync_add_and_fetch(&current_generation, 1);
	page_protected[page] = 2;
	mprotect((void *)(HALO_GUEST_WINDOW_BASE + page * PAGE), PAGE, PROT_READ | PROT_WRITE);
}

static struct sigaction previous_segv, previous_bus, previous_ill;

static void report_crash(int signal_number, siginfo_t *information, void *context)
{
	ucontext_t *ucontext = context;
	const struct sigcontext *registers = (const struct sigcontext *)&ucontext->uc_mcontext;
	uint64_t pc = registers->pc, lr = registers->regs[30];
	int index;

	host_logf(HOST_LOG_ERROR, "signal %d at address %p: pc %016llx lr %016llx sp %016llx",
		signal_number, information->si_addr, (unsigned long long)pc, (unsigned long long)lr,
		(unsigned long long)registers->sp);
	if (pc >= host_image.base && pc < host_image.end)
		host_logf(HOST_LOG_ERROR, "  in the guest image: addr2line -e halo_guest.elf 0x%llx 0x%llx",
			(unsigned long long)pc, (unsigned long long)lr);
	for (index = 0; index < 31; index += 4)
	{
		host_logf(HOST_LOG_ERROR, "  x%-2d %016llx %016llx %016llx %016llx", index,
			(unsigned long long)registers->regs[index],
			(unsigned long long)(index + 1 < 31 ? registers->regs[index + 1] : 0),
			(unsigned long long)(index + 2 < 31 ? registers->regs[index + 2] : 0),
			(unsigned long long)(index + 3 < 31 ? registers->regs[index + 3] : 0));
	}
	/* the guest's frame records: fp and lr, 8 bytes each */
	{
		uint64_t fp = registers->regs[29];

		for (index = 0; index < 24 && fp && fp < LOW_LIMIT && (fp & 7) == 0; index++)
		{
			const uint64_t *frame = (const uint64_t *)fp;

			if (!host_low_owns(fp, 16))
				break;
			host_logf(HOST_LOG_ERROR, "  frame %2d: return %016llx", index, (unsigned long long)frame[1]);
			fp = frame[0];
		}
	}
}

static void chain(struct sigaction *previous, int signal_number, siginfo_t *information, void *context)
{
	sigaction(signal_number, previous, NULL);
	if (previous->sa_flags & SA_SIGINFO)
	{
		if (previous->sa_sigaction)
			previous->sa_sigaction(signal_number, information, context);
	}
	else if (previous->sa_handler != SIG_DFL && previous->sa_handler != SIG_IGN)
	{
		previous->sa_handler(signal_number);
	}
	/* returning re-executes the faulting instruction under the previous
	(or default) handler */
}

static void segv_handler(int signal_number, siginfo_t *information, void *context)
{
	uint64_t address = (uint64_t)information->si_addr;

	if (watch_active && in_window(address))
	{
		uint64_t page = watch_page(address);

		if (page_protected[page] == 1)
		{
			mark_written(page);
			return;
		}
		if (page_protected[page] == 2)
			return;
	}
	report_crash(signal_number, information, context);
	chain(&previous_segv, signal_number, information, context);
}

static void bus_handler(int signal_number, siginfo_t *information, void *context)
{
	report_crash(signal_number, information, context);
	chain(&previous_bus, signal_number, information, context);
}

static void ill_handler(int signal_number, siginfo_t *information, void *context)
{
	report_crash(signal_number, information, context);
	chain(&previous_ill, signal_number, information, context);
}

void host_install_signal_handlers(void)
{
	struct sigaction action;

	memset(&action, 0, sizeof(action));
	action.sa_flags = SA_SIGINFO | SA_NODEFER | SA_ONSTACK;
	sigemptyset(&action.sa_mask);
	action.sa_sigaction = segv_handler;
	sigaction(SIGSEGV, &action, &previous_segv);
	action.sa_sigaction = bus_handler;
	sigaction(SIGBUS, &action, &previous_bus);
	action.sa_sigaction = ill_handler;
	sigaction(SIGILL, &action, &previous_ill);
}

void host_memory_watch_initialize(void)
{
	watch_active = 1;
}

void host_memory_watch_use_hashes(void)
{
	watch_hashing = 1;
}

void host_memory_watch_protect(uint32_t address, uint32_t size)
{
	uint64_t first, last, page;

	if (!watch_active || !size || !in_window(address))
		return;
	first = watch_page(address);
	last = watch_page((uint64_t)address + size - 1);
	if (last >= WATCH_PAGE_COUNT)
		last = WATCH_PAGE_COUNT - 1;
	if (watch_hashing)
	{
		watch_hash_protect(&page_hashes, (uint32_t)first, (uint32_t)last);
		return;
	}
	for (page = first; page <= last; page++)
	{
		if (page_protected[page] != 1)
		{
			page_protected[page] = 1;
			mprotect((void *)(HALO_GUEST_WINDOW_BASE + page * PAGE), PAGE, PROT_READ);
		}
	}
}

uint32_t host_memory_watch_serial(void)
{
	return current_generation;
}

uint32_t host_memory_watch_generation(uint32_t address, uint32_t size)
{
	uint64_t first, last, page;
	uint32_t newest = 0;

	if (!size || !in_window(address))
		return 0;
	first = watch_page(address);
	last = watch_page((uint64_t)address + size - 1);
	if (last >= WATCH_PAGE_COUNT)
		last = WATCH_PAGE_COUNT - 1;
	if (watch_hashing)
		return watch_hash_generation(&page_hashes, (uint32_t)first, (uint32_t)last);
	for (page = first; page <= last; page++)
	{
		if (page_generation[page] > newest)
			newest = page_generation[page];
	}
	return newest;
}

void host_memory_watch_prepare_write(uint32_t address, uint32_t size)
{
	uint64_t start = address, first, last, page;

	if (!watch_active || watch_hashing || !size)
		return;
	if (start + size <= HALO_GUEST_WINDOW_BASE || start >= (uint64_t)HALO_GUEST_WINDOW_BASE + HALO_GUEST_WINDOW_SIZE)
		return;
	if (start < HALO_GUEST_WINDOW_BASE)
		start = HALO_GUEST_WINDOW_BASE;
	first = watch_page(start);
	last = watch_page((uint64_t)address + size - 1);
	if (last >= WATCH_PAGE_COUNT)
		last = WATCH_PAGE_COUNT - 1;
	for (page = first; page <= last; page++)
	{
		if (page_protected[page] == 1)
			mark_written(page);
	}
}

void host_memory_watch_begin_frame(void)
{
	if (watch_hashing)
		watch_hash_begin_frame(&page_hashes);
}

void host_memory_watch_forget(uint32_t address, uint32_t size)
{
	uint64_t first, last, page;

	if (!size || !in_window(address))
		return;
	first = watch_page(address);
	last = watch_page((uint64_t)address + size - 1);
	if (last >= WATCH_PAGE_COUNT)
		last = WATCH_PAGE_COUNT - 1;
	if (watch_hashing)
	{
		watch_hash_forget(&page_hashes, (uint32_t)first, (uint32_t)last);
		return;
	}
	for (page = first; page <= last; page++)
	{
		page_protected[page] = 0;
		page_generation[page] = __sync_add_and_fetch(&current_generation, 1);
	}
}
