# Executive Producer - Doudou Series Pipeline

## When To Use

Character-driven AI narrative series (Pixar-style vertical short drama with
recurring animal + human characters, fully-voiced dialogue, spatial
continuity across 30-60 shots). Requires local ComfyUI with H3 models and
IndexTTS2.

Do not use for: motion graphics without acting (route to `animation`),
talking-head avatar presenter (route to `avatar-spokesperson`).

## Contract

The pipeline produces character-consistent, lip-synced narrative video. It
does not silently substitute visual-only generation for dialogue shots, does
not skip quality gates, and does not allow schema enum violations.

## Stage Order

1. `script` - structure the story into schema-locked JSON
2. `blueprint` - Blender spatial ground truth
3. `character_lock` - one frozen portrait per character (VLM-validated)
4. `firstframes` - per-shot composition anchor (VLM content check)
5. `dialogue_audio` - IndexTTS2 emotional voice lines
6. `shots` - generation (ref_av for dialogue, i2v for empty) + QA loop
7. `final_qa` - Mage-VL + human contact sheet review
8. `compose` - ffmpeg assembly with sfx and ambient bed

## Hard Rules

- Schema enum violations in script = send back to script stage, never
  "fix it downstream"
- First-frame quality failures never flow into shots stage
- Every generation failure is classified before any retry
- Local generation only; zero API cost budget
