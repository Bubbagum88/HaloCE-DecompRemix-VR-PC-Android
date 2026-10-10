# Test49 private owner test candidate

Test49 carries forward the Test48 signed weapon-datum release/holster fix and
restores contact haptics to the behavior used by public v1.0.18. Palm pressure
feedback now requires actual tracked-hand surface collision while VR IK owns
the arm; the added head-to-hand probe no longer renews vibration in the
background. Weapon-fire haptic values and two-hand routing match v1.0.18.

The log now identifies emitted melee and weapon-switch action bits separately,
plus the speed of any physical swing gesture. The button mappings and native
weapon animation handoff are unchanged. See
[TEST49-REGRESSION-AUDIT.md](TEST49-REGRESSION-AUDIT.md) for the supplied-log
analysis and verification limits.

The APKs are private test candidates. Multiplayer, co-op, launcher, Android
touch/gamepad, revision management, and the other accumulated VR features are
carried forward. Test the Quest APK on headset and the flat APK on Android
before treating either runtime as accepted.
