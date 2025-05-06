import telebot
from file_handler import FileHandler
from telebot import types
import os
import json
from dotenv import load_dotenv
from error_logger import log_error
import zipfile
import io

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен из переменной окружения
TOKEN = os.getenv('TOKEN')

# Инициализация бота и обработчика файлов
bot = telebot.TeleBot(TOKEN)
file_handler = FileHandler()

# Словарь для хранения информации о загружаемых файлах
uploading_files = {}

# Словарь для хранения текущего контекста пользователя
user_context = {}

# Путь к файлу статистики
STATS_FILE = 'download_stats.json'

# Загружаем статистику из файла при запуске
def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Сохраняем статистику в файл
def save_stats():
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(download_stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        error_msg = f"Ошибка при сохранении статистики: {str(e)}"
        log_error(error_msg, "system", "save_stats")
        print(error_msg)  # Выводим ошибку в консоль для отладки

# Инициализируем статистику
download_stats = load_stats()

# Удаляем вебхук перед запуском
bot.remove_webhook()

# Установка команд бота
bot.set_my_commands([
    types.BotCommand("start", "Запустить бота и показать главное меню"),
    types.BotCommand("files", "Показать список сохраненных файлов"),
    types.BotCommand("get", "Скачать файл по имени"),
    types.BotCommand("search", "Поиск файлов по части имени"),
    types.BotCommand("help", "Показать справку по командам")
])


def create_main_menu():
    """Создает главное меню с кнопками"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('📥 Скачать файлы')
    btn2 = types.KeyboardButton('📋 Список файлов')
    btn3 = types.KeyboardButton('📤 Загрузить файл')
    btn4 = types.KeyboardButton('🔍 Поиск файлов')
    btn5 = types.KeyboardButton('❓ Помощь')
    btn6 = types.KeyboardButton('⚙️ Дополнительно')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup


def create_category_menu():
    """Создает меню выбора категории"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    # Сначала добавляем кнопку возврата в главное меню
    markup.add(types.KeyboardButton('🔙 Вернуться в главное меню'))
    
    # Добавляем кнопку "Книги" сразу после кнопки возврата
    markup.add(types.KeyboardButton('📚 Книги'))
    
    # Затем добавляем остальные категории
    for category in file_handler.categories:
        if category != "Книги":  # Пропускаем "Книги", так как уже добавили
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


def create_additional_menu():
    """Создает меню дополнительных функций"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('🔙 Вернуться в главное меню')
    btn2 = types.KeyboardButton('📊 Статистика скачиваний')
    btn3 = types.KeyboardButton('📈 Краткая статистика')
    btn4 = types.KeyboardButton('👤 Мои скачивания')
    btn5 = types.KeyboardButton('📦 Скачать архив со всеми файлами')
    markup.add(btn1, btn2, btn3, btn4, btn5)
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
        "/search query - Поиск файлов по части имени\n"
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
    # Сохраняем текущую категорию в контексте пользователя
    user_context[message.chat.id] = {'category': category}
    
    markup = create_subcategory_menu(category)
    bot.send_message(
        message.chat.id,
        f"📁 Выберите подкатегорию в {category}:",
        reply_markup=markup
    )


def list_files(message, category, subcategory=None):
    """Показывает список файлов в выбранной категории или подкатегории"""
    # Сохраняем текущий контекст
    user_context[message.chat.id] = {
        'category': category,
        'subcategory': subcategory
    }
    
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
    response += "📑 Файлы:\n"
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


@bot.message_handler(commands=['files'])
def files_command(message):
    """Обработчик команды /files"""
    show_all_files(message)


@bot.message_handler(commands=['get'])
def get_command(message):
    """Обработчик команды /get"""
    try:
        # Получаем имя файла из команды
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Пожалуйста, укажите имя файла.\nПример: /get example.txt")
            return

        file_name = parts[1].strip()
        found = False

        # Ищем файл во всех категориях и подкатегориях
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
            error_msg = f"Файл {file_name} не найден"
            log_error(error_msg, message.from_user.id, f"Command: /get {file_name}")
            bot.reply_to(message, f"❌ {error_msg}")
    except Exception as e:
        error_msg = f"Произошла ошибка при получении файла: {str(e)}"
        log_error(error_msg, message.from_user.id, f"Command: /get {file_name if 'file_name' in locals() else 'unknown'}")
        bot.reply_to(message, f"❌ {error_msg}")


@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Обработчик загрузки файлов"""
    try:
        if not message.document:
            error_msg = "Файл не найден в сообщении"
            log_error(error_msg, message.from_user.id)
            bot.reply_to(message, f"❌ {error_msg}")
            return

        if not message.document.file_id:
            error_msg = "Не удалось получить идентификатор файла"
            log_error(error_msg, message.from_user.id)
            bot.reply_to(message, f"❌ {error_msg}")
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
    except Exception as e:
        error_msg = f"Ошибка при обработке документа: {str(e)}"
        log_error(error_msg, message.from_user.id)
        bot.reply_to(message, f"❌ {error_msg}")


def process_category_selection(message):
    """Обработчик выбора категории"""
    if message.text == '🔙 Вернуться в главное меню':
        markup = create_main_menu()
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)
        # Очищаем контекст при возврате в главное меню
        user_context.pop(message.chat.id, None)
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
        # Очищаем контекст при возврате в главное меню
        user_context.pop(message.chat.id, None)
        return
    elif message.text == '⬅️ Назад к категориям':
        show_categories(message)
        # Очищаем контекст при возврате к категориям
        user_context.pop(message.chat.id, None)
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
            error_msg = "Информация о файле не найдена"
            log_error(error_msg, message.from_user.id)
            bot.reply_to(message, f"❌ {error_msg}")
            return

        # Проверяем, существует ли файл с таким именем
        existing_files = file_handler.get_files_list(category, subcategory)
        for file in existing_files:
            if file['name'] == file_info['file_name']:
                error_msg = f"Файл с именем {file_info['file_name']} уже существует в этой категории"
                log_error(error_msg, message.from_user.id, f"Category: {category}, Subcategory: {subcategory}")
                markup = create_main_menu()
                bot.send_message(
                    message.chat.id,
                    f"❌ {error_msg}",
                    reply_markup=markup
                )
                uploading_files.pop(message.chat.id, None)
                return

        file_data = bot.get_file(file_info['file_id'])
        if not file_data:
            error_msg = "Не удалось получить информацию о файле"
            log_error(error_msg, message.from_user.id)
            bot.reply_to(message, f"❌ {error_msg}")
            return

        downloaded_file = bot.download_file(file_data.file_path)
        if not downloaded_file:
            error_msg = "Не удалось скачать файл"
            log_error(error_msg, message.from_user.id)
            bot.reply_to(message, f"❌ {error_msg}")
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
        error_msg = f"Произошла ошибка при сохранении файла: {str(e)}"
        log_error(error_msg, message.from_user.id, f"Category: {category}, Subcategory: {subcategory}")
        markup = create_main_menu()
        bot.send_message(
            message.chat.id,
            f"❌ {error_msg}",
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
        bot.send_message(message.chat.id, "📭 Файлы не найдены")
        return
    
    # Сортируем файлы по категории, подкатегории и имени
    all_files.sort(key=lambda x: (x['category'], x.get('subcategory', ''), x['name']))
    
    # Отправляем общее количество файлов с эмодзи и выделением
    total_files = len(all_files)
    counter_message = f"📊 *СТАТИСТИКА ФАЙЛОВ*\n\n📚 Всего файлов в системе: *{total_files}*"
    bot.send_message(message.chat.id, counter_message, parse_mode='Markdown')
    
    # Разбиваем список на части по 10 файлов
    for i in range(0, len(all_files), 10):
        chunk = all_files[i:i + 10]
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
    
    # Отправляем статистику еще раз в конце с эмодзи стрелочки вверх
    final_counter_message = f"⬆️ *СТАТИСТИКА ФАЙЛОВ*\n\n📚 Всего файлов в системе: *{total_files}*"
    bot.send_message(message.chat.id, final_counter_message, parse_mode='Markdown')


def search_files(message):
    """Поиск файлов по части имени"""
    # Получаем поисковый запрос
    search_query = message.text.strip()

    if not search_query:
        bot.reply_to(message, "🔍 Укажите поисковый запрос\nПример: docker")
        return

    # Собираем все файлы
    all_files = []
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

    # Ищем файлы, содержащие поисковый запрос
    found_files = []
    search_query = search_query.lower()
    for file in all_files:
        # Проверяем имя файла и категорию
        if (search_query in file['name'].lower() or 
            (search_query == 'книги' and file['category'] == 'Книги') or
            (search_query == '📚 книги' and file['category'] == 'Книги')):
            found_files.append(file)

    if not found_files:
        bot.reply_to(message, f"🔍 По запросу '{search_query}' ничего не найдено")
        return

    # Сортируем найденные файлы
    found_files.sort(key=lambda x: (x['category'], x.get('subcategory', ''), x['name']))

    # Отправляем статистику поиска
    total_found = len(found_files)
    counter_message = f"🔍 *РЕЗУЛЬТАТЫ ПОИСКА*\n\n📚 Найдено файлов: *{total_found}*\n🔎 Поисковый запрос: *{search_query}*"
    bot.send_message(message.chat.id, counter_message, parse_mode='Markdown')

    # Отправляем найденные файлы
    for i in range(0, len(found_files), 10):
        chunk = found_files[i:i + 10]
        response = ""
        for file in chunk:
            response += f"📄 {file['name']}\n"
            response += f"📂 Путь: {file['category']}"
            if 'subcategory' in file:
                response += f"/{file['subcategory']}"
            response += f"\n📊 Размер: {file['size']}\n"
            response += f"🕒 Дата: {file['date']}\n\n"

        if response:
            bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['search'])
