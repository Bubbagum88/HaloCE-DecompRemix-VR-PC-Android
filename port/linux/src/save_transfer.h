/*
SAVE_TRANSFER.H

The desktop launcher's saves in and out (save_transfer.c), as the Android
launcher's SaveTransfer.java.
*/

#ifndef SAVE_TRANSFER_H
#define SAVE_TRANSFER_H

#include <stddef.h>

/* the place under the save root of a file at `path` (a zip's entry or a
folder's file, '/' or '\' separated), written to `out`; 0 when it is not a
save (a cache, another file) or not a safe name */
int save_transfer_destination(const char *path, char *out, size_t size);

/* the saves in `source` (a .zip, or a folder when `folder`) brought into
`save_root`, after the saves already there are backed up as a .zip in
`backups`; files of the same name replaced, others kept. 1 on success, the
outcome (or why nothing changed) in `result` */
int save_transfer_import(const char *source, int folder, const char *save_root, const char *backups,
	char *result, size_t result_size);

/* the saves of `save_root` (not its caches) as a .zip at `zip`; the number of
files, -1 on failure (why in `result`) */
int save_transfer_export(const char *save_root, const char *zip, char *result, size_t result_size);

#endif
