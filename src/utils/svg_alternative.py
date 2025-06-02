#!/usr/bin/env python3
"""
Альтернативна обробка SVG файлів без залежності від cairosvg
Надає інструкції та альтернативи для роботи з SVG файлами
"""

import os
import re
import xml.etree.ElementTree as ET
import subprocess
import shutil
from typing import Optional, Tuple, Dict, List
from PIL import Image, ImageDraw
import io


class SVGAlternativeHandler:
    """Альтернативна обробка SVG файлів без cairosvg"""
    
    def __init__(self):
        self.supported_alternatives = [
            "PNG", "JPEG", "BMP", "TIFF", "WEBP"
        ]
    
    def extract_svg_dimensions(self, svg_path: str) -> Tuple[int, int]:
        """Витягування розмірів SVG з XML"""
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Пошук розмірів в SVG тегу
            svg_match = re.search(r'<svg[^>]*>', content, re.IGNORECASE)
            if not svg_match:
                return (256, 256)  # Значення за замовчуванням
            
            svg_tag = svg_match.group(0)
            
            # Пошук width та height
            width_match = re.search(r'width\s*=\s*["\']?(\d+(?:\.\d+)?)', svg_tag)
            height_match = re.search(r'height\s*=\s*["\']?(\d+(?:\.\d+)?)', svg_tag)
            
            width = int(float(width_match.group(1))) if width_match else 256
            height = int(float(height_match.group(1))) if height_match else 256
            
            # Якщо розміри не знайдені, спробувати viewBox
            if not width_match or not height_match:
                viewbox_match = re.search(r'viewBox\s*=\s*["\']?[\d\s]*\s+[\d\s]*\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)', svg_tag)
                if viewbox_match:
                    width = int(float(viewbox_match.group(1)))
                    height = int(float(viewbox_match.group(2)))
            
            return (width, height)
            
        except Exception as e:
            print(f"Помилка читання SVG розмірів: {e}")
            return (256, 256)
    
    def get_svg_info(self, svg_path: str) -> Dict:
        """Отримання інформації про SVG файл"""
        info = {
            "valid_svg": False,
            "width": 0,
            "height": 0,
            "file_size": 0,
            "has_text": False,
            "has_paths": False,
            "has_images": False,
            "complexity": "Unknown"
        }
        
        try:
            info["file_size"] = os.path.getsize(svg_path)
            
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Перевірка чи це SVG файл
            if '<svg' not in content.lower():
                return info
            
            info["valid_svg"] = True
            
            # Отримання розмірів
            width, height = self.extract_svg_dimensions(svg_path)
            info["width"] = width
            info["height"] = height
            
            # Аналіз вмісту
            info["has_text"] = '<text' in content.lower() or '<tspan' in content.lower()
            info["has_paths"] = '<path' in content.lower()
            info["has_images"] = '<image' in content.lower()
            
            # Оцінка складності
            element_count = len(re.findall(r'<[^/!?][^>]*>', content))
            if element_count < 10:
                info["complexity"] = "Простий"
            elif element_count < 50:
                info["complexity"] = "Середній"
            else:
                info["complexity"] = "Складний"
                
        except Exception as e:
            print(f"Помилка аналізу SVG: {e}")
        
        return info
    
    def convert_svg_via_inkscape(self, svg_path: str, output_path: str = None, size: Tuple[int, int] = None) -> Optional[str]:
        """Конвертація SVG через Inkscape (якщо встановлений)"""
        if not self.is_inkscape_available():
            return None
        
        if output_path is None:
            output_path = svg_path.replace('.svg', '.png')
        
        try:
            cmd = ['inkscape']
            
            # Налаштування розміру
            if size:
                cmd.extend(['-w', str(size[0]), '-h', str(size[1])])
            
            # Вхідний та вихідний файли
            cmd.extend(['-o', output_path, svg_path])
            
            # Виконання команди
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                print(f"Помилка Inkscape: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Timeout при конвертації через Inkscape")
            return None
        except Exception as e:
            print(f"Помилка виконання Inkscape: {e}")
            return None
    
    def convert_svg_via_imagemagick(self, svg_path: str, output_path: str = None, size: Tuple[int, int] = None) -> Optional[str]:
        """Конвертація SVG через ImageMagick (якщо встановлений)"""
        if not self.is_imagemagick_available():
            return None
        
        if output_path is None:
            output_path = svg_path.replace('.svg', '.png')
        
        try:
            cmd = ['magick', 'convert']
            
            # Налаштування розміру
            if size:
                cmd.extend(['-size', f'{size[0]}x{size[1]}'])
            
            # Вхідний та вихідний файли
            cmd.extend([svg_path, output_path])
            
            # Виконання команди
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                print(f"Помилка ImageMagick: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("Timeout при конвертації через ImageMagick")
            return None
        except Exception as e:
            print(f"Помилка виконання ImageMagick: {e}")
            return None
    
    def is_inkscape_available(self) -> bool:
        """Перевірка доступності Inkscape"""
        return shutil.which('inkscape') is not None
    
    def is_imagemagick_available(self) -> bool:
        """Перевірка доступності ImageMagick"""
        return shutil.which('magick') is not None or shutil.which('convert') is not None
    
    def create_svg_placeholder(self, svg_path: str, output_path: str = None) -> str:
        """Створення placeholder зображення для SVG файлу"""
        if output_path is None:
            output_path = svg_path.replace('.svg', '_placeholder.png')
        
        try:
            # Отримання інформації про SVG
            svg_info = self.get_svg_info(svg_path)
            width = min(svg_info["width"], 512) if svg_info["width"] > 0 else 256
            height = min(svg_info["height"], 512) if svg_info["height"] > 0 else 256
            
            # Створення placeholder зображення
            placeholder = Image.new('RGB', (width, height), color='lightblue')
            
            # Додавання тексту
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(placeholder)
                
                # Спроба використати системний шрифт
                try:
                    font = ImageFont.truetype("arial.ttf", 24)
                except:
                    font = ImageFont.load_default()
                
                text = "SVG\nFile"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                draw.text((x, y), text, fill='darkblue', font=font)
                
                # Додавання рамки
                draw.rectangle([0, 0, width-1, height-1], outline='darkblue', width=2)
                
            except ImportError:
                pass
            
            placeholder.save(output_path, "PNG")
            return output_path
            
        except Exception as e:
            print(f"Помилка створення SVG placeholder: {e}")
            return None
    
    def suggest_svg_conversion_methods(self, svg_path: str) -> List[Dict]:
        """Пропозиція методів конвертації SVG файлів"""
        suggestions = []
        
        # Inkscape (якщо доступний)
        if self.is_inkscape_available():
            suggestions.append({
                "method": "Inkscape (встановлений)",
                "description": "Використання встановленого Inkscape для конвертації",
                "steps": [
                    "1. Автоматична конвертація через Inkscape",
                    "2. Висока якість векторної графіки",
                    "3. Підтримка всіх SVG функцій"
                ],
                "pros": ["Найкраща якість", "Автоматично", "Підтримка всіх функцій"],
                "cons": [],
                "available": True
            })
        else:
            suggestions.append({
                "method": "Inkscape (рекомендовано)",
                "description": "Встановіть Inkscape для найкращої конвертації SVG",
                "steps": [
                    "1. Завантажте Inkscape з inkscape.org",
                    "2. Встановіть програму",
                    "3. Перезапустіть RimWorld Mod Builder",
                    "4. SVG файли будуть конвертуватися автоматично"
                ],
                "pros": ["Найкраща якість", "Безкоштовно", "Автоматична конвертація"],
                "cons": ["Потребує встановлення"],
                "available": False
            })
        
        # ImageMagick (якщо доступний)
        if self.is_imagemagick_available():
            suggestions.append({
                "method": "ImageMagick (встановлений)",
                "description": "Використання встановленого ImageMagick",
                "steps": [
                    "1. Автоматична конвертація через ImageMagick",
                    "2. Хороша якість для простих SVG"
                ],
                "pros": ["Автоматично", "Швидко"],
                "cons": ["Обмежена підтримка складних SVG"],
                "available": True
            })
        
        # Ручні методи
        suggestions.extend([
            {
                "method": "Онлайн конвертери",
                "description": "Використання онлайн сервісів для конвертації",
                "steps": [
                    "1. Відкрийте convertio.co/svg-png/",
                    "2. Завантажте SVG файл",
                    "3. Виберіть PNG формат",
                    "4. Завантажте результат"
                ],
                "pros": ["Не потребує встановлення", "Швидко"],
                "cons": ["Потребує інтернет", "Обмеження розміру"],
                "available": True
            },
            {
                "method": "Веб-браузер",
                "description": "Відкриття SVG в браузері та збереження як зображення",
                "steps": [
                    "1. Відкрийте SVG файл в браузері",
                    "2. Клік правою кнопкою → Зберегти зображення",
                    "3. Або зробіть скріншот",
                    "4. Збережіть як PNG"
                ],
                "pros": ["Завжди доступно", "Простота"],
                "cons": ["Ручна робота", "Можлива втрата якості"],
                "available": True
            },
            {
                "method": "GIMP",
                "description": "Відкриття SVG в GIMP та експорт в PNG",
                "steps": [
                    "1. Завантажте GIMP з gimp.org",
                    "2. Відкрийте SVG файл в GIMP",
                    "3. File → Export As → PNG",
                    "4. Налаштуйте розмір та збережіть"
                ],
                "pros": ["Безкоштовно", "Контроль якості"],
                "cons": ["Потребує встановлення GIMP"],
                "available": True
            }
        ])
        
        return suggestions
    
    def suggest_online_converters(self) -> List[Dict]:
        """Пропозиція онлайн конвертерів SVG"""
        return [
            {
                "name": "Convertio",
                "url": "https://convertio.co/svg-png/",
                "description": "Популярний онлайн конвертер з підтримкою багатьох форматів",
                "features": ["Пакетна конвертація", "Налаштування якості", "API"]
            },
            {
                "name": "CloudConvert",
                "url": "https://cloudconvert.com/svg-to-png",
                "description": "Професійний онлайн конвертер файлів",
                "features": ["Висока якість", "Налаштування розміру", "Batch processing"]
            },
            {
                "name": "Online-Convert",
                "url": "https://www.online-convert.com/",
                "description": "Універсальний конвертер з багатьма опціями",
                "features": ["Налаштування DPI", "Зміна розміру", "Оптимізація"]
            },
            {
                "name": "SVG to PNG",
                "url": "https://svgtopng.com/",
                "description": "Спеціалізований конвертер SVG в PNG",
                "features": ["Простота використання", "Швидкість", "Без реєстрації"]
            }
        ]
    
    def get_conversion_instructions(self, svg_path: str) -> str:
        """Отримання детальних інструкцій для конвертації SVG"""
        svg_info = self.get_svg_info(svg_path)
        
        instructions = f"""
🎨 Інструкції для конвертації SVG файлу

📁 Файл: {os.path.basename(svg_path)}
📊 Розмір: {svg_info['width']}x{svg_info['height']} пікселів
🎯 Складність: {svg_info['complexity']}
💾 Розмір файлу: {svg_info['file_size'] / 1024:.1f} KB

🔧 Доступні методи конвертації:
"""
        
        # Додавання доступних автоматичних методів
        if self.is_inkscape_available():
            instructions += "\n✅ АВТОМАТИЧНО - Inkscape встановлений (найкраща якість)"
        elif self.is_imagemagick_available():
            instructions += "\n✅ АВТОМАТИЧНО - ImageMagick встановлений (хороша якість)"
        else:
            instructions += "\n⚠️ Автоматична конвертація недоступна"
        
        instructions += """

🌐 ШВИДКИЙ СПОСІБ - Онлайн конвертер:
   • Перейдіть на convertio.co/svg-png/
   • Завантажте SVG файл
   • Завантажте PNG результат

💻 ЯКІСНИЙ СПОСІБ - Inkscape:
   • Завантажте з inkscape.org
   • Встановіть програму
   • Перезапустіть RimWorld Mod Builder
   • SVG файли конвертуватимуться автоматично

🌐 ПРОСТИЙ СПОСІБ - Браузер:
   • Відкрийте SVG файл в браузері
   • Клік правою кнопкою → Зберегти зображення

💡 Поради:
• Для найкращої якості використовуйте Inkscape
• Онлайн конвертери підходять для простих SVG
• Зберігайте в PNG для збереження прозорості
• Для складних SVG краще використовувати векторні редактори
"""
        
        return instructions


# Функції для зворотної сумісності
def handle_svg_file(svg_path: str, size: Tuple[int, int] = None) -> Optional[Image.Image]:
    """Обробка SVG файлу з альтернативними методами"""
    handler = SVGAlternativeHandler()
    
    # Спроба конвертації через Inkscape
    if handler.is_inkscape_available():
        converted_path = handler.convert_svg_via_inkscape(svg_path, size=size)
        if converted_path and os.path.exists(converted_path):
            return Image.open(converted_path)
    
    # Спроба конвертації через ImageMagick
    if handler.is_imagemagick_available():
        converted_path = handler.convert_svg_via_imagemagick(svg_path, size=size)
        if converted_path and os.path.exists(converted_path):
            return Image.open(converted_path)
    
    # Створення placeholder
    placeholder_path = handler.create_svg_placeholder(svg_path)
    if placeholder_path:
        return Image.open(placeholder_path)
    
    return None


def show_svg_help(svg_path: str):
    """Показ допомоги для SVG файлів"""
    handler = SVGAlternativeHandler()
    instructions = handler.get_conversion_instructions(svg_path)
    print(instructions)


# Тестування модуля
if __name__ == "__main__":
    print("🎨 Тест SVG Alternative Handler")
    
    # Створення тестового handler
    handler = SVGAlternativeHandler()
    
    # Перевірка доступних інструментів
    print(f"Inkscape доступний: {handler.is_inkscape_available()}")
    print(f"ImageMagick доступний: {handler.is_imagemagick_available()}")
    
    # Показ методів конвертації
    methods = handler.suggest_svg_conversion_methods("test.svg")
    print(f"\n📋 Доступно {len(methods)} методів конвертації:")
    for i, method in enumerate(methods, 1):
        available = "✅" if method.get("available", False) else "⚠️"
        print(f"{available} {i}. {method['method']}: {method['description']}")
    
    # Показ онлайн конвертерів
    converters = handler.suggest_online_converters()
    print(f"\n🌐 Доступно {len(converters)} онлайн конвертерів:")
    for converter in converters:
        print(f"• {converter['name']}: {converter['url']}")
    
    print("\n✅ SVG Alternative Handler готовий до використання!")
