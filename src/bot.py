from __future__ import annotations
import tweepy
import datetime as _dt

from src.db import (
    connect, mark_seen, has_dupe, insert_drop, mark_posted,
    inc_post_counter, get_post_counter, top_recent_drops,
    get_last_digest_day, set_last_digest_day, today_utc,
    enqueue_review, log_metric, approve_top, pop_approved, remove_from_queue
)
from src.x_search import search_candidates, extract_best_url
from src.verify import host, is_https, is_shortener, is_social_only, domain_allowed, verify_official
from src.scoring import hard_block, score as score_fn
from src.compose import build_thread, project_name_from_text, build_sponsored_thread, build_weekly_digest
from src.posting import post_thread

DAY_MAP = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


def dupe_key(name: str, domain: str | None) -> str:
    return f"{(name or '').lower().strip()}::{(domain or 'unknown').lower().strip()}"


def should_add_cta(cfg, conn) -> bool:
    if not cfg.link_hub_url:
        return False
    counter = get_post_counter(conn)
    return ((counter + 1) % cfg.cta_every_n_posts) == 0


def cta_line(cfg) -> str | None:
    if not cfg.link_hub_url:
        return None
    return (cfg.cta_text + " " + cfg.link_hub_url).strip()


def make_clients(cfg) -> tuple[tweepy.Client, tweepy.Client, tweepy.API]:
    """
    read_client: bearer-token (search, lookups)
    write_client: OAuth1 user context (create_tweet)
    api_v1: OAuth1 for media upload (v1.1)
    """
    if not cfg.bearer:
        raise ValueError("Missing X_BEARER_TOKEN")

    # Read/search client (app-only)
    read_client = tweepy.Client(bearer_token=cfg.bearer, wait_on_rate_limit=True)

    # Write client (user context) -> REQUIRED for posting
    if not (cfg.api_key and cfg.api_secret and cfg.access_token and cfg.access_secret):
        raise ValueError("Missing OAuth1 keys (X_API_KEY/X_API_SECRET/X_ACCESS_TOKEN/X_ACCESS_SECRET)")

    write_client = tweepy.Client(
        consumer_key=cfg.api_key,
        consumer_secret=cfg.api_secret,
        access_token=cfg.access_token,
        access_token_secret=cfg.access_secret,
        wait_on_rate_limit=True,
    )

    auth = tweepy.OAuth1UserHandler(cfg.api_key, cfg.api_secret, cfg.access_token, cfg.access_secret)
    api_v1 = tweepy.API(auth)

    return read_client, write_client, api_v1


def maybe_post_weekly_digest(cfg, conn, write_client, api_v1):
    if not cfg.weekly_digest:
        return

    now = _dt.datetime.now(_dt.timezone.utc)
    target = DAY_MAP.get(cfg.weekly_digest_day, 0)
    if now.weekday() != target:
        return

    last = get_last_digest_day(conn)
    today = today_utc()
    if last == today:
        return

    rows = top_recent_drops(conn, limit=8)
    if not rows:
        return

    digest = build_weekly_digest(rows, cfg.account_tag, cta_line(cfg))
    if cfg.dry_run:
        print("\n--- WEEKLY DIGEST PREVIEW ---")
        for t in digest:
            print(t, "\n")
        set_last_digest_day(conn, today)
        return

    root_id = post_thread(
        write_client, api_v1, digest,
        cfg.card_title, "WEEKLY DIGEST", cfg.card_footer,
        self_reply_enabled=False, self_reply_text=""
    )
    set_last_digest_day(conn, today)
    inc_post_counter(conn)
    if cfg.metrics_enabled:
        log_metric(conn, "weekly_digest_posted", root_id)
    print(f"Posted weekly digest root: {root_id}")