def handle_search(message):
    """Обработчик команды поиска"""
    # Получаем поисковый запрос из команды
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "🔍 Укажите поисковый запрос\nПример: /search docker")
        return

    # Устанавливаем поисковый запрос и вызываем функцию поиска
    message.text = parts[1].strip()
    search_files(message)


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
    elif message.text == '🔍 Поиск файлов':
        bot.send_message(
            message.chat.id,
            "🔍 Введите поисковый запрос\nПример: docker"
        )
        bot.register_next_step_handler(message, search_files)
    elif message.text == '❓ Помощь':
        help_command(message)
    elif message.text == '⚙️ Дополнительно':
        markup = create_additional_menu()
        bot.send_message(
            message.chat.id,
            "⚙️ Выберите действие:",
            reply_markup=markup
        )
    elif message.text == '📊 Статистика скачиваний':
        show_download_stats(message)
    elif message.text == '📈 Краткая статистика':
        show_brief_stats(message)
    elif message.text == '👤 Мои скачивания':
        show_user_downloads(message)
    elif message.text == '📦 Скачать архив со всеми файлами':
        create_archive(message)
    elif message.text == '🔙 Вернуться в главное меню':
        markup = create_main_menu()
        bot.send_message(
            message.chat.id,
            "🏠 Главное меню:",
            reply_markup=markup
        )
        # Очищаем контекст при возврате в главное меню
        user_context.pop(message.chat.id, None)
    elif message.text == '⬅️ Назад к категориям':
        show_categories(message)
        # Очищаем контекст при возврате к категориям
        user_context.pop(message.chat.id, None)
    elif message.text == '⬅️ Назад к подкатегориям':
        # Получаем текущий контекст пользователя
        context = user_context.get(message.chat.id, {})
        category = context.get('category')
        
        if category and category in file_handler.subcategories:
            show_subcategories(message, category)
        else:
            # Если контекст не найден, возвращаемся к категориям
            show_categories(message)
    elif message.text.startswith('📂 ') or message.text == '📚 Книги':
        # Получаем название категории, убирая смайлик
        category = message.text[2:].strip() if message.text.startswith('📂 ') else "Книги"
        
        if category in file_handler.subcategories:
            show_subcategories(message, category)
        else:
            list_files(message, category)
    elif message.text.startswith('📁 '):
        subcategory = message.text[2:].strip()
        # Получаем текущий контекст пользователя
        context = user_context.get(message.chat.id, {})
        category = context.get('category')
        
        if category and subcategory in file_handler.subcategories.get(category, []):
            list_files(message, category, subcategory)
        else:
            # Если контекст не найден, ищем категорию с этой подкатегорией
            for cat in file_handler.subcategories:
                if subcategory in file_handler.subcategories[cat]:
                    list_files(message, cat, subcategory)
                    break
    elif message.text.startswith('📥 '):
        file_name = message.text[2:].strip()
        try:
            found = False
            for category in file_handler.categories:
                file_data = file_handler.get_file(file_name, category)
                if file_data is not None:
                    bot.send_document(
                        message.chat.id,
                        file_data,
                        visible_file_name=file_name
                    )
                    # Обновляем статистику скачиваний
                    if file_name not in download_stats:
                        download_stats[file_name] = {}
                    user_id = str(message.from_user.id)
                    download_stats[file_name][user_id] = download_stats[file_name].get(user_id, 0) + 1
                    save_stats()  # Сохраняем статистику после каждого скачивания
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
                            # Обновляем статистику скачиваний
                            if file_name not in download_stats:
                                download_stats[file_name] = {}
                            user_id = str(message.from_user.id)
                            download_stats[file_name][user_id] = download_stats[file_name].get(user_id, 0) + 1
                            save_stats()  # Сохраняем статистику после каждого скачивания
                            found = True
                            break
                    if found:
                        break
            
            if not found:
                bot.reply_to(message, f"❌ Файл {file_name} не найден.")
        except Exception as e:
            error_msg = f"Произошла ошибка при получении файла: {str(e)}"
            log_error(error_msg, message.from_user.id, f"File: {file_name}")
            bot.reply_to(message, f"❌ {error_msg}")
    else:
        # Если сообщение не является командой, используем его как поисковый запрос
        search_query = message.text.strip()
        if search_query:
            search_files(message)
        else:
            bot.send_message(
                message.chat.id,
                "❓ Неизвестная команда. Используйте меню или /help для получения списка команд."
            )


