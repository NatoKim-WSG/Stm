# Stm — AI clipping pipeline (Whop Content Rewards → YouTube Shorts + TikTok)

Goal: earn from Whop Content Rewards campaigns by turning permitted long-form videos into
3–5 vertical clips per day, posting them on the user's YouTube channel and TikTok account
(TikTok added 2026-11-25), and submitting the links to the campaign. Built in stages; each stage stays human-approved until it proves reliable.

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
   no near-duplicate uploads; stay at roughly 3–5 posts per day per platform; no misleading
   titles. Post the same clip to both YouTube and TikTok only when the campaign allows it.
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
| 5. Publish to YouTube / TikTok + submit within 30 min | `/publish-clip` | row in `tracking/posts.csv` |

## Build stages

- [x] V1 — campaign research files + clip pipeline (transcribe → pick → render); tested 2026-11-25
- [ ] V2 — YouTube upload script (Data API, OAuth). First test one upload: unverified Google
      Cloud projects may lock uploads to private until Google's API audit is passed. Default
      quota is roughly 6 uploads/day — enough for 3–5 Shorts.
      TikTok: its Content Posting API keeps posts from unaudited apps private, so TikTok
      uploads stay manual (the user in the app, or Claude in Chrome with the user watching).
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
- 2026-11-25 (later): Claude in Chrome connected. Joined (user said to) It's Personal, SEGA,
  Eneba BroPacks, Michael Sartain, Bobby VanRiper. User's YouTube channel: created 2022-05-07,
  **0 subscribers**; user wants gaming / popular creators / streamers that get views easily.
  Ranked in `campaigns/shortlist-2026-11-25.md`; files written for the top two:
  `campaigns/sega-steam-black-friday.md` (pick) and `campaigns/bobby-vanriper-gta6.md` (backup).
  Rule docs on Google Docs read best via `.../mobilebasic`.
- 2026-11-25 (later): user added **TikTok** (creating a new account themselves). Re-checked
  TikTok-only and gaming campaigns; joined SkiiMaskTimmy (60% Tier 1, harder than its card).
  SEGA stays the pick: same $5/1K on TikTok.
- User is in the **Philippines** (UTC+8, 13 h ahead of US Eastern). Most good campaigns want
  US / Tier 1 viewers. Plan: YouTube Shorts in English, published at US prime time
  (11 AM–2 PM or 5–9 PM ET = 12–3 AM or 6–10 AM PH time); the user must be awake to submit
  within 30 min. TikTok shows a new account's posts mostly in its own country, so posting
  time alone won't reach US viewers there — see `campaigns/shortlist-2026-11-25.md`.
