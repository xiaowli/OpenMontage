# Blueprint Director - Doudou Series

## Goal
Blender grey-box scenes → depth maps + camera views for every shot.

## Process
1. Build grey-box scenes from script spaces (no materials, primitives only)
2. Create cameras per camera_map (closeup 1.2m / medium 2.5m / wide 4m)
3. Walk character models through story route; render every camera
4. Export depth (distance-based emission, black floor 110/255) and camviews
5. Validate: no blank renders, VLM confirms each camview shows its space

## Blender 5.x Gotchas
- EEVEE (not EEVEE_NEXT); no Scene.use_nodes; Slot.material (not materials)
- Camera to_track_quat('-Z','Y'); camera INSIDE room; one AREA light per room
- Depth: emission shader by distance (1m=0.95, 11m=0.05); floor black at 110
