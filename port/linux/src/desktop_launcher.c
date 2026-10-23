/*
DESKTOP_LAUNCHER.C

Test72: the desktop builds' launcher (desktop_launcher.h), the owner's: "one
launcher for Windows flat and PCVR ... Play, Game data (pick XISO, validate,
extract), Verify/Repair, Mods (the same recipe files Android uses), What's
New, Graphics, Controls, VR or stereo options by target", and "one extracted
library ... shared by the flat and PCVR executables".

It is a window of its own, before the game's (SDL's renderer, the game's
Overpass fonts through stb_truetype), driven by the mouse, the keyboard
(arrows, Enter, Escape) or a gamepad (the D-pad, A, B). Its pages:

- HOME: play here; play the other build (halo.exe and halo-vr.exe, side by
  side, share the maps folder, the saves and the campaigns: the other is
  started, this one ends); the game data's state.
- GAME DATA: import an Xbox disc image (xiso.c, as the first start always
  could), its maps' SHA-256 recorded in library.sha256 beside them; VERIFY
  checks them against it; REPAIR extracts them again from the image.
- CUSTOM CAMPAIGNS: the Android app's three, by the same recipes
  (campaigns/<id>.properties, embedded) and the same folders (mods/<id>/maps,
  mods/ce, mods/original, mods/<id>.on, mods/custom_edition.on), so one
  library serves both: a folder of the player's files imported (each file's
  size and SHA-256 checked), the campaign put in and taken out (the
  ModInstaller.java swap). Downloads are the browser's: the page opens.
- SETTINGS: the headline settings (config.toml); everything else in the
  game's own Settings, controls with remapping included.
- PC VR (or VR): what the headset build needs, and playing it.
- WHAT'S NEW (the Android app's own text) and UPDATES (the fork's latest
  GitHub release, asked for only when the player asks).

A Custom Edition campaign needs the game started with Custom Edition maps
loading (its tag cache is reserved before main: xbox_memory.c): with one in,
playing starts the game anew with HALO_CUSTOM_EDITION set, the launcher not
shown again (HALO_LAUNCHER=0). Not on Android (its launcher is the app's) or
the web.
*/

#include "platform.h"
#include "port_config.h"
#include "update.h"
#include "xiso.h"
#include "text_hires.h"
#include "desktop_launcher.h"
#include "halo_port_version.h"
#include "save_transfer.h"

#if !defined(HALO_ANDROID) && !defined(HALO_WEB)

#include "../game/mcc_sha256.h"
#include <SDL3/SDL.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STBTT_STATIC
#define STB_TRUETYPE_IMPLEMENTATION
#include "../../third_party/stb/stb_truetype.h"

#ifdef _WIN32
#define LAUNCHER_SEPARATOR "\\"
#define LAUNCHER_FLAT_EXE "halo.exe"
#define LAUNCHER_VR_EXE "halo-vr.exe"
#else
#define LAUNCHER_SEPARATOR "/"
#define LAUNCHER_FLAT_EXE "halo"
#define LAUNCHER_VR_EXE "halo-vr"
#endif

#define LAUNCHER_WIDTH 1280
#define LAUNCHER_HEIGHT 800
#define LAUNCHER_PATH 1024
#define LAUNCHER_ATLAS 1024

/* ---------- the campaigns (ModInstaller.java's MODS, the same ids, names
and folders; each file's size and SHA-256 are its recipe's) */

struct launcher_mod_map
{
	const char *name;
	int extra; /* a level of its own: no campaign map put aside for it */
};

struct launcher_mod
{
	const char *id, *title, *status, *extension;
	/* an OpenSauce mod's own resource maps' prefix (maps/data_files), or
	NULL: it takes Custom Edition's (mods/ce) */
	const char *data_files;
	const char *summary, *page;
	struct launcher_mod_map maps[10];
	int map_count;
};

static const struct launcher_mod launcher_mods[] =
{
	{ "spv1", "SPV1 - CMT Single Player Campaign", "Supported", ".map", NULL,
		"The Custom Mapping Team's 2006 remake of all ten campaign levels, made for Halo Custom Edition: "
		"new weapons, enemies and vehicles throughout. Needs Halo Custom Edition's own bitmaps.map, "
		"sounds.map and loc.map. Each level downloads from halomaps.org on its own page.",
		"https://www.halomaps.org/hce/detail.cfm?fid=1921",
		{ { "a10", 0 }, { "a30", 0 }, { "a50", 0 }, { "b30", 0 }, { "b40", 0 },
		  { "c10", 0 }, { "c20", 0 }, { "c40", 0 }, { "d20", 0 }, { "d40", 0 } }, 10 },
	{ "lumoria", "Project Lumoria", "Supported", ".map", NULL,
		"The TM Mapping Team's 2012 campaign for Halo Custom Edition in four new levels (lumoria_a to "
		"lumoria_d), played beside the original campaign: New Game, map kind CUSTOM SINGLEPLAYER. Needs "
		"Halo Custom Edition's own bitmaps.map, sounds.map and loc.map.",
		"https://www.halomaps.org/hce/detail.cfm?fid=6503",
		{ { "lumoria_a", 1 }, { "lumoria_b", 1 }, { "lumoria_c", 1 }, { "lumoria_d", 1 } }, 4 },
	{ "altheros", "The Altheros Experience", "Experimental \xE2\x80\x94 currently not working", ".yelo", "alsthetic",
		"Altheros's Halo 1 campaign mod (private beta, October 2019): reworked encounters, weapons and "
		"effects as OpenSauce maps with their own resource maps. Not yet confirmed to run.",
		"https://www.moddb.com/mods/the-altheros-experience-halo-1-campaign-mod/downloads/latest-altheros-experience-10-24-2019",
		{ { "a10", 0 }, { "a30", 0 }, { "a50", 0 }, { "b30", 0 }, { "b40", 0 },
		  { "c10", 0 }, { "c20", 0 }, { "c40", 0 }, { "d20", 0 }, { "f10", 1 } }, 10 },
};
#define LAUNCHER_MOD_COUNT ((int)(sizeof(launcher_mods) / sizeof(launcher_mods[0])))
static const char *const launcher_resources[3] = { "bitmaps", "sounds", "loc" };

/* ---------- small helpers */

static int launcher_is_active;

int desktop_launcher_active(void)
{
	return launcher_is_active;
}

int desktop_launcher_wanted(void)
{
	const char *network_test = SDL_getenv("HALO_NETWORK_TEST");

	return config_boolean("launcher.show") && !config_boolean("debug.hidden_window") &&
		!(config_real("debug.exit_after") > 0.0) && !*config_string("debug.menu_open") &&
		!(network_test && *network_test);
}

static void path_join(char *out, size_t size, const char *a, const char *b)
{
	size_t length = strlen(a);
	int separator = length && (a[length - 1] == '/' || a[length - 1] == '\\');

	snprintf(out, size, "%s%s%s", a, separator ? "" : LAUNCHER_SEPARATOR, b);
}

static int path_type(const char *path, Uint64 *size)
{
	SDL_PathInfo info;

	if (!SDL_GetPathInfo(path, &info))
		return SDL_PATHTYPE_NONE;
	if (size)
		*size = info.size;
	return info.type;
}

static int file_exists(const char *path)
{
	return path_type(path, NULL) == SDL_PATHTYPE_FILE;
}

/* ModInstaller.java's move: nothing when there is nothing to move; a file
there already is replaced */
static int move_path(const char *from, const char *to, char *error, size_t size)
{
	if (path_type(from, NULL) == SDL_PATHTYPE_NONE)
		return 1;
	if (SDL_RenamePath(from, to))
		return 1;
	if (path_type(to, NULL) == SDL_PATHTYPE_FILE && SDL_RemovePath(to) && SDL_RenamePath(from, to))
		return 1;
	snprintf(error, size, "Could not move %s to %s (%s).", from, to, SDL_GetError());
	return 0;
}

static int touch_file(const char *path)
{
	SDL_IOStream *io = SDL_IOFromFile(path, "wb");

	if (!io)
		return 0;
	SDL_WriteIO(io, "\n", 1);
	return SDL_CloseIO(io);
}

static int lower_equals(const char *a, const char *b)
{
	for (; *a && *b; a++, b++)
	{
		char x = *a >= 'A' && *a <= 'Z' ? (char)(*a + 32) : *a;
		char y = *b >= 'A' && *b <= 'Z' ? (char)(*b + 32) : *b;
		if (x != y)
			return 0;
	}
	return !*a && !*b;
}

/* the embedded file of that name, NUL-terminated (a copy), or NULL */
static char *launcher_file_text(const char *name)
{
	unsigned int index;

	for (index = 0; index < desktop_launcher_file_count; index++)
	{
		const struct desktop_launcher_file *file = &desktop_launcher_files[index];
		if (file->name && !strcmp(file->name, name))
		{
			char *text = malloc(file->size + 1);
			if (!text)
				return NULL;
			memcpy(text, file->data, file->size);
			text[file->size] = '\0';
			return text;
		}
	}
	return NULL;
}

/* a recipe's value ("file.a10.map.sha256"), or "" */
static void recipe_value(const char *recipe, const char *key, char *out, size_t size)
{
	size_t key_length = strlen(key);
	const char *line = recipe;

	out[0] = '\0';
	while (line && *line)
	{
		const char *end = strchr(line, '\n');
		size_t length = end ? (size_t)(end - line) : strlen(line);
		if (length > key_length && !strncmp(line, key, key_length) && line[key_length] == '=')
		{
			size_t value = length - key_length - 1;
			if (value && line[key_length + value] == '\r')
				value--;
			if (value >= size)
				value = size - 1;
			memcpy(out, line + key_length + 1, value);
			out[value] = '\0';
			return;
		}
		line = end ? end + 1 : NULL;
	}
}

/* the file's SHA-256, as 64 hex digits; progress over bytes done */
static int file_sha256(const char *path, char hex[65], void (*progress)(void *, Uint64), void *context)
{
	static unsigned char buffer[1 << 20];
	struct mcc_sha256 sha;
	unsigned char digest[32];
	SDL_IOStream *io = SDL_IOFromFile(path, "rb");
	Uint64 done = 0;
	size_t got;
	int index;

	if (!io)
		return 0;
	mcc_sha256_begin(&sha);
	while ((got = SDL_ReadIO(io, buffer, sizeof(buffer))) > 0)
	{
		mcc_sha256_add(&sha, buffer, (int)got);
		done += got;
		if (progress)
			progress(context, done);
	}
	SDL_CloseIO(io);
	mcc_sha256_end(&sha, digest);
	for (index = 0; index < 32; index++)
		snprintf(hex + index * 2, 3, "%02x", digest[index]);
	return 1;
}

/* ---------- the work done off the window's thread (extracting, hashing,
copying, swapping), its progress shown */

enum
{
	JOB_NONE,
	JOB_IMPORT_IMAGE,
	JOB_VERIFY,
	JOB_MOD_IMPORT,
	JOB_MOD_IN,
	JOB_MOD_OUT,
	JOB_UPDATES,
	/* Test73: the saves in from a .zip or a folder, out as a .zip (job_saves) */
	JOB_SAVES_IMPORT_ZIP,
	JOB_SAVES_IMPORT_FOLDER,
	JOB_SAVES_EXPORT,
};

static struct
{
	SDL_Mutex *lock;
	SDL_Thread *thread;
	int kind, running, finished, ok, mod;
	char path[LAUNCHER_PATH], root[LAUNCHER_PATH];
	char step[256], result[1024];
	double fraction;
	Uint64 base, total;
} job;

static void job_progress(const char *step, double fraction)
{
	SDL_LockMutex(job.lock);
	if (step)
		snprintf(job.step, sizeof(job.step), "%s", step);
	job.fraction = fraction < 0.0 ? 0.0 : fraction > 1.0 ? 1.0 : fraction;
	SDL_UnlockMutex(job.lock);
}

static void job_bytes(void *context, Uint64 done)
{
	(void)context;
	if (job.total)
		job_progress(NULL, (double)(job.base + done) / (double)job.total);
}

static void job_extract_progress(void *context, const char *file, unsigned long long done, unsigned long long total)
{
	char step[256];
	(void)context;
	snprintf(step, sizeof(step), "Extracting %s (%llu of %llu MB)", file, done >> 20, total >> 20);
	job_progress(step, total ? (double)done / (double)total * 0.8 : 0.0);
}

/* ---------- the game data: the maps folder, and library.sha256 beside it
("# image <path>", then "<sha256> <size> <name>" a map) */

struct map_list
{
	char names[64][96];
	int count;
};

static SDL_EnumerationResult SDLCALL list_maps(void *userdata, const char *dirname, const char *fname)
{
	struct map_list *list = userdata;
	size_t length = strlen(fname);
	(void)dirname;
	if (length > 4 && lower_equals(fname + length - 4, ".map") && list->count < 64)
		snprintf(list->names[list->count++], sizeof(list->names[0]), "%s", fname);
	return SDL_ENUM_CONTINUE;
}

