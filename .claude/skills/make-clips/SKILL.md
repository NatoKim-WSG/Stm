---
name: make-clips
description: Turn a permitted source video into 3–5 captioned vertical Shorts for a chosen campaign — transcribe, pick the best moments, write clips.json, render, and hand the clips to the user for review. Use when the user has a source video or says to make clips.
---

# Make clips

Prerequisite: a campaign file in `campaigns/` that the user picked. Re-read its rules first.
If the source footage is not clearly permitted by that campaign, stop and ask.

## 1. Transcribe
```
.venv\Scripts\python -m clipper.transcribe sources\<name>.mp4
```
Long VODs take a while on CPU — run it in the background. Output: `work/<name>/transcript.txt`.

## 2. Pick moments
Read `transcript.txt` (in chunks if long). Choose 3–5 moments that:
- **Hook in the first 2 seconds** — a bold claim, a question, conflict, a surprising line.
  Start the clip on that line, not on the lead-up.
- **Stand alone** — a viewer with no context understands it.
- **Pay off** — end right after the punchline/answer/reaction; cut dead air.
- Are **20–60 s** unless the campaign says otherwise (hard max 180 s for Shorts).
- Do not overlap each other and fit the campaign's content rules.

Snap start/end to segment boundaries in the transcript, starting ~0.2 s before the first word.

## 3. Write `work/<name>/clips.json`
Format is documented at the top of `clipper/render.py`. For each clip fill in:
`id`, `start`, `end`, `hook` (≤ 6 words, on screen), `title` (≤ 70 chars, honest, no clickbait
that the clip doesn't deliver), `description`, `hashtags` (include every tag/mention the
campaign requires, plus `#shorts`), `reason`.
Default `"reframe": "blur"`; use `"crop"` with `crop_x` only when the speaker fills the frame.

## 4. Render
```
.venv\Scripts\python -m clipper.render work\<name>\clips.json
```
Re-render a single clip with `--only 02` after tweaks.

## 5. Check before handing over
- Extract a frame from each clip (`ffmpeg -ss 3 -i clip01.mp4 -frames:v 1 check.png`) and look
  at it: captions readable, not covering faces, hook not cut off.
- Confirm every campaign checklist item is met; list any that are not.

## 6. Hand to the user
Give the path of each clip and `output/<name>/upload_info.md`, with a one-line summary per clip.
Wait for the user's approval per clip before anything is published (see `/publish-clip`).
