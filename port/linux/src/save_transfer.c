/*
SAVE_TRANSFER.C

Test72 (a player's suggestion: "ability to import savefiles from zip or
folder", first done in the Android launcher, SaveTransfer.java): the
desktop launcher's GAME DATA page brings saves in from a .zip or a folder
and takes them out as a .zip.

The saves are the save root's (platform_save_root: z/ and u/, the game's z:\
and u:\): z/saved (player profiles, playlists, recordings), z/savegame.bin
(the campaign's checkpoint) and u/UDATA (Xbox save containers). What is
brought in is recognised by those names wherever they lie in it - a copy of
another device's save folder, its z or saved folder alone, a player_profiles
folder, a savegame.bin, an Xbox dump's UDATA folder - the same rules as the
Android launcher's. The caches (*.map, z/maps) are never taken, nor a name
that would leave the save root. An import is unpacked into a staging folder
first; only when it holds saves are the saves already there backed up (a
.zip in the save root's backups folder) and the new files put in place,
files of the same name replaced, others kept.

The zips read are stored or deflated (the port's inflate, as the updater
reads its releases); those written are stored: saves are small, and every
zip tool reads them.
*/

#include "save_transfer.h"

#if !defined(HALO_ANDROID) && !defined(HALO_WEB)

#include "zlib_prefixed.h"

#include <SDL3/SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SAVE_TRANSFER_MAXIMUM_FILES 4096
#define SAVE_TRANSFER_MAXIMUM_BYTES (512ul * 1024ul * 1024ul)
#define SAVE_TRANSFER_PATH 1024
#define SAVE_TRANSFER_MAXIMUM_SEGMENTS 16
#define SAVE_TRANSFER_MAXIMUM_SEGMENT 128

/* ---------- which files are saves */

static int save_name_safe(const char *segment, size_t length)
{
	size_t index;

	if (!length || length > SAVE_TRANSFER_MAXIMUM_SEGMENT)
		return 0;
	if ((length == 1 && segment[0] == '.') || (length == 2 && segment[0] == '.' && segment[1] == '.'))
		return 0;
	for (index = 0; index < length; index++)
	{
		unsigned char c = (unsigned char)segment[index];

		if (c < 32 || strchr("<>:\"|?*", c))
			return 0;
	}
	return 1;
}

static int segment_is(const char *segment, size_t length, const char *name)
{
	return strlen(name) == length && SDL_strncasecmp(segment, name, length) == 0;
}

