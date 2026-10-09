# Test43 requirement disposition

This record covers the user's additional launcher request after packaging
Test42: delete previously imported XISOs/game-data sets and manually choose
among multiple imported revisions/images. The source and package retain every
documented Test42 feature; see `TEST42-REQUIREMENT-DISPOSITION.md` for the
cumulative post-v1.0.18 VR and Android ledger.

| Request | Implementation | Verification and boundary |
| --- | --- | --- |
| Make revision/set selection easy to find | Main launcher now has a current-set button beside Play; it displays the selected label and distinct-set count and opens the full manager. | Launcher Java API compile and static route test; actual screen focus/tap behavior remains owner device testing. |
| Select among imported revisions/images | Each profile row clearly marks the current set and offers **Use this set**; selection atomically updates the active marker read by the next Java/native game launch. | Host fixture checks Java/native root agreement, including switch and restoration. User labels remain labels; revision is not inferred from filename. |
| Delete imported game data | A confirmation removes only an inactive complete managed profile under the app's game-versions directory. Active selection, existing/base data, other profiles, and original source files are protected. | Fixture covers active-set rejection, invalid marker fail-closed behavior, traversal rejection, deletion of only the selected inactive profile, and preservation of base files and another profile. |
| Delete copied XISO/ISO after import | Manager lists direct ISO/XISO files in the app-managed import inbox and confirms deletion of only that inbox file. | Fixture verifies deletion and rejects traversal. Android picker source URIs and external images are not retained, so those originals are not deleted by the launcher. |
| Do not pretend identical revisions are distinct | Exact same-map fingerprints continue to deduplicate. The verified USA Original/Rev 1/Rev 2 map data is byte-identical, so those images do not yield separate runnable map profiles. | Existing XISO evidence and fingerprint tests retained. Different fingerprints remain independently selectable. |

## Safety and acceptance

The selected profile is deliberately not deletable; the owner must select a
different complete set first. Base/existing data has no delete action. A
malformed active marker prevents deletion until a valid set is selected. The
recursive deletion routine is confined to the canonical, direct child profile
directory and does not follow symlinks. The inbox image deletion accepts only a
single ISO/XISO leaf directly under the canonical inbox folder.

Automated validation is not proof of Android provider behavior or headset UX.
The owner should verify profile switching and deletion on Android and Quest,
including saves in two profiles, the main-screen selector, and an inbox image
deletion. No install, game launch or publication is authorized in this pass.
