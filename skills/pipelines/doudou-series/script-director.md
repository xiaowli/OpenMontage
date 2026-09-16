# Script Director - Doudou Series

## Goal
Convert story synopsis into schema-locked script.json.

## Process
1. Read story synopsis
2. Break into shots (5.18s each, vertical 480x864)
3. Per shot: space (from vocabulary), camera, characters (from vocabulary),
   action (Chinese), motion (English), firstframe_brief, dialogue
4. Per dialogue line: speaker, line (pure text), action (stage direction),
   emo (vocabulary), emo_voice (English emotion), target_dur

## Schema Lock
- characters: exactly [豆豆, 希希, 爸爸] (or series vocabulary)
- space: exactly from scene vocabulary in CHARACTER_CONSTRAINTS.md
- No pinyin, no English, no mixed names

## Dialogue Rules (台词三律)
- 口气律: each character has a language fingerprint; audit consistency
- 留白律: dialogue coverage ≤40%; emotional peaks are silent
- 承接律: each line continues from previous shot's ending

## Anti-Patterns (from v5.4/v6.0 failures)
- Stage directions in line field → TTS reads them aloud
- "The cat says meow" → use sfx field, never TTS
- Emotion missing → downstream has no emotion vector, flat delivery
- Pinyin character names → constraint module drops the character silently

## Validation
Before returning, run:
- Every character value in vocabulary set
- Every space value in vocabulary set
- No brackets/parentheses in line fields
- Dialogue coverage <40%
