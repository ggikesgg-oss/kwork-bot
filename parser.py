import asyncio
import random
from playwright.async_api import async_playwright
import re
from config import KWORK_CATEGORY, DELAY_BETWEEN_REQUESTS
from database import db

class KworkParser:
    def __init__(self):
        self.base_url = "https://kwork.ru/projects"
    
    def get_category(self):
        """Получает категорию из БД"""
        category = db.get_filter('category')
        return category if category else KWORK_CATEGORY
    
    async def get_new_projects(self, last_check_ids=None):
        projects = []
        
        filters = db.get_filters_for_parser()
        category = self.get_category()
        
        print(f"🔍 Поиск в категории: {category}")
        print(f"💰 Бюджет: {filters['budget_min']} - {filters['budget_max']} ₽")
        print(f"✅ Include: {filters['keywords_include']}")
        print(f"❌ Exclude: {filters['keywords_exclude']}")
        
        async with async_playwright() as p:
            # ВАЖНО: headless=True для сервера!
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            try:
                url = f"{self.base_url}?c={category}&sort=date"
                print(f"Парсинг URL: {url}")
                
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(5000)
                
                # Прокручиваем для загрузки
                for i in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(2000)
                
                # Ищем все ссылки на проекты
                links = await page.query_selector_all('a[href*="/projects/"]')
                print(f"Найдено ссылок на проекты: {len(links)}")
                
                for link in links[:25]:
                    try:
                        href = await link.get_attribute('href')
                        if not href or '/projects/' not in href:
                            continue
                        
                        project_id = re.search(r'/projects/(\d+)', href)
                        if not project_id:
                            continue
                        project_id = project_id.group(1)
                        
                        # Получаем текст всей карточки
                        card = link
                        for _ in range(3):
                            parent = await card.query_selector('xpath=..')
                            if parent:
                                card = parent
                            else:
                                break
                        
                        card_text = await card.inner_text()
                        card_text = card_text.strip()
                        
                        # Пропускаем навигационные элементы
                        if len(card_text) < 20 or any(word in card_text.lower() for word in ['рубрики', 'смотреть открытые']):
                            continue
                        
                        # Извлекаем название
                        lines = card_text.split('\n')
                        title = lines[0] if lines else "Без названия"
                        title = title.strip()
                        
                        # Извлекаем цену
                        price = 0
                        price_match = re.search(r'(\d+[\d\s]*)\s*₽', card_text)
                        if price_match:
                            price = int(price_match.group(1).replace(' ', ''))
                        
                        print(f"\n📋 Проект {project_id}: {title[:50]}")
                        print(f"   Цена: {price}₽")
                        
                        # Фильтрация
                        text_lower = (title + " " + card_text).lower()
                        
                        # Проверяем exclude
                        excluded = False
                        for kw in filters["keywords_exclude"]:
                            if kw.lower() in text_lower:
                                print(f"   ❌ Exclude: {kw}")
                                excluded = True
                                break
                        if excluded:
                            continue
                        
                        # Проверяем бюджет
                        if price > 0 and price < filters["budget_min"]:
                            print(f"   ❌ Бюджет: {price} < {filters['budget_min']}")
                            continue
                        if price > 0 and price > filters["budget_max"]:
                            print(f"   ❌ Бюджет: {price} > {filters['budget_max']}")
                            continue
                        
                        # Проверяем include
                        if filters["keywords_include"]:
                            has_include = any(kw.lower() in text_lower for kw in filters["keywords_include"])
                            if not has_include:
                                print(f"   ❌ Нет ключевых слов из {filters['keywords_include']}")
                                continue
                        
                        print(f"   ✅ ПРОПУЩЕН!")
                        
                        project = {
                            'id': project_id,
                            'title': title[:100],
                            'description': card_text[:500],
                            'price': price,
                            'url': f"https://kwork.ru/projects/{project_id}"
                        }
                        projects.append(project)
                        
                    except Exception as e:
                        print(f"Ошибка: {e}")
                        continue
                
                print(f"\n✅ Найдено подходящих заказов: {len(projects)}")
                
            except Exception as e:
                print(f"Ошибка парсинга: {e}")
            finally:
                await browser.close()
        
        return projects