def show_download_stats(message):
    """Показывает статистику скачиваний файлов"""
    if not download_stats:
        bot.send_message(
            message.chat.id,
            "📊 Статистика скачиваний пуста.\nФайлы еще не скачивались."
        )
        return

    # Сортируем файлы по количеству скачиваний
    sorted_stats = sorted(
        download_stats.items(),
        key=lambda x: sum(x[1].values()),
        reverse=True
    )

    response = "📊 *СТАТИСТИКА СКАЧИВАНИЙ*\n\n"
    
    # Сначала показываем статистику архива, если он есть
    archive_stats = next((item for item in sorted_stats if item[0] == "📦 programming-documentation.zip"), None)
    if archive_stats:
        file_name, users = archive_stats
        total_downloads = sum(users.values())
        response += f"📦 *Архив с документацией*\n"
        response += f"📥 Всего скачиваний: *{total_downloads}*\n"
        # Показываем всех пользователей
        if users:
            response += "👥 *Список скачавших:*\n"
            sorted_users = sorted(users.items(), key=lambda x: x[1], reverse=True)
            for user_id, count in sorted_users:
                try:
                    # Пробуем получить информацию о пользователе
                    user = bot.get_chat_member(message.chat.id, int(user_id))
                    if user and user.user:
                        user_name = user.user.first_name
                        if user.user.last_name:
                            user_name += f" {user.user.last_name}"
                        username = f" (@{user.user.username})" if user.user.username else ""
                    else:
                        user_name = f"Пользователь {user_id}"
                        username = ""
                except Exception as e:
                    user_name = f"Пользователь {user_id}"
                    username = ""
                response += f"• {user_name}{username}: {count} раз\n"
        response += "\n"
    
    # Затем показываем статистику остальных файлов
    for file_name, users in sorted_stats:
        if file_name == "📦 programming-documentation.zip":  # Пропускаем архив, так как уже показали
            continue
        total_downloads = sum(users.values())
        response += f"📄 *{file_name}*\n"
        response += f"📥 Всего скачиваний: *{total_downloads}*\n"
        
        # Показываем всех пользователей
        if users:
            response += "👥 *Список скачавших:*\n"
            sorted_users = sorted(users.items(), key=lambda x: x[1], reverse=True)
            for user_id, count in sorted_users:
                try:
                    # Пробуем получить информацию о пользователе
                    user = bot.get_chat_member(message.chat.id, int(user_id))
                    if user and user.user:
                        user_name = user.user.first_name
                        if user.user.last_name:
                            user_name += f" {user.user.last_name}"
                        username = f" (@{user.user.username})" if user.user.username else ""
                    else:
                        user_name = f"Пользователь {user_id}"
                        username = ""
                except Exception as e:
                    user_name = f"Пользователь {user_id}"
                    username = ""
                response += f"• {user_name}{username}: {count} раз\n"
        response += "\n"

    # Разбиваем сообщение на части, если оно слишком длинное
    if len(response) > 4000:
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for part in parts:
            bot.send_message(message.chat.id, part, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, response, parse_mode='Markdown')


