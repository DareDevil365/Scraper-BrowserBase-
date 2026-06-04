"""
scraper.py — Unified Universal Scraper
Handles: standard local Playwright, local Stealth Playwright, and Cloud Browserbase.
Optimized: shared event loop and browser instance reuse, auto-routing fallback, and media config.
"""
import asyncio
import atexit
import hashlib
import json
import os
import random
import re
import threading
import time
import requests
from playwright.async_api import async_playwright
from markdownify import markdownify as md

# Shared local browser instance for reuse
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
    """Create one long-lived event loop for local Playwright work."""
    global _loop, _loop_thread
    with _loop_lock:
        if _loop and _loop.is_running():
            return _loop

        _loop = asyncio.new_event_loop()
        _loop_thread = threading.Thread(
            target=_loop.run_forever,
            name="scout-playwright-loop",
            daemon=True,
        )
        _loop_thread.start()
        return _loop


def _run_async(coro):
    """Run an async scraper coroutine on the shared Playwright loop."""
    loop = _ensure_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


async def _get_or_create_browser():
    """Get or create a shared browser instance to avoid repeated Chromium launches."""
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
                "--disable-infobars"
            ]
        )
    return _browser


async def close_browser():
    """Close the shared browser when done."""
    global _browser, _playwright_instance
    if _browser:
        try:
            if _browser.is_connected():
                await _browser.close()
        except Exception as e:
            print(f"    Browser close failed: {e}")
        _browser = None
    if _playwright_instance:
        try:
            await _playwright_instance.stop()
        except Exception as e:
            print(f"    Playwright stop failed: {e}")
        _playwright_instance = None


def _is_bot_blocked(title: str, markdown: str) -> bool:
    """Helper to detect standard anti-bot protection screens."""
    title_lower = title.lower() if title else ""
    content_lower = markdown.lower() if markdown else ""
    blocked_keywords = [
        "cloudflare", "just a moment", "attention required", "access denied", 
        "security check", "ddos guard", "bot check", "human verification", 
        "captcha", "robot check"
    ]
    return any(kw in title_lower or kw in content_lower for kw in blocked_keywords)


async def _fetch_browserbase(url: str, wait_for: str, timeout: int, block_media: bool) -> dict:
    """Fetcher logic specifically targeting Browserbase CDP."""
    result = {
        "title": "",
        "markdown": "",
        "raw_html": "",
        "success": False,
        "error": None,
        "images": [],
        "scraped_by": "browserbase"
    }

    api_key = os.environ.get("BROWSERBASE_API_KEY")
    if not api_key:
        result["error"] = "BROWSERBASE_API_KEY environment variable is not set"
        return result

    browser = None
    playwright_instance = None
    try:
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
        
        if not connect_url:
            raise Exception("Response from api.browserbase.com did not return connectUrl")
            
        playwright_instance = await async_playwright().start()
        browser = await playwright_instance.chromium.connect_over_cdp(connect_url)
        
        context = browser.contexts[0]
        page = context.pages[0]
        
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
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
        
    except Exception as e:
        result["error"] = str(e)
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


async def _fetch_page_raw(url: str, wait_for: str, timeout: int, method: str, block_media: bool) -> dict:
    """Raw page fetcher for a specific method (standard, stealth, or browserbase)."""
    result = {
        "title": "",
        "markdown": "",
        "raw_html": "",
        "success": False,
        "error": None,
        "images": [],
        "scraped_by": method
    }

    if method == "browserbase":
        return await _fetch_browserbase(url, wait_for, timeout, block_media)

    # Local Playwright (Stealth or Standard)
    context = None
    try:
        browser = await _get_or_create_browser()
        
        if method == "stealth":
            user_agent = random.choice(USER_AGENTS)
            viewport_width = random.randint(1280, 1920)
            viewport_height = random.randint(720, 1080)
            
            proxy = None
            proxy_url = os.environ.get("SCOUT_STEALTH_PROXY")
            if proxy_url:
                proxy = {"server": proxy_url}

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
                if block_media and req_url.endswith((".mp4", ".webm", ".woff", ".woff2", ".gif", ".png", ".jpg", ".jpeg", ".svg")):
                    return await route.abort()
                return await route.continue_()

            await context.route("**/*", route_handler)

            # Inject anti-bot detection overrides
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbgodfjkljgedofoilkjbhfbhaofn' },
                        { name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer' }
                    ]
                });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            """)
        else:
            # Standard local Playwright context
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            # Route filters
            if block_media:
                await context.route("**/*.{mp4,webm,woff,woff2,gif,png,jpg,jpeg,svg}", lambda route: route.abort())
            else:
                await context.route("**/*.{mp4,webm,woff,woff2}", lambda route: route.abort())

        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        
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

        if method == "stealth":
            await _human_scroll(page)
        else:
            await _auto_scroll(page)

        result["title"] = await page.title()
        main_html = await _extract_main_content(page)
        result["raw_html"] = main_html
        result["images"] = extract_images(main_html, url)

        markdown = md(main_html, heading_style="ATX", strip=["script", "style", "nav", "footer", "header"])
        result["markdown"] = _clean_markdown(markdown)
        result["success"] = len(result["markdown"]) > 50

    except Exception as e:
        result["error"] = str(e)
    finally:
        if context:
            try:
                await context.close()
            except Exception:
                pass

    return result


def _get_cache_dir() -> str:
    """Get path to outputs/.scraped_cache/ directory."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", ".scraped_cache")


