import asyncio
from playwright.async_api import async_playwright
from engine.scraper import _extract_main_content

async def run_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # HTML containing boilerplate classes (cookie consent, share, newsletter, footer, header)
        test_html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <header>This is header</header>
            <nav>Navigation links</nav>
            <main>
                <h1>Main Heading</h1>
                <p>This is the actual relevant content of the page.</p>
                <div class="cookie-banner">Cookie consent button accept</div>
                <div class="social-share">Share on facebook</div>
                <div class="newsletter-signup">Sign up to our newsletter</div>
            </main>
            <footer class="footer">This is footer</footer>
        </body>
        </html>
        """
        
        # Load the HTML content
        await page.set_content(test_html)
        
        # Call extract main content which executes the DOM pruner
        pruned_html = await _extract_main_content(page)
        
        print("Pruned HTML:\n", pruned_html)
        
        # Assertions
        assert "This is the actual relevant content" in pruned_html, "Main content missing!"
        assert "cookie-banner" not in pruned_html, "Cookie banner was not pruned!"
        assert "social-share" not in pruned_html, "Social share was not pruned!"
        assert "newsletter" not in pruned_html, "Newsletter signup was not pruned!"
        assert "header" not in pruned_html, "Header was not pruned!"
        assert "footer" not in pruned_html, "Footer was not pruned!"
        assert "nav" not in pruned_html, "Nav was not pruned!"
        
        print("\n[PASS] DOM-Level Pruning test passed successfully!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_test())
