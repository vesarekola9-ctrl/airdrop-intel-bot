import random

TEMPLATES = [
    {"t2":"✅ Steps:\n1) Open official link\n2) Read quests/requirements\n3) Complete tasks\n4) Track snapshot/claim",
     "t3":"🛡️ Safety:\n• Never share seed/private key\n• Never pay 'fees'\n• Avoid fake domains",
     "t4":"If you found this useful: bookmark + follow {tag} for VERIFIED drops."},
    {"t2":"Quick guide:\n1) Official link\n2) Quests / points\n3) Do tasks\n4) Save this thread for updates",
     "t3":"Safety check:\n• Domain must match official\n• No upfront payments\n• Separate wallet recommended",
     "t4":"More verified intel daily → {tag}"},
    {"t2":"Action list:\n1) Visit official site\n2) Find campaign page\n3) Complete quests\n4) Watch for snapshot/claim",
     "t3":"Do NOT:\n• Share seed/private key\n• Click lookalike domains\n• Pay activation fees",
     "t4":"Bookmark + follow {tag}."},
    {"t2":"What to do:\n1) Official link\n2) Confirm tasks\n3) Collect points\n4) Track deadlines",
     "t3":"Risk control:\n• Use burner wallet\n• Verify X profile\n• Avoid DMs & fees",
     "t4":"Verified drops only. Follow {tag}."},
    {"t2":"Checklist:\n1) Official link\n2) Docs/blog confirmation\n3) Do quests\n4) Monitor claim updates",
     "t3":"Security:\n• Never sign weird approvals\n• Revoke permissions later\n• No seed phrases ever",
     "t4":"Follow {tag} for daily verified threads."},
    {"t2":"Steps (fast):\n1) Open official\n2) Complete campaign tasks\n3) Track snapshot\n4) Wait for claim info",
     "t3":"Safety (fast):\n• No fees\n• No seeds\n• Correct domain only",
     "t4":"Save + follow {tag}."},
    {"t2":"How to farm:\n1) Official link\n2) Join quests\n3) Do tasks\n4) Keep notes for claim",
     "t3":"Safety notes:\n• Separate wallet\n• Small tx sizes\n• Verify domain",
     "t4":"More intel → {tag}"},
    {"t2":"Do this:\n1) Use official link\n2) Read requirements\n3) Complete tasks\n4) Track updates",
     "t3":"Avoid scams:\n• No upfront payments\n• No seed/private key\n• No fake domains",
     "t4":"Follow {tag} + bookmark."},
]

def pick_template(rotation: bool) -> dict:
    return random.choice(TEMPLATES) if rotation else TEMPLATES[0]
