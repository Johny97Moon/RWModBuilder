#!/usr/bin/env python3
"""
Система попереднього перегляду дефініцій для RimWorld Mod Builder
Візуалізація 2D спрайтів та інформації про предмети
"""

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import xml.etree.ElementTree as ET
from pathlib import Path
import re

class DefinitionPreview:
    """Клас для попереднього перегляду дефініцій"""
    
    def __init__(self, parent, project_path=None):
        self.parent = parent
        self.project_path = project_path
        self.current_definition = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Налаштування інтерфейсу попереднього перегляду"""
        # Головне вікно
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Попередній перегляд дефініції")
        self.window.geometry("800x600")
        self.window.transient(self.parent)
        
        # Головна панель
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Верхня панель з вибором файлу
        self.setup_file_selector(main_frame)
        
        # Основна область перегляду
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Ліва панель - 2D спрайт
        self.setup_sprite_panel(content_frame)
        
        # Права панель - інформація
        self.setup_info_panel(content_frame)
        
    def setup_file_selector(self, parent):
        """Налаштування селектора файлів"""
        selector_frame = ctk.CTkFrame(parent, height=60)
        selector_frame.pack(fill="x", pady=(0, 10))
        selector_frame.pack_propagate(False)
        
        # Заголовок
        ctk.CTkLabel(
            selector_frame,
            text="Виберіть XML файл для перегляду:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10, pady=15)
        
        # Кнопка вибору файлу
        self.select_file_btn = ctk.CTkButton(
            selector_frame,
            text="Обрати файл",
            command=self.select_definition_file,
            width=120
        )
        self.select_file_btn.pack(side="right", padx=10, pady=15)
        
        # Поле з назвою файлу
        self.file_label = ctk.CTkLabel(
            selector_frame,
            text="Файл не обрано",
            font=ctk.CTkFont(size=12)
        )
        self.file_label.pack(side="right", padx=10, pady=15)
        
    def setup_sprite_panel(self, parent):
        """Налаштування панелі спрайту"""
        # Ліва панель
        sprite_frame = ctk.CTkFrame(parent, width=400)
        sprite_frame.pack(side="left", fill="y", padx=(0, 10))
        sprite_frame.pack_propagate(False)
        
        # Заголовок
        sprite_label = ctk.CTkLabel(
            sprite_frame,
            text="2D Спрайт",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        sprite_label.pack(pady=10)
        
        # Область для спрайту
        self.sprite_display_frame = ctk.CTkFrame(sprite_frame, height=300)
        self.sprite_display_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.sprite_display_frame.pack_propagate(False)
        
        # Placeholder для спрайту
        self.sprite_label = ctk.CTkLabel(
            self.sprite_display_frame,
            text="Виберіть дефініцію\nдля перегляду спрайту",
            font=ctk.CTkFont(size=14)
        )
        self.sprite_label.pack(expand=True)
        
        # Інформація про спрайт
        self.sprite_info_frame = ctk.CTkFrame(sprite_frame)
        self.sprite_info_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.sprite_info_label = ctk.CTkLabel(
            self.sprite_info_frame,
            text="Інформація про спрайт",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.sprite_info_label.pack(pady=10)
        
        self.sprite_info_text = ctk.CTkTextbox(self.sprite_info_frame, height=100)
        self.sprite_info_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def setup_info_panel(self, parent):
        """Налаштування панелі інформації"""
        # Права панель
        info_frame = ctk.CTkFrame(parent)
        info_frame.pack(side="right", fill="both", expand=True)
        
        # Заголовок
        info_label = ctk.CTkLabel(
            info_frame,
            text="Інформація про дефініцію",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        info_label.pack(pady=10)
        
        # Основна інформація
        self.basic_info_frame = ctk.CTkFrame(info_frame, height=200)
        self.basic_info_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.basic_info_frame.pack_propagate(False)
        
        self.basic_info_text = ctk.CTkTextbox(self.basic_info_frame)
        self.basic_info_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Статистики
        self.stats_frame = ctk.CTkFrame(info_frame)
        self.stats_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        stats_label = ctk.CTkLabel(
            self.stats_frame,
            text="Статистики",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        stats_label.pack(pady=10)
        
        self.stats_text = ctk.CTkTextbox(self.stats_frame)
        self.stats_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def select_definition_file(self):
        """Вибір файлу дефініції"""
        if not self.project_path:
            messagebox.showwarning("Попередження", "Спочатку відкрийте проєкт")
            return
            
        from tkinter import filedialog
        
        # Пошук XML файлів у проєкті
        defs_path = Path(self.project_path) / "Defs"
        
        file_path = filedialog.askopenfilename(
            title="Виберіть XML файл дефініції",
            initialdir=str(defs_path) if defs_path.exists() else str(self.project_path),
            filetypes=[
                ("XML файли", "*.xml"),
                ("Всі файли", "*.*")
            ]
        )
        
        if file_path:
            self.load_definition(file_path)
            
    def load_definition(self, file_path):
        """Завантаження та аналіз дефініції"""
        try:
            # Читання XML файлу
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Пошук першої дефініції
            definition = None
            for child in root:
                if child.tag.endswith('Def'):
                    definition = child
                    break
                    
            if definition is None:
                messagebox.showwarning("Попередження", "У файлі не знайдено дефініцій")
                return
                
            self.current_definition = definition
            self.file_label.configure(text=Path(file_path).name)
            
            # Аналіз дефініції
            self.analyze_definition(definition)
            
            # Завантаження спрайту
            self.load_sprite(definition)
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося завантажити дефініцію:\n{str(e)}")
            
    def analyze_definition(self, definition):
        """Аналіз дефініції та відображення інформації"""
        def_type = definition.tag
        def_name = self.get_element_text(definition, 'defName', 'Невідомо')
        label = self.get_element_text(definition, 'label', 'Без назви')
        description = self.get_element_text(definition, 'description', 'Без опису')
        
        # Основна інформація
        basic_info = f"""Тип: {def_type}
