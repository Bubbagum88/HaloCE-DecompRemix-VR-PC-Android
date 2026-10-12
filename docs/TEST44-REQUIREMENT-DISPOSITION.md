# Test44 requirement disposition

This pass addresses the ISO-source deletion confusion shown in the Quest
screenshot and the A10 tutorial calibration report. All previously accepted
behavior remains in the Test43 baseline and is carried forward unchanged.

| Request | Implementation | Verification and boundary |
| --- | --- | --- |
| Explain what happens to a picker-selected ISO/XISO | First-run onboarding, main launcher and **Game files & versions** state that supported maps are copied, the source image is neither retained nor deleted by the launcher, and Android Files is used to delete it. The manager distinguishes picker sources from inbox copies. | Launcher static assertions, Android/SDL Java compilation, package text inspection. Real Android provider/file-manager behavior still requires device testing. |
| Explain the disabled Existing game data row | First-run imports populate protected base data labeled **Existing game data**. The manager describes its active row as a status indicator and tells users to use **Import ISO / XISO** or **Scan inbox** to add managed sets; the base is not a deletable imported copy. | Source test preserves active/base deletion guards and checks the new copy. Device UI remains pending. |
| Make A10 calibration follow the visible aiming reticle | On A10 only, fresh finite hand-aim reticle rays drive relative-look actions and script point-gaze checks. Changing between reticle and head sources re-baselines, avoiding false movement. Head-aim mode uses the existing head path; during hand aim, invalid/stale ray data pauses progress rather than crediting head movement. | Production-function C harness tests map gating, reticle/head divergence, stale/invalid handling, source transitions, recenter/tracking guards and non-A10 behavior. Actual tutorial sequence requires headset acceptance. |
| Make physical hand grabs truly contact-driven | NPC/enemy and loose-object grabs require a tracked palm sphere to overlap the target's authored collision model when Grip is pressed. The co-op host repeats that collision check for remote hands. Climbing requires the hand contact volume to overlap a solid vertical BSP/scenery surface and a new Grip press. Reload part/pouch pickup and optional virtual vehicle-wheel handles use the same shared 2–8 cm contact radius. Magazine seating remains a separate held-object bounds-alignment action. Aim direction and target-search rays cannot acquire these actions; camera LOS is only an obstruction guard after contact. Default contact radius is 4 cm. | Deterministic production-code tests pass for local contact gates, co-op world contact/Grip/lease handling, co-op NPC host contact revalidation, parkour, reload and vehicle handles. Quest acceptance must still confirm no selection without contact and successful touch-then-Grip latch on device. |
| Preserve all unrelated behavior | Reticle calibration path rejects other maps, seated/mounted state, cinematic view, non-hand aiming, invalid direction and stale timing. Existing game-data protections remain. | Full regression runner, both edition builds, APK parity/signing/alignment and candidate package gate; see delivery status for results. |

## Acceptance boundary

No test on source code alone proves the tutorial sequence or Android storage UI
on-device. The Test44 package remains a private test candidate until the owner
validates it. Public v1.0.18 and the prior Test43 package are preserved.
