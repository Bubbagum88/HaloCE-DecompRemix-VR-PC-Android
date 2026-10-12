# Test53 device checklist (Quest 3 and Android phone)

Install over v1.0.19 (same signing key, code 65; settings, saves and game data
are kept). Turn **VR Settings → BODY → CONTACT LOG** on for the interaction
checks and keep each session's `Download/HaloCE/halo_log_*.txt`. Host checks
and builds do not prove any item below; each needs a device result.

## 1. Voice (highest priority)

- [ ] Join a voice-enabled game; speak in the lobby. The game must not close.
- [ ] Speak during a match (push-to-talk and open mic). No crash.
- [ ] Another player hears you; you hear them. Volume slider works.
- [ ] The log's voice lines show sensible numbers (kbps 8–64, frame sizes),
      no "Opus encode failed".

## 2. Network 26

- [ ] Launcher network selector shows **All compatible networks (11–26)**
      selected on a fresh install; a previously chosen exact network is kept.
- [ ] Current OpenCE (Build184, network 26) servers are listed and joinable,
      over Wi-Fi and mobile data.
- [ ] Older network 24/25 servers still join (All compatible).
- [ ] Host a game (PvP and co-op); an OpenCE Build184 PC player can join.
- [ ] A co-op client riding an elevator no longer falls through it.
- [ ] Flashlights/vehicle lights look the same on host and clients.

## 3. Immersion (single player first)

- [ ] VR Settings opens with **IMMERSION** first; changing a toggle there
      shows on its usual page and vice versa.
- [ ] **Wall-run:** run diagonally at a wall, jump, keep pushing forward:
      you run along it for WALL TIME. Log: `VR parkour: wall run`.
- [ ] **Wall-jump / leap:** press Jump again while on the wall or gripping:
      you leap off toward where you look. Log: `VR parkour: wall jump`.
- [ ] **Grip climb / wall grab:** touch a wall with the free hand, squeeze
      Grip, pull down: you rise; release to launch. Log: `wall grip`.
- [ ] Parkour as a **co-op host** works; as a co-op client and in PvP it is
      off (log: `gate blocked ... reason=network-session` with CONTACT LOG on).
- [ ] **NPC grab:** touch a Grunt/Jackal/Marine with the free hand, squeeze
      Grip: it is held (`VR NPC: grabbed`). Elite/Hunter need both hands.
      Lift, drag, throw. After release it gets up or (dead) settles within
      5 s and fights normally. Note any `contact grab miss` with the
      `collision_candidates`/`collision_overlaps` count.
- [ ] **World grab:** weapons, equipment and the eight supported props;
      **LIFT VEHICLES** for an empty Warthog/Ghost/Scorpion/turret.
- [ ] **Manual reload:** with an assault rifle, pistol, sniper, shotgun,
      rocket launcher, flamethrower and needler: remove/eject, take a new
      one from the hip or shoulder pouch, insert, rack. Log:
      `VR manual reload input` and `attempt` lines must appear.
- [ ] **Body retention:** at 75 or 100, bodies stay after an encounter's
      checkpoint in campaign (the newest 45/60 at most).
- [ ] Impact damage, NPC rescue, magazine debris, shake cooling, close
      contact: each toggled on and off.

## 4. Must not regress (v1.0.19 behavior)

- [ ] Joining (PvP and co-op), co-op campaign, reticle, sprint (hold and
      toggle), weapon release/drop/holsters, haptics, Safe Geometry,
      calibration, launcher and updater screens.
- [ ] Android phone: touch controls, gamepad, joining, hosting.
- [ ] Custom Edition maps still listed and playable; none disappear.
- [ ] Settings with no player profile (fresh data) asks for a name.
