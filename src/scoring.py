import re

BLOCK_PATTERNS = [
    "seed phrase", "private key", "send usdt", "send eth", "activation fee",
    "processing fee", "gift card", "guaranteed profit"
]

GOOD_HINTS = ["docs", "official", "blog", "github", "mirror", "snapshot", "quest", "points"]

def hard_block(text: str) -> bool:
    t = (text or "").lower()
    return any(p in t for p in BLOCK_PATTERNS)

def score(text: str, official_url: str | None, verified: bool) -> int:
    t = (text or "").lower()
    s = 50

    if verified:
        s += 20

    for h in GOOD_HINTS:
        if h in t:
            s += 6

    if official_url and official_url.startswith("https://"):
        s += 5

    if len(re.sub(r"\s+", " ", t)) > 220:
        s += 8

    if "dm" in t and "link" not in t:
        s -= 8

    return max(0, min(100, s))
