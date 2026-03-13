import asyncio
import json
import os
from playwright.async_api import async_playwright

async def scrape_myscheme():
    async with async_playwright() as p:
        # Spoof a real browser to avoid blocks
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        categories = ["Agriculture", "Education", "Health", "Social Welfare"]
        base_dir = "data/schemes"
        os.makedirs(base_dir, exist_ok=True)

        for cat in categories:
            print(f"🔍 Checking Category: {cat}")
            try:
                # Use the search query URL which is more stable
                await page.goto(f"https://www.myscheme.gov.in/search/category/{cat}", wait_until="networkidle")
                
                # Wait for at least one card or a timeout
                await page.wait_for_selector(".scheme-card", timeout=10000)
                
                links = await page.eval_on_selector_all(".scheme-card a", "elements => elements.map(e => e.href)")
                print(f"✅ Found {len(links)} schemes in {cat}")

                for link in links[:5]: # Limit for Phase 1
                    await page.goto(link, wait_until="networkidle")
                    title = await page.locator("h1").inner_text()
                    
                    data = {
                        "title": title.strip(),
                        "category": cat,
                        "url": link,
                        "benefits": await page.locator("#benefits").inner_text() if await page.locator("#benefits").count() else "N/A",
                        "eligibility": await page.locator("#eligibility").inner_text() if await page.locator("#eligibility").count() else "N/A",
                        "documents": await page.locator("#documents-required").inner_text() if await page.locator("#documents-required").count() else "N/A"
                    }
                    
                    filename = "".join(x for x in title if x.isalnum() or x==' ')
                    filename = filename.lower().replace(" ", "_")[:30] + ".json"
                    
                    with open(os.path.join(base_dir, filename), "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"⚠️ Skipping {cat}: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_myscheme())
