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
there: vr_frame.c's bullet_stick_up). A speed a map's script set (game_speed) is kept and
given back; if something else changes the speed meanwhile, that is left as it
is. Eased in and out over a sixth of a second.
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
real game_time_get_speed(void);
void game_time_set_speed(real speed);

static struct
{
	boolean on, toggled, was_held, owns_speed;
	real base_speed, applied, blend;
	unsigned long last_ms;
} bullet = { FALSE, FALSE, FALSE, FALSE, 1.0f, 1.0f, 0.0f, 0 };

static boolean vr_bullet_time_allowed(void)
{
	short local = local_player_get_next(NONE);
	return config_boolean("vr.bullet_time") && vr_active() && vr_aiming() &&
		game_connection() == _game_connection_local && !network_coop_active() &&
		!cinematic_in_progress() && local != NONE && !director_inhibited_input(local) &&
		!game_time_get_paused();
}

static void vr_bullet_time_release(void)
{
	/* the game's own speed back, unless another changed it meanwhile */
	if (bullet.owns_speed && fabsf(game_time_get_speed() - bullet.applied) < 0.001f)
		game_time_set_speed(bullet.base_speed);
	bullet.owns_speed = FALSE;
	bullet.blend = 0.0f;
}

void vr_bullet_time_frame(void)
{
	unsigned long now = system_milliseconds();
	real seconds = bullet.last_ms ? (real)(now - bullet.last_ms) * 0.001f : 0.0f;
	boolean allowed = vr_bullet_time_allowed(), held = allowed && vr_bullet_time_held(), want;
	real scale, target, speed;

	bullet.last_ms = now;
	if (!(seconds >= 0.0f && seconds < 0.5f))
		seconds = 0.0f;
	if (!allowed)
	{
		if (bullet.on || bullet.owns_speed)
		{
			platform_log("VR bullet time: off (%s)", config_boolean("vr.bullet_time") ? "not here" : "turned off");
			vr_bullet_time_release();
		}
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
	if (!bullet.on && !bullet.owns_speed)
		return;
	if (!bullet.owns_speed)
	{
		bullet.base_speed = game_time_get_speed();
		if (!(bullet.base_speed > 0.0f && bullet.base_speed <= 100.0f))
			bullet.base_speed = 1.0f;
		bullet.owns_speed = TRUE;
		bullet.applied = bullet.base_speed;
		bullet.blend = 0.0f;
	}
	else if (fabsf(game_time_get_speed() - bullet.applied) >= 0.001f)
	{
		/* a script changed the speed: it is the game's now */
		bullet.owns_speed = FALSE;
		bullet.on = bullet.toggled = FALSE;
		platform_log("VR bullet time: off (the game set its own speed)");
		return;
	}
	scale = (real)config_real("vr.bullet_time_scale");
	scale = isfinite(scale) ? PIN(scale, 0.2f, 0.8f) : 0.4f;
	target = bullet.on ? 1.0f : 0.0f;
	/* eased in and out over about a sixth of a second */
	bullet.blend += (target - bullet.blend) * MIN(1.0f, seconds / 0.06f);
	if (fabsf(bullet.blend - target) < 0.02f)
		bullet.blend = target;
	speed = bullet.base_speed * (1.0f - bullet.blend * (1.0f - scale));
	if (!bullet.on && bullet.blend <= 0.0f)
	{
		vr_bullet_time_release();
		return;
	}
	game_time_set_speed(speed);
	bullet.applied = game_time_get_speed();
}

void vr_bullet_time_reset(void)
{
	vr_bullet_time_release();
	bullet.on = bullet.toggled = bullet.was_held = FALSE;
}

#else

#include "cseries.h"
#include "vr_bullet_time.h"
void vr_bullet_time_frame(void) {}
void vr_bullet_time_reset(void) {}

#endif