int save_transfer_destination(const char *path, char *out, size_t size)
{
	const char *starts[SAVE_TRANSFER_MAXIMUM_SEGMENTS];
	size_t lengths[SAVE_TRANSFER_MAXIMUM_SEGMENTS];
	char normalized[SAVE_TRANSFER_PATH];
	const char *cursor;
	const char *prefix = NULL;
	int count = 0, from = -1, index;
	size_t length, written;

	if (!path || !out || !size || strlen(path) >= sizeof(normalized))
		return 0;
	for (index = 0; path[index]; index++)
		normalized[index] = path[index] == '\\' ? '/' : path[index];
	normalized[index] = '\0';
	cursor = normalized;
	/* (a drive, a leading slash or "./" mean nothing here) */
	if (((cursor[0] >= 'A' && cursor[0] <= 'Z') || (cursor[0] >= 'a' && cursor[0] <= 'z')) && cursor[1] == ':')
		cursor += 2;
	while (*cursor)
	{
		const char *end = strchr(cursor, '/');

		length = end ? (size_t)(end - cursor) : strlen(cursor);
		if (length && !(length == 1 && cursor[0] == '.'))
		{
			if (length == 2 && cursor[0] == '.' && cursor[1] == '.')
				return 0;
			if (!save_name_safe(cursor, length) || count == SAVE_TRANSFER_MAXIMUM_SEGMENTS)
				return 0;
			starts[count] = cursor;
			lengths[count] = length;
			count++;
		}
		if (!end)
			break;
		cursor = end + 1;
	}
	if (!count)
		return 0;
	/* (the caches) */
	length = lengths[count - 1];
	if (length >= 4 && SDL_strncasecmp(starts[count - 1] + length - 4, ".map", 4) == 0)
		return 0;
	/* the last anchor wins (a backup of a folder holding "z"...) */
	for (index = count - 2; index >= 0 && !prefix; index--)
	{
		if (segment_is(starts[index], lengths[index], "udata"))
			prefix = "u/UDATA/";
		else if (segment_is(starts[index], lengths[index], "player_profiles"))
			prefix = "z/saved/player_profiles/";
		else if (segment_is(starts[index], lengths[index], "saved") &&
			!segment_is(starts[index + 1], lengths[index + 1], "maps"))
			prefix = "z/saved/";
		if (prefix)
			from = index + 1;
	}
	if (!prefix)
	{
		if (!segment_is(starts[count - 1], lengths[count - 1], "savegame.bin"))
			return 0;
		if (size < sizeof("z/savegame.bin"))
			return 0;
		strcpy(out, "z/savegame.bin");
		return 1;
	}
	written = strlen(prefix);
	if (written >= size)
		return 0;
	memcpy(out, prefix, written);
	for (index = from; index < count; index++)
	{
		if (written + lengths[index] + 1 >= size)
			return 0;
		if (index > from)
			out[written++] = '/';
		memcpy(out + written, starts[index], lengths[index]);
		written += lengths[index];
	}
	out[written] = '\0';
	return 1;
}

/* ---------- files and folders */

static void path_join(char *out, size_t size, const char *folder, const char *name)
{
	size_t length = strlen(folder);

	if (length && (folder[length - 1] == '/' || folder[length - 1] == '\\'))
		snprintf(out, size, "%s%s", folder, name);
	else
		snprintf(out, size, "%s/%s", folder, name);
}

/* a file's folder made, from its path */
static int make_parent(const char *path)
{
	char parent[SAVE_TRANSFER_PATH];
	char *slash;

	snprintf(parent, sizeof(parent), "%s", path);
	slash = strrchr(parent, '/');
	if (!slash)
		slash = strrchr(parent, '\\');
	if (!slash)
		return 1;
	*slash = '\0';
	return SDL_CreateDirectory(parent);
}

static int is_folder(const char *path)
{
	SDL_PathInfo info;

	return SDL_GetPathInfo(path, &info) && info.type == SDL_PATHTYPE_DIRECTORY;
}

/* each file under a folder, with its path relative to it */
typedef int (*file_visitor)(void *context, const char *relative, const char *path);

struct walk
{
	const char *root;
	file_visitor visit;
	void *context;
	int failed;
	int depth;
};

static SDL_EnumerationResult SDLCALL walk_entry(void *data, const char *directory, const char *name)
{
	struct walk *walk = data;
	char path[SAVE_TRANSFER_PATH], relative[SAVE_TRANSFER_PATH];
	SDL_PathInfo info;
	size_t root = strlen(walk->root);

	path_join(path, sizeof(path), directory, name);
	if (!SDL_GetPathInfo(path, &info))
		return SDL_ENUM_CONTINUE;
	/* (the path from the root, '/' separated) */
	snprintf(relative, sizeof(relative), "%s", path + root);
	{
		char *c;
		char *start = relative;

		for (c = relative; *c; c++)
			if (*c == '\\')
				*c = '/';
		while (*start == '/')
			start++;
		memmove(relative, start, strlen(start) + 1);
	}
	if (info.type == SDL_PATHTYPE_DIRECTORY)
	{
		if (walk->depth < SAVE_TRANSFER_MAXIMUM_SEGMENTS)
		{
			walk->depth++;
			if (!SDL_EnumerateDirectory(path, walk_entry, walk))
				walk->failed = 1;
			walk->depth--;
		}
	}
	else if (info.type == SDL_PATHTYPE_FILE)
	{
		if (!walk->visit(walk->context, relative, path))
		{
			walk->failed = 1;
			return SDL_ENUM_FAILURE;
		}
	}
	return walk->failed ? SDL_ENUM_FAILURE : SDL_ENUM_CONTINUE;
}