static int library_record(const char *root, const char *image, char *error, size_t size)
{
	char maps[LAUNCHER_PATH], manifest[LAUNCHER_PATH], path[LAUNCHER_PATH], line[512];
	struct map_list list;
	SDL_IOStream *io;
	int index;
	Uint64 total = 0, bytes;

	memset(&list, 0, sizeof(list));
	path_join(maps, sizeof(maps), root, "maps");
	SDL_EnumerateDirectory(maps, list_maps, &list);
	if (!list.count)
	{
		snprintf(error, size, "No maps in %s.", maps);
		return 0;
	}
	for (index = 0; index < list.count; index++)
	{
		path_join(path, sizeof(path), maps, list.names[index]);
		if (path_type(path, &bytes) == SDL_PATHTYPE_FILE)
			total += bytes;
	}
	path_join(manifest, sizeof(manifest), root, "library.sha256");
	io = SDL_IOFromFile(manifest, "wb");
	if (!io)
	{
		snprintf(error, size, "Could not write %s.", manifest);
		return 0;
	}
	snprintf(line, sizeof(line), "# image %s\n", image ? image : "");
	SDL_WriteIO(io, line, strlen(line));
	job.base = 0;
	job.total = total;
	for (index = 0; index < list.count; index++)
	{
		char hex[65], step[256];
		path_join(path, sizeof(path), maps, list.names[index]);
		snprintf(step, sizeof(step), "Recording %s", list.names[index]);
		job_progress(step, job.total ? (double)job.base / (double)job.total : 0.0);
		if (path_type(path, &bytes) != SDL_PATHTYPE_FILE || !file_sha256(path, hex, job_bytes, NULL))
			continue;
		job.base += bytes;
		snprintf(line, sizeof(line), "%s %llu %s\n", hex, (unsigned long long)bytes, list.names[index]);
		SDL_WriteIO(io, line, strlen(line));
	}
	SDL_CloseIO(io);
	return 1;
}

/* the image recorded in library.sha256, or "" */
static void library_image(const char *root, char *image, size_t size)
{
	char manifest[LAUNCHER_PATH];
	char *text;

	image[0] = '\0';
	path_join(manifest, sizeof(manifest), root, "library.sha256");
	text = SDL_LoadFile(manifest, NULL);
	if (text)
	{
		if (!strncmp(text, "# image ", 8))
		{
			size_t length = strcspn(text + 8, "\r\n");
			if (length >= size)
				length = size - 1;
			memcpy(image, text + 8, length);
			image[length] = '\0';
		}
		SDL_free(text);
	}
}

static int job_verify(const char *root, char *result, size_t size)
{
	char manifest[LAUNCHER_PATH], maps[LAUNCHER_PATH];
	char *text, *line;
	int checked = 0, bad = 0, missing = 0;
	char first_bad[128] = "";
	Uint64 total = 0;

	path_join(manifest, sizeof(manifest), root, "library.sha256");
	path_join(maps, sizeof(maps), root, "maps");
	text = SDL_LoadFile(manifest, NULL);
	if (!text)
	{
		/* no record yet: these maps become it */
		if (!library_record(root, "", result, size))
			return 0;
		snprintf(result, size, "There was no record of these maps yet: their checksums are recorded now, "
			"and VERIFY checks them against it from now on.");
		return 1;
	}
	for (line = text; line && *line; line = strchr(line, '\n') ? strchr(line, '\n') + 1 : NULL)
	{
		char hex[65], name[128];
		unsigned long long bytes;
		if (*line != '#' && sscanf(line, "%64s %llu %127s", hex, &bytes, name) == 3)
			total += bytes;
	}
	job.base = 0;
	job.total = total;
	for (line = text; line && *line; line = strchr(line, '\n') ? strchr(line, '\n') + 1 : NULL)
	{
		char hex[65], name[128], path[LAUNCHER_PATH], actual[65], step[256];
		unsigned long long bytes;
		Uint64 size_now;
		if (*line == '#' || sscanf(line, "%64s %llu %127s", hex, &bytes, name) != 3)
			continue;
		path_join(path, sizeof(path), maps, name);
		snprintf(step, sizeof(step), "Checking %s", name);
		job_progress(step, job.total ? (double)job.base / (double)job.total : 0.0);
		checked++;
		if (path_type(path, &size_now) != SDL_PATHTYPE_FILE)
		{
			missing++;
			if (!first_bad[0]) snprintf(first_bad, sizeof(first_bad), "%s (missing)", name);
		}
		else if (size_now != bytes || !file_sha256(path, actual, job_bytes, NULL) || strcmp(actual, hex))
		{
			bad++;
			if (!first_bad[0]) snprintf(first_bad, sizeof(first_bad), "%s (changed)", name);
		}
		job.base += bytes;
	}
	SDL_free(text);
	if (!bad && !missing)
		snprintf(result, size, "All %d maps are as they were imported.", checked);
	else
		snprintf(result, size, "%d of %d maps are missing or changed, %s first. REPAIR extracts them again "
			"from the disc image.", bad + missing, checked, first_bad);
	return !bad && !missing;
}

/* the disc image's maps into root/maps (aside the old ones, back if it fails) */
static int job_import_image(const char *image, const char *root, char *result, size_t size)
{
	char maps[LAUNCHER_PATH], aside[LAUNCHER_PATH], error[512];
	int had = 0, ok;

	path_join(maps, sizeof(maps), root, "maps");
	path_join(aside, sizeof(aside), root, "maps.replaced");
	if (path_type(maps, NULL) == SDL_PATHTYPE_DIRECTORY)
	{
		if (path_type(aside, NULL) != SDL_PATHTYPE_NONE)
		{
			snprintf(result, size, "%s is there from an earlier repair: move or delete it first.", aside);
			return 0;
		}
		if (!SDL_RenamePath(maps, aside))
		{
			snprintf(result, size, "Could not put the maps folder aside (%s).", SDL_GetError());
			return 0;
		}
		had = 1;
	}
	error[0] = '\0';
	ok = xiso_extract_maps(image, root, job_extract_progress, NULL, error, sizeof(error)) != 0;
	if (!ok)
	{
		if (had)
			SDL_RenamePath(aside, maps);
		snprintf(result, size, "%s", error[0] ? error : "The disc image could not be read.");
		return 0;
	}
	if (had)
	{
		/* the old maps go (the new ones are whole) */
		struct map_list list;
		char path[LAUNCHER_PATH];
		int index;
		memset(&list, 0, sizeof(list));
		SDL_EnumerateDirectory(aside, list_maps, &list);
		for (index = 0; index < list.count; index++)
		{
			path_join(path, sizeof(path), aside, list.names[index]);
			SDL_RemovePath(path);
		}
		path_join(path, sizeof(path), aside, "loading.tga");
		SDL_RemovePath(path);
		SDL_RemovePath(aside);
	}
	if (!library_record(root, image, result, size))
		return 0;
	snprintf(result, size, "The maps are in %s%smaps, and their checksums recorded.", root, LAUNCHER_SEPARATOR);
	return 1;
}

/* ---------- the campaigns: the folders ModInstaller.java keeps */

static void mod_path(char *out, size_t size, const char *root, const char *a, const char *b, const char *c)
{
	char first[LAUNCHER_PATH], second[LAUNCHER_PATH];
	path_join(first, sizeof(first), root, a);
	if (!b)
	{
		snprintf(out, size, "%s", first);
		return;
	}
	path_join(second, sizeof(second), first, b);
	if (!c)
		snprintf(out, size, "%s", second);
	else
		path_join(out, size, second, c);
}

static int mod_installed(const char *root, const struct launcher_mod *mod)
{
	char marker[LAUNCHER_PATH], name[128];
	snprintf(name, sizeof(name), "%s.on", mod->id);
	mod_path(marker, sizeof(marker), root, "mods", name, NULL);
	if (file_exists(marker))
		return 1;
	snprintf(name, sizeof(name), "%s.changing", mod->id);
	mod_path(marker, sizeof(marker), root, "mods", name, NULL);
	return file_exists(marker);
}

int desktop_launcher_mod_map(const char *root, const char *file_name)
{
	int mod, index;

	if (!root || !file_name)
		return 0;
	for (mod = 0; mod < (int)(sizeof(launcher_mods) / sizeof(launcher_mods[0])); mod++)
	{
		if (!mod_installed(root, &launcher_mods[mod]))
			continue;
		for (index = 0; index < launcher_mods[mod].map_count; index++)
		{
			char name[128];
			snprintf(name, sizeof(name), "%s%s", launcher_mods[mod].maps[index].name, launcher_mods[mod].extension);
			if (!SDL_strcasecmp(name, file_name))
				return 1;
		}
	}
	return 0;
}

/* the files a campaign needs, each with its place and its recipe's size and
hash: its maps, then its resource maps (its own, or Custom Edition's) */
struct mod_file
{
	char name[96], target[LAUNCHER_PATH], hash[65];
	Uint64 size;
};

static int mod_files(const char *root, const struct launcher_mod *mod, struct mod_file *files)
{
	char recipe_name[96], key[160], value[96];
	char *recipe;
	int count = 0, index;

	snprintf(recipe_name, sizeof(recipe_name), "campaigns/%s.properties", mod->id);
	recipe = launcher_file_text(recipe_name);
	if (!recipe)
		return 0;
	for (index = 0; index < mod->map_count; index++)
	{
		struct mod_file *file = &files[count++];
		char maps[LAUNCHER_PATH];
		snprintf(file->name, sizeof(file->name), "%s%s", mod->maps[index].name, mod->extension);
		mod_path(maps, sizeof(maps), root, "mods", mod->id, "maps");
		path_join(file->target, sizeof(file->target), maps, file->name);
	}
	for (index = 0; index < 3; index++)
	{
		struct mod_file *file = &files[count++];
		if (mod->data_files)
		{
			char folder[LAUNCHER_PATH];
			snprintf(file->name, sizeof(file->name), "%s-%s.map", mod->data_files, launcher_resources[index]);
			mod_path(folder, sizeof(folder), root, "mods", mod->id, "data_files");
			path_join(file->target, sizeof(file->target), folder, file->name);
		}
		else
		{
			char folder[LAUNCHER_PATH];
			snprintf(file->name, sizeof(file->name), "%s.map", launcher_resources[index]);
			mod_path(folder, sizeof(folder), root, "mods", "ce", NULL);
			path_join(file->target, sizeof(file->target), folder, file->name);
		}
	}
	for (index = 0; index < count; index++)
	{
		snprintf(key, sizeof(key), "file.%s.size", files[index].name);
		recipe_value(recipe, key, value, sizeof(value));
		files[index].size = (Uint64)strtoull(value, NULL, 10);
		snprintf(key, sizeof(key), "file.%s.sha256", files[index].name);
		recipe_value(recipe, key, files[index].hash, sizeof(files[index].hash));
	}
	free(recipe);
	return count;
}

/* whether the campaign's files are all here, whole (out of the game or in it) */
static int mod_ready(const char *root, const struct launcher_mod *mod, int *have, int *need)
{
	struct mod_file files[16];
	int count = mod_files(root, mod, files), index, present = 0, installed = mod_installed(root, mod);

	for (index = 0; index < count; index++)
	{
		Uint64 size = 0;
		int whole = path_type(files[index].target, &size) == SDL_PATHTYPE_FILE && size == files[index].size;
		if (!whole && installed)
		{
			/* in the game: the maps (and resource maps) are in maps/ */
			char in_game[LAUNCHER_PATH], maps[LAUNCHER_PATH];
			path_join(maps, sizeof(maps), root, "maps");
			if (index >= mod->map_count && mod->data_files)
			{
				char folder[LAUNCHER_PATH];
				path_join(folder, sizeof(folder), maps, "data_files");
				path_join(in_game, sizeof(in_game), folder, files[index].name);
			}
			else
				path_join(in_game, sizeof(in_game), maps, files[index].name);
			whole = path_type(in_game, &size) == SDL_PATHTYPE_FILE && size == files[index].size;
		}
		present += whole;
	}
	if (have) *have = present;
	if (need) *need = count;
	return count && present == count;
}

/* the player's folder: every file a campaign needs, wherever it is in it
(three folders deep), by its name */
struct found_files
{
	struct mod_file *files;
	int count, depth;
	char found[16][LAUNCHER_PATH];
};

static SDL_EnumerationResult SDLCALL find_mod_files(void *userdata, const char *dirname, const char *fname)
{
	struct found_files *found = userdata;
	char path[LAUNCHER_PATH];
	int index, type;

	path_join(path, sizeof(path), dirname, fname);
	type = path_type(path, NULL);
	if (type == SDL_PATHTYPE_DIRECTORY && found->depth < 3)
	{
		found->depth++;
		SDL_EnumerateDirectory(path, find_mod_files, found);
		found->depth--;
		return SDL_ENUM_CONTINUE;
	}
	if (type != SDL_PATHTYPE_FILE)
		return SDL_ENUM_CONTINUE;
	for (index = 0; index < found->count; index++)
	{
		const char *name = found->files[index].name;
		const char *dash = strchr(name, '-');
		/* the Altheros download's "-bitmaps.map" is alsthetic-bitmaps.map */
		if (!found->found[index][0] && (lower_equals(fname, name) || (dash && lower_equals(fname, dash))))
			snprintf(found->found[index], sizeof(found->found[index]), "%s", path);
	}
	return SDL_ENUM_CONTINUE;
}

