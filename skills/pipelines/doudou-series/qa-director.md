# QA Director - Doudou Series

## Goal
Mage-VL full-sequence check on every shot + human contact sheet review.

## Process
1. Mage-VL: 16 frames per shot, compare against script (content/character/
   drift), produce pass/fail per shot
2. Build contact sheet: 6 grids of 10 thumbnails (2.5s midpoint per shot)
3. Present to human for review — THIS IS MANDATORY
4. Failed shots → classify via indie-qa → repair loop OR human waiver

## Why Mage-VL Is Non-Negotiable
v6: Mage-VL found 22 content problems that Qwen3-VL-4B fast-check + human
frame-sampling ALL missed. Skipping this layer = shipping unseen failures.
