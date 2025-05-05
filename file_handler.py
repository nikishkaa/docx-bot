import os
from datetime import datetime

class FileHandler:
    def __init__(self):
        self.upload_dir = "uploads"
        self.categories = ["Java", "AI", "DevOps", "Other"]
        self.subcategories = {
            "DevOps": ["Docker", "Kubernetes"]
        }
        self._create_directories()

    def _create_directories(self):
        """Создает необходимые директории для хранения файлов"""
        # Создаем основную директорию uploads, если её нет
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
        
        # Создаем подпапки для каждой категории
        for category in self.categories:
            category_path = os.path.join(self.upload_dir, category)
            if not os.path.exists(category_path):
                os.makedirs(category_path)
            
            # Создаем подпапки для подкатегорий, если они есть
            if category in self.subcategories:
                for subcategory in self.subcategories[category]:
                    subcategory_path = os.path.join(category_path, subcategory)
                    if not os.path.exists(subcategory_path):
                        os.makedirs(subcategory_path)

    def save_file(self, file_id, file_name, file_data, category="Other", subcategory=None):
        """Сохраняет файл в указанную категорию"""
        # Определяем путь для сохранения файла
        if subcategory and category in self.subcategories and subcategory in self.subcategories[category]:
            save_path = os.path.join(self.upload_dir, category, subcategory, file_name)
        else:
            save_path = os.path.join(self.upload_dir, category, file_name)
        
        # Сохраняем файл
        with open(save_path, 'wb') as f:
            f.write(file_data)
        
        return save_path

    def get_file(self, file_name, category=None, subcategory=None):
        """Получает файл по имени"""
        # Если указана категория и подкатегория, ищем в конкретной подпапке
        if category and subcategory and category in self.subcategories and subcategory in self.subcategories[category]:
            file_path = os.path.join(self.upload_dir, category, subcategory, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
        
        # Если указана только категория, ищем в папке категории
        if category:
            file_path = os.path.join(self.upload_dir, category, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
        
        # Если категория не указана, ищем во всех папках
        for category in self.categories:
            # Проверяем в основной папке категории
            file_path = os.path.join(self.upload_dir, category, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
            
            # Проверяем в подпапках категории
            if category in self.subcategories:
                for subcategory in self.subcategories[category]:
                    file_path = os.path.join(self.upload_dir, category, subcategory, file_name)
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            return f.read()
        
        return None

    def get_files_list(self, category=None, subcategory=None):
        """Получает список файлов в указанной категории"""
        files = []
        
        if category and subcategory and category in self.subcategories and subcategory in self.subcategories[category]:
            # Получаем файлы из конкретной подпапки
            category_path = os.path.join(self.upload_dir, category, subcategory)
            if os.path.exists(category_path):
                files.extend(self._get_category_files(category_path, category, subcategory))
        elif category:
            # Получаем файлы из папки категории
            category_path = os.path.join(self.upload_dir, category)
            if os.path.exists(category_path):
                files.extend(self._get_category_files(category_path, category))
        else:
            # Получаем файлы из всех категорий
            for category in self.categories:
                category_path = os.path.join(self.upload_dir, category)
                if os.path.exists(category_path):
                    files.extend(self._get_category_files(category_path, category))
        
        return files

    def _get_category_files(self, category_path, category, subcategory=None):
        """Получает информацию о файлах в указанной категории"""
        files = []
        for file_name in os.listdir(category_path):
            file_path = os.path.join(category_path, file_name)
            if os.path.isfile(file_path):
                file_info = {
                    'name': file_name,
                    'size': self._format_size(os.path.getsize(file_path)),
                    'date': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                    'category': category
                }
                if subcategory:
                    file_info['subcategory'] = subcategory
                files.append(file_info)
        return files

    def _format_size(self, size):
        """Форматирует размер файла в читаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB" 