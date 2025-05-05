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

# Словарь для хранения информации о загружаемых файлах
uploading_files = {}

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
    btn1 = types.KeyboardButton('📥 Скачать файлы')
    btn2 = types.KeyboardButton('📋 Список файлов')
    btn3 = types.KeyboardButton('📤 Загрузить файл')
    btn4 = types.KeyboardButton('❓ Помощь')
    markup.add(btn1, btn2, btn3, btn4)
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
    """Обработчик команды /start"""
    markup = create_main_menu()
    bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать!\n\n"
        "Я помогу вам управлять файлами.\n"
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

def show_categories(message, view_only=False):
    """Показывает меню с категориями"""
    markup = create_category_menu()
    if view_only:
        bot.send_message(
            message.chat.id,
            "📋 Выберите категорию для просмотра списка файлов:",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            "📥 Выберите категорию для скачивания файлов:",
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
        file_path = f"{category}"
        if 'subcategory' in file:
            file_path += f"/{file['subcategory']}"
        file_path += f"/{file['name']}"
        
        response += f"📄 {file['name']}\n"
        response += f"📂 Путь: {file_path}\n"
        response += f"📊 Размер: {file['size']}\n"
        response += f"🕒 Дата: {file['date']}\n\n"
    
    markup = create_files_menu(files, category, subcategory)
    bot.send_message(message.chat.id, response, reply_markup=markup)

@bot.message_handler(commands=['get'])
def get_file(message):
    try:
        file_name = message.text.split()[1] if len(message.text.split()) > 1 else None
        
        if not file_name:
            bot.reply_to(message, "❌ Пожалуйста, укажите имя файла.\nПример: /get example.txt")
            return

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

@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Обработчик загрузки файлов"""
    if not message.document:
        bot.reply_to(message, "❌ Ошибка: файл не найден в сообщении.")
        return

    if not message.document.file_id:
        bot.reply_to(message, "❌ Ошибка: не удалось получить идентификатор файла.")
        return

    # Сохраняем информацию о файле
    uploading_files[message.chat.id] = {
        'file_id': message.document.file_id,
        'file_name': message.document.file_name
    }

    markup = create_category_menu()
    bot.send_message(
        message.chat.id,
        "📂 Выберите категорию для файла:",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, process_category_selection)

def process_category_selection(message):
    """Обработчик выбора категории"""
    if message.text == '🔙 Вернуться в главное меню':
        markup = create_main_menu()
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)
        return

    category = message.text[2:].strip() if message.text.startswith('📂 ') else "Other"
    
    if category in file_handler.subcategories:
        markup = create_subcategory_menu(category)
        bot.send_message(
            message.chat.id,
            f"📁 Выберите подкатегорию в {category}:",
            reply_markup=markup
        )
        bot.register_next_step_handler(message, lambda m: process_subcategory_selection(m, category))
    else:
        save_file_to_category(message, category)

def process_subcategory_selection(message, category):
    """Обработчик выбора подкатегории"""
    if message.text == '🔙 Вернуться в главное меню':
        markup = create_main_menu()
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)
        return
    elif message.text == '⬅️ Назад к категориям':
        show_categories(message)
        return

    subcategory = message.text[2:].strip() if message.text.startswith('📁 ') else None
    
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
    """Сохранение файла в выбранную категорию"""
    try:
        # Получаем информацию о файле из словаря
        file_info = uploading_files.get(message.chat.id)
        if not file_info:
            bot.reply_to(message, "❌ Ошибка: информация о файле не найдена.")
            return

        # Проверяем, существует ли файл с таким именем
        existing_files = file_handler.get_files_list(category, subcategory)
        for file in existing_files:
            if file['name'] == file_info['file_name']:
                markup = create_main_menu()
                bot.send_message(
                    message.chat.id,
                    f"❌ Файл с именем {file_info['file_name']} уже существует в этой категории.",
                    reply_markup=markup
                )
                uploading_files.pop(message.chat.id, None)
                return

        file_data = bot.get_file(file_info['file_id'])
        if not file_data:
            bot.reply_to(message, "❌ Ошибка: не удалось получить информацию о файле.")
            return

        downloaded_file = bot.download_file(file_data.file_path)
        if not downloaded_file:
            bot.reply_to(message, "❌ Ошибка: не удалось скачать файл.")
            return

        file_handler.save_file(
            file_info['file_id'],
            file_info['file_name'],
            downloaded_file,
            category,
            subcategory
        )
        
        # Удаляем информацию о файле после успешного сохранения
        uploading_files.pop(message.chat.id, None)
        
        markup = create_main_menu()
        location = f"подкатегорию {subcategory} категории {category}" if subcategory else f"категорию {category}"
        bot.send_message(
            message.chat.id,
            f"✅ Файл {file_info['file_name']} успешно сохранен в {location}!",
            reply_markup=markup
        )
    except Exception as e:
        # Удаляем информацию о файле в случае ошибки
        uploading_files.pop(message.chat.id, None)
        markup = create_main_menu()
        bot.send_message(
            message.chat.id,
            f"❌ Произошла ошибка при сохранении файла: {str(e)}",
            reply_markup=markup
        )

def show_all_files(message):
    """Показывает все файлы из всех категорий и подкатегорий"""
    all_files = []
    
    # Собираем файлы из всех категорий и подкатегорий
    for category in file_handler.categories:
        # Получаем файлы из основной категории
        files = file_handler.get_files_list(category)
        for file in files:
            file['category'] = category
            all_files.append(file)
        
        # Получаем файлы из подкатегорий
        if category in file_handler.subcategories:
            for subcategory in file_handler.subcategories[category]:
                files = file_handler.get_files_list(category, subcategory)
                for file in files:
                    file['category'] = category
                    file['subcategory'] = subcategory
                    all_files.append(file)
    
    if not all_files:
        bot.send_message(message.chat.id, "Файлы не найдены")
        return
    
    # Сортируем файлы по категории, подкатегории и имени
    all_files.sort(key=lambda x: (x['category'], x.get('subcategory', ''), x['name']))
    
    # Отправляем общее количество файлов с эмодзи и выделением
    total_files = len(all_files)
    counter_message = f"📊 *СТАТИСТИКА ФАЙЛОВ*\n\n📚 Всего файлов в системе: *{total_files}*"
    bot.send_message(message.chat.id, counter_message, parse_mode='Markdown')
    
    # Разбиваем список на части по 10 файлов
    for i in range(0, len(all_files), 10):
        chunk = all_files[i:i+10]
        response = ""
        for file in chunk:
            response += f"📄 {file['name']}\n"
            response += f"📂 Путь: {file['category']}"
            if 'subcategory' in file:
                response += f"/{file['subcategory']}"
            response += f"\n📊 Размер: {file['size']}\n"
            response += f"🕒 Дата: {file['date']}\n\n"
        
        # Отправляем часть списка
        if response:  # Отправляем только если есть что отправлять
            bot.send_message(message.chat.id, response)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if message.text == '📥 Скачать файлы':
        show_categories(message)
    elif message.text == '📋 Список файлов':
        show_all_files(message)
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
        category = message.text[2:].strip()
        if category in file_handler.subcategories:
            show_subcategories(message, category)
        else:
            list_files(message, category)
    elif message.text.startswith('📁 '):
        subcategory = message.text[2:].strip()
        for category in file_handler.subcategories:
            if subcategory in file_handler.subcategories[category]:
                list_files(message, category, subcategory)
                break
    elif message.text.startswith('📥 '):
        file_name = message.text[2:].strip()
        
        try:
            # Ищем файл во всех категориях и подкатегориях
            found = False
            for category in file_handler.categories:
                file_data = file_handler.get_file(file_name, category)
                if file_data is not None:
                    bot.send_document(
                        message.chat.id,
                        file_data,
                        visible_file_name=file_name
                    )
                    found = True
                    break
                
                if category in file_handler.subcategories:
                    for subcategory in file_handler.subcategories[category]:
                        file_data = file_handler.get_file(file_name, category, subcategory)
                        if file_data is not None:
                            bot.send_document(
                                message.chat.id,
                                file_data,
                                visible_file_name=file_name
                            )
                            found = True
                            break
                    if found:
                        break
            
            if not found:
                bot.reply_to(message, f"❌ Файл {file_name} не найден.")
        except Exception as e:
            bot.reply_to(message, f"❌ Произошла ошибка при получении файла: {str(e)}")
    else:
        bot.send_message(
            message.chat.id,
            "❓ Неизвестная команда. Используйте меню или /help для получения списка команд."
        )

if __name__ == "__main__":
    print("Бот запущен...")
    # Запускаем бота
    bot.polling(non_stop=True) 