/*
CUSTOM_EDITION_OPENSAUCE.C

OpenSauce script functions that Custom Edition campaigns call, so that their
scripts can run (custom_edition_scripts.c refuses a map whose scripts call a
function this build does not have).

The Altheros Experience (10.24.2019) refused to load because of them; its
levels call, by their compiled scripts:
- pp_set_effect_instance_active and pp_set_effect_instance_fade (VISR night
  vision: b30, b40, c10, c20, c40, d20, f10, a50), pp_bloom_set_exposure (a50).
  This build has no OpenSauce post-processing: the calls are accepted and
  draw nothing, and the scripts go on as they would.
- object_data_get_real and object_data_set_real (a30's gravity lift: an
  object's transitional_velocity x/y/z read and written). These work: they
  read and write the object's own fields, as OpenSauce does.

Each takes the parameter types the maps were compiled with (read from their
syntax nodes), which a call must match (custom_edition_script_call_valid).
The functions have indices past the game's table and past GulchCE's MCC
functions (mcc_scripts.h, 0x7000-), and are found by name only when the
game's table has no function of that name (hs_find_function_by_name).
*/

/* ---------- headers */

#include "cseries.h"
#include "errors.h"
#include "math/real_math.h"
#include "memory/data.h"
#include "hs/hs.h"
#include "hs/hs_library_internal.h"
#include "hs/hs_scenario_definitions.h"
#include "objects/objects.h"
#include "custom_edition_opensauce.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>

/* ---------- constants */

enum
{
	_opensauce_pp_set_effect_instance_active = CUSTOM_EDITION_HS_FIRST,
	_opensauce_pp_set_effect_instance_fade,
	_opensauce_pp_bloom_set_exposure,
	_opensauce_object_data_get_real,
	_opensauce_object_data_set_real,
	_opensauce_function_end
};

/* ---------- structures */

struct opensauce_definition_2
{
	struct hs_function_definition definition;
	short more_parameter_types[1];
};

struct opensauce_definition_3
{
	struct hs_function_definition definition;
	short more_parameter_types[2];
};

struct opensauce_definition_4
{
	struct hs_function_definition definition;
	short more_parameter_types[3];
};

/* the script engine reads a function's parameter types on from
parameter_types[0] (as the game's own hs_function_definition_with_N_parameters
are laid out): the types after the first follow it directly, as they do in
every build of the game, which is 32-bit */
typedef char opensauce_definition_layout_assert[
	offsetof(struct opensauce_definition_2, more_parameter_types) ==
		offsetof(struct hs_function_definition, parameter_types) + sizeof(short) ? 1 : -1];

/* ---------- private code */

static void opensauce_post_processing_absent(
	char const *name)
{
	static boolean logged;

	if (!logged)
	{
		logged = TRUE;
		error(
			_error_silent,
			"custom edition: the scripts use OpenSauce post-processing ('%s'), which this build does not draw: the effects do not show",
			name);
	}

	return;
}

static void opensauce_post_processing_evaluate(
	short function_index,
	long thread_index,
	boolean initialize)
{
	long *arguments = hs_macro_function_evaluate(function_index, thread_index, initialize);

	if (arguments)
	{
		opensauce_post_processing_absent(custom_edition_script_function(function_index)->name);
		hs_return(thread_index, 0);
	}

	return;
}

