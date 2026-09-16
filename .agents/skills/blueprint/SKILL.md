---
name: blueprint
description: >
  Blender headless spatial blueprint for narrative video: grey-box scenes,
  camera system, per-shot depth maps, and route validation. Use before any
  first-frame generation to guarantee spatial continuity (which wall the door
  is on, which direction characters face across cuts). Depth maps use
  distance-based emission greyscale (near=white, far=black, black regions
  filled to 110/255 to prevent purple-noise artifacts).
---

# Spatial Blueprint (Blender Headless)

## Why

Language cannot guarantee spatial continuity across 60 shots. A 3D grey-box
scene is the ground truth: door positions, furniture layout, character
sight-lines, and camera coverage are decided once, in 3D, then every shot's
depth map is derived from the same scene.

## Pipeline

1. **Scene grey-box**: walls, floor, furniture primitives (no materials)
2. **Camera system**: closeup 1.2m / medium 2.5m / wide 4m; name per shot
3. **Route validation**: walk character models through the story path,
   render every camera — expose direction errors HERE (cheap) not in
   generation (expensive)
4. **Export**:
   - `depth_XX.png`: distance-based emission grey (1m→0.95, 11m→0.05),
     black regions floored to 110/255
   - `camXX.png`: same-camera colour render (composition reference)

## Blender 5.x API Notes (verified on Blender 5.2)

- `BLENDER_EEVEE_NEXT` → renamed `BLENDER_EEVEE`
- `Scene.use_nodes` / `Scene.node_tree` removed
- `MaterialSlot.materials` → `material`
- Camera look_at: `to_track_quat('-Z','Y')`
- Cameras must be INSIDE the room; wall-clipped cameras render blank
- EEVEE needs one AREA light per room or interiors render black
- WORKBENCH solid mode unsuitable for colour camviews (flat grey)

## Output Contract

- `world/camera_map.json`: shot_id → {space, camera, note}
- `world/depth/depth_XX.png`: one per shot, 480×864
- `world/camviews/camXX.png`: one per camera position
- Validate: every depth PNG non-blank (std > threshold), every camview
  shows the intended space (VLM check: "is this a living room?")
