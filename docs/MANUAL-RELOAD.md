# Optional physical reloads

Implementation status: source implemented and host/guest checks in progress;
headset acceptance is pending. This feature is off by default. Classic reload
and the existing native action-animation handoff remain available.

## Player operation

Enable **Manual reload** in VR Controls. In a local game, use the free hand's
grip to take the magazine from a supported weapon, pull it clear, and release.
Grip near the free-hand-side hip or shoulder to retrieve its replacement.
Shoulder and hip retrieval each have an independent toggle (both default on).
Pouches automatically follow the free-hand side: left with a right-hand gun,
right with a left-hand gun. Bring the replacement
to the weapon's socket with its orientation aligned (a short haptic pulse), then
release grip. It seats smoothly over 0.10 seconds before the finishing mechanism
becomes available. Finish with the weapon's mechanism below.
Grip must be pressed anew at each grab; holding it while passing a socket does
not automatically acquire the object.

| Weapon | Physical part | Finish |
|---|---|---|
| Assault rifle | Magazine | Grip operating handle, pull backward relative to gun, release |
| Pistol | Magazine | Grip slide, pull backward relative to gun, release |
| Sniper rifle | Magazine and attached bullet mesh | Grip operating handle, pull backward relative to gun, release |
| Shotgun | One shell from hip/shoulder; no fictitious removable magazine | Insert shell, then grip/pull/release pump; one native round per cycle |
| SPNKR | Tube assembly | After insertion, grip and release the push-bar latch at its authored node |
| Flamethrower | Fuel canister | After insertion, grip and release the cover at its authored node |
| Needler | Crystal bundle retrieved from hip/shoulder | Align the authored needle cluster and insert; native replenishment commits after seating, with no fictitious bolt |
| Plasma pistol/rifle | Native battery/heat behavior retained | Stock tags have zero reload capacity/count; no invented battery refill |
| Gravity/fuel-rod/custom weapons | Native behavior retained | No validated player first-person reload profile in these supplied maps |

The shotgun sequence currently pumps after each inserted shell. The original
button reload remains the quicker native multi-shell sequence. The SPNKR and
flamethrower use physical latch grip/release, without inventing a moving bolt.
The flamethrower's native reload policy discards remaining canister fuel; the
physical path preserves that policy.
The Needler bundle reuses its 16 authored visible needles as one reload object;
these are a visual cluster, not 16 individual ammunition units. The actual
20-round capacity and reserve transfer stay under the native magazine rules.

Press the normal reload button to cancel a physical sequence and use classic
reload. Weapon changes, dropping/putting away the weapon, death, vehicle entry,
cinematics, inhibited input, lost tracking, map transitions, or disabling the
option cancel transient state. Ammunition is unchanged before final commit.
Online play uses the existing native reload path: this implementation does not
send unrecognized physical-reload packets or alter host ammo authority.

## Evidence and implementation

The supplied USA Original/Rev1/Rev2 map sets are byte-identical; see
[the image matrix](USA-IMAGE-COMPARISON.md). The audit read model/tag structures
through the existing cache parser and recovered layouts in `model_definitions.h`
and `models.c`, and read compressed vertex influences using the renderer's
node-index/3 convention. AR magazine/handle have 129/82 rigid vertices; pistol
magazine/slide have 144/476; sniper magazine/handle have 185/80, plus the
magazine's 152-vertex bullet child. Shotgun shell/pump have 112/351 vertices;
its `frame magazine` is a 68-vertex loading gate, not the shell. SPNKR tubes and
push bar have 1680/256; flamethrower canister/cover have 48/52. The Needler has
16 independent 46-vertex needles, including the authored `frame eneedle13` name.

The actual existing first-person mesh nodes move with the tracked free hand.
No copyrighted game geometry is embedded or redistributed. Magazine descendants
move and hide together. The shotgun insertion anchor uses the authored bind
pose so an idle animation's hidden shell does not determine the socket.
Charging travel is measured relative to the gun, so moving both hands together
does not cock it. Pose age, bounds, finite matrices and hierarchy traversal are
guarded. All state is transient; saves retain the engine's own ammo state.

