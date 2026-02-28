from __future__ import annotations
import re
import requests
from urllib.parse import urlparse
import tweepy

SHORTENERS = {
    "bit.ly","t.co","tinyurl.com","goo.gl","ow.ly","buff.ly","cutt.ly","is.gd","rebrand.ly","linktr.ee"
}
SOCIAL_ONLY = {"t.me","telegram.me","discord.gg","discord.com"}

def host(url: str | None) -> str | None:
    if not url:
        return None
    try:
        h = (urlparse(url).netloc or "").lower()
        if h.startswith("www."):
            h = h[4:]
        return h or None
    except Exception:
        return None

def is_https(url: str) -> bool:
    try:
        return urlparse(url).scheme.lower() == "https"
    except Exception:
        return False

def is_shortener(domain: str | None) -> bool:
    return (domain or "") in SHORTENERS

def is_social_only(domain: str | None) -> bool:
    return (domain or "") in SOCIAL_ONLY

def domain_allowed(allowlist: list[str], domain: str | None) -> bool:
    if not allowlist:
        return True
    d = (domain or "").lower()
    if not d:
        return False
    return any(d == a or d.endswith("." + a) for a in allowlist)

def fetch_html(url: str) -> str:
    r = requests.get(url, timeout=12, headers={"User-Agent":"Mozilla/5.0"})
    r.raise_for_status()
    return r.text[:400_000]

def extract_x_handle_from_html(html: str) -> str | None:
    patterns = [
        r'https?://(?:www\.)?x\.com/([A-Za-z0-9_]{2,15})(?!/status)',
        r'https?://(?:www\.)?twitter\.com/([A-Za-z0-9_]{2,15})(?!/status)',
    ]
    for p in patterns:
        m = re.search(p, html, re.IGNORECASE)
        if m:
            return m.group(1)
    return None

def user_profile_matches_domain(client: tweepy.Client, username: str, domain: str) -> bool:
    resp = client.get_user(username=username, user_fields=["description","url","entities"])
    if not resp or not resp.data:
        return False
    u = resp.data

    urls = []
    if getattr(u, "url", None):
        urls.append(u.url)
    ent = getattr(u, "entities", None) or {}
    if "url" in ent and ent["url"] and "urls" in ent["url"]:
        for x in ent["url"]["urls"]:
            if x.get("expanded_url"):
                urls.append(x["expanded_url"])

    desc = (getattr(u, "description", "") or "").lower()

    for uurl in urls:
        if domain in (host(uurl) or ""):
            return True
    if domain in desc:
        return True
    return False

def verify_official(client: tweepy.Client, official_url: str) -> tuple[bool, str | None, str | None]:
    d = host(official_url)
    if not d:
        return (False, None, None)

    try:
        html = fetch_html(official_url)
    except Exception:
        return (False, d, None)

    handle = extract_x_handle_from_html(html)
    if not handle:
        return (False, d, None)

    try:
        ok = user_profile_matches_domain(client, handle, d)
        return (ok, d, handle)
    except Exception:
        return (False, d, handle)