static int copy_checked(const char *from, struct mod_file *file, char *error, size_t size)
{
	static unsigned char buffer[1 << 20];
	char partial[LAUNCHER_PATH], hex[65];
	SDL_IOStream *in, *out;
	struct mcc_sha256 sha;
	unsigned char digest[32];
	size_t got;
	Uint64 done = 0;
	int index;

	snprintf(partial, sizeof(partial), "%s.part", file->target);
	in = SDL_IOFromFile(from, "rb");
	out = in ? SDL_IOFromFile(partial, "wb") : NULL;
	if (!in || !out)
	{
		if (in) SDL_CloseIO(in);
		snprintf(error, size, "Could not copy %s.", file->name);
		return 0;
	}
	mcc_sha256_begin(&sha);
	while ((got = SDL_ReadIO(in, buffer, sizeof(buffer))) > 0)
	{
		if (SDL_WriteIO(out, buffer, got) != got)
			break;
		mcc_sha256_add(&sha, buffer, (int)got);
		done += got;
		job_bytes(NULL, done);
	}
	SDL_CloseIO(in);
	SDL_CloseIO(out);
	mcc_sha256_end(&sha, digest);
	for (index = 0; index < 32; index++)
		snprintf(hex + index * 2, 3, "%02x", digest[index]);
	if (done != file->size || strcmp(hex, file->hash))
	{
		SDL_RemovePath(partial);
		snprintf(error, size, "%s is not the supported version (its size or SHA-256 differ): kept out.", file->name);
		return 0;
	}
	return move_path(partial, file->target, error, size);
}

static void make_folders_for(const char *path)
{
	char folder[LAUNCHER_PATH];
	char *slash;
	snprintf(folder, sizeof(folder), "%s", path);
	slash = strrchr(folder, LAUNCHER_SEPARATOR[0]);
	if (slash)
	{
		*slash = '\0';
		SDL_CreateDirectory(folder);
	}
}

static int job_mod_import(const char *root, const struct launcher_mod *mod, const char *folder,
	char *result, size_t size)
{
	struct mod_file files[16];
	struct found_files found;
	int count = mod_files(root, mod, files), index, imported = 0, already = 0, missing = 0, rejected = 0;
	char error[512] = "", recipe_name[96], support[LAUNCHER_PATH];
	char *recipe;

	if (!count)
	{
		snprintf(result, size, "This build has no setup recipe for %s.", mod->title);
		return 0;
	}
	if (mod_installed(root, mod))
	{
		snprintf(result, size, "%s is in the game: put the original campaign back before importing again.", mod->title);
		return 0;
	}
	memset(&found, 0, sizeof(found));
	found.files = files;
	found.count = count;
	job_progress("Looking through the folder", 0.0);
	SDL_EnumerateDirectory(folder, find_mod_files, &found);
	job.total = 0;
	for (index = 0; index < count; index++)
		if (found.found[index][0])
			job.total += files[index].size;
	job.base = 0;
	for (index = 0; index < count; index++)
	{
		Uint64 size_now = 0;
		char hex[65], step[256];
		if (path_type(files[index].target, &size_now) == SDL_PATHTYPE_FILE && size_now == files[index].size &&
			file_sha256(files[index].target, hex, NULL, NULL) && !strcmp(hex, files[index].hash))
		{
			already++;
			continue;
		}
		if (!found.found[index][0])
		{
			missing++;
			continue;
		}
		snprintf(step, sizeof(step), "Copying and checking %s", files[index].name);
		job_progress(step, job.total ? (double)job.base / (double)job.total : 0.0);
		make_folders_for(files[index].target);
		if (copy_checked(found.found[index], &files[index], error, sizeof(error)))
			imported++;
		else
			rejected++;
		job.base += files[index].size;
	}
	/* the recipe beside the mod's files, as the Android app keeps it */
	snprintf(recipe_name, sizeof(recipe_name), "campaigns/%s.properties", mod->id);
	recipe = launcher_file_text(recipe_name);
	mod_path(support, sizeof(support), root, "mods", mod->id, "support.properties");
	if (recipe)
	{
		SDL_IOStream *io;
		make_folders_for(support);
		io = SDL_IOFromFile(support, "wb");
		if (io)
		{
			SDL_WriteIO(io, recipe, strlen(recipe));
			SDL_CloseIO(io);
		}
		free(recipe);
	}
	snprintf(result, size, "%d imported, %d already here, %d not in that folder%s%s%s",
		imported, already, missing, rejected ? ", " : ".", rejected ? error : "", "");
	return !rejected && !missing;
}

static int is_xbox_map(const char *path)
{
	unsigned char header[8];
	SDL_IOStream *io = SDL_IOFromFile(path, "rb");
	size_t got;
	if (!io)
		return 0;
	got = SDL_ReadIO(io, header, sizeof(header));
	SDL_CloseIO(io);
	/* the cache header 'head', little-endian, version 5 (the Xbox's) */
	return got == 8 && header[0] == 'd' && header[1] == 'a' && header[2] == 'e' && header[3] == 'h' &&
		header[4] == 5 && header[5] == 0 && header[6] == 0 && header[7] == 0;
}

/* ModInstaller.java's swapIn: the originals aside, the campaign's maps (and
their converted sounds) in, its resource maps in, its markers */
static int mod_swap_in(const char *root, const struct launcher_mod *mod, char *error, size_t size)
{
	char maps[LAUNCHER_PATH], originals[LAUNCHER_PATH], mod_maps[LAUNCHER_PATH], name[128];
	char game[LAUNCHER_PATH], original[LAUNCHER_PATH], modded[LAUNCHER_PATH], from[LAUNCHER_PATH], marker[LAUNCHER_PATH];
	int index;

	path_join(maps, sizeof(maps), root, "maps");
	mod_path(originals, sizeof(originals), root, "mods", "original", NULL);
	mod_path(mod_maps, sizeof(mod_maps), root, "mods", mod->id, "maps");
	SDL_CreateDirectory(originals);
	for (index = 0; index < mod->map_count; index++)
	{
		snprintf(name, sizeof(name), "%s.map", mod->maps[index].name);
		path_join(original, sizeof(original), originals, name);
		path_join(game, sizeof(game), maps, name);
		if (!mod->maps[index].extra && !file_exists(original) && !is_xbox_map(game))
		{
			snprintf(error, size, "The original Xbox campaign map %s is missing.", name);
			return 0;
		}
	}
	snprintf(name, sizeof(name), "%s.changing", mod->id);
	mod_path(marker, sizeof(marker), root, "mods", name, NULL);
	touch_file(marker);
	for (index = 0; index < mod->map_count; index++)
	{
		char audio_from[LAUNCHER_PATH], audio_to[LAUNCHER_PATH];
		snprintf(name, sizeof(name), "%s.map", mod->maps[index].name);
		path_join(game, sizeof(game), maps, name);
		path_join(original, sizeof(original), originals, name);
		snprintf(name, sizeof(name), "%s%s", mod->maps[index].name, mod->extension);
		path_join(modded, sizeof(modded), maps, name);
		path_join(from, sizeof(from), mod_maps, name);
		snprintf(audio_from, sizeof(audio_from), "%s.audio", from);
		snprintf(audio_to, sizeof(audio_to), "%s.audio", modded);
		if ((!mod->maps[index].extra && !file_exists(original) && !move_path(game, original, error, size)) ||
			!move_path(from, modded, error, size) || !move_path(audio_from, audio_to, error, size))
			return 0;
	}
	if (mod->data_files)
	{
		char game_data[LAUNCHER_PATH], mod_data[LAUNCHER_PATH];
		path_join(game_data, sizeof(game_data), maps, "data_files");
		mod_path(mod_data, sizeof(mod_data), root, "mods", mod->id, "data_files");
		SDL_CreateDirectory(game_data);
		for (index = 0; index < 3; index++)
		{
			snprintf(name, sizeof(name), "%s-%s.map", mod->data_files, launcher_resources[index]);
			path_join(from, sizeof(from), mod_data, name);
			path_join(game, sizeof(game), game_data, name);
			if (!move_path(from, game, error, size))
				return 0;
		}
	}
	else
	{
		/* Custom Edition's resource maps in (the originals' aside) */
		for (index = 0; index < 3; index++)
		{
			char kept[LAUNCHER_PATH];
			snprintf(name, sizeof(name), "%s.map", launcher_resources[index]);
			mod_path(kept, sizeof(kept), root, "mods", "ce", name);
			path_join(game, sizeof(game), maps, name);
			path_join(original, sizeof(original), originals, name);
			if (!file_exists(kept))
				continue;
			if ((file_exists(game) && !file_exists(original) && !move_path(game, original, error, size)) ||
				!move_path(kept, game, error, size))
				return 0;
		}
	}
	snprintf(name, sizeof(name), "%s.on", mod->id);
	mod_path(from, sizeof(from), root, "mods", name, NULL);
	touch_file(from);
	mod_path(from, sizeof(from), root, "mods", "custom_edition.on", NULL);
	touch_file(from);
	SDL_RemovePath(marker);
	return 1;
}

/* ModInstaller.java's restore: the campaign's maps out (kept, to go back in
at once), the originals back, its resource maps out, its markers gone */
static int mod_restore(const char *root, const struct launcher_mod *mod, char *error, size_t size)
{
	char maps[LAUNCHER_PATH], originals[LAUNCHER_PATH], mod_maps[LAUNCHER_PATH], name[128];
	char game[LAUNCHER_PATH], original[LAUNCHER_PATH], modded[LAUNCHER_PATH], to[LAUNCHER_PATH], marker[LAUNCHER_PATH];
	int index, yelo = strcmp(mod->extension, ".map") != 0;

	path_join(maps, sizeof(maps), root, "maps");
	mod_path(originals, sizeof(originals), root, "mods", "original", NULL);
	mod_path(mod_maps, sizeof(mod_maps), root, "mods", mod->id, "maps");
	for (index = 0; index < mod->map_count; index++)
	{
		snprintf(name, sizeof(name), "%s.map", mod->maps[index].name);
		path_join(original, sizeof(original), originals, name);
		path_join(game, sizeof(game), maps, name);
		if (!mod->maps[index].extra && !file_exists(original) && !is_xbox_map(game))
		{
			snprintf(error, size, "The original backup of %s is missing; the campaign's files are kept. "
				"Import the disc image again (GAME DATA) before retrying.", name);
			return 0;
		}
	}
	snprintf(name, sizeof(name), "%s.changing", mod->id);
	mod_path(marker, sizeof(marker), root, "mods", name, NULL);
	touch_file(marker);
	SDL_CreateDirectory(mod_maps);
	for (index = 0; index < mod->map_count; index++)
	{
		char audio_from[LAUNCHER_PATH], audio_to[LAUNCHER_PATH];
		snprintf(name, sizeof(name), "%s.map", mod->maps[index].name);
		path_join(game, sizeof(game), maps, name);
		path_join(original, sizeof(original), originals, name);
		snprintf(name, sizeof(name), "%s%s", mod->maps[index].name, mod->extension);
		path_join(modded, sizeof(modded), maps, name);
		path_join(to, sizeof(to), mod_maps, name);
		snprintf(audio_from, sizeof(audio_from), "%s.audio", modded);
		snprintf(audio_to, sizeof(audio_to), "%s.audio", to);
		if (file_exists(original) || mod->maps[index].extra || yelo)
		{
			if ((!yelo ? file_exists(original) || mod->maps[index].extra : file_exists(modded)) &&
				!move_path(modded, to, error, size))
				return 0;
			if (!move_path(audio_from, audio_to, error, size))
				return 0;
			if (file_exists(original) && !move_path(original, game, error, size))
				return 0;
		}
	}
	if (mod->data_files)
	{
		char game_data[LAUNCHER_PATH], mod_data[LAUNCHER_PATH];
		path_join(game_data, sizeof(game_data), maps, "data_files");
		mod_path(mod_data, sizeof(mod_data), root, "mods", mod->id, "data_files");
		SDL_CreateDirectory(mod_data);
		for (index = 0; index < 3; index++)
		{
			char from[LAUNCHER_PATH];
			snprintf(name, sizeof(name), "%s-%s.map", mod->data_files, launcher_resources[index]);
			path_join(from, sizeof(from), game_data, name);
			path_join(to, sizeof(to), mod_data, name);
			if (!move_path(from, to, error, size))
				return 0;
		}
	}
	else
	{
		char kept_folder[LAUNCHER_PATH];
		mod_path(kept_folder, sizeof(kept_folder), root, "mods", "ce", NULL);
		SDL_CreateDirectory(kept_folder);
		for (index = 0; index < 3; index++)
		{
			char kept[LAUNCHER_PATH];
			snprintf(name, sizeof(name), "%s.map", launcher_resources[index]);
			path_join(kept, sizeof(kept), kept_folder, name);
			path_join(game, sizeof(game), maps, name);
			path_join(original, sizeof(original), originals, name);
			if ((file_exists(game) && !file_exists(kept) && !move_path(game, kept, error, size)) ||
				(file_exists(original) && !move_path(original, game, error, size)))
				return 0;
		}
	}
	mod_path(to, sizeof(to), root, "mods", "custom_edition.on", NULL);
	SDL_RemovePath(to);
	snprintf(name, sizeof(name), "%s.on", mod->id);
	mod_path(to, sizeof(to), root, "mods", name, NULL);
	SDL_RemovePath(to);
	SDL_RemovePath(marker);
	return 1;
}

/* ---------- the fork's latest release (only when the player asks) */

