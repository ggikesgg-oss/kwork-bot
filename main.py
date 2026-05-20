#!/usr/bin/env python3
import asyncio
import signal
import threading
from datetime import datetime
from flask import Flask
import os

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PARSE_INTERVAL_MINUTES
from database import db
from parser import KworkParser
from bot import KworkBot
from response_generator import response_gen

# Flask приложение для healthcheck
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Kwork Bot is running!", 200

class KworkMonitor:
    def __init__(self):
        self.parser = KworkParser()
        self.bot = KworkBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.running = True
        self.processed_ids = set()
        self.load_processed_ids()
    
    def load_processed_ids(self):
        """Загружает ID обработанных заказов"""
        try:
            import sqlite3
            conn = sqlite3.connect('responses.db')
            cursor = conn.execute("SELECT order_id FROM processed_orders")
            self.processed_ids = {row[0] for row in cursor.fetchall()}
            conn.close()
            print(f"Загружено {len(self.processed_ids)} обработанных заказов")
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            self.processed_ids = set()
    
    async def check_new_orders(self):
        """Проверяет новые заказы"""
        print(f"[{datetime.now()}] Проверяю новые заказы...")
        
        projects = await self.parser.get_new_projects(self.processed_ids)
        
        if not projects:
            print(f"[{datetime.now()}] Новых заказов не найдено")
            return
        
        print(f"[{datetime.now()}] Найдено {len(projects)} новых заказов")
        
        for project in projects:
            if project['id'] in self.processed_ids:
                continue
            
            print(f"Обрабатываю заказ: {project['title']} ({project['price']}₽)")
            
            response_text = await response_gen.generate_response(project)
            await self.bot.send_new_order(project, response_text)
            
            # Сохраняем в БД
            db.mark_order_processed(project['id'])
            self.processed_ids.add(project['id'])
            
            await asyncio.sleep(2)
    
    async def run_monitor(self):
        print("🚀 Запуск монитора заказов Kwork")
        print(f"📊 Интервал проверки: {PARSE_INTERVAL_MINUTES} минут")
        print("🤖 Бот запущен...")
        
        bot_task = asyncio.create_task(self.bot.start())
        
        try:
            while self.running:
                await self.check_new_orders()
                await asyncio.sleep(PARSE_INTERVAL_MINUTES * 60)
        except asyncio.CancelledError:
            print("Монитор остановлен")
        finally:
            bot_task.cancel()
    
    def stop(self):
        self.running = False
        print("Остановка монитора...")

def run_bot_in_thread():
    """Запускает бота в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    monitor = KworkMonitor()
    
    def signal_handler():
        print("Получен сигнал остановки...")
        monitor.stop()
    
    loop.add_signal_handler(signal.SIGINT, signal_handler)
    loop.add_signal_handler(signal.SIGTERM, signal_handler)
    
    try:
        loop.run_until_complete(monitor.run_monitor())
    except KeyboardInterrupt:
        print("Бот остановлен")

if __name__ == "__main__":
    import sys
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()
    
    # Запускаем веб-сервер для healthcheck
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
