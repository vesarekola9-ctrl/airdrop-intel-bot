from __future__ import annotations
import tweepy
from typing import Any

def build_query(keywords: list[str], lang: str) -> str:
    or_kw = " OR ".join([f'"{k}"' if " " in k else k for k in keywords])
    return f"({or_kw}) -is:retweet -is:reply lang:{lang}"

def search_candidates(client: tweepy.Client, keywords: list[str], lang: str, max_results: int) -> list[dict[str, Any]]:
    q = build_query(keywords, lang)
    resp = client.search_recent_tweets(
        query=q,
        max_results=min(max_results, 100),
        tweet_fields=["created_at", "text", "entities", "author_id"],
        expansions=["author_id"],
    )
    users = {u.id: u for u in (resp.includes.get("users", []) if resp and resp.includes else [])}
    out = []
    if not resp or not resp.data:
        return out

    for t in resp.data:
        u = users.get(t.author_id)
        out.append({
            "tweet_id": str(t.id),
            "text": t.text or "",
            "author_id": str(t.author_id) if t.author_id else None,
            "author_username": getattr(u, "username", None),
            "entities": getattr(t, "entities", None),
        })
    return out

def extract_best_url(candidate: dict[str, Any]) -> str | None:
    ent = candidate.get("entities") or {}
    urls = ent.get("urls") or []
    for u in urls:
        ex = u.get("expanded_url") or u.get("url")
        if ex and ex.startswith("http"):
            return ex.rstrip(").,!?")
    import re
    m = re.search(r"(https?://\S+)", candidate.get("text",""))
    if m:
        return m.group(1).rstrip(").,!?")
    return None
