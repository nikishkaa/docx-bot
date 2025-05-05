import telebot
from file_handler import FileHandler
from telebot import types
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен из переменной окружения
TOKEN = os.getenv('TOKEN')

# Инициализация бота и обработчика файлов
bot = telebot.TeleBot(TOKEN)
file_handler = FileHandler()

# Удаляем вебхук перед запуском
bot.remove_webhook()

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
    # Сначала добавляем кнопки навигации
    markup.add(types.KeyboardButton('🔙 Вернуться в главное меню'))
    # Затем добавляем категории
    for category in file_handler.categories:
        btn = types.KeyboardButton(f"📂 {category}")
        markup.add(btn)
    return markup

def create_subcategory_menu(category):
    """Создает меню выбора подкатегории"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Сначала добавляем кнопки навигации
    nav_buttons = [
        types.KeyboardButton('⬅️ Назад к категориям'),
        types.KeyboardButton('🔙 Вернуться в главное меню')
    ]
    markup.add(*nav_buttons)
    
    # Затем добавляем подкатегории
    if category in file_handler.subcategories:
        for subcategory in file_handler.subcategories[category]:
            btn = types.KeyboardButton(f"📁 {subcategory}")
            markup.add(btn)
    return markup

def create_files_menu(files, category, subcategory=None):
    """Создает меню со списком файлов для скачивания"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Сначала добавляем кнопки навигации
    nav_buttons = []
    if subcategory:
        nav_buttons.append(types.KeyboardButton('⬅️ Назад к подкатегориям'))
    nav_buttons.append(types.KeyboardButton('⬅️ Назад к категориям'))
    nav_buttons.append(types.KeyboardButton('🔙 Вернуться в главное меню'))
    markup.add(*nav_buttons)
    
    # Затем добавляем кнопки для каждого файла
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

def show_subcategories(message, category):
    """Показывает меню с подкатегориями"""
    markup = create_subcategory_menu(category)
    bot.send_message(
        message.chat.id,
        f"📁 Выберите подкатегорию в {category}:",
        reply_markup=markup
    )

def list_files(message, category, subcategory=None):
    """Показывает список файлов в выбранной категории или подкатегории"""
    files = file_handler.get_files_list(category, subcategory)
    if not files:
        if subcategory:
            markup = create_subcategory_menu(category)
            bot.send_message(
                message.chat.id,
                f"📭 В подкатегории {subcategory} категории {category} пока нет файлов.",
                reply_markup=markup
            )
        else:
            markup = create_category_menu()
            bot.send_message(
                message.chat.id,
                f"📭 В категории {category} пока нет файлов.",
                reply_markup=markup
            )
        return

    response = f"📁 Файлы в "
    if subcategory:
        response += f"подкатегории {subcategory} категории {category}:\n\n"
    else:
        response += f"категории {category}:\n\n"
    
    # Сначала показываем подкатегории, если они есть
    if not subcategory and category in file_handler.subcategories:
        response += "📂 Подкатегории:\n"
        for subcat in file_handler.subcategories[category]:
            response += f"📁 {subcat}\n"
        response += "\n"
    
    # Затем показываем файлы
    response += "📄 Файлы:\n"
    for file in files:
        response += f"📄 {file['name']}\n"
        response += f"📊 Размер: {file['size']}\n"
        response += f"🕒 Дата: {file['date']}\n\n"
    
    # Создаем меню с кнопками для скачивания файлов
    markup = create_files_menu(files, category, subcategory)
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
    
    # Если у категории есть подкатегории, показываем их
    if category in file_handler.subcategories:
        markup = create_subcategory_menu(category)
        bot.send_message(
            message.chat.id,
            f"📁 Выберите подкатегорию в {category}:",
            reply_markup=markup
        )
        bot.register_next_step_handler(message, lambda m: process_subcategory_selection(m, category))
    else:
        # Если подкатегорий нет, сохраняем файл сразу в категорию
        save_file_to_category(message, category)

def process_subcategory_selection(message, category):
    if message.text == '🔙 Вернуться в главное меню':
        markup = create_main_menu()
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)
        return
    elif message.text == '⬅️ Назад к категориям':
        show_categories(message)
        return

    # Получаем подкатегорию из текста сообщения
    subcategory = message.text[2:] if message.text.startswith('📁 ') else None
    
    if subcategory and subcategory in file_handler.subcategories[category]:
        save_file_to_category(message, category, subcategory)
    else:
        markup = create_subcategory_menu(category)
        bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, выберите подкатегорию из списка:",
            reply_markup=markup
        )

def save_file_to_category(message, category, subcategory=None):
    try:
        # Получаем информацию о файле из предыдущего сообщения
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Сохраняем файл в выбранную категорию/подкатегорию
        file_handler.save_file(
            message.document.file_id,
            message.document.file_name,
            downloaded_file,
            category,
            subcategory
        )
        
        markup = create_main_menu()
        location = f"подкатегорию {subcategory} категории {category}" if subcategory else f"категорию {category}"
        bot.send_message(
            message.chat.id,
            f"✅ Файл {message.document.file_name} успешно сохранен в {location}!",
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
        if category in file_handler.subcategories:
            show_subcategories(message, category)
        else:
            list_files(message, category)
    elif message.text.startswith('📁 '):
        # Обработка выбора подкатегории
        subcategory = message.text[2:].strip()
        # Находим категорию для этой подкатегории
        for category in file_handler.subcategories:
            if subcategory in file_handler.subcategories[category]:
                list_files(message, category, subcategory)
                break
    elif message.text.startswith('📥 '):
        # Обработка нажатия на кнопку скачивания файла
        file_name = message.text[2:].strip()  # Убираем эмодзи и пробел
        
        try:
            # Ищем файл во всех категориях и подкатегориях
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