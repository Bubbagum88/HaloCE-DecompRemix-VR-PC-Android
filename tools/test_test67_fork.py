"""Test67: the OpenCE fork jcompto95-tech's branches (HALOFREAK95's videos),
as this port took them: what must hold so they never regress the port.

1. Network: the host still advertises network 28 (11..28 joined); the
   community extras use only their own kinds 87-92 (votes, chat, Armor), each
   behind network.community_extras (on by default), so OpenCE network 28 peers
   without them drop them as unknown kinds; the stock vote messages 78/79 are
   unchanged; the launcher's Server Browser turns the extras on or off.
2. Every visual extra off (or "classic") by default, so the stock game is
   what a player gets until they choose otherwise; their rows in Video Setup.
3. The headset: third person never in VR; stencil shadows cast none from the
   player's own body in VR; an item a hand holds is never Jolt's.
4. The pieces the fork dropped or left out that this port keeps: a vehicle
   meeting a dead body bleeds onto it (ragdoll.c calls it); stencil shadows
   one face a draw on every build (no new GL import); the overshield's height
   fade and the armor's recolor/glow in this port's renderer.
5. The VR BUTTONS page's reset: first and last, and DONE once pressed.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: (ROOT / path).read_text(encoding='utf-8', errors='replace')

# 1. network
limits = read('port/linux/include/halo_port_limits.h')
assert re.search(r'#define HALO_PORT_NETWORK_VERSION 28\b', limits)
assert re.search(r'#define HALO_PORT_NETWORK_VERSION_MAXIMUM 28\b', limits)
header = read('port/linux/game/network_distributed.h')
kinds = dict((name, int(value)) for name, value in re.findall(r'_distributed_message_(\w+) = (\d+),', header))
assert kinds['votekick'] == 78 and kinds['votekick_status'] == 79 and kinds['map_share_progress'] == 86
assert [kinds[k] for k in ('vote_choice', 'vote_details', 'chat_up', 'chat', 'armor', 'armors')] == [87, 88, 89, 90, 91, 92]
assert max(kinds.values()) == 92
config = read('port/linux/src/port_config.c')
assert '{ "network.community_extras", _config_boolean, "true", "HALO_NET_COMMUNITY_EXTRAS"' in config
extras = read('port/linux/game/network_extras.c')
assert 'config_boolean("network.community_extras")' in extras
for path, count in (('port/linux/game/armor_sync.c', 2), ('port/linux/game/network_chat.c', 2),
                    ('port/linux/game/network_votekick.c', 4)):
    assert read(path).count('network_extras_enabled()') == count, path
votekick = read('port/linux/game/network_votekick.c')
assert 'if (network_extras_enabled())\n\t\t\t\tdistributed_send_to_machine(machine_indices[index], &details, _distributed_message_vote_details' in votekick
browser = read('port/android/app/src/main/java/com/halo/decomp/ServerBrowser.java')
profile = read('port/android/app/src/main/java/com/halo/decomp/NetworkProfile.java')
assert 'Community extras (armor, chat, vote bans): ' in browser and 'NetworkProfile.setCommunityExtras(' in browser
assert 'ConfigSettings.write(root, "network", Collections.singletonMap("community_extras"' in profile
print('PASS: network 28 kept; the extras only on their own kinds 87-92, each behind network.community_extras; launcher switch')

# 2. defaults and rows
defaults = {
    'display.third_person': '"false"', 'display.stencil_shadows': '"false"', 'display.overshield_effect': '"false"',
    'game.dynamic_blood': '"false"', 'game.vehicle_blood': '"false"', 'game.projectile_effects': '"false"',
    'game.item_physics': '"\\"classic\\""', 'display.big_multiplayer_guns': '"\\"classic\\""',
    'game.corpse_duration': '"\\"default\\""', 'game.corpse_limit': '"\\"default\\""',
    'game.decal_duration': '"\\"default\\""', 'game.decals': '"\\"default\\""',
    'display.spartan_armor_color': '"\\"default\\""', 'display.visor_color': '"\\"default\\""',
    'display.others_custom_armor': '"false"',
}
for key, default in defaults.items():
    m = re.search(r'\{ "' + re.escape(key) + r'", _config_\w+, (".*?"), ', config)
    assert m and m.group(1) == default, (key, m and m.group(1))
menus = ROOT / 'port/assets/menus/ce'
video = 'main_menu.settings_select.player_setup.player_profile_edit.video_settings.'
effects = (menus / (video + 'extra_effects.xml')).read_text()
for setting in ('display.shield_glow', 'display.overshield_effect', 'game.dynamic_blood', 'game.vehicle_blood',
                'game.projectile_effects', 'display.stencil_shadows', 'game.item_physics'):
    assert 'setting="%s"' % setting in effects, setting
graphics = (menus / (video + 'graphics.xml')).read_text()
for setting in ('game.death_physics', 'display.big_multiplayer_guns', 'game.corpse_duration', 'game.corpse_limit',
                'game.decal_duration', 'game.decals'):
    assert 'setting="%s"' % setting in graphics, setting
assert '/op_decals" x="54" y="373" platform="desktop"/>' in graphics
fov = (menus / (video + 'fov_viewmodels.xml')).read_text()
assert 'setting="display.third_person"' in fov and 'spartan_armor/spartan_armor_settings_screen' in fov
print('PASS: every visual extra stock by default; rows in Extra Effects, Graphics and FOV and Viewmodels')

# 3. the headset
third = read('port/linux/game/third_person.c')
assert '#ifdef HALO_VR' in third and 'if (vr_active())' in third
shadows = read('port/linux/game/stencil_shadows.c')
assert '#define STENCIL_SHADOWS_ONE_FACE 1' in shadows and '#ifdef HALO_GLES' not in shadows
assert '&& !vr_active()' in shadows[shadows.index('static short stencil_shadow_casters('):]
items = read('port/linux/game/item_physics.c')
assert 'item_physics_held(item_index)' in items and 'vr_world_interaction_remote_owned(item_index)' in items
assert 'network_game_distributed_client()' in items
print('PASS: no third person in VR; no own-body stencil shadow in VR; a held item is the hand\'s; clients take the host\'s items')

# 4. kept pieces
blood = read('port/linux/game/blood.c')
assert 'void blood_vehicle_hit_body(' in blood and 'blood_vehicle_hit_body(' in read('port/linux/game/ragdoll.c')
renderer = read('port/linux/src/d3d8_gl.c')
for name in ('void d3d8_gl_draw_positions(', 'void d3d8_gl_set_height_fade(', 'void d3d8_gl_set_recolor(',
             'void d3d8_gl_set_glow(', 'void halo_screen_light_bloom('):
    assert name in renderer, name
assert 'glStencilOpSeparate' not in read('port/linux/src/gl.h')
psh = read('port/linux/src/nv2a_psh.c')
assert 'uniform vec4 recolor;' in psh and 'uniform vec4 glow;' in psh and 'blend_constant' not in psh
print('PASS: vehicle-hit blood kept; stencil volumes one face a draw; height fade, recolor and glow in this renderer')

# 5. the VR BUTTONS page's reset
menu = read('port/linux/game/vr_menu.c')
buttons = menu[menu.index('static struct vr_menu_setting const vr_menu_buttons[] =\n{'):]
buttons = buttons[:buttons.index('\n};')]
rows = re.findall(r'\{ "([^"]+)", "([^"]*)", (_vr_setting_\w+)', buttons)
assert rows[0] == ('ALL TO DEFAULT', 'buttons', '_vr_setting_reset_buttons'), rows[0]
assert rows[-1] == ('RESET BUTTONS', 'buttons', '_vr_setting_reset_buttons'), rows[-1]
assert '"DONE" : "APPLY"' in menu and 'vr_menu_buttons_reset_at = system_milliseconds();' in menu
print('PASS: the VR BUTTONS page resets from its first row (ALL TO DEFAULT) and its last, and says DONE')

# 6. licenses: what Test67 brings, credited, with its full notices
credits = read('CREDITS.md')
notices = read('THIRD-PARTY-NOTICES.txt')
for name in ('jcompto95-tech', 'GulchCE', 'bcdec', 'JavaSteam', 'OkHttp', 'Ktor', 'Bouncy Castle', 'Protocol Buffers',
             'SLF4J', 'XZ for Java', 'zstd-jni', 'Zstandard'):
    assert name in credits[credits.index('## Test67 additions'):], name
for title in ('JavaSteam and javasteam-depotdownloader 1.8.0 (MIT)', 'Bouncy Castle bcprov-jdk18on 1.83 (MIT)',
              'Protocol Buffers for Java 4.31.1 (BSD-3-Clause)', 'SLF4J API 2.0.17 (MIT)', 'XZ for Java 1.11 (0BSD)',
              'zstd-jni 1.5.7-6 (BSD-2-Clause)', 'Zstandard, inside zstd-jni (BSD)', 'port/third_party/bcdec/LICENSE'):
    assert '===== %s' % title in notices or '===== Test67: %s' % title in notices, title
assert 'TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION' in notices[notices.index('Test67: Apache License 2.0'):]
print('PASS: Test67\'s fork, GulchCE, bcdec and Steam Workshop libraries credited, each with its complete notice')
