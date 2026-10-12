# Test47 OpenCE Build177 integration review

Checked against the official [OpenCE Build177 release](https://github.com/OpenCommunityEdition/OpenCE/releases/tag/build-177), commit `9da2a45ffa364b720ae9faab6a1dee876926fe42`, dated 2026-10-10. Build177 is the latest upstream release checked for this candidate.

The runtime is **based on OpenCE Build157 / network24**. This candidate selectively carries forward compatible fixes and assets; it is not a Build177 engine rebase and does not change network protocol identity. Do not describe it as full Build177 parity.

## Selected and verified changes

- **Build169 (`5ed36d1`) — Custom Edition tag block bounds.** CE maps can return safe empty tag data for references outside a block rather than asserting. The strict checks remain for the ordinary Xbox cache path. Source guards cover both the CE exception and the bounded fallback.
- **Build170 (`7124534`) — resource and Android lifecycle cleanup.** Selected engine allocation/release fixes are applied. Android gamepad handles now close through SDL; callback-backed audio streams signal and release their worker state on destruction; host-owned threads detach their guest pthread state before exit. VR/menu-specific implementations remain intact.
- **Build173 (`5e8ab02`) — large co-op respawn placement.** At five or more players the native campaign respawn logic selects a safe grounded player in the largest nearby group; small games retain the normal host-oriented path. This changes no player limit or network message.
- **Build175 (`bb5471b`) — older-kernel fixed mapping behavior.** The port already contained the safe check added in Test26: if an old kernel treats `MAP_FIXED_NOREPLACE` as a hint and returns another address, that mapping is unmapped and the attempt is treated as occupied. This behavior is retained and covered by the integration guard.
- **Build176 (`c9e4f13`) — ART overlap fallback.** When pagemap is denied, the Android host checks residency with `mincore` and checks swap for the exact ART mapping slice via `smaps`. It unmaps only a confirmed empty slice. A busy or unknown range is left mapped, with diagnostic logging. The regression harness forces pagemap denial and covers empty, resident and unknown outcomes under ASan/UBSan. This container does not implement Linux `mincore`, so the test uses a deterministic mincore shim; Quest-device runtime validation of this fallback remains pending.
- **Build177 (`9da2a45`) — weapon reticle redraws.** Updated high-resolution reticle and sniper-scope assets use the PC HUD sheet matches. The existing pixel-CRC check gates replacement to the exact expected Xbox bitmap, leaving other map revisions' art untouched. Redraw attribution is in `CREDITS.md`.

## Reviewed but not ported wholesale

- **Build174 (`775015e`) — high-resolution controller-button artwork and UI rendering.** The upstream patch was checked with `git apply --check`; it conflicts with this port's customized HUD renderer, texture path, embedded-asset tooling and menu code. It is a visual/UI change and does not repair networking or the reported interactions. Replacing those paths wholesale would risk the already customized VR and Android menus, so this candidate does not include it. This is an explicit scope boundary, not a claim that the upstream feature is present.
- **Build171 (`b5a4870`)** only reformats an existing comment and has no runtime behavior to port.
- No upstream network/protocol version change is included: network24 remains unchanged. Build177's release is not evidence that every OpenCE server, game image or co-op combination has been device-tested.

## Checks

`tools/test_opence_177_integration.py` guards the selected CE, respawn, lifecycle, map reservation and HUD asset paths. `tools/test_android_memory_reclaim.py` exercises the pagemap-denied branch with deterministic residency results. Both are part of `tools/run-quest-checks.py`. The two APK builds and package gate remain required; source tests do not replace Quest or Android runtime testing.
