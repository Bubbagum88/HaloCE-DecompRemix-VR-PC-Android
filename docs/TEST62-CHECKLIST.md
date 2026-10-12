# Test62 implementation and evidence checklist

Private **1.0.29-test62 / code74**; branch `test39-interaction-completion`.
Baseline: Test61 `ccb380e5` / record `23dd309f`, plus `4ed9b8f3`
impact fallback. Owner's 2026-10-12 08:58 log and 08:03 vehicle video were
reviewed locally. Device acceptance is pending for every changed behavior.

## Scope ledger

| Request | Implemented behavior | Evidence to rerun/record | Device status |
|---|---|---|---|
| Settle boarding eyes before control lock | 0.5 s minimum, 0.35 s stable within 1.5 cm, 3 s cap; vehicle-local sample | test_test57b_vehicle_anchor; seat/held-wheel regressions | Pending |
| All-vehicle adjustments | CTRL REACH/LEFT/HEIGHT adds to four profiles; finite/clamp/comfort limits | Production prepare harness and menu width/pagination checks | Pending |
| Easier contact grab | 5 cm default assist, 16 cm with default contact; saved settings stay | Production body-capsule near/far/distinct-node tests | Pending |
| Heavy restraint, allies and corpses | Stationary root at first grip; second distinct grip lifts living Elite/Hunter; corpses one-hand | Production velocity harness, both heavy mobilities, release/death transitions and native melee-restraint guards | Pending |
| Responsive floor/wall/body slams | Globals damage fallback; floor uses configured threshold; repeated-hit debounce retained | test_interaction_impact, test_test62_fixes, native sphere-sweep harness | Pending |
| Shield break/blood on actual impacts | Native damage/depletion first; body art only after vitality loss, own localized effect or loaded assault-rifle body-material response; no new tag loads | Production contact-damage wrapper plus shield/body/no-art/duplicate-effect tests; impact/melee caller wiring | Pending |
| Ragdoll solver, range and recovery | 60 m default, 20..80 adjustable; 24 slots; parent topology validation; recovery <=1 s | 12 stock skeletons x 9 cases, invalid-rig no-mutation cases | Pending |
| More natural reload grip | Free hand uses adjusted visible palm rotation, either handedness | test_test59_reload_ragdoll and manual-reload state/contact suites | Pending |
| Reload insertion/rack feedback | Protect brief event pulses from same-hand rendered and central wall-contact overwrite; master HAPTICS retained | test_test62_fixes pulse timing, rollback/invalid-value and handedness cases | Pending |
| Parkour responsiveness | CLIMB GRAB default 14 cm, WALL TIME 2 s; actual hand-to-surface radius on ray fallback; saved choices/state rules stay | Production parkour suite and defaults checks | Pending |
| Enemy-only assisted fist combat | Optional gaze/punch acquisition, collision-resolved approach, same-target combo restraint, 0.9 s stun/rear damage, closed-fist/positive-speed requirements, native melee-stun guards and capsule spacing | test_test62_extra uses production module under ASan/UBSan; native melee call wiring and dependency checks | Pending |
| Combat visuals/audio | Head/chest highlights, hit flash and rigid spine-subtree reaction; native hurt sounds/damage | Production reaction fixture checks finite/limb lengths/original palette preservation | Pending |
| Physical chest grenades | Optional free-hand contact/Grip/release, adjustable slots, momentum, count only after valid native spawn | test_test62_extra production state/native projectile tests: reservation, lost-owner/recenter/fresh-grip cancel, release-tick button suppression, wall/BSP, count/owner, authority; fresh-palm/world-clamp and independent-hand event haptic fixtures | Pending |
| Reticle micro-movement | AIM STEADY shares gun/shot/scope angular pose; default OFF retains scope filter | Scope and aim regressions; recenter/time guard inspection | Pending |
| Scope attachment | Fresh rendered wrist anchor includes offsets/pullback; shared aim orientation and existing per-gun settings | test_test22 fresh/stale anchor and both-hand/profile cases; zero-offset publication and renderer order inspection | Pending |
| Host permissions and multiplayer safety | Server Setup HOST VR ACTIONS plus existing VR INTERACTIONS handshake; new actions host-only; PvP/guests native | test_test62_extra session/permission gates; existing physical-network and native-menu tests | Pending paired clients |
| Auto toggles and feature conflicts | Existing dependency resolver extended for fist combat; exclusive hand ownership respected | test_test60_toggles plus reload/holster/drop/contact/parkour suites | Pending |
| Flat controls, saves, lifecycle, voice | Familiar flat UI and existing behavior retained; no protocol/voice implementation edits | Full regression suite, both native builds, APK/signature/identity checks | Pending |
| Complete matching packages and handoff | Code74, both APKs, source/guide/delivery record | Final hashes, cert, manifest and clean source commit recorded on completion | Pending |

