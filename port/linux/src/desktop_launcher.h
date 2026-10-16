/*
DESKTOP_LAUNCHER.H

Test72: the desktop builds' launcher (Windows flat and PC VR, Linux), shown
before the game's own window: play (here, or the other build: halo.exe and
halo-vr.exe share one folder and one library), the game data (an Xbox disc
image imported, verified and repaired), the custom campaigns (the Android
app's: the same recipes, folders and checks), settings, PC VR, What's New
and updates. desktop_launcher.c.
*/

#ifndef DESKTOP_LAUNCHER_H
#define DESKTOP_LAUNCHER_H

/* a file the launcher shows or reads (tools/embed_assets.py): the Android
app's What's New and campaign recipes, the same files */
struct desktop_launcher_file
{
	const char *name;
	const unsigned int *data;
	unsigned int size;
};

extern const struct desktop_launcher_file desktop_launcher_files[];
extern const unsigned int desktop_launcher_file_count;

/* whether the launcher comes first this run (launcher.show, and not a run
nobody watches: debug.hidden_window, debug.exit_after, debug.menu_open,
HALO_NETWORK_TEST) */
int desktop_launcher_wanted(void);
/* the launcher, until the player plays (it returns: the game goes on here)
or quits, or plays the other build (the process ends) */
void desktop_launcher_run(void);
/* while the launcher runs, a missing maps folder is its to offer
(platform_offer_game_data leaves it) */
int desktop_launcher_active(void);

#endif