def _get_cache_file_path(url: str) -> str:
    """Compute MD5 hash of URL and return cache JSON path."""
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    return os.path.join(_get_cache_dir(), f"{url_hash}.json")


def _read_from_cache(url: str, cache_ttl: int) -> dict:
    """Read cached scrape result if it exists and is not stale."""
    try:
        cache_path = _get_cache_file_path(url)
        if not os.path.exists(cache_path):
            return None

        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        timestamp = data.get("timestamp", 0)
        # Check if the cache is stale
        if time.time() - timestamp > cache_ttl:
            return None

        result = data.get("result")
        if result:
            result["scraped_by"] = result.get("scraped_by", "unknown") + " (cached)"
            return result
    except Exception as e:
        print(f"    [Scraper Cache] Failed to read cache: {e}")
    return None


def _write_to_cache(url: str, result: dict):
    """Write scrape result to disk cache atomically."""
    try:
        cache_dir = _get_cache_dir()
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = _get_cache_file_path(url)

        data = {
            "timestamp": time.time(),
            "result": result
        }

        # Use an atomic write via temp file rename to prevent concurrency/crash issues
        temp_path = f"{cache_path}.tmp_{random.randint(0, 1000000)}"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, cache_path)
    except Exception as e:
        print(f"    [Scraper Cache] Failed to write cache: {e}")


async def fetch_page(
    url: str, 
    wait_for: str = None, 
    timeout: int = 30000, 
    retries: int = 1,
    method: str = "auto",
    block_media: bool = True,
    bypass_cache: bool = False,
    cache_ttl: int = 259200
) -> dict:
    """
    Fetch a page using Playwright with optional Stealth, Cloud Browserbase, or Standard backends.
    Handles dynamic routing and auto-fallback when bot checks are encountered.
    """
    if not bypass_cache:
        cached = _read_from_cache(url, cache_ttl)
        if cached:
            print(f"    [Scraper Cache] Cache hit for {url}")
            return cached

    result = {
        "url": url,
        "title": "",
        "markdown": "",
        "raw_html": "",
        "success": False,
        "error": None,
        "images": [],
        "scraped_by": ""
    }

    target_method = method.lower().strip() if method else "auto"

    for attempt in range(retries + 1):
        current_method = target_method
        if target_method == "auto":
            current_method = "stealth"

        try:
            print(f"    [Scraper] Fetching {url} via {current_method} (attempt {attempt + 1})...")
            attempt_res = await _fetch_page_raw(url, wait_for, timeout, current_method, block_media)
            
            # Check for bot block
            if attempt_res["success"] and _is_bot_blocked(attempt_res["title"], attempt_res["markdown"]):
                print(f"    [Scraper] Bot block detected for {url} using {current_method}.")
                
                api_key = os.environ.get("BROWSERBASE_API_KEY")
                if target_method == "auto" and current_method == "stealth" and api_key:
                    print(f"    [Scraper] BROWSERBASE_API_KEY is configured. Falling back to Browserbase Cloud...")
                    attempt_res = await _fetch_page_raw(url, wait_for, timeout, "browserbase", block_media)
                else:
                    print(f"    [Scraper] Falling back to standard local Playwright...")
                    attempt_res = await _fetch_page_raw(url, wait_for, timeout, "standard", block_media)

            if attempt_res["success"]:
                result.update(attempt_res)
                _write_to_cache(url, result)
                break
            
            result["error"] = attempt_res["error"]
            if attempt < retries:
                await asyncio.sleep(2 * (attempt + 1))
                
        except Exception as e:
            result["error"] = str(e)
            print(f"    [Scraper] Attempt {attempt + 1} failed: {e}")
            if attempt < retries:
                await asyncio.sleep(2 * (attempt + 1))
            else:
                break

    return result