static int walk_folder(const char *root, file_visitor visit, void *context)
{
	struct walk walk;

	walk.root = root;
	walk.visit = visit;
	walk.context = context;
	walk.failed = 0;
	walk.depth = 0;
	if (!is_folder(root))
		return 1;
	if (!SDL_EnumerateDirectory(root, walk_entry, &walk))
		return 0;
	return !walk.failed;
}

/* a folder and all it holds removed */
static int remove_visit(void *context, const char *relative, const char *path)
{
	(void)context;
	(void)relative;
	SDL_RemovePath(path);
	return 1;
}

static SDL_EnumerationResult SDLCALL remove_folders(void *data, const char *directory, const char *name)
{
	char path[SAVE_TRANSFER_PATH];

	(void)data;
	path_join(path, sizeof(path), directory, name);
	if (is_folder(path))
	{
		SDL_EnumerateDirectory(path, remove_folders, NULL);
		SDL_RemovePath(path);
	}
	return SDL_ENUM_CONTINUE;
}

static void remove_tree(const char *root)
{
	if (!is_folder(root))
	{
		SDL_RemovePath(root);
		return;
	}
	walk_folder(root, remove_visit, NULL);
	SDL_EnumerateDirectory(root, remove_folders, NULL);
	SDL_RemovePath(root);
}

/* a file copied, at most `limit` bytes; the bytes, or -1 */
static long long copy_file(SDL_IOStream *in, const char *target, unsigned long long limit, char *reason, size_t size)
{
	unsigned char buffer[65536];
	SDL_IOStream *out;
	unsigned long long total = 0;
	size_t count;

	if (!make_parent(target) || !(out = SDL_IOFromFile(target, "wb")))
	{
		snprintf(reason, size, "could not write %s (%s)", target, SDL_GetError());
		return -1;
	}
	while ((count = SDL_ReadIO(in, buffer, sizeof(buffer))) > 0)
	{
		total += count;
		if (total > limit || SDL_WriteIO(out, buffer, count) != count)
		{
			if (total > limit)
				snprintf(reason, size, "the saves are larger than %lu MB", SAVE_TRANSFER_MAXIMUM_BYTES >> 20);
			else
				snprintf(reason, size, "could not write %s (%s)", target, SDL_GetError());
			SDL_CloseIO(out);
			return -1;
		}
	}
	if (!SDL_CloseIO(out))
	{
		snprintf(reason, size, "could not write %s (%s)", target, SDL_GetError());
		return -1;
	}
	return (long long)total;
}

/* ---------- what an import brought */

struct import
{
	char stage[SAVE_TRANSFER_PATH];
	int files, skipped, checkpoint;
	unsigned long long bytes;
	char profiles[512];
	int profile_count;
	char reason[512];
};

static void import_noted(struct import *import, const char *place)
{
	static const char profiles[] = "z/saved/player_profiles/";

	if (!strcmp(place, "z/savegame.bin"))
		import->checkpoint = 1;
	if (!strncmp(place, profiles, sizeof(profiles) - 1))
	{
		const char *name = place + sizeof(profiles) - 1;
		const char *slash = strchr(name, '/');
		char profile[SAVE_TRANSFER_MAXIMUM_SEGMENT + 1];
		size_t length;
		const char *found;

		if (!slash)
			return;
		length = (size_t)(slash - name);
		if (length >= sizeof(profile))
			return;
		memcpy(profile, name, length);
		profile[length] = '\0';
		/* (each profile named once, in the order found) */
		for (found = import->profiles; (found = strstr(found, profile)) != NULL; found += length)
		{
			if ((found == import->profiles || found[-2] == ',') && (found[length] == '\0' || found[length] == ','))
				return;
		}
		if (strlen(import->profiles) + length + 3 < sizeof(import->profiles))
		{
			if (import->profiles[0])
				strcat(import->profiles, ", ");
			strcat(import->profiles, profile);
			import->profile_count++;
		}
	}
}

