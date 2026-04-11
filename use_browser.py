#!/usr/bin/env python3
"""Access the target Xiaohongshu note and extract content"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

URL = "https://www.xiaohongshu.com/discovery/item/69d24abf000000002300660d"

async def main():
    output_dir = Path("/home/leo/.openclaw/workspace/collection")
    output_dir.mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Navigating to {URL}...")
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(8)  # Wait for dynamic content
        
        # Screenshot
        screenshot_file = output_dir / "2026-04-10-163100.png"
        await page.screenshot(path=str(screenshot_file), full_page=True)
        print(f"Screenshot: {screenshot_file}")
        
        # Get all text content
        try:
            # Try to get main content
            content = await page.inner_text("body")
            text_file = output_dir / "2026-04-10-163100.txt"
            text_file.write_text(content, encoding="utf-8")
            print(f"Text saved: {text_file}")
            print(f"Content length: {len(content)} chars")
            print(f"Preview: {content[:800]}")
        except Exception as e:
            print(f"Text error: {e}")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
