---
name: publish-clip
description: Publish an approved clip to YouTube Shorts and/or TikTok and submit its link to the campaign within the 30-minute window, then log it. Use only after the user has approved that specific clip.
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
No upload script yet (stage V2). Until it is built:
1. Give the user the clip path and paste-ready title + caption from `upload_info.md`.
2. The user uploads it, public:
   - **YouTube:** YouTube Studio / the YouTube app, as a Short.
   - **TikTok:** the TikTok app or tiktok.com/upload. If the caption carries #Ad / #Sponsored,
     also switch on *Content disclosure → Branded content* (TikTok's own rule for paid promos).
     Keep comments and likes on.
3. The user pastes back the post URL.

**Posting one clip on both platforms:** only if the campaign file says cross-posting is
allowed. Each post is its own submission with its own 30-minute window, so publish and submit
one platform, then the other — never both at once.

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
`date,campaign,clip,platform,url,published_at,submitted_at,status,views,earnings`
(`platform` = youtube / tiktok; one row per post.)
Use ISO times (local). `status` = submitted / approved / rejected / paid.