def show_brief_stats(message):
    """Показывает краткую статистику скачиваний файлов"""
    if not download_stats:
        bot.send_message(
            message.chat.id,
            "📊 Статистика скачиваний пуста.\nФайлы еще не скачивались."
        )
        return

    # Сортируем файлы по количеству скачиваний
    sorted_stats = sorted(
        download_stats.items(),
        key=lambda x: sum(x[1].values()),
        reverse=True
    )

    response = "📈 *КРАТКАЯ СТАТИСТИКА СКАЧИВАНИЙ*\n\n"
    
    # Сначала показываем статистику архива, если он есть
    archive_stats = next((item for item in sorted_stats if item[0] == "📦 programming-documentation.zip"), None)
    if archive_stats:
        file_name, users = archive_stats
        total_downloads = sum(users.values())
        unique_users = len(users)
        response += f"📦 *Архив с документацией*\n"
        response += f"📥 Всего скачиваний: *{total_downloads}*\n"
        response += f"👥 Уникальных скачавших: *{unique_users}*\n\n"
    
    # Затем показываем статистику остальных файлов
    for file_name, users in sorted_stats:
        if file_name == "📦 programming-documentation.zip":  # Пропускаем архив, так как уже показали
            continue
        total_downloads = sum(users.values())
        unique_users = len(users)
        response += f"📄 *{file_name}*\n"
        response += f"📥 Всего скачиваний: *{total_downloads}*\n"
        response += f"👥 Уникальных скачавших: *{unique_users}*\n\n"

    bot.send_message(message.chat.id, response, parse_mode='Markdown')


