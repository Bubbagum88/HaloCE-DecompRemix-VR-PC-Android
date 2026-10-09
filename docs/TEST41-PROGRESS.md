# Test41 progress and handoff

## Completed in this candidate

- Rechecked the supplied logs against OpenCE's local/network session state;
  the saved campaign is local even though one separate log contains an earlier
  public multiplayer match and another has an invite that never completes.
- Added change-triggered interaction diagnostics for connection mode, active
  game/map/VR state, interaction options, reach, NPC rig slots and haptics.
- Applied the user-configured 12/18/25/30/40 cm reach to world objects, NPC
  contact and parkour wall contact; widened climbing probes to cover diagonal
  surfaces within the same bounded range.
- Increased the mod's physical NPC interaction-rig pool from four to eight and
  renamed the setting **NPC RIG SLOTS**, making clear that this does not change
  Halo's native corpse ragdoll cap.
- Unified controller vibration under the single **HAPTICS** strength. The
  separate load-haptics toggle was removed; zero disables the routed effects.
- Added **HOLSTER HAPTICS** as a separate on/off exception for weapon-hand
  holster entry/draw/stow buzzes. Holster actions and the free-hand reload
  pouches remain separate; reload and other effects still follow master
  HAPTICS.
- Corrected interaction option dependencies and made the packaging script
  include Test41's own delivery, progress, requirement and device-checklist
  documents.
- Built and verified the private flat/VR APK pair. Both builds passed all 87
  registered regression suites; package verification records exact hashes and
  the Test40-matching signing certificate in `TEST41-DELIVERY.md`.

## What remains for owner verification

Install Test41 over Test40 without clearing application data. Follow
`TEST41-DEVICE-CHECKLIST.md` one action at a time and retain the complete log.
The key acceptance results still needed are physical Grunt/Elite/Hunter grabs,
wall climb/jump, lift, rescue, manual reload/debris, contact feedback, and
whether each toggle changes the intended live behavior in a solo campaign.
Check that local-only features remain suppressed only after an actual network
join. Do not treat a pending invite as a joined multiplayer session.

The native corpse limit is not modified by NPC RIG SLOTS. Script-controlled or
unsafe actor rigs remain excluded. NPC rescue still has its eligibility and
fall-duration rules. Arbitrary rigs are not retargeted; only bounded
graph-validated local humanoid layouts are admitted. These constraints should
not be loosened without matching evidence and a focused test.

Do not publish this candidate or advance the accepted-state pointer until the
owner reports headset acceptance. Public v1.0.18 and Test40 remain preserved.
