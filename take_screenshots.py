import asyncio
from playwright.async_api import async_playwright
import os

BASE = "https://gramgpt-backend-v2.onrender.com/mini-app"
OUT = "src/api/static/landing/images"
os.makedirs(OUT, exist_ok=True)

PAGES = [
    ("dashboard", "dashboard.html", "#dashboard-metrics", 1200, 800),
    ("commenting", "commenting.html", ".card", 1200, 800),
    ("dialogs", "dialogs.html", ".card", 1200, 800),
    ("accounts", "accounts.html", ".card", 1200, 800),
    ("analytics", "dashboard.html", "#revenue-chart", 1200, 800),
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 430, "height": 932},
            device_scale_factor=2,
        )
        for name, page_path, selector, w, h in PAGES:
            page = await context.new_page()
            url = f"{BASE}/{page_path}"
            print(f"Opening {url}...")
            try:
                await page.goto(url, timeout=30000, wait_until="networkidle")
                await asyncio.sleep(2)
                # Wait for content
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                except:
                    pass
                await asyncio.sleep(1)
                filepath = os.path.join(OUT, f"screenshot-{name}.png")
                await page.screenshot(path=filepath, full_page=True)
                print(f"  Saved {filepath} ({os.path.getsize(filepath)} bytes)")
            except Exception as e:
                print(f"  FAILED: {e}")
            finally:
                await page.close()
        await browser.close()

asyncio.run(main())