static int job_updates(char *result, size_t size)
{
	char path[LAUNCHER_PATH], error[256], tag[96] = "";
	const char *base = SDL_GetBasePath();
	char *text, *at;

	path_join(path, sizeof(path), base ? base : ".", "latest-release.json");
	job_progress("Asking GitHub for the latest release", 0.3);
	/* (no more than 1 MiB of it, as updater.c's check) */
	if (!update_download("https://api.github.com/repos/" HALO_PORT_REPOSITORY "/releases/latest", path,
		1024ULL * 1024, NULL, NULL, error, sizeof(error)))
	{
		snprintf(result, size, "Could not reach GitHub (%s).", error);
		return 0;
	}
	text = SDL_LoadFile(path, NULL);
	SDL_RemovePath(path);
	if (!text || !(at = strstr(text, "\"tag_name\"")) || !(at = strchr(at + 10, '"')))
	{
		if (text) SDL_free(text);
		snprintf(result, size, "GitHub's answer had no release in it.");
		return 0;
	}
	{
		char *end = strchr(at + 1, '"');
		size_t length = end ? (size_t)(end - at - 1) : 0;
		if (length >= sizeof(tag)) length = sizeof(tag) - 1;
		memcpy(tag, at + 1, length);
		tag[length] = '\0';
	}
	SDL_free(text);
	if (strstr(tag, HALO_PORT_VERSION))
		snprintf(result, size, "The latest release is %s: this build is it.", tag);
	else
		snprintf(result, size, "The latest release is %s (this build: %s). OPEN THE RELEASES PAGE shows it and its files.",
			tag, HALO_PORT_VERSION);
	return 1;
}

/* ---------- the saves (Test73: save_transfer.c, as the Android launcher's
SaveTransfer.java): brought in from a .zip or a folder, the saves already
there kept first as a .zip in the save root's backups folder; taken out as a
.zip. The game is not running while the launcher is shown */

static int job_saves(int kind, const char *path, char *result, size_t size)
{
	const char *save_root = platform_save_root();
	char backups[LAUNCHER_PATH], zip[LAUNCHER_PATH];

	if (kind == JOB_SAVES_EXPORT)
	{
		size_t length = strlen(path);

		/* (a name typed without its .zip) */
		snprintf(zip, sizeof(zip), "%s%s", path, length >= 4 && lower_equals(path + length - 4, ".zip") ? "" : ".zip");
		job_progress("Exporting the saves", 0.5);
		return save_transfer_export(save_root, zip, result, size) >= 0;
	}
	path_join(backups, sizeof(backups), save_root, "backups");
	job_progress(kind == JOB_SAVES_IMPORT_FOLDER ? "Bringing the saves in from the folder" :
		"Bringing the saves in from the .zip", 0.5);
	return save_transfer_import(path, kind == JOB_SAVES_IMPORT_FOLDER, save_root, backups, result, size);
}

static int SDLCALL job_thread(void *data)
{
	char result[1024] = "";
	int ok = 0;
	(void)data;

	switch (job.kind)
	{
	case JOB_IMPORT_IMAGE: ok = job_import_image(job.path, job.root, result, sizeof(result)); break;
	case JOB_VERIFY: ok = job_verify(job.root, result, sizeof(result)); break;
	case JOB_MOD_IMPORT: ok = job_mod_import(job.root, &launcher_mods[job.mod], job.path, result, sizeof(result)); break;
	case JOB_MOD_IN:
	{
		int index;
		ok = 1;
		/* one campaign at a time: another in the game goes out first */
		for (index = 0; index < LAUNCHER_MOD_COUNT && ok; index++)
			if (index != job.mod && mod_installed(job.root, &launcher_mods[index]))
				ok = mod_restore(job.root, &launcher_mods[index], result, sizeof(result));
		if (ok && !mod_ready(job.root, &launcher_mods[job.mod], NULL, NULL))
		{
			snprintf(result, sizeof(result), "Some of %s's files are not here yet: IMPORT them first.", launcher_mods[job.mod].title);
			ok = 0;
		}
		if (ok)
			ok = mod_swap_in(job.root, &launcher_mods[job.mod], result, sizeof(result));
		if (ok)
			snprintf(result, sizeof(result), "%s is in the game. PLAY starts it (the game loads Custom Edition maps).",
				launcher_mods[job.mod].title);
		break;
	}
	case JOB_MOD_OUT:
		ok = mod_restore(job.root, &launcher_mods[job.mod], result, sizeof(result));
		if (ok)
			snprintf(result, sizeof(result), "The original campaign is back; %s stays here to go back in at once.",
				launcher_mods[job.mod].title);
		break;
	case JOB_UPDATES: ok = job_updates(result, sizeof(result)); break;
	case JOB_SAVES_IMPORT_ZIP:
	case JOB_SAVES_IMPORT_FOLDER:
	case JOB_SAVES_EXPORT: ok = job_saves(job.kind, job.path, result, sizeof(result)); break;
	}
	platform_log("launcher: %s", result);
	SDL_LockMutex(job.lock);
	snprintf(job.result, sizeof(job.result), "%s", result);
	job.ok = ok;
	job.finished = 1;
	SDL_UnlockMutex(job.lock);
	return 0;
}

static void job_start(int kind, int mod, const char *path)
{
	if (job.running)
		return;
	job.kind = kind;
	job.mod = mod;
	snprintf(job.path, sizeof(job.path), "%s", path ? path : "");
	job.running = 1;
	job.finished = 0;
	job.fraction = 0.0;
	job.step[0] = job.result[0] = '\0';
	job.thread = SDL_CreateThread(job_thread, "launcher job", NULL);
	if (!job.thread)
	{
		job.running = 0;
		snprintf(job.result, sizeof(job.result), "Could not start (%s).", SDL_GetError());
	}
}

/* ---------- the window: fonts, text, buttons */

struct launcher_font
{
	SDL_Texture *texture;
	stbtt_packedchar ascii[95], latin[96], punctuation[23];
	float size, ascent;
	int valid;
};

static struct
{
	SDL_Window *window;
	SDL_Renderer *renderer;
	struct launcher_font body, small, heading, title;
	SDL_Gamepad *gamepad;
	int page, mod, focus, focus_count, buttons, activated, clicked, back, mouse_moved, quit, play;
	int dialog_pending;
	float mouse_x, mouse_y, scroll;
	char status[1024];
	char dialog_path[LAUNCHER_PATH];
	SDL_AtomicInt dialog_done;
	int dialog_kind;
} ui;

enum { PAGE_HOME, PAGE_DATA, PAGE_MODS, PAGE_MOD, PAGE_SETTINGS, PAGE_VR, PAGE_NEWS, PAGE_UPDATES, PAGE_LOGS,
	PAGE_CONTROLS };

static const unsigned char *launcher_font_data(const char *file)
{
	unsigned int index;
	for (index = 0; index < text_hires_embedded_count; index++)
		if (text_hires_embedded[index].file && !strcmp(text_hires_embedded[index].file, file))
			return (const unsigned char *)text_hires_embedded[index].data;
	return NULL;
}

static void font_load(struct launcher_font *font, const char *file, float size)
{
	const unsigned char *data = launcher_font_data(file);
	unsigned char *alpha, *rgba;
	stbtt_pack_context pack;
	stbtt_pack_range ranges[3];
	stbtt_fontinfo info;
	int ascent, descent, gap, index;

	memset(font, 0, sizeof(*font));
	font->size = size;
	if (!data || !stbtt_InitFont(&info, data, stbtt_GetFontOffsetForIndex(data, 0)))
		return;
	stbtt_GetFontVMetrics(&info, &ascent, &descent, &gap);
	font->ascent = (float)ascent * stbtt_ScaleForPixelHeight(&info, size);
	alpha = calloc(LAUNCHER_ATLAS, LAUNCHER_ATLAS);
	rgba = malloc(LAUNCHER_ATLAS * LAUNCHER_ATLAS * 4);
	if (!alpha || !rgba || !stbtt_PackBegin(&pack, alpha, LAUNCHER_ATLAS, LAUNCHER_ATLAS, 0, 1, NULL))
	{
		free(alpha);
		free(rgba);
		return;
	}
	stbtt_PackSetOversampling(&pack, 2, 1);
	memset(ranges, 0, sizeof(ranges));
	ranges[0].font_size = size; ranges[0].first_unicode_codepoint_in_range = 32; ranges[0].num_chars = 95;
	ranges[0].chardata_for_range = font->ascii;
	ranges[1].font_size = size; ranges[1].first_unicode_codepoint_in_range = 160; ranges[1].num_chars = 96;
	ranges[1].chardata_for_range = font->latin;
	ranges[2].font_size = size; ranges[2].first_unicode_codepoint_in_range = 0x2010; ranges[2].num_chars = 23;
	ranges[2].chardata_for_range = font->punctuation;
	stbtt_PackFontRanges(&pack, data, 0, ranges, 3);
	stbtt_PackEnd(&pack);
	for (index = 0; index < LAUNCHER_ATLAS * LAUNCHER_ATLAS; index++)
	{
		rgba[index * 4 + 0] = rgba[index * 4 + 1] = rgba[index * 4 + 2] = 255;
		rgba[index * 4 + 3] = alpha[index];
	}
	font->texture = SDL_CreateTexture(ui.renderer, SDL_PIXELFORMAT_RGBA32, SDL_TEXTUREACCESS_STATIC,
		LAUNCHER_ATLAS, LAUNCHER_ATLAS);
	if (font->texture)
	{
		SDL_UpdateTexture(font->texture, NULL, rgba, LAUNCHER_ATLAS * 4);
		SDL_SetTextureBlendMode(font->texture, SDL_BLENDMODE_BLEND);
		font->valid = 1;
	}
	free(alpha);
	free(rgba);
}

/* the next character of UTF-8 text */
static unsigned int utf8_next(const char **text)
{
	const unsigned char *s = (const unsigned char *)*text;
	unsigned int code;

	if (s[0] < 0x80) { code = s[0]; *text += 1; }
	else if ((s[0] & 0xE0) == 0xC0 && s[1]) { code = ((s[0] & 0x1Fu) << 6) | (s[1] & 0x3Fu); *text += 2; }
	else if ((s[0] & 0xF0) == 0xE0 && s[1] && s[2]) { code = ((s[0] & 0x0Fu) << 12) | ((s[1] & 0x3Fu) << 6) | (s[2] & 0x3Fu); *text += 3; }
	else { code = '?'; *text += 1; }
	return code;
}

static const stbtt_packedchar *font_glyph(const struct launcher_font *font, unsigned int code, int *index)
{
	/* (the bullet, U+2022, and the dashes are in the punctuation range) */
	if (code >= 32 && code < 127) { *index = (int)(code - 32); return font->ascii; }
	if (code >= 160 && code < 256) { *index = (int)(code - 160); return font->latin; }
	if (code >= 0x2010 && code < 0x2010 + 23) { *index = (int)(code - 0x2010); return font->punctuation; }
	*index = '?' - 32;
	return font->ascii;
}

static float text_width(const struct launcher_font *font, const char *text, size_t length)
{
	const char *end = text + length;
	float x = 0.0f, y = 0.0f;

	while (*text && text < end)
	{
		int index;
		const stbtt_packedchar *chars = font_glyph(font, utf8_next(&text), &index);
		stbtt_aligned_quad quad;
		stbtt_GetPackedQuad(chars, LAUNCHER_ATLAS, LAUNCHER_ATLAS, index, &x, &y, &quad, 0);
	}
	return x;
}

static float text_draw(const struct launcher_font *font, float x, float y, const char *text, Uint32 color)
{
	float pen = x, baseline = y + font->ascent;

	if (!font->valid)
	{
		SDL_SetRenderDrawColor(ui.renderer, (Uint8)(color >> 24), (Uint8)(color >> 16), (Uint8)(color >> 8), 255);
		SDL_RenderDebugText(ui.renderer, x, y, text);
		return (float)strlen(text) * 8.0f;
	}
	SDL_SetTextureColorMod(font->texture, (Uint8)(color >> 24), (Uint8)(color >> 16), (Uint8)(color >> 8));
	SDL_SetTextureAlphaMod(font->texture, (Uint8)color);
	while (*text)
	{
		int index;
		unsigned int code = utf8_next(&text);
		const stbtt_packedchar *chars;
		stbtt_aligned_quad quad;
		SDL_FRect source, target;
		if (code == '\n')
			break;
		chars = font_glyph(font, code, &index);
		stbtt_GetPackedQuad(chars, LAUNCHER_ATLAS, LAUNCHER_ATLAS, index, &pen, &baseline, &quad, 0);
		source.x = quad.s0 * LAUNCHER_ATLAS; source.y = quad.t0 * LAUNCHER_ATLAS;
		source.w = (quad.s1 - quad.s0) * LAUNCHER_ATLAS; source.h = (quad.t1 - quad.t0) * LAUNCHER_ATLAS;
		target.x = quad.x0; target.y = quad.y0; target.w = quad.x1 - quad.x0; target.h = quad.y1 - quad.y0;
		if (target.w > 0.0f && target.h > 0.0f)
			SDL_RenderTexture(ui.renderer, font->texture, &source, &target);
	}
	return pen - x;
}

