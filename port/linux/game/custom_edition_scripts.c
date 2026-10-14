/*
CUSTOM_EDITION_SCRIPTS.C

The scripts of Halo Custom Edition maps, run by this build's script
interpreter (custom_edition_cache.h).

A compiled script names each function it calls, and each engine global it
uses, by its index in the engine's table, and Halo PC's tables are not this
build's: Halo PC has functions and globals this build does not, in among
the ones both have, so from some point on the same index names another
entry (timberland.map's player_effect_start would call the function 29
places before it, and beavercreek_halo3.yelo's switch_bsp would call
playback). A compiled script also keeps every name, in its string data:
each call and each engine global is found again here by that name, with
the game's own hs_find_function_by_name and hs_find_global_by_name, and a
map whose scripts use one this build does not have is refused. The value
types of both builds are numbered alike: every call in the maps examined
has its function's type here (docs/custom_edition_caches.md).

OpenSauce's functions such campaigns call are this build's too
(custom_edition_opensauce.c). Halo PC's display-only engine globals this
build lacks (rasterizer_fps: Halo PC's frame-rate counter, set by The
Altheros Experience's a10 and a30) are not refused: setting one to a
constant does nothing and reading one is FALSE, as GulchCE turns MCC-only
calls into constants (mcc_boolean_result). Any other use of one is refused.
*/

/* ---------- headers */

#include "cseries.h"
#include "errors.h"
#include "math/real_math.h"
#include "memory/data.h"
#include "tag_files/tag_groups.h"
#include "hs/hs.h"
#include "hs/hs_scenario_definitions.h"
#include "scenario/scenario_definitions.h"
#include "cache_file_formats.h"
#include "custom_edition_cache.h"

#include <string.h>

/* ---------- constants */

/* a syntax node's flags, as hs_runtime.c names them */
enum
{
	_hs_syntax_node_primitive_bit = 0,
	_hs_syntax_node_script_bit,
	_hs_syntax_node_global_bit,
	_hs_syntax_node_permanent_bit,
};
/* (a global's reference: hs.c's name for the bit) */
#define _hs_syntax_node_variable_bit _hs_syntax_node_global_bit

/* engine globals are told from the scenario's by this bit of their
designator (hs_find_global_by_name) */
#define HS_EXTERNAL_GLOBAL_DESIGNATOR_BIT 15

/* missing names are logged up to this many times */
#define MAXIMUM_MISSING_NAME_MESSAGES 8
/* the uses of display-only engine globals a map may have */
#define MAXIMUM_DISPLAY_GLOBAL_USES 32

/* ---------- structures */

struct scripts_conversion
{
	struct hs_syntax_node *nodes;
	long node_count;
	char const *strings;
	unsigned long string_bytes;
	long functions_renumbered;
	long globals_renumbered;
	long missing_count;
	/* the nodes that use a display-only engine global
	(display_globals_resolve) */
	long display_global_nodes[MAXIMUM_DISPLAY_GLOBAL_USES];
	long display_global_count;
};

/* Halo PC's engine globals that only change what is drawn for a developer,
which this build does not have: a map may set them (to nothing) and read
them (FALSE) */
static char const *const display_only_globals[] =
{
	"rasterizer_fps",
};

/* ---------- private code */

/* the string at `offset` in the script string data, or NULL unless it lies
within it */
static char const *script_string_get(
	struct scripts_conversion const *conversion,
	long offset)
{
	return offset >= 0 &&
		(unsigned long)offset < conversion->string_bytes &&
		memchr(conversion->strings + offset, 0, conversion->string_bytes - offset) ?
		conversion->strings + offset :
		NULL;
}

static void script_name_missing(
	struct scripts_conversion *conversion,
	char const *kind,
	char const *name)
{
	if (conversion->missing_count < MAXIMUM_MISSING_NAME_MESSAGES)
	{
		error(_error_silent, "custom edition: the scripts use the %s '%s', which this build does not have", kind, name);
	}
	conversion->missing_count++;

	return;
}

/* A call names its function with its first child, which has the function's
index too; FALSE when the call is not laid out so. */
static boolean function_call_convert(
	struct scripts_conversion *conversion,
	struct hs_syntax_node *call)
{
	long name_index = DATUM_INDEX_TO_ABSOLUTE_INDEX(call->data);
	struct hs_syntax_node *name_node;
	char const *name;
	short function_index;

