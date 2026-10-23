#!/bin/bash
# HaloCE Quest VR's installer for the Steam Frame, run in its Desktop Mode from
# the Steam Frame bundle (tools/steam_frame/bundle.py: this script, launch.sh,
# HaloCEQuestVR.apk and "Install HaloCE Quest VR.desktop", in a folder
# HaloCEQuestVR-SteamFrame unpacked in Downloads). Adapted from
# ringfall-mjolnir-vr's port/android/steam_frame_install.sh (Stefan Maier /
# Cesarus85, AGPL-3.0 or later). Everything is answered with dialogs, no
# keyboard:
# - the game in ~/Documents/HaloCEQuestVR (Lepton.java), its APK replaced
#   (Lepton installs a newer one at the next start), so running the installer
#   again with a newer bundle updates the game; settings, saves and game data
#   stay;
# - the game data: the game unpacks the largest disc image (.iso or .xiso) it
#   finds in Downloads, Documents or the Desktop on its first start (Lepton.java,
#   XisoExtractor); the installer says whether it sees one;
# - the game in the Steam library, unless it is there already: added by Steam
#   itself (steam://addnonsteamgame, as SteamOS's "Add to Steam" does), from a
#   desktop file beside the game. Steam is not closed: it keeps its shortcuts
#   in memory and writes them back, and on the Steam Frame Desktop Mode runs
#   inside Gaming Mode's session, which ends with Steam.
# HALO_UNATTENDED=1 answers every question with its default and prints instead
# of showing dialogs, for testing over adb or ssh; it leaves Steam alone.
# Not yet run on a Frame.

BUNDLE="$(cd "$(dirname "$0")" && pwd)"
GAME_DIR="$HOME/Documents/HaloCEQuestVR"
STEAM_DIR="$HOME/.local/share/Steam"
LEPTON="$STEAM_DIR/steamapps/common/Lepton/lepton"
TITLE="HaloCE Quest VR"
NAME="HaloCE Quest VR"
APK_NAME="HaloCEQuestVR.apk"
LAUNCHER="halo-ce-quest-vr.sh"
# (the desktop file Steam adds the game from)
NAME_FILE="HaloCE Quest VR"

# what the installer did, for looking into problems: written to /tmp while it
# runs, then kept beside the game as install.log
LOG="/tmp/halo-ce-quest-vr-install.log"
: > "$LOG"
log() { echo "$(date '+%F %T') $*" >> "$LOG"; }
keep_log() { [ -d "$GAME_DIR" ] && cp -f "$LOG" "$GAME_DIR/install.log" 2>/dev/null; }
trap keep_log EXIT
log "installer from $BUNDLE"

# whether Steam runs: its pid file (~/.steam/steam.pid), or its client's
# process (ubuntu12_32/steam: the process is not always named "steam")
steam_running()
{
    local pid
    pid="$(cat "$HOME/.steam/steam.pid" 2>/dev/null)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    pgrep -f 'ubuntu12_32/steam( |$)' >/dev/null || pgrep -x steam >/dev/null
}

unattended() { [ "${HALO_UNATTENDED:-0}" = 1 ] || ! command -v zenity >/dev/null; }

info()
{
    if unattended; then printf "info: %b\n" "$1"; else zenity --info --title="$TITLE" --width=460 --text="$1"; fi
}

fail()
{
    log "error: $1"
    if unattended; then printf "error: %b\n" "$1" >&2; else zenity --error --title="$TITLE" --width=460 --text="$1"; fi
    exit 1
}

# yes/no; unattended: the default given ($2, "yes" or "no")
ask()
{
    if unattended; then [ "$2" = yes ]; return; fi
    zenity --question --title="$TITLE" --width=460 --text="$1"
}

# a disc image where the game looks for one (Lepton.imageFolders): the largest
# (the game's image is a few GB; anything under 500 MB is not one)
find_image()
{
    find "$HOME/Downloads" "$HOME/Documents" "$HOME/Desktop" "$GAME_DIR" -maxdepth 1 -type f \
        \( -iname '*.iso' -o -iname '*.xiso' \) -size +500M -printf '%s\t%p\n' 2>/dev/null |
        sort -rn | head -n 1 | cut -f2-
}