## Full request accounting

This is the active Test62 scope, including additions after the four-item
handoff. A populated implementation row is not a claim that a headset result
exists. The related device checks remain required.

| Owner request | Current outcome and limits |
|---|---|
| Resume Test62 from the handoff; review the D: log/video evidence | Handoff and latest 08:58 log read; vehicle video reviewed. The four original requests are the first rows above. Evidence findings are distinguished from historical claims. |
| Refine ragdolls, optionally use Euphoria-like behavior or a better solver if safe | Parent-relative solver refined/guarded and stock skeleton harness retained. Active balance, motors and Euphoria replacement were conditional investigations, not mandatory unimplemented features: no validated replacement was found, so it was not added. |
| Keep working manual reload; improve magazine hold, insertion/cocking feedback and responsiveness | Palm alignment and haptic priority changed; existing native transaction, ammo conservation, input choices and tolerances retained. Per-weapon feel still needs device evidence. |
| Review/refine everything since the latest public release; defaults and automatic requirements | The inherited-feature ledger below maps retained systems, source areas and checks. New defaults are modest and preserve saved choices. This is not an assertion that every line or all runtime combinations were tested. |
| Make immersive vehicles as good as possible | Settling/anchor corrections, all-vehicle offsets and existing per-vehicle controls/comfort features covered. Driving comfort across every seat/map is a device check. |
| Improve parkour by default | 14 cm climb contact and 2 s wallrun defaults; eye-to-hand acquisition bounded by actual surface distance; input and host restrictions retained. Contact and lifecycle regressions remain required. |
| Arkham Shadow-style fist targeting, approach, repeated combat and enemy-only lock | Optional gaze/punch acquisition with native-collision approach; one renewable two-second target lock restrains horizontal enemy movement. It is not a permanent magnetic attachment or a camera rotation/teleport. Allies and players are not acquisition targets. |
| Automatically enable fist-required melee; highlights, stun, rear takedown, grab/slam follow-up | Required fist/impact/positive-speed behavior and suggested contact/grab settings are covered. Head/chest highlights and timed stun/rear-damage follow-up use native damage/protection rules. A rear strike is increased native melee damage, not an unconditional instant kill. |
| Custom animations and appropriate effects/sounds enabled by combat | Procedural hit/stun spine reaction plus highlight/impact flash, existing physical-hit haptics and native hurt/material audio/effects. No new choreographed takedown animation or copied Arkham assets. Skeletons without a suitable spine keep native animation. |
| GoldenEye-style steadier reticle and review drifting scopes, effective per-gun alignment | Optional shared angular AIM STEADY plus fresh final-wrist scope origin; existing per-weapon offsets remain. No unmeasured universal per-gun defaults or separate cosmetic reticle filter. |
| Optional chest grenades, adjustable location, physical grip/release and momentum | Frag/plasma representations, three position controls and throw scale; sampled hand momentum feeds native projectiles with counts reserved safely. Tracking/state/owner loss cancels and needs a fresh grip. |
| Full multiplayer/co-op compatibility pass; auto-disable where necessary and host options if possible | New HOST VR ACTIONS in native Server Setup uses the existing handshake. New actions run locally or on a permitted co-op host, not remote clients/PvP. Existing four-remote-machine NPC pose limit and local-only feature guards remain; no protocol changes were authorized. |
| Shield break and blood/body splatter for strong floor/wall slams throughout the game | Native damage owns actual shield depletion; real body loss selects authored body/material art, with loaded-asset fallback. Missing art is skipped. Tests cover selection/guards; all campaign maps/species are not device-certified. |
| Full suite, identity, both builds, package, docs, delivery and local commits | 1.0.29-test62/code74. Final results/hashes belong in DELIVERY-STATUS. No install, launch, push, release, protocol or voice implementation edits. PC/Steam Frame deferred. |