/* text wrapped to a width, from y; returns the height it took (drawn only
when draw is set, between top and bottom) */
static float text_wrapped(const struct launcher_font *font, float x, float y, float width, const char *text,
	Uint32 color, int draw, float top, float bottom)
{
	float line_height = font->size * 1.25f, start = y;
	const char *line = text;

	while (line && *line)
	{
		const char *paragraph_end = strchr(line, '\n');
		size_t paragraph = paragraph_end ? (size_t)(paragraph_end - line) : strlen(line);
		const char *at = line, *end = line + paragraph;

		if (!paragraph)
			y += line_height * 0.6f;
		while (at < end)
		{
			const char *fit = at, *space = NULL, *probe = at;
			char buffer[1024];
			size_t length;
			while (probe < end)
			{
				const char *next = probe;
				utf8_next(&next);
				if (text_width(font, at, (size_t)(next - at)) > width)
					break;
				if (*probe == ' ')
					space = probe;
				probe = next;
			}
			fit = probe >= end ? end : space && space > at ? space : probe > at ? probe : at + 1;
			length = (size_t)(fit - at);
			if (length >= sizeof(buffer)) length = sizeof(buffer) - 1;
			memcpy(buffer, at, length);
			buffer[length] = '\0';
			if (draw && y + line_height >= top && y <= bottom)
				text_draw(font, x, y, buffer, color);
			y += line_height;
			at = fit;
			while (at < end && *at == ' ')
				at++;
		}
		line = paragraph_end ? paragraph_end + 1 : NULL;
	}
	return y - start;
}

#define COLOR_TEXT 0xE6EDF2FFu
#define COLOR_DIM 0x9AAAB8FFu
#define COLOR_BLUE 0x5FB7FFFFu
#define COLOR_GOLD 0xFFC85AFFu
#define COLOR_RED 0xFF7A6AFFu
#define COLOR_GREEN 0x8CDC8CFFu

static void fill(float x, float y, float w, float h, Uint32 color)
{
	SDL_FRect rect = { x, y, w, h };
	SDL_SetRenderDrawColor(ui.renderer, (Uint8)(color >> 24), (Uint8)(color >> 16), (Uint8)(color >> 8), (Uint8)color);
	SDL_RenderFillRect(ui.renderer, &rect);
}

static void frame_rect(float x, float y, float w, float h, Uint32 color)
{
	SDL_FRect rect = { x, y, w, h };
	SDL_SetRenderDrawColor(ui.renderer, (Uint8)(color >> 24), (Uint8)(color >> 16), (Uint8)(color >> 8), (Uint8)color);
	SDL_RenderRect(ui.renderer, &rect);
}

/* a button: drawn, focused by the arrows or the pointer, pressed by Enter,
A or a click; TRUE the frame it is pressed */
static int button(float x, float y, float w, float h, const char *label, int enabled)
{
	int index = ui.buttons++;
	int hover = ui.mouse_x >= x && ui.mouse_x < x + w && ui.mouse_y >= y && ui.mouse_y < y + h;
	int focused;
	float label_width;

	if (hover && ui.mouse_moved && enabled)
		ui.focus = index;
	focused = ui.focus == index;
	fill(x, y, w, h, !enabled ? 0x1A2028FFu : focused ? 0x1E4E7EFFu : 0x16283AFFu);
	frame_rect(x, y, w, h, focused && enabled ? COLOR_BLUE : 0x2C4A66FFu);
	label_width = text_width(&ui.body, label, strlen(label));
	text_draw(&ui.body, x + (w - label_width) * 0.5f, y + (h - ui.body.size) * 0.5f - 2.0f, label,
		enabled ? COLOR_TEXT : 0x5A6672FFu);
	return enabled && ((hover && ui.clicked) || (focused && ui.activated));
}

/* ---------- the dialogs (SDL's, answered through events) */

static void SDLCALL dialog_answer(void *userdata, const char * const *files, int filter)
{
	(void)userdata;
	(void)filter;
	ui.dialog_path[0] = '\0';
	if (files && files[0])
		snprintf(ui.dialog_path, sizeof(ui.dialog_path), "%s", files[0]);
	SDL_SetAtomicInt(&ui.dialog_done, 1);
}

static void dialog_image(int kind)
{
	static const SDL_DialogFileFilter filters[] = { { "Xbox disc images", "iso;xiso" }, { "All files", "*" } };
	SDL_SetAtomicInt(&ui.dialog_done, 0);
	ui.dialog_kind = kind;
	ui.dialog_pending = 1;
	SDL_ShowOpenFileDialog(dialog_answer, NULL, ui.window, filters, 2, NULL, false);
}

static void dialog_folder(int kind)
{
	SDL_SetAtomicInt(&ui.dialog_done, 0);
	ui.dialog_kind = kind;
	ui.dialog_pending = 1;
	SDL_ShowOpenFolderDialog(dialog_answer, NULL, ui.window, NULL, false);
}

/* Test73: a .zip of saves to bring in, or where to write one */
static void dialog_zip(int kind, int save)
{
	static const SDL_DialogFileFilter filters[] = { { "Zip archives", "zip" }, { "All files", "*" } };
	SDL_SetAtomicInt(&ui.dialog_done, 0);
	ui.dialog_kind = kind;
	ui.dialog_pending = 1;
	if (save)
		SDL_ShowSaveFileDialog(dialog_answer, NULL, ui.window, filters, 1, NULL);
	else
		SDL_ShowOpenFileDialog(dialog_answer, NULL, ui.window, filters, 2, NULL, false);
}

/* ---------- the data root and the builds */

static int data_root_maps(char *root, size_t size, int *map_count)
{
	char maps[LAUNCHER_PATH];
	struct map_list list;

	snprintf(root, size, "%s", platform_data_root());
	path_join(maps, sizeof(maps), root, "maps");
	memset(&list, 0, sizeof(list));
	if (path_type(maps, NULL) == SDL_PATHTYPE_DIRECTORY)
		SDL_EnumerateDirectory(maps, list_maps, &list);
	if (map_count)
		*map_count = list.count;
	return list.count > 0;
}

static void other_build(char *path, size_t size)
{
	const char *base = SDL_GetBasePath();
#ifdef HALO_VR
	path_join(path, size, base ? base : ".", LAUNCHER_FLAT_EXE);
#else
	path_join(path, size, base ? base : ".", LAUNCHER_VR_EXE);
#endif
}

/* this build or the other, started anew (the launcher not shown again,
Custom Edition maps loading when a campaign is in); FALSE if it could not */
static int start_build(const char *path, int custom_edition)
{
	SDL_setenv_unsafe("HALO_LAUNCHER", "0", 1);
	if (custom_edition)
		SDL_setenv_unsafe("HALO_CUSTOM_EDITION", "1", 1);
	platform_log("launcher: starting %s%s", path, custom_edition ? " with Custom Edition maps" : "");
	return update_launch(path);
}

/* ---------- the pages */

static int custom_edition_marked(const char *root)
{
	char marker[LAUNCHER_PATH];
	mod_path(marker, sizeof(marker), root, "mods", "custom_edition.on", NULL);
	return file_exists(marker);
}

static void page_heading(const char *heading)
{
	text_draw(&ui.heading, 80.0f, 40.0f, heading, COLOR_BLUE);
	fill(80.0f, 84.0f, LAUNCHER_WIDTH - 160.0f, 2.0f, 0x2C4A66FFu);
}

static int back_button(void)
{
	return button(80.0f, LAUNCHER_HEIGHT - 90.0f, 200.0f, 50.0f, "BACK", 1) || ui.back;
}

static void page_home(void)
{
	char root[LAUNCHER_PATH], other[LAUNCHER_PATH], line[512];
	int maps = 0, has = data_root_maps(root, sizeof(root), &maps), index, installed = -1;
	float y = 330.0f;

	text_draw(&ui.title, 80.0f, 60.0f, "HALO: COMBAT EVOLVED", COLOR_TEXT);
#ifdef HALO_VR
	text_draw(&ui.heading, 80.0f, 130.0f,
#ifdef _WIN32
		"WINDOWS \xE2\x80\xA2 PC VR",
#else
		"LINUX \xE2\x80\xA2 PC VR",
#endif
		COLOR_BLUE);
#else
	text_draw(&ui.heading, 80.0f, 130.0f,
#ifdef _WIN32
		"WINDOWS \xE2\x80\xA2 KEYBOARD, MOUSE & GAMEPAD",
#else
		"LINUX \xE2\x80\xA2 KEYBOARD, MOUSE & GAMEPAD",
#endif
		COLOR_BLUE);
#endif
	text_draw(&ui.small, 80.0f, 172.0f, HALO_PORT_VERSION " \xE2\x80\xA2 community release", COLOR_DIM);
	if (has)
		snprintf(line, sizeof(line), "Game data: %d maps in %s", maps, root);
	else
		snprintf(line, sizeof(line), "Game data: none yet. GAME DATA imports it from your Xbox disc image (.iso).");
	text_draw(&ui.body, 80.0f, 220.0f, line, has ? COLOR_GREEN : COLOR_GOLD);
	for (index = 0; index < LAUNCHER_MOD_COUNT; index++)
		if (mod_installed(root, &launcher_mods[index]))
			installed = index;
	snprintf(line, sizeof(line), "Campaign: %s", installed >= 0 ? launcher_mods[installed].title : "the original Halo campaign");
	text_draw(&ui.body, 80.0f, 254.0f, line, COLOR_TEXT);

	if (button(80.0f, y, 360.0f, 64.0f, "PLAY", has))
		ui.play = 1;
	other_build(other, sizeof(other));
	if (file_exists(other))
	{
#ifdef HALO_VR
		if (button(460.0f, y, 360.0f, 64.0f, "PLAY ON THE SCREEN", has))
#else
		if (button(460.0f, y, 360.0f, 64.0f, "PLAY IN VR", has))
#endif
		{
			if (start_build(other, custom_edition_marked(root)))
				ui.quit = 2;
			else
				snprintf(ui.status, sizeof(ui.status), "Could not start %s.", other);
		}
	}
	y += 90.0f;
	if (button(80.0f, y, 360.0f, 56.0f, "GAME DATA", 1)) { ui.page = PAGE_DATA; ui.focus = 0; }
	if (button(460.0f, y, 360.0f, 56.0f, "CUSTOM CAMPAIGNS", 1)) { ui.page = PAGE_MODS; ui.focus = 0; }
	y += 72.0f;
	if (button(80.0f, y, 360.0f, 56.0f, "SETTINGS", 1)) { ui.page = PAGE_SETTINGS; ui.focus = 0; }
#ifdef HALO_VR
	if (button(460.0f, y, 360.0f, 56.0f, "VR HEADSETS", 1)) { ui.page = PAGE_VR; ui.focus = 0; }
#else
	if (button(460.0f, y, 360.0f, 56.0f, "PC VR", 1)) { ui.page = PAGE_VR; ui.focus = 0; }
#endif
	/* Test73b: every button of each controller (page_controls) */
	if (button(840.0f, y, 360.0f, 56.0f, "CONTROLS", 1)) { ui.page = PAGE_CONTROLS; ui.focus = 0; ui.scroll = 0.0f; }
	y += 72.0f;
	if (button(80.0f, y, 360.0f, 56.0f, "WHAT'S NEW", 1)) { ui.page = PAGE_NEWS; ui.focus = 0; ui.scroll = 0.0f; }
	if (button(460.0f, y, 360.0f, 56.0f, "UPDATES", 1)) { ui.page = PAGE_UPDATES; ui.focus = 0; }
	y += 72.0f;
	if (button(80.0f, y, 360.0f, 56.0f, "QUIT", 1) || ui.back)
		ui.quit = 1;
	/* Test73b: where the logs are (page_logs) */
	if (button(460.0f, y, 360.0f, 56.0f, "LOGS", 1)) { ui.page = PAGE_LOGS; ui.focus = 0; }
}

static void page_data(void)
{
	char root[LAUNCHER_PATH], image[LAUNCHER_PATH], line[1200];
	int maps = 0, has = data_root_maps(root, sizeof(root), &maps);
	const char *base = SDL_GetBasePath();

	page_heading("GAME DATA");
	text_wrapped(&ui.body, 80.0f, 110.0f, LAUNCHER_WIDTH - 160.0f,
		"The game's data is the maps folder of an Xbox disc image of Halo: Combat Evolved (an .iso or .xiso "
		"you made from your own disc). It is extracted once, beside the game; halo.exe and halo-vr.exe share "
		"it, with the saves and the custom campaigns. Nothing of the game comes with this download.",
		COLOR_TEXT, 1, 0.0f, (float)LAUNCHER_HEIGHT);
	if (has)
		snprintf(line, sizeof(line), "%d maps in %s%smaps", maps, root, LAUNCHER_SEPARATOR);
	else
		snprintf(line, sizeof(line), "No maps folder yet. IMPORT puts it in %s.", base ? base : ".");
	text_draw(&ui.body, 80.0f, 250.0f, line, has ? COLOR_GREEN : COLOR_GOLD);
	library_image(has ? root : (base ? base : "."), image, sizeof(image));
	if (image[0])
	{
		snprintf(line, sizeof(line), "Imported from %s", image);
		text_draw(&ui.small, 80.0f, 284.0f, line, COLOR_DIM);
	}
	snprintf(job.root, sizeof(job.root), "%s", has ? root : (base ? base : "."));
	if (button(80.0f, 340.0f, 360.0f, 56.0f, has ? "IMPORT AGAIN FROM AN IMAGE" : "IMPORT FROM A DISC IMAGE", !job.running))
		dialog_image(JOB_IMPORT_IMAGE);
	if (button(460.0f, 340.0f, 300.0f, 56.0f, "VERIFY", has && !job.running))
		job_start(JOB_VERIFY, 0, NULL);
	if (button(780.0f, 340.0f, 300.0f, 56.0f, "REPAIR", has && !job.running))
	{
		if (image[0] && file_exists(image))
			job_start(JOB_IMPORT_IMAGE, 0, image);
		else
			dialog_image(JOB_IMPORT_IMAGE);
	}
	if (button(80.0f, 420.0f, 360.0f, 56.0f, "OPEN THE FOLDER", 1))
	{
		char url[LAUNCHER_PATH + 16];
		snprintf(url, sizeof(url), "file:///%s", has ? root : (base ? base : "."));
		SDL_OpenURL(url);
	}
	/* Test73: the saves (the player profiles, the campaign's checkpoint,
	Xbox save containers), in and out, as the Android launcher's */
	snprintf(line, sizeof(line), "SAVES \xE2\x80\xA2 %s", platform_save_root());
	text_draw(&ui.body, 80.0f, 500.0f, line, COLOR_TEXT);
	if (button(80.0f, 540.0f, 360.0f, 56.0f, "IMPORT SAVES (.ZIP)", !job.running))
		dialog_zip(JOB_SAVES_IMPORT_ZIP, 0);
	if (button(460.0f, 540.0f, 300.0f, 56.0f, "IMPORT SAVES (FOLDER)", !job.running))
		dialog_folder(JOB_SAVES_IMPORT_FOLDER);
	if (button(780.0f, 540.0f, 300.0f, 56.0f, "EXPORT SAVES (.ZIP)", !job.running))
		dialog_zip(JOB_SAVES_EXPORT, 1);
	text_draw(&ui.small, 80.0f, 608.0f, "An import keeps the saves already here first, as a .zip in the backups folder there.",
		COLOR_DIM);
	if (back_button() && !job.running) { ui.page = PAGE_HOME; ui.focus = 0; }
}

