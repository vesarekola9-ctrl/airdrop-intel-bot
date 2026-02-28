from src.templates import pick_template

def project_name_from_text(text: str) -> str:
    words = (text or "").split()
    for w in words[:10]:
        if w.isupper() and 3 <= len(w) <= 18:
            return w[:18]
    return (words[0] if words else "PROJECT")[:18]

def build_thread(name: str, official_url: str, score: int, verified: bool, handle: str | None,
                 account_tag: str, cta_line: str | None, template_rotation: bool) -> list[str]:
    badge = "VERIFIED ✅" if verified else "UNVERIFIED ⚠️"
    h = f" (via @{handle})" if handle else ""

    t = pick_template(template_rotation)

    t1 = f"🪂 {name} — {badge}{h}\nScore: {score}/100\nOfficial: {official_url}"
    t2 = t["t2"]
    t3 = t["t3"]
    t4 = t["t4"].format(tag=account_tag)

    if cta_line:
        t4 = (t4 + "\n\n" + cta_line).strip()

    return [x[:275] for x in [t1, t2, t3, t4]]

def build_sponsored_thread(title: str, project: str, official_url: str, note: str, tag: str,
                          account_tag: str, cta_line: str | None) -> list[str]:
    t1 = f"⭐ {title} — {project}\n{tag}\nOfficial: {official_url}"
    t2 = f"Why featured: {note[:180]}"
    t3 = "🛡️ Safety:\n• Never share seed/private key\n• Never pay 'fees'\n• Use only official links"
    t4 = f"Follow {account_tag} for VERIFIED drops + weekly digests."
    if cta_line:
        t4 = (t4 + "\n\n" + cta_line).strip()
    return [x[:275] for x in [t1, t2, t3, t4]]

def build_weekly_digest(rows, account_tag: str, cta_line: str | None) -> list[str]:
    root = f"🗓️ Weekly Airdrop Intel Digest\nTop recent VERIFIED threads & links.\nFollow {account_tag}."
    lines = []
    for r in rows:
        badge = "✅" if int(r["verified"]) == 1 else "⚠️"
        lines.append(f"{badge} {r['name']} ({r['score']}/100) {r['official_url']}")
    body = "\n".join(lines)[:270]
    if cta_line:
        body = (body + "\n\n" + cta_line)[:275]
    return [root[:275], body]