## Inherited-feature regression ledger: public v1.0.18 through Test61

The **verified current public baseline is v1.0.18**, checked live on
2026-10-12: [releases/latest](https://github.com/moistman42069/HaloCE-Quest-VR/releases/latest)
resolved to [v1.0.18](https://github.com/moistman42069/HaloCE-Quest-VR/releases/tag/v1.0.18),
network24/code48. The local annotated `v1.0.18` tag peels to the matching
live release commit `3867cd0ed565e8da97f3e9c62c27e316e30a4b73`.
RELEASE-PROVENANCE-1.0.18 records runtime source
`2680beaa42d9b53098a21198200f79c76aa3b308` and final APK hashes.

CURRENT-STATE's former v1.0.19 pointer was stale. That attempted release was
withdrawn/cancelled; no local v1.0.19 tag exists. Its historical notes and
private Test38-61 work still matter to the regression audit, but are not a
newer accepted public baseline. Public artifacts are not modified here.

This ledger covers **all private work since v1.0.18**, including Test38-52,
rather than only the later Test53-61 refinements. History sources include
Test38/39/43/47 device checks, Test48/49 regression records, Test50/51 crash
and diagnostic records, Test52/53 converter/voice investigation and the
Test53-61 implementation checklists. These records identify intended behavior
and past defects; production paths and current tests remain the evidence
for this candidate.

Key source milestones include `b0ffc182`/`ca1f5cc4` (signed-handle weapon
release), `8e15b331` (contact haptic restoration), `0353820e` (reticle/voice
diagnostics), `a11229c8` (voice config join failure), `206258e4`/`0d95d381`
(asm/voice/ABI hardening), `95707191`/`e16de259` (touch/head pose),
`8f863ee2` (Test54 interactions), `64bc7e48` (Test55 polish),
`46a18740` (parent-relative solver), `edfdfc5e` (immersive steering),
`5553d6f9` (vehicle profiles), `131edc83` (drawn-vehicle anchor),
`84cc50f3`/`6817b021`/`96a907f5` (Test59 vehicles/reload/network28),
`e2769e90` (Test60 impacts/dependencies), and `0cc1ec73` (Test61).

**Evidence key:** source locations and test registrations/bodies were located
for this audit; a listed suite is a coverage mapping, not its current pass
result. Final runs must be recorded separately. All rows have device/runtime
acceptance pending for the new candidate.

| Retained area / relevant private history | Production areas to preserve | Existing automated coverage / final gate | Still unknown on the new APKs |
|---|---|---|---|
| Join, browser admission, co-op lifecycle and 128-player menu capacity; Test53/59 selected OpenCE updates | `network_distributed.c`, `network_browser.c`, `network_coop.c`, `network_objects.c`; campaign lifecycle/game state | `test_test17_network_data`, `test_test33_network_browser_lifecycle`, `test_campaign_lifecycle`, `test_campaign_capacity`, `test_network26_signalling`, `test_opence_184_integration`; focused `test_test59_network28` | Real joins/rejoins, long campaign/checkpoints, mixed peers and high-population performance; 128-player capacity is not a stability certification |
| Voice and native/guest ABI; Test52/53 converter/Opus repair | `voice_audio.c`, `network_voice.c`, Android asm conversion/build tools and guest ABI declarations | `test_android_asm_convert`, `test_android_guest_prototypes`, `test_voice_encode_hardening`, `test_voice_chat_integration`, `test_voice_chat_protocol`, built-image check and ABI lint | Actual mic permission, speaking/hearing, host disabled voice, join/exit while streaming; Test62 does not edit voice or protocol |
| Holsters, release-grip drop, firing/contact haptics, two-hand gun handling; v1.0.18 regression repair retained | `vr_frame.c`, `vr_render.c`, interaction hand owner/latch helpers | `test_vr_weapon_release_latch`, `test_vr_pending_release`, `test_vr_holster_haptics`, `test_vr_optional_feedback`, `test_test21`, `test_test22`; focused `test_test49_haptics_melee` | Idle vibration, shooting feel, weapon swap versus melee, both-handed grip/drop and overlapping holster/pouch contacts |
| Manual reload, both pouches, calibration, old-mag reseat, charging and persistent same-map debris; Test53-61 | `vr_manual_reload.c` and math/contact helpers; `vr_frame.c` pouch/holster placement; `vr_render.c` palms | `test_manual_reload`, `test_manual_reload_palette`, `test_reload_contact`, `test_magazine_debris`, `test_test54_interactions`, `test_test55_polish`, `test_test61_fixes`; focused `test_test59_reload_ragdoll` plus Test62 pulse tests | Each supported weapon, empty/tactical reload, moving/recentering, left/right hand, insertion/rack feel, saved pouch offsets; local-play limit retained |
| Contact-driven props/scenery, custom scenery, whole-vehicle lifting, mass/throw strength and remote ownership; Test53-56 | `vr_world_interaction.c`, `vr_world_props.c`, collision/hold/vehicle-lift math; `network_interaction.c` | `test_contact_acquisition`, `test_vr_world_physics`, `test_vr_world_props`, `test_vr_vehicle_lift`, `test_prop_collision`, `test_world_remote`, `test_prop_native_sync`, `test_test38_network_interaction` | Dense scenes, script-owned exceptions, occupied/unsafe vehicles, actual multiplayer contact and handover |
| NPC/allies, custom rigs, rescue, close-contact capsules, living recovery; Test53-61 | `vr_npc_interaction.c`, `vr_npc_rescue.c`, `bipeds.c`, stock/custom rig construction | `test_vr_npc_interaction`, `test_vr_npc_rescue`, `test_test38_close_contact`, `test_test54_interactions`, `test_test56_polish`, `test_test61_fixes` | Each species/ally, scripted situations, moving platforms and rescue destinations; custom-rig fallback remains local-only and guarded |
| Death ragdolls, retained corpses, 24 slots, force/impact damage and bounded recovery; Test53-61 | `vr_articulated_native.c`, `vr_npc_impulse.h`, `vr_interaction_impact.c`, damage/garbage collection | `test_test56_ragdoll`, `test_vr_corpse_retention`, `test_interaction_impact`, focused `test_test59_reload_ragdoll`, Test62 contact/rig tests | Real animation handoff, all maps/surfaces, heavy busy scenes and stable frame time; no Euphoria/active-balance claim |
| World climbing, wallrun/jump/leap, sprint hold/toggle, arm run, shake cooling and dependencies; Test53-60 | `vr_parkour.c`, `vr_frame.c`, `bipeds.c`, `vr_menu.c`, interaction state helpers | `test_vr_parkour`, `test_vr_tick_head_view`, `test_test54_interactions`, `test_test55_polish`, `test_test60_toggles`, `test_interaction_lifecycle`, `test_test38_contact` | Real wall topology, chained moves, tracking resets, optional sprint behavior and mixed-feature contacts |
| Immersive wheel/bar/stick, reach, control glow/haptics, seat/view/recenter, glass/hatch; Test55-61 | `vr_vehicle_handles.h`, `vr_render.c`, player/vehicle-control math; per-vehicle profile table | `test_test38_vehicle_handles`, `test_test57_vehicles`, `test_test57b_vehicle_anchor`, `test_test61_vehicle_hold`, `test_vr_vehicle_lifecycle`, `test_test31_vehicle_glass`, `test_test32_vehicles` | Warthog/Ghost/Scorpion/Wraith/Banshee actual seats, tilt, passenger/co-op behavior, hidden wheel and first/third-person comfort |
| Full body/hands/fingers, fixed arm length, native animation handoff and contact smoothing | `vr_render.c`, articulated/body IK and contact math, render palettes | `test_vr_arm_ik_reach`, `test_hand_compliance`, `test_test20c_hands`, `test_test16_actions`, `test_test38_contact_volume`, `test_test54_interactions` | Hands/body modes, forearm/torso clipping, both eyes, weapon-specific animations and Quest OS differences |
| All supported scope profiles, reticle-to-shot matching, mounted weapons/turrets and aiming | `vr_frame.c`, `vr_scope_profiles.h`, `vr_render.c`, unit firing ray | `test_test20e_reticle`, `test_test22`, `test_test38_scope_vehicle`, `test_test57_vehicles`, Test62 fresh-anchor tests | Scope alignment by gun and hand, tank/Shade/Ghost hit direction, micro-movement feel and revisions |
| Android touch/controller/gyro, hot plug, visibility, free look and layout export/import/hide | `TouchControls.java`, `TouchLayout*.java`, `Gamepad*.java`, `Gyro*.java`, `HaloActivity.java` | `test_android_gamepad`, `test_test31_touch_lifecycle`, `test_touch_layout_codec`, `test_test15_io`, `test_test31_flat_pointer` | Real devices/controllers, disconnect recovery, touch layout after update and concurrent touch/gamepad |
| Save/profile/checkpoint continuity, solo MP-map spawn and map lifecycle | `source/saved games/game_state.c`, player spawn, launcher active-root selection and campaign code | `test_campaign_lifecycle`, `test_solo_multiplayer_spawn`, `test_interaction_lifecycle`, `test_host_watch_hash`, Android/native file tests | Real previous saves, checkpoint reload with active interactions and map transitions |
| ISO/revision selection, imported-data/inbox deletion and save isolation; Test43 retained | `GameDataLibrary.java`, `GameDataManager.java`, `XisoExtractor.java`, launcher active paths | `test_test19_media`, `test_test17_network_data`, `test_test32_launcher`, `test_test37_launcher`; separate `pytest tools/test_cache_file_formats.py` | SAF permissions, real original/Rev1/Rev2 import, one/multiple sets, deletion UI and storage exhaustion; source images outside managed inbox are not silently deleted |
| Launcher network selector/population, compatible updater, native browser/menu pointer/arrows/help | `NetworkProfile.java`, `NetworkSettings.java`, browser/invite Java, `Updater.java`/`UpdatePolicy.java`, `menu_functions.c` and menu XML | `test_test37_network_profiles`, `test_test37_launcher`, `test_quest_browser`, `test_test15_io`, `test_test32_launcher`, `test_test32_menu_arrows`, native menu/platform/lifecycle suites | Live directory contents/population, server reachability, actual signed update install and full headset pointer ergonomics |
| Safe geometry defaults, a10 crosshair calibration, performance/memory/refresh and renderer guards | `port_config.c`, launcher geometry policy, `vr_frame.c` tutorial ray, render/Android memory paths | `test_test32_geometry`, `test_test18_vehicle_tutorial`, `test_test20_render_perf`, `test_test42_refresh_rate`, `test_android_memory_reclaim`, `test_quest_render_targets` | Problem geometry/maps, actual light calibration, frame deadlines/thermal behavior and sustained memory load |
| Logs, supplied icon fit, guides, identities and matching package contents | `RunLog.java`, native diagnostics, Android icon resources, `generate-field-guide.py`, `package-quest.py` | Launcher log-destination checks; package icon-layer/hash, guide-marker, asset/version/cert/ZIP checks | Real log export after crash/launch and launcher icon crop on both devices; final artifact checks pending |

Focused tests `test_test49_haptics_melee`, `test_test59_network28` and
`test_test59_reload_ragdoll` were found outside the registered full-suite list
during this audit and added to the runner. Their final run results must still
be recorded; registration alone is not a pass. Cache-format pytest,
whole-program ABI checks and APK packaging checks remain separate from the
Python suite runner.

### Bounded combat presentation

The requested target lock is implemented as a renewable two-second same-target
restraint and a collision-resolved approach by the player. It does not turn
the camera or drag an enemy around to remain attached to the center of view.
Disengagement/occlusion/distance guards release it. Custom animation currently
means the procedural hit/stun reaction, not a newly choreographed finisher.
The rear action applies native damage with the assist's multiplier and retains
engine protection rules. Device acceptance must include whether these bounded
choices achieve the intended combat feel.

## Evidence and limits

- The pre-lift root driver followed a moving hand target; a first grip did
  not provide stationary restraint. The fix uses native collision, not root
  teleportation or removal of actor metadata.
- `VR impact: no melee damage` in the owner's log proves the missing campaign
  damage effect. The independent 6 m/s floor cutoff was stricter than the
  user's IMPACT SPEED setting. Damage still respects directional impact speed,
  caps and per-target debounce.
- The contact-damage wrapper calls native damage first, then checks real body
  vitality loss before creating authored body/material effects. Stock Elite
  collision data has no localized effect, so the optional fallback reads the
  already loaded assault-rifle projectile's response for the body's material.
  No loaded effect means no extra art. Existing native shield depletion is
  retained; the wrapper avoids duplicate localized effects and does not force
  every slam to break a shield. Logs include before/after vitality, effect tag,
  scale and material for further map-specific reports.
- Assisted empty-fist damage first exhausts the unit/weapon/unarmed lookups.
  Only if all are NONE and assistance is active does it use one quarter of
  the native globals impact effect; this is not a general melee-damage change.
- Reload haptic replacement is a code-path finding, not a user-feel claim:
  rendered contact requests followed a reload request on the same action.
  [OpenXR xrApplyHapticFeedback](https://registry.khronos.org/OpenXR/specs/1.1/man/html/xrApplyHapticFeedback.html)
  specifies replacement of a running haptic event.
- The scope used the controller origin after the drawn gun was translated
  to its wrist/offset/pullback position. Test62 hands the fresh final wrist
  origin to the scope even when wrist translation is zero; it does not add
  a guessed revision-specific correction.
- The final audit also covers grenade ownership loss/recenter cancellation,
  a fresh Grip edge after cancellation and reserving the release tick against
  a simultaneous button throw. Combat OFF/invalid speed cancels its state;
  enabling the menu feature restores a positive default only if speed was OFF.
  Approach uses native biped capsule widths, not the larger render bounds.
- The four-remote-machine NPC pose budget is an existing protocol constraint.
  Normal co-op capacity is unchanged. Manual reload/custom-rig/debris local
  restrictions and existing parkour host restrictions remain documented.
  No voice or network-protocol implementation change is authorized.
- New chest throws, combat assistance and visual reactions are experimental.
  Tests use production functions with bounded engine fixtures; they do not
  substitute for actual game maps, controller tracking, two-eye visuals,
  paired co-op or performance measurements.
- Euphoria/better-solver work was assessed. The existing parent-relative solver
  and native recovery were retained. Active balance, motor control and the
  broader reactive behavior system described by Euphoria's developers are
  not implemented or claimed. A speculative replacement would abandon the
  stock-skeleton evidence without comparable game validation.
- Existing guarded behavior for unusual/custom rigs and scripted actors is
  retained. There is no promise that arbitrary content or every server works.
  PC/Steam Frame remains deferred.

## Stock-cache impact evidence

The impact lookup was checked against **24 extracted stock USA cache files**,
not inferred from the unit definition alone. Local evidence is retained in
`D:\HaloQuest\_scratch\impact-tags62.txt` and
`D:\HaloQuest\_scratch\impact-native62.json`; those are private inspection
reports, not game-data assets for the package.

- All **23 playable maps** contain `globals\falling` with authored damage
  bounds 155/155 and flags 0, including no shield-skip flag. The UI cache has
  no such gameplay damage entry. These authored values are not a claim that
  every hit deals 155 damage: impact scale, resistance and native rules apply.
- Across the seven campaign caches containing the standard Elite collision
  definition, localized damage art is NONE and the native shield-depletion
  effect is present.
- The loaded assault-rifle projectile has body material 14's response
  `weapons\assault rifle\effects\impact elite armored skin` in those caches.
  This is the grounded fallback used when the body has no localized effect;
  it is not a guessed blood tag or a shield effect reused for flesh.
- Cache inspection proves availability/selection inputs for these stock files.
  It does not prove the on-headset effect appearance, hit timing, every game
  revision/mod or all possible network outcomes.

## Final lifecycle/contact audit

- New-map initialization and old-map disposal in `objects.c` now clear
  grenade/combat state, in addition to checkpoint restore and input/session
  guards. Reused datum values cannot keep a prior map's lock/held grenade.
- `parkour_grab_through` now rejects the ray crossing unless the hand-to-hit
  distance is within its configured radius. The former comment promised that
  bound, but the code did not enforce it.
- FIST COMBAT has hard menu dependencies on FIST REQUIRED, impact MELEE and
  positive MELEE SPEED. Switching MELEE to SWING or MELEE SPEED to OFF turns
  the assist off visibly. Enabling it preserves an existing positive threshold.
  Direct configuration still requires closed-fist input and impact mode at runtime. Native swing
  and assisted direct impact cannot run together; menu dependencies are not
  the only enforcement point.
- The NPC authority audit found that production `network_interaction_npc_ready`
  can be true on a negotiated client too. Authority now additionally requires
  an explicit server connection outside local play. Client grips and replicated
  display keep their existing path; the wire protocol is unchanged. The
  `test_test62_contact` fixture uses real readiness/authority/control functions
  for a ready client and permitted host, rather than mocking every client
  as not ready. Paired-device outcomes remain pending.
- Native melee startup, queued hit keyframes, contact attachment and continuous
  melee damage consult the bounded combat-stun/NPC-restraint guard. Restraint
  applies on authorized VR or flat co-op hosts; unrelated actors/player melee
  retain their normal path. Native recovery remains in charge after release.
- Held grenade visuals use the final post-contact/post-action-blend palm.
  Publication/getter checks include valid hand, unit, contact epoch, exact
  pose timestamp and finite geometry. Hidden or unsupported rigs use tracking
  plus the native projectile obstruction query with shell clearance; stale
  visual palms do not get reused. These are visual guards, not a replacement
  for the release-time native projectile placement check.
- Grenade pickup/release events protect 40/65 ms feedback against subsequent
  continuous surface/finger requests on that hand. Independent hand timing,
  reset and invalid-clock cases have focused production fixtures. This does
  not replace the master HAPTICS policy or prove physical controller feel.
- Cache-format pytest has completed: **127 passed, 4 skipped**. The four skips
  are optional real custom-map fixtures not present here; they do not establish
  SPV1/custom-map support. Both full-suite/native build gates passed; final APK/package verification is recorded separately in DELIVERY-STATUS.

## References used for design/review

No external game code, assets, animations or sounds were copied.

- [GoldenEye VR project](https://github.com/MrSco/goldeneye-vr):
  aim-steadying reference; Halo extends its existing shared aim filter.
- [Arkham Shadow director interview](https://www.pockettactics.com/batman-arkham-shadow-interview):
  gaze, punching and movement as a combat reference. Halo's implementation
  uses its own collision, allegiance, animation palettes and damage.
- [Official Arkham Shadow description](https://www.dc.com/games/batman-arkham-shadow-2024):
  inspiration, not feature parity.
- [NaturalMotion on Euphoria](https://mcvuk.com/development-news/ecstatic-movement-naturalmotion-on-euphoria/):
  developer explanation used to distinguish active reactive behavior from
  this port's bounded ragdoll solver.

## Final gates

Both flavor build runs passed all 125 suites registered at their start, plus the compiled-image Opus and guest ABI gates. The additional package metadata suite passed all five cases separately and is now registered for future full runs. Final package/signature/archive checks passed; hashes and exact source are recorded in DELIVERY-STATUS. Owner device acceptance remains pending.

Do not replace pending device status with an unsupported success claim.

1. Rerun the final shield/material-effect, ownership and input-conflict regressions.
2. Rerun the entire quest suite after all final source and guide edits.
3. Both flavors built; identities/signatures verified and matching source/artifacts packaged with hashes.
4. Record actual results and unresolved device checks in DELIVERY-STATUS.
5. Deliver privately. No push, tag, publish, install or launch.