/* the real field of an object that `data` and `subdata` name (OpenSauce's
names), or NULL; `writable` is FALSE for one only read */
static real *object_data_real(
	struct object_datum *object,
	char const *data,
	char const *subdata,
	boolean *writable)
{
	real_vector3d *vector = NULL;
	short component = NONE;

	*writable = TRUE;
	if (!data)
	{
		return NULL;
	}
	if (!_stricmp(data, "position"))
	{
		vector = (real_vector3d *)&object->object.position;
		*writable = FALSE;
	}
	else if (!_stricmp(data, "transitional_velocity") || !_stricmp(data, "translational_velocity"))
	{
		vector = &object->object.translational_velocity;
	}
	else if (!_stricmp(data, "angular_velocity"))
	{
		vector = &object->object.angular_velocity;
	}
	else if (!_stricmp(data, "forward"))
	{
		vector = &object->object.forward;
		*writable = FALSE;
	}
	else if (!_stricmp(data, "up"))
	{
		vector = &object->object.up;
		*writable = FALSE;
	}
	else if (!_stricmp(data, "center"))
	{
		vector = (real_vector3d *)&object->object.bounding_sphere_center;
		*writable = FALSE;
	}
	else if (!_stricmp(data, "radius"))
	{
		*writable = FALSE;
		return &object->object.bounding_sphere_radius;
	}
	else if (!_stricmp(data, "scale"))
	{
		return &object->object.scale;
	}
	else
	{
		return NULL;
	}
	if (subdata && (!_stricmp(subdata, "x") || !_stricmp(subdata, "i")))
	{
		component = 0;
	}
	else if (subdata && (!_stricmp(subdata, "y") || !_stricmp(subdata, "j")))
	{
		component = 1;
	}
	else if (subdata && (!_stricmp(subdata, "z") || !_stricmp(subdata, "k")))
	{
		component = 2;
	}
	if (component == NONE)
	{
		return NULL;
	}

	return component == 0 ? &vector->i : component == 1 ? &vector->j : &vector->k;
}

static void object_data_unknown(
	char const *data,
	char const *subdata)
{
	static long logged;

	if (logged < 4)
	{
		logged++;
		error(
			_error_silent,
			"custom edition: object_data '%.32s' '%.32s' is not one this build reads or writes",
			data ? data : "",
			subdata ? subdata : "");
	}

	return;
}

static void object_data_get_real_evaluate(
	short function_index,
	long thread_index,
	boolean initialize)
{
	long *arguments = hs_macro_function_evaluate(function_index, thread_index, initialize);
	union { real number; long bits; } result;

	if (arguments)
	{
		struct object_datum *object = object_try_and_get(arguments[0]);
		char const *data = (char const *)(uintptr_t)arguments[1];
		char const *subdata = (char const *)(uintptr_t)arguments[2];
		boolean writable;
		real *field = object ? object_data_real(object, data, subdata, &writable) : NULL;

		if (object && !field)
		{
			object_data_unknown(data, subdata);
		}
		result.number = field ? *field : 0.0f;
		hs_return(thread_index, result.bits);
	}

	return;
}

static void object_data_set_real_evaluate(
	short function_index,
	long thread_index,
	boolean initialize)
{
	long *arguments = hs_macro_function_evaluate(function_index, thread_index, initialize);
	union { real number; long bits; } value;

	if (arguments)
	{
		struct object_datum *object = object_try_and_get(arguments[0]);
		char const *data = (char const *)(uintptr_t)arguments[1];
		char const *subdata = (char const *)(uintptr_t)arguments[2];
		boolean writable;
		real *field = object ? object_data_real(object, data, subdata, &writable) : NULL;

		value.bits = arguments[3];
		if (object && (!field || !writable))
		{
			object_data_unknown(data, subdata);
		}
		/* The script value is an IEEE-754 real. Inspect its exponent rather
		than trusting floating-point comparisons under compiler fast-math:
		neither NaN nor either infinity may enter object physics. */
		else if (field && ((uint32_t)value.bits & 0x7F800000u) != 0x7F800000u)
		{
			*field = value.number;
		}
		hs_return(thread_index, 0);
	}

	return;
}

/* ---------- globals */

static struct opensauce_definition_2 pp_set_effect_instance_active_definition =
{
	{
		_hs_type_void, 0, "pp_set_effect_instance_active", hs_macro_function_parse,
		opensauce_post_processing_evaluate,
		"OpenSauce: shows or hides a post-processing effect instance (not drawn in this build).",
		"<instance-index> <active>", 2, { _hs_type_short_integer }
	},
	{ _hs_type_boolean }
};