/* a file from the source into the staging folder, if it is a save */
static int import_file(struct import *import, const char *relative, SDL_IOStream *in)
{
	char place[SAVE_TRANSFER_PATH], target[SAVE_TRANSFER_PATH];
	long long copied;

	if (!save_transfer_destination(relative, place, sizeof(place)))
	{
		import->skipped++;
		return 1;
	}
	if (++import->files > SAVE_TRANSFER_MAXIMUM_FILES)
	{
		snprintf(import->reason, sizeof(import->reason), "it holds more than %d save files", SAVE_TRANSFER_MAXIMUM_FILES);
		return 0;
	}
	path_join(target, sizeof(target), import->stage, place);
	copied = copy_file(in, target, SAVE_TRANSFER_MAXIMUM_BYTES - import->bytes, import->reason, sizeof(import->reason));
	if (copied < 0)
		return 0;
	import->bytes += (unsigned long long)copied;
	import_noted(import, place);
	return 1;
}

static int import_folder_visit(void *context, const char *relative, const char *path)
{
	struct import *import = context;
	char place[SAVE_TRANSFER_PATH];
	SDL_IOStream *in;
	int ok;

	if (!save_transfer_destination(relative, place, sizeof(place)))
	{
		import->skipped++;
		return 1;
	}
	in = SDL_IOFromFile(path, "rb");
	if (!in)
	{
		snprintf(import->reason, sizeof(import->reason), "could not read %s (%s)", path, SDL_GetError());
		return 0;
	}
	ok = import_file(import, relative, in);
	SDL_CloseIO(in);
	return ok;
}

/* ---------- zips */

static unsigned long zip_word(const unsigned char *bytes)
{
	return (unsigned long)bytes[0] | (unsigned long)bytes[1] << 8;
}

static unsigned long zip_long(const unsigned char *bytes)
{
	return zip_word(bytes) | zip_word(bytes + 2) << 16;
}

/* an entry unpacked (stored or deflated) into memory, checked against its
size and CRC */
static unsigned char *zip_entry(SDL_IOStream *zip, unsigned long local_offset, int method, unsigned long packed,
	unsigned long size, unsigned long crc, char *reason, size_t reason_size)
{
	unsigned char header[30];
	unsigned char *input, *output;
	z_stream stream;
	int result;

	if (SDL_SeekIO(zip, (Sint64)local_offset, SDL_IO_SEEK_SET) < 0 ||
		SDL_ReadIO(zip, header, sizeof(header)) != sizeof(header) || zip_long(header) != 0x04034b50 ||
		SDL_SeekIO(zip, (Sint64)(zip_word(header + 26) + zip_word(header + 28)), SDL_IO_SEEK_CUR) < 0)
	{
		snprintf(reason, reason_size, "an entry's header could not be read");
		return NULL;
	}
	input = malloc(packed ? packed : 1);
	output = malloc(size ? size : 1);
	if (!input || !output || (packed && SDL_ReadIO(zip, input, packed) != packed))
	{
		snprintf(reason, reason_size, "an entry could not be read");
		free(input);
		free(output);
		return NULL;
	}
	if (method == 0)
	{
		if (packed != size)
		{
			snprintf(reason, reason_size, "a stored entry's sizes differ");
			free(input);
			free(output);
			return NULL;
		}
		memcpy(output, input, size);
	}
	else
	{
		memset(&stream, 0, sizeof(stream));
		if (inflateInit2(&stream, -MAX_WBITS) != Z_OK)
		{
			snprintf(reason, reason_size, "zlib would not start");
			free(input);
			free(output);
			return NULL;
		}
		stream.next_in = input;
		stream.avail_in = (uInt)packed;
		stream.next_out = output;
		stream.avail_out = (uInt)size;
		result = inflate(&stream, Z_FINISH);
		inflateEnd(&stream);
		if ((result != Z_STREAM_END && result != Z_BUF_ERROR && result != Z_OK) || stream.total_out != size)
		{
			snprintf(reason, reason_size, "an entry did not unpack (zlib %d)", result);
			free(input);
			free(output);
			return NULL;
		}
	}
	free(input);
	if (crc32(crc32(0L, Z_NULL, 0), output, (uInt)size) != crc)
	{
		snprintf(reason, reason_size, "an entry's checksum is wrong (a damaged .zip)");
		free(output);
		return NULL;
	}
	return output;
}

