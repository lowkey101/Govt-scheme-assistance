import asyncio
import json
import os
import random
from playwright.async_api import async_playwright
import playwright_stealth

async def scrape_myscheme():
    async with async_playwright() as p:
        # 1. Launch with extra arguments to look less like a bot
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        
        page = await context.new_page()
        
        # 2. Fix the Stealth Import Call
        await playwright_stealth.stealth_async(page)
        
        categories = ["Agriculture", "Education", "Health", "Social Welfare"]
        base_dir = "data/schemes"
        os.makedirs(base_dir, exist_ok=True)

        for cat in categories:
            print(f"🔍 Checking Category: {cat}")
            try:
                url = f"https://www.myscheme.gov.in/search/category/{cat}"
                
                # 3. Use 'networkidle' but with a longer timeout
                await page.goto(url, wait_until="networkidle", timeout=90000)
                
                # 4. Human-like jitter: Scroll a bit to trigger JS loading
                await page.mouse.wheel(0, random.randint(300, 700))
                await asyncio.sleep(random.uniform(2, 4))
                
                # Try to find scheme links. myScheme links usually look like /schemes/name
                await page.wait_for_selector("a[href*='/schemes/']", timeout=30000)
                
                links = await page.eval_on_selector_all("a[href*='/schemes/']", "elements => elements.map(e => e.href)")
                links = list(set(links)) 
                print(f"✅ Found {len(links)} schemes in {cat}")

                for link in links[:5]:
                    await page.goto(link, wait_until="networkidle", timeout=60000)
                    await asyncio.sleep(random.uniform(1, 3)) 
                    
                    title = await page.locator("h1").inner_text()
                    
                    data = {
                        "title": title.strip(),
                        "category": cat,
                        "url": link,
                        "benefits": await page.locator("#benefits").inner_text() if await page.locator("#benefits").count() else "N/A",
                        "eligibility": await page.locator("#eligibility").inner_text() if await page.locator("#eligibility").count() else "N/A",
                        "documents": await page.locator("#documents-required").inner_text() if await page.locator("#documents-required").count() else "N/A"
                    }
                    
                    safe_title = "".join(x for x in title if x.isalnum() or x==' ').strip()
                    filename = safe_title.lower().replace(" ", "_")[:30] + ".json"
                    
                    with open(os.path.join(base_dir, filename), "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    print(f"💾 Saved: {filename}")
                        
            except Exception as e:
                print(f"⚠️ Error in {cat}: {str(e)[:150]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_myscheme())
