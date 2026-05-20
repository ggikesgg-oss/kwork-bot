from flask import Flask
import threading
import os
import sys

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Kwork Bot is running!", 200

def run_bot():
    # Импортируем и запускаем бота
    from main import KworkMonitor
    import asyncio
    
    async def start():
        monitor = KworkMonitor()
        await monitor.run_monitor()
    
    asyncio.run(start())

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем веб-сервер
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
