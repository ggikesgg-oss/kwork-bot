from flask import Flask
import threading
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running!", 200

@app.route('/health')
def health_check():
    return "OK", 200

def run_bot():
    # Запускаем основного бота
    os.system('python main.py')

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    # Запускаем веб-сервер для healthcheck
    app.run(host='0.0.0.0', port=10000)
