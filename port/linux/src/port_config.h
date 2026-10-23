/*
PORT_CONFIG.H

The native ports' settings, read from config.toml (port_config.c): next to
the executable on the desktop, in the data folder (the one holding maps/)
on Android. A missing file is written with the defaults. Each setting can
also be set for one run with its HALO_* environment variable, which wins
over the file (the tools and the Android app pass settings that way).

Settings are named "section.key", as in the file: "display.vsync".
*/

#ifndef PORT_CONFIG_H
#define PORT_CONFIG_H
#include <stddef.h>

int config_write(const char *name, const char *value);
int config_text(const char *name, char *text, size_t size);
int config_default(const char *name, char *text, size_t size);
void config_folder(char *path, size_t size);
char *config_file_read(const char *path, size_t *size);
unsigned long config_changes(void);
/* Test72: values held over settings' own, never written (port_config.c) */
int config_override(const char *name, const char *text);
int config_is_overridden(const char *name);
void config_override_clear(void);
/* debug.fixed_step (also in halo_linux_source_fixups.h, for the game's
sources) */
int halo_fixed_step(void);

int config_boolean(const char *name);
long config_integer(const char *name);
double config_real(const char *name);
/* never NULL; "" when unset */
const char *config_string(const char *name);
/* the built-in default of a real setting (0 when unknown) */
double config_default_real(const char *name);
/* sets a boolean setting, and writes it into config.toml (only its line
changes); 1 on success */
int config_write_boolean(const char *name, int value);
/* as config_write_boolean, for a real or a string (no quotes or
backslashes in it) */
int config_write_real(const char *name, double value);
int config_write_string(const char *name, const char *value);
/* a setting compared with, or written from, its value as text ("true",
"0.2", "floating"), as the setting's own type; for menu rows that set
several settings at once */
int config_matches(const char *name, const char *text);
int config_write_text(const char *name, const char *text);

#ifdef HALO_VR
void config_vr_vehicle_defaults(void);
#endif
/* Test73 (10d): VR INTERACTIONS (net.physical_interactions) turned on once in
a config saved before it was on by default (game.c game_initialize) */
void config_vr_interactions_default(void);

#endif
