---
name: publish-clip
description: Publish an approved clip to YouTube and submit its link to the Whop campaign within the 30-minute window, then log it. Use only after the user has approved that specific clip.
---

# Publish a clip

**Only for clips the user has explicitly approved in this conversation.** Approval of one clip
does not cover another. If in doubt, ask.

## Before publishing
- Re-read the campaign file: required tags/mentions/links are in the title or description,
  length limits are met, the campaign is still active and has budget.
- Confirm Whop submission can happen right away. **Whop requires the post link to be submitted
  within 30 minutes of going public** — never publish and then wait.

## Publish (current stage: manual upload)
The YouTube upload script is not built yet (stage V2). Until it is:
1. Give the user the clip path and paste-ready title + description from `upload_info.md`.
2. The user uploads it in YouTube Studio / the YouTube app as a Short, public.
3. The user pastes back the video URL.

## Submit to Whop
- **Content Rewards campaigns** (pay per 1k views) are not in Whop's API: the user submits the
  Short's link on the campaign page on contentrewards.com, or Claude in Chrome does it with the
  user watching.
  Have the link and the campaign page ready before the clip goes public.
- **Whop Workforce bounties** (`bnty_…`, fixed reward) only: `mcp__whop__call_write_operation` with
  name `create_bounty_submission`, arguments
  `{"bounty_id": "<bnty_…>", "deliverable": {"urls": ["<Short URL>"]}}`. The guard hook allows
  only bounty-submission writes, and Claude Code asks the user before each one.
- Fallback: the user submits in the Whop app, or Claude in Chrome does it with the user watching.
- Report the submission result to the user.

## Log
Append a row to `tracking/posts.csv`:
`date,campaign,clip,youtube_url,published_at,submitted_at,status,views,earnings`
Use ISO times (local). `status` = submitted / approved / rejected / paid.
