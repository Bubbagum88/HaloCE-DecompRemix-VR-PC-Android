/* Content-matched local MCC paths; the host's name stays on the wire. */
#include "cseries.h"
#include "errors.h"
#include "game/game.h"
#include "networking/network_game_manager.h"
#include "interface/ui_widget.h"
#include "mcc_cache.h"
#include "mcc_identity.h"
#include "mcc_maps.h"
#include "mcc_package.h"
#include "mcc_precache.h"
#include "mcc_ui_network.h"
#include <string.h>

#define MCC_IDENTITY_MAX_CANDIDATES 16
static struct {
    char name[64];
    unsigned char digest[32];
    struct mcc_precache_snapshot files;
    int valid;
} mcc_host_identity;
static struct {
    char session[64], local[64];
    unsigned char digest[32];
    struct mcc_precache_snapshot files;
} mcc_client_identity;

static int mcc_identity_error(char const *message)
{
    wchar_t text[256];
    unsigned i;
    error(_error_silent,"mcc identity: %s",message);
    for (i=0;message[i] && i<255;i++) text[i]=(unsigned char)message[i];
    text[i]=0;
    display_error_text_when_main_menu_loaded(text);
    return 0;
}

void mcc_identity_disconnect(void)
{
    memset(&mcc_client_identity,0,sizeof(mcc_client_identity));
    memset(&mcc_host_identity,0,sizeof(mcc_host_identity));
    mcc_cache_precache_clear();
}

char const *mcc_identity_local_name(char const *name)
{
    char canonical[64];
    if (mcc_client_identity.session[0] && mcc_package_name(name,canonical) &&
        !csstrcasecmp(canonical,mcc_client_identity.session)) return mcc_client_identity.local;
    return name;
}

static unsigned char const *mcc_identity_expected(char const *name)
{
    char canonical[64];
    if (!mcc_package_name(name,canonical)) return NULL;
    if (mcc_client_identity.session[0] &&
        (!csstrcasecmp(canonical,mcc_client_identity.session) ||
         !csstrcasecmp(canonical,mcc_client_identity.local))) return mcc_client_identity.digest;
    return NULL;
}

/* This port: OpenCE network 28's game advertisement has no MCC fingerprint
 * (mcc_offline.h): a game on an MCC map is never offered; any other passes. */
void const *mcc_identity_host_settings(void const *settings,long bytes,struct network_game *copy)
{
    struct network_game const *game=settings;
    if (!game || bytes!=sizeof(*game)) return NULL;
    memcpy(copy,game,sizeof(*copy));
    mcc_host_identity.valid=0;
    if (mcc_level_name(game->map.name)) {
        mcc_identity_error("Halo 1 MCC maps play solo in this build: they cannot be hosted online.");
        return NULL;
    }
    return copy;
}

static int mcc_identity_matches(char const *name,unsigned char const digest[32],
    struct mcc_precache_snapshot *validated)
{
    struct mcc_precache_snapshot before,after;
    unsigned char actual[32];
    int ok=mcc_precache_snapshot(name,&before) && mcc_content_probe(name,actual) &&
        !memcmp(actual,digest,32) && mcc_precache_snapshot(name,&after) &&
        !memcmp(&before,&after,sizeof(before));
    if (ok && validated) *validated=after;
    return ok;
}

int mcc_identity_accept(struct network_game const *game)
{
    char session[64],selected[64];
    char const *leaf,*candidate,*candidate_leaf;
    short i,count;
    unsigned candidates=0,matches=0;
    struct mcc_precache_snapshot selected_files;
    /* This port: no MCC fingerprint travels (mcc_offline.h); a game on an MCC
     * map is never joined, any other is not this file's to judge. */
    static unsigned char const mcc_content_sha256[32];
    memset(&mcc_client_identity,0,sizeof(mcc_client_identity));
    mcc_cache_precache_clear();
    if (!mcc_level_name(game->map.name)) return 1;
    if (mcc_level_name(game->map.name))
        return mcc_identity_error("Halo 1 MCC maps play solo in this build: a game on one cannot be joined.");
    if (!mcc_package_name(game->map.name,session))
        return mcc_identity_error("The host did not supply a valid MCC content identity.");
    /* A verified exact installation is unambiguous even with duplicate copies. */
    if (mcc_identity_matches(session,mcc_content_sha256,&selected_files)) {
        strcpy(selected,session);
        matches=1;
    } else {
        leaf=strrchr(session,'\\')+1;
        mcc_maps_rescan();
        count=mcc_maps_count(FALSE);
        /* Bound work before hashing any fallback candidates. */
        for (i=0;i<count;i++) {
            candidate=mcc_maps_level_name(i);
            candidate_leaf=strrchr(candidate,'\\')+1;
            if (!csstrcasecmp(leaf,candidate_leaf) && ++candidates>MCC_IDENTITY_MAX_CANDIDATES)
                return mcc_identity_error("Too many MCC maps share this filename. Keep one matching package installed and retry.");
        }
        for (i=0;i<count;i++) {
            candidate=mcc_maps_level_name(i);
            candidate_leaf=strrchr(candidate,'\\')+1;
            if (csstrcasecmp(leaf,candidate_leaf) || !csstrcasecmp(candidate,session)) continue;
            if (mcc_identity_matches(candidate,mcc_content_sha256,&selected_files)) {
                strcpy(selected,candidate);
                if (++matches>1) return mcc_identity_error("Several local MCC packages match the host. Keep one matching copy, or use the host's package folder name.");
            }
        }
    }
    if (!matches) return mcc_identity_error("No local MCC map and required resources match the host's SHA-256 fingerprint. Install the same complete package; its folder name may differ.");
    mcc_client_identity.files=selected_files;
    strcpy(mcc_client_identity.session,session);
    strcpy(mcc_client_identity.local,selected);
    memcpy(mcc_client_identity.digest,mcc_content_sha256,32);
    error(_error_silent,"mcc identity: %s resolved to %s (SHA-256 matched)",session,selected);
    return 1;
}

int mcc_identity_check(char const *name)
{
    unsigned char const *expected=mcc_identity_expected(name);
    struct mcc_precache_snapshot files;
    if (!expected) return 1;
    if (!mcc_precache_snapshot(mcc_client_identity.local,&files)) return 0;
    if (!memcmp(&files,&mcc_client_identity.files,sizeof(files))) return 1;
    return mcc_identity_matches(mcc_client_identity.local,expected,NULL);
}

int mcc_identity_loaded(char const *name,struct mcc_runtime *runtime)
{
    unsigned char actual[32];
    unsigned char const *expected=mcc_identity_expected(name);
    if (!expected) return game_connection()!=_game_connection_network_client &&
        game_connection()!=_game_connection_network_server;
    return mcc_resources_fingerprint(runtime,actual) && !memcmp(actual,expected,32);
}

/* This port: GulchCE restarts an MCC map hosted online through the server's
 * round transition (mcc_ui_network.inl, included by its server manager).
 * An MCC map is never hosted here (mcc_offline.h), so there is no such game
 * to restart: the pause menu's and the scripts' restarts of a solo game
 * reset the map themselves. */
boolean mcc_ui_restart_network_game(void)
{
    return FALSE;
}

boolean mcc_ui_network_restart_pregame(void)
{
    return FALSE;
}
