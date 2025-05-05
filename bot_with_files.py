import telebot
from file_handler import FileHandler
from telebot import types
import os

# Инициализация бота и обработчика файлов
bot = telebot.TeleBot('7373495523:AAEge_21E9927fNFa9ETnEKknc437cGM4JU')
file_handler = FileHandler()

# Установка команд бота
bot.set_my_commands([
    types.BotCommand("start", "Запустить бота и показать главное меню"),
    types.BotCommand("files", "Показать список сохраненных файлов"),
    types.BotCommand("get", "Скачать файл по имени"),
    types.BotCommand("help", "Показать справку по командам")
])

def create_main_menu():
    """Создает главное меню с кнопками"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('📁 Список файлов')
    btn2 = types.KeyboardButton('📤 Загрузить файл')
    btn3 = types.KeyboardButton('❓ Помощь')
    markup.add(btn1, btn2, btn3)
    return markup

def create_category_menu():
    """Создает меню выбора категории"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for category in file_handler.categories:
        btn = types.KeyboardButton(f"📂 {category}")
        markup.add(btn)
    markup.add(types.KeyboardButton('🔙 Вернуться в главное меню'))
    return markup

def create_files_menu(files, category):
    """Создает меню со списком файлов для скачивания"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Добавляем кнопки навигации
    nav_buttons = [
        types.KeyboardButton('⬅️ Назад к категориям'),
        types.KeyboardButton('🔙 Вернуться в главное меню')
    ]
    markup.add(*nav_buttons)
    
    # Добавляем кнопки для каждого файла
    for file in files:
        btn = types.KeyboardButton(f"📥 {file['name']}")
        markup.add(btn)
    
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    markup = create_main_menu()
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я бот для работы с файлами.\n\n"
        "Выберите действие в меню ниже:",
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "📚 Список доступных команд:\n\n"
        "/start - Запустить бота и показать главное меню\n"
        "/files - Показать список сохраненных файлов\n"
        "/get filename - Скачать файл по имени\n"
        "/help - Показать это сообщение\n\n"
        "Также вы можете использовать кнопки меню для навигации."
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['files'])
def show_categories(message):
    """Показывает меню с категориями"""
    markup = create_category_menu()
    bot.send_message(
        message.chat.id,
        "📂 Выберите категорию:",
        reply_markup=markup
    )

def list_files(message, category):
    """Показывает список файлов в выбранной категории"""
    files = file_handler.get_files_list(category)
    if not files:
        markup = create_category_menu()
        bot.send_message(
            message.chat.id,
            f"📭 В категории {category} пока нет файлов.",
            reply_markup=markup
        )
        return

    response = f"📁 Файлы в категории {category}:\n\n"
    for file in files:
        response += f"📄 {file['name']}\n"
        response += f"📊 Размер: {file['size']}\n"
        response += f"🕒 Дата: {file['date']}\n\n"
    
    # Создаем меню с кнопками для скачивания файлов
    markup = create_files_menu(files, category)
    bot.send_message(message.chat.id, response, reply_markup=markup)

@bot.message_handler(commands=['get'])
def get_file(message):
    try:
        # Получаем имя файла из команды
        file_name = message.text.split()[1] if len(message.text.split()) > 1 else None
        
        if not file_name:
            bot.reply_to(message, "❌ Пожалуйста, укажите имя файла.\nПример: /get example.txt")
            return

        # Получаем файл
        file_data = file_handler.get_file(file_name)
        
        if file_data is None:
            bot.reply_to(message, f"❌ Файл {file_name} не найден.")
            return

        # Отправляем файл пользователю
        bot.send_document(
            message.chat.id,
            file_data,
            visible_file_name=file_name
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Произошла ошибка при получении файла: {str(e)}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    # Создаем меню выбора категории
    markup = create_category_menu()
    bot.send_message(
        message.chat.id,
        "📂 Выберите категорию для файла:",
        reply_markup=markup
    )
    # Сохраняем информацию о файле для последующей обработки
    bot.register_next_step_handler(message, process_category_selection)

def process_category_selection(message):
    if message.text == '🔙 Вернуться в главное меню':
        markup = create_main_menu()
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)
        return

    # Получаем категорию из текста сообщения
    category = message.text[2:] if message.text.startswith('📂 ') else "Other"
    
    try:
        # Получаем информацию о файле из предыдущего сообщения
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Сохраняем файл в выбранную категорию
        file_handler.save_file(
            message.document.file_id,
            message.document.file_name,
            downloaded_file,
            category
        )
        
        markup = create_main_menu()
        bot.send_message(
            message.chat.id,
            f"✅ Файл {message.document.file_name} успешно сохранен в категорию {category}!",
            reply_markup=markup
        )
    except Exception as e:
        markup = create_main_menu()
        bot.send_message(
            message.chat.id,
            f"❌ Произошла ошибка при сохранении файла: {str(e)}",
            reply_markup=markup
        )

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """Обработчик текстовых сообщений"""
    if message.text == '📁 Список файлов':
        show_categories(message)
    elif message.text == '📤 Загрузить файл':
        bot.send_message(
            message.chat.id,
            "📎 Отправьте мне файл, и я его сохраню."
        )
    elif message.text == '❓ Помощь':
        help_command(message)
    elif message.text == '🔙 Вернуться в главное меню':
        markup = create_main_menu()
        bot.send_message(
            message.chat.id,
            "Главное меню:",
            reply_markup=markup
        )
    elif message.text == '⬅️ Назад к категориям':
        show_categories(message)
    elif message.text.startswith('📂 '):
        # Обработка выбора категории
        category = message.text[2:].strip()
        list_files(message, category)
    elif message.text.startswith('📥 '):
        # Обработка нажатия на кнопку скачивания файла
        file_name = message.text[2:].strip()  # Убираем эмодзи и пробел
        
        try:
            # Ищем файл во всех категориях
            file_data = file_handler.get_file(file_name)
            if file_data is None:
                bot.reply_to(message, f"❌ Файл {file_name} не найден.")
                return
            
            bot.send_document(
                message.chat.id,
                file_data,
                visible_file_name=file_name
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Произошла ошибка при получении файла: {str(e)}")
    else:
        bot.send_message(
            message.chat.id,
            "❓ Неизвестная команда. Используйте меню или /help для получения списка команд."
        )

if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(non_stop=True) 