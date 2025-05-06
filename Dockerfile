FROM python:3.9-slim

WORKDIR /app

# Установка необходимых пакетов
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование файлов проекта
COPY . .

# Создание директории для загрузок
RUN mkdir -p uploads

# Запуск бота
CMD ["python", "bot_with_files.py"] 