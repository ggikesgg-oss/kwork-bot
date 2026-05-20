import os
import threading
import subprocess
import time
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    """Запускает основного бота"""
    subprocess.run(["python", "main.py"])

def keep_alive():
    """Внутренний сторож: не даёт Render усыпить бота"""
    url = "http://localhost:10000/health"
    while True:
        time.sleep(600)  # Ждём 10 минут
        try:
            requests.get(url, timeout=30)
            print("🐧 Сторож: бодрствую, пинг отправлен")
        except Exception as e:
            print(f"❌ Сторож: ошибка пинга - {e}")

if __name__ == '__main__':
    print("🚀 Запуск healthcheck сервера")
    
    # Запускаем сторожа в отдельном потоке
    watcher_thread = threading.Thread(target=keep_alive, daemon=True)
    watcher_thread.start()
    print("🐧 Сторож запущен (будет пинать бота каждые 10 минут)")
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    print("🤖 Бот запущен")
    
    # Запускаем Flask сервер
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Flask сервер на порту {port}")
    app.run(host='0.0.0.0', port=port)
