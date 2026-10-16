/*
HALO_PORT_VERSION.H

Test72: this fork's version as the desktop builds show it (the desktop
launcher, desktop_launcher.c), the same as the Android packages' versionName
and versionCode (port/android/app/build.gradle); the release script keeps
them in step (tools/test_test72_launcher.py checks it).
*/

#ifndef HALO_PORT_VERSION_H
#define HALO_PORT_VERSION_H

#define HALO_PORT_VERSION "1.0.39-test72"
#define HALO_PORT_VERSION_CODE 84
/* where the fork's releases are (the Android app's UpdatePolicy.REPOSITORY) */
#define HALO_PORT_REPOSITORY "moistman42069/HaloCE-Quest-VR"

#endif
