# Assessing Skills and Authenticity — Clean Rebuild v2

A true-alpha transparent, code-friendly asset pack for 1920 × 1080 video projects. No generated checkerboard, cracked black/white margins, or painted artificial transparency.

## Filenames and organization

- `frames/ASA_S##_Frame_<name>.png` — full-canvas 16:9 overlay with a **real transparent video cutout**. The rest of the frame is the neutral off-white branded working base.
- `scenes/S##_Name/ASA_S##_Element_<name>.png` — individual scene compositions or separately reusable UI elements, all with transparent alpha.
- Each PNG has a matching editable SVG source at the same path.
- `manifest.json` — maps scenes, frames, elements, 1920×1080 canvas, and exact video-cutout rectangles for code.
- `previews/` — every illustration against off-white and charcoal backgrounds for transparency verification.

## Scene mapping

1. S01 ScreenShare: live assessment screen showing task and participant windows.
2. S02 ClarifyDetails: project case study with annotated details, precise clarification prompts, and separate magnifier.
3. S03 ThinkAloud: candidate task walkthrough and four separately animated reasoning-step cards.
4. S04 TargetedQuestions: six distinct prepared-question modules with separable cards.
5. S05 FollowUpQuestions: initial answer branching into specific follow-ups and separable conversation cards.

## Layer order in Adobe Express / code

1. Set the full-canvas background to `#F7F5F2` or use your approved dentsu background.
2. Place real moving video footage in the cutout rectangle given in `manifest.json` (coordinates are pixels in 1920×1080).
3. Place the corresponding `Frame_*.png` overlay above the video. The video hole is a true transparent cutout.
4. Place `Element_*.png` foreground illustration layers above the frame. Animate/fade/translate them independently.
5. Add editable titles/narration captions using your own code or Adobe Express text. Add your approved dentsu logo separately, if authorized.

## Motion ideas

- S01: video/task interface scale-in; screen sharing badge pop-in.
- S02: portfolio slide-in; magnifier animate over the relevant field, then question callouts.
- S03: task list reveals; reasoning steps animate 1 → 4.
- S04: six question cards cascade in, grouped by role relevance.
- S05: initial-answer card appears, then branch paths and follow-up cards sequentially.

## Technical validation

PNGs were rendered from clean SVG geometry. Image corners are fully transparent. Frame video windows are transparent and verified by alpha samples. Light/dark previews were exported and are inside the ZIP.

Note: These assets are **original editorial training illustrations based on your established working palette**, not automatically approved official dentsu brand identity. For internal release, replace generic labels and insert the official logo from the company's authorized design library. Human silhouettes/icons and UI are fictional, not real candidate records.
