#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Обробник форматів зображень для RimWorld Mod Builder
Незалежний від GUI бібліотек модуль для роботи з різними форматами зображень
"""

import os
import io
from typing import Dict, List, Optional, Tuple
from PIL import Image

# Імпорти для додаткових форматів (з обробкою помилок)
# PSD підтримка
try:
    from psd_tools import PSDImage  # type: ignore
    PSD_AVAILABLE = True
except ImportError:
    PSD_AVAILABLE = False
    PSDImage = None

# SVG підтримка
try:
    import cairosvg  # type: ignore
    SVG_AVAILABLE = True
except ImportError:
    SVG_AVAILABLE = False
    cairosvg = None

# Додаткові формати через imageio
try:
    import imageio  # type: ignore
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False
    imageio = None

# HEIF/HEIC підтримка
try:
    from pillow_heif import register_heif_opener  # type: ignore
    register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False
    register_heif_opener = None


class ImageFormatHandler:
    """Клас для обробки різних форматів зображень"""

    # Підтримувані формати з описами
    SUPPORTED_FORMATS = {
        # Стандартні формати
        '.png': {'name': 'PNG', 'description': 'Portable Network Graphics', 'native': True},
        '.jpg': {'name': 'JPEG', 'description': 'Joint Photographic Experts Group', 'native': True},
        '.jpeg': {'name': 'JPEG', 'description': 'Joint Photographic Experts Group', 'native': True},
        '.bmp': {'name': 'BMP', 'description': 'Windows Bitmap', 'native': True},
        '.tga': {'name': 'TGA', 'description': 'Truevision TGA', 'native': True},
        '.gif': {'name': 'GIF', 'description': 'Graphics Interchange Format', 'native': True},

        # Розширені формати
        '.tiff': {'name': 'TIFF', 'description': 'Tagged Image File Format', 'native': True},
        '.tif': {'name': 'TIFF', 'description': 'Tagged Image File Format', 'native': True},
        '.webp': {'name': 'WebP', 'description': 'Google WebP Format', 'native': True},
        '.ico': {'name': 'ICO', 'description': 'Windows Icon', 'native': True},

        # Спеціальні формати
        '.psd': {'name': 'PSD', 'description': 'Adobe Photoshop Document', 'native': False, 'requires': 'psd-tools'},
        '.svg': {'name': 'SVG', 'description': 'Scalable Vector Graphics', 'native': False, 'requires': 'cairosvg'},
        '.exr': {'name': 'EXR', 'description': 'OpenEXR High Dynamic Range', 'native': False, 'requires': 'imageio'},
        '.hdr': {'name': 'HDR', 'description': 'High Dynamic Range', 'native': False, 'requires': 'imageio'},
        '.heic': {'name': 'HEIC', 'description': 'High Efficiency Image Container', 'native': False, 'requires': 'pillow-heif'},
        '.heif': {'name': 'HEIF', 'description': 'High Efficiency Image Format', 'native': False, 'requires': 'pillow-heif'},
    }

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Отримати список підтримуваних розширень"""
        return list(cls.SUPPORTED_FORMATS.keys())

    @classmethod
    def get_file_dialog_filter(cls) -> str:
        """Отримати фільтр для діалогу вибору файлів"""
        # Групуємо формати
        native_formats = []
        special_formats = []

        for ext, info in cls.SUPPORTED_FORMATS.items():
            format_str = f"*{ext}"
            if info['native']:
                native_formats.append(format_str)
            else:
                special_formats.append(format_str)

        filters = []
        filters.append(f"Всі зображення ({' '.join(native_formats + special_formats)})")
        filters.append(f"Стандартні формати ({' '.join(native_formats)})")

        if special_formats:
            filters.append(f"Спеціальні формати ({' '.join(special_formats)})")

        # Додаємо окремі формати
        for ext, info in cls.SUPPORTED_FORMATS.items():
            filters.append(f"{info['name']} (*{ext})")

        return ";;".join(filters)

    @classmethod
    def get_format_info(cls, file_path: str) -> Dict:
        """Отримати інформацію про формат файлу"""
        ext = os.path.splitext(file_path)[1].lower()
        return cls.SUPPORTED_FORMATS.get(ext, {
            'name': 'Unknown',
            'description': 'Unknown format',
            'native': False
        })

    @classmethod
    def can_handle_format(cls, file_path: str) -> bool:
        """Перевірити, чи можна обробити формат"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in cls.SUPPORTED_FORMATS:
            return False

        format_info = cls.SUPPORTED_FORMATS[ext]
        if format_info['native']:
            return True

        # Перевіряємо доступність спеціальних бібліотек
        requires = format_info.get('requires', '')
        if requires == 'psd-tools':
            return PSD_AVAILABLE
        elif requires == 'cairosvg':
            return SVG_AVAILABLE
        elif requires == 'imageio':
            return IMAGEIO_AVAILABLE
        elif requires == 'pillow-heif':
            return HEIF_AVAILABLE

        return False

    @classmethod
    def load_image_as_pil(cls, file_path: str) -> Optional[Image.Image]:
        """Завантажити зображення як PIL Image"""
        # Валідація шляху файлу
        if not file_path or not isinstance(file_path, str):
            print(f"Неправильний шлях до файлу: {file_path}")
            return None

        # Нормалізація шляху
        file_path = os.path.normpath(os.path.abspath(file_path))

        # Перевірка існування файлу
        if not os.path.exists(file_path):
            print(f"Файл не існує: {file_path}")
            return None

        # Перевірка доступності для читання
        if not os.access(file_path, os.R_OK):
            print(f"Немає доступу для читання файлу: {file_path}")
            return None

        ext = os.path.splitext(file_path)[1].lower()
        print(f"Завантаження файлу: {file_path} (розширення: {ext})")

        try:
            if ext == '.psd':
                if not PSD_AVAILABLE:
                    print("psd-tools не встановлено. Встановіть: pip install psd-tools")
                    return None

                print("Обробка PSD файлу...")
                # Додаткова перевірка для PSD файлів
                try:
                    psd = PSDImage.open(file_path)
                    pil_image = psd.composite()
                    print(f"PSD файл успішно завантажено: {pil_image.size}")
                    return pil_image
                except Exception as psd_error:
                    print(f"Помилка обробки PSD файлу: {psd_error}")
                    # Спробувати як звичайний файл
                    try:
                        return Image.open(file_path)
                    except:
                        return None

            elif ext == '.svg':
                if not SVG_AVAILABLE:
                    print("cairosvg не встановлено. Встановіть: pip install cairosvg")
                    return None

                # Обробка SVG файлів
                png_data = cairosvg.svg2png(url=file_path, output_width=512, output_height=512)
                return Image.open(io.BytesIO(png_data))

            elif ext in ['.exr', '.hdr']:
                if not IMAGEIO_AVAILABLE:
                    print("imageio не встановлено. Встановіть: pip install imageio")
                    return None

                # Обробка HDR форматів
                image_array = imageio.imread(file_path)
                # Конвертуємо в 8-bit для відображення
                if image_array.dtype != 'uint8':
                    image_array = (image_array * 255).astype('uint8')
                return Image.fromarray(image_array)

            elif ext in ['.heic', '.heif']:
                if not HEIF_AVAILABLE:
                    print("pillow-heif не встановлено. Встановіть: pip install pillow-heif")
                    return None

                # Обробка HEIF форматів
                return Image.open(file_path)

            else:
                # Стандартні формати через PIL
                return Image.open(file_path)

        except FileNotFoundError:
            print(f"Файл не знайдено: {file_path}")
            return None
        except PermissionError:
            print(f"Немає дозволу на читання файлу: {file_path}")
            return None
        except Exception as e:
            print(f"Помилка завантаження {file_path}: {type(e).__name__}: {e}")
            return None

    @classmethod
    def convert_to_png(cls, input_path: str, output_path: str, max_size: Optional[Tuple[int, int]] = None) -> bool:
        """Конвертувати зображення в PNG формат"""
        try:
            pil_image = cls.load_image_as_pil(input_path)
            if pil_image is None:
                return False

            # Конвертуємо в RGB якщо потрібно
            if pil_image.mode in ('RGBA', 'LA'):
                # Зберігаємо прозорість для PNG
                pass
            elif pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Масштабуємо якщо потрібно
            if max_size:
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Зберігаємо як PNG
            pil_image.save(output_path, 'PNG', optimize=True)
            return True

        except Exception as e:
            print(f"Помилка конвертації {input_path} в PNG: {e}")
            return False

    @classmethod
    def get_image_info(cls, file_path: str) -> Optional[Dict]:
        """Отримати детальну інформацію про зображення"""
        try:
            pil_image = cls.load_image_as_pil(file_path)
            if pil_image is None:
                return None

            file_size = os.path.getsize(file_path)
            format_info = cls.get_format_info(file_path)

            info = {
                'width': pil_image.width,
                'height': pil_image.height,
                'mode': pil_image.mode,
                'format': pil_image.format or format_info['name'],
                'file_size': file_size,
                'format_info': format_info,
                'has_transparency': pil_image.mode in ('RGBA', 'LA', 'P'),
            }

            # Додаткова інформація з метаданих
            if hasattr(pil_image, 'info') and pil_image.info:
                info['metadata'] = pil_image.info

            return info

        except Exception as e:
            print(f"Помилка отримання інформації про {file_path}: {e}")
            return None

    @classmethod
    def optimize_image(cls, input_path: str, output_path: str, quality: int = 85, max_size: Optional[Tuple[int, int]] = None) -> bool:
        """Оптимізувати зображення"""
        try:
            pil_image = cls.load_image_as_pil(input_path)
            if pil_image is None:
                return False

            # Масштабуємо якщо потрібно
            if max_size:
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Визначаємо формат виводу
            ext = os.path.splitext(output_path)[1].lower()
            
            if ext == '.png':
                # PNG з оптимізацією
                pil_image.save(output_path, 'PNG', optimize=True)
            elif ext in ['.jpg', '.jpeg']:
                # JPEG з заданою якістю
                if pil_image.mode in ('RGBA', 'LA'):
                    pil_image = pil_image.convert('RGB')
                pil_image.save(output_path, 'JPEG', quality=quality, optimize=True)
            else:
                # Інші формати
                pil_image.save(output_path, optimize=True)

            return True

        except Exception as e:
            print(f"Помилка оптимізації {input_path}: {e}")
            return False

    @classmethod
    def get_available_formats(cls) -> Dict[str, bool]:
        """Отримати список доступних форматів з їх статусом"""
        formats = {}
        
        for ext, info in cls.SUPPORTED_FORMATS.items():
            if info['native']:
                formats[info['name']] = True
            else:
                # Перевіряємо доступність спеціальних бібліотек
                requires = info.get('requires', '')
                if requires == 'psd-tools':
                    formats[info['name']] = PSD_AVAILABLE
                elif requires == 'cairosvg':
                    formats[info['name']] = SVG_AVAILABLE
                elif requires == 'imageio':
                    formats[info['name']] = IMAGEIO_AVAILABLE
                elif requires == 'pillow-heif':
                    formats[info['name']] = HEIF_AVAILABLE
                else:
                    formats[info['name']] = False
        
        return formats

    @classmethod
    def get_missing_dependencies(cls) -> List[str]:
        """Отримати список відсутніх залежностей"""
        missing = []
        
        if not PSD_AVAILABLE:
            missing.append('psd-tools (для PSD файлів)')
        if not SVG_AVAILABLE:
            missing.append('cairosvg (для SVG файлів)')
        if not IMAGEIO_AVAILABLE:
            missing.append('imageio (для HDR форматів)')
        if not HEIF_AVAILABLE:
            missing.append('pillow-heif (для HEIF форматів)')
        
        return missing