- User chose **streamers & gaming** over SEGA (worried ad clips won't be watched). Joined and
  wrote files: `jasontheween-sourjacks.md` (TikTok, $4/1K, no country rule),
  `expedia-ishowspeed.md` and `sypherpk.md` (YouTube OK, 10K views/video, 50% English-speaking).
  Reach "pool" campaigns (Lacy etc.) need 1M total views to share the pool — skip.
- 2026-11-25 (evening): user said go → downloaded Sour Jacks Ep. 501 (campaign Drive) and the
  last 20 min of IShowSpeed's 2026-11-06 stream (yt-dlp, approved window 2:46:29–end). Editor
  upgraded on the user's request: hooks with accent word + pop-in, punch-in zooms, colour grade,
  FFmpeg-generated SFX, colour emoji pop-ups (Pillow + Segoe UI Emoji), jump-cut `segments`,
  `box` reframe for streams. Clips awaiting the user's per-clip approval:
  `output/sourjacks-ep501/clip01-02.mp4` (TikTok, needs the user's new TikTok account) and
  `output/speed-expedia-20261106/clip01-02.mp4` (YouTube Shorts, post at US prime time).
- User's existing YouTube channel is **not** streamer-niche (Expedia/Reach requires streamer or
  travel accounts). Plan: user creates a dedicated streamer-clips channel (brand channel under
  the same Google account) + a TikTok with the same name, and connects both in Whop → Settings →
  Connected Accounts. Post Speed/Sypher/Bobby clips only there; keep SEGA-type promos off it.
  The V2 upload script must authorise that brand channel, not the personal one.
- **Moving to the PC (2026-11-25):** clip plans and hand-fixed transcripts are in git
  (`work/<name>/clips.json`, `transcript.json`); videos are not. To get the 4 clips back on the
  PC, either copy the laptop's `output\` folder by USB/Drive, or rebuild them:
  1. `curl -L -o sources\sourjacks-ep501.mp4 "https://drive.usercontent.google.com/download?id=169YOcmn_M4Mt1YnoyawY1QzEkdeQO2aZ&export=download&confirm=t"`
     (285 MB, campaign's Drive folder "New JasonWeen Content", file "Ep. 501.mp4")
  2. `.venv\Scripts\yt-dlp --js-runtimes node --download-sections "*2:33:00-inf" --force-keyframes-at-cuts -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]" --merge-output-format mp4 -o "sources\speed-expedia-20261106.%(ext)s" https://www.youtube.com/watch?v=Kyv61l2vF6M`
     (≈386 MB). Check `ffprobe` duration ≈ 1210.9 s — clip times assume the file starts at
     stream 2:33:00 exactly; if it differs, shift the `segments` by the difference.
  3. `.venv\Scripts\python -m clipper.render work\sourjacks-ep501\clips.json` and the same for
     `work\speed-expedia-20261106\clips.json` (no re-transcribing needed).
- **Next:** user creates the streamer-clips YouTube channel + TikTok and connects them in Whop;
  user reviews the 4 clips and approves per clip; Speed clips post at US prime time with the
  user awake to submit within 30 min (`/publish-clip`). Then more Sour Jacks episodes (Ep. 502,
  503, 301… in the same Drive folder) and SypherPK VODs. Optional: Expedia logo from the
  campaign's Brand Assets folder (ask before downloading). SEGA is parked (promo content would
  dilute the streamer channel).

## Working with the user

- The user leaves tool choices to Claude: recommend one option and proceed, explaining briefly;
  don't survey alternatives.
- Build in stages; prepare everything and stop at the approval step (hard rule 1).
- User is in the Philippines (UTC+8); new channels (0 followers). Prefers campaigns that get
  views easily: streamers, popular creators, gaming. Wants clips heavily edited — hooks, sound
  effects, zooms, colour, emoji pop-ups (see the make-clips skill).
- Explain campaign rules in plain words and quote the exact wording when it matters (e.g.
  "streamer niche" = what the channel posts, not that the user must stream).
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

- Getting sources (only footage the campaign permits, and only after the user OKs the download):
  - Google Drive file (public link): find the file id (Drive page → `[data-id]`), then
    `curl -L -o sources\<name>.mp4 "https://drive.usercontent.google.com/download?id=<id>&export=download&confirm=t"`
  - YouTube / Twitch VOD section:
    `.venv\Scripts\yt-dlp --js-runtimes node --download-sections "*H:MM:SS-inf" -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]" --merge-output-format mp4 -o "sources\<name>.%(ext)s" <url>`
- `--device auto` (default) uses an NVIDIA GPU via CUDA when one is found, else CPU. The
  original laptop has an AMD integrated GPU (no CUDA), so there `small` is the default and
  `medium` only for short sources. On a CUDA GPU, `medium` or `large-v3` is fine.
- FFmpeg 9 (Gyan essentials build, has libass + libx264) is on PATH.
- Reframe modes: `blur` (whole frame + blurred fill — safe default) or `crop` with `crop_x` 0–1
  (use when one speaker fills the frame).

## Layout

```
clipper/        transcribe.py, render.py, captions.py (caption style lives in DEFAULT_STYLE),
                effects.py (zooms, colour grade, emoji pop-ups, generated SFX)
campaigns/      one .md per campaign, from _template.md
sources/        source videos (git-ignored, delete after use)
work/<name>/    transcript.json, transcript.txt, clips.json (these three are in git so another
                PC can re-render), per-clip subtitle files and frames (ignored);
                work/_assets/ = generated SFX and emoji PNGs (ignored, rebuilt on demand)
output/<name>/  finished clipNN.mp4 + upload_info.md
tracking/       posts.csv — every published clip and its submission
.claude/skills/ find-campaigns, make-clips, publish-clip
```
