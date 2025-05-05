import os
from datetime import datetime

class FileHandler:
    def __init__(self):
        self.upload_dir = "uploads"
        self.categories = ["Java", "DevOps", "Other"]
        self._create_directories()

    def _create_directories(self):
        """Создает основную директорию и подпапки для категорий"""
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
        
        # Создаем подпапки для каждой категории
        for category in self.categories:
            category_path = os.path.join(self.upload_dir, category)
            if not os.path.exists(category_path):
                os.makedirs(category_path)

    def save_file(self, file_id, file_name, file_data, category="Other"):
        """Сохраняет файл в указанную категорию"""
        if category not in self.categories:
            category = "Other"
        
        category_path = os.path.join(self.upload_dir, category)
        file_path = os.path.join(category_path, file_name)
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        return file_path

    def get_file(self, file_name, category=None):
        """Получает файл по имени и категории"""
        if category:
            # Если указана категория, ищем только в ней
            file_path = os.path.join(self.upload_dir, category, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
        else:
            # Если категория не указана, ищем во всех папках
            for cat in self.categories:
                file_path = os.path.join(self.upload_dir, cat, file_name)
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        return f.read()
        return None

    def get_files_list(self, category=None):
        """Возвращает список файлов, опционально фильтруя по категории"""
        files = []
        
        if category and category in self.categories:
            # Получаем файлы только из указанной категории
            category_path = os.path.join(self.upload_dir, category)
            if os.path.exists(category_path):
                files.extend(self._get_category_files(category_path, category))
        else:
            # Получаем файлы из всех категорий
            for cat in self.categories:
                category_path = os.path.join(self.upload_dir, cat)
                if os.path.exists(category_path):
                    files.extend(self._get_category_files(category_path, cat))
        
        return files

    def _get_category_files(self, category_path, category):
        """Получает список файлов из конкретной категории"""
        files = []
        for filename in os.listdir(category_path):
            file_path = os.path.join(category_path, filename)
            file_stats = os.stat(file_path)
            file_info = {
                'name': filename,
                'size': self._format_size(file_stats.st_size),
                'date': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'category': category
            }
            files.append(file_info)
        return files

    def _format_size(self, size_bytes):
        """Форматирует размер файла в читаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB" 