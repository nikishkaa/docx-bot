FROM python:3.9-slim

WORKDIR /app

# Копируем только requirements.txt сначала
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем остальные файлы
COPY . .

# Создаем директорию для загрузок
RUN mkdir -p uploads


CMD ["python", "bot_with_files.py"] 