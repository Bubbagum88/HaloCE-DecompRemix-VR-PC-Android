/*
VR_BULLET_TIME.C

Test70: BULLET TIME (the owner: optional slow motion; "if global slow motion
cannot safely work in multiplayer/co-op, restrict it"). While its button is
held (or toggled on) the game's time runs at TIME SCALE: every tick of the
world is the same as ever, only fewer of them a second, so physics stays as
stable as at full speed, and the head and hands, drawn each display frame
between ticks (render_interpolation.c), stay as responsive as ever.

A local game only: never a network game's client or host, co-op or
multiplayer (their machines must tick together). Not in a menu, a cutscene
or while paused; in a seat as on foot (Test72: its button, R UP too, works
there: vr_frame.c's bullet_stick_up). Eased in and out over a sixth of a
second.

Test73: the slowing is game_time.c's local scale, on top of the game's own
speed, never written into it (game_time_set_local_scale). Before, BULLET TIME
set the game's speed itself, which is the game state's: a checkpoint saved
during it kept the slow motion, a death's revert brought it back with BULLET
TIME off (so turning it off, or the setting, gave nothing back), and pressing
its button slowed that slow motion again (a player's report: "stuck in bullet
time", "only causes the slo motion to double up"). Now a checkpoint keeps the
game's own speed only; a speed a map's script sets (game_speed) is the game's
own, and BULLET TIME slows it as it slows 1, and gives it back as it is. A
saved game taken (a revert, a continue, a core) starts with BULLET TIME off
(game_state_call_after_load_procs: vr_bullet_time_reset), and one an earlier
build left slowed is put back (game_time_after_load).
*/

#ifdef HALO_VR

#include "cseries.h"
#include "game/game.h"
#include "game/players.h"
#include "cutscene/cinematics.h"
#include "camera/director.h"
#include "network_coop.h"
#include "../src/vr.h"
#include "../src/port_config.h"
#include "vr_bullet_time.h"
#include <math.h>

void platform_log(char const *format, ...);
unsigned long system_milliseconds(void);

static struct
{
	boolean on, toggled, was_held;
	real blend;
	unsigned long last_ms;
} bullet = { FALSE, FALSE, FALSE, 0.0f, 0 };

static boolean vr_bullet_time_allowed(void)
{
	short local = local_player_get_next(NONE);
	return config_boolean("vr.bullet_time") && vr_active() && vr_aiming() &&
		game_connection() == _game_connection_local && !network_coop_active() &&
		!cinematic_in_progress() && local != NONE && !director_inhibited_input(local) &&
		!game_time_get_paused();
}

/* the game's own speed, unslowed, back at once */
static void vr_bullet_time_release(void)
{
	game_time_set_local_scale(1.0f);
	bullet.blend = 0.0f;
}

void vr_bullet_time_frame(void)
{
	unsigned long now = system_milliseconds();
	real seconds = bullet.last_ms ? (real)(now - bullet.last_ms) * 0.001f : 0.0f;
	boolean allowed = vr_bullet_time_allowed(), held = allowed && vr_bullet_time_held(), want;
	real scale, target;

	bullet.last_ms = now;
	if (!(seconds >= 0.0f && seconds < 0.5f))
		seconds = 0.0f;
	if (!allowed)
	{
		if (bullet.on || bullet.blend > 0.0f)
			platform_log("VR bullet time: off (%s)", config_boolean("vr.bullet_time") ? "not here" : "turned off");
		vr_bullet_time_release();
		bullet.on = bullet.toggled = bullet.was_held = FALSE;
		return;
	}
	if (config_boolean("vr.bullet_time_toggle"))
	{
		if (held && !bullet.was_held)
			bullet.toggled = !bullet.toggled;
		want = bullet.toggled;
	}
	else
		want = held;
	bullet.was_held = held;
	if (want != bullet.on)
	{
		bullet.on = want;
		vr_haptic(0, want ? 0.45f : 0.25f, 0.06f);
		vr_haptic(1, want ? 0.45f : 0.25f, 0.06f);
		platform_log("VR bullet time: %s", want ? "on" : "off");
	}
	if (!bullet.on && bullet.blend <= 0.0f)
	{
		vr_bullet_time_release();
		return;
	}
	scale = (real)config_real("vr.bullet_time_scale");
	scale = isfinite(scale) ? PIN(scale, 0.2f, 0.8f) : 0.4f;
	target = bullet.on ? 1.0f : 0.0f;
	/* eased in and out over about a sixth of a second */
	bullet.blend += (target - bullet.blend) * MIN(1.0f, seconds / 0.06f);
	if (fabsf(bullet.blend - target) < 0.02f)
		bullet.blend = target;
	if (!bullet.on && bullet.blend <= 0.0f)
	{
		vr_bullet_time_release();
		return;
	}
	game_time_set_local_scale(1.0f - bullet.blend * (1.0f - scale));
}

void vr_bullet_time_reset(void)
{
	vr_bullet_time_release();
	bullet.on = bullet.toggled = bullet.was_held = FALSE;
	bullet.last_ms = 0;
}

#else

#include "cseries.h"
#include "vr_bullet_time.h"
void vr_bullet_time_frame(void) {}
void vr_bullet_time_reset(void) {}

#endif
