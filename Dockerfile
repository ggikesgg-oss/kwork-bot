FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Копируем requirements и устанавливаем Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask aiohttp

# Копируем весь код
COPY . .

# Запускаем бота через healthcheck.py
CMD ["python", "healthcheck.py"]