static void page_mods(void)
{
	char root[LAUNCHER_PATH], line[512];
	int index, have, need;
	float y = 120.0f;

	data_root_maps(root, sizeof(root), NULL);
	snprintf(job.root, sizeof(job.root), "%s", root);
	page_heading("CUSTOM CAMPAIGNS");
	for (index = 0; index < LAUNCHER_MOD_COUNT; index++)
	{
		const struct launcher_mod *mod = &launcher_mods[index];
		int installed = mod_installed(root, mod), ready = mod_ready(root, mod, &have, &need);
		if (button(80.0f, y, 640.0f, 56.0f, mod->title, 1)) { ui.page = PAGE_MOD; ui.mod = index; ui.focus = 0; }
		snprintf(line, sizeof(line), "%s \xE2\x80\xA2 %s", mod->status,
			installed ? "in the game now" : ready ? "files ready" : need ? "files not here yet" : "no recipe");
		text_draw(&ui.small, 740.0f, y + 16.0f, line, installed ? COLOR_GREEN : strncmp(mod->status, "Supported", 9) ? COLOR_GOLD : COLOR_DIM);
		y += 76.0f;
	}
	text_wrapped(&ui.small, 80.0f, y + 10.0f, LAUNCHER_WIDTH - 160.0f,
		"The same campaigns, folders and checks as the Quest and Android app: one library serves both. "
		"Each campaign's files come from where their authors published them; this launcher checks every one "
		"(its exact size and SHA-256) before it goes in.",
		COLOR_DIM, 1, 0.0f, (float)LAUNCHER_HEIGHT);
	if (back_button()) { ui.page = PAGE_HOME; ui.focus = 0; }
}

static void page_mod(void)
{
	const struct launcher_mod *mod = &launcher_mods[ui.mod];
	char root[LAUNCHER_PATH], line[512];
	int have = 0, need = 0, installed, ready;
	float y;

	data_root_maps(root, sizeof(root), NULL);
	snprintf(job.root, sizeof(job.root), "%s", root);
	installed = mod_installed(root, mod);
	ready = mod_ready(root, mod, &have, &need);
	page_heading(mod->title);
	text_draw(&ui.body, 80.0f, 104.0f, mod->status, strncmp(mod->status, "Supported", 9) ? COLOR_GOLD : COLOR_GREEN);
	y = 140.0f + text_wrapped(&ui.body, 80.0f, 140.0f, LAUNCHER_WIDTH - 160.0f, mod->summary, COLOR_TEXT, 1, 0.0f,
		(float)LAUNCHER_HEIGHT);
	snprintf(line, sizeof(line), "%s \xE2\x80\xA2 %d of %d files here", installed ? "In the game now" : ready ? "Ready to go in" :
		"Not all its files are here", have, need);
	text_draw(&ui.body, 80.0f, y + 12.0f, line, installed ? COLOR_GREEN : ready ? COLOR_BLUE : COLOR_GOLD);
	y += 60.0f;
	if (button(80.0f, y, 420.0f, 56.0f, "IMPORT FILES FROM A FOLDER", !installed && !job.running))
		dialog_folder(JOB_MOD_IMPORT);
	if (button(520.0f, y, 340.0f, 56.0f, "OPEN ITS DOWNLOAD PAGE", 1))
		SDL_OpenURL(mod->page);
	y += 76.0f;
	if (installed)
	{
		if (button(80.0f, y, 420.0f, 56.0f, "PUT THE ORIGINAL BACK", !job.running))
			job_start(JOB_MOD_OUT, ui.mod, NULL);
	}
	else if (button(80.0f, y, 420.0f, 56.0f, "PUT IT IN THE GAME", ready && !job.running))
		job_start(JOB_MOD_IN, ui.mod, NULL);
	text_wrapped(&ui.small, 80.0f, y + 80.0f, LAUNCHER_WIDTH - 160.0f,
		"Download its files in your browser (OPEN ITS DOWNLOAD PAGE), unpack them into a folder, then IMPORT "
		"FILES FROM A FOLDER: each file the campaign needs is found by its name, checked and copied. "
		"Custom Edition's own bitmaps.map, sounds.map and loc.map come from a Halo Custom Edition installation's maps folder.",
		COLOR_DIM, 1, 0.0f, (float)LAUNCHER_HEIGHT);
	if (back_button() && !job.running) { ui.page = PAGE_MODS; ui.focus = 0; }
}

/* a settings row: its label and its choices, cycled by its button */
struct launcher_setting
{
	const char *label, *key;
	int count;
	const char *values[8], *names[8];
};

static const struct launcher_setting launcher_settings[] =
{
	{ "DISPLAY", "display.mode", 3, { "fullscreen", "borderless", "windowed" }, { "FULLSCREEN", "BORDERLESS", "WINDOWED" } },
	{ "V-SYNC", "display.vsync", 2, { "true", "false" }, { "ON", "OFF" } },
	{ "FRAME RATE LIMIT", "display.max_fps", 6, { "0", "60", "120", "144", "240", "-1" }, { "AUTO", "60", "120", "144", "240", "NONE" } },
	/* Test73: as the Android launcher's Geometry compatibility (LauncherHelp.java) */
	{ "GEOMETRY", "renderer.safe_geometry", 2, { "true", "false" }, { "SAFE", "NORMAL" } },
#ifdef HALO_VR
	/* Test73 (the owner's): where the headset shows the menus, the main
	menu's too (VR SETTINGS' MENU POSITION, vr.menu_anchor) */
	{ "MENU POSITION", "vr.menu_anchor", 3, { "head", "world", "follow" },
		{ "FOLLOWS THE HEAD", "FIXED IN FRONT", "FIXED, COMES BACK" } },
#endif
#ifndef HALO_VR
	{ "STEREO 3D", "display.stereo", 6, { "off", "sbs_half", "sbs_full", "tab_half", "tab_full", "anaglyph" },
		{ "OFF", "SBS HALF", "SBS FULL", "TAB HALF", "TAB FULL", "ANAGLYPH" } },
	{ "SPRINT", "movement.sprint", 4, { "off", "hold", "toggle", "auto" }, { "OFF", "HOLD", "TOGGLE", "AUTO" } },
	{ "SLIDE", "movement.slide", 2, { "false", "true" }, { "OFF", "ON" } },
	{ "WALL RUN", "movement.parkour_wallrun", 2, { "false", "true" }, { "OFF", "ON" } },
	{ "WALL JUMP", "movement.parkour_walljump", 2, { "false", "true" }, { "OFF", "ON" } },
#endif
	{ "THIS LAUNCHER AT START", "launcher.show", 2, { "true", "false" }, { "SHOWN", "SKIPPED" } },
};
#define LAUNCHER_SETTING_COUNT ((int)(sizeof(launcher_settings) / sizeof(launcher_settings[0])))

static void page_settings(void)
{
	int index;
	float y = 110.0f;

	page_heading("SETTINGS");
	for (index = 0; index < LAUNCHER_SETTING_COUNT; index++)
	{
		const struct launcher_setting *setting = &launcher_settings[index];
		char label[160];
		int current = -1, choice;
		for (choice = 0; choice < setting->count; choice++)
			if (config_matches(setting->key, setting->values[choice]))
				current = choice;
		snprintf(label, sizeof(label), "%s:  %s", setting->label, current >= 0 ? setting->names[current] : "CUSTOM");
		if (button(80.0f, y, 640.0f, 50.0f, label, 1))
		{
			int next = current < 0 ? 0 : (current + 1) % setting->count;
			if (!config_write_text(setting->key, setting->values[next]))
				snprintf(ui.status, sizeof(ui.status), "Could not save %s.", setting->label);
		}
		y += 58.0f;
	}
	{
		/* (each note below the one before) */
		float note = 110.0f;

		note += text_wrapped(&ui.small, 760.0f, note, LAUNCHER_WIDTH - 840.0f,
			"Every other setting is in the game: SETTINGS, then your player profile: Video Setup (graphics, field "
			"of view, extra effects, STEREO 3D), Controls Setup (keyboard and mouse, with remapping), Gamepad Setup, "
			"Audio, MOVEMENT. They are saved in config.toml beside the game.",
			COLOR_DIM, 1, 0.0f, (float)LAUNCHER_HEIGHT) + 18.0f;
		note += text_wrapped(&ui.small, 760.0f, note, LAUNCHER_WIDTH - 840.0f,
			"GEOMETRY: Safe is the default on every build (PC, PC VR, Quest VR, Android). It keeps scenery from "
			"stretching into triangles or strips by not caching static geometry, not streaming it persistently and "
			"not rebasing vertices on the GPU, and can cost frame rate. Normal turns those back on. It is a renderer "
			"option, not a game version. It applies from the game's start (PLAY).",
			COLOR_DIM, 1, 0.0f, (float)LAUNCHER_HEIGHT) + 18.0f;
#ifndef HALO_VR
		/* Test73b (the owner: for the flat builds "make sure ... there's an actual button mapping for it.
		Shift maybe"): SPRINT's key, said where SPRINT is chosen */
		text_wrapped(&ui.small, 760.0f, note, LAUNCHER_WIDTH - 840.0f,
			"SPRINT: HOLD sprints while Left Shift is held, TOGGLE starts and stops it with a press (Controls "
			"Setup in the game changes the key). A gamepad has no free button for it: choose AUTO, and the left "
			"stick pushed fully forward for a moment sprints. CONTROLS, on the first page, shows every button.",
			COLOR_DIM, 1, 0.0f, (float)LAUNCHER_HEIGHT);
#else
		(void)note;
#endif
	}
	if (back_button()) { ui.page = PAGE_HOME; ui.focus = 0; }
}

static void page_vr(void)
{
	char other[LAUNCHER_PATH], root[LAUNCHER_PATH];
	int has = data_root_maps(root, sizeof(root), NULL);

#ifdef HALO_VR
	page_heading("VR HEADSETS");
#else
	page_heading("PC VR");
#endif
	text_wrapped(&ui.body, 80.0f, 110.0f, LAUNCHER_WIDTH - 160.0f,
		"The PC VR build (halo-vr.exe, beside halo.exe, the same maps, saves and campaigns) runs through OpenXR "
		"on the headset's own PC software: SteamVR (2.17 or later; this is a 32-bit game), Meta Quest Link or Air "
		"Link, Virtual Desktop, Pico Connect, or Windows Mixed Reality where it is still installed. Set the one "
		"you use as the active OpenXR runtime, start it, then play. Valve Index, HTC Vive, Meta Touch, Pico, "
		"HP Reverb G2 and PlayStation VR2 (through SteamVR) controllers are known; others SteamVR maps to them. "
		"If the headset does not start, halo-vr.log beside the game says why (LOGS, on the first page, opens its "
		"folder).",
		COLOR_TEXT, 1, 0.0f, (float)LAUNCHER_HEIGHT);
	text_wrapped(&ui.small, 80.0f, 420.0f, LAUNCHER_WIDTH - 160.0f,
		"VR settings (hands, buttons, IMMERSION, scopes, menus) are in the headset: pause, VR SETTINGS. They are "
		"saved apart from the screen build's, in config-vr.toml."
#ifdef HALO_VR
		" Where the menus are shown (following the head, or fixed in front of you, the main menu's too) is "
		"also in SETTINGS here: MENU POSITION."
#endif
		,
		COLOR_DIM, 1, 0.0f, (float)LAUNCHER_HEIGHT);
	other_build(other, sizeof(other));
#ifndef HALO_VR
	if (button(80.0f, 520.0f, 360.0f, 56.0f, "PLAY IN VR", has && file_exists(other)))
	{
		if (start_build(other, custom_edition_marked(root)))
			ui.quit = 2;
		else
			snprintf(ui.status, sizeof(ui.status), "Could not start %s.", other);
	}
	if (!file_exists(other))
		text_draw(&ui.small, 460.0f, 538.0f, "halo-vr.exe is not beside this game.", COLOR_GOLD);
#else
	(void)has;
#endif
	if (back_button()) { ui.page = PAGE_HOME; ui.focus = 0; }
}