DefName: {def_name}
Назва: {label}
Опис: {description}

Категорія: {self.get_element_text(definition, 'category', 'Не вказано')}
Клас: {self.get_element_text(definition, 'thingClass', 'Thing')}"""

        self.basic_info_text.delete("1.0", "end")
        self.basic_info_text.insert("1.0", basic_info)
        
        # Статистики
        stats_info = self.extract_stats(definition)
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("1.0", stats_info)
        
    def extract_stats(self, definition):
        """Витягування статистик з дефініції"""
        stats_base = definition.find('statBases')
        if stats_base is None:
            return "Статистики не знайдено"
            
        stats_lines = ["Базові статистики:"]
        
        for stat in stats_base:
            stat_name = stat.tag
            stat_value = stat.text or "0"
            
            # Переклад назв статистик
            stat_translations = {
                'MaxHitPoints': 'Максимальне здоров\'я',
                'WorkToBuild': 'Робота для побудови',
                'Flammability': 'Горючість',
                'Beauty': 'Краса',
                'Mass': 'Маса',
                'MarketValue': 'Ринкова вартість',
                'DeteriorationRate': 'Швидкість псування',
                'Comfort': 'Комфорт',
                'Nutrition': 'Поживність'
            }
            
            translated_name = stat_translations.get(stat_name, stat_name)
            stats_lines.append(f"  {translated_name}: {stat_value}")
            
        return "\n".join(stats_lines)
        
    def load_sprite(self, definition):
        """Завантаження та відображення спрайту"""
        # Пошук шляху до текстури
        graphic_data = definition.find('graphicData')
        if graphic_data is None:
            self.show_no_sprite()
            return
            
        tex_path_elem = graphic_data.find('texPath')
        if tex_path_elem is None:
            self.show_no_sprite()
            return
            
        tex_path = tex_path_elem.text
        if not tex_path:
            self.show_no_sprite()
            return
            
        # Пошук файлу текстури
        texture_file = self.find_texture_file(tex_path)
        if not texture_file:
            self.show_no_sprite(f"Текстура не знайдена: {tex_path}")
            return
            
        # Завантаження та відображення
        try:
            self.display_sprite(texture_file, graphic_data)
        except Exception as e:
            self.show_no_sprite(f"Помилка завантаження: {str(e)}")
            
    def find_texture_file(self, tex_path):
        """Пошук файлу текстури"""
        if not self.project_path:
            return None
            
        textures_path = Path(self.project_path) / "Textures"
        
        # Можливі розширення
        extensions = ['.png', '.jpg', '.jpeg']
        
        for ext in extensions:
            full_path = textures_path / f"{tex_path}{ext}"
            if full_path.exists():
                return full_path
                
        return None
        
    def display_sprite(self, texture_file, graphic_data):
        """Відображення спрайту"""
        try:
            # Завантаження зображення
            img = Image.open(texture_file)
            
            # Масштабування для відображення
            max_size = (250, 250)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Створення фону (шахівниця для прозорості)
            bg = self.create_transparency_background(img.size)
            bg.paste(img, (0, 0), img if img.mode == 'RGBA' else None)
            
            photo = ImageTk.PhotoImage(bg)
            
            # Очищення попереднього спрайту
            for widget in self.sprite_display_frame.winfo_children():
                widget.destroy()
                
            # Відображення спрайту
            sprite_label = ctk.CTkLabel(self.sprite_display_frame, image=photo, text="")
            sprite_label.image = photo  # Зберігаємо посилання
            sprite_label.pack(expand=True)
            
            # Інформація про спрайт
            original_img = Image.open(texture_file)
            sprite_info = f"""Файл: {texture_file.name}
