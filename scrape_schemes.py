import asyncio
import json
import os
from playwright.async_api import async_playwright

async def scrape_myscheme():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Target Category (Example: Agriculture)
        categories = ["Agriculture", "Education", "Social Welfare"]
        os.makedirs("data/schemes", exist_ok=True)

        for cat in categories:
            print(f"Scraping Category: {cat}")
            await page.goto(f"https://www.myscheme.gov.in/search/category/{cat}")
            await page.wait_for_selector(".scheme-card")
            
            # Extract links and basic info
            links = await page.eval_on_selector_all(".scheme-card a", "elements => elements.map(e => e.href)")
            
            for link in links[:5]: # Limit for testing
                await page.goto(link)
                await page.wait_for_load_state("networkidle")
                
                title = await page.locator("h1").inner_text()
                data = {
                    "title": title.strip(),
                    "category": cat,
                    "benefits": await page.locator("#benefits").inner_text(),
                    "eligibility": await page.locator("#eligibility").inner_text(),
                    "documents": await page.locator("#documents-required").inner_text(),
                    "url": link
                }
                
                filename = f"data/schemes/{title.lower().replace(' ', '_')[:30]}.json"
                with open(filename, "w") as f:
                    json.dump(data, f, indent=4)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_myscheme())