`weapons.c` calls its original ammo-transfer and chamber-completion functions
only after a completed sequence. The original finite reserve/infinite ammo,
capacity, per-shell load count and discarded-fuel policies are preserved.
Automatic follow-on reload is suppressed during that one commit, including the
infinite-ammo/low-reserve edge. The normal reload button bypasses this path.

## Requirement disposition

M23 component contact: gameplay-time bounded scans of the renderer's registered
rigid vertices build local bounds for the actual magazine/needle cluster and
charging part. Those oriented bounds follow the same transformed component as
the mesh. Palm and unclaimed finger queries include them; the hand holding a
reload part solves finger contact against the part only, so world geometry
cannot force that grip open. Other interaction owners retain their grip poses.
Detached tracking uses the predicted render pose rather than a 30 Hz visual
sample. Bounds are an envelope, not triangle-perfect mesh collision; stereo
contact comfort and individual weapon ergonomics still need headset checks.
Magazine/handle grip acquisition also guides the displayed hand onto the
component bounds over 0.08 seconds. This closes the interaction-radius gap
without snapping the magazine away from its captured pose.

### Shared contact and compliance

World-object and NPC grasps now run finger volume queries against only the
owned object's native collision model. They no longer bypass finger contact
entirely, and unrelated walls cannot pry those grip poses open. Missing native
colliders retain the deliberate grip pose instead of using unrelated geometry.

**CONTACT LIMIT** bounds controller/visible-hand separation (default 18 cm,
8–40 cm selectable). When collision or a constrained grip leaves the hand
beyond that limit, the corresponding arm/hand geometry shrinks out coherently
over 0.08 seconds toward its shoulder, avoiding a severed visible wrist. It
returns after separation falls below 75% of the limit. Gun geometry is excluded.
It never teleports through a wall to chase the controller. This affects local
arm/hand presentation only; body/legs, collision, ammo and network transforms are
not moved. A lifecycle reset while over the limit starts hidden, avoiding a
distant-hand flash. Headset verification should check this visual transition
against walls and during resisted NPC/prop grasps.

`test_reload_contact.py` executes the production registered-vertex bound scan,
transformed component trace and guided hand target. `test_hand_compliance.py`
executes the actual finger query routing and cap/recovery state under sanitizers.

| Requirement | Source disposition | Remaining validation |
|---|---|---|
| M1 optional manual reload | Off-by-default local-game setting, seven authored profiles | Headset operation |
| M2 retrieval | Fresh grip at independently enabled hip/shoulder, automatically on the free-hand side | Physical comfort/reach |
| M3 magazine models | Existing authored mesh and rigid node subtrees | Stereo alignment |
| M4 removal | Grip, relative separation, release; shotgun is loose-shell exception | Reach/tolerance tuning |
| M5 insertion | Socket distance and forward/up alignment, haptic feedback, release and 0.10-second seating blend | Natural fit on device |
| M6 ammo synchronization | One native commit; online native fallback | Real save/checkpoint and multiplayer regression |
| M7 chambering | Gun-relative handle/slide/pump; authored latch grip for assemblies | Device movement and ergonomics |
| M8 per-weapon definitions | Seven exact first-person tags; battery/non-player native behaviors above | Additional custom-tag definitions |
| M9 two-hand interaction | Exclusive grip ownership clears support lock while manipulating | Both handednesses in headset |
| M10 cancellation | Lifecycle, explicit button, stale/invalid pose and tracking checks | Interrupt every stage on device |
| M11 haptics | Bounded transition pulses using existing haptic scaling | User preference/device result |

`tools/test_manual_reload.py` exercises the physical sequence, grip-edge rules,
missed sockets, incomplete handle pulls, cancellation from every phase,
exactly-once completion, relative movement, shell retrieval, and the **actual
native ammo function** over capacities/reserves/tactical/empty/infinite-ammo and
discard-on-reload cases under AddressSanitizer/UndefinedBehaviorSanitizer.
Compilation is checked with the Android guest ABI, not only host stubs.

The hardware checklist is: each supported weapon empty and tactical; left and
right weapon hands; grip already held on switch; two-hand support release;
misaligned insertion; missed retrieval; release/drop at every stage; pause,
death, vehicle, cinematic and level transition; save/load mid-sequence; classic
button fallback; option disabled; stock online reload; no unexpected ammo gain;
stable frame timing. Passing host tests is not a headset acceptance claim.