	if (name_index >= conversion->node_count)
	{
		return FALSE;
	}
	name_node = &conversion->nodes[name_index];
	name = script_string_get(conversion, name_node->string_offset);
	if (!name || name_node->type != _hs_function_name)
	{
		return FALSE;
	}
	function_index = hs_find_function_by_name(name);
	if (function_index == NONE)
	{
		script_name_missing(conversion, "function", name);
	}
	else if (call->function_index != function_index)
	{
		call->function_index = function_index;
		name_node->function_index = function_index;
		conversion->functions_renumbered++;
	}

	return TRUE;
}

/* FALSE when the global's name is not in the string data */
static boolean engine_global_convert(
	struct scripts_conversion *conversion,
	struct hs_syntax_node *reference)
{
	char const *name = script_string_get(conversion, reference->string_offset);
	short designator;

	if (!name)
	{
		return FALSE;
	}
	designator = hs_find_global_by_name(name);
	if (designator == NONE || !TEST_FLAG(designator, HS_EXTERNAL_GLOBAL_DESIGNATOR_BIT))
	{
		short display_global;

		for (display_global = 0; display_global < (short)NUMBEROF(display_only_globals); display_global++)
		{
			if (!_stricmp(name, display_only_globals[display_global]))
			{
				break;
			}
		}
		if (display_global < (short)NUMBEROF(display_only_globals) &&
			reference->type == _hs_type_boolean &&
			conversion->display_global_count < MAXIMUM_DISPLAY_GLOBAL_USES)
		{
			conversion->display_global_nodes[conversion->display_global_count++] = reference - conversion->nodes;
		}
		else
		{
			script_name_missing(conversion, "engine global", name);
		}
	}
	else if (reference->short_value != designator)
	{
		reference->short_value = designator;
		conversion->globals_renumbered++;
	}

	return TRUE;
}

/* the node a datum index names, or NULL */
static struct hs_syntax_node *conversion_node_get(
	struct scripts_conversion const *conversion,
	long datum_index)
{
	long index = DATUM_INDEX_TO_ABSOLUTE_INDEX(datum_index);

	return datum_index != NONE && index < conversion->node_count && conversion->nodes[index].datum_header ?
		&conversion->nodes[index] :
		NULL;
}

/* a node made a constant of its own type: TRUE/FALSE `value` (as
mcc_boolean_result) */
static void conversion_node_make_constant(
	struct hs_syntax_node *node,
	long value)
{
	node->flags = FLAG(_hs_syntax_node_primitive_bit) | FLAG(_hs_syntax_node_permanent_bit);
	node->constant_type = node->type;
	node->data = node->type == _hs_type_void ? 0 : value;
	node->source_offset = NONE;

	return;
}

/* The uses of display-only engine globals: a `set` of one to a constant
becomes a constant itself (nothing is set), a read of one FALSE; another use
(a set of a computed value) is refused, as a missing global is. */
static void display_globals_resolve(
	struct scripts_conversion *conversion)
{
	short set_function = hs_find_function_by_name("set");
	long use;
	long node_index;

	if (!conversion->display_global_count)
	{
		return;
	}
	/* sets first: a set's target is its first argument */
	for (node_index = 0; set_function != NONE && node_index < conversion->node_count; node_index++)
	{
		struct hs_syntax_node *call = &conversion->nodes[node_index];
		struct hs_syntax_node *name_node;
		struct hs_syntax_node *target;
		struct hs_syntax_node *value;

		if (!call->datum_header ||
			TEST_FLAG(call->flags, _hs_syntax_node_primitive_bit) ||
			TEST_FLAG(call->flags, _hs_syntax_node_script_bit) ||
			call->function_index != set_function ||
			!(name_node = conversion_node_get(conversion, call->data)) ||
			!(target = conversion_node_get(conversion, name_node->next_node_index)))
		{
			continue;
		}
		for (use = 0; use < conversion->display_global_count; use++)
		{
			if (&conversion->nodes[conversion->display_global_nodes[use]] == target)
			{
				break;
			}
		}
		if (use == conversion->display_global_count)
		{
			continue;
		}
		value = conversion_node_get(conversion, target->next_node_index);
		if (value &&
			value->next_node_index == NONE &&
			value->type == _hs_type_boolean &&
			value->constant_type == _hs_type_boolean &&
			TEST_FLAG(value->flags, _hs_syntax_node_primitive_bit) &&
			TEST_FLAG(value->flags, _hs_syntax_node_permanent_bit) &&
			!TEST_FLAG(value->flags, _hs_syntax_node_script_bit) &&
			!TEST_FLAG(value->flags, _hs_syntax_node_variable_bit) &&
			(call->type == _hs_type_void || call->type == _hs_type_boolean))
		{
			conversion_node_make_constant(call, value->boolean_value != FALSE);
			/* (the target, no longer reached, names no global either) */
			conversion_node_make_constant(target, FALSE);
		}
		else
		{
			script_name_missing(conversion, "engine global (set without a permanent boolean constant)",
				script_string_get(conversion, target->string_offset));
		}
		/* (resolved either way) */
		conversion->display_global_nodes[use] = conversion->display_global_nodes[--conversion->display_global_count];
	}
	/* the rest are reads */
	for (use = 0; use < conversion->display_global_count; use++)
	{
		conversion_node_make_constant(&conversion->nodes[conversion->display_global_nodes[use]], FALSE);
	}
	conversion->display_global_count = 0;