static int import_zip(struct import *import, const char *path)
{
	SDL_IOStream *zip = SDL_IOFromFile(path, "rb");
	Sint64 length;
	unsigned char tail[65536 + 22];
	size_t tail_size;
	long found = -1, index;
	unsigned long entries, directory_offset, directory_size, entry;
	unsigned char *directory = NULL;
	unsigned long position = 0;
	int ok = 0;

	if (!zip)
	{
		snprintf(import->reason, sizeof(import->reason), "could not open %s (%s)", path, SDL_GetError());
		return 0;
	}
	length = SDL_GetIOSize(zip);
	tail_size = length < (Sint64)sizeof(tail) ? (size_t)length : sizeof(tail);
	if (length < 22 || SDL_SeekIO(zip, length - (Sint64)tail_size, SDL_IO_SEEK_SET) < 0 ||
		SDL_ReadIO(zip, tail, tail_size) != tail_size)
	{
		snprintf(import->reason, sizeof(import->reason), "it is not a .zip");
		goto done;
	}
	for (index = (long)tail_size - 22; index >= 0; index--)
	{
		if (zip_long(tail + index) == 0x06054b50)
		{
			found = index;
			break;
		}
	}
	if (found < 0)
	{
		snprintf(import->reason, sizeof(import->reason), "it is not a .zip (no directory at its end)");
		goto done;
	}
	entries = zip_word(tail + found + 10);
	directory_size = zip_long(tail + found + 12);
	directory_offset = zip_long(tail + found + 16);
	if (entries == 0xFFFF || directory_offset == 0xFFFFFFFFul ||
		(Sint64)directory_offset + (Sint64)directory_size > length)
	{
		snprintf(import->reason, sizeof(import->reason), "its directory is damaged or too large (zip64)");
		goto done;
	}
	directory = malloc(directory_size ? directory_size : 1);
	if (!directory || SDL_SeekIO(zip, (Sint64)directory_offset, SDL_IO_SEEK_SET) < 0 ||
		SDL_ReadIO(zip, directory, directory_size) != directory_size)
	{
		snprintf(import->reason, sizeof(import->reason), "its directory could not be read");
		goto done;
	}
	for (entry = 0; entry < entries; entry++)
	{
		unsigned long flags, method, crc, packed, size, name_length, extra, comment, local;
		char name[SAVE_TRANSFER_PATH], place[SAVE_TRANSFER_PATH];
		unsigned char *data;
		SDL_IOStream *memory;
		int stored;

		if (position + 46 > directory_size || zip_long(directory + position) != 0x02014b50)
		{
			snprintf(import->reason, sizeof(import->reason), "its directory is damaged");
			goto done;
		}
		flags = zip_word(directory + position + 8);
		method = zip_word(directory + position + 10);
		crc = zip_long(directory + position + 16);
		packed = zip_long(directory + position + 20);
		size = zip_long(directory + position + 24);
		name_length = zip_word(directory + position + 28);
		extra = zip_word(directory + position + 30);
		comment = zip_word(directory + position + 32);
		local = zip_long(directory + position + 42);
		if (position + 46 + name_length > directory_size || name_length >= sizeof(name))
		{
			snprintf(import->reason, sizeof(import->reason), "its directory is damaged");
			goto done;
		}
		memcpy(name, directory + position + 46, name_length);
		name[name_length] = '\0';
		position += 46 + name_length + extra + comment;
		/* (folders, and what is not a save) */
		if (!name_length || name[name_length - 1] == '/' || name[name_length - 1] == '\\')
			continue;
		if (!save_transfer_destination(name, place, sizeof(place)))
		{
			import->skipped++;
			continue;
		}
		if ((flags & 1) || (method != 0 && method != 8))
		{
			snprintf(import->reason, sizeof(import->reason), "%s is %s", name,
				(flags & 1) ? "encrypted" : "packed in a way this does not read (only stored or deflated)");
			goto done;
		}
		if (size > SAVE_TRANSFER_MAXIMUM_BYTES - import->bytes)
		{
			snprintf(import->reason, sizeof(import->reason), "the saves are larger than %lu MB",
				SAVE_TRANSFER_MAXIMUM_BYTES >> 20);
			goto done;
		}
		data = zip_entry(zip, local, (int)method, packed, size, crc, import->reason, sizeof(import->reason));
		if (!data)
			goto done;
		memory = SDL_IOFromConstMem(data, size);
		stored = memory && import_file(import, name, memory);
		if (memory)
			SDL_CloseIO(memory);
		free(data);
		if (!stored)
			goto done;
	}
	ok = 1;
done:
	free(directory);
	SDL_CloseIO(zip);
	return ok;
}

