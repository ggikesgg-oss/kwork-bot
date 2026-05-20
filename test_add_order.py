from database import db
from bot import KworkBot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from response_generator import response_gen
import asyncio

async def test():
    bot = KworkBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Тестовый заказ
    test_project = {
        'id': '9999999',
        'title': 'Нужен парсер для сайта с автоматизацией',
        'description': 'Нужно спарсить данные с сайта и сохранить в Excel',
        'price': 5000,
        'url': 'https://kwork.ru/projects/9999999'
    }
    
    response = await response_gen.generate_response(test_project)
    print(f"Сгенерированный отклик:\n{response}")
    
    # Отправляем в Telegram
    await bot.send_new_order(test_project, response)
    print("\n✅ Тестовое сообщение отправлено в Telegram!")

asyncio.run(test())
