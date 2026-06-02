"""
scraper_browserbase.py — Browserbase-based page fetcher
Connects to Browserbase's headless cloud browser over Chrome DevTools Protocol (CDP)
"""
import asyncio
import os
import re
import requests
from playwright.async_api import async_playwright
from markdownify import markdownify as md


def _run_async(coro):
    """Helper to run async code synchronously."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def fetch_page(url: str, wait_for: str = None, timeout: int = 30000, retries: int = 1) -> dict:
    """
    Fetch a page using Playwright connected to Browserbase.
    """
    result = {
        "url": url,
        "title": "",
        "markdown": "",
        "raw_html": "",
        "success": False,
        "error": None,
        "images": []
    }

    api_key = os.environ.get("BROWSERBASE_API_KEY")
    if not api_key:
        result["error"] = "BROWSERBASE_API_KEY environment variable is not set"
        print("    [Browserbase] BROWSERBASE_API_KEY is not set")
        return result

    for attempt in range(retries + 1):
        browser = None
        playwright_instance = None
        try:
            print(f"    [Browserbase] Creating cloud session (attempt {attempt + 1})...")
            # 1. Create a session on Browserbase
            headers = {
                "Content-Type": "application/json",
                "X-BB-API-Key": api_key
            }
            payload = {
                "browserSettings": {
                    "solveCaptchas": True,
                    "blockAds": True
                }
            }
            
            session_resp = requests.post(
                "https://api.browserbase.com/v1/sessions",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if session_resp.status_code != 200:
                raise Exception(f"Failed to create Browserbase session: {session_resp.text}")
                
            session_data = session_resp.json()
            connect_url = session_data.get("connectUrl")
            session_id = session_data.get("id")
            
            if not connect_url:
                raise Exception("Response from api.browserbase.com did not return connectUrl")
                
            print(f"    [Browserbase] Session ID: {session_id} - Connecting over CDP...")
            
            # 2. Connect over CDP
            playwright_instance = await async_playwright().start()
            browser = await playwright_instance.chromium.connect_over_cdp(connect_url)
            
            context = browser.contexts[0]
            page = context.pages[0]
            
            print(f"    [Browserbase] Navigating to: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            
            # Dismiss cookie consent/popups
            await _dismiss_popups(page)
            
            try:
                await page.wait_for_load_state("networkidle", timeout=1000)
            except Exception:
                pass
                
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=8000)
                except Exception:
                    pass
                    
            await _auto_scroll(page)
            
            result["title"] = await page.title()
            main_html = await _extract_main_content(page)
            result["raw_html"] = main_html
            result["images"] = extract_images(main_html, url)
            
            markdown = md(main_html, heading_style="ATX", strip=["script", "style", "nav", "footer", "header"])
            result["markdown"] = _clean_markdown(markdown)
            result["success"] = len(result["markdown"]) > 50
            
            print(f"    [Browserbase] Successfully scraped {len(result['markdown'])} chars.")
            break
            
        except Exception as e:
            result["error"] = str(e)
            print(f"    [Browserbase] Scrape error on attempt {attempt + 1}: {e}")
            if attempt < retries:
                await asyncio.sleep(2 * (attempt + 1))
            else:
                break
        finally:
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            if playwright_instance:
                try:
                    await playwright_instance.stop()
                except Exception:
                    pass

    return result


async def _dismiss_popups(page):
    selectors = [
        "button:has-text('Accept')",
        "button:has-text('Accept All')",
        "button:has-text('Got it')",
        "button:has-text('I agree')",
        "button:has-text('OK')",
        "button:has-text('Close')",
        "[class*='cookie'] button",
        "[id*='cookie'] button",
    ]
    for selector in selectors:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=500):
                await btn.click(timeout=1000)
                await asyncio.sleep(0.15)
                break
        except Exception:
            continue


async def _auto_scroll(page, max_scrolls: int = 2):
    for _ in range(max_scrolls):
        try:
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(0.2)
        except Exception:
            break


async def _extract_main_content(page) -> str:
    for selector in ["main", "article", "[role='main']", "#content", ".content", "#main", ".main-content"]:
        try:
            el = page.locator(selector).first
            if await el.is_visible(timeout=500):
                html = await el.inner_html()
                if len(html) > 200:
                    return html
        except Exception:
            continue
    return await page.locator("body").inner_html()


def extract_images(html_content: str, base_url: str) -> list[dict]:
    from urllib.parse import urljoin
    images = []
    img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', html_content, re.IGNORECASE)
    alt_tags = re.findall(r'<img[^>]+alt=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
    
    for i, src in enumerate(img_tags):
        alt = alt_tags[i] if i < len(alt_tags) else ""
        if "pixel" in src.lower() or "tracker" in src.lower() or src.startswith("data:image"):
            continue
        full_url = urljoin(base_url, src)
        images.append({"url": full_url, "alt": alt})
    return images


def _clean_markdown(text: str) -> str:
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'\[[\s]*\]\(.*?\)', '', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    return text.strip()


def scrape_sync(url: str, wait_for: str = None) -> dict:
    """Synchronous wrapper for fetch_page."""
    return _run_async(fetch_page(url, wait_for))
