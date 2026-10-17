"""Run deterministic Quest/flat regressions serially. Does not launch the game.

Run with Linux/WSL clang and a JDK. Per-suite output is under ignored build/.
Cache-format pytest tests are separate: python3 -m pytest -q tools/test_cache_file_formats.py
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/quest-regressions'
# (test27: test_campaign_actors tested the retired CE01/CE02 co-op's actor
# messages, replaced by OpenCE's co-op; it is kept in tools/ for the record)
SUITES = [
    'test_android_asm_convert', 'test_android_guest_prototypes', 'test_voice_encode_hardening', 'test_contact_acquisition', 'test_vr_tick_head_view', 'test_vr_immersion_menu', 'test_network26_signalling', 'test_opence_184_integration', 'test_test54_interactions', 'test_test55_polish', 'test_test56_ragdoll', 'test_test60_toggles', 'test_test61_vehicle_hold', 'test_test61_fixes', 'test_test62_fixes', 'test_test62_extra', 'test_test62_contact', 'test_test63', 'test_test65', 'test_test66', 'test_test66_campaigns', 'test_test66_ragdolls', 'test_test67', 'test_test67_campaigns', 'test_test67_strike', 'test_test67_resources', 'test_test67_combat_pose', 'test_test67_combat_moves', 'test_test67_projectile_parry', 'test_test67_mcc', 'test_test67_mcc_upstream', 'test_test67_upstream_harness', 'test_test67_fork', 'test_test68_network29', 'test_test69_opensauce', 'test_test69_scripts', 'test_test70_launcher', 'test_test70_controls', 'test_test70_weapons', 'test_test70_movement', 'test_test71_mods', 'test_test71_reload', 'test_openxr_bindings', 'test_test72_pico', 'test_test72_flat_movement', 'test_test72_windows', 'test_test72_stereo', 'test_test72_combat', 'test_test72_menus', 'test_test72_lefthand', 'test_test72_passenger', 'test_test72_spv1', 'test_test72_eyes', 'test_test72_opence208', 'test_test72_deflection', 'test_test72_tester', 'test_test72_launcher', 'test_test72_hf95', 'test_test72_network_mtu', 'test_test72_controller', 'test_test72_saves', 'test_test72_third_person', 'test_test56_polish', 'test_test57_vehicles', 'test_test57b_vehicle_anchor',
    'test_test59_network28', 'test_test59_reload_ragdoll', 'test_test49_haptics_melee',
    'test_test17_network_data', 'test_test16_actions',
    'test_campaign_lifecycle', 'test_campaign_capacity', 'test_quest_browser',
    'test_quest_vr_math', 'test_quest_render_targets', 'test_test15_refinements',
    'test_test15_io', 'test_android_gamepad', 'test_vr_vehicle_lifecycle',
    'test_test18_vehicle_tutorial', 'test_test19_network_browser', 'test_test19_media',
    'test_test20_render_perf', 'test_test20_alignment', 'test_test20c_hands', 'test_test20d', 'test_test20e_network', 'test_test20e_reticle', 'test_test21', 'test_test22', 'test_test23', 'test_test24', 'test_test24b', 'test_test25', 'test_test26', 'test_test27', 'test_test28', 'test_test29', 'test_test30', 'test_test31',
    'test_test31_transparency',
    'test_test31_vehicle_glass',
    'test_test31_menu_assets', 'test_test31_menu_maps',
    'test_test31_text_input', 'test_test31_audio', 'test_test31_reverb',
    'test_test31_menu_platform', 'test_test31_browser_filters',
    'test_test31_menu_lifecycle', 'test_test31_vr_menu',
    'test_test31_menu_presentation',
    'test_test31_flat_pointer',
    'test_test31_menu_settings', 'test_test31_graphics',
    'test_test31_vr_local_players',
    'test_test31_touch_lifecycle',
    'test_touch_layout_codec',
    'test_test31_menu_startup',
    'test_test32_launcher',
    'test_test32_hud_gesture',
    'test_test32_vehicles',
    'test_test32_geometry',
    'test_test32_menu_arrows',
    'test_test33_network_browser_lifecycle',
    'test_test34_opence',
    'test_test35_opence',
    'test_test36_opence157',
    'test_test37_network_profiles', 'test_test37_launcher', 'test_test37_wire',
    'test_test38_network_interaction', 'test_test38_network_input', 'test_legacy_coop_layouts', 'test_test38_scope_vehicle', 'test_test38_vehicle_handles',
    'test_test38_contact', 'test_test38_contact_volume', 'test_test38_close_contact', 'test_manual_reload', 'test_magazine_debris', 'test_solo_multiplayer_spawn', 'test_vr_world_physics', 'test_vr_vehicle_lift', 'test_vr_npc_interaction', 'test_vr_npc_rescue', 'test_vr_parkour', 'test_vr_holster_haptics', 'test_interaction_lifecycle', 'test_manual_reload_palette', 'test_interaction_impact', 'test_prop_collision', 'test_hand_compliance', 'test_vr_arm_ik_reach', 'test_world_remote', 'test_vr_world_props', 'test_prop_native_sync', 'test_reload_contact', 'test_vr_optional_feedback',
    'test_host_watch_hash',
    'test_android_memory_reclaim', 'test_opence_177_integration',
    'test_opence_167_fixes',
    'test_test42_refresh_rate',
    'test_voice_chat_integration',
    'test_voice_chat_protocol',
    'test_test46_candidate', 'test_vr_pending_release', 'test_vr_weapon_release_latch',
    'test_vr_corpse_retention', 'test_package_candidate_metadata',
]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    failed = []
    for name in SUITES:
        print('RUN', name, flush=True)
        with (OUT / (name + '.log')).open('w') as log:
            result = subprocess.run([sys.executable, str(ROOT / 'tools' / (name + '.py'))],
                                    cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        print('FAIL' if result.returncode else 'PASS', name, flush=True)
        if result.returncode:
            failed.append(name)
    print('Failed suites:', failed, flush=True)
    return bool(failed)

if __name__ == '__main__':
    sys.exit(main())
