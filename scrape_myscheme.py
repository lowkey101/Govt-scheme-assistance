import asyncio
import json
import os
from playwright.async_api import async_playwright

async def scrape_myscheme():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 13 Categories as seen on myScheme
        categories = ["Agriculture", "Education & Learning", "Health & Wellness", "Social Welfare & Empowerment"]
        base_dir = "data/schemes"
        os.makedirs(base_dir, exist_ok=True)

        for cat in categories:
            cat_slug = cat.lower().replace(" ", "-").replace("&", "and")
            print(f"🚀 Scraping Category: {cat}")
            
            # Navigate to category search
            await page.goto(f"https://www.myscheme.gov.in/search/category/{cat}")
            try:
                await page.wait_for_selector(".scheme-card", timeout=15000)
            except:
                print(f"⚠️ No schemes found for {cat}")
                continue
            
            # Get links
            links = await page.eval_on_selector_all(".scheme-card a", "elements => elements.map(e => e.href)")
            
            for link in links[:10]: # Limit to 10 for Phase 1 testing
                try:
                    await page.goto(link)
                    await page.wait_for_load_state("networkidle")
                    
                    title = await page.locator("h1").inner_text()
                    scheme_id = title.lower().replace(" ", "_")[:30]
                    
                    # Extract Structured Data
                    data = {
                        "title": title.strip(),
                        "category": cat,
                        "url": link,
                        "benefits": await page.locator("#benefits").inner_text() if await page.locator("#benefits").count() else "",
                        "eligibility": await page.locator("#eligibility").inner_text() if await page.locator("#eligibility").count() else "",
                        "documents": await page.locator("#documents-required").inner_text() if await page.locator("#documents-required").count() else ""
                    }
                    
                    # Save JSON
                    with open(f"{base_dir}/{scheme_id}.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                        
                except Exception as e:
                    print(f"❌ Error on {link}: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_myscheme())