/* the zip written: stored entries, then the directory */
struct zip_writer
{
	SDL_IOStream *out;
	unsigned char *directory;
	size_t directory_size, directory_capacity;
	unsigned long entries, offset;
	int failed;
	char reason[512];
};

static void put_word(unsigned char *bytes, unsigned long value)
{
	bytes[0] = (unsigned char)value;
	bytes[1] = (unsigned char)(value >> 8);
}

static void put_long(unsigned char *bytes, unsigned long value)
{
	put_word(bytes, value & 0xFFFF);
	put_word(bytes + 2, value >> 16);
}

static int zip_add(struct zip_writer *writer, const char *name, const void *data, unsigned long size)
{
	unsigned char header[30], central[46];
	size_t name_length = strlen(name);
	unsigned long crc = crc32(crc32(0L, Z_NULL, 0), data, (uInt)size);

	memset(header, 0, sizeof(header));
	put_long(header, 0x04034b50);
	put_word(header + 4, 10);
	put_word(header + 8, 0);
	put_word(header + 12, 0x21); /* (a fixed date: 1980-01-01) */
	put_long(header + 14, crc);
	put_long(header + 18, size);
	put_long(header + 22, size);
	put_word(header + 26, (unsigned long)name_length);
	if (SDL_WriteIO(writer->out, header, sizeof(header)) != sizeof(header) ||
		SDL_WriteIO(writer->out, name, name_length) != name_length ||
		(size && SDL_WriteIO(writer->out, data, size) != size))
	{
		snprintf(writer->reason, sizeof(writer->reason), "could not write the .zip (%s)", SDL_GetError());
		return 0;
	}
	memset(central, 0, sizeof(central));
	put_long(central, 0x02014b50);
	put_word(central + 4, 20);
	put_word(central + 6, 10);
	put_word(central + 14, 0x21);
	put_long(central + 16, crc);
	put_long(central + 20, size);
	put_long(central + 24, size);
	put_word(central + 28, (unsigned long)name_length);
	put_long(central + 42, writer->offset);
	if (writer->directory_size + sizeof(central) + name_length > writer->directory_capacity)
	{
		size_t capacity = (writer->directory_capacity + sizeof(central) + name_length) * 2;
		unsigned char *grown = realloc(writer->directory, capacity);

		if (!grown)
		{
			snprintf(writer->reason, sizeof(writer->reason), "out of memory");
			return 0;
		}
		writer->directory = grown;
		writer->directory_capacity = capacity;
	}
	memcpy(writer->directory + writer->directory_size, central, sizeof(central));
	memcpy(writer->directory + writer->directory_size + sizeof(central), name, name_length);
	writer->directory_size += sizeof(central) + name_length;
	writer->offset += (unsigned long)(sizeof(header) + name_length + size);
	writer->entries++;
	return 1;
}

