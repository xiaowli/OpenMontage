---
name: indie-tts2
description: >
  Local IndexTTS2 emotional dialogue synthesis with duration control. Use when
  a character needs a voice line that sounds acted rather than narrated:
  per-line emotion control (angry/soft/desperate), voice cloning from a
  reference clip, and precise duration targeting to fit a fixed shot window.
  Runs locally on RTX 5070Ti (6GB VRAM floor).
---

# IndexTTS2: Emotional Dialogue with Duration Control

## Why Not edge-tts

edge-tts (Xiaoxiao/Yunjian) produces news-anchor cadence. For acted dialogue
you need per-line emotion, and emotion injected as text guidance
("angry, questioning sharply") plus voice cloning from a reference clip.

## Deployment

- Repo: `E:/AI/models/index-tts` (venv ready), models at `E:/AI/models/IndexTTS-2`
- Runtime: `.venv/Scripts/python.exe`, `from indextts.infer_v2 import IndexTTS2`
- Init: `IndexTTS2(cfg_path="checkpoints/config.yaml", model_dir="E:/AI/models/IndexTTS-2", use_qwen_emo=True)`
- Throughput: RTF ~5 (10s inference → 2s audio); 40 lines ≈ 7 minutes

## Calling

```python
tts.infer(
    spk_audio_prompt=ref_clip_path,   # voice timbre comes from this clip
    text=line_text,                    # the actual dialogue
    use_emo_text=True,                 # REQUIRED to enable emotion text
    emo_text="angry, questioning sharply",
    output_path=out_wav,
)
```

**Gotchas:**
- `use_emo_text=True` is required alongside `emo_text` — silently ignored
  otherwise (result: flat narrator voice).
- There is NO `duration` parameter in this build. Control length by editing
  the text (shorter/longer phrasing), then measure and atempo in post if
  needed (≤1.35x to stay natural).
- Output: 22050 Hz mono WAV.
- `emo_text` accepts natural English emotion descriptions; the QwenEmotion
  model converts them to emotion vectors (e.g. afraid 0.8).

## Voice Reference Clips

Use one stable reference clip per character. Source options:
- A previous TTS generation of the same character (consistent timbre)
- A human recording of the target voice

## Batch Script Pattern

For a series, iterate `script.json → dialogue[]`, per line:
1. Skip if output exists and >50KB (resume support)
2. Infer with emo_text
3. Check duration ≤ shot_window - 0.4s (lead-in); if over, re-generate with
   shortened text or apply atempo ≤1.35x in post
