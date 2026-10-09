# Test43 device acceptance checklist

Run on Android and Quest after installing over the prior app, preserving app
data. Do not uninstall or clear storage.

## Main launcher and selection

- [ ] Main screen shows the current game-data label and set count near **Play**.
- [ ] Tapping it opens **Game files & versions**; the Settings entry reaches the
      same manager.
- [ ] With two distinct imported map sets, the currently selected one is marked
      and the other can be selected.
- [ ] Return to the launcher: the displayed selected label updates. Launch the
      game and confirm it uses that map set; switch back and verify the first
      set remains available.
- [ ] Distinct saves and config remain attached to their data sets.
- [ ] Byte-identical imports show one deduplicated set; no unsupported
      Original/Rev 1/Rev 2 detection is shown.

## Deletion and safety

- [ ] The active imported set's Delete control is disabled. Select another set;
      delete the former set and confirm its maps/config/local saves disappear.
- [ ] Existing/base data cannot be deleted. Other profiles and their saves stay
      intact.
- [ ] Canceling the confirmation changes no files.
- [ ] An ISO/XISO inside `game-versions/inbox` appears in the inbox section and
      can be deleted after confirmation; a canceled action preserves it.
- [ ] A source image selected from Downloads/file picker remains in Downloads.
- [ ] Import a new set after deletion, then verify selection, map discovery,
      server join prompting and existing launch flow still work.

## Regression smoke checks

- [ ] Game starts in flat Android with touch controls and gamepad available.
- [ ] Quest still starts immersive with Safe Geometry and prior VR menu/settings.
- [ ] Save/profile/network configuration survives app update and set switching.
- [ ] Logs contain the active game-data root when a game starts.
