"""Test73: what this port takes from OpenCE's forks (innerhat, universal), each with the fork commit it came from.
The full list of the forks' commits and the verdict for each is the Test73 checklist's (taken, already here, not
applicable, or left for the owner).

innerhat 83e8bb135: a new map's first-person weapon state names no weapon. The state is cleared with a memset, and 0
is no datum's index: the render's check for a weapon deleted under it (weapon_index != NONE and no such weapon)
then logged "weapon (0x0), deleted unexpectedly" after every map load. The real
first_person_weapons_initialize_for_new_map runs here on a state full of garbage.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73_forks'


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def fn(text, name):
    m = re.search(r'^(?:static )?(?:inline )?[\w *]+\b' + re.escape(name) + r'\s*\([^;{]*\)\s*\{', text, re.M)
    assert m, name
    a = text.index('{', m.start())
    b, depth = a + 1, 1
    while depth:
        depth += (text[b] == '{') - (text[b] == '}')
        b += 1
    return text[m.start():b] + '\n'


def run(name, source):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (name + '.c')
    path.write_text(source, encoding='utf-8')
    subprocess.run(['clang', '-std=gnu11', '-O1', '-Wall', '-Werror', '-fsanitize=address,undefined', str(path),
                    '-o', str(OUT / name)], check=True)
    result = subprocess.run([str(OUT / name)], check=True, capture_output=True, text=True)
    print(result.stdout.strip())


weapons = read('source/interface/first_person_weapons.c')
# (the check the cleared index is for: a weapon index that is not NONE whose weapon is gone is logged and forgotten)
assert re.search(r'first_person_weapon->weapon_index!=NONE &&\s*!weapon_try_and_get\(first_person_weapon->weapon_index\)'
                 r'[\s\S]{0,200}deleted unexpectedly', weapons), 'the stale-weapon check'
run('new_map_weapon', r'''
#include <stdio.h>
#include <string.h>
#define NONE -1
#define MAXIMUM_NUMBER_OF_LOCAL_PLAYERS 4
#define csmemset memset
struct first_person_weapon { char visible; long unit_index, weapon_index; short current_sound_state;
	long current_sound_index; char rest[64]; };
static struct first_person_weapon first_person_weapons[MAXIMUM_NUMBER_OF_LOCAL_PLAYERS];
''' + fn(weapons, 'first_person_weapons_initialize_for_new_map') + r'''
int main(void)
{
	int index;

	memset(first_person_weapons, 0x5a, sizeof(first_person_weapons));
	first_person_weapons_initialize_for_new_map();
	for (index = 0; index < MAXIMUM_NUMBER_OF_LOCAL_PLAYERS; index++)
	{
		struct first_person_weapon const *weapon = &first_person_weapons[index];

		if (weapon->unit_index != NONE || weapon->weapon_index != NONE || weapon->current_sound_index != NONE ||
			weapon->current_sound_state != NONE || weapon->visible || weapon->rest[0])
		{
			printf("FAIL: local player %d's first-person state after a new map\n", index);
			return 1;
		}
	}
	puts("PASS: a new map's first-person weapon state names no unit, weapon or sound (innerhat 83e8bb135)");
	return 0;
}
''')
memory = read('source/cseries/debug_memory.c')
signatures = dict(re.findall(r'(debug_memory_\w+_signature) = (0x[0-9A-Fa-f]+)', memory))
run('realloc_failed', r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAXIMUM_POINTER_SIZE 0x7fffffff
#define match_assert(file, line, condition) do { if (!(condition)) { puts("FAIL: assert " #condition); exit(1); } } while (0)
typedef unsigned char byte;
enum { debug_memory_allocated_signature = %(allocated)s, debug_memory_disposed_signature = %(disposed)s,
	debug_memory_trailing_signature = %(trailing)s };
struct debug_memory_header { unsigned long signature; struct debug_memory_header *next, *previous; unsigned long size;
	const char *file; long line; long allocation_id; unsigned long checksum; };
static struct { long next_allocation_id; long current_heap_size, maximum_pointer_size; } debug_memory_globals;
static struct debug_memory_header *listed; /* the one block of the allocation list */
static int fail_next;
static void debug_check_memory_globals(const char *file, long line) { (void)file; (void)line; }
static void debug_check_pointer_header(struct debug_memory_header *header, const char *file, long line)
{
	(void)file; (void)line;
	if (header->signature != debug_memory_allocated_signature) { puts("FAIL: Pointer has been disposed"); exit(1); }
}
static void debug_check_pointer_overrun(void *pointer, const char *file, long line) { (void)pointer; (void)file; (void)line; }
static void debug_memory_remove_pointer(struct debug_memory_header *header, const char *file, long line)
{
	(void)file; (void)line;
	if (listed != header) { puts("FAIL: removed a block not listed"); exit(1); }
	listed = NULL;
}
static void debug_memory_add_pointer(struct debug_memory_header *header) { listed = header; }
static void debug_memory_fill_with_random(byte *data, unsigned long size) { memset(data, 0xcd, size); }
static void *system_realloc(void *pointer, size_t size)
{
	if (fail_next) { fail_next = 0; return NULL; }
	return realloc(pointer, size);
}
''' % {'allocated': signatures['debug_memory_allocated_signature'],
       'disposed': signatures['debug_memory_disposed_signature'],
       'trailing': signatures['debug_memory_trailing_signature']} + fn(memory, 'debug_realloc') + r'''
int main(void)
{
	char *block = debug_realloc(NULL, 100, "test", 1), *same;
	struct debug_memory_header *header;

	if (!block || !listed) { puts("FAIL: the first allocation"); return 1; }
	memcpy(block, "kept", 5);
	header = (struct debug_memory_header *)block - 1;
	fail_next = 1;
	if (debug_realloc(block, 1 << 20, "test", 2)) { puts("FAIL: the failing realloc returned a block"); return 1; }
	if (header->signature != debug_memory_allocated_signature || listed != header || strcmp(block, "kept"))
	{
		puts("FAIL: a failed realloc left the caller's block disposed or unlisted");
		return 1;
	}
	/* (the caller still owns it: a later realloc or free of it goes through the header check) */
	same = debug_realloc(block, 200, "test", 3);
	if (!same || strcmp(same, "kept")) { puts("FAIL: the block after a failed realloc"); return 1; }
	debug_realloc(same, 0, "test", 4);
	puts("PASS: a failed debug_realloc gives the caller its block back, allocated and listed (halo-ce-universal 50331e0a5)");
	return 0;
}
''')
sounds = read('port/linux/game/custom_edition_sounds.c')
chunk_struct = re.search(r'struct decoded_chunk\n\{[\s\S]*?\n\};\n', sounds).group(0)
globals_struct = re.search(r'static struct\n\{\n\tstruct decoded_chunk \*chunks;[\s\S]*?\} custom_edition_sounds_globals;\n',
                           sounds).group(0)
chunk_bytes = re.search(r'#define DECODED_CHUNK_BYTES (0x[0-9a-fA-F]+)', sounds).group(1)
run('sound_chunks', r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define NONE -1
#define TRUE 1
#define FALSE 0
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define DECODED_CHUNK_BYTES ''' + chunk_bytes + r'''
typedef unsigned char byte;
typedef int boolean;
''' + chunk_struct + globals_struct + fn(sounds, 'decoded_reserve') + fn(sounds, 'decoded_commit') +
    fn(sounds, 'custom_edition_sounds_decoded_bytes') + fn(sounds, 'custom_edition_sounds_read') +
    fn(sounds, 'custom_edition_sounds_dispose') + r'''
#define SOUNDS 40
static unsigned long sizes[SOUNDS];
static long offsets[SOUNDS];
static byte fill(int sound, unsigned long at) { return (byte)(sound * 31 + at * 7 + (at >> 9)); }
int main(void)
{
	int sound;
	unsigned long at;
	byte *check;

	custom_edition_sounds_globals.decoded_limit = 0x10000000;
	/* small sounds that leave a chunk part used, a sound larger than a chunk, and more after it */
	for (sound = 0; sound < SOUNDS; sound++)
	{
		byte *where;

		sizes[sound] = sound == 17 ? 3 * DECODED_CHUNK_BYTES + 12345 : 300000 + 4099 * (unsigned long)sound;
		where = decoded_reserve(sizes[sound], &offsets[sound]);
		if (!where || offsets[sound] != (long)custom_edition_sounds_decoded_bytes()) { puts("FAIL: reserve"); return 1; }
		for (at = 0; at < sizes[sound]; at++)
			where[at] = fill(sound, at);
		decoded_commit(sizes[sound]);
	}
	if (custom_edition_sounds_globals.chunk_count < 3) { puts("FAIL: the sounds were not split into chunks"); return 1; }
	for (sound = 1; sound < custom_edition_sounds_globals.chunk_count; sound++)
	{
		struct decoded_chunk const *previous = &custom_edition_sounds_globals.chunks[sound - 1];

		if (custom_edition_sounds_globals.chunks[sound].base != previous->base + previous->used)
		{
			puts("FAIL: a gap between chunks");
			return 1;
		}
	}
	check = malloc(sizes[17]);
	for (sound = 0; sound < SOUNDS; sound++)
	{
		if (!custom_edition_sounds_read(offsets[sound], (long)sizes[sound], check)) { puts("FAIL: read"); return 1; }
		for (at = 0; at < sizes[sound]; at++)
			if (check[at] != fill(sound, at)) { printf("FAIL: sound %d byte %lu\n", sound, at); return 1; }
	}
	/* a read across two sounds, and so across a chunk's end */
	for (sound = 0; sound + 1 < SOUNDS; sound++)
	{
		long from = offsets[sound + 1] - 1000;

		if (!custom_edition_sounds_read(from, 2000, check) || check[999] != fill(sound, sizes[sound] - 1) ||
			check[1000] != fill(sound + 1, 0))
		{
			printf("FAIL: a read across sounds %d and %d\n", sound, sound + 1);
			return 1;
		}
	}
	if (custom_edition_sounds_read((long)custom_edition_sounds_decoded_bytes() - 10, 11, check) ||
		custom_edition_sounds_read(-1, 4, check))
	{
		puts("FAIL: a read past the sounds");
		return 1;
	}
	{
		long offset;

		custom_edition_sounds_globals.decoded_limit = custom_edition_sounds_decoded_bytes() + 100;
		if (decoded_reserve(101, &offset) || !decoded_reserve(100, &offset)) { puts("FAIL: the region's limit"); return 1; }
	}
	free(check);
	custom_edition_sounds_dispose();
	if (custom_edition_sounds_globals.chunks || custom_edition_sounds_decoded_bytes()) { puts("FAIL: dispose"); return 1; }
	puts("PASS: Custom Edition's converted sounds kept in chunks, read back whole and across chunks, limit kept, all freed "
		"(halo-ce-universal e777348a2)");
	return 0;
}
''')
menus = read('port/linux/game/menu_functions.c')
# (which start goes on with a saved game: Continue and Load Game do; New Game's list, its difficulty and a map played
# alone do not)
for function, expected in (('campaign_continue', 'TRUE'), ('saved_game_continue', 'TRUE'), ('difficulty_start', 'FALSE'),
                           ('mcc_solo_choose', 'FALSE'), ('level_choose', 'FALSE')):
    calls = re.findall(r'campaign_start\([^;]*, (TRUE|FALSE)\);', fn(menus, function))
    assert calls and set(calls) == {expected}, (function, calls)
run('new_game', r'''
#include <stdio.h>
#include <string.h>
#define TRUE 1
#define FALSE 0
typedef int boolean;
static int player_spawn_count = 1, allowed, sounds;
static char map[64], steps[64];
static void player_ui_set_single_player_local_player_controller(int player, short controller) { (void)player; (void)controller; }
static void main_set_map_name(char const *name) { strcpy(map, name); allowed = TRUE; strcat(steps, "m"); }
static void main_disallow_persistent_storage(void) { allowed = FALSE; strcat(steps, "d"); }
static void main_set_difficulty(short difficulty) { (void)difficulty; strcat(steps, "f"); }
static void game_connection_set(int connection) { (void)connection; }
static void main_menu_switch_to_single_player(void) { strcat(steps, "s"); }
static void player_ui_remember_player1_profile(boolean remember) { (void)remember; }
static void ui_play_audio_feedback_sound(int sound) { (void)sound; sounds++; }
#define SOUND_FORWARD 1
''' + fn(menus, 'campaign_start') + r'''
int main(void)
{
	campaign_start("levels\\a30\\a30", 2, 0, FALSE);
	if (allowed || strcmp(steps, "mdfs")) { printf("FAIL: New Game took the saved game (%s)\n", steps); return 1; }
	steps[0] = 0;
	campaign_start("levels\\a30\\a30", 2, 0, TRUE);
	if (!allowed || strcmp(steps, "mfs")) { printf("FAIL: Continue did not take the saved game (%s)\n", steps); return 1; }
	puts("PASS: New Game starts its level anew, Continue and Load Game go on with the saved game (halo-ce-universal "
		"eaa3b6194)");
	return 0;
}
''')
main = read('source/main/main.c')
# (halo-ce-universal 544f8cd29: with interpolation, no frame of a map before its first tick, so a level is not seen
# before its startup scripts' fade and cinematic; inline in main_loop_iteration, so pinned rather than run)
loop = fn(main, 'main_loop_iteration')
assert re.search(r'if \(halo_interpolation_enabled\(\)\)\s*render_frame = main_globals\.main_menu_scenario_loaded \|\|\s*'
                 r'\(main_globals\.halt_time_scale && game_time_get\(\)>0\);', loop), 'no frame before the first tick'
assert re.search(r'render_frame &= !game_engine_running\(\) \|\| game_time_get\(\)>=3;', loop)
print('PASS: no frame of a map is drawn before its first tick, with interpolation (halo-ce-universal 544f8cd29)')
state = read('source/saved games/game_state_xbox.c')
prefix = re.search(r'struct xbox_game_state_globals_prefix\n\{[\s\S]*?\n\};\n', state).group(0)
writer = re.search(r'static struct\n\{\n\t/\* the snapshot[\s\S]*?\} game_state_writer = \{ 0 \};\n', state).group(0)
run('checkpoint_writer', r'''
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#define TRUE 1
#define FALSE 0
#define WINAPI
#define INFINITE 0xFFFFFFFFu
#define FILE_BEGIN 0
#define INVALID_SET_FILE_POINTER 0xFFFFFFFFu
#define CPU_PAGE_SIZE 0x1000
#define SIZE 0x40000
typedef int boolean;
typedef unsigned char byte;
typedef int BOOL;
typedef unsigned int DWORD;
typedef void *LPVOID, *HANDLE;
#define match_assert(file, line, condition) do { if (!(condition)) { puts("FAIL: assert " #condition); exit(1); } } while (0)
#define match_vassert(file, line, condition, text) do { if (!(condition)) { puts(text); exit(1); } } while (0)
static char temporary[256];
#define csprintf(buffer, ...) (snprintf(buffer, sizeof(buffer), __VA_ARGS__), buffer)
#define _error_log 0
static void error(int kind, char const *format, ...) { (void)kind; (void)format; }
static DWORD GetLastError(void) { return 0; }
static int recover_saved_games_hack;
/* (the shims: events with manual or automatic reset, a thread, a file of SIZE bytes that writes slowly) */
struct event { pthread_mutex_t lock; pthread_cond_t condition; int manual, signaled; };
static HANDLE CreateEventA(void *attributes, BOOL manual, BOOL initial, char const *name)
{
	struct event *event = calloc(1, sizeof(*event));
	(void)attributes; (void)name;
	pthread_mutex_init(&event->lock, NULL); pthread_cond_init(&event->condition, NULL);
	event->manual = manual; event->signaled = initial;
	return event;
}
static BOOL SetEvent(HANDLE handle)
{
	struct event *event = handle;
	pthread_mutex_lock(&event->lock); event->signaled = 1; pthread_cond_broadcast(&event->condition);
	pthread_mutex_unlock(&event->lock);
	return TRUE;
}
static BOOL ResetEvent(HANDLE handle)
{
	struct event *event = handle;
	pthread_mutex_lock(&event->lock); event->signaled = 0; pthread_mutex_unlock(&event->lock);
	return TRUE;
}
static DWORD WaitForSingleObject(HANDLE handle, DWORD milliseconds)
{
	struct event *event = handle;
	(void)milliseconds;
	pthread_mutex_lock(&event->lock);
	while (!event->signaled)
		pthread_cond_wait(&event->condition, &event->lock);
	if (!event->manual)
		event->signaled = 0;
	pthread_mutex_unlock(&event->lock);
	return 0;
}
static pthread_t thread;
static char file_handle[1];
/* (an event's handle is freed; the file's and the thread's are not this shim's to free) */
static BOOL CloseHandle(HANDLE handle) { if (handle && handle != &thread && handle != (HANDLE)file_handle) free(handle); return TRUE; }
static int threads_allowed = 1;
static HANDLE CreateThread(void *attributes, size_t stack, DWORD (*start)(LPVOID), LPVOID argument, DWORD flags, DWORD *id)
{
	(void)attributes; (void)stack; (void)flags; (void)id;
	if (!threads_allowed || pthread_create(&thread, NULL, (void *(*)(void *))start, argument))
		return NULL;
	return &thread;
}
static byte file[SIZE];
static volatile int writes_started, writes_done, writing;
static DWORD SetFilePointer(HANDLE handle, long distance, long *high, DWORD method)
{
	(void)handle; (void)distance; (void)high; (void)method;
	return 0;
}
static BOOL WriteFile(HANDLE handle, void const *data, DWORD size, unsigned long *written, void *overlapped)
{
	(void)handle; (void)overlapped;
	writes_started++; writing = 1;
	usleep(150000);
	memcpy(file, data, size); *written = size;
	writing = 0; writes_done++;
	return TRUE;
}
static BOOL ReadFile(HANDLE handle, void *data, DWORD size, unsigned long *read, void *overlapped)
{
	(void)handle; (void)overlapped;
	memcpy(data, file, size); *read = size;
	return TRUE;
}
''' + prefix + r'''
static struct xbox_game_state_globals_prefix xbox_game_state_globals;
''' + writer + r'''
static byte *game_state_base;
static int accepted;
/* (game_state.c's: checked, copied in, MCC's slots put back) */
static boolean game_state_image_accept(void *image, long size)
{
	accepted++;
	memcpy(game_state_base, image, (size_t)size);
	return TRUE;
}
''' + fn(state, 'game_state_writer_main') + fn(state, 'game_state_writer_ready') + fn(state, 'game_state_writer_wait') +
    fn(state, 'game_state_close_file') + fn(state, 'game_state_write_to_file') + fn(state, 'game_state_read_from_file') + r'''
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec / 1e9; }
int main(int argc, char **argv)
{
	double start;

	game_state_base = malloc(SIZE);
	xbox_game_state_globals.buffer_allocated = TRUE;
	xbox_game_state_globals.buffer = game_state_base;
	xbox_game_state_globals.buffer_size = SIZE;
	xbox_game_state_globals.file_open = TRUE;
	xbox_game_state_globals.handle = file_handle;
	if (argc > 1)
	{
		/* (no thread: written as the Xbox wrote it, before the checkpoint returns) */
		threads_allowed = 0;
		memset(game_state_base, 'A', SIZE);
		if (!game_state_write_to_file() || writes_done != 1 || file[SIZE - 1] != 'A') { puts("FAIL: the fallback"); return 1; }
		puts("PASS: without the writer thread a checkpoint is written before it returns (halo-ce-universal fba8d44c5)");
		return 0;
	}
	memset(game_state_base, 'A', SIZE);
	start = now();
	if (!game_state_write_to_file() || now() - start > 0.1) { puts("FAIL: the checkpoint waited for its write"); return 1; }
	/* (the game goes on, changing its state, while the snapshot is written) */
	memset(game_state_base, 'B', SIZE);
	if (writes_done) { puts("FAIL: the write was not behind the game's back"); return 1; }
	if (!game_state_read_from_file() || accepted != 1 || game_state_base[0] != 'A' || game_state_base[SIZE - 1] != 'A')
	{
		puts("FAIL: a revert during the write did not take the checkpoint, through game_state_image_accept");
		return 1;
	}
	/* (the next checkpoint waits for the last one's write) */
	memset(game_state_base, 'C', SIZE);
	if (!game_state_write_to_file() || writes_done != 1) { puts("FAIL: the second checkpoint"); return 1; }
	game_state_close_file();
	if (writes_done != 2 || writing || file[0] != 'C' || file[SIZE - 1] != 'C' || game_state_writer.snapshot_valid)
	{
		printf("FAIL: closing the file did not wait for the last write (%d done)\n", writes_done);
		return 1;
	}
	puts("PASS: a checkpoint written behind the game's back: returns at once, a revert meanwhile takes it from memory "
		"through game_state_image_accept, the next waits for it, closing waits too (halo-ce-universal fba8d44c5)");
	return 0;
}
''')
subprocess.run([str(OUT / 'checkpoint_writer'), 'nothread'], check=True)

bounds = read('port/linux/game/object_bounds_cache.c')
collisions = read('source/physics/collisions.c')
math = read('source/math/real_math.c')
# (object_test_vector's own first test, as written there: the skip must agree with it on every case)
condition = re.search(r'if \((object_index != ignore_object_index &&\s*!TEST_FLAG\(object->object\.flags, _object_invisible_bit\) &&'
                      r'[\s\S]*?\(object->object\.bounding_sphere_radius\)\))\)', fn(collisions, 'object_test_vector')).group(1)
assert re.search(r'!object_bounds_cache_vector_misses\(object_index, flags, _collision_test_objects_first_type_bit, point, '
                 r'vector\) &&\s*object_mark_function\(object_index\) &&\s*object_test_vector\(', fn(collisions, 'collision_test_vector'))
run('vector_skip', r'''
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#define TRUE 1
#define FALSE 0
#define NONE -1
#define MAXIMUM_OBJECTS_PER_MAP 64
#define DATUM_INDEX_TO_ABSOLUTE_INDEX(index) ((index) & 0xFFFF)
#define FLAG(bit) (1UL << (bit))
#define TEST_FLAG(flags, bit) (((flags) & FLAG(bit)) != 0)
#define _collision_test_objects_first_type_bit 8
#define _object_invisible_bit 0
typedef int boolean;
typedef float real;
typedef struct { real x, y, z; } real_point3d;
typedef struct { real i, j, k; } real_vector3d;
static __attribute__((unused)) boolean point_in_sphere(real_point3d const *p, real_point3d const *c, real r)
{
	real x = p->x - c->x, y = p->y - c->y, z = p->z - c->z;
	return x * x + y * y + z * z <= r * r;
}
''' + fn(math, 'fast_vector_intersects_sphere') +
    re.search(r'struct object_bounds\n\{[\s\S]*?\n\};\n', bounds).group(0) +
    'static struct object_bounds object_bounds[MAXIMUM_OBJECTS_PER_MAP];\nstatic long object_bounds_epoch = 1;\n' +
    fn(bounds, 'object_bounds_cache_update') + fn(bounds, 'object_bounds_cache_invalidate') +
    fn(bounds, 'object_bounds_cache_vector_misses') + r'''
struct object_datum { struct { unsigned long flags; short type; real_point3d bounding_sphere_center; real bounding_sphere_radius; } object; };
static real random_real(real low, real high) { return low + (high - low) * (real)rand() / (real)RAND_MAX; }
int main(void)
{
	int trial, skipped = 0, tested = 0;

	srand(73);
	for (trial = 0; trial < 200000; trial++)
	{
		long object_index = (long)((trial % 7 + 1) << 16) | (trial % MAXIMUM_OBJECTS_PER_MAP);
		long ignore_object_index = NONE;
		struct object_datum datum = { { 0, (short)(rand() % 12),
			{ random_real(-20, 20), random_real(-20, 20), random_real(-5, 5) }, random_real(0.05f, 6.f) } };
		struct object_datum const *object = &datum;
		unsigned long flags = (unsigned long)rand() << 8 & 0xFFFFF00UL;
		real_point3d point_value = { random_real(-30, 30), random_real(-30, 30), random_real(-8, 8) };
		real_vector3d vector_value = { random_real(-40, 40), random_real(-40, 40), random_real(-10, 10) };
		real_point3d const *point = &point_value;
		real_vector3d const *vector = &vector_value;
		boolean full, misses;

		object_bounds_cache_update(object_index, datum.object.type, &datum.object.bounding_sphere_center,
			datum.object.bounding_sphere_radius);
		full = (''' + condition + r''');
		misses = object_bounds_cache_vector_misses(object_index, flags, _collision_test_objects_first_type_bit, point, vector);
		if (misses == full) { printf("FAIL: trial %d: the skip %s an object the test %s\n", trial, misses ? "passes by" : "keeps",
			full ? "takes" : "refuses"); return 1; }
		skipped += misses;
		tested++;
		/* (another datum in that slot, or the game state replaced: not known, never skipped) */
		if (object_bounds_cache_vector_misses(object_index + 0x10000, flags, _collision_test_objects_first_type_bit, point, vector))
		{
			puts("FAIL: a stale entry skipped an object");
			return 1;
		}
		if (trial % 1000 == 999)
		{
			object_bounds_cache_invalidate();
			if (object_bounds_cache_vector_misses(object_index, flags, _collision_test_objects_first_type_bit, point, vector))
			{
				puts("FAIL: an entry from before the game state was replaced skipped an object");
				return 1;
			}
		}
	}
	if (!skipped || skipped == tested) { puts("FAIL: the cases do not cover both outcomes"); return 1; }
	printf("PASS: a vector's object loop passes by exactly the objects object_test_vector's first test refuses "
		"(%d of %d cases), never on a stale entry (halo-ce-universal b9ac6b855)\n", skipped, tested);
	return 0;
}
''')
syscalls = read('port/android/host/host_syscall.c')
clock_case = re.search(r'\tcase SYS_clock_gettime:\n\tcase SYS_clock_getres:\n\t\{[\s\S]*?\n\t\treturn result_of\(result\);\n\t\}\n',
                       syscalls).group(0)
assert 'syscall(number' not in clock_case, "the guest's clock goes into the kernel each time"
run('guest_clock', r'''
#define _GNU_SOURCE
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
#define GUEST(type, address) ((type)(uintptr_t)(address))
''' + re.search(r'struct guest_timespec\n\{[\s\S]*?\n\};\n', syscalls).group(0) + fn(syscalls, 'timespec_out') +
    fn(syscalls, 'result_of') + r'''
static long call(long number, long long a, long long b)
{
	switch (number)
	{
''' + clock_case + r'''
	}
	return -ENOSYS;
}
static long long nanoseconds(struct guest_timespec const *t) { return t->seconds * 1000000000LL + t->nanoseconds; }
int main(void)
{
	struct guest_timespec guest, again, resolution;
	struct timespec kernel;
	int index;

	for (index = 0; index < 1000; index++)
	{
		if (call(SYS_clock_gettime, CLOCK_MONOTONIC, (long long)(uintptr_t)&guest) ||
			syscall(SYS_clock_gettime, CLOCK_MONOTONIC, &kernel) ||
			call(SYS_clock_gettime, CLOCK_MONOTONIC, (long long)(uintptr_t)&again))
		{
			puts("FAIL: the clock");
			return 1;
		}
		/* (the same clock as the system call's: between the two reads around it) */
		if (nanoseconds(&guest) > (int32_t)kernel.tv_sec * 1000000000LL + kernel.tv_nsec ||
			(int32_t)kernel.tv_sec * 1000000000LL + kernel.tv_nsec > nanoseconds(&again))
		{
			puts("FAIL: the guest's clock is not the kernel's monotonic clock");
			return 1;
		}
	}
	if (call(SYS_clock_getres, CLOCK_MONOTONIC, (long long)(uintptr_t)&resolution) || nanoseconds(&resolution) <= 0 ||
		call(SYS_clock_gettime, 0x7fff, (long long)(uintptr_t)&guest) != -EINVAL)
	{
		puts("FAIL: the clock's resolution, or a clock that does not exist");
		return 1;
	}
	puts("PASS: the guest's clock_gettime and clock_getres read the C library's clocks, the kernel's monotonic clock "
		"and errors as before, with no system call (halo-ce-universal a6445c28f, done on the host)");
	return 0;
}
''')
print('PASS: Test73 fork ports')