static int zip_finish(struct zip_writer *writer)
{
	unsigned char end[22];

	memset(end, 0, sizeof(end));
	put_long(end, 0x06054b50);
	put_word(end + 8, writer->entries);
	put_word(end + 10, writer->entries);
	put_long(end + 12, (unsigned long)writer->directory_size);
	put_long(end + 16, writer->offset);
	if ((writer->directory_size &&
			SDL_WriteIO(writer->out, writer->directory, writer->directory_size) != writer->directory_size) ||
		SDL_WriteIO(writer->out, end, sizeof(end)) != sizeof(end))
	{
		snprintf(writer->reason, sizeof(writer->reason), "could not write the .zip (%s)", SDL_GetError());
		return 0;
	}
	return 1;
}

/* a save of the root into the zip: a file whose place is itself */
static int export_visit(void *context, const char *relative, const char *path)
{
	struct zip_writer *writer = context;
	char place[SAVE_TRANSFER_PATH], name[SAVE_TRANSFER_PATH + 8];
	size_t size = 0;
	void *data;
	int ok;

	if (!save_transfer_destination(relative, place, sizeof(place)) || SDL_strcasecmp(place, relative) != 0)
		return 1;
	if (writer->entries >= SAVE_TRANSFER_MAXIMUM_FILES)
	{
		snprintf(writer->reason, sizeof(writer->reason), "more than %d save files", SAVE_TRANSFER_MAXIMUM_FILES);
		return 0;
	}
	data = SDL_LoadFile(path, &size);
	if (!data)
	{
		snprintf(writer->reason, sizeof(writer->reason), "could not read %s (%s)", path, SDL_GetError());
		return 0;
	}
	snprintf(name, sizeof(name), "save/%s", relative);
	ok = size <= SAVE_TRANSFER_MAXIMUM_BYTES && zip_add(writer, name, data, (unsigned long)size);
	SDL_free(data);
	return ok;
}

int save_transfer_export(const char *save_root, const char *zip, char *result, size_t result_size)
{
	struct zip_writer writer;
	int ok;

	memset(&writer, 0, sizeof(writer));
	writer.out = SDL_IOFromFile(zip, "wb");
	if (!writer.out)
	{
		snprintf(result, result_size, "Could not write %s (%s).", zip, SDL_GetError());
		return -1;
	}
	ok = walk_folder(save_root, export_visit, &writer) && zip_finish(&writer);
	if (!SDL_CloseIO(writer.out))
		ok = 0;
	free(writer.directory);
	if (!ok)
	{
		SDL_RemovePath(zip);
		snprintf(result, result_size, "Saves not exported: %s.", writer.reason[0] ? writer.reason : "the folder could not be read");
		return -1;
	}
	if (!writer.entries)
	{
		SDL_RemovePath(zip);
		snprintf(result, result_size, "There are no saves yet in %s.", save_root);
		return 0;
	}
	snprintf(result, result_size, "%lu save files exported to %s.", writer.entries, zip);
	return (int)writer.entries;
}

/* ---------- the import put in place */

struct place
{
	const char *save_root;
	char reason[512];
};

