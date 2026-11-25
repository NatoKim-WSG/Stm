---
name: find-campaigns
description: Research Whop Content Rewards campaigns, read their rules, rank them, and save each one as a campaign file. Use when the user asks which campaign to clip, wants new campaigns, or names a campaign to set up.
---

# Find and rank campaigns

1. **Gather campaigns.** Content Rewards runs at contentrewards.com (Content Rewards Inc.; Whop
   only processes payouts) and is not in Whop's API (checked 2026-11-25). Read the public
   directory https://contentrewards.com/c/discover/clipping and campaign pages with web fetch —
   budgets there read *spent / total*. Rules, reference files and country details unlock only
   after joining: for those use Claude in Chrome on the user's signed-in account, or ask the
   user to paste them.
   The Whop MCP's `list_bounties` only shows Workforce bounties (fixed reward per task) — check
   them as a side option, not as Content Rewards. Never guess campaign terms — every number must
   come from the campaign page.

2. **For each candidate, read the full brief and rules**, then fill a copy of
   `campaigns/_template.md` as `campaigns/<slug>.md`. Record what the page says, word for word
   for anything that could disqualify a clip (required tags, banned content, source rules).

3. **Rank** the candidates in a table, best first, scoring:
   - Pay per 1,000 views, and max payout per clip
   - Budget remaining vs. total (a nearly spent budget may close before views pay out)
   - YouTube Shorts accepted? (required — skip campaigns that exclude it)
   - Source footage: provided by the campaign or clearly permitted (required)
   - How clippable the content is (talking, reactions, stories > slow tutorials)
   - Minimum views, deadlines, audience/region requirements, AI-editing rules
   - Competition: many submissions on a small budget = lower expected earnings

4. **Recommend one or two** with the reasoning, then let the user choose. Do not start cutting
   until the user picks a campaign.

5. Flag anything unclear (e.g. "does this campaign accept re-uploads of the same moment?") as a
   question for the user rather than assuming.
