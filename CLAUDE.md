# Stm — AI clipping pipeline (Whop Content Rewards → YouTube Shorts)

Goal: earn from Whop Content Rewards campaigns by turning permitted long-form videos into
3–5 vertical Shorts per day, posting them on the user's YouTube channel, and submitting the
links to the campaign. Built in stages; each stage stays human-approved until it proves reliable.

## Hard rules (never break these)

1. **Nothing goes public and nothing gets submitted without the user's explicit "yes" for that
   specific clip.** Uploading, publishing, submitting to Whop and deleting posts are all outward
   actions; approval for one clip never covers the next.
2. **Read the campaign rules before cutting anything.** Every campaign gets a file in
   `campaigns/` (copy `campaigns/_template.md`). Clips must satisfy every checklist item:
   allowed source footage, required tags/mentions/links, length limits, banned content,
   platform and audience requirements, whether AI editing is allowed.
3. **Only clip footage the campaign permits** (campaign-provided assets or sources the brief
   names). If the source's permission is unclear, stop and ask.
4. **Whop's 30-minute window:** a post's link must be submitted within 30 minutes of going public.
   Never publish a clip unless submission can happen right after. Log every post in
   `tracking/posts.csv` with the publish time.
5. **Protect the channel:** every clip must be meaningfully edited (captions, hook, reframing);
   no near-duplicate uploads; stay at roughly 3–5 Shorts per day; no misleading titles.
6. **Secrets stay local:** OAuth client files and tokens (`client_secret*.json`, `token*.json`,
   `.env`) are never printed, committed or sent anywhere.
7. Disk is tight (~23 GB free on C:). Delete source videos and `work/` intermediates once a
   campaign's clips are posted; never keep more than a few sources at once.
8. **Never move money on Whop.** The Whop connection has admin scopes (transfers, withdrawals,
   payout destinations, swaps) because Whop's consent screen required them. The guard hook
   `.claude/hooks/whop_guard.py` (wired in `.claude/settings.json`) allows only read tools and
   `create_bounty_submission` / `submit_bounty_submission` / `cancel_bounty_submission`; every
   other Whop write is denied, and each allowed write still asks the user. Never weaken the guard
   or its settings without the user's explicit request.

## The daily flow

| Step | Skill | Output |
|---|---|---|
| 1. Find and rank campaigns, read rules | `/find-campaigns` | `campaigns/<slug>.md` |
| 2. Get permitted source video | (manual or download) | `sources/<name>.mp4` |
| 3. Transcribe, pick moments, render | `/make-clips` | `output/<name>/clipNN.mp4` + `upload_info.md` |
| 4. User reviews clips | — | approval per clip |
| 5. Publish to YouTube + submit to Whop within 30 min | `/publish-clip` | row in `tracking/posts.csv` |

## Build stages

- [x] V1 — campaign research files + clip pipeline (transcribe → pick → render); tested 2026-11-25
- [ ] V2 — YouTube upload script (Data API, OAuth). First test one upload: unverified Google
      Cloud projects may lock uploads to private until Google's API audit is passed. Default
      quota is roughly 6 uploads/day — enough for 3–5 Shorts.
- [ ] V3 — Whop submission. **Checked 2026-11-25: Content Rewards (pay-per-1k-views) campaigns
      are NOT in Whop's public API** — none of the MCP's 472 operations cover them; the docs show
      them only as an app inside a whop. Content Rewards is now run by Content Rewards Inc. at
      contentrewards.com (site footer: "independent of Whop. Whop processes payouts."). Public
      directory: https://contentrewards.com/c/discover/clipping — budgets read *spent / total*;
      rules, reference files (source footage) and creator lists unlock only after joining.
      Discovery and submission go through contentrewards.com: the user, or Claude in Chrome
      with the user watching.
      The API's `list_bounties` returns Whop Workforce tasks instead (fixed reward per accepted
      submission, often with livestream proof, country lists). For those only:
      `create_bounty_submission` with `bounty_id` (`bnty_…`) and `deliverable.urls`.
      Whop MCP connected 2026-11-25 (`whop`, local config); re-sign-in with `/mcp` if it shows
      "Needs authentication". Money-moving operations are blocked — see hard rule 8.
