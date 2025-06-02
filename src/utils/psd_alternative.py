#!/usr/bin/env python3
"""
Альтернативна обробка PSD файлів без залежності від psd-tools
Надає інструкції та альтернативи для роботи з PSD файлами
"""

import os
import struct
from typing import Optional, Dict, List
from PIL import Image
import io


class PSDAlternativeHandler:
    """Альтернативна обробка PSD файлів без psd-tools"""
    
    def __init__(self):
        self.supported_alternatives = [
            "PNG", "JPEG", "BMP", "TIFF", "WEBP"
        ]
    
    def extract_psd_preview(self, psd_path: str) -> Optional[Image.Image]:
        """
        Спроба витягування вбудованого превью з PSD файлу
        Працює тільки для PSD файлів з вбудованим JPEG превью
        """
        try:
            with open(psd_path, 'rb') as f:
                # Читання заголовка PSD
                signature = f.read(4)
                if signature != b'8BPS':
                    return None
                
                version = struct.unpack('>H', f.read(2))[0]
                if version != 1:
                    return None
                
                # Пропускаємо зарезервовані байти
                f.read(6)
                
                # Читання каналів, висоти, ширини (пропускаємо для витягування превью)
                _ = struct.unpack('>H', f.read(2))[0]  # channels
                _ = struct.unpack('>I', f.read(4))[0]  # height
                _ = struct.unpack('>I', f.read(4))[0]  # width
                _ = struct.unpack('>H', f.read(2))[0]  # depth
                _ = struct.unpack('>H', f.read(2))[0]  # color_mode
                
                # Пропускаємо Color Mode Data
                color_mode_length = struct.unpack('>I', f.read(4))[0]
                f.read(color_mode_length)
                
                # Читання Image Resources
                image_resources_length = struct.unpack('>I', f.read(4))[0]
                image_resources_data = f.read(image_resources_length)
                
                # Пошук JPEG превью в Image Resources
                preview_image = self._extract_jpeg_preview(image_resources_data)
                if preview_image:
                    return preview_image
                
                return None
                
        except Exception as e:
            print(f"Помилка читання PSD файлу: {e}")
            return None
    
    def _extract_jpeg_preview(self, image_resources_data: bytes) -> Optional[Image.Image]:
        """Витягування JPEG превью з Image Resources"""
        try:
            offset = 0
            while offset < len(image_resources_data) - 12:
                # Читання Image Resource Block
                signature = image_resources_data[offset:offset+4]
                if signature != b'8BIM':
                    offset += 1
                    continue
                
                resource_id = struct.unpack('>H', image_resources_data[offset+4:offset+6])[0]
                
                # Пропускаємо назву ресурсу
                name_length = image_resources_data[offset+6]
                if name_length == 0:
                    name_length = 1  # Padding
                if name_length % 2 == 1:
                    name_length += 1  # Padding to even
                
                data_offset = offset + 6 + 1 + name_length
                data_length = struct.unpack('>I', image_resources_data[data_offset:data_offset+4])[0]
                
                # Перевірка на JPEG превью (Resource ID 1033, 1036)
                if resource_id in [1033, 1036]:
                    jpeg_data = image_resources_data[data_offset+4:data_offset+4+data_length]
                    try:
                        return Image.open(io.BytesIO(jpeg_data))
                    except:
                        pass
                
                offset = data_offset + 4 + data_length
                if data_length % 2 == 1:
                    offset += 1  # Padding
            
            return None
            
        except Exception:
            return None
    
    def get_psd_info(self, psd_path: str) -> Dict:
        """Отримання базової інформації про PSD файл"""
        info = {
            "valid_psd": False,
            "width": 0,
            "height": 0,
            "channels": 0,
            "color_mode": "Unknown",
            "bit_depth": 0,
            "file_size": 0,
            "has_preview": False
        }
        
        try:
            info["file_size"] = os.path.getsize(psd_path)
            
            with open(psd_path, 'rb') as f:
                # Перевірка сигнатури
                signature = f.read(4)
                if signature != b'8BPS':
                    return info
                
                version = struct.unpack('>H', f.read(2))[0]
                if version != 1:
                    return info
                
                info["valid_psd"] = True
                
                # Пропускаємо зарезервовані байти
                f.read(6)
                
                # Читання основної інформації
                info["channels"] = struct.unpack('>H', f.read(2))[0]
                info["height"] = struct.unpack('>I', f.read(4))[0]
                info["width"] = struct.unpack('>I', f.read(4))[0]
                info["bit_depth"] = struct.unpack('>H', f.read(2))[0]
                color_mode = struct.unpack('>H', f.read(2))[0]
                
                # Декодування режиму кольору
                color_modes = {
                    0: "Bitmap",
                    1: "Grayscale",
                    2: "Indexed",
                    3: "RGB",
                    4: "CMYK",
                    7: "Multichannel",
                    8: "Duotone",
                    9: "Lab"
                }
                info["color_mode"] = color_modes.get(color_mode, f"Unknown ({color_mode})")
                
                # Перевірка наявності превью
                preview = self.extract_psd_preview(psd_path)
                info["has_preview"] = preview is not None
                
        except Exception as e:
            print(f"Помилка читання PSD інформації: {e}")
        
        return info
    
    def suggest_psd_conversion_methods(self, psd_path: str = "") -> List[Dict]:
        """Пропозиція методів конвертації PSD файлів"""
        _ = psd_path  # Параметр для майбутнього використання
        suggestions = [
            {
                "method": "Adobe Photoshop",
                "description": "Відкрийте PSD в Photoshop та експортуйте як PNG",
                "steps": [
                    "1. Відкрийте файл в Adobe Photoshop",
                    "2. File → Export → Export As...",
                    "3. Виберіть PNG формат",
                    "4. Налаштуйте якість та збережіть"
                ],
                "pros": ["Найкраща якість", "Підтримка всіх функцій PSD"],
                "cons": ["Потребує ліцензію Photoshop"]
            },
            {
                "method": "GIMP (безкоштовно)",
                "description": "Використайте GIMP для конвертації PSD в PNG",
                "steps": [
                    "1. Завантажте GIMP з gimp.org",
                    "2. Відкрийте PSD файл в GIMP",
                    "3. File → Export As...",
                    "4. Виберіть PNG та збережіть"
                ],
                "pros": ["Безкоштовно", "Хороша підтримка PSD"],
                "cons": ["Може не підтримувати всі ефекти"]
            },
            {
                "method": "Photopea (онлайн)",
                "description": "Безкоштовний онлайн редактор, схожий на Photoshop",
                "steps": [
                    "1. Відкрийте photopea.com",
                    "2. Завантажте PSD файл",
                    "3. File → Export as → PNG",
                    "4. Завантажте результат"
                ],
                "pros": ["Безкоштовно", "Не потребує встановлення", "Хороша підтримка PSD"],
                "cons": ["Потребує інтернет"]
            },
            {
                "method": "ImageMagick",
                "description": "Командний рядок для пакетної конвертації",
                "steps": [
                    "1. Встановіть ImageMagick",
                    "2. Відкрийте командний рядок",
                    "3. magick convert input.psd output.png",
                    "4. Файл буде сконвертовано"
                ],
                "pros": ["Пакетна обробка", "Автоматизація"],
                "cons": ["Командний рядок", "Базова підтримка PSD"]
            }
        ]
        
        return suggestions
    
    def suggest_online_converters(self) -> List[Dict]:
        """Пропозиція онлайн конвертерів"""
        return [
            {
                "name": "Convertio",
                "url": "https://convertio.co/psd-png/",
                "description": "Онлайн конвертер з підтримкою багатьох форматів",
                "features": ["Пакетна конвертація", "Хмарне зберігання", "API"]
            },
            {
                "name": "Zamzar",
                "url": "https://www.zamzar.com/convert/psd-to-png/",
                "description": "Простий онлайн конвертер файлів",
                "features": ["Email доставка", "Історія конвертацій"]
            },
            {
                "name": "Online-Convert",
                "url": "https://www.online-convert.com/",
                "description": "Професійний онлайн конвертер",
                "features": ["Налаштування якості", "Зміна розміру"]
            }
        ]
    
    def create_psd_placeholder(self, psd_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """Створення placeholder зображення для PSD файлу"""
        if output_path is None:
            output_path = psd_path.replace('.psd', '_placeholder.png')
        
        try:
            # Спроба витягнути превью
            preview = self.extract_psd_preview(psd_path)
            if preview:
                preview.save(output_path, "PNG")
                return output_path
            
            # Створення placeholder зображення
            psd_info = self.get_psd_info(psd_path)
            if psd_info["valid_psd"]:
                width = min(psd_info["width"], 512)
                height = min(psd_info["height"], 512)
            else:
                width, height = 256, 256
            
            # Створення простого placeholder
            placeholder = Image.new('RGB', (width, height), color='lightgray')
            
            # Додавання тексту (якщо можливо)
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(placeholder)
                
                # Спроба використати системний шрифт
                try:
                    font = ImageFont.truetype("arial.ttf", 24)
                except:
                    font = ImageFont.load_default()
                
                text = "PSD\nFile"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                draw.text((x, y), text, fill='black', font=font)
                
            except ImportError:
                # Якщо ImageDraw недоступний, створюємо простий placeholder
                pass
            
            placeholder.save(output_path, "PNG")
            return output_path
            
        except Exception as e:
            print(f"Помилка створення placeholder: {e}")
            return None
    
    def get_conversion_instructions(self, psd_path: str) -> str:
        """Отримання детальних інструкцій для конвертації"""
        psd_info = self.get_psd_info(psd_path)
        
        instructions = f"""
🎨 Інструкції для конвертації PSD файлу

📁 Файл: {os.path.basename(psd_path)}
📊 Розмір: {psd_info['width']}x{psd_info['height']} пікселів
🎨 Режим: {psd_info['color_mode']}
💾 Розмір файлу: {psd_info['file_size'] / 1024:.1f} KB

🔧 Рекомендовані методи конвертації:

1. 🌐 ШВИДКИЙ СПОСІБ - Photopea (онлайн)
   • Перейдіть на photopea.com
   • Завантажте PSD файл
   • File → Export as → PNG
   • Завантажте результат

2. 💻 ЯКІСНИЙ СПОСІБ - GIMP (безкоштовно)
   • Завантажте GIMP з gimp.org
   • Відкрийте PSD файл
   • File → Export As → PNG

3. 💰 ПРОФЕСІЙНИЙ СПОСІБ - Adobe Photoshop
   • Відкрийте в Photoshop
   • File → Export → Export As → PNG

💡 Поради:
• Зберігайте в PNG для збереження прозорості
• Використовуйте максимальну якість
• Перевірте, чи всі шари відображаються правильно
"""
        
        return instructions


# Alias для зворотної сумісності
PSDAlternative = PSDAlternativeHandler

# Функції для зворотної сумісності
def handle_psd_file(psd_path: str) -> Optional[Image.Image]:
    """Обробка PSD файлу з альтернативними методами"""
    handler = PSDAlternativeHandler()
    
    # Спроба витягнути превью
    preview = handler.extract_psd_preview(psd_path)
    if preview:
        return preview
    
    # Створення placeholder
    placeholder_path = handler.create_psd_placeholder(psd_path)
    if placeholder_path:
        return Image.open(placeholder_path)
    
    return None


def show_psd_help(psd_path: str):
    """Показ допомоги для PSD файлів"""
    handler = PSDAlternativeHandler()
    instructions = handler.get_conversion_instructions(psd_path)
    print(instructions)


# Тестування модуля
if __name__ == "__main__":
    print("🎨 Тест PSD Alternative Handler")
    
    # Створення тестового handler
    handler = PSDAlternativeHandler()
    
    # Показ методів конвертації
    methods = handler.suggest_psd_conversion_methods("test.psd")
    print(f"\n📋 Доступно {len(methods)} методів конвертації:")
    for i, method in enumerate(methods, 1):
        print(f"{i}. {method['method']}: {method['description']}")
    
    # Показ онлайн конвертерів
    converters = handler.suggest_online_converters()
    print(f"\n🌐 Доступно {len(converters)} онлайн конвертерів:")
    for converter in converters:
        print(f"• {converter['name']}: {converter['url']}")
    
    print("\n✅ PSD Alternative Handler готовий до використання!")