def run(cfg) -> int:
    try:
        read_client, write_client, api_v1 = make_clients(cfg)
    except Exception as e:
        print(str(e))
        return 2

    conn = connect()

    maybe_post_weekly_digest(cfg, conn, write_client, api_v1)

    # Sponsored mode
    if cfg.sponsored_mode and cfg.sponsored_project and cfg.sponsored_official_url:
        cta = cta_line(cfg) if should_add_cta(cfg, conn) else None
        thread = build_sponsored_thread(
            cfg.sponsored_title, cfg.sponsored_project, cfg.sponsored_official_url,
            cfg.sponsored_note, cfg.sponsored_tag, cfg.account_tag, cta
        )
        print("\n--- SPONSORED THREAD PREVIEW ---")
        for t in thread:
            print(t, "\n")

        if cfg.dry_run:
            inc_post_counter(conn)
            if cfg.metrics_enabled:
                log_metric(conn, "sponsored_dry_run", cfg.sponsored_project)
            return 0

        root_id = post_thread(
            write_client, api_v1, thread,
            cfg.card_title, f"{cfg.sponsored_project} | SPONSORED", cfg.card_footer,
            cfg.self_reply_enabled, cfg.self_reply_text
        )
        inc_post_counter(conn)
        if cfg.metrics_enabled:
            log_metric(conn, "sponsored_posted", root_id)
        print(f"Posted sponsored root: {root_id}")
        return 0

    candidates = search_candidates(read_client, cfg.keywords, cfg.lang, cfg.results_per_run)
    print(f"Found {len(candidates)} candidates")

    posted = 0
    queued = 0
    rejected = 0

    for c in candidates:
        tid = c["tweet_id"]
        if not mark_seen(conn, tid):
            continue

        text = c["text"]
        if hard_block(text):
            rejected += 1
            if cfg.metrics_enabled:
                log_metric(conn, "reject_hard_block", tid)
            continue

        url = extract_best_url(c)
        if not url:
            rejected += 1
            if cfg.metrics_enabled:
                log_metric(conn, "reject_no_url", tid)
            continue

        d = host(url)

        if cfg.require_https and not is_https(url):
            rejected += 1
            if cfg.metrics_enabled:
                log_metric(conn, "reject_not_https", url)
            continue
        if cfg.block_shorteners and is_shortener(d):
            rejected += 1
            if cfg.metrics_enabled:
                log_metric(conn, "reject_shortener", d or "")
            continue
        if cfg.reject_social_only and is_social_only(d):
            rejected += 1
            if cfg.metrics_enabled:
                log_metric(conn, "reject_social_only", d or "")
            continue
        if not domain_allowed(cfg.allowlist_domains, d):
            rejected += 1
            if cfg.metrics_enabled:
                log_metric(conn, "reject_allowlist", d or "")
            continue

        # verify uses read_client (lookups)
        verified, domain, handle = verify_official(read_client, url)

        name = project_name_from_text(text)
        key = dupe_key(name, domain)

        if has_dupe(conn, key):
            rejected += 1
            if cfg.metrics_enabled:
                log_metric(conn, "reject_dupe", key)
            continue

        sc = score_fn(text, url, verified)

        if cfg.only_verified and not verified:
            if sc >= cfg.queue_min_score:
                enqueue_review(conn, key, name, url, domain, verified, sc, "not_verified", tid, text)
                queued += 1
                if cfg.metrics_enabled:
                    log_metric(conn, "queued_not_verified", f"{name}|{sc}")
            else:
                rejected += 1
                if cfg.metrics_enabled:
                    log_metric(conn, "reject_not_verified_low", f"{name}|{sc}")
            continue

        min_needed = cfg.min_score_verified if verified else cfg.min_score_unverified
        if sc < min_needed:
            if sc >= cfg.queue_min_score:
                enqueue_review(conn, key, name, url, domain, verified, sc, f"below_threshold({min_needed})", tid, text)
                queued += 1
                if cfg.metrics_enabled:
                    log_metric(conn, "queued_below_threshold", f"{name}|{sc}")
            else:
                rejected += 1
                if cfg.metrics_enabled:
                    log_metric(conn, "reject_low_score", f"{name}|{sc}")
            continue

        if not cfg.auto_post:
            enqueue_review(conn, key, name, url, domain, verified, sc, "auto_post_disabled", tid, text)
            queued += 1
            if cfg.metrics_enabled:
                log_metric(conn, "queued_auto_disabled", f"{name}|{sc}")
            continue

        drop_id = insert_drop(conn, key, name, url, domain, verified, sc)
        cta = cta_line(cfg) if should_add_cta(cfg, conn) else None
        thread = build_thread(name, url, sc, verified, handle, cfg.account_tag, cta, cfg.template_rotation)

        print("\n--- THREAD PREVIEW ---")
        for t in thread:
            print(t, "\n")

        if cfg.dry_run:
            inc_post_counter(conn)
            posted += 1
            if cfg.metrics_enabled:
                log_metric(conn, "dry_run_post", f"{name}|{sc}")
            if posted >= cfg.max_posts_per_run:
                break
            continue

        # posting uses write_client
        root_id = post_thread(
            write_client, api_v1, thread,
            cfg.card_title, f"{name} | {'VERIFIED' if verified else 'WATCH'}", cfg.card_footer,
            cfg.self_reply_enabled, cfg.self_reply_text
        )
        mark_posted(conn, drop_id, root_id)
        inc_post_counter(conn)
        posted += 1
        if cfg.metrics_enabled:
            log_metric(conn, "posted", f"{name}|{root_id}|{sc}")
        print(f"Posted root: {root_id}")

        if posted >= cfg.max_posts_per_run:
            break

    print(f"Run done. Posted(or would post) {posted} | queued {queued} | rejected {rejected}")
    return 0


def approve_and_post(cfg) -> int:
    try:
        read_client, write_client, api_v1 = make_clients(cfg)
    except Exception as e:
        print(str(e))
        return 2

    conn = connect()

    approve_top(conn, cfg.approve_post_limit)
    rows = pop_approved(conn, cfg.approve_post_limit)

    if not rows:
        print("No approved items to post.")
        return 0

    posted = 0
    for r in rows:
        name = r["name"]
        url = r["official_url"]
        verified = bool(r["verified"])
        sc = int(r["score"])

        if cfg.only_verified and not verified:
            remove_from_queue(conn, int(r["id"]))
            if cfg.metrics_enabled:
                log_metric(conn, "approve_skip_not_verified", name)
            continue

        cta = cta_line(cfg) if should_add_cta(cfg, conn) else None
        thread = build_thread(name, url, sc, verified, None, cfg.account_tag, cta, cfg.template_rotation)

        print("\n--- APPROVED THREAD PREVIEW ---")
        for t in thread:
            print(t, "\n")

        if cfg.dry_run:
            inc_post_counter(conn)
            remove_from_queue(conn, int(r["id"]))
            posted += 1
            if cfg.metrics_enabled:
                log_metric(conn, "approve_dry_run_post", f"{name}|{sc}")
            continue

        root_id = post_thread(
            write_client, api_v1, thread,
            cfg.card_title, f"{name} | {'VERIFIED' if verified else 'WATCH'}", cfg.card_footer,
            cfg.self_reply_enabled, cfg.self_reply_text
        )

        drop_id = insert_drop(conn, r["dupe_key"], name, url, r["official_domain"], verified, sc)
        mark_posted(conn, drop_id, root_id)

        inc_post_counter(conn)
        remove_from_queue(conn, int(r["id"]))
        posted += 1
        if cfg.metrics_enabled:
            log_metric(conn, "approve_posted", f"{name}|{root_id}|{sc}")

        print(f"Posted approved root: {root_id}")

    print(f"Approve flow done. Posted {posted}")
    return 0
