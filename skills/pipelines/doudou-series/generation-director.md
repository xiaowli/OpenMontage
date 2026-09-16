# Generation Director - Doudou Series

## Goal
Generate every shot. Dialogue shots → ref_av mode; empty shots → i2v mode.

## Route Selection
- dialogue present → ref_av (portraits + TTS audio drive generation)
- no dialogue → i2v (first frame + full-appearance MCSLA prompt)

## Per-Shot Loop
1. Submit workflow (h3-refav-local template)
2. Wait for completion (~200s on 5070Ti)
3. OCR burn-in check (RapidOCR bottom 35%, ≥2 chars = FAIL)
4. VLM fast check (5 frames + 2 zooms)
5. FAIL → classify → apply matching strategy → retry (max 4)
6. PASS → replace → next shot

## Retry Strategy (from indie-qa)
- Attempt 1-2: same mode, different seed
- Attempt 3+: switch mode (i2v → ref_av or add ref-only) per failure type
- After 4: mark skipped, continue to next shot (do not block the batch)

## Parallel Safety
Benchmark/batch runs must have EXCLUSIVE access to ComfyUI. Concurrent
requests cause KV allocation failures and 40x slowdowns.
