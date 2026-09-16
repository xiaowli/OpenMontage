# Compose Director - Doudou Series

## Goal
Assemble final cut: shot concat + TTS timeline + sfx placement + ambient bed.

## Process
1. Concat all shots (ffmpeg concat demuxer, copy codec)
2. Mix audio: TTS at per-line timestamps (atempo ≤1.35x if overflow),
   ambient bed at -32dB, SFX at script sfx field times (NOT random)
3. No BGM. No subtitles. Zero burned text.
4. Loudness scan: max ≤ -0.5dB
5. Output: release/<series>_<version>.mp4

## Gotchas
- TTS files are WAV 22050Hz mono → aformat to 48000 stereo before mixing
- KVarN files may be .ogg not .mp3 — check actual extension
- sfx timestamps are absolute (shot start + field t)
