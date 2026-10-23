"""Test73 (the owner: immersive driving "a bit over sensitive and doesnt really match where im turning"; "all
vehicles should be as responsive and feel good to use as possible"; it applies to single player too): each vehicle
answers the immersive controls in proportion, all the way at their full lock (60 degrees), through
vehicle_vr_steering_facing (vehicles.c), which inverts how vehicle_update reads a driver's facing.

Read from the stock Xbox maps' vehicle tags (_scratch/t72/xbox_vehicles.py; every map): the Warthog (human jeep) turns
its wheels to the facing offset up to 30 degrees each way, at 180 degrees a second; the Scorpion (human tank) turns
at a rate of the offset over 90 degrees (full from 90); the Ghost and the Wraith (alien scout) at the square root of
the offset; the Banshee (alien fighter) in proportion to it. Before, the controls' 60 went 1:1 into the offset: the
Warthog's wheels were at full lock by 30 (the second half of the wheel did nothing), the Scorpion never reached its
full turn, and the Ghost turned hard at the smallest twist.

Compiled here: the real vehicle_vr_steering_facing over each kind's definition, driven across the controls' range,
and each kind's response by vehicles.c's own formulas (pinned to its text): linear in the controls, full at full
lock (the hover's as fast as before at full lock); the Banshee's and other kinds' offsets unchanged.
"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/test73_driving'
vehicles = (ROOT / 'source/units/vehicles.c').read_text(encoding='utf-8')
header = (ROOT / 'source/units/vehicles.h').read_text(encoding='utf-8')
handles = (ROOT / 'port/linux/game/vr_vehicle_handles.h').read_text(encoding='utf-8')


def fn(text, name):
    m = re.search(r'^(?:static )?[\w *]+\b' + re.escape(name) + r'\s*\(', text, re.M)
    while m and text[text.index(')', m.end()):].lstrip(')\n\t ').startswith(';'):
        m = re.compile(r'^(?:static )?[\w *]+\b' + re.escape(name) + r'\s*\(', re.M).search(text, m.end())
    assert m, name
    a = text.index('{', m.start())
    b, depth = a + 1, 1
    while depth:
        depth += (text[b] == '{') - (text[b] == '}')
        b += 1
    return text[m.start():b] + '\n'


# ---------- the response formulas the mapping inverts (vehicle_update, update_alien_scout_physics)
assert 'steering_angle = arctangent(steer_cross, steer_dot);' in vehicles
assert ('if (desired_position<DEGREES_TO_RADIANS(definition->unknown30c))\n\t\t\t\tdesired_position = '
        'DEGREES_TO_RADIANS(definition->unknown30c);') in vehicles
assert 'PIN(steering_angle*0.63661975f, -1.0f, 1.0f)*definition->unknown2f8,' in vehicles
assert 'real desired = square_root((real)(fabs(steering)*0.0069813174f))*sign;' in vehicles
assert 'if (fabs(desired)>_real_epsilon && steering/desired<2.0f)\n\t\t\t\tdesired = steering*0.5f;' in vehicles
assert "scale_vector3d(&axis, (-angle)*definition->unknown314*(1.0f/_pi), &desired_angular_velocity);" in vehicles
# (the tank is type 0: vehicle_update's `if (definition->vehicle_type)` sends it to the rate branch)
assert re.search(r'_vehicle_type_human_tank = 0,\s*\n\s*_vehicle_type_human_jeep,', vehicles)
# ---------- the controls use it
assert 'steer=vehicle_vr_steering_facing(vr_wheel.vehicle,steer,VR_WHEEL_LOCK);' in handles
assert 'real vehicle_vr_steering_facing(\n\tlong vehicle_index,\n\treal controls,\n\treal lock);' in header
enum = vehicles[vehicles.index('enum', vehicles.index('_vehicle_type_human_tank') - 40):]
enum = enum[:enum.index('};') + 2]

HARNESS = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
typedef float real;
typedef int boolean;
#define NONE (-1L)
#define _pi 3.14159265f
#define PIN(x,l,h) ((x)<(l)?(l):((x)>(h)?(h):(x)))
#define MIN(a,b) ((a)<(b)?(a):(b))
#define DEGREES_TO_RADIANS(d) ((d)*0.017453293f)
enum { _object_type_biped, _object_type_vehicle };
%s
struct object_datum { struct { short type; } object; long definition_index; };
struct vehicle_definition { short vehicle_type; real unknown308, unknown30c; };
static struct object_datum the_vehicle = { { _object_type_vehicle }, 1 };
static struct vehicle_definition stock;
static struct object_datum *object_try_and_get(long i) { return i == 7 ? &the_vehicle : 0; }
#define vehicle_specific_definition_get(i) (&stock)
%s
#define LOCK 1.04719755f
/* each kind's answer to a facing offset, as vehicle_update has it */
static real response(short type, real offset)
{
	switch (type)
	{
	case _vehicle_type_human_jeep: return PIN(offset, DEGREES_TO_RADIANS(stock.unknown30c), DEGREES_TO_RADIANS(stock.unknown308));
	case _vehicle_type_human_tank: return PIN(offset*0.63661975f, -1.0f, 1.0f)*0.14f;
	case _vehicle_type_alien_scout:
	{
		long sign = offset!=0.0f ? (offset<0.0f ? -1 : 1) : 0;
		real desired = sqrtf(fabsf(offset)*0.0069813174f)*sign;
		if (fabsf(desired)>1e-6f && offset/desired<2.0f) desired = offset*0.5f;
		return desired;
	}
	default: return offset * 0.20f / _pi;
	}
}
int main(void)
{
	static const short types[] = { _vehicle_type_human_jeep, _vehicle_type_human_tank, _vehicle_type_alien_scout,
		_vehicle_type_alien_fighter };
	static const char *const names[] = { "Warthog", "Scorpion", "Ghost/Wraith", "Banshee" };
	for (int t = 0; t < 4; t++)
	{
		real full, before_full, worst = 0;
		stock.vehicle_type = types[t];
		stock.unknown308 = types[t] == _vehicle_type_human_jeep ? 30.0f : 0.0f;
		stock.unknown30c = types[t] == _vehicle_type_human_jeep ? -30.0f : 0.0f;
		full = response(types[t], vehicle_vr_steering_facing(7, LOCK, LOCK));
		before_full = response(types[t], LOCK);
		for (int step = -100; step <= 100; step++)
		{
			real controls = LOCK * step / 100.0f;
			real offset = vehicle_vr_steering_facing(7, controls, LOCK);
			real answer = response(types[t], offset);
			real linear = full * step / 100.0f;
			/* (the hover's small-turn region, under 1.6 degrees of offset, is linear in the offset itself) */
			real tolerance = types[t] == _vehicle_type_alien_scout && fabsf(offset) < 0.03f ? 0.3f * fabsf(full) : 1e-4f;
			assert(fabsf(answer - linear) <= tolerance);
			if (fabsf(answer - linear) > worst && tolerance < 0.01f) worst = fabsf(answer - linear);
			assert(step == 0 || (answer > 0) == (step > 0)); /* the controls' own sign */
		}
		/* full at full lock: the Warthog's wheels at 30, the Scorpion's whole turn rate; the hover as before */
		if (types[t] == _vehicle_type_human_jeep) assert(fabsf(full - DEGREES_TO_RADIANS(30.0f)) < 1e-5f);
		if (types[t] == _vehicle_type_human_tank) assert(fabsf(full - 0.14f) < 1e-5f && before_full < 0.7f * 0.14f + 1e-4f);
		if (types[t] == _vehicle_type_alien_scout) assert(fabsf(full - before_full) < 1e-6f);
		if (types[t] == _vehicle_type_alien_fighter)
			for (int step = -10; step <= 10; step++) assert(vehicle_vr_steering_facing(7, LOCK * step / 10.0f, LOCK) == LOCK * step / 10.0f);
		/* half the controls: half the answer (before: the Warthog's wheels already at 30 at half the wheel) */
		{
			real half = response(types[t], vehicle_vr_steering_facing(7, 0.5f * LOCK, LOCK));
			assert(fabsf(half - 0.5f * full) < 1e-4f);
			if (types[t] == _vehicle_type_human_jeep) assert(fabsf(response(types[t], 0.5f * LOCK) - full) < 1e-5f);
			if (types[t] == _vehicle_type_alien_scout) assert(response(types[t], 0.5f * LOCK) > 0.7f * full);
		}
		printf("%%s: in proportion over the controls' whole turn (worst %%.1e), full at full lock\n", names[t], (double)worst);
	}
	/* no vehicle, a turret, a mangled number: the controls' own */
	assert(vehicle_vr_steering_facing(NONE, 0.3f, LOCK) == 0.3f);
	stock.vehicle_type = _vehicle_type_turret; assert(vehicle_vr_steering_facing(7, 0.3f, LOCK) == 0.3f);
	assert(isnan(vehicle_vr_steering_facing(7, NAN, LOCK)));
	/* a jeep with no turn bounds (a falling box's): as it is */
	stock.vehicle_type = _vehicle_type_human_jeep; stock.unknown308 = stock.unknown30c = 0;
	assert(vehicle_vr_steering_facing(7, 0.3f, LOCK) == 0.3f);
	return 0;
}
''' % (enum, fn(vehicles, 'vehicle_vr_steering_facing'))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'driving.c').write_text(HARNESS, encoding='utf-8')
subprocess.run(['clang', '-std=gnu11', '-O1', '-g', '-Wall', '-Werror', '-Wno-unused-function', '-Wno-unused-variable',
                '-fsanitize=address,undefined', '-fno-sanitize-recover=all', str(OUT / 'driving.c'), '-lm', '-o',
                str(OUT / 'driving')], check=True)
print(subprocess.run([str(OUT / 'driving')], check=True, capture_output=True, text=True).stdout.strip())
print('PASS: Test73 driving: the Warthog, Scorpion, Ghost/Wraith and Banshee answer the immersive controls in '
      'proportion, all the way at full lock')