# the Steam users' shortcut files (userdata/0 is no user)
shortcut_files()
{
    local config
    for config in "$STEAM_DIR"/userdata/*/config; do
        case "$config" in */userdata/0/*) continue ;; esac
        [ -f "$config/shortcuts.vdf" ] && echo "$config/shortcuts.vdf"
    done
}

# whether a Steam user's library holds the game's launcher
have_shortcut()
{
    local file
    while read -r file; do
        grep -qaF "$GAME_DIR/$LAUNCHER" "$file" && return 0
    done < <(shortcut_files)
    return 1
}

# the game added to the library of the Steam user logged in, by Steam (it must
# run), from a desktop file beside the game
add_shortcut()
{
    local desktop="$GAME_DIR/$NAME_FILE.desktop" url
    printf '[Desktop Entry]\nType=Application\nName=%s\nExec=%s\nPath=%s\nIcon=steam\nTerminal=false\n' \
        "$NAME" "$GAME_DIR/$LAUNCHER" "$GAME_DIR" > "$desktop" && chmod 755 "$desktop" || return 1
    url="steam://addnonsteamgame/$(python3 -I -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$desktop")"
    log "asking Steam: $url"
    # (Steam's own "Add to Steam" touches this first: steamos-add-to-steam)
    touch /tmp/addnonsteamgamefile
    steam "$url" >/dev/null 2>&1 &
    for _ in $(seq 30); do have_shortcut && break; sleep 1; done
    have_shortcut
}

# --- the game

[ -x "$LEPTON" ] || fail "Lepton, which runs Android games on the Steam Frame, was not found.\n\nStart any Android game from the Steam store once, then run this installer again."
for file in "$APK_NAME" launch.sh; do
    [ -f "$BUNDLE/$file" ] || fail "The installer is incomplete ($file is missing). Unpack the bundle again."
done

if [ -f "$GAME_DIR/$APK_NAME" ]; then
    ask "$NAME is installed already. Update it to this version?\n\n(Your settings, saves and game data stay.)" yes || exit 0
else
    ask "This installs $NAME on your Steam Frame.\n\nYou need your own disc image of Halo: Combat Evolved for the original Xbox (an .iso or .xiso file), for example in Downloads.\n\nContinue?" yes || exit 0
fi

mkdir -p "$GAME_DIR" || fail "Could not create $GAME_DIR."
# (the game runs in Lepton's container as a user of its own)
chmod 777 "$GAME_DIR"
cp "$BUNDLE/launch.sh" "$GAME_DIR/$LAUNCHER.tmp" && chmod 755 "$GAME_DIR/$LAUNCHER.tmp" &&
    mv -f "$GAME_DIR/$LAUNCHER.tmp" "$GAME_DIR/$LAUNCHER" || fail "Could not write $GAME_DIR/$LAUNCHER."
# (newer than the installed one: Lepton installs it at the next start)
cp "$BUNDLE/$APK_NAME" "$GAME_DIR/$APK_NAME.tmp" && chmod 666 "$GAME_DIR/$APK_NAME.tmp" &&
    mv -f "$GAME_DIR/$APK_NAME.tmp" "$GAME_DIR/$APK_NAME" && touch "$GAME_DIR/$APK_NAME" ||
    fail "Could not write $GAME_DIR/$APK_NAME (is the storage full?)."

# --- the game data (the game unpacks it on its first start)

if [ ! -f "$GAME_DIR/maps/ui.map" ]; then
    image="$(find_image)"
    if [ -n "$image" ]; then
        log "disc image for the first start: $image"
        image_note="\n\nOn its first start the game copies what it needs out of\n$image\n(a few minutes; the headset shows nothing meanwhile)."
    else
        info "No disc image was found in Downloads, Documents or on the Desktop.\n\nPut your disc image of Halo: Combat Evolved for the Xbox (.iso or .xiso) in Downloads before you start the game: it copies what it needs out of it on its first start."
    fi
fi

# --- Steam

if have_shortcut; then
    log "the Steam shortcut is there"
elif unattended; then
    echo "info: the Steam shortcut is missing (not added unattended)"
elif ! steam_running; then
    info "Steam is not running, so $NAME could not be added to your library.\n\nStart Steam and run the installer again."
else
    add_shortcut || fail "Steam did not add $NAME to your library. Run the installer again; if it happens again, add\n$GAME_DIR/$NAME_FILE.desktop\nwith Steam's \"Add a Non-Steam Game\"."
fi

if unattended; then
    echo "info: installed in $GAME_DIR (each run's log in $GAME_DIR/logs)"
    exit 0
fi
# (Test73b: where the logs are, said where the player looks once)
if ask "$NAME is installed.${image_note:-}\n\nSwitch to Gaming Mode now? Start $NAME from your library there (under Non-Steam). To quit, use the main menu's QUIT GAME, or Steam's Exit game.\n\nIf something goes wrong, each run's log is in\n$GAME_DIR/logs\n(the newest is the last run)." yes; then
    steamos-session-select gamescope >/dev/null 2>&1 ||
        info "Switch to Gaming Mode yourself (the \"Return to Gaming Mode\" icon or the power menu)."
fi
