# First Frame Director - Doudou Series

## Goal
One VLM-passed composition anchor per shot. Bad first frame = bad shot.

## Process
1. Flux + CN-Depth (blueprint depth map, strength 0.45-0.6)
2. Prompt: MCSLA with full appearance (I2V mode) + era anchor + forbidden
   props negative
3. VLM content check: subject / scene / era / no text
4. FAIL → classify → fix → retry (max 4) → skip with mark

## Era Blacklist (auto-inject into negative)
smartphone, mobile phone, laptop, LED screen, modern appliances
