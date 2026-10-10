# Test47 progress record

Candidate **1.0.28-test47 / Android code58** continues on
`test39-interaction-completion`. Preserve the private Test46/Test45 candidates
and public v1.0.18. No GitHub release is authorized. Do not install or launch
the game. PC/Steam Frame remains deferred.

## Owner's reports addressed

1. **Visible hand/arm stretching:** comparison with the public v1.0.18 tag
   confirms that release also scaled both authored arm lengths (up to 18% longer
   and down to 65%) when the tracked wrist exceeded its reach. Test47 removes
   that deformation workaround and clamps the wrist target to the reachable
   shoulder/bone interval. The existing body/arms modes and leg motion remain;
   headset fit at the reach limits still needs owner acceptance.
2. **Manual reload does nothing:** Test46 logs confirmed manual reload was
   enabled and the supported rifle model's authored magazine/chamber bounds
   existed, but did not contain a user-action attempt. The current code sampled
   the engine reload bit while Grip came from the VR render-frame path. Test47
   reads the remapped VR USE/RELOAD pad action directly and merges it with the
   native bit for a rising edge, while preserving actual palm contact, fresh
   Grip/Trigger, hand ownership and native ammo completion. Change-only logs
   expose the exact input/contact/ownership state during headset retest. The
   right-stick click remains melee.
3. **Local New Game multiplayer map spawns outside the map:** the public log
   confirms selection/loading of a multiplayer map but does not record a spawn
   decision. Source inspection found that the no-engine player-spawn path could
   reattach `dead_units[local_player]` from campaign continuation. Test47 clears
   and bypasses that stale slot for a local multiplayer free-roam map, selects
   a validated in-BSP start and multiplayer biped, and records placement and
   BSP leaf. Network sessions and campaign scenarios are excluded.
4. **Ragdoll retention limit:** inspection showed the native 50/30 active-
   garbage thresholds are shared across corpses and other garbage, rather than
   a true fixed ragdoll count. Test47 raises them to 75/45 by default in solo VR
   campaign, offers 100/60 or STOCK, and leaves every multiplayer mode on the
   native thresholds. Memory/object pressure can still collect earlier.

## Focused verification

The following have passed in WSL with Clang and sanitizers:

- `tools/test_manual_reload.py`: reload input-edge merge, duplicate-edge
  prevention, contact-gated ejection, phase transitions, cancellation and
  exact native ammunition conservation.
- `tools/test_solo_multiplayer_spawn.py`: local-map classification, stale-slot
  bypass, native/fallback start selection, CTF/odd-ball/race/teleporter
  candidate priorities, and exclusion of campaign/network paths.
- `tools/test_vr_arm_ik_reach.py`: production reach bounds and clamp, with
  authored lengths retained under ASan/UBSan.
- `tools/test_test46_candidate.py` and `tools/test_vr_pending_release.py`:
  cumulative candidate/source guards and failed weapon-release recovery.

The full regression runner, both clean flavor builds, signing/asset checks and
the final candidate package remain required. Quest and Android device
acceptance remain pending. Keep the delivery evidence in
`TEST47-DELIVERY-STATUS.md` and execute `TEST47-DEVICE-CHECKLIST.md` after the
owner installs the APKs.

## Carried-forward scope

See `TEST47-REQUIREMENT-DISPOSITION.md` and
`VR-INTERACTION-REQUIREMENTS.md` for the status of all prior work: contact-driven
hands, props, NPCs/allies and ragdolls; manual reload, parkour/climbing,
holsters, haptics, persistent visual magazines, bounded vehicle lifting, NPC
recovery, voice chat; OpenCE menus/network/co-op; launcher revisions and
network/population selection; Android touch/controller support; Safe Geometry,
body IK, scopes, calibration, vehicles and saves. These features stay in the
candidate, with their device and protocol boundaries stated per item.
