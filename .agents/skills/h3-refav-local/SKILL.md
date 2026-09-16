---
name: h3-refav-local
description: >
  Local ComfyUI H3 Reference-to-Video with lip-sync for character-consistent
  narrative video. Use when a pipeline stage needs talking-character clips where
  the character must stay on-model across shots (portrait reference) AND the
  mouth must match a specific voice line (TTS audio drives the mouth). This is
  the OmniStudio local generation kernel for character-driven series like
  "豆豆历险记" (Doudou Adventures).
---

# H3 RefAV Local (Character Lock + Lip-Sync)

One ComfyUI graph solves the two hardest problems of AI character video:

1. **Character drift** — `ref_images` injects frozen portrait(s); the character
   stays on-model across every shot.
2. **Lip-sync** — `ref_audios` injects the actual voice line (IndexTTS2);
   the mouth follows real speech, not model imagination.

## When to Use

- Character-dialogue shots in a narrative series (character speaks a line)
- Any shot where the character must look identical to previous shots
- Do NOT use for empty shots (no character) — use plain I2V instead
- Do NOT use for pure action shots without dialogue — I2V is faster

## Server Contract

- ComfyUI running at `http://localhost:8188` (override: `COMFYUI_SERVER_URL`)
- Required models in `models/`:
  - `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors`
  - `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`
  - `loras/minimax_h3_turbo_v4_step600_ema.safetensors`
  - `vae/minimax_h3_video_vae_fp16.safetensors`
  - `vae/minimax_h3_audio_vae_fp32.safetensors`
- Custom nodes: JR_H3 suite (UnifiedAcceleration, TurboLoRA, SigmaShift,
  EnhancedVideoCombine), MiniMaxH3 nodes

## Workflow

Use the bundled `h3_refav_workflow_api.json` (API format). Templated nodes:

| Node | Input | Replace with |
|------|-------|-------------|
| `60`/`8N` | LoadImage | First frame (composition anchor) / portrait per character |
| `61` | LoadAudio | The character's TTS voice line (WAV) |
| `58` | prompt | MCSLA-structured prompt (see below) |
| `1` | noise_seed | Per-shot seed |

**Critical gotchas (all verified the hard way):**

- Upload audio via `POST /upload/image` (NOT `/upload/audio` — that endpoint
  returns 405). Field name is `image` regardless of file type.
- `JR_H3_EnhancedVideoCombine` requires `codec: "H.264"`, `container: "MP4"`,
  `audio_codec: "AAC"` — exact case, these are enum values.
- `quality` is an INT (20), not "Auto".
- The workflow file on disk is the single source of truth. Do not hand-edit
  graph wiring; only replace the templated inputs above.
- Output files land in ComfyUI's own `output/` dir — resolve
  `fullpath` against it, then copy to the project workspace.

## Prompt Format (MCSLA v7)

```
pixar 3d animation movie still. {camera}. {subject-identity-short}.
Reference 1 defines the character faces and outfits exactly - follow them.
the kitten appears EXACTLY ONCE if present. {ACTING emotion timeline}.
{BeatSheet action timeline}. {motion}. {scene + era anchor}. {tail reminders}.
STRICTLY FORBIDDEN: any text, letters, words, subtitles
```

- In ref_av mode, subject uses IDENTITY SHORT FORM only (e.g. "the father",
  "the orange tabby kitten") — portraits carry the appearance. Long appearance
  text competes with the portrait and causes drift.
- Multi-character shots: order by screen importance, join with
  `and separately, `, end with a one-line Reminder.
- Emotion timeline (ACTING): `[0-2s: stern face] [2-4s: pointing]` mapped from
  the dialogue's `emo` field.
- Action timeline (CINEDANCE BeatSheet): `[0-2s: turns toward door]` from the
  storyboard's motion beats.

## Reference Images

- `ref_image_1..N-1`: character portraits (one per character in the shot),
  generated once per series, VLM-validated against the character card, frozen.
- `ref_image_N` (last): the shot's first frame — composition anchor.
- The anchor line "Reference 1 defines the character faces and outfits
  exactly" is required; without it the model re-interprets appearance.

## Audio

- One merged WAV per shot. Multi-line dialogue: concat TTS segments with
  0.15s gaps (ffmpeg concat).
- IndexTTS2 output at 22.05kHz mono is accepted directly.
- Clip length is fixed at 124 frames (5.18s @ 24fps); audio longer than the
  clip is cropped by `crop_to_audio: true` — keep TTS ≤ 4.7s.

## Known Limitations

- Composition freedom: Ref2VA anchors content, not exact framing. First-frame
  as final ref_image helps but does not fully lock framing.
- Night-window shots are a known H3 weakness (purple-noise walls) — prefer
  day/dusk scenes or accept higher retry rates.
- Generation ~200s/shot on RTX 5070Ti (int8 + TurboLoRA 6-step).

## Quality Gate

Run after generation, before accepting the shot:
1. OCR bottom 35% — any 2+ consecutive characters = burned text, FAIL
2. VLM check: character on-model? EXACTLY ONE kitten? era-appropriate props?
3. FAIL → classify (multi_cat / attr_leak / color_drift / burned_text /
   scene_drift / face_drift) → apply the matching fix strategy → retry
   (max 4 attempts, then skip and mark).
