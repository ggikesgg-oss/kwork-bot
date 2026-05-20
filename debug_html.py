import asyncio
from playwright.async_api import async_playwright
import re

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://kwork.ru/projects?c=web_programming&sort=date")
        await page.wait_for_timeout(5000)
        
        # Находим все ссылки на проекты
        links = await page.query_selector_all('a[href*="/projects/"]')
        print(f"Найдено ссылок: {len(links)}")
        
        for i, link in enumerate(links[:3]):
            print(f"\n========== ПРОЕКТ {i+1} ==========")
            
            # Получаем родительский элемент
            parent = await link.query_selector('xpath=..')
            if parent:
                # Получаем HTML родителя
                html = await parent.inner_html()
                print("HTML родителя:")
                print(html[:1000])
                
                # Получаем текст родителя
                text = await parent.inner_text()
                print("\nТекст родителя:")
                print(text)
                
                # Ищем цену в тексте
                price_patterns = [
                    r'(\d+[\d\s]*)\s*₽',
                    r'до\s*(\d+)',
                    r'бюджет[:\s]*(\d+)',
                ]
                
                for pattern in price_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        print(f"Найдена цена по паттерну '{pattern}': {match.group(1)}")
        
        await page.wait_for_timeout(10000)
        await browser.close()

asyncio.run(debug())
