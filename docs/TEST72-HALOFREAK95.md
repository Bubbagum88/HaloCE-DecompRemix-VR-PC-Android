# Test72: HaloFreak95's build, reviewed

Reviewed directly: their `halo.exe` (SHA-256 e4f45a93…, "Halo Divers mods by
John", built from an OpenCE tree under "Halo Ragdolls\build\OpenCE") and
`OpenCEMods.zip` (that exe, `dual_wield.bin`, `dual_body.bin`,
`gutted_elite.bin`, `installer.ps1`, a README). No source was included: their
settings, help texts and module names were read from the exe, and each
feature below was rebuilt here on this port's own systems. Their fast decals
were also published as source (jcompto95-tech/OpenCE PR #2, 1b9b09d4),
ported from that.

## Gained

| Theirs | Here | Builds | Default |
|---|---|---|---|
| `display.decals_on_gpu` (PR #2) | FAST DECALS: decals drawn from their own stream as the Xbox drew them; quad lists from one kept index buffer | all | on for PC; off on Android and Quest until measured |
| `game.blood_layers` | BLOOD LAYERS: a blood splat is not laid where that many unfaded ones already lie within its radius | all | 6 on Android and Quest; 0 (all) on PC |
| `display.ammo_counter_color` | RIFLE DISPLAY (Spartan Armor): the first-person assault rifle's counter, compass, icons and readout recoloured per transparent draw, as the visor is | all | stock |
| `game.shadow_objects_stop` | stencil shadows end at machines and scenery behind the caster too | all | on (stencil shadows themselves stay opt-in) |
| `display.holstered_weapons` | HOLSTERED GUNS: carried, unheld guns worn on the back (long guns) or right thigh (pistols, needler), drawn only, from each model's default pose at the wearer's spine and thigh nodes, with its lighting and camouflage | all | off |

## Already here (not duplicated)

- `input.touch_aim_assist`: AIM ASSIST (`input.mouse_aim_assist`) already
  covers swipe and gyro aim on Android; its help now says so.
- `display.others_shield_colors`, `display.others_visor_colors`: SHOW PLAYERS
  CUSTOM ARMOR (`display.others_custom_armor`) shows others' armor, lights,
  visor and shield as they chose, under one switch.
- `display.plasma_lights` (plasma bolts and needles lighting the level):
  Projectile Effects' projectile lights (`projectile_lights.c`) already do
  this.
- `game.shadows` "stencil": STENCIL SHADOWS (`display.stencil_shadows`).

## Not integrated, and why

- Dual wield (`game.dual_wield`, `dual_wield.bin`) and dual-wield bodies
  (`dual_body.bin`), gutted Elites (`gutted_elite.bin`): binary data of their
  own formats with no source or description, carrying Halo 2 animation data;
  offline only, and it changes the plasma rifle's damage for balance. VR has
  its own two-handed and hand-held weapon systems.
- The Jackal shield's light (part of `display.plasma_lights`): a light made
  for every shield each frame; small gain against the Quest's light budget.
- `display.ammo_counter_bloom`: needs a bloom pass this renderer does not
  have.
- `audio.loose_sounds`: a modders' tool that reads Halo PC `.sound` tag files
  from a tags folder.
- `audio.plasma_rifle_sounds`: plays their own WAV files, which the download
  does not include.
- `debug.gpu_flush_draws`: a workaround for Mesa on Intel graphics in their
  renderer; this port's renderer has no such report.
- `crash_reports.upload`: uploads crash reports to their server.

Tests: `tools/test_test72_hf95.py`, `tools/test_test31_transparency.py`
(the rifle display's draw wrapper).
