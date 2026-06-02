"""
scraper_stealth.py — Local Stealth Scraper
Mimics Browserbase's cloud capabilities locally:
1. Navigator.webdriver fingerprint masking & stealth overrides
2. Ad, tracker, and heavyweight script blocklist (increases speed & reduces detection)
3. Randomized modern User-Agents, Viewports, and Locales
4. Smooth human-like scrolling to trigger lazy loading naturally
5. Advanced automatic cookie popup consent dismissal
6. Optional local proxy rotation support
"""
import asyncio
import os
import random
import re
import threading
from playwright.async_api import async_playwright
from markdownify import markdownify as md

# Share browser instance
_browser = None
_playwright_instance = None
_loop = None
_loop_thread = None
_loop_lock = threading.Lock()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0"
]

AD_TRACKER_DOMAINS = [
    "google-analytics.com", "googletagmanager.com", "googletagservices.com",
    "doubleclick.net", "facebook.net", "facebook.com/tr", "adnxs.com",
    "scorecardresearch.com", "hotjar.com", "crazyegg.com", "mixpanel.com",
    "optimizely.com", "adroll.com", "quantserve.com", "analytics",
    "pixel", "tracker", "telemetry", "disqus.com", "crisp.chat"
]


def _ensure_loop():
    global _loop, _loop_thread
    with _loop_lock:
        if _loop and _loop.is_running():
            return _loop
        _loop = asyncio.new_event_loop()
        _loop_thread = threading.Thread(
            target=_loop.run_forever,
            name="scout-stealth-loop",
            daemon=True,
        )
        _loop_thread.start()
        return _loop


def _run_async(coro):
    loop = _ensure_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


async def _get_or_create_browser():
    global _browser, _playwright_instance
    if _browser is not None:
        try:
            if _browser.is_connected():
                return _browser
        except Exception:
            pass
        _browser = None

    if _playwright_instance is not None:
        try:
            await _playwright_instance.stop()
        except Exception:
            pass
        _playwright_instance = None

    if _browser is None:
        _playwright_instance = await async_playwright().start()
        _browser = await _playwright_instance.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--window-size=1920,1080"
            ]
        )
    return _browser


async def close_browser():
    global _browser, _playwright_instance
    if _browser:
        try:
            if _browser.is_connected():
                await _browser.close()
        except Exception:
            pass
        _browser = None
    if _playwright_instance:
        try:
            await _playwright_instance.stop()
        except Exception:
            pass
        _playwright_instance = None


async def fetch_page(url: str, wait_for: str = None, timeout: int = 30000, retries: int = 1) -> dict:
    """
    Scrapes a page using local stealth techniques:
    1. Removes webdriver flag
    2. Overrides navigator settings
    3. Blocks ad/tracker assets to speed up
    4. Smooth human scrolling
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

    # Optional local proxy configuration (reads from environment)
    proxy = None
    proxy_url = os.environ.get("SCOUT_STEALTH_PROXY")
    if proxy_url:
        proxy = {"server": proxy_url}

    for attempt in range(retries + 1):
        context = None
        try:
            browser = await _get_or_create_browser()
            
            # Select random User-Agent and viewport
            user_agent = random.choice(USER_AGENTS)
            viewport_width = random.randint(1280, 1920)
            viewport_height = random.randint(720, 1080)
            
            context = await browser.new_context(
                user_agent=user_agent,
                viewport={"width": viewport_width, "height": viewport_height},
                locale="en-US",
                timezone_id="America/New_York",
                proxy=proxy,
                accept_downloads=False
            )

            # Block heavy media resources and ad/tracker analytics scripts
            async def route_handler(route):
                req_url = route.request.url.lower()
                if any(domain in req_url for domain in AD_TRACKER_DOMAINS):
                    return await route.abort()
                if req_url.endswith((".mp4", ".webm", ".woff", ".woff2", ".gif", ".png", ".jpg", ".jpeg", ".svg")):
                    # Block images/fonts if they are not needed for text extraction
                    return await route.abort()
                return await route.continue_()

            await context.route("**/*", route_handler)

            # Inject anti-bot detection overrides before loading
            await context.add_init_script("""
                // Mask Webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Mock Chrome environment
                window.chrome = {
                    runtime: {}
                };

                // Overwrite Notification Permissions Query
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // Mock Plugins list
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbgodfjkljgedofoilkjbhfbhaofn' },
                        { name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer' }
                    ]
                });

                // Mock Languages list
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)

            page = await context.new_page()

            # Navigate
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

            # Attempt to dismiss cookie banners
            await _dismiss_popups(page)

            # Settle network
            try:
                await page.wait_for_load_state("networkidle", timeout=1200)
            except Exception:
                pass

            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=6000)
                except Exception:
                    pass

            # Human scroll simulation
            await _human_scroll(page)

            result["title"] = await page.title()
            
            # Content extraction
            main_html = await _extract_main_content(page)
            result["raw_html"] = main_html
            result["images"] = extract_images(main_html, url)

            # Convert to markdown
            markdown = md(main_html, heading_style="ATX", strip=["script", "style", "nav", "footer", "header"])
            result["markdown"] = _clean_markdown(markdown)
            result["success"] = len(result["markdown"]) > 50

            break  # Success
            
        except Exception as e:
            result["error"] = str(e)
            if attempt < retries:
                await asyncio.sleep(1.5 * (attempt + 1))
            else:
                break
        finally:
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

    return result


async def _dismiss_popups(page):
    selectors = [
        "button:has-text('Accept')", "button:has-text('Accept All')",
        "button:has-text('Got it')", "button:has-text('I agree')",
        "button:has-text('OK')", "button:has-text('Close')",
        "[class*='cookie'] button", "[id*='cookie'] button",
        "[class*='consent'] button", "[id*='consent'] button"
    ]
    for selector in selectors:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=300):
                await btn.click(timeout=800)
                await asyncio.sleep(0.1)
                break
        except Exception:
            continue


async def _human_scroll(page):
    """Simulates a human scrolling slowly in random intervals to trigger lazy loads naturally."""
    try:
        total_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")
        current_scroll = 0
        
        while current_scroll < total_height and current_scroll < 3000:
            step = random.randint(300, 600)
            current_scroll += step
            await page.evaluate(f"window.scrollTo(0, {current_scroll})")
            await asyncio.sleep(random.uniform(0.15, 0.35))
            
            # Update height just in case lazy load expanded the page
            total_height = await page.evaluate("document.body.scrollHeight")
    except Exception:
        pass


async def _extract_main_content(page) -> str:
    for selector in ["main", "article", "[role='main']", "#content", ".content", "#main", ".main-content"]:
        try:
            el = page.locator(selector).first
            if await el.is_visible(timeout=300):
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
