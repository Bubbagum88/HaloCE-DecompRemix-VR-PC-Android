# Test38 device acceptance checklist

These are the owner-provided physical test checklists, preserved in full.
All device checks are pending until actually performed. Automated solver,
protocol and package checks are recorded separately. Unsupported features
must be marked not applicable with their documented implementation limit,
not silently marked passed.

## M28: Device-test checklist

The final delivery notes must include a detailed physical test checklist.

At minimum test:

### Manual reload toggle
1. Default installation/update leaves Manual Reloading OFF.
2. Existing normal reload still works with it OFF.
3. Toggle persists after restarting the game.

### Magazine retrieval
4. Grab a magazine from left shoulder.
5. Grab a magazine from left hip.
6. Confirm accidental hand movement does not constantly spawn magazines.
7. Drop a magazine and recover correctly.

### Magazine insertion
8. Approach magazine well from several reasonable angles.
9. Verify near alignment guides/snaps naturally.
10. Verify magazine does not insert from obviously incorrect positions.
11. Confirm insertion haptic.
12. Confirm correct ammo count after insertion.

### Weapon state
13. Empty weapon and perform complete reload.
14. Tactical/partial reload if supported.
15. Cancel reload midway.
16. Switch weapons halfway through.
17. Drop magazine.
18. Die during reload.
19. Enter a vehicle during reload.

### Charging interaction
20. Grab charging handle.
21. Pull through correct range.
22. Release.
23. Verify weapon becomes usable.
24. Verify appropriate haptic feedback.

### Left-handed support
25. Perform reload with weapon right-handed.
26. Perform equivalent workflow with weapon left-handed.
27. Verify no regression to left-handed weapon orientation/HUD.

### Two-handed weapons
28. Begin with two-handed grip.
29. Release support hand.
30. retrieve magazine.
31. reload.
32. return hand to weapon.
33. verify two-handed stabilization resumes normally.

### Finger/world collision
34. Place open palm slowly against wall.
35. Verify each finger settles independently.
36. Slide hand across wall.
37. Curl fingers near wall.
38. Wrap fingers around crate/ledge.
39. Press fingertips into surface.
40. Pull hand away slowly.
41. Pull hand away quickly.
42. Confirm there is no obvious snapping.
43. Confirm fingers do not heavily penetrate geometry.
44. Confirm rendered hand does not detach excessively from controller.

### Held objects
45. Hold normal weapon and inspect finger pose.
46. Hold magazine and inspect finger pose.
47. Operate charging handle.
48. Confirm hand collision does not fight against objects intentionally held.

### Performance
49. Test during a normal campaign encounter.
50. Test while dual-hand interactions and AI are active.
51. Compare performance with Manual Reloading OFF and ON.
52. Confirm improved finger collision does not create noticeable Quest CPU/frame-time regression.

---

## W58: Device test plan

The delivery must contain a physical-device checklist.

At minimum:

### Settings
1. Confirm World Interaction defaults OFF.
2. Enable it.
3. Restart game.
4. Confirm setting persists.
5. Disable it and verify classic behavior returns.

### Object grabbing
6. Grab a small prop.
7. Carry it.
8. rotate it.
9. drop it.
10. throw it.
11. grab it from a different point.
12. verify wall collision.
13. test one-hand and two-hand control.

### Weight
14. light object feels easy.
15. medium object has mild resistance.
16. heavy object has stronger resistance.
17. two hands improve heavy-object control.

### Grunts
18. grab Grunt.
19. verify ragdoll.
20. lift.
21. shake/move.
22. gentle drop.
23. hard throw.
24. throw into wall.
25. throw into floor.
26. verify surviving Grunt recovers.
27. verify AI resumes.

### Jackals
28. repeat comparable tests.

### Elites
29. one-hand attempt should resist/not fully ragdoll where intended.
30. two-hand grab.
31. verify ragdoll.
32. throw.
33. verify impact behavior.
34. verify recovery if alive.

### Hunters
35. verify two-hand requirement.
36. verify significant weight/resistance.
37. confirm interaction does not destabilize physics.

### Friendlies
38. grab Marine.
39. release gently.
40. verify recovery.
41. verify AI/script state remains valid.

### Collision
42. throw NPC at wall.
43. throw NPC at ground.
44. throw NPC into NPC.
45. throw crate into NPC.
46. verify speed-based damage.
47. verify gentle impacts do not cause huge damage.

### Edge cases
48. switch weapon while holding object.
49. enter vehicle.
50. pause.
51. die.
52. reload checkpoint.
53. start cutscene.
54. verify constraints always clean up.

### Campaign
55. test scripted encounter.
56. test mission-critical NPC.
57. ensure progression still works.

### Performance
58. test large AI encounter.
59. activate multiple ragdolls.
60. inspect frame stability.

### Co-op
61. Quest host + Quest client if possible.
62. Quest + Android client.
63. Quest + stock OpenCE client.
64. verify object transforms.
65. verify ragdoll visibility.
66. verify damage.
67. verify recovery.
68. verify no persistent desync.

### Competitive multiplayer
69. confirm the feature is disabled or handled according to the final networking design.
70. verify no gameplay advantage leaks into ordinary PvP.

---

