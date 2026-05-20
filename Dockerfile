FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Запускаем
CMD ["python", "healthcheck.py"]
