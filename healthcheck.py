import os
import threading
import subprocess
from flask import Flask

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "OK", 200

def run_bot():
    # Запускаем основного бота
    subprocess.run(["python", "main.py"])

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер для healthcheck
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
