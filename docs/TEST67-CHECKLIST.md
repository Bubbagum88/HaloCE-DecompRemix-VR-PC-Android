# Test67 precision polish checklist

Private successor to Test66, planned 1.0.34-test67 / code79. Baseline c74e4a59
(runtime 0b5c7e62). No publish, push, install or game launch; local commits only.
No voice/codec change; network 28 unchanged (the owner later allowed the fork's
community extras on new message kinds 87-92, which stock peers ignore). Saved
settings preserved.

## Owner evidence and acceptance

The owner confirms smoother Test66, good immersive Warthog/Ghost/tank behavior,
excellent Sniper magazine presentation, improved ragdolls and parkour. Other
vehicles and full regression coverage are not device-confirmed. Preserve these
paths. Evidence: 2026-10-13 22:25:19 and 22:31:54 logs, 22:32:39 video,
request attachment e8b05ad6-8bcc-46f4-aaa1-54dc2e3d5a80. Both sessions exit0.

## Work (implementation reviewed; device acceptance remains separate)

- [x] Preserve Sniper authored magazine grip exactly.
- [x] AR hand, thumb/fingers, magazine orientation/offset and insertion profile.
- [x] Audit all seven reload profiles: magazine/extraction/insertion/axis,
  charge/slide, lock, haptics. Preserve ammo, storage, debris, well assist.
- [x] Sprint 1-3x in menu/runtime/math, both Arm Run and Button Sprint; default1.5.
- [x] Combat defaults informed by owner reach3/lunge8; saved values retained.
- [x] Stable per-grab body/skeleton attachment and fingers, both hands/heavies.
- [x] One deliberate punch per strike; no duplicate lunge damage.
- [x] Melee-only durability and difficulty, without scaling bullets/global health.
- [x] Distinct block/parry timing, sound, haptic, visual response and counter opening.
- [x] Multi-enemy intent switching, no permanent target lock; enemy hierarchy.
- [x] Appropriate shove/stun/knockdown/ragdoll, NPC recovery <=1s.
- [x] Light parkour contact/curves/seams review; no rewrite absent evidence.
- [x] Audit existing local SPV1/Altheros and required resources/provenance.
- [x] Bundle our permitted support/setup files, automate optional preparation,
  explicit included/required/missing/source labels and validation; no Halo assets.
- [x] Preserve vehicles, handedness, grenades, body/IK, scopes/reticles, holsters,
  inputs, haptics, multiplayer/co-op, OpenCE and Android/performance.
- [x] Hide weapon reticle with empty holstered hands; keep vehicle aiming and fist markers.
- [x] Review the supplied Arkham challenge reference: sampled entire timeline,
  focused exchange detail; original Halo-themed cues and native sounds only.
- [x] Independent per-enemy reaction/warning memory, intended-target-only carried
  strikes, vertical arrival check, occupied-hand defense isolation.
- [x] COMBAT MOVES toggle: species-specific procedural attack overlays, physical
  duck/sidestep, exact held-arm control and native-jump/downward-hit pummel openings.
- [x] Preserve NPC/Jolt palette ownership, bone lengths and foot placement;
  unsupported rigs keep native poses. No forced mount/teleport or persistent injury.
- [x] DEFLECT SHOTS toggle, soft auto-enable with fists; actual moving projectile
  contact, grenade fuse preservation, damage attribution and online authority.
- [x] Latest owner addition: gun-carrying hands can actively parry melee/shots.
  Stationary aiming/firing is not a shield; reload/support-hand ownership preserved.
- [x] Altheros new blue-screen log: exact 512 MiB resource partition overflow
  fixed, ten owner maps checked offline, converted-cache identity safeguarded.
- [x] Test68 merged in: GulchCE Halo 1 MCC maps, solo only (online MCC deferred;
  MCC's network 42 not supported), launcher Steam Workshop (JavaSteam 1.8.0,
  token only, no stored password), installed-map manager, folder and MCC
  resource-map imports. GulchCE's MCC tests adapted: 890 pass (140 of them
  32-bit programs run under qemu-i386); 152 Windows-only harness cases and 1
  opt-in fixture not run; 2 online files excluded, 3 cases deselected.
- [x] OpenCE testing 52e33a39 hardening (map sharing, Custom Edition geometry
  and Ogg limits, stb_vorbis); OpenCE main is still build 201.
- [x] Every jcompto95-tech (HALOFREAK95) fork branch reviewed and taken, adapted
  to this renderer, VR and the Android bridge: third person (flat only, never
  VR), Extra Effects screen (shield glow moved), Big Multiplayer Guns, animated
  overshield, corpse/decal limits, stencil shadows (one face a draw on GLES; no
  own-body shadow in VR), projectile effects v2 with dynamic/vehicle blood and
  projectile lights, weapons physics on Jolt (held items never Jolt's), the
  Armor menu (armor, lights, visor, flashlight, shield colors), text chat,
  vote-ban. Every visual extra off/classic by default.
- [x] Network extras (owner decision): armor sync, chat, vote details on new kinds
  87-92 behind network.community_extras (default on); launcher Server Browser
  switch; network 28, votes 78/79 and voice unchanged.
- [x] Not taken, superseded: player-colors (network 29 bump; armor sync replaces
  it), separate visor-color (inside armor menu), dynamic-blood v1/v2 and
  projectile-effects v1 (earlier versions of v2), v1 blood tuning console;
  light bloom stays the fork's desktop-only no-op; Decals row desktop-only as
  the fork intends.
- [x] VR BUTTONS: ALL TO DEFAULT first row (plus RESET BUTTONS last), DONE for 2 s.
- [x] Licenses: CREDITS and THIRD-PARTY-NOTICES complete texts for new libraries.
- [x] Targeted tests, full suite, both builds, package identity/signature/hash checks.
- [x] Docs, device checklist, exact delivery record, memory, local commits.

## Initial concrete findings

- Lunge landed then same-hand new lunge in the same tick: 22:33:08.881;
  repeated at 22:25:53.196. The acquisition guard only lasts during travel.
- Sprint menu, vr_frame runtime and vr_sprint_scale_for_effort cap at1.5.
- Sniper authored mag frame25 at9cm accepted. AR sampled frame52 at9cm.
- Reload sampling currently recognizes only frame magazine and ophandle/slide,
  though supported profiles include shells/tubes/canister/crystals. Audit needed.
- Altheros local ReadMe labels 2019 content private beta; no redistribution
  license supplied. Existing owner files remain local, cannot treat as bundle grant.

## Design reference

Camouflaj developer talk: https://gdcvault.com/play/1035681/ (freeflow combat
translation to VR). Used as conceptual reference only; no proprietary code/assets.

Automated results must not be described as headset verification.

Implementation and evidence links: TEST67-EVIDENCE.md; production/regression tests test_test67, test_test67_campaigns, test_test62_extra and existing full suite. Checked implementation items do not claim headset acceptance.
