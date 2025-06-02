#!/usr/bin/env python3
"""
Steam Workshop інтеграція для RimWorld Mod Builder
Підготовка модів для публікації в Steam Workshop
"""

import os
import shutil
import json
from pathlib import Path
from PIL import Image
import xml.etree.ElementTree as ET

class SteamWorkshopManager:
    """Менеджер для роботи з Steam Workshop"""
    
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.workshop_path = None
        self.mod_info = {}
        
    def detect_rimworld_path(self):
        """Автоматичне виявлення шляху до RimWorld"""
        possible_paths = [
            # Steam стандартні шляхи
            Path.home() / "AppData/LocalLow/Ludeon Studios/RimWorld by Ludeon Studios",
            Path("C:/Program Files (x86)/Steam/steamapps/common/RimWorld"),
            Path("C:/Program Files/Steam/steamapps/common/RimWorld"),
            Path("D:/Steam/steamapps/common/RimWorld"),
            Path("E:/Steam/steamapps/common/RimWorld"),
            
            # GOG та інші
            Path("C:/GOG Games/RimWorld"),
            Path("C:/Program Files/RimWorld"),
            
            # Користувацькі шляхи
            Path.home() / "Games/RimWorld",
        ]
        
        for path in possible_paths:
            if path.exists() and (path / "RimWorldWin64.exe").exists():
                return path
                
        return None
        
    def find_workshop_folder(self):
        """Пошук папки Workshop для RimWorld"""
        rimworld_path = self.detect_rimworld_path()
        if not rimworld_path:
            return None
            
        # Пошук Steam Workshop папки
        steam_path = rimworld_path.parent.parent.parent
        workshop_path = steam_path / "workshop/content/294100"  # 294100 - ID RimWorld
        
        if workshop_path.exists():
            return workshop_path
            
        return None
        
    def prepare_for_workshop(self, output_path=None):
        """Підготовка мода для Steam Workshop"""
        if not output_path:
            output_path = self.project_path.parent / f"{self.project_path.name}_Workshop"
            
        output_path = Path(output_path)
        
        try:
            # Створення папки для Workshop версії
            if output_path.exists():
                shutil.rmtree(output_path)
            output_path.mkdir(parents=True)
            
            # Копіювання основних файлів
            self._copy_mod_files(output_path)
            
            # Створення Preview.png
            self._create_preview_image(output_path)
            
            # Створення PublishedFileId.txt (якщо потрібно)
            self._create_published_file_id(output_path)
            
            # Валідація для Workshop
            validation_result = self._validate_for_workshop(output_path)
            
            return {
                'success': True,
                'output_path': output_path,
                'validation': validation_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def _copy_mod_files(self, output_path):
        """Копіювання файлів мода"""
        # Список папок для копіювання
        folders_to_copy = ['About', 'Defs', 'Textures', 'Assemblies', 'Languages', 'Sounds', 'Patches']
        
        for folder_name in folders_to_copy:
            source_folder = self.project_path / folder_name
            if source_folder.exists():
                dest_folder = output_path / folder_name
                shutil.copytree(source_folder, dest_folder)
                
        # Копіювання окремих файлів
        files_to_copy = ['LoadFolders.xml', 'Manifest.xml']
        for file_name in files_to_copy:
            source_file = self.project_path / file_name
            if source_file.exists():
                shutil.copy2(source_file, output_path / file_name)
                
    def _create_preview_image(self, output_path):
        """Створення Preview.png для Steam Workshop"""
        preview_path = output_path / "Preview.png"
        
        # Пошук існуючого preview
        existing_preview = self.project_path / "About" / "Preview.png"
        if existing_preview.exists():
            # Копіювання та оптимізація існуючого preview
            img = Image.open(existing_preview)
            
            # Steam Workshop вимагає 512x512 або більше
            if img.size[0] < 512 or img.size[1] < 512:
                img = img.resize((512, 512), Image.Resampling.LANCZOS)
                
            img.save(preview_path, 'PNG', optimize=True)
        else:
            # Створення базового preview
            self._generate_default_preview(preview_path)
            
    def _generate_default_preview(self, preview_path):
        """Генерація базового preview зображення"""
        # Читання інформації про мод
        about_xml = self.project_path / "About" / "About.xml"
        mod_name = "Unknown Mod"
        mod_author = "Unknown Author"
        
        if about_xml.exists():
            try:
                tree = ET.parse(about_xml)
                root = tree.getroot()
                
                name_elem = root.find('name')
                if name_elem is not None:
                    mod_name = name_elem.text or mod_name
                    
                author_elem = root.find('author')
                if author_elem is not None:
                    mod_author = author_elem.text or mod_author
                    
            except Exception:
                pass
                
        # Створення простого preview
        img = Image.new('RGB', (512, 512), color='#2C3E50')
        
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            
            # Спроба використати системний шрифт
            try:
                font_large = ImageFont.truetype("arial.ttf", 36)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Малювання тексту
            draw.text((256, 200), mod_name, font=font_large, anchor="mm", fill='white')
            draw.text((256, 280), f"by {mod_author}", font=font_small, anchor="mm", fill='#BDC3C7')
            draw.text((256, 350), "RimWorld Mod", font=font_small, anchor="mm", fill='#3498DB')
            
        except ImportError:
            # Якщо PIL не підтримує текст, створюємо просте зображення
            pass
            
        img.save(preview_path, 'PNG')
        
    def _create_published_file_id(self, output_path):
        """Створення PublishedFileId.txt для оновлення існуючого мода"""
        # Цей файл створюється тільки якщо мод вже опублікований
        # Користувач може додати його вручну з ID з Steam Workshop
        pass
        
    def _validate_for_workshop(self, output_path):
        """Валідація мода для Steam Workshop"""
        issues = []
        warnings = []
        
        # Перевірка обов'язкових файлів
        required_files = [
            'About/About.xml',
            'Preview.png'
        ]
        
        for file_path in required_files:
            if not (output_path / file_path).exists():
                issues.append(f"Відсутній обов'язковий файл: {file_path}")
                
        # Перевірка About.xml
        about_xml = output_path / "About" / "About.xml"
        if about_xml.exists():
            try:
                tree = ET.parse(about_xml)
                root = tree.getroot()
                
                # Перевірка обов'язкових полів
                required_fields = ['name', 'author', 'packageId', 'supportedVersions']
                for field in required_fields:
                    if root.find(field) is None:
                        issues.append(f"Відсутнє поле в About.xml: {field}")
                        
                # Перевірка packageId формату
                package_id = root.find('packageId')
                if package_id is not None and package_id.text:
                    if '.' not in package_id.text:
                        warnings.append("packageId повинен містити крапку (наприклад: author.modname)")
                        
            except Exception as e:
                issues.append(f"Помилка читання About.xml: {str(e)}")
                
        # Перевірка Preview.png
        preview_png = output_path / "Preview.png"
        if preview_png.exists():
            try:
                img = Image.open(preview_png)
                if img.size[0] < 512 or img.size[1] < 512:
                    warnings.append("Preview.png менше 512x512 пікселів")
                if img.size[0] != img.size[1]:
                    warnings.append("Preview.png не квадратний (рекомендується квадратний)")
            except Exception as e:
                issues.append(f"Помилка Preview.png: {str(e)}")
                
        # Перевірка розміру мода
        total_size = self._calculate_folder_size(output_path)
        if total_size > 100 * 1024 * 1024:  # 100 MB
            warnings.append(f"Мод дуже великий: {total_size // (1024*1024)} MB")
            
        return {
            'issues': issues,
            'warnings': warnings,
            'valid': len(issues) == 0
        }
        
    def _calculate_folder_size(self, folder_path):
        """Розрахунок розміру папки"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                total_size += os.path.getsize(file_path)
        return total_size
        
    def create_workshop_description(self):
        """Створення опису для Steam Workshop"""
        about_xml = self.project_path / "About" / "About.xml"
        
        if not about_xml.exists():
            return "Опис мода недоступний."
            
        try:
            tree = ET.parse(about_xml)
            root = tree.getroot()
            
            name = root.find('name')
            author = root.find('author')
            description = root.find('description')
            supported_versions = root.find('supportedVersions')
            
            # Формування опису
            desc_parts = []
            
            if description is not None and description.text:
                desc_parts.append(description.text.strip())
                
            desc_parts.append("\n[h1]Інформація про мод[/h1]")
            
            if author is not None and author.text:
                desc_parts.append(f"[b]Автор:[/b] {author.text}")
                
            if supported_versions is not None:
                versions = [li.text for li in supported_versions.findall('li') if li.text]
                if versions:
                    desc_parts.append(f"[b]Підтримувані версії:[/b] {', '.join(versions)}")
                    
            desc_parts.append("\n[h1]Встановлення[/h1]")
            desc_parts.append("1. Підпишіться на мод")
            desc_parts.append("2. Увімкніть мод у списку модів гри")
            desc_parts.append("3. Перезапустіть гру")
            
            desc_parts.append("\n[i]Створено за допомогою RimWorld Mod Builder[/i]")
            
            return "\n".join(desc_parts)
            
        except Exception as e:
            return f"Помилка створення опису: {str(e)}"
            
    def get_workshop_guidelines(self):
        """Отримання рекомендацій для Steam Workshop"""
        return {
            'preview_image': {
                'min_size': '512x512 пікселів',
                'recommended_size': '1024x1024 пікселів',
                'format': 'PNG або JPG',
                'content': 'Показуйте ключові особливості мода'
            },
            'description': {
                'language': 'Використовуйте зрозумілу мову',
                'formatting': 'Використовуйте BBCode для форматування',
                'content': 'Опишіть що робить мод та як його використовувати'
            },
            'tags': {
                'relevant': 'Використовуйте релевантні теги',
                'limit': 'Максимум 5 тегів',
                'examples': ['Gameplay', 'Items', 'Buildings', 'Quality of Life']
            },
            'compatibility': {
                'versions': 'Вказуйте підтримувані версії RimWorld',
                'mods': 'Згадуйте сумісність з іншими модами',
                'conflicts': 'Попереджайте про можливі конфлікти'
            }
        }

    def export_for_local_testing(self, rimworld_mods_path):
        """Експорт мода для локального тестування"""
        if not rimworld_mods_path:
            return {'success': False, 'error': 'Не вказано шлях до папки модів RimWorld'}

        try:
            mods_path = Path(rimworld_mods_path)
            if not mods_path.exists():
                return {'success': False, 'error': 'Папка модів RimWorld не існує'}

            # Назва папки мода
            mod_folder_name = self.project_path.name
            dest_path = mods_path / mod_folder_name

            # Видалення існуючої версії
            if dest_path.exists():
                shutil.rmtree(dest_path)

            # Копіювання мода
            shutil.copytree(self.project_path, dest_path)

            return {
                'success': True,
                'destination': dest_path,
                'message': f'Мод скопійовано до {dest_path}'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
