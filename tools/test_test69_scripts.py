"""Test69: Halo PC's display-only engine global rasterizer_fps in Custom Edition scripts.

The Altheros Experience's a10 and a30 run (set rasterizer_fps false) and
(set rasterizer_fps true): Halo PC's frame-rate counter, an engine global this
build does not have, so those levels were refused like b40 (owner's
2026-10-14 blue screen). custom_edition_scripts.c now makes a set of it to a
constant a no-op and a read of it FALSE (as GulchCE turns MCC-only calls into
constants); any other use is refused as before. This runs the production
converter on a script shaped like a10's (ASan/UBSan).
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "port/linux/game"

STUBS = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
typedef unsigned char byte;
typedef byte boolean;
typedef float real;
#define TRUE 1
#define FALSE 0
#define NONE (-1)
#define FLAG(b) (1<<(b))
#define TEST_FLAG(v,b) (((v)>>(b))&1)
#define NUMBEROF(a) (sizeof(a)/sizeof((a)[0]))
#define DATUM_INDEX_TO_ABSOLUTE_INDEX(i) ((i)&0xFFFF)
#define _stricmp strcasecmp
#define SCENARIO_TAG 0x73636e72
enum { _error_silent = 0 };
static int messages;
static void error(int kind, char const *format, ...) { (void)kind; (void)format; messages++; }
enum { _hs_function_name = 2, _hs_type_void = 4, _hs_type_boolean = 5, _hs_type_real = 6, _hs_type_short_integer = 7 };
struct data_array { char name[32]; short maximum_count; short size; byte valid; byte identifier_zero_invalid;
    unsigned long signature; short first_free_absolute_index; short count; short actual_count; short next_identifier; void *data; };
struct hs_syntax_node { short datum_header; union { short index; short constant_type; short function_index; short script_index; };
    short type; short flags; long next_node_index; union { long string_offset; long source_offset; };
    union { long data; boolean boolean_value; real real_value; short short_value; }; };
struct tag_data { int32_t size; };
struct scenario { struct tag_data hs_syntax_data; struct tag_data hs_string_constants; };
static struct { struct data_array array; struct hs_syntax_node nodes[24]; } syntax;
static char strings[256];
static int string_used;
static struct scenario the_scenario;
static int scenarios_given;
static void *custom_edition_cache_tag_next(uint8_t *c, uint32_t l, uint32_t g, uint32_t b, int32_t *t)
{ (void)c; (void)l; (void)g; (void)b; *t = 0; return scenarios_given++ ? NULL : &the_scenario; }
static void *custom_edition_cache_data_get(uint8_t *c, uint32_t l, void const *d, uint32_t *size)
{ (void)c; (void)l; if (d == &the_scenario.hs_syntax_data) { *size = sizeof(syntax); return &syntax; }
  *size = sizeof(strings); return strings; }
static char const *custom_edition_cache_tag_name(uint8_t *c, uint32_t l, int32_t t) { (void)c; (void)l; (void)t; return "scenario"; }
static short hs_find_function_by_name(char const *name)
{ static char const *const table[] = { "begin", "begin_random", "if", "cond", "set", "and", "or", "not" };
  short i; for (i = 0; i < 8; i++) if (!strcasecmp(name, table[i])) return i;
  return !strcasecmp(name, "pp_set_effect_instance_fade") ? 0x7101 : NONE; }
static short hs_find_global_by_name(char const *name) { return !strcasecmp(name, "display_framerate") ? (short)0x8010 : NONE; }
'''

HARNESS = r'''
#include <assert.h>
static long text(char const *s) { long at = string_used; strcpy(strings + at, s); string_used += (int)strlen(s) + 1; return at; }
static long D(int i) { return 0x01000000L | i; }
static void put(int i, short type, short flags, short index, long next, long string, long data)
{ struct hs_syntax_node *n = &syntax.nodes[i]; memset(n, 0, sizeof(*n)); n->datum_header = (short)(0x100 + i);
  n->type = type; n->flags = flags; n->function_index = index; n->next_node_index = next == NONE ? NONE : D((int)next);
  n->string_offset = string; n->data = data; }
/* (begin (set <global> <value>) (pp_set_effect_instance_fade 0 0 1 .3) (not <global>)); `value_flags` 9: a constant,
8: a computed value; `fps_type` the references' type. Halo PC's function and global indices are not this build's. */
static boolean convert_rhs(short value_flags, short fps_type, char const *global,
                           short value_type, short constant_type, long value_data)
{ memset(&syntax, 0, sizeof(syntax)); memset(strings, 0, sizeof(strings)); string_used = 0; scenarios_given = 0;
  strcpy(syntax.array.name, "script node"); syntax.array.maximum_count = 24; syntax.array.size = sizeof(struct hs_syntax_node);
  put(0, _hs_type_void, 8, 0, NONE, NONE, D(1));
  put(1, _hs_function_name, 9, 0, 2, text("begin"), 0);
  put(2, _hs_type_void, 8, 31, 6, NONE, D(3));
  put(3, _hs_function_name, 9, 31, 4, text("set"), 0);
  put(4, fps_type, 13, 0, 5, text(global), (long)(unsigned short)0x8123);
  put(5, value_type, value_flags, constant_type, NONE, NONE, value_data);
  put(6, _hs_type_void, 8, 0x1F0, 12, NONE, D(7));
  put(7, _hs_function_name, 9, 0x1F0, 8, text("pp_set_effect_instance_fade"), 0);
  put(8, _hs_type_short_integer, 9, 0, 9, NONE, 0);
  put(9, _hs_type_real, 9, 0, 10, NONE, 0);
  put(10, _hs_type_real, 9, 0, 11, NONE, 0);
  put(11, _hs_type_real, 9, 0, NONE, NONE, 0);
  put(12, _hs_type_boolean, 8, 77, NONE, NONE, D(13));
  put(13, _hs_function_name, 9, 77, 14, text("not"), 0);
  put(14, fps_type, 13, 0, NONE, text(global), (long)(unsigned short)0x8123);
  put(20, _hs_type_boolean, 8, 77, NONE, NONE, D(21));
  put(21, _hs_function_name, 9, 77, 22, text("not"), 0);
  put(22, _hs_type_boolean, 9, 0, NONE, NONE, 1);
  syntax.array.count = 23; syntax.array.actual_count = 18;
  return custom_edition_scripts_convert((byte *)&the_scenario, 1u << 20); }
static boolean convert(short value_flags, short fps_type, char const *global)
{ return convert_rhs(value_flags, fps_type, global, _hs_type_boolean, _hs_type_boolean,
                     value_flags == 9 ? 0 : D(20)); }
static int constant(int i, short type, long value)
{ struct hs_syntax_node *n = &syntax.nodes[i];
  return n->flags == 9 && n->constant_type == type && n->type == type && n->data == value && n->source_offset == NONE; }
int main(void)
{
  /* a10 and a30: the set does nothing, its target and the read are FALSE, OpenSauce's function is found */
  assert(convert(9, _hs_type_boolean, "rasterizer_fps"));
  assert(constant(2, _hs_type_void, 0));
  assert(constant(4, _hs_type_boolean, 0));
  assert(constant(14, _hs_type_boolean, 0));
  assert(syntax.nodes[6].function_index == 0x7101 && syntax.nodes[7].function_index == 0x7101);
  assert(syntax.nodes[2].function_index == 4 && syntax.nodes[12].function_index == 7 && syntax.nodes[0].function_index == 0);
  /* refused: a set of a computed value, another missing global, a use of another type */
  assert(!convert(8, _hs_type_boolean, "rasterizer_fps"));
  assert(!convert(9, _hs_type_boolean, "rasterizer_wireframe"));
  assert(!convert(9, _hs_type_real, "rasterizer_fps"));
  /* Both shipped literal values remain valid. A malformed RHS must not be
     erased by the no-op rewrite before the normal script type check sees it. */
  assert(convert_rhs(9, _hs_type_boolean, "rasterizer_fps", _hs_type_boolean, _hs_type_boolean, 1));
  assert(constant(2, _hs_type_void, 0) && constant(4, _hs_type_boolean, 0));
  /* Actual a10/a30 literals retain unused high bytes of 0xFFFFFF00/01;
     only the low boolean byte is meaningful. */
  assert(convert_rhs(9, _hs_type_boolean, "rasterizer_fps", _hs_type_boolean, _hs_type_boolean, 0xFFFFFF00L));
  assert(convert_rhs(9, _hs_type_boolean, "rasterizer_fps", _hs_type_boolean, _hs_type_boolean, 0xFFFFFF01L));
  assert(!convert_rhs(9, _hs_type_boolean, "rasterizer_fps", _hs_type_real, _hs_type_real, 0));
  assert(!convert_rhs(9, _hs_type_boolean, "rasterizer_fps", _hs_type_boolean, _hs_type_real, 0));
  assert(!convert_rhs(1, _hs_type_boolean, "rasterizer_fps", _hs_type_boolean, _hs_type_boolean, 0));
  assert(!convert_rhs(11, _hs_type_boolean, "rasterizer_fps", _hs_type_boolean, _hs_type_boolean, 0));
  /* a known global is renumbered, not touched otherwise */
  assert(convert(9, _hs_type_boolean, "display_framerate"));
  assert(syntax.nodes[4].flags == 13 && syntax.nodes[4].short_value == (short)0x8010 && syntax.nodes[2].flags == 8);
  puts("ok");
  return 0;
}
'''

with tempfile.TemporaryDirectory(prefix="test69-scripts-") as directory:
    work = Path(directory)
    stubs = work / "stubs"
    for header in ("cseries.h", "errors.h", "math/real_math.h", "memory/data.h", "tag_files/tag_groups.h", "hs/hs.h",
                   "hs/hs_scenario_definitions.h", "scenario/scenario_definitions.h"):
        (stubs / header).parent.mkdir(parents=True, exist_ok=True)
        (stubs / header).write_text("")
    for header in ("cache_file_formats.h", "custom_edition_cache.h"):
        (work / header).write_text("")
    (work / "prelude.h").write_text(STUBS)
    (work / "test.c").write_text((GAME / "custom_edition_scripts.c").read_text(encoding="utf-8") + HARNESS)
    executable = work / "scripts"
    subprocess.run(["clang", "-std=gnu11", "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                    "-Wall", "-Werror", "-Wno-unused-function", "-include", str(work / "prelude.h"),
                    "-I", str(stubs), str(work / "test.c"), "-o", str(executable)], check=True)
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0 and result.stdout.strip() == "ok", (result.returncode, result.stdout, result.stderr)
print("PASS: Test69 script converter: a10/a30's (set rasterizer_fps false) a no-op, its target and reads FALSE "
      "constants, OpenSauce's function renumbered, a known global renumbered; a computed set, another missing "
      "global, non-boolean use, malformed/nonpermanent/script-marked RHS refused (ASan/UBSan)")