Розмір: {original_img.size[0]} x {original_img.size[1]} пікселів
Режим: {original_img.mode}
Розмір файлу: {texture_file.stat().st_size // 1024} KB

Графічний клас: {self.get_element_text(graphic_data, 'graphicClass', 'Graphic_Single')}
Розмір малювання: {self.get_element_text(graphic_data, 'drawSize', 'За замовчуванням')}"""

            self.sprite_info_text.delete("1.0", "end")
            self.sprite_info_text.insert("1.0", sprite_info)
            
        except Exception as e:
            self.show_no_sprite(f"Помилка відображення: {str(e)}")
            
    def create_transparency_background(self, size):
        """Створення фону з шахівницею для прозорих зображень"""
        bg = Image.new('RGB', size, 'white')
        draw = ImageDraw.Draw(bg)
        
        # Розмір квадратів шахівниці
        square_size = 10
        
        for x in range(0, size[0], square_size):
            for y in range(0, size[1], square_size):
                if (x // square_size + y // square_size) % 2:
                    draw.rectangle(
                        [x, y, x + square_size, y + square_size],
                        fill='lightgray'
                    )
                    
        return bg
        
    def show_no_sprite(self, message="Спрайт недоступний"):
        """Показ повідомлення про відсутність спрайту"""
        # Очищення попереднього вмісту
        for widget in self.sprite_display_frame.winfo_children():
            widget.destroy()
            
        # Показ повідомлення
        no_sprite_label = ctk.CTkLabel(
            self.sprite_display_frame,
            text=message,
            font=ctk.CTkFont(size=14)
        )
        no_sprite_label.pack(expand=True)
        
        # Очищення інформації про спрайт
        self.sprite_info_text.delete("1.0", "end")
        self.sprite_info_text.insert("1.0", "Інформація про спрайт недоступна")
        
    def get_element_text(self, parent, tag, default=""):
        """Отримання тексту елемента XML"""
        element = parent.find(tag)
        return element.text if element is not None and element.text else default
        
    def set_project_path(self, project_path):
        """Встановлення шляху проєкту"""
        self.project_path = project_path


def show_definition_preview(parent, project_path=None):
    """Функція для показу попереднього перегляду дефініцій"""
    preview = DefinitionPreview(parent, project_path)
    return preview
