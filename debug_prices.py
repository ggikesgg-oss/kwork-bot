import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://kwork.ru/projects?c=web_programming&sort=date")
        await page.wait_for_timeout(5000)
        
        # Сохраняем скриншот
        await page.screenshot(path="kwork_screenshot.png")
        
        # Сохраняем HTML
        html = await page.content()
        with open("kwork_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        # Ищем цены
        prices = await page.query_selector_all('[class*="price"], [class*="cost"], [class*="budget"]')
        print(f"Найдено элементов с ценой: {len(prices)}")
        
        for p in prices[:5]:
            text = await p.inner_text()
            print(f"Цена: {text}")
        
        # Ищем карточки проектов
        cards = await page.query_selector_all('.project-card, .card')
        print(f"\nНайдено карточек: {len(cards)}")
        
        for card in cards[:3]:
            html = await card.inner_html()
            print(f"\n--- HTML карточки ---")
            print(html[:500])
        
        await browser.close()

asyncio.run(debug())
