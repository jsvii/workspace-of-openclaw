#!/usr/bin/env python3
"""Extract content from Xiaohongshu page using playwright"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

URL = "https://www.xiaohongshu.com/discovery/item/69d24abf000000002300660d"

async def main():
    output_dir = Path("/home/leo/.openclaw/workspace/collection")
    output_dir.mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Navigating to {URL}")
        await page.goto(URL, wait_until="networkidle", timeout=30000)
        
        # Wait for dynamic content
        await asyncio.sleep(5)
        
        # Get page content
        content = await page.content()
        
        # Save raw HTML
        html_file = output_dir / "2026-04-10-144100.html"
        html_file.write_text(content, encoding="utf-8")
        print(f"Saved HTML to {html_file}")
        
        # Try to get main text content
        try:
            # Get all text from the page
            text_content = await page.inner_text("body")
            text_file = output_dir / "2026-04-10-144100.txt"
            text_file.write_text(text_content, encoding="utf-8")
            print(f"Saved text to {text_file}")
        except Exception as e:
            print(f"Could not extract text: {e}")
        
        # Take a screenshot
        try:
            screenshot_file = output_dir / "2026-04-10-144100.png"
            await page.screenshot(path=screenshot_file, full_page=True)
            print(f"Saved screenshot to {screenshot_file}")
        except Exception as e:
            print(f"Could not take screenshot: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
