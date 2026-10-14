"""Test69: OpenSauce script functions for Custom Edition campaigns (custom_edition_opensauce.c).

The Altheros Experience showed a blue screen: its scripts call OpenSauce
functions this build did not have, so the map was refused ("the scripts use 8
functions or engine globals this build does not have, and cannot run",
owner's 2026-10-14 Quest log, b40). Its ten levels' compiled scripts call:
pp_set_effect_instance_active (short, boolean) and pp_set_effect_instance_fade
(short, real, real, real) on b30, b40, c10, c20, c40, d20, f10 and a50;
pp_bloom_set_exposure (real, real) on a50; object_data_get_real (object,
string, string) and object_data_set_real (object, string, string, real) on a30
(its gravity lift). The types are those the maps were compiled with.

This compiles the production file with stub headers and runs its lookup,
the call check the map loader applies, and the evaluators (ASan/UBSan), and
pins the script engine's hooks.
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
typedef int boolean;
typedef float real;
#define TRUE 1
#define FALSE 0
#define NONE (-1)
#define NUMBEROF(a) (sizeof(a)/sizeof((a)[0]))
#define TEST_FLAG(v,b) (((v)>>(b))&1)
#define _stricmp strcasecmp
enum { _error_silent = 0 };
static int errors_logged;
static void error(int kind, char const *format, ...) { (void)kind; (void)format; errors_logged++; }
enum { _hs_type_void = 4, _hs_type_boolean = 5, _hs_type_real = 6, _hs_type_short_integer = 7,
       _hs_type_string = 9, _hs_type_object = 37 };
typedef union { struct { real x, y, z; }; real n[3]; } real_point3d;
typedef union { struct { real i, j, k; }; real n[3]; } real_vector3d;
struct _object_datum { unsigned long flags; long magic; real_point3d position; real_vector3d translational_velocity;
    real_vector3d forward, up, angular_velocity; real_point3d bounding_sphere_center; real bounding_sphere_radius; real scale; };
struct object_datum { long definition_index; struct _object_datum object; };
static struct object_datum the_object;
#define object_try_and_get(index) ((index) == 7 ? &the_object : NULL)
typedef boolean (*hs_function_parse_proc)(short, long);
typedef void (*hs_evaluate_procedure)(short, long, boolean);
/* (packed: the guest's 32-bit layout, no padding after parameter_types) */
struct __attribute__((packed)) hs_function_definition { short return_type; short flags; char const *name; hs_function_parse_proc parse;
    hs_evaluate_procedure evaluate; char const *help; char const *usage; short parameter_count; short parameter_types[1]; };
struct hs_syntax_node { short datum_header; union { short index; short constant_type; short function_index; short script_index; };
    short type; short flags; long next_node_index; union { long string_offset; long source_offset; }; union { long data; real real_value; }; };
struct data_array { int unused; };
static struct hs_syntax_node test_nodes[16];
static void *datum_try_and_get(struct data_array *array, long index)
{ (void)array; return index >= 0 && index < 16 && test_nodes[index].datum_header ? &test_nodes[index] : NULL; }
static boolean hs_macro_function_parse(short function, long expression) { (void)function; (void)expression; return TRUE; }
static long test_arguments[8];
static long *hs_macro_function_evaluate(short function, long thread, boolean initialize)
{ (void)function; (void)thread; (void)initialize; return test_arguments; }
static long returned; static int returns;
static void hs_return(long thread, long value) { (void)thread; returned = value; returns++; }
'''

HARNESS = r'''
#include <assert.h>
#include <math.h>
static long bits(real value) { union { real number; long bits; } u; u.bits = 0; u.number = value; return u.bits; }
static real number(long value) { union { real number; long bits; } u; u.bits = value; return u.number; }
static void node(int index, short type, short flags, long next, long data)
{ memset(&test_nodes[index], 0, sizeof(test_nodes[index])); test_nodes[index].datum_header = 1;
  test_nodes[index].type = type; test_nodes[index].flags = flags; test_nodes[index].next_node_index = next; test_nodes[index].data = data; }
/* a call of `function` (node 0) naming it by node 1, arguments of `types` (nodes 2...) */
static boolean call_valid(short function, short const *types, int count, short call_flags)
{ int i; memset(test_nodes, 0, sizeof(test_nodes));
  node(0, _hs_type_void, call_flags, NONE, 1); test_nodes[0].function_index = function;
  node(1, 2, 8, count ? 2 : NONE, 0);
  for (i = 0; i < count; i++) node(2 + i, types[i], 9, i + 1 < count ? 3 + i : NONE, 0);
  return custom_edition_script_call_valid(&test_nodes[0], (struct data_array *)0); }
static void evaluate(short function, long a0, long a1, long a2, long a3)
{ struct hs_function_definition *d = custom_edition_script_function(function);
  test_arguments[0] = a0; test_arguments[1] = a1; test_arguments[2] = a2; test_arguments[3] = a3;
  returns = 0; d->evaluate(function, 0, TRUE); assert(returns == 1); }
static int types_are(short function, short result, int count, short a, short b, short c, short d)
{ struct hs_function_definition *f = custom_edition_script_function(function); short want[4] = { a, b, c, d }; int i;
  if (!f || f->return_type != result || f->parameter_count != count) return 0;
  for (i = 0; i < count; i++) if (f->parameter_types[i] != want[i]) return 0;
  return 1; }
int main(void)
{
  short active = custom_edition_script_find("pp_set_effect_instance_active");
  short fade = custom_edition_script_find("PP_SET_EFFECT_INSTANCE_FADE");
  short bloom = custom_edition_script_find("pp_bloom_set_exposure");
  short get = custom_edition_script_find("object_data_get_real");
  short set = custom_edition_script_find("object_data_set_real");
  short s4[4] = { _hs_type_short_integer, _hs_type_real, _hs_type_real, _hs_type_real };
  short sb[2] = { _hs_type_short_integer, _hs_type_boolean };
  short o4[4] = { _hs_type_object, _hs_type_string, _hs_type_string, _hs_type_real };
  char x[] = "x", z[] = "z", tv[] = "transitional_velocity", position[] = "position", bogus[] = "health";
  /* names, indices past GulchCE's MCC range, nothing else */
  assert(active == 0x7100 && fade == 0x7101 && bloom == 0x7102 && get == 0x7103 && set == 0x7104);
  assert(custom_edition_script_find("sleep") == NONE && custom_edition_script_find(NULL) == NONE);
  assert(!custom_edition_script_function(0x70FF) && !custom_edition_script_function(0x7105) && !custom_edition_script_function(3));
  /* the types the Altheros levels' scripts were compiled with */
  assert(types_are(active, _hs_type_void, 2, _hs_type_short_integer, _hs_type_boolean, 0, 0));
  assert(types_are(fade, _hs_type_void, 4, _hs_type_short_integer, _hs_type_real, _hs_type_real, _hs_type_real));
  assert(types_are(bloom, _hs_type_void, 2, _hs_type_real, _hs_type_real, 0, 0));
  assert(types_are(get, _hs_type_real, 3, _hs_type_object, _hs_type_string, _hs_type_string, 0));
  assert(types_are(set, _hs_type_void, 4, _hs_type_object, _hs_type_string, _hs_type_string, _hs_type_real));
  /* the loader's call check: a permanent call with exactly these argument types */
  assert(call_valid(fade, s4, 4, 8) && call_valid(active, sb, 2, 8) && call_valid(set, o4, 4, 8));
  assert(!call_valid(fade, s4, 3, 8));                 /* an argument missing */
  assert(!call_valid(active, s4, 2, 8));               /* real where boolean is taken */
  assert(!call_valid(active, sb, 2, 0));               /* not permanent */
  assert(!call_valid(active, sb, 2, 8 | 1));           /* a primitive */
  assert(!call_valid(active, sb, 2, 8 | 2));           /* a script's call */
  { short extra[3] = { _hs_type_short_integer, _hs_type_boolean, _hs_type_boolean }; assert(!call_valid(active, extra, 3, 8)); }
  assert(!call_valid(0x7105, sb, 2, 8));
  /* post-processing: accepted, nothing drawn, logged once */
  errors_logged = 0;
  evaluate(fade, 0, bits(0.0f), bits(1.0f), bits(0.3f)); assert(returned == 0);
  evaluate(active, 1, 1, 0, 0); assert(returned == 0);
  evaluate(bloom, bits(0.5f), bits(0.0f), 0, 0); assert(returned == 0);
  assert(errors_logged == 1);
  /* a30's gravity lift: velocity read, raised and written back, per axis */
  memset(&the_object, 0, sizeof(the_object));
  the_object.object.translational_velocity.i = 0.25f; the_object.object.translational_velocity.k = -0.5f;
  evaluate(get, 7, (long)(intptr_t)tv, (long)(intptr_t)z, 0); assert(number(returned) == -0.5f);
  evaluate(set, 7, (long)(intptr_t)tv, (long)(intptr_t)z, bits(number(returned) + 0.75f));
  assert(the_object.object.translational_velocity.k == 0.25f && returned == 0);
  evaluate(get, 7, (long)(intptr_t)tv, (long)(intptr_t)x, 0); assert(number(returned) == 0.25f);
  /* read-only and unknown fields, a missing object, nonfinite values: nothing written */
  the_object.object.position.x = 3.0f; errors_logged = 0;
  evaluate(set, 7, (long)(intptr_t)position, (long)(intptr_t)x, bits(9.0f)); assert(the_object.object.position.x == 3.0f);
  evaluate(get, 7, (long)(intptr_t)position, (long)(intptr_t)x, 0); assert(number(returned) == 3.0f);
  evaluate(get, 7, (long)(intptr_t)bogus, (long)(intptr_t)x, 0); assert(number(returned) == 0.0f);
  assert(errors_logged == 2);
  evaluate(get, NONE, (long)(intptr_t)tv, (long)(intptr_t)x, 0); assert(number(returned) == 0.0f);
  evaluate(set, NONE, (long)(intptr_t)tv, (long)(intptr_t)x, bits(5.0f));
  evaluate(set, 7, (long)(intptr_t)tv, (long)(intptr_t)x, bits(NAN)); assert(the_object.object.translational_velocity.i == 0.25f);
  evaluate(set, 7, (long)(intptr_t)tv, (long)(intptr_t)x, bits(INFINITY)); assert(the_object.object.translational_velocity.i == 0.25f);
  evaluate(set, 7, (long)(intptr_t)tv, (long)(intptr_t)x, bits(-INFINITY)); assert(the_object.object.translational_velocity.i == 0.25f);
  /* The same shared write guard covers angular velocity and scale. */
  the_object.object.angular_velocity.j = -0.125f; the_object.object.scale = 1.0f;
  evaluate(set, 7, (long)(intptr_t)"angular_velocity", (long)(intptr_t)"y", bits(INFINITY)); assert(the_object.object.angular_velocity.j == -0.125f);
  evaluate(set, 7, (long)(intptr_t)"scale", 0, bits(-INFINITY)); assert(the_object.object.scale == 1.0f);
  /* Finite values (including signed zero) keep their exact representation. */
  evaluate(set, 7, (long)(intptr_t)"scale", 0, bits(1.25f)); assert(the_object.object.scale == 1.25f);
  evaluate(set, 7, (long)(intptr_t)"angular_velocity", (long)(intptr_t)"y", bits(-0.0f)); assert(signbit(the_object.object.angular_velocity.j));
  evaluate(set, 7, (long)(intptr_t)tv, 0, bits(1.0f)); assert(the_object.object.translational_velocity.i == 0.25f);
  puts("ok");
  return 0;
}
'''

with tempfile.TemporaryDirectory(prefix="test69-opensauce-") as directory:
    work = Path(directory)
    stubs = work / "stubs"
    for header in ("cseries.h", "errors.h", "math/real_math.h", "memory/data.h", "hs/hs.h", "hs/hs_library_internal.h",
                   "hs/hs_scenario_definitions.h", "objects/objects.h"):
        (stubs / header).parent.mkdir(parents=True, exist_ok=True)
        (stubs / header).write_text("")
    (work / "prelude.h").write_text(STUBS)
    source = (GAME / "custom_edition_opensauce.c").read_text(encoding="utf-8")
    (work / "test.c").write_text(source.replace('#include "custom_edition_opensauce.h"',
                                                '#include "' + str(GAME / "custom_edition_opensauce.h") + '"')
                                 + HARNESS)
    executable = work / "opensauce"
    subprocess.run(["clang", "-std=gnu11", "-O1", "-g", "-fsanitize=address,undefined", "-fno-sanitize=alignment", "-fno-sanitize-recover=all",
                    "-Wall", "-Werror", "-Wno-unused-function", "-include", str(work / "prelude.h"),
                    "-I", str(stubs), str(work / "test.c"), "-o", str(executable), "-lm"], check=True)
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0 and result.stdout.strip() == "ok", (result.returncode, result.stdout, result.stderr)
print("PASS: Test69 OpenSauce functions: names at 0x7100-0x7104, the Altheros levels' compiled argument types, "
      "the loader's call check, post-processing accepted (nothing drawn, logged once), a30's velocity read/write, "
      "read-only/unknown/missing/nonfinite refused; finite velocity/scale preserved (ASan/UBSan)")

hs = (ROOT / "source/hs/hs.c").read_text(encoding="utf-8")
runtime = (ROOT / "source/hs/hs_runtime.c").read_text(encoding="utf-8")
# the game's own table first, then OpenSauce's
find = hs[hs.index("short hs_find_function_by_name("):hs.index("boolean hs_evaluate_by_name(")]
assert find.index("hs_function_table_count") < find.index("return custom_edition_script_find(name);")
assert "custom_edition_script_call_valid(expression, hs_syntax_data)" in hs
get = hs[hs.index("struct hs_function_definition *hs_function_get("):]
assert get.index("custom_edition_script_function(function_index)") < get.index("match_assert(")
assert runtime.count("custom_edition_script_function(") == 4  # (two sites: declaration and call)
assert "mcc_script_function(expression->index) || custom_edition_script_function(expression->index)" in runtime
print("PASS: Test69 OpenSauce functions found by the script engine after its own table and MCC's: "
      "name lookup, map call check, hs_function_get, the evaluator's index bound and names")
