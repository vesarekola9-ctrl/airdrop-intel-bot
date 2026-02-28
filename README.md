# Airdrop Intel Bot (PRO+++)

## What it does
- Searches X for airdrop/testnet/points keywords
- Extracts official URL from tweet entities
- Verifies (best-effort):
  - Fetch official page HTML
  - Extract project X handle
  - Check handle profile mentions same domain
- Scores & filters strictly
- ONLY_VERIFIED mode (recommended)
- AUTO_POST mode: posts only top candidates, otherwise queues for manual approval
- Manual approval flow via GitHub Actions (workflow_dispatch)
- Thread template rotation (8 templates)
- One safe self-reply for engagement
- Weekly digest post (1x/week)
- Sponsored mode for paid featured threads (#ad)

## Quick start (GitHub)
1) Add all files to your repo.
2) Add GitHub Secrets (Settings -> Secrets and variables -> Actions):
   - X_BEARER_TOKEN, X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
   - DRY_RUN=1 first, then 0
   - LINK_HUB_URL (your Notion / hub link)
   - ACCOUNT_TAG, CARD_TITLE, CARD_FOOTER

3) Run workflow `airdrop-intel-bot` manually once
4) Check logs (THREAD PREVIEW)
5) Set DRY_RUN=0 to start posting

## Manual approve queue
- Run workflow `approve-queue` (workflow_dispatch)
- It posts top queue items (APPROVE_POST_LIMIT)

## Recommended settings
- ONLY_VERIFIED=1
- MAX_POSTS_PER_RUN=1
- MIN_SCORE_VERIFIED=80
- QUEUE_MIN_SCORE=70
- CTA_EVERY_N_POSTS=3