static struct opensauce_definition_4 pp_set_effect_instance_fade_definition =
{
	{
		_hs_type_void, 0, "pp_set_effect_instance_fade", hs_macro_function_parse,
		opensauce_post_processing_evaluate,
		"OpenSauce: fades a post-processing effect instance (not drawn in this build).",
		"<instance-index> <start> <end> <time>", 4, { _hs_type_short_integer }
	},
	{ _hs_type_real, _hs_type_real, _hs_type_real }
};

static struct opensauce_definition_2 pp_bloom_set_exposure_definition =
{
	{
		_hs_type_void, 0, "pp_bloom_set_exposure", hs_macro_function_parse,
		opensauce_post_processing_evaluate,
		"OpenSauce: sets the bloom exposure (not drawn in this build).",
		"<exposure> <time>", 2, { _hs_type_real }
	},
	{ _hs_type_real }
};

static struct opensauce_definition_3 object_data_get_real_definition =
{
	{
		_hs_type_real, 0, "object_data_get_real", hs_macro_function_parse,
		object_data_get_real_evaluate,
		"OpenSauce: an object's real field (position, transitional_velocity, angular_velocity, forward, up, center: x/y/z; radius, scale).",
		"<object> <data-name> <subdata-name>", 3, { _hs_type_object }
	},
	{ _hs_type_string, _hs_type_string }
};

static struct opensauce_definition_4 object_data_set_real_definition =
{
	{
		_hs_type_void, 0, "object_data_set_real", hs_macro_function_parse,
		object_data_set_real_evaluate,
		"OpenSauce: sets an object's real field (transitional_velocity, angular_velocity: x/y/z; scale).",
		"<object> <data-name> <subdata-name> <value>", 4, { _hs_type_object }
	},
	{ _hs_type_string, _hs_type_string, _hs_type_real }
};

static struct hs_function_definition *const opensauce_functions[] =
{
	&pp_set_effect_instance_active_definition.definition,
	&pp_set_effect_instance_fade_definition.definition,
	&pp_bloom_set_exposure_definition.definition,
	&object_data_get_real_definition.definition,
	&object_data_set_real_definition.definition,
};

typedef char opensauce_functions_count_assert[
	NUMBEROF(opensauce_functions) == _opensauce_function_end - CUSTOM_EDITION_HS_FIRST ? 1 : -1];

/* ---------- public code */

struct hs_function_definition *custom_edition_script_function(
	short function_index)
{
	return function_index >= CUSTOM_EDITION_HS_FIRST && function_index < _opensauce_function_end ?
		opensauce_functions[function_index - CUSTOM_EDITION_HS_FIRST] :
		NULL;
}

short custom_edition_script_find(
	char const *name)
{
	short index;

	for (index = 0; name && index < (short)NUMBEROF(opensauce_functions); index++)
	{
		if (!_stricmp(opensauce_functions[index]->name, name))
		{
			return (short)(CUSTOM_EDITION_HS_FIRST + index);
		}
	}

	return NONE;
}

boolean custom_edition_script_call_valid(
	struct hs_syntax_node const *call,
	struct data_array *syntax)
{
	struct hs_function_definition *function = custom_edition_script_function(call->function_index);
	struct hs_syntax_node *node;
	long next;
	short argument;

	/* (a permanent call (flag 8), neither a primitive's nor a script's
	(flags 1 and 2), of the function the name node names, and its arguments
	of the types it takes; as mcc_script_call_valid) */
	if (!function || !(call->flags & 8) || (call->flags & 3) ||
		!(node = datum_try_and_get(syntax, call->data)))
	{
		return FALSE;
	}
	next = node->next_node_index;
	for (argument = 0; argument < function->parameter_count; argument++)
	{
		node = datum_try_and_get(syntax, next);
		if (!node || node->type != function->parameter_types[argument])
		{
			return FALSE;
		}
		next = node->next_node_index;
	}

	return next == NONE;
}