- [ ] V4 — view and earnings tracking

## Status / where we left off (update this at the end of each session)

- 2026-11-25: V1 tested. Whop MCP connected on the laptop with the money guard (hard rule 8).
  Found that Content Rewards lives at contentrewards.com; user has an account there.
  Research so far: `campaigns/shortlist-2026-11-25.md`.
- **Next:** connect Claude in Chrome (`/chrome`), open the shortlisted campaigns, ask the user
  before each **Join**, read the unlocked rules/files, write `campaigns/<slug>.md` for the best
  2–3, then the user picks one. Still need the user's country (some campaigns pay by region).

## Working with the user

- The user leaves tool choices to Claude: recommend one option and proceed, explaining briefly;
  don't survey alternatives.
- Build in stages; prepare everything and stop at the approval step (hard rule 1).
- Keep this file and the skills updated whenever a rule, flow or stage changes — they are the
  project's memory and move with the repo (Claude's per-machine memory does not).

## Setting up on a new PC (e.g. the GPU PC)

1. Install Git, Python 3.13, Claude Code, Chrome + the Claude in Chrome extension, and FFmpeg
   with libass + libx264 (Windows: Gyan "essentials" build) on PATH.
2. `git clone https://github.com/NatoKim-WSG/Stm.git` and open Claude Code in that folder.
3. `python -m venv .venv` then `.venv\Scripts\pip install -r requirements.txt`
   (Linux/macOS: `.venv/bin/pip`). **Do this before using Whop tools** — the guard hook blocks
   every Whop call until `.venv` exists.
4. NVIDIA GPU: install CUDA 12 cuBLAS + cuDNN 9 as the faster-whisper README's GPU section
   describes, then check `.venv\Scripts\python -c "import ctranslate2; print(ctranslate2.get_cuda_device_count())"`
   prints 1 or more.
5. Secrets never go through git: copy any `client_secret*.json` / `token*.json` / `.env` by hand.
6. Optional: re-add the Whop MCP (`/mcp`). Content Rewards isn't in Whop's API, so the pipeline
   doesn't need it; if added, the guard in `.claude/settings.json` applies automatically.
7. Run `/chrome` to connect Claude in Chrome, then continue from "Status" above.

## Backlog (ideas worth adding, roughly in order of value)

- Face-follow cropping for single-speaker sources (instead of fixed `crop_x`).
- Extra moment signals for streams: audio loudness spikes, laughter, chat-replay activity.
- More caption templates (fonts, colours, emoji pop-ins) selectable per campaign.

Decision 2026-11-25: keep this own pipeline instead of adopting
github.com/jaspher19/open-clip-editor (days old, single maintainer, Node + Python web app, its
LLM picker needs a separate API key). Borrow its ideas above instead; revisit if it matures.

## Commands (Windows, PowerShell; venv at `.venv`)

```
.venv\Scripts\python -m clipper.transcribe sources\<name>.mp4 [--model small|medium] [--language en] [--device auto|cpu|cuda]
.venv\Scripts\python -m clipper.render work\<name>\clips.json [--only 01 03]
```

- `--device auto` (default) uses an NVIDIA GPU via CUDA when one is found, else CPU. The
  original laptop has an AMD integrated GPU (no CUDA), so there `small` is the default and
  `medium` only for short sources. On a CUDA GPU, `medium` or `large-v3` is fine.
- FFmpeg 9 (Gyan essentials build, has libass + libx264) is on PATH.
- Reframe modes: `blur` (whole frame + blurred fill — safe default) or `crop` with `crop_x` 0–1
  (use when one speaker fills the frame).

## Layout

```
clipper/        transcribe.py, render.py, captions.py (caption style lives in DEFAULT_STYLE)
campaigns/      one .md per campaign, from _template.md
sources/        source videos (git-ignored, delete after use)
work/<name>/    transcript.json, transcript.txt, clips.json, per-clip subtitle files
output/<name>/  finished clipNN.mp4 + upload_info.md
tracking/       posts.csv — every published clip and its submission
.claude/skills/ find-campaigns, make-clips, publish-clip
```
