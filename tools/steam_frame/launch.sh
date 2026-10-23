#!/bin/bash
# HaloCE Quest VR on the Steam Frame, started from the Steam library (the
# shortcut tools/steam_frame/install.sh adds). Adapted from ringfall-mjolnir-vr's
# port/android/steam_frame_launch.sh (Stefan Maier / Cesarus85, AGPL-3.0 or
# later; docs/VR_ARCHITECTURE.md, "Test73: the Steam Frame plan"), as Steam
# starts an Android title of its own: Lepton runs the APK in a container of its
# own and installs it anew whenever the APK is newer than the installed one.
# The game's data, settings, saves and logs: ~/Documents/HaloCEQuestVR
# (Lepton.java): each run's log in logs/ (RunLog.java), this script's in
# launcher.log, the container's Android log in logcat.txt. Run on a Frame: a
# player's Test73 log (2026-10-22), started from Steam, quit from the menu.
#
# (a container of its own, not the shortcut's id: with that, SteamVR's client
# in the container waited on xrCreateInstance, ringfall's finding; not
# ringfall's own 4290000001 either, so both games can be installed)
export SteamAppId="${HALO_LEPTON_APP_ID:-4290007373}"
# (what Steam gives an Android title of its own and a non-Steam game not: the
# app's data in the container links to the compat data path's internal/, a
# dangling link without it; and the shader paths, Lepton reads the dump path
# against the other)
export STEAM_COMPAT_DATA_PATH="$HOME/.local/share/Steam/steamapps/compatdata/$SteamAppId"
export STEAM_COMPAT_SHADER_PATH="$HOME/.local/share/Steam/steamapps/shadercache/$SteamAppId"
mkdir -p "$STEAM_COMPAT_DATA_PATH/internal" "$STEAM_COMPAT_SHADER_PATH"
unset STEAM_FOSSILIZE_DUMP_PATH LD_PRELOAD
LEPTON="$HOME/.local/share/Steam/steamapps/common/Lepton/lepton"
DATA="$HOME/Documents/HaloCEQuestVR"
APK="$DATA/HaloCEQuestVR.apk"
LOG="$DATA/launcher.log"
# (written by the game when the player quits it, sdl_platform.c: no start again)
QUIT="$DATA/quit_requested.txt"
rm -f "$QUIT"
CONTEXT="steamlaunch-$SteamAppId"

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }
log "start (pid $$, parent $PPID)"

if [ ! -x "$LEPTON" ] || [ ! -f "$APK" ]; then
    log "missing: $LEPTON or $APK (run the installer again)"
    exit 1
fi

# Steam's "Exit game" ends the game's processes as Steam knows them (this
# script, under Steam's reaper), not the container, which podman runs: a
# signal here is passed on to Lepton, and a watcher of its own takes the
# container down once this script is gone (killed)
stopping=0
child=0
stop()
{
    log "signal $1"
    stopping=1
    [ "$child" -gt 0 ] && kill -TERM "$child" 2>/dev/null
}
trap 'stop TERM' TERM
trap 'stop INT' INT
trap 'stop HUP' HUP

script=$$
setsid bash -c '
    while kill -0 '"$script"' 2>/dev/null; do sleep 1; done
    echo "$(date "+%F %T") watcher: the game was ended, so its container" >> "'"$LOG"'"
    "'"$LEPTON"'" kill "'"$CONTEXT"'" >/dev/null 2>&1
' </dev/null >/dev/null 2>&1 &

# the game's log while it runs (Lepton's logcat of its container), for
# looking into problems: logcat.txt, anew each start
LOGCAT="$DATA/logcat.txt"
: > "$LOGCAT"
setsid bash -c '
    while kill -0 '"$script"' 2>/dev/null; do
        "'"$LEPTON"'" logcat "'"$CONTEXT"'" 2>/dev/null | grep -v "^ERROR: \|^steamlaunch-\|^$" >> "'"$LOGCAT"'"
        sleep 3
    done
' </dev/null >/dev/null 2>&1 &

run()
{
    "$LEPTON" waitforexitandrun -- "$APK" &
    child=$!
    # (wait returns early when a signal comes: until Lepton is gone)
    while kill -0 "$child" 2>/dev/null; do
        wait "$child"
    done
    child=0
}

# (a start that ends within 30 s is tried again, up to three times, unless the
# player quit: a new APK's first start may only install it, a start right
# after a game that was ended hard can fail in SteamVR, which then needs a
# moment, and Lepton drops the install of a container ended that soon)
for attempt in 1 2 3; do
    started=$SECONDS
    run
    if (( stopping || SECONDS - started >= 30 )) || [ -e "$QUIT" ]; then
        break
    fi
    log "attempt $attempt ended within $((SECONDS - started)) s: again"
    sleep 5
done
rm -f "$QUIT"
log "end"
