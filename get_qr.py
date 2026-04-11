#!/usr/bin/env python3
"""Generate QR code for Xiaohongshu login using playwright with xvfb"""
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    output_file = Path("/home/leo/.openclaw/workspace/collection/xhs_login.png")
    output_dir = output_file.parent
    output_dir.mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--ozone-platform=x11',  # Force X11
            ],
            env={
                'DISPLAY': os.environ.get('DISPLAY', ':99'),
                'WAYLAND_DISPLAY': '',
            }
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        page = await context.new_page()
        
        print("Navigating to Xiaohongshu (timeout=90s)...")
        try:
            await page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded", timeout=90000)
            print("Page loaded!")
        except Exception as e:
            print(f"Navigation: {e}")
        
        await asyncio.sleep(3)
        await page.screenshot(path=str(output_file))
        print(f"Screenshot: {output_file}")
        
        await browser.close()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