/* a folder as the player finds it: a relative one (the data root "." when
the game was started in its folder) made whole from the current folder */
static void folder_whole(char *out, size_t size, const char *folder)
{
	int whole = folder[0] == '/' || folder[0] == '\\' || (folder[0] && folder[1] == ':');
	char *current = whole ? NULL : SDL_GetCurrentDirectory();

	if (current && !strcmp(folder, "."))
		snprintf(out, size, "%s", current);
	else if (current)
		path_join(out, size, current, folder);
	else
		snprintf(out, size, "%s", folder);
	SDL_free(current);
}

/* whether two whole folders are one (a separator at the end or not; on
Windows either separator, and letters in either case) */
static int same_folder(const char *a, const char *b)
{
	char x[LAUNCHER_PATH], y[LAUNCHER_PATH];
	char *both[2] = { x, y };
	int index;

	snprintf(x, sizeof(x), "%s", a);
	snprintf(y, sizeof(y), "%s", b);
	for (index = 0; index < 2; index++)
	{
		char *path = both[index], *letter;
		size_t length;
#ifdef _WIN32
		for (letter = path; *letter; letter++)
			if (*letter == '/')
				*letter = '\\';
#else
		(void)letter;
#endif
		while ((length = strlen(path)) > 1 && (path[length - 1] == '/' || path[length - 1] == '\\'))
			path[length - 1] = '\0';
	}
#ifdef _WIN32
	return lower_equals(x, y);
#else
	return !strcmp(x, y);
#endif
}

/* Test73b (the owner: "where are logs generating for steam and pc? these
things should be clarified" / "do that for all launchers i guess. useful for
log finding"): where this build's logs are, each folder opened in a press
(the Android launcher's and the Steam Frame's say theirs) */
static void page_logs(void)
{
	char root[LAUNCHER_PATH], data[LAUNCHER_PATH], game[LAUNCHER_PATH], logs[LAUNCHER_PATH];
	char line[LAUNCHER_PATH * 2 + 400], url[LAUNCHER_PATH + 16];
	const char *base = SDL_GetBasePath();
	float y = 110.0f, width = LAUNCHER_WIDTH - 160.0f;
	int separate;

	data_root_maps(root, sizeof(root), NULL);
	folder_whole(data, sizeof(data), root);
	folder_whole(game, sizeof(game), base ? base : ".");
	path_join(logs, sizeof(logs), game, "logs");
	separate = !same_folder(data, game);
	page_heading("LOGS");
	y += text_wrapped(&ui.body, 80.0f, y, width,
		"Something wrong? Send the log of the run it happened in, with a few words on what happened, this "
		"version (" HALO_PORT_VERSION ") and, for PC VR, your headset and its PC software.",
		COLOR_TEXT, 1, 0.0f, (float)LAUNCHER_HEIGHT) + 14.0f;
#ifdef _WIN32
	text_draw(&ui.body, 80.0f, y, "halo.log and halo-vr.log", COLOR_BLUE);
	y += ui.body.size * 1.25f;
	snprintf(line, sizeof(line),
		"Beside the game, in %s: the last run of halo.exe (on the screen) and of halo-vr.exe (PC VR), or this "
		"one's while it runs: the start, the game data folder, invites, the headset's start and a crash's report.",
		game);
	y += text_wrapped(&ui.small, 80.0f, y, width, line, COLOR_DIM, 1, 0.0f, (float)LAUNCHER_HEIGHT) + 10.0f;
	text_draw(&ui.body, 80.0f, y, "logs", COLOR_BLUE);
	y += ui.body.size * 1.25f;
	y += text_wrapped(&ui.small, 80.0f, y, width,
		"Beside them, the ten runs before of each build: halo_<date>_<time>.log and halo-vr_<date>_<time>.log, "
		"named by when that run last wrote (each start keeps its build's last log there first).",
		COLOR_DIM, 1, 0.0f, (float)LAUNCHER_HEIGHT) + 10.0f;
#else
	text_draw(&ui.body, 80.0f, y, "The terminal", COLOR_BLUE);
	y += ui.body.size * 1.25f;
	y += text_wrapped(&ui.small, 80.0f, y, width,
		"The start, the game data folder, invites, the headset's start and a crash's report go to the terminal "
		"the game is started from: start it from one (./halo 2> halo.log keeps them in a file).",
		COLOR_DIM, 1, 0.0f, (float)LAUNCHER_HEIGHT) + 10.0f;
#endif
	text_draw(&ui.body, 80.0f, y, "debug.txt", COLOR_BLUE);
	y += ui.body.size * 1.25f;
	snprintf(line, sizeof(line),
		"In the game data folder, %s: the game's own log, each run after the one before (at 64 MB it becomes "
		"debug.old.txt and begins again).", data);
	y += text_wrapped(&ui.small, 80.0f, y, width, line, COLOR_DIM, 1, 0.0f, (float)LAUNCHER_HEIGHT) + 24.0f;

	if (button(80.0f, y, 360.0f, 56.0f, "OPEN THE GAME'S FOLDER", 1))
	{
		snprintf(url, sizeof(url), "file:///%s", game);
		SDL_OpenURL(url);
	}
#ifdef _WIN32
	if (button(460.0f, y, 300.0f, 56.0f, "OPEN THE LOGS FOLDER", path_type(logs, NULL) == SDL_PATHTYPE_DIRECTORY))
	{
		snprintf(url, sizeof(url), "file:///%s", logs);
		SDL_OpenURL(url);
	}
	if (path_type(logs, NULL) != SDL_PATHTYPE_DIRECTORY)
		text_draw(&ui.small, 460.0f, y + 64.0f, "(made at the game's next start)", COLOR_DIM);
#endif
	if (separate && button(780.0f, y, 300.0f, 56.0f, "OPEN THE DATA FOLDER", 1))
	{
		snprintf(url, sizeof(url), "file:///%s", data);
		SDL_OpenURL(url);
	}
	if (back_button()) { ui.page = PAGE_HOME; ui.focus = 0; }
}

/* Test73 (the owner: "make sure the new features details are more clean (the pop up that shows new features in
the launcher is the one i mean)"): What's New drawn as it is written (whats_new.txt; the Android launcher's
WhatsNew.java alike): its first line the title, a line in capitals a heading, "• " a point whose lines wrap after
its bullet, a blank line a small gap, anything else plain text */
enum news_line { NEWS_GAP, NEWS_TITLE, NEWS_HEADING, NEWS_POINT, NEWS_TEXT };

static enum news_line news_line_kind(const char *line, size_t length, int first)
{
	size_t index;

	while (length && (line[length - 1] == ' ' || line[length - 1] == '\r'))
		length--;
	if (!length)
		return NEWS_GAP;
	if (first)
		return NEWS_TITLE;
	if (length >= 4 && !memcmp(line, "\xE2\x80\xA2 ", 4))
		return NEWS_POINT;
	for (index = 0; index < length; index++)
	{
		if (line[index] >= 'a' && line[index] <= 'z')
			return NEWS_TEXT;
	}
	return NEWS_HEADING;
}

/* the notes laid out from y, drawn when draw is set (the lines within top..bottom): their height */
static float news_layout(const char *text, float y, int draw, float top, float bottom)
{
	float start = y, width = LAUNCHER_WIDTH - 160.0f;
	int first = 1;

	while (text && *text)
	{
		const char *end = strchr(text, '\n');
		size_t length = end ? (size_t)(end - text) : strlen(text);
		char line[2048];
		enum news_line kind;

		if (length >= sizeof(line))
			length = sizeof(line) - 1;
		memcpy(line, text, length);
		line[length] = '\0';
		kind = news_line_kind(line, length, first);
		switch (kind)
		{
		case NEWS_GAP:
			y += ui.body.size * 0.6f;
			break;
		case NEWS_TITLE:
			y += text_wrapped(&ui.body, 80.0f, y, width, line, COLOR_TEXT, draw, top, bottom) + 4.0f;
			break;
		case NEWS_HEADING:
			y += 4.0f;
			y += text_wrapped(&ui.body, 80.0f, y, width, line, COLOR_BLUE, draw, top, bottom) + 2.0f;
			break;
		case NEWS_POINT:
			if (draw && y + ui.body.size * 1.25f >= top && y <= bottom)
				text_draw(&ui.body, 86.0f, y, "\xE2\x80\xA2", COLOR_BLUE);
			y += text_wrapped(&ui.body, 108.0f, y, width - 28.0f, line + 4, COLOR_TEXT, draw, top, bottom) + 3.0f;
			break;
		case NEWS_TEXT:
			y += text_wrapped(&ui.body, 80.0f, y, width, line, COLOR_DIM, draw, top, bottom);
			break;
		}
		if (kind != NEWS_GAP)
			first = 0;
		text = end ? end + 1 : NULL;
	}
	return y - start;
}

static void page_news(void)
{
	static char *text;
	float height;

	if (!text)
		text = launcher_file_text("whats_new.txt");
	page_heading("WHAT'S NEW");
	if (text)
	{
		height = news_layout(text, 0.0f, 0, 0.0f, 0.0f);
		if (ui.scroll > height - 520.0f) ui.scroll = height - 520.0f;
		if (ui.scroll < 0.0f) ui.scroll = 0.0f;
		SDL_Rect clip = { 0, 100, LAUNCHER_WIDTH, LAUNCHER_HEIGHT - 210 };
		SDL_SetRenderClipRect(ui.renderer, &clip);
		news_layout(text, 110.0f - ui.scroll, 1, 100.0f, (float)(LAUNCHER_HEIGHT - 110));
		SDL_SetRenderClipRect(ui.renderer, NULL);
	}
	if (button(300.0f, LAUNCHER_HEIGHT - 90.0f, 400.0f, 50.0f, "FULL RELEASE NOTES (GITHUB)", 1))
		SDL_OpenURL("https://github.com/" HALO_PORT_REPOSITORY "/releases");
	if (back_button()) { ui.page = PAGE_HOME; ui.focus = 0; }
}

/* Test73b (the owner: "a controls section, one where you can click, it'll give you the actual proper mappings. For
each controller type ... what can change certain mappings ... You can select like what controller type you're
using"): every button of each controller and what changes it, from controls/controllers.txt, which the Android
launcher's ControlsGuide shows too. A line "== LABEL | KIND | WHERE" begins a controller's page: KIND vr or flat,
WHERE the launchers that list it ("pc", this one); a page labelled * is shown under every page of its kind; lines
beginning "#" are the file's notes */
#define CONTROLS_PAGES 16

struct controls_page
{
	char label[32];
	int vr;
	const char *body;
	size_t length;
};

/* a header's field, its spaces at either end dropped (in place) */
static char *controls_field(char *text)
{
	size_t length;

	while (*text == ' ')
		text++;
	length = strlen(text);
	while (length && (text[length - 1] == ' ' || text[length - 1] == '\r'))
		text[--length] = '\0';
	return text;
}

/* the pages of `file` that `where` lists, in their order (at most `maximum`), and each kind's shared page
(common[0] the flat pages', common[1] the headsets'; a NULL body where there is none): how many pages */
static int controls_pages(const char *file, const char *where, struct controls_page *pages, int maximum,
	struct controls_page common[2])
{
	const char *line = file;
	struct controls_page *open = NULL;
	int count = 0;

	memset(common, 0, 2 * sizeof(*common));
	while (line && *line)
	{
		const char *end = strchr(line, '\n');
		size_t length = end ? (size_t)(end - line) : strlen(line);

		if (length >= 3 && !memcmp(line, "== ", 3))
		{
			char header[256], *label, *kind, *places;
			int listed = 0;

			if (open)
				open->length = (size_t)(line - open->body);
			open = NULL;
			snprintf(header, sizeof(header), "%.*s", (int)(length - 3), line + 3);
			kind = strchr(header, '|');
			places = kind ? strchr(kind + 1, '|') : NULL;
			if (kind && places)
			{
				*kind++ = '\0';
				*places++ = '\0';
				label = controls_field(header);
				kind = controls_field(kind);
				/* (its places, a word each) */
				while (*places)
				{
					size_t word;

					places += strspn(places, " \r");
					word = strcspn(places, " \r");
					if (word && word == strlen(where) && !strncmp(places, where, word))
						listed = 1;
					places += word;
				}
				if (listed && (!strcmp(kind, "vr") || !strcmp(kind, "flat")))
				{
					int vr = !strcmp(kind, "vr");

					if (!strcmp(label, "*"))
						open = &common[vr];
					else if (count < maximum)
						open = &pages[count++];
					if (open)
					{
						snprintf(open->label, sizeof(open->label), "%s", label);
						open->vr = vr;
						open->body = end ? end + 1 : line + length;
					}
				}
			}
		}
		line = end ? end + 1 : NULL;
	}
	if (open)
		open->length = strlen(open->body);
	return count;
}