static int place_visit(void *context, const char *relative, const char *path)
{
	struct place *place = context;
	char target[SAVE_TRANSFER_PATH];

	path_join(target, sizeof(target), place->save_root, relative);
	if (!make_parent(target))
	{
		snprintf(place->reason, sizeof(place->reason), "could not create the folder of %s (%s)", target, SDL_GetError());
		return 0;
	}
	SDL_RemovePath(target);
	if (!SDL_RenamePath(path, target))
	{
		SDL_IOStream *in = SDL_IOFromFile(path, "rb");
		long long copied = in ? copy_file(in, target, SAVE_TRANSFER_MAXIMUM_BYTES, place->reason, sizeof(place->reason)) : -1;

		if (in)
			SDL_CloseIO(in);
		if (copied < 0)
		{
			if (!in)
				snprintf(place->reason, sizeof(place->reason), "could not read %s (%s)", path, SDL_GetError());
			return 0;
		}
	}
	return 1;
}

int save_transfer_import(const char *source, int folder, const char *save_root, const char *backups,
	char *result, size_t result_size)
{
	struct import import;
	struct place place;
	char backup[SAVE_TRANSFER_PATH], backup_note[SAVE_TRANSFER_PATH + 64] = "";
	char stamp[64];
	int ok;

	memset(&import, 0, sizeof(import));
	path_join(import.stage, sizeof(import.stage), save_root, "import.tmp");
	remove_tree(import.stage);
	if (!SDL_CreateDirectory(import.stage))
	{
		snprintf(result, result_size, "Saves not changed: could not prepare %s (%s).", import.stage, SDL_GetError());
		return 0;
	}
	ok = folder ? walk_folder(source, import_folder_visit, &import) : import_zip(&import, source);
	if (!ok)
	{
		remove_tree(import.stage);
		snprintf(result, result_size, "Saves not changed: %s.", import.reason[0] ? import.reason : "it could not be read");
		return 0;
	}
	if (!import.files)
	{
		remove_tree(import.stage);
		snprintf(result, result_size, "Saves not changed: no saves found in it (looked for a save, z, saved or "
			"player_profiles folder, savegame.bin, or an Xbox UDATA folder).");
		return 0;
	}
	/* the saves already there kept, first */
	{
		SDL_Time now = 0;
		SDL_DateTime date;

		if (SDL_GetCurrentTime(&now) && SDL_TimeToDateTime(now, &date, true))
			snprintf(stamp, sizeof(stamp), "%04d-%02d-%02d_%02d-%02d-%02d", date.year, date.month, date.day,
				date.hour, date.minute, date.second);
		else
			snprintf(stamp, sizeof(stamp), "%lld", (long long)now);
	}
	SDL_CreateDirectory(backups);
	snprintf(backup, sizeof(backup), "%s/saves-%s.zip", backups, stamp);
	{
		char exported[512];
		int files = save_transfer_export(save_root, backup, exported, sizeof(exported));

		if (files < 0)
		{
			remove_tree(import.stage);
			snprintf(result, result_size, "Saves not changed: the saves already here could not be backed up (%s)", exported);
			return 0;
		}
		if (files > 0)
			snprintf(backup_note, sizeof(backup_note), ". Your saves before this are in %s", backup);
	}
	place.save_root = save_root;
	place.reason[0] = '\0';
	ok = walk_folder(import.stage, place_visit, &place);
	remove_tree(import.stage);
	if (!ok)
	{
		snprintf(result, result_size, "Saves only partly brought in: %s%s.", place.reason, backup_note);
		return 0;
	}
	snprintf(result, result_size, "%d save file%s brought in%s%s%s%s%s%s.", import.files, import.files == 1 ? "" : "s",
		import.profile_count ? " (profiles: " : "", import.profiles, import.profile_count ? ")" : "",
		import.checkpoint ? ", the campaign checkpoint" : "",
		import.skipped ? "; other files left out" : "", backup_note);
	return 1;
}

#endif
