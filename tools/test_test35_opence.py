"""Build 148 particle-radius validation remains in the Build 157 candidate."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def function(source, name):
    match = re.search(r"^(?:static )?(?:inline )?[\w *]+\b" + re.escape(name) + r"\s*\([^;{]*\)\s*\{", source, re.M)
    assert match, name
    start = source.index("{", match.start())
    depth, end = 1, start + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start():end]


# Preserve the released Build 148 fixes while the candidate moves to Build 157.
limits = read("port/linux/include/halo_port_limits.h")
assert re.search(r"^#define HALO_PORT_NETWORK_VERSION 29$", limits, re.M)
gradle = read("port/android/app/build.gradle")
assert ("versionCode Math.max(84, buildNumber)" in gradle or
        "versionCode Math.max(83, buildNumber)" in gradle or
        "versionCode Math.max(82, buildNumber)" in gradle or
        "versionCode Math.max(81, buildNumber)" in gradle or
        "versionCode Math.max(80, buildNumber)" in gradle or
        "versionCode Math.max(79, buildNumber)" in gradle or
        "versionCode Math.max(78, buildNumber)" in gradle or
        "versionCode Math.max(77, buildNumber)" in gradle or
        "versionCode Math.max(76, buildNumber)" in gradle or
        "versionCode Math.max(75, buildNumber)" in gradle or
        "versionCode Math.max(74, buildNumber)" in gradle or
        "versionCode Math.max(73, buildNumber)" in gradle or
        "versionCode Math.max(72, buildNumber)" in gradle or
        "versionCode Math.max(71, buildNumber)" in gradle or
        "versionCode Math.max(70, buildNumber)" in gradle or
        "versionCode Math.max(69, buildNumber)" in gradle or
        "versionCode Math.max(68, buildNumber)" in gradle or
        "versionCode Math.max(67, buildNumber)" in gradle or
        "versionCode Math.max(66, buildNumber)" in gradle or
        "versionCode Math.max(65, buildNumber)" in gradle or
        "versionCode Math.max(64, buildNumber)" in gradle or
        "versionCode Math.max(63, buildNumber)" in gradle or
        "versionCode Math.max(62, buildNumber)" in gradle or
        "versionCode Math.max(61, buildNumber)" in gradle or
        "versionCode Math.max(60, buildNumber)" in gradle)
frame = read("port/linux/src/vr_frame.c")
assert ("HaloCE Quest test72 candidate 1.0.39-test72 code84" in frame or
        "HaloCE Quest test71 candidate 1.0.38-test71 code83" in frame or
        "HaloCE Quest test70 candidate 1.0.37-test70 code82" in frame or
        "HaloCE Quest test69 candidate 1.0.36-test69 code81" in frame or
        "HaloCE Quest test68 candidate 1.0.35-test68 code80" in frame or
        "HaloCE Quest test67 candidate 1.0.34-test67 code79" in frame or
        "HaloCE Quest test66 candidate 1.0.33-test66 code78" in frame or
        "HaloCE Quest test65 candidate 1.0.32-test65 code77" in frame or
        "HaloCE Quest test64 candidate 1.0.31-test64 code76" in frame or
        "HaloCE Quest test63 candidate 1.0.30-test63 code75" in frame or
        "HaloCE Quest test62 candidate 1.0.29-test62 code74" in frame or
        "HaloCE Quest test61 candidate 1.0.28-test61 code73" in frame or
        "HaloCE Quest test60 candidate 1.0.27-test60 code72" in frame or
        "HaloCE Quest test59 candidate 1.0.26-test59 code71" in frame or
        "HaloCE Quest test58 candidate 1.0.25-test58 code70" in frame or
        "HaloCE Quest test57 candidate 1.0.24-test57 code69" in frame or
        "HaloCE Quest test56 candidate 1.0.23-test56 code68" in frame or
        "HaloCE Quest test55 candidate 1.0.22-test55 code67" in frame or
        "HaloCE Quest test54 candidate 1.0.21-test54 code66" in frame or
        "HaloCE Quest test53 candidate 1.0.20-test53 code65" in frame or
        "HaloCE Quest test52 candidate 1.0.20-test52 code64" in frame or
        "HaloCE Quest v1.0.19 release code63" in frame or
        "HaloCE Quest test51 candidate 1.0.32-test51 code62" in frame or
        "HaloCE Quest test50 candidate 1.0.31-test50 code61" in frame or
        "HaloCE Quest test49 candidate 1.0.30-test49 code60" in frame)
assert ("OpenCE Build206 merged / network29" in frame or
        "OpenCE Build201 merged / network28" in frame or
        "OpenCE Build157 base / network28; selected fixes through Build201" in frame or
        "OpenCE Build157 base / network26; selected fixes through Build184" in frame or
        "OpenCE Build157 base / network24; selected fixes from Builds167,169,170,173,176" in frame or
        "OpenCE Build 157 base / network 24; selected Build167 compatibility fixes" in frame)
updater = read('port/android/app/src/main/java/com/halo/decomp/Updater.java')
assert ('Engine base: OpenCE Build 157; hosting network 29. Selected fixes through Build 206' in updater or
        'Engine base: OpenCE Build 157 / network 28. Selected fixes through Build 201' in updater or
        'Engine base: OpenCE Build 157 / network 26. Selected fixes through Build 184' in updater or
        'Engine base: OpenCE Build 157 / network 24. Selected fixes from Builds 167, 169, 170, 173, 176 and reticle assets from 177' in updater or
        'Engine base: OpenCE Build 157 / network 24, with selected compatibility fixes reviewed against Build 167' in updater)
package_script = read("tools/package-quest.py")
assert ('b"Engine base: OpenCE Build 157; hosting network 29. Selected fixes through Build 206' in package_script or
        'b"Engine base: OpenCE Build 157 / network 28. Selected fixes through Build 201' in package_script or
        'b"Engine base: OpenCE Build 157 / network 26. Selected fixes through Build 184' in package_script or
        'b"Engine base: OpenCE Build 157 / network 24. Selected fixes from Builds 167, 169, 170, 173, 176 and reticle assets from 177' in package_script or
        'b"Engine base: OpenCE Build 157 / network 24, with selected compatibility fixes reviewed against Build 167"' in package_script)
assert 'if candidate_at_least(args.label, 42) else' in package_script
assert 'archive.read("assets/guide/player-guide.txt")).lower()' in package_script
assert 'b"export or import a versioned layout"' in package_script
assert '[] if candidate_at_least(args.label, 42) else' in package_script
assert '"runtime_accepted": bool(args.stable and args.label == "1.0.19")' in package_script
assert 'args.stable and args.label == "1.0.16"' in package_script
assert 'args.stable and args.label == "1.0.18"' in package_script
assert 'args.stable and args.label == "1.0.19"' in package_script
assert 'reject_orphaned_apk_data' in package_script
assert '"source_commit": runtime_commit if args.stable else commit' in package_script
release_notes = read("docs/RELEASE-1.0.18.md")
for marker in ["## 1. Installation", "## 3. Controls / Inputs", "network version 24",
               "All compatible networks", "Hosting and signed advertisements always remain network 24",
               "original Xbox Halo CE XISO", "@MeWhenINameMyself"]:
    assert marker.lower() in release_notes.lower(), marker
guide_generator = read("tools/generate-field-guide.py")
assert "HALO_RELEASE_GUIDE" in guide_generator and "RELEASE-'+stable_release+'.md" in guide_generator

# SPV1's ten map files are larger than 128 MiB, but fit the current bounded
# Custom Edition cache reader. Test66: the owner reports SPV1 working with
# OpenCE's changes, so the launcher no longer warns; its maps still fit.
installer = read("port/android/app/src/main/java/com/halo/decomp/ModInstaller.java")
spv1 = installer[installer.index("static final Mod SPV1"):installer.index("private static final String DETAIL_URL")]
spv1 = spv1[:spv1.index("static final long[] ALTHEROS_DATA_SIZES")] if "ALTHEROS_DATA_SIZES" in spv1 else spv1
map_sizes = [int(size) for size in re.findall(r'new ModMap\("[a-z0-9]+",\s*\d+,\s*(\d+)L\)', spv1)]
assert len(map_sizes) == 10 and min(map_sizes) > 128 * 1024 * 1024
cache_header = read("port/linux/game/cache_file_formats.h")
assert "CUSTOM_EDITION_CACHE_FILE_MAXIMUM_BYTES 0x18000000UL" in cache_header
assert "CUSTOM_EDITION_CACHE_FILE_MAXIMUM_BYTES_UPGRADED 0x24000000UL" in cache_header
launcher = read("port/android/app/src/main/java/com/halo/decomp/LauncherActivity.java")
for marker in ["(experimental; unverified)", "157-253 MiB each", "128 MiB limit",
               "protected-map conversion, resources and gameplay still need"]:
    assert marker not in launcher
# Test66: The Altheros Experience's .yelo maps (the largest 425 MiB) fit the
# OpenSauce-upgraded bound
altheros = installer[installer.index("static final Mod ALTHEROS"):installer.index("static final Mod[] MODS")]
yelo_sizes = [int(size) for size in re.findall(r'new ModMap\("[a-z0-9]+",\s*-?\d+,\s*(\d+)L\)', altheros)]
assert len(yelo_sizes) == 10 and max(yelo_sizes) <= 0x24000000

# Every upstream particle radius field used to make a collision radius is
# checked at its tag-schema callback and wired into that tag's schema.
schema_header = read("port/linux/game/tag_schema.h")
validator = read("port/linux/game/tag_validate.c")
assert "void tag_validate_non_negative(" in schema_header
non_negative = function(validator, "tag_validate_non_negative")
assert "!(*value >= 0.0f)" in non_negative and "*value = 0.0f" in non_negative

render = read("port/linux/game/tag_schema_render.c")
particle = function(render, "particle_check")
type_state = function(render, "particle_system_type_state_check")
particle_state = function(render, "particle_system_particle_state_check")
particle_type = function(render, "particle_system_type_check")
contrail = function(render, "contrail_point_state_check")
weather = function(render, "weather_particle_type_check")
assert "particle->radius_lower_bound" in particle and "particle->radius_upper_bound" in particle
assert "state->variables.particle_state_multipliers.radius" in type_state
assert "state->variables.radius" in particle_state
assert "type->variables.radius" in particle_type
assert '"width", &state->width' in contrail
assert "type->radius_lower_bound" in weather and "type->radius_upper_bound" in weather
for marker in ("TAG_SCHEMA_CHECK(particle_check)",
               "TAG_SCHEMA_CHECK(contrail_point_state_check)",
               "TAG_SCHEMA_CHECK(weather_particle_type_check)"):
    assert marker in render

effects = read("port/linux/game/tag_schema_effects.c")
effect_particles = function(effects, "effect_particles_check")
breakable_particles = function(effects, "breakable_surface_particle_effect_check")
assert "particles->radius_lower_bound" in effect_particles and "particles->radius_upper_bound" in effect_particles
assert "particles->radius_lower_bound" in breakable_particles and "particles->radius_upper_bound" in breakable_particles
assert "TAG_SCHEMA_CHECK(effect_particles_check)" in effects
assert "TAG_SCHEMA_CHECK(breakable_surface_particle_effect_check)" in effects

# Exercise the actual shared correction helper under ASan/UBSan. Its >= form
# intentionally treats NaN as invalid in addition to negative values.
main_source = read("source/main/main.c")
build_label = function(main_source, "main_native_build_label")
error_tail = function(main_source, "main_native_error_tail")
assert "#ifdef HALO_NATIVE_BUILD_INFO" in main_source
assert "main_native_error_tail(error_get())" in main_source
helper_fixture = r'''
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
typedef float real;
struct tag_validation { unsigned corrections; };
static void tag_validate_correct(struct tag_validation *v, char const *format, ...) { (void)format; v->corrections++; }
''' + non_negative + r'''
int main(void) {
 struct tag_validation v={0};
 real negative=-0.25f, positive=1.5f, zero=0.0f, nan=NAN;
 tag_validate_non_negative(&v,"radius",&negative); assert(negative==0.0f && v.corrections==1);
 tag_validate_non_negative(&v,"radius",&positive); assert(positive==1.5f && v.corrections==1);
 tag_validate_non_negative(&v,"width",&zero); assert(zero==0.0f && v.corrections==1);
 tag_validate_non_negative(&v,"radius",&nan); assert(nan==0.0f && v.corrections==2);
 puts("PASS: negative and NaN collision radii correct to zero; valid values remain unchanged");
}
'''

diagnostic_fixture = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define HALO_ANDROID 1
#define HALO_BUILD_NUMBER 0
#define HALO_BUILD_FLAVOR "release"
#define _snprintf snprintf
''' + build_label + "\n" + error_tail + r'''
int main(void) {
 char label[96], long_line[131];
 char const *recent;
 main_native_build_label(label,sizeof(label));
 assert(strcmp(label,"OpenCE Android | local build (release)")==0);
 recent=main_native_error_tail("older\r\nnewer\r\n");
 assert(strcmp(recent,"newer\r\nolder\r\n")==0);
 recent=main_native_error_tail("line0\nline1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\n");
 assert(strncmp(recent,"line9\r\nline8\r\n",14)==0);
 assert(strstr(recent,"line1\r\n")==NULL && strstr(recent,"line0\r\n")==NULL);
 memset(long_line,'x',sizeof(long_line)-1); long_line[sizeof(long_line)-1]=0;
 recent=main_native_error_tail(long_line);
 assert(strlen(recent)==115 && strstr(recent,"...")!=NULL);
 assert(strcmp(main_native_error_tail("\r\n"),"No recent messages. See debug.txt for details.\r\n")==0);
 puts("PASS: native halt diagnostics label the platform and prioritize eight recent bounded error lines");
}
'''

out = ROOT / "build/test35"
out.mkdir(parents=True, exist_ok=True)
for name, source in (("tag_radius", helper_fixture), ("error_screen", diagnostic_fixture)):
    cfile, binary = out / (name + ".c"), out / name
    cfile.write_text(source, encoding="utf-8")
    subprocess.run(["clang", "-std=gnu11", "-O1", "-fsanitize=address,undefined", str(cfile), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)

physics = function(read("source/physics/point_physics.c"), "point_physics_update")
assert "if (!(radius >= 0.0f))" in physics
assert "radius = 0.0f" in physics and "radius_reported = TRUE" in physics
assert physics.index("radius = 0.0f") < physics.index("radius>=0.f")
assert "updater_defines(getattr(sln, \"port_release\", False))" in read("tools/android_build.py")
print("PASS: Build 148 radius sources and platform diagnostic integration are covered")
