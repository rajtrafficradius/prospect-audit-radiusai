import os
import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse

async def scrape_page(page, url):
    """Scrapes the visible text from a given URL."""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Extract text, remove excessive whitespace
        content = await page.evaluate("() => document.body.innerText")
        return {"url": url, "content": " ".join(content.split())}
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {"url": url, "content": ""}

async def scrape_website_core_pages(base_url, output_dir=None):
    """
    Crawls the homepage and attempts to find/scrape About, Services, and Contact pages.
    Also takes a full-page screenshot of the homepage for Vision CRO analysis.
    Returns a dictionary of scraped data.
    """
    if not base_url.startswith("http"):
        base_url = f"https://{base_url}"
        
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Scrape Homepage
        print(f"Scraping Homepage: {base_url}")
        
        # Take screenshot for Vision Agent
        try:
            await page.goto(base_url, wait_until="networkidle", timeout=30000)
            screenshot_path = os.path.join(output_dir, "homepage_screenshot.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"Saved UI Screenshot: {screenshot_path}")
        except Exception as e:
            print(f"Failed to capture screenshot: {e}")
            
        home_data = await scrape_page(page, base_url)
        results.append(home_data)

        # Attempt to find links to key pages
        try:
            links = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a'))
                    .map(a => ({ text: a.innerText.toLowerCase(), href: a.href }))
            }''')
            
            # Filter for common core pages
            core_paths = set()
            for link in links:
                text = link.get('text', '')
                href = link.get('href', '')
                if 'about' in text or 'contact' in text or 'service' in text:
                    if href.startswith('http') and urlparse(href).netloc == urlparse(base_url).netloc:
                         core_paths.add(href)
            
            # Scrape up to 4 additional core pages to keep LLM context size reasonable
            for url in list(core_paths)[:4]:
                print(f"Scraping subpage: {url}")
                page_data = await scrape_page(page, url)
                results.append(page_data)

        except Exception as e:
            print(f"Could not discover subpages: {e}")

        await browser.close()
        
    return results

def run_scraper(base_url, output_dir=None):
    """Synchronous wrapper for the async scraper."""
    return asyncio.run(scrape_website_core_pages(base_url, output_dir))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        data = run_scraper(sys.argv[1])
        for p in data:
            print(f"--- {p['url']} ---")
            print(p['content'][:200] + "...\n")