/* a page's text without the file's notes, and the shared page of its kind after it, a blank line between
(allocated; NULL when there is no memory) */
static char *controls_compose(const struct controls_page *page, const struct controls_page common[2])
{
	const struct controls_page *shared = &common[page->vr ? 1 : 0];
	size_t size = page->length + (shared->body ? shared->length : 0) + 4;
	char *text = malloc(size), *out = text;
	int part;

	if (!text)
		return NULL;
	for (part = 0; part < 2; part++)
	{
		const struct controls_page *from = part ? shared : page;
		const char *line = from->body, *stop;

		if (!line)
			continue;
		stop = line + from->length;
		if (part && out > text)
			*out++ = '\n';
		while (line < stop)
		{
			const char *end = memchr(line, '\n', (size_t)(stop - line));
			size_t length = end ? (size_t)(end - line) : (size_t)(stop - line);

			if (!length || line[0] != '#')
			{
				memcpy(out, line, length);
				out += length;
				*out++ = '\n';
			}
			line = end ? end + 1 : stop;
		}
		/* (its blank lines at the end dropped) */
		while (out - text >= 2 && out[-1] == '\n' && out[-2] == '\n')
			out--;
	}
	*out = '\0';
	return text;
}

static void page_controls(void)
{
	static char *file, *text;
	static struct controls_page pages[CONTROLS_PAGES], common[2];
	static int count = -1, chosen = -1, shown = -1;
	int index;

	if (count < 0)
	{
		file = launcher_file_text("controls/controllers.txt");
		count = file ? controls_pages(file, "pc", pages, CONTROLS_PAGES, common) : 0;
		/* (the build's own first: the headset's controllers, or the keyboard) */
		for (index = 0; index < count && chosen < 0; index++)
#ifdef HALO_VR
			if (!strcmp(pages[index].label, "QUEST (TOUCH)"))
#else
			if (!strcmp(pages[index].label, "KEYBOARD + MOUSE"))
#endif
				chosen = index;
		if (chosen < 0)
			chosen = 0;
	}
	page_heading("CONTROLS");
	if (!count)
	{
		text_draw(&ui.body, 80.0f, 110.0f, "The controls could not be read.", COLOR_GOLD);
		if (back_button()) { ui.page = PAGE_HOME; ui.focus = 0; }
		return;
	}
	/* the controllers, four a row, the one shown marked */
	for (index = 0; index < count; index++)
	{
		char label[48];

		snprintf(label, sizeof(label), index == chosen ? "\xE2\x80\xA2 %s" : "%s", pages[index].label);
		if (button(80.0f + (float)(index % 4) * 285.0f, 104.0f + (float)(index / 4) * 52.0f, 270.0f, 44.0f, label, 1))
		{
			chosen = index;
			ui.scroll = 0.0f;
		}
	}
	if (chosen != shown)
	{
		free(text);
		text = controls_compose(&pages[chosen], common);
		shown = chosen;
	}
	if (text)
	{
		float top = 104.0f + (float)((count + 3) / 4) * 52.0f + 12.0f, bottom = (float)(LAUNCHER_HEIGHT - 110);
		float height = news_layout(text, 0.0f, 0, 0.0f, 0.0f);
		SDL_Rect clip = { 0, (int)top, LAUNCHER_WIDTH, (int)(bottom - top) };

		if (ui.scroll > height - (bottom - top)) ui.scroll = height - (bottom - top);
		if (ui.scroll < 0.0f) ui.scroll = 0.0f;
		SDL_SetRenderClipRect(ui.renderer, &clip);
		news_layout(text, top - ui.scroll, 1, top, bottom);
		SDL_SetRenderClipRect(ui.renderer, NULL);
	}
	if (back_button()) { ui.page = PAGE_HOME; ui.focus = 0; }
}

static void page_updates(void)
{
	char line[256];

	page_heading("UPDATES");
	snprintf(line, sizeof(line), "This build: %s", HALO_PORT_VERSION);
	text_draw(&ui.body, 80.0f, 110.0f, line, COLOR_TEXT);
	text_wrapped(&ui.small, 80.0f, 150.0f, LAUNCHER_WIDTH - 160.0f,
		"CHECK asks GitHub for the latest release (nothing is asked unless you press it). Updating is "
		"downloading the new release and putting its files beside these; your maps, saves, campaigns and "
		"settings stay.",
		COLOR_DIM, 1, 0.0f, (float)LAUNCHER_HEIGHT);
	if (button(80.0f, 240.0f, 300.0f, 56.0f, "CHECK", !job.running))
		job_start(JOB_UPDATES, 0, NULL);
	if (button(400.0f, 240.0f, 360.0f, 56.0f, "OPEN THE RELEASES PAGE", 1))
		SDL_OpenURL("https://github.com/" HALO_PORT_REPOSITORY "/releases");
	if (back_button()) { ui.page = PAGE_HOME; ui.focus = 0; }
}

/* ---------- the loop */

static void launcher_input(void)
{
	SDL_Event event;

	ui.activated = ui.clicked = ui.back = ui.mouse_moved = 0;
	while (SDL_PollEvent(&event))
	{
		SDL_ConvertEventToRenderCoordinates(ui.renderer, &event);
		switch (event.type)
		{
		case SDL_EVENT_QUIT:
		case SDL_EVENT_WINDOW_CLOSE_REQUESTED:
			ui.quit = 1;
			break;
		case SDL_EVENT_MOUSE_MOTION:
			ui.mouse_x = event.motion.x;
			ui.mouse_y = event.motion.y;
			ui.mouse_moved = 1;
			break;
		case SDL_EVENT_MOUSE_BUTTON_DOWN:
			ui.mouse_x = event.button.x;
			ui.mouse_y = event.button.y;
			ui.mouse_moved = 1;
			if (event.button.button == SDL_BUTTON_LEFT)
				ui.clicked = 1;
			break;
		case SDL_EVENT_MOUSE_WHEEL:
			ui.scroll -= event.wheel.y * 60.0f;
			break;
		case SDL_EVENT_KEY_DOWN:
			if (event.key.key == SDLK_ESCAPE) ui.back = 1;
			else if (event.key.key == SDLK_RETURN || event.key.key == SDLK_SPACE) ui.activated = 1;
			else if (event.key.key == SDLK_DOWN || event.key.key == SDLK_TAB) { ui.focus++; ui.scroll += 40.0f; }
			else if (event.key.key == SDLK_UP) { ui.focus--; ui.scroll -= 40.0f; }
			break;
		case SDL_EVENT_GAMEPAD_ADDED:
			if (!ui.gamepad)
				ui.gamepad = SDL_OpenGamepad(event.gdevice.which);
			break;
		case SDL_EVENT_GAMEPAD_BUTTON_DOWN:
			if (event.gbutton.button == SDL_GAMEPAD_BUTTON_SOUTH) ui.activated = 1;
			else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_EAST) ui.back = 1;
			else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_DPAD_DOWN) { ui.focus++; ui.scroll += 40.0f; }
			else if (event.gbutton.button == SDL_GAMEPAD_BUTTON_DPAD_UP) { ui.focus--; ui.scroll -= 40.0f; }
			break;
		default:
			break;
		}
	}
	if (ui.focus_count > 0)
	{
		if (ui.focus < 0) ui.focus = ui.focus_count - 1;
		if (ui.focus >= ui.focus_count) ui.focus = 0;
	}
	/* while a job runs or a dialog is open, only the window lives */
	if (ui.dialog_pending || job.running)
		ui.activated = ui.clicked = ui.back = 0;
}

static void launcher_busy_overlay(void)
{
	char step[256];
	double fraction;

	SDL_LockMutex(job.lock);
	snprintf(step, sizeof(step), "%s", job.step);
	fraction = job.fraction;
	SDL_UnlockMutex(job.lock);
	fill(0.0f, LAUNCHER_HEIGHT - 170.0f, (float)LAUNCHER_WIDTH, 70.0f, 0x0A1018F0u);
	text_draw(&ui.small, 80.0f, LAUNCHER_HEIGHT - 162.0f, step[0] ? step : "Working...", COLOR_TEXT);
	fill(80.0f, LAUNCHER_HEIGHT - 130.0f, LAUNCHER_WIDTH - 160.0f, 14.0f, 0x2C3A48FFu);
	fill(80.0f, LAUNCHER_HEIGHT - 130.0f, (float)((LAUNCHER_WIDTH - 160.0f) * fraction), 14.0f, COLOR_BLUE);
}

void desktop_launcher_run(void)
{
	char root[LAUNCHER_PATH], self[LAUNCHER_PATH];

	launcher_is_active = 1;
	memset(&ui, 0, sizeof(ui));
	memset(&job, 0, sizeof(job));
	job.lock = SDL_CreateMutex();
	ui.window = SDL_CreateWindow("Halo: Combat Evolved", LAUNCHER_WIDTH, LAUNCHER_HEIGHT, SDL_WINDOW_RESIZABLE);
	ui.renderer = ui.window ? SDL_CreateRenderer(ui.window, NULL) : NULL;
	if (!ui.window || !ui.renderer || !job.lock)
	{
		/* no launcher here: the game as before */
		platform_log("launcher: cannot open its window (%s); the game starts as before", SDL_GetError());
		if (ui.renderer) SDL_DestroyRenderer(ui.renderer);
		if (ui.window) SDL_DestroyWindow(ui.window);
		launcher_is_active = 0;
		return;
	}
	SDL_SetRenderVSync(ui.renderer, 1);
	SDL_SetRenderLogicalPresentation(ui.renderer, LAUNCHER_WIDTH, LAUNCHER_HEIGHT, SDL_LOGICAL_PRESENTATION_LETTERBOX);
	SDL_SetRenderDrawBlendMode(ui.renderer, SDL_BLENDMODE_BLEND);
	font_load(&ui.body, "Overpass-750.ttf", 24.0f);
	font_load(&ui.small, "Overpass-750.ttf", 19.0f);
	font_load(&ui.heading, "Overpass-900.ttf", 34.0f);
	font_load(&ui.title, "Overpass-900.ttf", 64.0f);
	platform_log("launcher: shown (%s)", HALO_PORT_VERSION);
	while (!ui.quit && !ui.play)
	{
		launcher_input();
		if (ui.dialog_pending && SDL_GetAtomicInt(&ui.dialog_done))
		{
			ui.dialog_pending = 0;
			if (ui.dialog_path[0])
				job_start(ui.dialog_kind, ui.mod, ui.dialog_path);
		}
		if (job.running && job.finished)
		{
			SDL_WaitThread(job.thread, NULL);
			job.thread = NULL;
			job.running = 0;
			platform_data_root_refresh();
			snprintf(ui.status, sizeof(ui.status), "%s", job.result);
		}
		SDL_SetRenderDrawColor(ui.renderer, 8, 14, 22, 255);
		SDL_RenderClear(ui.renderer);
		fill(0.0f, 0.0f, (float)LAUNCHER_WIDTH, 6.0f, COLOR_BLUE);
		ui.buttons = 0;
		{
			int drawn = ui.page;

			switch (drawn)
			{
			case PAGE_DATA: page_data(); break;
			case PAGE_MODS: page_mods(); break;
			case PAGE_MOD: page_mod(); break;
			case PAGE_SETTINGS: page_settings(); break;
			case PAGE_VR: page_vr(); break;
			case PAGE_NEWS: page_news(); break;
			case PAGE_UPDATES: page_updates(); break;
			case PAGE_LOGS: page_logs(); break;
			case PAGE_CONTROLS: page_controls(); break;
			default: page_home(); break;
			}
			/* a page's result line is that page's: another page starts
			without it (it sat over WHAT'S NEW's button) */
			if (ui.page != drawn)
				ui.status[0] = '\0';
		}
		ui.focus_count = ui.buttons;
		if (job.running)
			launcher_busy_overlay();
		else if (ui.status[0])
			text_wrapped(&ui.small, 320.0f, LAUNCHER_HEIGHT - 84.0f, LAUNCHER_WIDTH - 400.0f, ui.status,
				COLOR_GOLD, 1, 0.0f, (float)LAUNCHER_HEIGHT);
		SDL_RenderPresent(ui.renderer);
	}
	if (ui.body.texture) SDL_DestroyTexture(ui.body.texture);
	if (ui.small.texture) SDL_DestroyTexture(ui.small.texture);
	if (ui.heading.texture) SDL_DestroyTexture(ui.heading.texture);
	if (ui.title.texture) SDL_DestroyTexture(ui.title.texture);
	if (ui.gamepad) SDL_CloseGamepad(ui.gamepad);
	SDL_DestroyRenderer(ui.renderer);
	SDL_DestroyWindow(ui.window);
	launcher_is_active = 0;
	platform_data_root_refresh();
	if (ui.quit == 2)
		exit(EXIT_SUCCESS); /* the other build plays */
	if (ui.quit)
	{
		platform_log("launcher: quit");
		exit(EXIT_SUCCESS);
	}
	/* a Custom Edition campaign in, the game not started with its maps
	loading: this build anew, with them (the tag cache is reserved before
	main, xbox_memory.c) */
	data_root_maps(root, sizeof(root), NULL);
	if (custom_edition_marked(root) && !config_boolean("game.custom_edition") &&
		update_executable_path(self, sizeof(self)) && start_build(self, 1))
		exit(EXIT_SUCCESS);
	platform_log("launcher: play");
}

#else

int desktop_launcher_wanted(void) { return 0; }
void desktop_launcher_run(void) {}
int desktop_launcher_active(void) { return 0; }
int desktop_launcher_mod_map(const char *root, const char *file_name) { (void)root; (void)file_name; return 0; }

#endif
