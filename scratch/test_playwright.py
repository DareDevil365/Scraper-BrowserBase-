import sys
from playwright.sync_api import sync_playwright

url = "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHWkc_Gs5v7f-eLEuD3-eXEdn-jQvr3gPGmKQZ7n24h48w6g4n3iLvFZ5md6YQGvrKM4eHHEfT2MaODZyKl47LNYSoMrWlY9-L-oegbPfNtOi2eBl0hdAInSpgOwpfz2FocBIt91Y6zIYtNWPCRpChbe1-Ky1uJCyCGzfQ="

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to URL...")
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        print("Final URL:", page.url)
        browser.close()
except Exception as e:
    print("Error:", e)
