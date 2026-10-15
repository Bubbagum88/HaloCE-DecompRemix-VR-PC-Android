# Credits and licenses

## Test31 integration

The OpenCE Build 145 menus, Server Setup, profile/gametype options, scoreboard,
network-22 changes and optional graphics settings are adapted from
[OpenCommunityEdition/OpenCE](https://github.com/OpenCommunityEdition/OpenCE),
principally MrBruh/cybersecurity and its contributors. Shadow resolution,
per-pixel lighting and I3DL2 room reverb build on Tyberious's contributions
(upstream #44/#46/#47/#48). FXAA follows Timothy Lottes's published approach;
desktop SMAA source/data retains its MIT license under `port/third_party/smaa`.
The XML parser is Expat; its license is retained with the source. Android's
local scancode-name table is adapted from SDL 3.4.16 under SDL's license.
Quest/Android input, VR-menu and rendering adaptations are project work.

This fork depends on substantial prior work. Credits distinguish code foundations, reference material and related projects; they do not imply endorsement or that all features of another project are included.

| Project / people | Contribution or relationship |
| --- | --- |
| Bungie and the original Halo team; Microsoft and the respective rights holders | Original Halo: Combat Evolved game, art, audio, story and technology. Game maps/data are supplied by the player, not licensed by this repository's source license. |
| [punpckhdq/halo](https://github.com/punpckhdq/halo), [bnunu/halo-1](https://github.com/bnunu/halo-1) and their contributors | Xbox Halo CE decompilation foundation. The inherited port identifies build 2342 (`cachebeta.exe`) as its decompilation target. |
| [bnunu/halo-ce-universal](https://github.com/bnunu/halo-ce-universal), [cybersecurity/halo-ce-universal](https://github.com/cybersecurity/halo-ce-universal) and contributors | Native Linux/Windows/Android port, guest/host architecture, renderer, networking, extraction/launcher and platform work inherited by this fork. |
| [astromaddie/HaloCE-VR](https://github.com/astromaddie/HaloCE-VR) / Madison | OpenXR VR foundation merged into the predecessor checkout as CC0: stereo rendering, tracked inputs, hand aiming, initial arm IK, scope, vehicles, room-scale, menus and related VR systems. |
| [moistman42069](https://github.com/moistman42069) and this fork's development/testing work | Quest adaptation and integration, body/finger/contact refinements, interaction/default changes, launcher/browser, campaign/avatar extensions, flat touch controls, logging, packaging and device feedback. See current-state for evidence and unfinished verification. |
| [ChupathingyCE](https://github.com/ChupathingyCE/chupathingyce) and the halo.milenko.org service maintainers | Compatible native-port directory and published invite/listing/announcement protocol used by the launcher. The service is independent of this fork. |
| [LivingFray/HaloCEVR](https://github.com/LivingFray/HaloCEVR) | Earlier original-PC VR conversion and room-scale design reference acknowledged by the inherited VR code. This Android project is a separate codebase/target; no exclusive or first-to-VR claim is made. |
| MrBruh; Aerocatia; Overpass font contributors | Selected OpenCE Build177 high-resolution HUD/reticle redraws by MrBruh, based on Aerocatia's reference photos; sniper 2x/10x labels use Overpass. Only the selected reticle and sniper-scope artwork is included in this candidate. |
| [rollingrock / FRIK](https://github.com/rollingrock/Fallout-4-VR-Body), [hai-vr / hvr-ik](https://github.com/hai-vr/hvr-ik), [Unity two-bone IK documentation](https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.2/manual/constraints/TwoBoneIKConstraint.html) | Body/IK reference research for bend continuity, bounded reach, head/body priorities and target/hint separation. These were studied as references; the test13 refinements were implemented for Halo's own rig, without importing their code or foreign game bindings. |
| Players and bug reporters | Headset recordings, logs and feedback that guided menu, body, grip, finger and multiplayer changes. Private recordings/logs and identifying information are not published. |

## Bundled software and assets

The root [LICENSE.md](LICENSE.md) is the inherited CC0 dedication. It does not replace dependency licenses or grant rights to Halo game data/trademarks. Existing copyright/license headers are retained.

- **SDL3**: platform, input/audio/activity support; zlib license. Shipped dependency version is 3.4.16. [Notice](docs/licenses/SDL3-LICENSE.txt).
- **Khronos OpenXR SDK/loader**: VR API/loader, version 1.1.63. [License](docs/licenses/OpenXR-LICENSE).
- **musl** 1.2.5: guest C runtime; [copyright/license](docs/licenses/musl-COPYRIGHT). The vendored math subset has its own [notes](port/third_party/musl-math/README.md).
- **KCP**, **miniupnpc**, **Mbed TLS**, **tomlc17**, **stb**: retained [third-party sources/notices](port/third_party). Consult each component's LICENSE/README and file headers.
- **extract-xiso**: original work by in, with additional project contributors. Required acknowledgement: **This product includes software developed by in &lt;in@fishtank.com&gt;.** [Modified BSD license](port/third_party/extract-xiso/LICENSE.TXT). Extraction code retains that notice.
- **zlib** and **libtiff**: inherited compression/image libraries; notices remain in [zlib](source/memory/zlib/README) and [libtiff headers](source/bitmaps/libtiff/tiff.h).
- **Overpass** by Red Hat/Delve Withrington, **Newtown** by Roger White, and the port's respaced **OpenCE** title font: [font provenance and license files](port/assets/fonts/README.md). The release bundle includes their notices.
- **Orbitron Regular** by [The Orbitron Project Authors](https://github.com/googlefonts/orbitron-vf): optional Halo-inspired display type for short Android launcher labels and buttons. It is not Halo's original font; it is bundled unmodified under the [SIL Open Font License 1.1](https://github.com/googlefonts/orbitron-vf/blob/master/OFL.txt), also retained at `port/android/app/src/main/assets/fonts/OFL-Orbitron.txt`.
- **LLVM/Clang, Android SDK/NDK, Gradle, CMake, Ninja and Python** provide the build toolchain; they are not all bundled with the APKs.

The public repository begins with a privacy-clean current snapshot. Earlier private author metadata is not exposed. Public upstream links and retained file/license notices preserve attribution; this snapshot is not a claim that this fork wrote the inherited code.

## Test15 additions

Selected v10/v11 networking and gameplay changes are adapted from bnunu/cybersecurity halo-ce-universal contributors; pinned commits and integration boundaries are in [the upstream audit](docs/TEST15-UPSTREAM.md). Ordered static GPU uploads follow Andiweli's [HaloCE-Android-AAOS fix](https://github.com/Andiweli/HaloCE-Android-AAOS/commit/a88f25763b8a51335554ef02e613127ee92677d4). SnowyMouse's [Halo cache format documentation](https://gist.github.com/SnowyMouse/39168bddd597549038a35d78aee39513) (CC BY 3.0) informed header reporting; the recognition code is adapted for this launcher. Activision's official mobile control guides informed HUD usability only; no shooter code/art was imported. Launcher backgrounds are procedural original drawings, with no extracted Halo artwork bundled.

Test15 Android controller support retains SDL 3.4.16 mappings and Android input APIs. Local SDL changes are recorded under `port/android/patches`, including generic Android digital-only L2/R2 mapping and the existing clipboard-service guard. SDL copyright/license remains in the bundled third-party notices. Controller settings/navigation/visibility are project code.

## Test19 additions

Signed OpenCE lobby discovery and Ed25519/X25519 identity binding are adapted
from cybersecurity/halo-ce-universal build 84, principally commit
`c04765d7f49f49bda706a258826134ef41c566ca`. The stock Xbox widget integration is
project code. [Monocypher](https://monocypher.org/) by Loup Vaillant and its
contributors supplies the cryptographic primitives; complete licenses accompany
`port/third_party/monocypher` and the bundled notices. XboxDev/extract-xiso's
format handling and deep-tree warning informed the importer correction. Khronos
OpenGL ES and OpenXR specifications informed renderer-state and reticle-space
review. These references establish API/format behavior, not device acceptance.

## Test66 additions

- **Jolt Physics 5.6.0**, by Jorrit Rouwe and contributors, powers OpenCE's dynamic death ragdolls. The OpenCE ragdoll integration (PR #317) is adapted through a Quest/Android guest-to-host bridge. The complete [MIT notice](port/third_party/JoltPhysics/LICENSE) is included in the APK field guide and distribution notices.
- **Lucide Icons and Contributors** supply the speaker icons adapted from OpenCE. The complete [icon license](port/assets/icons/lucide/LICENSE), including inherited Feather notices, is included in the APK field guide and distribution notices.
- **The Altheros Experience**, by Altheros, is an optional user-supplied custom campaign. The launcher provides import/install/restore support; its maps and other game assets are not bundled.

## Test67 additions

- **The OpenCE fork by jcompto95-tech** (HALOFREAK95), CC0 like OpenCE: third-person camera, Extra Effects screen, Big Multiplayer Guns, animated overshield, corpse and decal limits, stencil shadows, projectile effects with dynamic and vehicle blood and projectile lights, weapons physics on Jolt, the Armor menu (armor, lights, visor, flashlight and shield colors, shared), text chat and votes to ban. Adapted to this port's renderer, VR and Android bridge; [integration record](docs/TEST67-EVIDENCE.md).
- **OpenCE testing 52e33a39** (map sharing and Custom Edition loading hardened) and its hardened **stb_vorbis** (public domain / MIT, under the stb notice).
- **GulchCE** by chestahh, CC0: the Halo 1 MCC map loader, adapted solo only.
- **bcdec** by Sergii Kudlai (MIT or Unlicense): the MCC maps' BCn texture decoder; [license](port/third_party/bcdec/LICENSE).
- **JavaSteam** and **javasteam-depotdownloader** by Long Tran and contributors (MIT): the launcher's Steam Workshop sign-in and downloads.
- The Steam Workshop's runtime libraries, as Gradle resolves them: **OkHttp** and **Okio** (Square, Apache 2.0), **Kotlin standard library**, **kotlinx.coroutines**, **kotlinx.serialization** and **kotlinx-io** (JetBrains, Apache 2.0), **Ktor** (JetBrains, Apache 2.0), **JetBrains annotations** (Apache 2.0), **AndroidX annotation, startup and tracing** (Google, Apache 2.0), **Apache Commons Lang** (Apache 2.0), **Protocol Buffers for Java** (Google, BSD-3-Clause), **Bouncy Castle** (MIT), **SLF4J API** (QOS.ch, MIT), **XZ for Java** (0BSD), **zstd-jni** (Luben Karavelov, BSD-2-Clause) with **Zstandard** (Meta, BSD). Their complete notices are in THIRD-PARTY-NOTICES.txt and the APK field guide.

## Test71 additions

- **libarchive-android** 1.1.7 by Hai Zhang (Apache 2.0), around **libarchive** 3.8 by Tim Kientzle and contributors (BSD-2-Clause, with the parts its COPYING lists): the launcher unpacks a mod's archive on the headset (The Altheros Experience is a RAR5), downloaded or picked. Built into it, as its native library ships: **zlib** (Jean-loup Gailly and Mark Adler, zlib license), **bzip2** 1.0.8 (Julian Seward, BSD-style), **XZ Utils' liblzma** (Lasse Collin and contributors, 0BSD), **LZ4** (Yann Collet, BSD-2-Clause), **Zstandard** (Meta, BSD) and **Mbed TLS** (Arm and contributors, Apache 2.0). Their complete notices are in THIRD-PARTY-NOTICES.txt and the APK field guide.
- **Project Lumoria** (TM Mapping Team) and **The Altheros Experience** (Altheros) are downloaded by the launcher from where their authors published them (halomaps.org; moddb.com), as SPV1 is; nothing of theirs is bundled.
