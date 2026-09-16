# Character Lock Director - Doudou Series

## Goal
ONE frozen VLM-validated portrait per character. All downstream stages
reference these files exclusively.

## Process
1. Generate 4 pose variants per character (Flux, character card traits)
2. VLM reverse-validation per variant: "Does this show [exact card traits]?"
3. Select best passing variant; freeze as canonical
4. Write character_cards.md with confirmed traits
5. Reject: any portrait with unlisted attributes (glasses when card says none)

## Failure Pattern This Prevents
v7 had TWO Xixi designs in one film (pink-hat vs purple-T) because portraits
were never validated against a card. The constraint module referenced card
traits while generation used portrait appearance → conflict → inconsistency.

## Rule
If no portrait passes VLM check after 4 attempts: STOP, flag to human.
Never proceed with an unvalidated portrait.
