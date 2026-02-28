from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from datetime import datetime

def make_card(title: str, project: str, footer: str) -> Path:
    out = Path("data")
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"card_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"

    W, H = 1200, 675
    img = Image.new("RGB", (W, H), (12, 12, 16))
    d = ImageDraw.Draw(img)

    try:
        big = ImageFont.truetype("DejaVuSans.ttf", 64)
        mid = ImageFont.truetype("DejaVuSans.ttf", 52)
        sm = ImageFont.truetype("DejaVuSans.ttf", 28)
    except Exception:
        big = mid = sm = ImageFont.load_default()

    d.text((70, 70), title, font=big, fill=(245,245,250))
    d.text((70, 260), project, font=mid, fill=(120,255,200))
    d.text((70, 600), footer, font=sm, fill=(200,200,210))

    img.save(path, "PNG")
    return path
