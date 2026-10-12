# Legacy campaign compatibility

Default campaign support is network 15-24. Optional legacy 12-14 support requires
explicit launcher consent and retains old-host allegiance limitations. Network 11
has no campaign co-op. Hosting stays network 24; CE maps require 23-24.

The owner's screenshot showed a network21 campaign lobby named Noodle. The
previous23 floor blocked it even when21 was selected. That floor was a conservative
policy, not evidence of a network21 campaign packet incompatibility. The current
receiver accepts the network21 campaign schemas. This change enables that join
path; reachability, content matching and actual gameplay still need testing with
that host.

## Source evidence

Primary history was inspected in the official OpenCE repository, through pinned
commit73dc01d09a21875f14c77b4430f20518d1f5ad09 (Build157). Exact commits and extracted
historical wire structures for every network12–24 are preserved in
`tools/fixtures/legacy-coop-layouts.json`.

- Network11 predates OpenCE campaign co-op. It cannot be made a co-op host by
  changing a client setting.
- Network12 introduced campaign co-op;13 expanded the actor pool;14 added device
  position states and unit open/close events. Old hosts cannot send later features
  they do not implement.
- [Network15's allegiance change](https://github.com/OpenCommunityEdition/OpenCE/commit/5ff4b6e)
  appends two four-word allegiance vectors to the presentation record. The old
  network12-14 record is 32 bytes shorter. The optional adapter accepts exactly
  that historical prefix only when the joined host is 12-14 and the user enabled
  `network.legacy_coop`. Camera/HUD/input update normally, but absent allegiance
  data is never fabricated or applied. Old hosts cannot send script-driven team
  changes: Marines or friendly reticles may behave incorrectly. Consent is OFF
  by default, with explicit launcher warnings. Prefer current hosts.
- [Network16's BSP change](https://github.com/OpenCommunityEdition/OpenCE/commit/087ca8a)
  uses a former padding byte in client input. Packet length and existing field
  offsets remain unchanged. Older hosts ignore that byte; they retain their older
  BSP synchronization behavior.
- Network17 uses two formerly zero presentation padding bytes for cluster+1.
  Older hosts' zero padding means no activating cluster. Existing offsets and
  presentation length are unchanged.
- Network15–24 campaign presentation, event, device-group, object-name,
  object-transform, object-look, skip-vote and device-state layouts match the
  current layouts after accounting for that explicitly documented padding reuse.
  Player input has the same offsets and length throughout12–24.
- The native co-op file from the app's network21 integration differs from current
  code only in the later valid-camera guard. No legacy decoder is needed for21.
  The guard remains intact.
- Network22/23 Custom Edition map identity and capacity changes are separate;
  campaign widening does not relax the CE-map floor.

## Implementation and validation

Both initial native admission and subsequent lobby settings validate the new
campaign minimum. The launcher uses the same15 campaign and23 CE boundaries for
Join eligibility, population totals and explanations. Direct invites still pass
through native admission. Retired app-specific CE01/CE02 campaign sessions remain
incompatible. Unknown versions and versions above24 remain refused. Local host
advertisements and package host metadata remain24.

`tools/test_legacy_coop_layouts.py` compiles pinned historical presentation structs
alongside the production struct and receiver, then passes legacy packets through
that actual receiver using AddressSanitizer and UndefinedBehaviorSanitizer. It
checks camera, HUD/input and allegiance fields, stale/non-client/invalid-time
rejection, input-layout identity, and the concrete12–14 record-size shortfall.
It also compares all listed campaign schemas against the current definitions.
Guest32-bit integer widths are retained in the host fixture.

The updated native admission suite exercises every target11–24 plus All
compatible, all relevant mode/version combinations, malformed/unknown/retired
hosts, CE guards, immutable startup selection and post-join mode changes. The
Java suite checks actual population calculations and settings persistence.
These suites, the browser suite and the Test27/29/34 regression suites pass.

These checks establish schema/admission behavior; they do not establish a full
campaign playthrough against every old binary. Legacy hosts retain their own
bugs and missing features (especially early BSP, scenery and death handling).
Current-network hosts remain the preferred co-op experience. Record host version,
map/data set, device, joining method and logs when testing historical hosts.
