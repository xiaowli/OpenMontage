---
name: indie-qa
description: >
  Quality gate and failure-mode classifier for character-driven AI video
  shots. Use after every generation to decide PASS/FAIL, classify the failure
  type, and apply the matching fix strategy before the next attempt. This is
  the automated repair loop for the 豆豆历险记-style narrative pipeline.
---

# Indie QA: Failure Classifier + Repair Loop

## Quality Gate Sequence

Run in order after each generation. First FAIL wins.

1. **Burned text (deterministic, ~2s)** — RapidOCR on the bottom 35% of 3
   frames (1s/2.5s/4s). ≥2 consecutive characters = FAIL.
   - Do NOT use white-pixel ratio: white scenes (kitchens, snow, pink
     ceilings) false-positive up to 53%.
2. **Fast check (VLM, ~10s)** — sample 5 frames at 0.5s intervals + 2 zoomed
   center crops. Checklist must include: "Is the subject the script's
   character?", exactly-one-cat, outfit consistency, burned letters, era
   props (no smartphones in pre-modern settings).
3. **Full-sequence check (Mage-VL, ~36s)** — 16 frames + script comparison.
   Catches: content mismatch, gradual color drift, transient artifacts that
   single frames miss. This layer found 22 problems that layer-2 + human
   sampling all missed.

## Failure Taxonomy → Fix Strategy

| Type | Detection cue | Fix strategy |
|------|--------------|-------------|
| `multi_cat` | 2+ cats in any frame | Strengthen EXACTLY ONE in prompt, switch seed |
| `attr_leak` | glasses/props on wrong character | Switch to ref_av mode (portrait anchor) |
| `color_drift` | cat fur gray/black/brown | Switch to ref_av mode; portrait is the only reliable color lock |
| `burned_text` | OCR hits | Switch seed (prompt already forbids text) |
| `scene_drift` | indoor→outdoor or wrong room | Regenerate first frame (verify depth-map match) + ref_av |
| `face_drift` | face changes mid-shot | ref_av mode; check portrait quality first |
| `era_violation` | smartphone/modern items | Add era anchor to prompt + first frame must pass era check |
| `purple_noise` | night-window purple walls | H3 weakness; minimize window size in prompt, or change scene to day |

## Repair Loop Rules

- Max 4 attempts per shot per failure type. After 4, skip and mark `skipped`.
- Switch strategy between attempts: seed change alone fixes <20% of failures;
  mode change (i2v→ref_av) fixes ~70%.
- First-frame failures MUST be fixed at the first-frame stage. Never feed a
  known-bad first frame into I2V/RefAV.
- Log every attempt: shot_id, seed, prompt hash, failure type, fix applied.
  This log is the training data for the classifier.

## Human Review

The final gate is a contact sheet (all shots as thumbnails) reviewed by a
human. Scripts pass ≠ video passes. Budget 10 minutes for 60 shots.
