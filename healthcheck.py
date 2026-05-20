import os
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    import asyncio
    from main import KworkMonitor
    
    async def start():
        monitor = KworkMonitor()
        await monitor.run_monitor()
    
    asyncio.run(start())

if __name__ == '__main__':
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask для healthcheck
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
