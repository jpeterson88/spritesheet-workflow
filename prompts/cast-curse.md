# Curse Cast Animation Prompt

Create a curse-casting animation spritesheet for the subject using the supplied
anchor images as authoritative references.

The animation should read as a deliberate curse-casting action, not a generic
idle pose or a separate attack with unrelated motion.

Ghost is casting a curse.
Use 16 frames.

## Intent

- The subject is a ghost preparing, focusing, and releasing a curse spell.
- The ghost is forward-facing, south-facing, and centered in the frame.
- The motion should feel controlled, readable, and intentional.
- The motion should feel smooth and not too fast.
- The pose progression should make the casting action obvious without changing
  identity.

## Visual priorities

- Preserve the subject identity, silhouette language, palette, outline style,
  and rendering medium from the identity anchor.
- Use high-fidelity graphics, not pixel art.
- Use the directional or pose anchor only to support body orientation and spell
  staging.
- Keep camera, framing, and overall scale stable across the animation.
- If the subject already has a known style, keep that style consistent rather
  than inventing a new one.

## Motion language

- Use hand, arm, torso, and head movement to communicate spell gathering and
  release.
- The hands should circle around the chest, not the belly.
- Keep one hand about half a circle ahead of the other so the motion reads as
  staggered, ritualistic, and spell-like.
- The eyes should shift into a dazed state during the cast.
- Keep the idle-style up-and-down bobbing motion while casting.
- The mouth should visibly move as the ghost whispers the curse.
- Allow modest squash, lean, compression, and attached motion smear if needed
  for readability.
- Keep the body coherent and recognizable in every frame.
- The spell should feel like it builds from the caster’s body and hands rather
  than appearing as a separate environmental effect.

## Timing

1. Frame 1: Entry pose, forward-facing, hands near the chest, idle bob already
   active.
2. Frame 2: Hands begin the circular motion, with the lower hand slightly ahead.
3. Frame 3: The circle becomes clear while the mouth starts whispering.
4. Frame 4: Increase the circle slightly and keep the bobbing motion steady.
5. Frame 5: Eyes begin shifting toward the dazed state.
6. Frame 6: Continue the chest-centered circle at an even, unhurried pace.
7. Frame 7: The stagger between the hands becomes more obvious.
8. Frame 8: Maintain a front-facing stance while the cast builds.
9. Frame 9: Dazed eyes are clearly established.
10. Frame 10: The circle reaches its widest, most readable arc.
11. Frame 11: Peak the cast while staying smooth and controlled.
12. Frame 12: Hold the peak briefly, with mouth still whispering.
13. Frame 13: Begin a gentle recoil from the peak without breaking the rhythm.
14. Frame 14: Let the hands descend slightly, keeping the circular path alive.
15. Frame 15: Relax back toward the entry pose, preserving the bob and whisper.
16. Frame 16: Return to a near-entry pose that matches Frame 1 closely enough
    to loop seamlessly back into the start.

## Composition

- Keep one complete subject in each cell.
- Do not add scenery, props, UI, text, borders, or grid guides.
- Do not let the subject cross cell boundaries.
- Keep the background uniformly removable.

## Hard constraints

- No identity drift.
- No palette drift.
- No outline or rendering-medium drift.
- No camera movement or perspective change.
- No side-facing or back-facing framing; keep the ghost forward-facing / south
  facing.
- No extra limbs or accessories.
- No unrelated environment, scenery, or detached VFX.
- No belly-rub motion; the hands must circle the chest area with staggered
  offset.
- No westward, vertical, or diagonal framing change.