	return;
}

/* FALSE after logging why when the scenario's scripts cannot run */
static boolean scenario_scripts_convert(
	byte *tag_cache,
	unsigned long loaded_bytes,
	int32_t tag_index,
	struct scenario *scenario)
{
	struct scripts_conversion conversion = { 0 };
	uint32_t syntax_bytes = 0;
	uint32_t string_bytes = 0;
	struct data_array *syntax = custom_edition_cache_data_get(tag_cache, loaded_bytes, &scenario->hs_syntax_data, &syntax_bytes);
	long node_index;

	if (!syntax)
	{
		return TRUE;
	}
	conversion.strings = custom_edition_cache_data_get(tag_cache, loaded_bytes, &scenario->hs_string_constants, &string_bytes);
	conversion.string_bytes = conversion.strings ? string_bytes : 0;
	if (syntax_bytes < sizeof(*syntax) ||
		syntax->size != sizeof(struct hs_syntax_node) ||
		syntax->count < 0 ||
		syntax->count > syntax->maximum_count ||
		syntax_bytes < sizeof(*syntax) + (unsigned long)syntax->maximum_count * sizeof(struct hs_syntax_node))
	{
		error(
			_error_silent,
			"custom edition: the script syntax of '%s' is not laid out as this build's",
			custom_edition_cache_tag_name(tag_cache, loaded_bytes, tag_index));
		return FALSE;
	}
	/* the nodes follow the array (its data pointer is set there when the
	scripts are loaded, hs_scenario_postprocess), and those in use come
	first */
	conversion.nodes = (struct hs_syntax_node *)(syntax + 1);
	conversion.node_count = syntax->count;

	for (node_index = 0; node_index < conversion.node_count; node_index++)
	{
		struct hs_syntax_node *node = &conversion.nodes[node_index];
		boolean converted = TRUE;

		if (!node->datum_header)
		{
			continue;
		}
		if (!TEST_FLAG(node->flags, _hs_syntax_node_primitive_bit))
		{
			/* a call of one of the scenario's scripts names it by the
			scenario's own index */
			if (!TEST_FLAG(node->flags, _hs_syntax_node_script_bit))
			{
				converted = function_call_convert(&conversion, node);
			}
		}
		else if (TEST_FLAG(node->flags, _hs_syntax_node_global_bit) &&
			TEST_FLAG(node->short_value, HS_EXTERNAL_GLOBAL_DESIGNATOR_BIT))
		{
			converted = engine_global_convert(&conversion, node);
		}
		if (!converted)
		{
			error(
				_error_silent,
				"custom edition: script syntax node %ld of '%s' does not name what it uses",
				node_index,
				custom_edition_cache_tag_name(tag_cache, loaded_bytes, tag_index));
			return FALSE;
		}
	}
	display_globals_resolve(&conversion);
	error(
		_error_silent,
		"custom edition: %ld script calls and %ld engine global references were given this build's index",
		conversion.functions_renumbered,
		conversion.globals_renumbered);
	if (conversion.missing_count)
	{
		error(
			_error_silent,
			"custom edition: the scripts use %ld functions or engine globals this build does not have, and cannot run",
			conversion.missing_count);
		return FALSE;
	}

	return TRUE;
}

/* ---------- public code */

boolean custom_edition_scripts_convert(
	byte *tag_cache,
	unsigned long loaded_bytes)
{
	struct scenario *scenario;
	int32_t tag_index = NONE;

	while ((scenario = custom_edition_cache_tag_next(tag_cache, loaded_bytes, SCENARIO_TAG, sizeof(*scenario), &tag_index)) != NULL)
	{
		if (!scenario_scripts_convert(tag_cache, loaded_bytes, tag_index, scenario))
		{
			return FALSE;
		}
	}

	return TRUE;
}