def show_user_downloads(message):
    """Показывает статистику скачиваний конкретного пользователя"""
    user_id = str(message.from_user.id)
    user_files = {}
    
    # Собираем все файлы, которые скачивал пользователь
    for file_name, users in download_stats.items():
        if user_id in users:
            user_files[file_name] = users[user_id]
    
    if not user_files:
        bot.send_message(
            message.chat.id,
            "📭 У вас пока нет скачанных файлов."
        )
        return

    # Сортируем файлы по количеству скачиваний
    sorted_files = sorted(
        user_files.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Получаем информацию о пользователе
    try:
        user = bot.get_chat_member(message.chat.id, int(user_id))
        if user and user.user:
            user_name = user.user.first_name
            if user.user.last_name:
                user_name += f" {user.user.last_name}"
            username = f" (@{user.user.username})" if user.user.username else ""
        else:
            user_name = f"Пользователь {user_id}"
            username = ""
    except Exception as e:
        user_name = f"Пользователь {user_id}"
        username = ""

    response = f"👤 *СТАТИСТИКА СКАЧИВАНИЙ*\n\n"
    response += f"Пользователь: *{user_name}{username}*\n\n"
    
    total_downloads = sum(user_files.values())
    unique_files = len(user_files)
    response += f"📥 Всего скачано файлов: *{total_downloads}*\n"
    response += f"📄 Уникальных файлов: *{unique_files}*\n\n"
    
    response += "📄 *Список скачанных файлов:*\n\n"
    
    # Сначала показываем архив, если он есть
    archive_downloads = next((item for item in sorted_files if item[0] == "📦 programming-documentation.zip"), None)
    if archive_downloads:
        file_name, count = archive_downloads
        response += f"• 📦 *Архив с документацией*: {count} раз\n"
    
    # Затем показываем остальные файлы
    for file_name, count in sorted_files:
        if file_name == "📦 programming-documentation.zip":  # Пропускаем архив, так как уже показали
            continue
        response += f"• *{file_name}*: {count} раз\n"

    bot.send_message(message.chat.id, response, parse_mode='Markdown')


def create_archive(message):
    """Создает архив со всеми файлами"""
    try:
        # Создаем архив в памяти
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Проходим по всем категориям
            for category in file_handler.categories:
                category_path = os.path.join(file_handler.base_dir, category)
                if os.path.exists(category_path):
                    # Добавляем файлы из основной категории
                    for root, dirs, files in os.walk(category_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Получаем относительный путь для архива
                            arcname = os.path.relpath(file_path, file_handler.base_dir)
                            zipf.write(file_path, arcname)

        # Перемещаем указатель в начало архива
        archive.seek(0)
        
        # Обновляем статистику скачиваний архива
        archive_name = "📦 programming-documentation.zip"
        if archive_name not in download_stats:
            download_stats[archive_name] = {}
        user_id = str(message.from_user.id)
        download_stats[archive_name][user_id] = download_stats[archive_name].get(user_id, 0) + 1
        save_stats()
        
        # Отправляем архив
        bot.send_document(
            message.chat.id,
            archive,
            visible_file_name='programming-documentation.zip',
            caption="📦 Архив с документацией по программированию"
        )
    except Exception as e:
        error_msg = f"Ошибка при создании архива: {str(e)}"
        log_error(error_msg, message.from_user.id)
        bot.reply_to(message, f"❌ {error_msg}")


if __name__ == "__main__":
    print("Бот запущен...")
    # Запускаем бота
    bot.polling(non_stop=True) 