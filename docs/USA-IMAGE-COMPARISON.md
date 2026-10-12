# Supplied USA image comparison (2026-10-08)

## Result

The three owner-supplied images labelled USA Original, Rev 1 and Rev 2 contain **byte-identical sets of 24 map files**: 10 campaign maps, 13 multiplayer maps, and the menu map. Every map is Xbox cache format 5, NTSC build `01.10.12.2276`. These labels describe the supplied files; the audit does not authenticate disc provenance from filenames.

The complete images differ in size and non-map payloads. No revision-specific map, scope, turret or network behavior change is justified by these samples. The launcher continues to recommend the original XISO as a conservative compatibility baseline; the exact tested Rev 1 and Rev 2 sets are also accepted and contain identical map data. That recommendation does not indicate a known incompatibility in either tested revision.

| Supplied label | Image bytes | Image SHA-256 | Files |
|---|---:|---|---:|
| (USA) (Rev 1) | 3546677248 | `8140d5b914e3f12583065635f89d82ebc086322d704f25a20a50018b53278e0e` | 114 |
| (USA) (Rev 2) | 3625713664 | `43ec0813edadd592b7b489a930f108d289db9313ac337611110ffca8be0a7258` | 50 |
| (USA) | 3728867328 | `bbed30485a34fb971687648f31a8b50467c92d7ef296e3f97bad51372db1b012` | 1166 |

The extra files in the supplied images are confined to `xdemos`: Original has
1,136 entries there, Rev 1 has 84, and Rev 2 has 20. The other 30 paths and
file sizes match across all three images, including `default.xbe` and the five
root Bink files. These non-map files were inventoried by path and size, but
their contents were not hashed. All three supplied XISOs use partition offset
0; other container/partition layouts were not tested.

## Production validation

The actual `XisoExtractor`, `MapInfo`, and `GameDataLibrary` classes were compiled with JDK17 and run against all three complete images. Each image extracted successfully, all 24 headers passed the production recognizer, and finishing each import returned the same managed profile rather than creating duplicate data sets. The production fingerprint is:

`3c44b1947d1c1ce53557f39e7a0398071fd25e48401d94eca6de040b5047d587`

The independent repository XDVDFS parser also traversed every directory and verified every file extent stayed inside the image. All three partitions begin at byte 0. Per-map SHA-256 comparison covered complete files, not just their headers. No game assets or image files are included in this repository.

## Shared map identities

| Map | Bytes | SHA-256 |
|---|---:|---|
| maps/a10.map | 173903872 | `f7461e5b6eaf0314c4f03a1c6e43752b06ae3e4782b70b240a8c15e5f634b3ce` |
| maps/a30.map | 152610816 | `4875fa105e6c517589a796cfdcc7fcaa07e98df13d14e601bfc9eb1eab7e30b5` |
| maps/a50.map | 176224256 | `f8ec33c0130191cf944ef7b4a3f210bb680cfd1341cdf3a6ef3447391049abe7` |
| maps/b30.map | 162877440 | `a6e2ae628f96b666922d6429541068c3e117e8aa5031d00d187b3c853630be0f` |
| maps/b40.map | 186873856 | `0a7b26d6d828e7b773d36d9d5c798b9bf4b143332301a0c0e7a3d685782eab48` |
| maps/beavercreek.map | 22122496 | `c65ac17d830552cdebfc173c1e8aa17f1f009149138c2c8e72afda1f79f88a60` |
| maps/bloodgulch.map | 22571008 | `50fe52406f075d975e24100a65b26ff696458023dd3509878953052ab0ef858f` |
| maps/boardingaction.map | 22075392 | `e14cebccd63f7780e1f5da7a1687a37bdaa3f0821701095075336ef548889efb` |
| maps/c10.map | 166926336 | `d65683f92e2f78cf8ba4d31c26b212869652b5d5ec037add480865a49e18434e` |
| maps/c20.map | 76980224 | `6560cd88af4c5b4e2f02f14017085a7b47e9a9622198c30f36b03d3d3943d6b8` |
| maps/c40.map | 166295552 | `b5fb3db5b111280e8494c5ec7612604d7facd1e0a511987afa38a228a115a896` |
| maps/carousel.map | 20215808 | `1c6353df6e4530437841b09775e62fa067caa46bb0e40f4579bbf2276991a38e` |
| maps/chillout.map | 20336640 | `81819e9d7037a6b6c4e9a7472a431ebb53ed25ea00d8af634ac8384f1fe13d8b` |
| maps/d20.map | 131012608 | `6b38b4776f4be1e9e12063db202e5809245aae0ded3d9cef56602d7fd69c96be` |
| maps/d40.map | 170405888 | `7c6dccc9f928f4a44db992c4d6f5fa6191e9cfd331bb0d0b631540f0fc9bc796` |
| maps/damnation.map | 23756800 | `8b97ca7d73a4b720ba1b88deeb5a250b02a3f6886ffd2ddaa789cc9ad05e47b8` |
| maps/hangemhigh.map | 21338112 | `932a3a13a69fff5dd6e69c9b2c896c1bf3942c54a2a207975c4d0da4df07ed30` |
| maps/longest.map | 20512768 | `12977a4042ecb960cbe48ef936046a35c6754c18829ad2d17206b66ddd03864e` |
| maps/prisoner.map | 21323776 | `50740d89600b7fa53613ced764fa6e688434a8132948224658bf1ed07662aa3d` |
| maps/putput.map | 19777536 | `7f5d13335d44982b0fbf7aad6b767d035aa64b32bf5c38d6d29bf20916fce5d4` |
| maps/ratrace.map | 23840768 | `ad83896842b2303d145b944f644e4ddfe8d0dd80feda7efcb058a0f567a6bdec` |
| maps/sidewinder.map | 24823808 | `210f7a01bac7b4c242483b1a640e0bc32fb0a2b4f97f56e69668720563b34912` |
| maps/ui.map | 14145536 | `35e3e560478d85178749be310ad13d6d6ecde618d32675261a3554592333a833` |
| maps/wizard.map | 19687424 | `e782ad19071efa1c73f30be44feb6b7e073e15f00337e23d877a8e9776f2f3ad` |

## Limits

These checks prove container parsing, data recognition, full map equality, and managed-import deduplication for these exact three samples. They do not prove headset gameplay, every region or repack, damaged-image recovery, every server protocol, or universal multiplayer compatibility. A server must still use a supported protocol and compatible map content. The directory does not supply enough map hashes to claim automatic per-server disc revision matching. Existing gameplay and save handling were not changed by this audit.