async def fetch_multiple(urls: list[str], callback=None) -> list[dict]:
    """Fetch multiple pages sequentially using shared browser."""
    results = []
    for i, url in enumerate(urls):
        result = await fetch_page(url)
        if callback:
            await callback(i, len(urls), result)
        results.append(result)
    return results


async def _dismiss_popups(page):
    """Try to click common cookie/consent dismiss buttons."""
    selectors = [
        "button:has-text('Accept')",
        "button:has-text('Accept All')",
        "button:has-text('Got it')",
        "button:has-text('I agree')",
        "button:has-text('OK')",
        "button:has-text('Close')",
        "[class*='cookie'] button",
        "[id*='cookie'] button",
        "[class*='consent'] button",
        "[id*='consent'] button"
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


async def _auto_scroll(page, max_scrolls: int = 2):
    """Scroll down to trigger lazy-loaded content."""
    for _ in range(max_scrolls):
        try:
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(0.2)
        except Exception:
            break


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
            total_height = await page.evaluate("document.body.scrollHeight")
    except Exception:
        pass


async def _extract_main_content(page) -> str:
    """Extract the most relevant content area from the page."""
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
    """Extract all relevant image URLs and alt text from HTML."""
    from urllib.parse import urljoin
    images = []
    
    img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', html_content, re.IGNORECASE)
    alt_tags = re.findall(r'<img[^>]+alt=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
    
    for i, src in enumerate(img_tags):
        alt = alt_tags[i] if i < len(alt_tags) else ""
        if "pixel" in src.lower() or "tracker" in src.lower() or src.startswith("data:image"):
            continue
            
        full_url = urljoin(base_url, src)
        images.append({
            "url": full_url,
            "alt": alt
        })
    return images


def _clean_markdown(text: str) -> str:
    """Clean up markdown output — remove excessive whitespace, empty links, etc."""
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'\[[\s]*\]\(.*?\)', '', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    return text.strip()


def scrape_sync(url: str, wait_for: str = None) -> dict:
    """Synchronous wrapper for fetch_page."""
    return _run_async(fetch_page(url, wait_for))


async def fetch_youtube_search_async(query: str, max_results: int = 5) -> list[dict]:
    """Scrape YouTube search results. Try browserless HTTP request first, then fall back to Playwright browser context."""
    import urllib.parse
    import re
    import json
    import time
    import requests
    
    # Method 1: Browserless HTTP requests (extremely fast, lightweight, and headless-friendly)
    try:
        print(f"    [Scraper] Searching YouTube for '{query}' browserlessly via HTTP requests...")
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        response = requests.get(url, headers=headers, timeout=12)
        if response.status_code == 200:
            html = response.text
            json_match = re.search(r'var ytInitialData\s*=\s*({.*?});', html)
            if not json_match:
                json_match = re.search(r'window\["ytInitialData"\]\s*=\s*({.*?});', html)
                
            if json_match:
                data = json.loads(json_match.group(1))
                videos = []
                section_contents = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
                for section in section_contents:
                    if 'itemSectionRenderer' in section:
                        items = section['itemSectionRenderer']['contents']
                        for item in items:
                            if 'videoRenderer' in item:
                                vr = item['videoRenderer']
                                video_id = vr.get('videoId')
                                if not video_id:
                                    continue
                                    
                                title = ""
                                try:
                                    title = vr['title']['runs'][0]['text']
                                except Exception:
                                    pass
                                    
                                channel = ""
                                try:
                                    channel = vr['ownerText']['runs'][0]['text']
                                except Exception:
                                    pass
                                    
                                description = ""
                                try:
                                    description = "".join([run.get('text', '') for run in vr['descriptionSnippet']['runs']])
                                except Exception:
                                    pass
                                    
                                views_text = ""
                                view_count = 0
                                try:
                                    views_text = vr['viewCountText']['simpleText']
                                    match = re.search(r'([\d,]+)\s*views?', views_text.lower())
                                    if match:
                                        view_count = int(match.group(1).replace(",", ""))
                                except Exception:
                                    try:
                                        views_text = vr['shortViewCountText']['simpleText']
                                    except Exception:
                                        pass
                                
                                videos.append({
                                    "id": video_id,
                                    "url": f"https://www.youtube.com/watch?v={video_id}",
                                    "title": title,
                                    "channel": channel,
                                    "description": description,
                                    "views_text": views_text,
                                    "view_count": view_count
                                })
                                
                                if len(videos) >= max_results:
                                    print(f"    [Scraper] Browserless HTTP search succeeded. Found {len(videos)} videos.")
                                    return videos
                                    
                if videos:
                    print(f"    [Scraper] Browserless HTTP search succeeded. Found {len(videos)} videos.")
                    return videos
        print("    [Scraper] Browserless HTTP YouTube search did not return results. Falling back to Playwright...")
    except Exception as e:
        print(f"    [Scraper] Browserless HTTP YouTube search failed: {e}. Falling back to Playwright...")

    # Method 2: Playwright Browser Fallback (if HTTP method failed or blocked)
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    context = None
    try:
        browser = await _get_or_create_browser()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        
        # Block heavy resources and tracking scripts to optimize search loading speed
        async def route_handler(route):
            req_url = route.request.url.lower()
            if any(domain in req_url for domain in AD_TRACKER_DOMAINS):
                return await route.abort()
            if req_url.endswith((".mp4", ".webm", ".woff", ".woff2", ".gif", ".png", ".jpg", ".jpeg", ".svg")):
                return await route.abort()
            return await route.continue_()

        await context.route("**/*", route_handler)
        
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="commit", timeout=20000)
        except Exception as e:
            print(f"    [Scraper] YouTube initial goto commit failed: {e}")
            
        start_time = time.time()
        loaded = False
        while time.time() - start_time < 20:
            current_url = page.url
            if "consent.youtube.com" in current_url:
                print("    [Scraper] YouTube redirect to consent page detected. Dismissing...")
                for selector in ["button:has-text('Accept all')", "button:has-text('I agree')", "button:has-text('Agree')", "button[aria-label*='Accept']"]:
                    try:
                        btn = page.locator(selector).first
                        if await btn.is_visible(timeout=1000):
                            await btn.click()
                            print("    [Scraper] Consent clicked, waiting for page redirect...")
                            await asyncio.sleep(2)
                            break
                    except Exception:
                        continue
            
            try:
                if await page.locator("ytd-video-renderer").first.is_visible(timeout=500):
                    loaded = True
                    break
            except Exception:
                pass
            
            await asyncio.sleep(0.5)
            
        if not loaded:
            print("    [Scraper] YouTube results failed to load selector 'ytd-video-renderer'")
            return []
            
        results = await page.evaluate("""(max_res) => {
            const videos = [];
            const renderers = document.querySelectorAll('ytd-video-renderer');
            for (let i = 0; i < Math.min(renderers.length, max_res); i++) {
                const el = renderers[i];
                const titleEl = el.querySelector('a#video-title');
                if (!titleEl) continue;
                
                const title = titleEl.innerText.trim();
                const href = titleEl.getAttribute('href');
                const url = href ? 'https://www.youtube.com' + href : '';
                
                const channelEl = el.querySelector('#channel-info ytd-channel-name a') || el.querySelector('#channel-name a');
                const channel = channelEl ? channelEl.innerText.trim() : '';
                
                const metaSpans = el.querySelectorAll('#metadata-line span.inline-metadata-item');
                const viewsText = metaSpans.length > 0 ? metaSpans[0].innerText.trim() : '';
                
                videos.push({ title, url, channel, description: '', views_text: viewsText });
            }
            return videos;
        }""", max_results)
        
        # Post-process views and extract video IDs in Python
        for r in results:
            views = 0
            views_text = r["views_text"]
            match = re.search(r'([\d.,]+)\s*([KMBkmb]?)(?:\s*views?)?', views_text, re.IGNORECASE)
            if match:
                num_str = match.group(1).replace(",", "")
                suffix = match.group(2).upper()
                try:
                    val = float(num_str)
                    if suffix == 'K':
                        val *= 1000
                    elif suffix == 'M':
                        val *= 1000000
                    elif suffix == 'B':
                        val *= 1000000000
                    views = int(val)
                except ValueError:
                     pass
            r["view_count"] = views
            
            # Extract video ID
            vid_id = ""
            vid_url = r["url"]
            vid_match = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11})', vid_url)
            if vid_match:
                vid_id = vid_match.group(1)
            r["id"] = vid_id
            
        return results
    except Exception as e:
        print(f"    [Scraper] Browser YouTube search failed: {e}")
        return []
    finally:
        if context:
            try:
                await context.close()
            except Exception:
                pass


def scrape_youtube_search_sync(query: str, max_results: int = 5) -> list[dict]:
    """Synchronous wrapper for fetch_youtube_search_async."""
    return _run_async(fetch_youtube_search_async(query, max_results))


def _shutdown_loop():
    global _loop
    if not _loop or not _loop.is_running():
        return
    try:
        asyncio.run_coroutine_threadsafe(close_browser(), _loop).result(timeout=10)
    except Exception:
        pass
    try:
        _loop.call_soon_threadsafe(_loop.stop)
    except Exception:
        pass


atexit.register(_shutdown_loop)
