"""
Менеджер проєктів для управління модами RimWorld
"""

import os
import json
import sys
from typing import Dict, List, Optional

# Додаємо шлях для імпорту utils
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(os.path.dirname(current_dir), 'utils')
if utils_dir not in sys.path:
    sys.path.insert(0, utils_dir)

try:
    from xml_validator import XmlValidator
except ImportError:
    # Fallback для випадку, коли модуль не знайдено
    class XmlValidator:
        def validate_file(self, file_path):
            return {"valid": True, "errors": [], "warnings": []}


class ProjectManager:
    """Клас для управління проєктами модів"""

    def __init__(self):
        self.current_project_path = None
        self.project_config = {}
        self.xml_validator = XmlValidator()

    def create_new_project(self, project_path: str, mod_info: Dict) -> bool:
        """
        Створення нового проєкту мода

        Args:
            project_path: Шлях до папки проєкту
            mod_info: Інформація про мод (назва, автор, опис тощо)

        Returns:
            True якщо проєкт створено успішно, False інакше
        """
        try:
            # Створюємо структуру папок
            self._create_mod_structure(project_path)

            # Створюємо About.xml
            self._create_about_xml(project_path, mod_info)

            # Створюємо конфігураційний файл проєкту
            self._create_project_config(project_path, mod_info)

            self.current_project_path = project_path
            return True

        except Exception as e:
            print(f"Помилка створення проєкту: {e}")
            return False

    def _create_mod_structure(self, project_path: str):
        """Створення стандартної структури папок мода"""
        folders = [
            "About",
            "Defs",
            "Defs/ThingDefs",
            "Defs/RecipeDefs",
            "Defs/PawnKindDefs",
            "Defs/BiomeDefs",
            "Defs/ResearchProjectDefs",
            "Patches",
            "Textures",
            "Textures/Things",
            "Textures/Things/Items",
            "Textures/Things/Buildings",
            "Textures/UI",
            "Sounds",
            "Languages",
            "Languages/English",
            "Languages/English/Keyed",
            "Languages/English/DefInjected",
            "Languages/Ukrainian",
            "Languages/Ukrainian/Keyed",
            "Languages/Ukrainian/DefInjected",
            "Assemblies"
        ]

        for folder in folders:
            folder_path = os.path.join(project_path, folder)
            os.makedirs(folder_path, exist_ok=True)

    def _create_about_xml(self, project_path: str, mod_info: Dict):
        """Створення файлу About.xml"""
        about_content = f"""<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
    <name>{mod_info.get('name', 'New Mod')}</name>
    <author>{mod_info.get('author', 'Unknown Author')}</author>
    <packageId>{mod_info.get('package_id', 'author.modname')}</packageId>
    <description>{mod_info.get('description', 'Mod description')}</description>
    <url>{mod_info.get('url', '')}</url>
    <supportedVersions>
        <li>{mod_info.get('version', '1.5')}</li>
    </supportedVersions>
    <modDependencies>
        <!-- Додайте залежності тут -->
    </modDependencies>
    <loadAfter>
        <!-- Моди, після яких завантажувати цей мод -->
    </loadAfter>
    <loadBefore>
        <!-- Моди, перед якими завантажувати цей мод -->
    </loadBefore>
</ModMetaData>"""

        about_path = os.path.join(project_path, "About", "About.xml")
        with open(about_path, 'w', encoding='utf-8') as f:
            f.write(about_content)

    def _create_project_config(self, project_path: str, mod_info: Dict):
        """Створення конфігураційного файлу проєкту"""
        config = {
            "project_name": mod_info.get('name', 'New Mod'),
            "project_version": "1.0.0",
            "created_date": "",
            "last_modified": "",
            "mod_info": mod_info,
            "settings": {
                "auto_backup": True,
                "validate_xml": True,
                "compress_textures": False
            }
        }

        config_path = os.path.join(project_path, ".rwmbuilder_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def load_project(self, project_path: str) -> bool:
        """
        Завантаження існуючого проєкту

        Args:
            project_path: Шлях до папки проєкту

        Returns:
            True якщо проєкт завантажено успішно, False інакше
        """
        try:
            # Перевіряємо, чи це валідний проєкт мода
            if not self._is_valid_mod_project(project_path):
                return False

            # Завантажуємо конфігурацію проєкту
            config_path = os.path.join(project_path, ".rwmbuilder_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.project_config = json.load(f)
            else:
                # Створюємо базову конфігурацію для існуючого проєкту
                self.project_config = self._create_default_config(project_path)

            self.current_project_path = project_path
            return True

        except Exception as e:
            print(f"Помилка завантаження проєкту: {e}")
            return False

    def _is_valid_mod_project(self, project_path: str) -> bool:
        """Перевірка, чи є папка валідним проєктом мода"""
        # Перевіряємо наявність About.xml
        about_path = os.path.join(project_path, "About", "About.xml")
        return os.path.exists(about_path)

    def _create_default_config(self, project_path: str) -> Dict:
        """Створення базової конфігурації для існуючого проєкту"""
        # Спробуємо прочитати інформацію з About.xml
        about_path = os.path.join(project_path, "About", "About.xml")
        mod_info = {}

        if os.path.exists(about_path):
            try:
                # Тут можна додати парсинг XML для отримання інформації
                mod_info = {"name": "Existing Mod", "author": "Unknown"}
            except:
                pass

        return {
            "project_name": mod_info.get('name', 'Existing Mod'),
            "project_version": "1.0.0",
            "mod_info": mod_info,
            "settings": {
                "auto_backup": True,
                "validate_xml": True,
                "compress_textures": False
            }
        }

    def get_project_files(self) -> List[str]:
        """Отримання списку файлів проєкту"""
        if not self.current_project_path:
            return []

        files = []
        for root, dirs, filenames in os.walk(self.current_project_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append(file_path)

        return files

    def validate_project(self) -> Dict:
        """
        Валідація проєкту

        Returns:
            Словник з результатами валідації
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        if not self.current_project_path:
            results["valid"] = False
            results["errors"].append("Проєкт не завантажено")
            return results

        # Перевіряємо структуру папок
        required_folders = ["About", "Defs"]
        for folder in required_folders:
            folder_path = os.path.join(self.current_project_path, folder)
            if not os.path.exists(folder_path):
                results["errors"].append(f"Відсутня обов'язкова папка: {folder}")
                results["valid"] = False

        # Перевіряємо About.xml
        about_path = os.path.join(self.current_project_path, "About", "About.xml")
        if not os.path.exists(about_path):
            results["errors"].append("Відсутній файл About.xml")
            results["valid"] = False
        else:
            # Валідуємо XML
            xml_result = self.xml_validator.validate_file(about_path)
            if not xml_result["valid"]:
                results["errors"].extend(xml_result["errors"])
                results["valid"] = False

        # Перевіряємо XML файли в Defs
        defs_path = os.path.join(self.current_project_path, "Defs")
        if os.path.exists(defs_path):
            for root, dirs, files in os.walk(defs_path):
                for file in files:
                    if file.endswith('.xml'):
                        file_path = os.path.join(root, file)
                        xml_result = self.xml_validator.validate_file(file_path)
                        if not xml_result["valid"]:
                            results["warnings"].extend([
                                f"{file}: {error}" for error in xml_result["errors"]
                            ])

        return results

    def export_mod(self, export_path: str, export_type: str = "folder",
                   steam_workshop: bool = False, progress_callback=None) -> bool:
        """
        Експорт мода для використання в грі

        Args:
            export_path: Шлях для експорту
            export_type: Тип експорту ("folder", "zip")
            steam_workshop: Підготовка для Steam Workshop
            progress_callback: Функція для відображення прогресу

        Returns:
            True якщо експорт успішний, False інакше
        """
        if not self.current_project_path:
            return False

        try:
            import shutil
            import zipfile
            import tempfile
            from datetime import datetime

            # Валідуємо проєкт перед експортом
            validation = self.validate_project()
            if not validation["valid"]:
                print(f"Проєкт не пройшов валідацію: {validation['errors']}")
                return False

            # Створюємо тимчасову папку для підготовки
            with tempfile.TemporaryDirectory() as temp_dir:
                mod_name = self.project_config.get("project_name", "UnknownMod")
                temp_mod_path = os.path.join(temp_dir, mod_name)

                if progress_callback:
                    progress_callback(10, "Копіювання файлів...")

                # Копіюємо файли проєкту
                self._copy_project_files(temp_mod_path, progress_callback)

                if progress_callback:
                    progress_callback(50, "Підготовка метаданих...")

                # Підготовка для Steam Workshop
                if steam_workshop:
                    self._prepare_steam_workshop(temp_mod_path)

                if progress_callback:
                    progress_callback(70, "Створення експорту...")

                # Експорт в залежності від типу
                if export_type == "zip":
                    success = self._create_zip_export(temp_mod_path, export_path, mod_name, progress_callback)
                else:
                    success = self._create_folder_export(temp_mod_path, export_path, progress_callback)

                if progress_callback:
                    progress_callback(100, "Експорт завершено!")

                return success

        except Exception as e:
            print(f"Помилка експорту: {e}")
            return False

    def _copy_project_files(self, dest_path: str, progress_callback=None):
        """Копіювання файлів проєкту з фільтрацією"""
        import shutil

        # Файли та папки, які потрібно виключити
        exclude_patterns = {
            '.rwmbuilder_config.json',
            '.git', '.gitignore',
            '__pycache__', '*.pyc',
            '.vscode', '.idea',
            'Thumbs.db', '.DS_Store'
        }

        def should_exclude(item_name: str) -> bool:
            for pattern in exclude_patterns:
                if pattern.startswith('.') and item_name.startswith(pattern):
                    return True
                if pattern.endswith('*') and item_name.endswith(pattern[:-1]):
                    return True
                if item_name == pattern:
                    return True
            return False

        os.makedirs(dest_path, exist_ok=True)

        items = os.listdir(self.current_project_path)
        total_items = len(items)

        for i, item in enumerate(items):
            if should_exclude(item):
                continue

            src = os.path.join(self.current_project_path, item)
            dst = os.path.join(dest_path, item)

            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

            if progress_callback and total_items > 0:
                progress = 10 + (i / total_items) * 40  # 10-50%
                progress_callback(int(progress), f"Копіювання {item}...")

    def _prepare_steam_workshop(self, mod_path: str):
        """Підготовка для Steam Workshop"""
        # Створюємо PublishedFileId.txt якщо не існує
        published_file_path = os.path.join(mod_path, "About", "PublishedFileId.txt")
        if not os.path.exists(published_file_path):
            with open(published_file_path, 'w') as f:
                f.write("0")  # Буде замінено Steam при першій публікації

        # Перевіряємо наявність Preview.png
        preview_path = os.path.join(mod_path, "About", "Preview.png")
        if not os.path.exists(preview_path):
            # Створюємо базове зображення попереднього перегляду
            self._create_default_preview(preview_path)

    def _create_default_preview(self, preview_path: str):
        """Створення базового зображення попереднього перегляду"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Створюємо зображення 512x512 (рекомендований розмір для Steam)
            img = Image.new('RGB', (512, 512), color='#2C3E50')
            draw = ImageDraw.Draw(img)

            # Додаємо текст
            mod_name = self.project_config.get("project_name", "RimWorld Mod")

            try:
                # Спробуємо використати системний шрифт
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                # Якщо не вдалося, використовуємо базовий
                font = ImageFont.load_default()

            # Центруємо текст
            bbox = draw.textbbox((0, 0), mod_name, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (512 - text_width) // 2
            y = (512 - text_height) // 2

            draw.text((x, y), mod_name, fill='white', font=font)

            # Зберігаємо
            img.save(preview_path, 'PNG')

        except Exception as e:
            print(f"Не вдалося створити Preview.png: {e}")

    def _create_zip_export(self, mod_path: str, export_path: str, mod_name: str, progress_callback=None) -> bool:
        """Створення ZIP архіву"""
        import zipfile
        from datetime import datetime

        # Створюємо назву файлу з датою
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"{mod_name}_{timestamp}.zip"
        zip_path = os.path.join(export_path, zip_filename)

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Рекурсивно додаємо всі файли
                for root, dirs, files in os.walk(mod_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, mod_path)
                        zipf.write(file_path, arc_path)

                        if progress_callback:
                            progress_callback(80, f"Архівування {file}...")

            return True

        except Exception as e:
            print(f"Помилка створення ZIP: {e}")
            return False

    def _create_folder_export(self, mod_path: str, export_path: str, progress_callback=None) -> bool:
        """Створення експорту в папку"""
        import shutil

        try:
            mod_name = os.path.basename(mod_path)
            final_path = os.path.join(export_path, mod_name)

            # Видаляємо існуючу папку якщо є
            if os.path.exists(final_path):
                shutil.rmtree(final_path)

            # Копіюємо підготовлену папку
            shutil.copytree(mod_path, final_path)

            if progress_callback:
                progress_callback(90, "Завершення експорту...")

            return True

        except Exception as e:
            print(f"Помилка створення папки експорту: {e}")
            return False
