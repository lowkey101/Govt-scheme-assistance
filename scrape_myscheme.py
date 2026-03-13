import asyncio
import json
import os
from playwright.async_api import async_playwright
from playwright_stealth import stealth # Corrected import

async def scrape_myscheme():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        # Corrected: use 'stealth' directly on the page
        await stealth(page)
        
        categories = ["Agriculture", "Education", "Health", "Social Welfare"]
        base_dir = "data/schemes"
        os.makedirs(base_dir, exist_ok=True)

        for cat in categories:
            print(f"🔍 Checking Category: {cat}")
            try:
                url = f"https://www.myscheme.gov.in/search/category/{cat}"
                # Use a longer timeout for govt sites
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for the card or the link pattern
                # Using a broader selector as backup
                try:
                    await page.wait_for_selector("a[href*='/schemes/']", timeout=20000)
                except:
                    print(f"⚠️ No schemes found in {cat} (possibly blocked or empty)")
                    continue

                links = await page.eval_on_selector_all("a[href*='/schemes/']", "elements => elements.map(e => e.href)")
                links = list(set(links)) # Unique links only
                print(f"✅ Found {len(links)} schemes in {cat}")

                for link in links[:5]:
                    await page.goto(link, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(2) # Give JS time to render content
                    
                    title = await page.locator("h1").inner_text()
                    
                    data = {
                        "title": title.strip(),
                        "category": cat,
                        "url": link,
                        "benefits": await page.locator("#benefits").inner_text() if await page.locator("#benefits").count() else "N/A",
                        "eligibility": await page.locator("#eligibility").inner_text() if await page.locator("#eligibility").count() else "N/A",
                        "documents": await page.locator("#documents-required").inner_text() if await page.locator("#documents-required").count() else "N/A"
                    }
                    
                    # Clean filename
                    safe_title = "".join(x for x in title if x.isalnum() or x==' ').strip()
                    filename = safe_title.lower().replace(" ", "_")[:30] + ".json"
                    
                    with open(os.path.join(base_dir, filename), "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                        
            except Exception as e:
                print(f"⚠️ Error in {cat}: {str(e)[:100]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_myscheme())
