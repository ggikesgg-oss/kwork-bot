#!/usr/bin/env python3
import asyncio
import signal
from datetime import datetime

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PARSE_INTERVAL_MINUTES
from database import db
from parser import KworkParser
from bot import KworkBot
from response_generator import response_gen

class KworkMonitor:
    def __init__(self):
        self.parser = KworkParser()
        self.bot = KworkBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.running = True
        self.processed_ids = set()
        
    async def check_new_orders(self):
        print(f"[{datetime.now()}] Проверяю новые заказы...")
        
        projects = await self.parser.get_new_projects(self.processed_ids)
        
        if not projects:
            print(f"[{datetime.now()}] Новых заказов не найдено")
            return
        
        print(f"[{datetime.now()}] Найдено {len(projects)} новых заказов")
        
        for project in projects:
            if db.is_order_processed(project['id']):
                continue
            
            print(f"Обрабатываю заказ: {project['title']} ({project['price']}₽)")
            
            response_text = await response_gen.generate_response(project)
            
            await self.bot.send_new_order(project, response_text)
            
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

async def main():
    monitor = KworkMonitor()
    
    def signal_handler():
        print("\nПолучен сигнал остановки...")
        monitor.stop()
    
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler)
    loop.add_signal_handler(signal.SIGTERM, signal_handler)
    
    try:
        await monitor.run_monitor()
    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем")

if __name__ == "__main__":
    asyncio.run(main())
