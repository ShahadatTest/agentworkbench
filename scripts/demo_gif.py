"""Record the short demo animation for the README from the demo data.

    pip install playwright pillow
    AGENTWORKBENCH_DB=./demo.db python scripts/demo_seed.py
    AGENTWORKBENCH_DB=./demo.db uvicorn app:app --port 8777 &
    python scripts/demo_gif.py http://127.0.0.1:8777
"""
import io
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8777"
OUT = Path(__file__).resolve().parent.parent / "docs" / "images" / "demo.gif"
SIZE = (960, 540)
frames = []


def shot(page, ms):
    page.wait_for_timeout(250)
    img = Image.open(io.BytesIO(page.screenshot())).convert("RGB").resize(SIZE, Image.LANCZOS)
    frames.append((img, ms))


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    page = browser.new_context(viewport={"width": 1280, "height": 720}).new_page()
    page.goto(BASE + "/login")
    page.fill("input[name=password]", "demo-password-123")
    page.click("button.go")
    page.wait_for_url(BASE + "/")
    shot(page, 2200)
    page.hover(".task.urgent .box")
    shot(page, 700)
    page.click(".task.urgent .box")
    page.wait_for_url(BASE + "/")
    shot(page, 1800)
    page.click("a.proj[href='/p/dental-booking']")
    page.wait_for_load_state()
    shot(page, 2400)
    page.goto(BASE + "/briefing")
    shot(page, 2400)
    page.goto(BASE + "/search?q=restore")
    shot(page, 2200)
    browser.close()

first = frames[0][0].quantize(colors=128, method=Image.MEDIANCUT)
rest = [f.quantize(palette=first, dither=Image.NONE) for f, _ in frames[1:]]
first.save(OUT, save_all=True, append_images=rest, duration=[ms for _, ms in frames], loop=0, optimize=True)
print(OUT, OUT.stat().st_size // 1024, "KB")
