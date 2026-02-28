import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def b(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    if not v.strip():  # missing secret -> "" should not flip to False
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")

def i(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default

@dataclass
class Cfg:
    dry_run: bool
    max_posts_per_run: int

    bearer: str
    api_key: str
    api_secret: str
    access_token: str
    access_secret: str

    keywords: list[str]
    lang: str
    results_per_run: int

    min_score_verified: int
    min_score_unverified: int
    queue_min_score: int

    require_https: bool
    reject_social_only: bool
    block_shorteners: bool
    allowlist_domains: list[str]

    account_tag: str
    card_title: str
    card_footer: str

    link_hub_url: str
    cta_every_n_posts: int
    cta_text: str

    weekly_digest: bool
    weekly_digest_day: str

    sponsored_mode: bool
    sponsored_title: str
    sponsored_project: str
    sponsored_official_url: str
    sponsored_note: str
    sponsored_tag: str

    auto_post: bool
    only_verified: bool
    approve_post_limit: int

    self_reply_enabled: bool
    self_reply_text: str

    template_rotation: bool
    metrics_enabled: bool

def load_cfg() -> Cfg:
    kw = [k.strip() for k in os.getenv("KEYWORDS", "").split(",") if k.strip()]
    al = [d.strip().lower() for d in os.getenv("ALLOWLIST_DOMAINS", "").split(",") if d.strip()]

    return Cfg(
        dry_run=b("DRY_RUN", True),
        max_posts_per_run=i("MAX_POSTS_PER_RUN", 1),

        bearer=os.getenv("X_BEARER_TOKEN", "").strip(),
        api_key=os.getenv("X_API_KEY", "").strip(),
        api_secret=os.getenv("X_API_SECRET", "").strip(),
        access_token=os.getenv("X_ACCESS_TOKEN", "").strip(),
        access_secret=os.getenv("X_ACCESS_SECRET", "").strip(),

        keywords=kw or ["airdrop", "testnet", "points campaign", "snapshot"],
        lang=os.getenv("LANG", "en").strip(),
        results_per_run=i("RESULTS_PER_RUN", 50),

        min_score_verified=i("MIN_SCORE_VERIFIED", 80),
        min_score_unverified=i("MIN_SCORE_UNVERIFIED", 95),
        queue_min_score=i("QUEUE_MIN_SCORE", 70),

        require_https=b("REQUIRE_HTTPS", True),
        reject_social_only=b("REJECT_SOCIAL_ONLY", True),
        block_shorteners=b("BLOCK_SHORTENERS", True),
        allowlist_domains=al,

        account_tag=os.getenv("ACCOUNT_TAG", "@AirdropIntelHQ").strip(),
        card_title=os.getenv("CARD_TITLE", "VERIFIED AIRDROP INTEL").strip(),
        card_footer=os.getenv("CARD_FOOTER", "@AirdropIntelHQ").strip(),

        link_hub_url=os.getenv("LINK_HUB_URL", "").strip(),
        cta_every_n_posts=max(1, i("CTA_EVERY_N_POSTS", 3)),
        cta_text=os.getenv("CTA_TEXT", "All links & beginner setup → ").strip(),

        weekly_digest=b("WEEKLY_DIGEST", True),
        weekly_digest_day=os.getenv("WEEKLY_DIGEST_DAY", "MON").strip().upper(),

        sponsored_mode=b("SPONSORED_MODE", False),
        sponsored_title=os.getenv("SPONSORED_TITLE", "SPONSORED").strip(),
        sponsored_project=os.getenv("SPONSORED_PROJECT", "").strip(),
        sponsored_official_url=os.getenv("SPONSORED_OFFICIAL_URL", "").strip(),
        sponsored_note=os.getenv("SPONSORED_NOTE", "Featured campaign. Do your own research.").strip(),
        sponsored_tag=os.getenv("SPONSORED_TAG", "#ad").strip(),

        auto_post=b("AUTO_POST", True),
        only_verified=b("ONLY_VERIFIED", True),
        approve_post_limit=i("APPROVE_POST_LIMIT", 2),

        self_reply_enabled=b("SELF_REPLY_ENABLED", True),
        self_reply_text=os.getenv("SELF_REPLY_TEXT", "Bookmark this. Verified links only. Beginner setup in bio.").strip(),

        template_rotation=b("TEMPLATE_ROTATION", True),
        metrics_enabled=b("METRICS_ENABLED", True),
    )
