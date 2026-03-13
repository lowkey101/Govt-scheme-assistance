import asyncio
import json
import os
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def scrape_myscheme():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Create a realistic context
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        
        page = await context.new_page()
        # Apply stealth to bypass bot detection
        await stealth_async(page)
        
        categories = ["Agriculture", "Education", "Health", "Social Welfare"]
        base_dir = "data/schemes"
        os.makedirs(base_dir, exist_ok=True)

        for cat in categories:
            print(f"🔍 Checking Category: {cat}")
            try:
                # Direct search URL for more stability
                url = f"https://www.myscheme.gov.in/search/category/{cat}"
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Human-like scroll to trigger lazy loading
                await page.mouse.wheel(0, 500)
                await asyncio.sleep(2)
                
                # Use a more generic selector if .scheme-card fails
                await page.wait_for_selector("a[href*='/schemes/']", timeout=20000)
                
                links = await page.eval_on_selector_all("a[href*='/schemes/']", "elements => elements.map(e => e.href)")
                # Remove duplicates
                links = list(set(links))
                print(f"✅ Found {len(links)} schemes in {cat}")

                for link in links[:5]:
                    await page.goto(link, wait_until="domcontentloaded", timeout=60000)
                    await asyncio.sleep(1) # Breathe
                    
                    title = await page.locator("h1").inner_text()
                    
                    data = {
                        "title": title.strip(),
                        "category": cat,
                        "url": link,
                        "benefits": await page.locator("#benefits").inner_text() if await page.locator("#benefits").count() else "Check website",
                        "eligibility": await page.locator("#eligibility").inner_text() if await page.locator("#eligibility").count() else "Check website",
                        "documents": await page.locator("#documents-required").inner_text() if await page.locator("#documents-required").count() else "Not listed"
                    }
                    
                    filename = "".join(x for x in title if x.isalnum() or x==' ')
                    filename = filename.lower().replace(" ", "_")[:30] + ".json"
                    
                    with open(os.path.join(base_dir, filename), "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                        
            except Exception as e:
                print(f"⚠️ Skipping {cat}: {str(e)[:100]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_myscheme())
