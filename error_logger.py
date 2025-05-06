import logging
import os
from datetime import datetime

# Создаем директорию для логов, если её нет
if not os.path.exists('logs'):
    os.makedirs('logs')

# Настраиваем логгер
logger = logging.getLogger('bot_logger')
logger.setLevel(logging.ERROR)

# Создаем форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Создаем файловый обработчик с именем файла, включающим текущую дату
log_filename = f'logs/error_log_{datetime.now().strftime("%Y-%m-%d")}.log'
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
logger.addHandler(file_handler)

def log_error(error_message, user_id=None, additional_info=None):
    """
    Логирует ошибку в файл
    
    Args:
        error_message (str): Сообщение об ошибке
        user_id (int, optional): ID пользователя, у которого произошла ошибка
        additional_info (str, optional): Дополнительная информация об ошибке
    """
    log_message = f"Error: {error_message}"
    if user_id:
        log_message += f" | User ID: {user_id}"
    if additional_info:
        log_message += f" | Additional Info: {additional_info}"
    
    logger.error(log_message) 