#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Менеджер текстур для RimWorld Mod Builder
Версія з CustomTkinter - сучасний та красивий GUI

Переваги CustomTkinter:
- Легке встановлення: pip install customtkinter
- Сучасний вигляд з темними/світлими темами
- Знайома API (базується на tkinter)
- Відмінна продуктивність
- Активна розробка та підтримка
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
from typing import Optional
from PIL import Image, ImageTk
import threading
import json
from datetime import datetime

# Додаємо шлях до core модулів
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.image_formats import ImageFormatHandler

# Налаштування CustomTkinter
ctk.set_appearance_mode("dark")  # "dark" або "light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class TextureManagerCustomTkinter:
    """Менеджер текстур з CustomTkinter GUI"""

    def __init__(self, project_path: Optional[str] = None, parent_window=None):
        self.project_path = project_path
        self.textures_path = os.path.join(project_path, "Textures") if project_path else None
        self.format_handler = ImageFormatHandler()
        self.parent_window = parent_window

        # Стан інтерфейсу
        self.current_filter = "all"
        self.sort_mode = "name"
        self.zoom_level = 1.0
        self.selected_file = None
        self.file_items = []

        # Кеш зображень
        self.image_cache = {}
        self.thumbnail_cache = {}

        self.setup_ui()
        
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Визначаємо батьківське вікно
        if self.parent_window:
            # Використовуємо передане батьківське вікно
            self.root = self.parent_window
            # Головний контейнер для вбудованого режиму
            self.main_frame = ctk.CTkFrame(self.root)
            self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        else:
            # Створюємо власне вікно для автономного режиму
            self.root = ctk.CTk()
            self.root.title("🎮 RimWorld Mod Builder - Менеджер текстур")
            self.root.geometry("1400x900")
            self.root.minsize(1000, 600)

            # Іконка (якщо є)
            try:
                self.root.iconbitmap("assets/icon.ico")
            except:
                pass

            # Головний контейнер для автономного режиму
            self.main_frame = ctk.CTkFrame(self.root)
            self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.setup_header()
        self.setup_toolbar()
        self.setup_content_area()
        self.setup_status_bar()
        
        # Завантажити текстури при запуску
        if self.textures_path and os.path.exists(self.textures_path):
            self.refresh_textures()
    
    def setup_header(self):
        """Налаштування заголовка"""
        header_frame = ctk.CTkFrame(self.main_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Заголовок
        title_label = ctk.CTkLabel(
            header_frame,
            text="🎮 RimWorld Mod Builder - Менеджер текстур",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        # Кнопки теми
        theme_frame = ctk.CTkFrame(header_frame)
        theme_frame.pack(side="right", padx=20, pady=15)
        
        ctk.CTkLabel(theme_frame, text="Тема:").pack(side="left", padx=(10, 5))
        
        self.theme_switch = ctk.CTkSwitch(
            theme_frame,
            text="🌙 Темна",
            command=self.toggle_theme
        )
        self.theme_switch.pack(side="left", padx=5)
        self.theme_switch.select()  # Темна тема за замовчуванням
        
    def setup_toolbar(self):
        """Налаштування панелі інструментів"""
        toolbar_frame = ctk.CTkFrame(self.main_frame)
        toolbar_frame.pack(fill="x", padx=10, pady=5)
        
        # Ліва група - файлові операції
        left_group = ctk.CTkFrame(toolbar_frame)
        left_group.pack(side="left", padx=10, pady=10)
        
        self.import_btn = ctk.CTkButton(
            left_group,
            text="📥 Імпорт",
            command=self.import_texture,
            width=100
        )
        self.import_btn.pack(side="left", padx=5)
        
        self.batch_import_btn = ctk.CTkButton(
            left_group,
            text="📦 Батч-імпорт",
            command=self.batch_import,
            width=120
        )
        self.batch_import_btn.pack(side="left", padx=5)
        
        self.export_btn = ctk.CTkButton(
            left_group,
            text="📤 Експорт",
            command=self.export_texture,
            width=100
        )
        self.export_btn.pack(side="left", padx=5)
        
        # Центральна група - фільтри
        center_group = ctk.CTkFrame(toolbar_frame)
        center_group.pack(expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(center_group, text="Фільтр:").pack(side="left", padx=(10, 5))
        
        self.filter_combo = ctk.CTkComboBox(
            center_group,
            values=["Всі файли", "PNG", "JPEG", "PSD", "SVG", "Інші"],
            command=self.on_filter_changed,
            width=120
        )
        self.filter_combo.pack(side="left", padx=5)
        
        ctk.CTkLabel(center_group, text="Сортування:").pack(side="left", padx=(15, 5))
        
        self.sort_combo = ctk.CTkComboBox(
            center_group,
            values=["За назвою", "За розміром", "За датою", "За форматом"],
            command=self.on_sort_changed,
            width=120
        )
        self.sort_combo.pack(side="left", padx=5)
        
        # Права група - дії
        right_group = ctk.CTkFrame(toolbar_frame)
        right_group.pack(side="right", padx=10, pady=10)
        
        self.convert_btn = ctk.CTkButton(
            right_group,
            text="🔄 Конвертувати",
            command=self.convert_to_png,
            width=120
        )
        self.convert_btn.pack(side="left", padx=5)
        
        self.optimize_btn = ctk.CTkButton(
            right_group,
            text="⚡ Оптимізувати",
            command=self.optimize_texture,
            width=120
        )
        self.optimize_btn.pack(side="left", padx=5)
        
        self.refresh_btn = ctk.CTkButton(
            right_group,
            text="🔄 Оновити",
            command=self.refresh_textures,
            width=100
        )
        self.refresh_btn.pack(side="left", padx=5)
    
    def setup_content_area(self):
        """Налаштування основної області контенту"""
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Розділення на ліву та праву панелі
        self.setup_left_panel(content_frame)
        self.setup_right_panel(content_frame)
    
    def setup_left_panel(self, parent):
        """Ліва панель - список файлів"""
        left_frame = ctk.CTkFrame(parent)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Заголовок лівої панелі
        left_header = ctk.CTkFrame(left_frame)
        left_header.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            left_header,
            text="📁 Текстури проєкту",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=10)
        
        # Лічильник файлів
        self.file_count_label = ctk.CTkLabel(
            left_header,
            text="0 файлів",
            font=ctk.CTkFont(size=12)
        )
        self.file_count_label.pack(side="right", padx=10)
        
        # Список файлів (прокручуваний)
        self.file_list_frame = ctk.CTkScrollableFrame(
            left_frame,
            label_text="Список текстур"
        )
        self.file_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Контекстне меню для файлів
        self.setup_context_menu()
    
    def setup_right_panel(self, parent):
        """Права панель - попередній перегляд"""
        right_frame = ctk.CTkFrame(parent)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Заголовок правої панелі
        right_header = ctk.CTkFrame(right_frame)
        right_header.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            right_header,
            text="🖼️ Попередній перегляд",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=10)
        
        # Контроли масштабування
        zoom_frame = ctk.CTkFrame(right_header)
        zoom_frame.pack(side="right", padx=10)
        
        self.zoom_out_btn = ctk.CTkButton(
            zoom_frame,
            text="🔍-",
            width=40,
            command=self.zoom_out
        )
        self.zoom_out_btn.pack(side="left", padx=2)
        
        self.zoom_label = ctk.CTkLabel(
            zoom_frame,
            text="100%",
            width=60
        )
        self.zoom_label.pack(side="left", padx=5)
        
        self.zoom_in_btn = ctk.CTkButton(
            zoom_frame,
            text="🔍+",
            width=40,
            command=self.zoom_in
        )
        self.zoom_in_btn.pack(side="left", padx=2)
        
        self.fit_btn = ctk.CTkButton(
            zoom_frame,
            text="📐",
            width=40,
            command=self.fit_to_window
        )
        self.fit_btn.pack(side="left", padx=2)
        
        # Область для зображення
        self.image_frame = ctk.CTkFrame(right_frame)
        self.image_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Прокручувана область для великих зображень
        self.image_canvas = tk.Canvas(
            self.image_frame,
            bg=self.image_frame.cget("fg_color")[1],  # Темний фон
            highlightthickness=0
        )
        
        # Скролбари
        v_scrollbar = ctk.CTkScrollbar(
            self.image_frame,
            orientation="vertical",
            command=self.image_canvas.yview
        )
        h_scrollbar = ctk.CTkScrollbar(
            self.image_frame,
            orientation="horizontal",
            command=self.image_canvas.xview
        )
        
        self.image_canvas.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        # Розміщення елементів
        self.image_canvas.pack(side="left", fill="both", expand=True)
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Лейбл для відображення зображення
        self.image_label = ctk.CTkLabel(
            self.image_canvas,
            text="Оберіть зображення для перегляду",
            font=ctk.CTkFont(size=14)
        )
        self.image_canvas.create_window(
            0, 0,
            window=self.image_label,
            anchor="nw"
        )
        
        # Інформаційна панель
        info_frame = ctk.CTkFrame(right_frame)
        info_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Табби для інформації
        self.info_tabview = ctk.CTkTabview(info_frame)
        self.info_tabview.pack(fill="x", padx=10, pady=10)
        
        # Вкладка "Інформація"
        self.info_tab = self.info_tabview.add("📋 Інформація")
        self.info_text = ctk.CTkTextbox(self.info_tab, height=100)
        self.info_text.pack(fill="x", padx=5, pady=5)
        
        # Вкладка "Метадані"
        self.metadata_tab = self.info_tabview.add("🏷️ Метадані")
        self.metadata_text = ctk.CTkTextbox(self.metadata_tab, height=100)
        self.metadata_text.pack(fill="x", padx=5, pady=5)
        
        # Вкладка "Дії"
        self.actions_tab = self.info_tabview.add("⚙️ Дії")
        self.setup_actions_tab()
    
    def setup_actions_tab(self):
        """Налаштування вкладки дій"""
        actions_frame = ctk.CTkFrame(self.actions_tab)
        actions_frame.pack(fill="x", padx=5, pady=5)
        
        # Кнопки дій для вибраного файлу
        self.rename_btn = ctk.CTkButton(
            actions_frame,
            text="✏️ Перейменувати",
            command=self.rename_texture,
            width=140
        )
        self.rename_btn.pack(side="left", padx=5, pady=5)
        
        self.duplicate_btn = ctk.CTkButton(
            actions_frame,
            text="📋 Дублювати",
            command=self.duplicate_texture,
            width=140
        )
        self.duplicate_btn.pack(side="left", padx=5, pady=5)
        
        self.delete_btn = ctk.CTkButton(
            actions_frame,
            text="🗑️ Видалити",
            command=self.delete_texture,
            fg_color="red",
            hover_color="darkred",
            width=140
        )
        self.delete_btn.pack(side="left", padx=5, pady=5)
    
    def setup_status_bar(self):
        """Налаштування статусної панелі"""
        status_frame = ctk.CTkFrame(self.main_frame)
        status_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # Ліва частина - статистика
        self.stats_label = ctk.CTkLabel(
            status_frame,
            text="📊 Файлів: 0 | Розмір: 0 MB | Формати: 0",
            font=ctk.CTkFont(size=12)
        )
        self.stats_label.pack(side="left", padx=20, pady=10)
        
        # Права частина - прогрес
        self.progress_frame = ctk.CTkFrame(status_frame)
        self.progress_frame.pack(side="right", padx=20, pady=10)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Готовий",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(side="left", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=200
        )
        self.progress_bar.pack(side="left", padx=10)
        self.progress_bar.set(0)
    
    def setup_context_menu(self):
        """Налаштування контекстного меню"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="📖 Відкрити", command=self.open_texture)
        self.context_menu.add_command(label="👁️ Переглянути", command=self.preview_texture)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✏️ Перейменувати", command=self.rename_texture)
        self.context_menu.add_command(label="📋 Дублювати", command=self.duplicate_texture)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔄 Конвертувати в PNG", command=self.convert_to_png)
        self.context_menu.add_command(label="⚡ Оптимізувати", command=self.optimize_texture)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Видалити", command=self.delete_texture)
    
    # Методи обробки подій
    def toggle_theme(self):
        """Перемикання теми"""
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
            self.theme_switch.configure(text="🌙 Темна")
        else:
            ctk.set_appearance_mode("light")
            self.theme_switch.configure(text="☀️ Світла")
    
    def on_filter_changed(self, value):
        """Обробка зміни фільтра"""
        filter_map = {
            "Всі файли": "all",
            "PNG": "png",
            "JPEG": "jpeg",
            "PSD": "psd",
            "SVG": "svg",
            "Інші": "other"
        }
        self.current_filter = filter_map.get(value, "all")
        self.refresh_file_list()
    
    def on_sort_changed(self, value):
        """Обробка зміни сортування"""
        sort_map = {
            "За назвою": "name",
            "За розміром": "size",
            "За датою": "date",
            "За форматом": "format"
        }
        self.sort_mode = sort_map.get(value, "name")
        self.refresh_file_list()
    
    def run(self):
        """Запустити додаток (тільки для автономного режиму)"""
        if not self.parent_window:
            self.root.mainloop()
        else:
            print("Менеджер текстур працює у вбудованому режимі")
    
    # Основні методи роботи з текстурами
    def refresh_textures(self):
        """Оновити список текстур"""
        if not self.textures_path or not os.path.exists(self.textures_path):
            self.file_items = []
            self.update_file_count()
            return

        self.progress_label.configure(text="Сканування файлів...")
        self.progress_bar.set(0.1)
        self.root.update()

        # Сканування файлів у фоновому режимі
        threading.Thread(target=self._scan_textures, daemon=True).start()

    def _scan_textures(self):
        """Сканування текстур у фоновому режимі"""
        try:
            if not self.textures_path:
                return

            file_items = []
            supported_extensions = self.format_handler.get_supported_extensions()

            # Рекурсивний пошук файлів
            for root, _, files in os.walk(self.textures_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()

                    if file_ext in supported_extensions:
                        relative_path = os.path.relpath(file_path, self.textures_path)
                        format_info = self.format_handler.get_format_info(file_path)

                        try:
                            stat = os.stat(file_path)
                            file_data = {
                                'path': file_path,
                                'relative_path': relative_path,
                                'name': file,
                                'size': stat.st_size,
                                'mtime': stat.st_mtime,
                                'format_info': format_info,
                                'ext': file_ext
                            }
                            file_items.append(file_data)
                        except OSError:
                            continue

            # Оновити UI в головному потоці
            self.root.after(0, self._update_file_list, file_items)

        except Exception as e:
            self.root.after(0, self._show_error, f"Помилка сканування: {e}")

    def _update_file_list(self, file_items):
        """Оновити список файлів в UI"""
        self.file_items = file_items
        self.refresh_file_list()
        self.progress_label.configure(text="Готовий")
        self.progress_bar.set(1.0)
        self.root.after(1000, lambda: self.progress_bar.set(0))

    def _show_error(self, message):
        """Показати помилку"""
        messagebox.showerror("Помилка", message)
        self.progress_label.configure(text="Помилка")
        self.progress_bar.set(0)

    def refresh_file_list(self):
        """Оновити відображення списку файлів"""
        # Очистити поточний список
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()

        # Фільтрація файлів
        filtered_files = self._filter_files(self.file_items)

        # Сортування файлів
        sorted_files = self._sort_files(filtered_files)

        # Створення елементів списку
        for i, file_data in enumerate(sorted_files):
            self._create_file_item(file_data, i)

        # Оновлення статистики
        self.update_file_count()
        self.update_statistics()

    def _filter_files(self, files):
        """Фільтрація файлів за типом"""
        if self.current_filter == "all":
            return files

        filtered = []
        for file_data in files:
            format_name = file_data['format_info']['name'].lower()

            if self.current_filter == "png" and format_name == "png":
                filtered.append(file_data)
            elif self.current_filter == "jpeg" and format_name == "jpeg":
                filtered.append(file_data)
            elif self.current_filter == "psd" and format_name == "psd":
                filtered.append(file_data)
            elif self.current_filter == "svg" and format_name == "svg":
                filtered.append(file_data)
            elif self.current_filter == "other" and format_name not in ["png", "jpeg", "psd", "svg"]:
                filtered.append(file_data)

        return filtered

    def _sort_files(self, files):
        """Сортування файлів"""
        if self.sort_mode == "name":
            return sorted(files, key=lambda x: x['name'].lower())
        elif self.sort_mode == "size":
            return sorted(files, key=lambda x: x['size'], reverse=True)
        elif self.sort_mode == "date":
            return sorted(files, key=lambda x: x['mtime'], reverse=True)
        elif self.sort_mode == "format":
            return sorted(files, key=lambda x: x['format_info']['name'])
        else:
            return files

    def _create_file_item(self, file_data, _):
        """Створити елемент списку файлів"""
        item_frame = ctk.CTkFrame(self.file_list_frame)
        item_frame.pack(fill="x", padx=5, pady=2)

        # Іконка формату з кольоровим кодуванням
        format_colors = {
            "PNG": "#4CAF50",    # Зелений
            "JPEG": "#2196F3",   # Синій
            "PSD": "#9C27B0",    # Фіолетовий
            "SVG": "#FF9800",    # Помаранчевий
            "TIFF": "#F44336",   # Червоний
            "WebP": "#00BCD4",   # Бірюзовий
            "BMP": "#795548",    # Коричневий
            "GIF": "#FFEB3B"     # Жовтий
        }

        format_name = file_data['format_info']['name']
        color = format_colors.get(format_name, "#9E9E9E")

        format_label = ctk.CTkLabel(
            item_frame,
            text=format_name,
            width=50,
            fg_color=color,
            corner_radius=5,
            font=ctk.CTkFont(size=10, weight="bold")
        )
        format_label.pack(side="left", padx=5, pady=5)

        # Інформація про файл
        info_frame = ctk.CTkFrame(item_frame)
        info_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # Назва файлу
        name_label = ctk.CTkLabel(
            info_frame,
            text=file_data['name'],
            font=ctk.CTkFont(weight="bold"),
            anchor="w"
        )
        name_label.pack(fill="x", padx=5)

        # Розмір та шлях
        size_mb = file_data['size'] / (1024 * 1024)
        size_text = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_data['size'] / 1024:.1f} KB"

        details_label = ctk.CTkLabel(
            info_frame,
            text=f"{size_text} • {file_data['relative_path']}",
            font=ctk.CTkFont(size=10),
            anchor="w",
            text_color="gray"
        )
        details_label.pack(fill="x", padx=5)

        # Кнопка вибору
        select_btn = ctk.CTkButton(
            item_frame,
            text="👁️",
            width=40,
            command=lambda: self.select_file(file_data)
        )
        select_btn.pack(side="right", padx=5, pady=5)

        # Прив'язка контекстного меню
        def show_context_menu(event):
            self.selected_file = file_data
            self.context_menu.post(event.x_root, event.y_root)

        item_frame.bind("<Button-3>", show_context_menu)  # Права кнопка миші

    def select_file(self, file_data):
        """Вибрати файл для перегляду"""
        self.selected_file = file_data
        self.update_preview(file_data)
        self.update_info_panel(file_data)

    def update_file_count(self):
        """Оновити лічильник файлів"""
        count = len([widget for widget in self.file_list_frame.winfo_children()])
        self.file_count_label.configure(text=f"{count} файлів")

    def update_statistics(self):
        """Оновити статистику"""
        if not self.file_items:
            self.stats_label.configure(text="📊 Файлів: 0 | Розмір: 0 MB | Формати: 0")
            return

        total_files = len(self.file_items)
        total_size = sum(item['size'] for item in self.file_items)
        total_size_mb = total_size / (1024 * 1024)

        formats = set(item['format_info']['name'] for item in self.file_items)
        format_count = len(formats)

        self.stats_label.configure(
            text=f"📊 Файлів: {total_files} | Розмір: {total_size_mb:.1f} MB | Формати: {format_count}"
        )

    def update_preview(self, file_data):
        """Оновити попередній перегляд зображення"""
        try:
            # Завантажити зображення
            pil_image = self.format_handler.load_image_as_pil(file_data['path'])
            if pil_image is None:
                self.image_label.configure(
                    text=f"❌ Не вдалося завантажити\n{file_data['name']}",
                    image=None
                )
                return

            # Масштабування зображення
            display_size = self._calculate_display_size(pil_image.size)
            resized_image = pil_image.resize(display_size, Image.Resampling.LANCZOS)

            # Конвертація в PhotoImage
            photo = ImageTk.PhotoImage(resized_image)

            # Оновлення лейбла
            self.image_label.configure(
                text="",
                image=photo
            )

            # Оновити розмір canvas
            self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))

        except Exception as e:
            self.image_label.configure(
                text=f"❌ Помилка завантаження:\n{str(e)}",
                image=None
            )

    def _calculate_display_size(self, original_size):
        """Розрахувати розмір для відображення"""
        max_width = 400
        max_height = 400

        width, height = original_size

        # Застосувати масштаб
        width = int(width * self.zoom_level)
        height = int(height * self.zoom_level)

        # Обмежити максимальним розміром (тільки при зменшенні)
        if self.zoom_level <= 1.0:
            if width > max_width or height > max_height:
                ratio = min(max_width / width, max_height / height)
                width = int(width * ratio)
                height = int(height * ratio)

        return (width, height)

    def update_info_panel(self, file_data):
        """Оновити інформаційну панель"""
        # Основна інформація
        info_text = f"""Файл: {file_data['name']}
Шлях: {file_data['relative_path']}
Формат: {file_data['format_info']['name']}
Розмір файлу: {self._format_file_size(file_data['size'])}
Дата зміни: {datetime.fromtimestamp(file_data['mtime']).strftime('%d.%m.%Y %H:%M')}

Статус: {'✅ Підтримується' if file_data['format_info']['native'] else '⚠️ Потребує конвертації'}
Рекомендації: {'Оптимальний для RimWorld' if file_data['format_info']['name'] == 'PNG' else 'Рекомендується конвертація в PNG'}"""

        self.info_text.delete("0.0", "end")
        self.info_text.insert("0.0", info_text)

        # Метадані зображення
        try:
            image_info = self.format_handler.get_image_info(file_data['path'])
            if image_info:
                metadata_text = f"""Розміри: {image_info['width']} x {image_info['height']} пікселів
Режим кольору: {image_info['mode']}
Прозорість: {'Так' if image_info.get('has_transparency', False) else 'Ні'}
DPI: {image_info.get('metadata', {}).get('dpi', 'Не вказано')}

Додаткова інформація:
{json.dumps(image_info.get('metadata', {}), indent=2, ensure_ascii=False) if image_info.get('metadata') else 'Метадані відсутні'}"""
            else:
                metadata_text = "Не вдалося отримати метадані зображення"

        except Exception as e:
            metadata_text = f"Помилка читання метаданих: {e}"

        self.metadata_text.delete("0.0", "end")
        self.metadata_text.insert("0.0", metadata_text)

    def _format_file_size(self, size_bytes):
        """Форматувати розмір файлу"""
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes} байт"

    def zoom_in(self):
        """Збільшити масштаб"""
        self.zoom_level = min(self.zoom_level * 1.25, 5.0)
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        
    def zoom_out(self):
        """Зменшити масштаб"""
        self.zoom_level = max(self.zoom_level / 1.25, 0.1)
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        
    def fit_to_window(self):
        """Підігнати під вікно"""
        self.zoom_level = 1.0
        self.zoom_label.configure(text="100%")
        
    def import_texture(self):
        """Імпорт текстури"""
        if not self.textures_path:
            messagebox.showwarning("Попередження", "Проєкт не відкрито")
            return

        # Створити фільтр файлів на основі підтримуваних форматів
        try:
            # Спробувати отримати динамічний фільтр
            _ = self.format_handler.get_file_dialog_filter()
            # Використовуємо статичний фільтр для кращої сумісності
            filetypes = [
                ("Всі підтримувані", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp *.psd *.svg"),
                ("PNG файли", "*.png"),
                ("JPEG файли", "*.jpg *.jpeg"),
                ("PSD файли", "*.psd"),
                ("SVG файли", "*.svg"),
                ("Всі файли", "*.*")
            ]
        except:
            # Fallback якщо є проблеми з динамічним фільтром
            filetypes = [
                ("Всі підтримувані", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp *.psd *.svg"),
                ("Всі файли", "*.*")
            ]

        file_path = filedialog.askopenfilename(
            title="Оберіть текстуру для імпорту",
            filetypes=filetypes
        )

        if file_path:
            try:
                print(f"🔍 Імпорт файлу: {file_path}")

                # Валідація вхідного файлу
                if not os.path.exists(file_path):
                    messagebox.showerror("Помилка", f"Файл не існує: {file_path}")
                    return

                if not os.access(file_path, os.R_OK):
                    messagebox.showerror("Помилка", f"Немає доступу для читання файлу: {file_path}")
                    return

                # Перевірити підтримку формату
                if not self.format_handler.can_handle_format(file_path):
                    ext = os.path.splitext(file_path)[1].lower()
                    format_info = self.format_handler.get_format_info(file_path)

                    if not format_info.get('native', True):
                        missing_deps = self.format_handler.get_missing_dependencies()
                        if missing_deps:
                            messagebox.showerror(
                                "Відсутні залежності",
                                f"Для обробки {ext} файлів потрібно встановити:\n" + "\n".join(missing_deps)
                            )
                            return

                    messagebox.showwarning("Попередження", f"Формат {ext} може не підтримуватися")

                # Валідація папки призначення
                if not os.path.exists(self.textures_path):
                    try:
                        os.makedirs(self.textures_path, exist_ok=True)
                        print(f"📁 Створено папку: {self.textures_path}")
                    except Exception as e:
                        messagebox.showerror("Помилка", f"Не вдалося створити папку текстур: {e}")
                        return

                # Підготовка шляхів
                filename = os.path.basename(file_path)
                dest_path = os.path.join(self.textures_path, filename)

                print(f"📄 Джерело: {file_path}")
                print(f"📄 Призначення: {dest_path}")

                # Перевірити, чи файл вже існує
                if os.path.exists(dest_path):
                    result = messagebox.askyesno(
                        "Файл існує",
                        f"Файл {filename} вже існує. Замінити?"
                    )
                    if not result:
                        return

                # Спробувати завантажити зображення для валідації
                print("🖼️ Валідація зображення...")
                test_image = self.format_handler.load_image_as_pil(file_path)
                if test_image is None:
                    result = messagebox.askyesno(
                        "Попередження",
                        f"Не вдалося завантажити зображення як {os.path.splitext(filename)[1].upper()}.\n"
                        "Можливо, файл пошкоджений або формат не підтримується.\n\n"
                        "Продовжити імпорт?"
                    )
                    if not result:
                        return
                else:
                    print(f"✅ Зображення валідне: {test_image.size}")

                # Копіювати файл
                import shutil
                print("📋 Копіювання файлу...")
                shutil.copy2(file_path, dest_path)

                # Перевірити успішність копіювання
                if os.path.exists(dest_path):
                    file_size = os.path.getsize(dest_path)
                    print(f"✅ Файл скопійовано успішно ({file_size} байт)")
                    messagebox.showinfo("Успіх", f"Текстуру {filename} імпортовано успішно!")
                    self.refresh_textures()
                else:
                    messagebox.showerror("Помилка", "Файл не було скопійовано")

            except FileNotFoundError as e:
                error_msg = f"Файл не знайдено: {e}"
                print(f"❌ {error_msg}")
                messagebox.showerror("Помилка", error_msg)
            except PermissionError as e:
                error_msg = f"Немає дозволу на доступ до файлу: {e}"
                print(f"❌ {error_msg}")
                messagebox.showerror("Помилка", error_msg)
            except Exception as e:
                error_msg = f"Не вдалося імпортувати текстуру: {type(e).__name__}: {e}"
                print(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Помилка", error_msg)

    def batch_import(self):
        """Батч-імпорт текстур"""
        if not self.textures_path:
            messagebox.showwarning("Попередження", "Проєкт не відкрито")
            return

        file_paths = filedialog.askopenfilenames(
            title="Оберіть текстури для імпорту",
            filetypes=[
                ("Всі підтримувані", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp *.psd *.svg"),
                ("PNG файли", "*.png"),
                ("JPEG файли", "*.jpg *.jpeg"),
                ("PSD файли", "*.psd"),
                ("SVG файли", "*.svg"),
                ("Всі файли", "*.*")
            ]
        )

        if file_paths:
            print(f"🔍 Батч-імпорт {len(file_paths)} файл(ів)")

            # Валідація папки призначення
            if not os.path.exists(self.textures_path):
                try:
                    os.makedirs(self.textures_path, exist_ok=True)
                    print(f"📁 Створено папку: {self.textures_path}")
                except Exception as e:
                    messagebox.showerror("Помилка", f"Не вдалося створити папку текстур: {e}")
                    return

            imported_count = 0
            errors = []
            warnings = []

            for i, file_path in enumerate(file_paths):
                try:
                    print(f"📄 Обробка {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")

                    # Валідація файлу
                    if not os.path.exists(file_path):
                        errors.append(f"{os.path.basename(file_path)}: файл не існує")
                        continue

                    if not os.access(file_path, os.R_OK):
                        errors.append(f"{os.path.basename(file_path)}: немає доступу для читання")
                        continue

                    # Перевірити підтримку формату
                    if not self.format_handler.can_handle_format(file_path):
                        ext = os.path.splitext(file_path)[1].lower()
                        format_info = self.format_handler.get_format_info(file_path)

                        if not format_info.get('native', True):
                            warnings.append(f"{os.path.basename(file_path)}: формат {ext} може не підтримуватися")

                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(self.textures_path, filename)

                    # Перевірити конфлікт імен
                    if os.path.exists(dest_path):
                        base_name, ext = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(dest_path):
                            new_filename = f"{base_name}_{counter}{ext}"
                            dest_path = os.path.join(self.textures_path, new_filename)
                            counter += 1
                        warnings.append(f"{filename} перейменовано в {os.path.basename(dest_path)}")

                    # Копіювати файл
                    import shutil
                    shutil.copy2(file_path, dest_path)

                    # Перевірити успішність
                    if os.path.exists(dest_path):
                        imported_count += 1
                    else:
                        errors.append(f"{filename}: не вдалося скопіювати")

                except Exception as e:
                    filename = os.path.basename(file_path) if file_path else "невідомий файл"
                    errors.append(f"{filename}: {type(e).__name__}: {e}")

            # Показати детальний результат
            message_parts = [f"Імпортовано {imported_count} з {len(file_paths)} файл(ів)"]

            if warnings:
                message_parts.append(f"\nПопередження ({len(warnings)}):")
                message_parts.append("\n".join(warnings[:3]))
                if len(warnings) > 3:
                    message_parts.append(f"... та ще {len(warnings) - 3}")

            if errors:
                message_parts.append(f"\nПомилки ({len(errors)}):")
                message_parts.append("\n".join(errors[:3]))
                if len(errors) > 3:
                    message_parts.append(f"... та ще {len(errors) - 3}")

            message = "\n".join(message_parts)

            if errors:
                messagebox.showwarning("Результат батч-імпорту", message)
            else:
                messagebox.showinfo("Результат батч-імпорту", message)

            print(f"✅ Батч-імпорт завершено: {imported_count} успішно, {len(errors)} помилок")
            self.refresh_textures()

    def export_texture(self):
        """Експорт текстури"""
        if not self.selected_file:
            messagebox.showwarning("Попередження", "Оберіть файл для експорту")
            return

        file_path = filedialog.asksaveasfilename(
            title="Експорт текстури",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("Всі файли", "*.*")]
        )

        if file_path:
            try:
                import shutil
                shutil.copy2(self.selected_file['path'], file_path)
                messagebox.showinfo("Успіх", "Текстуру експортовано успішно!")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося експортувати: {e}")

    def convert_to_png(self):
        """Конвертація в PNG"""
        if not self.selected_file:
            messagebox.showwarning("Попередження", "Оберіть файл для конвертації")
            return

        if not self.textures_path:
            messagebox.showwarning("Попередження", "Проєкт не відкрито")
            return

        if self.selected_file['format_info']['name'] == 'PNG':
            messagebox.showinfo("Інформація", "Файл вже в форматі PNG")
            return

        try:
            # Створити нову назву файлу
            base_name = os.path.splitext(self.selected_file['name'])[0]
            new_name = f"{base_name}.png"
            new_path = os.path.join(self.textures_path, new_name)

            # Конвертувати
            success = self.format_handler.convert_to_png(
                self.selected_file['path'],
                new_path
            )

            if success:
                messagebox.showinfo("Успіх", f"Файл конвертовано в {new_name}")
                self.refresh_textures()
            else:
                messagebox.showerror("Помилка", "Не вдалося конвертувати файл")

        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка конвертації: {e}")

    def optimize_texture(self):
        """Оптимізація текстури"""
        if not self.selected_file:
            messagebox.showwarning("Попередження", "Оберіть файл для оптимізації")
            return

        if not self.textures_path:
            messagebox.showwarning("Попередження", "Проєкт не відкрито")
            return

        # Діалог налаштувань оптимізації
        dialog = OptimizationDialog(self.root, self.selected_file)
        if dialog.result:
            try:
                settings = dialog.result

                # Створити оптимізовану версію
                base_name = os.path.splitext(self.selected_file['name'])[0]
                optimized_name = f"{base_name}_optimized.png"
                optimized_path = os.path.join(self.textures_path, optimized_name)

                success = self.format_handler.optimize_image(
                    self.selected_file['path'],
                    optimized_path,
                    quality=settings['quality'],
                    max_size=settings['max_size']
                )

                if success:
                    messagebox.showinfo("Успіх", f"Файл оптимізовано: {optimized_name}")
                    self.refresh_textures()
                else:
                    messagebox.showerror("Помилка", "Не вдалося оптимізувати файл")

            except Exception as e:
                messagebox.showerror("Помилка", f"Помилка оптимізації: {e}")

    def delete_texture(self):
        """Видалити текстуру"""
        if not self.selected_file:
            messagebox.showwarning("Попередження", "Оберіть файл для видалення")
            return

        result = messagebox.askyesno(
            "Видалення",
            f"Ви впевнені, що хочете видалити {self.selected_file['name']}?\n\nЦю дію неможливо скасувати."
        )

        if result:
            try:
                os.remove(self.selected_file['path'])
                messagebox.showinfo("Успіх", "Текстуру видалено")
                self.selected_file = None
                self.refresh_textures()
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося видалити файл: {e}")

    def rename_texture(self):
        """Перейменувати текстуру"""
        if not self.selected_file:
            messagebox.showwarning("Попередження", "Оберіть файл для перейменування")
            return

        if not self.textures_path:
            messagebox.showwarning("Попередження", "Проєкт не відкрито")
            return

        # Простий діалог введення
        from tkinter import simpledialog

        current_name = os.path.splitext(self.selected_file['name'])[0]
        new_name = simpledialog.askstring(
            "Перейменування",
            "Введіть нову назву файлу:",
            initialvalue=current_name
        )

        if new_name and new_name != current_name:
            try:
                ext = os.path.splitext(self.selected_file['name'])[1]
                new_filename = f"{new_name}{ext}"
                new_path = os.path.join(self.textures_path, new_filename)

                if os.path.exists(new_path):
                    messagebox.showerror("Помилка", "Файл з такою назвою вже існує")
                    return

                os.rename(self.selected_file['path'], new_path)
                messagebox.showinfo("Успіх", f"Файл перейменовано на {new_filename}")
                self.refresh_textures()

            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося перейменувати файл: {e}")

    def duplicate_texture(self):
        """Дублювати текстуру"""
        if not self.selected_file:
            messagebox.showwarning("Попередження", "Оберіть файл для дублювання")
            return

        if not self.textures_path:
            messagebox.showwarning("Попередження", "Проєкт не відкрито")
            return

        try:
            base_name = os.path.splitext(self.selected_file['name'])[0]
            ext = os.path.splitext(self.selected_file['name'])[1]

            # Знайти унікальну назву
            counter = 1
            while True:
                new_name = f"{base_name}_copy{counter}{ext}"
                new_path = os.path.join(self.textures_path, new_name)
                if not os.path.exists(new_path):
                    break
                counter += 1

            import shutil
            shutil.copy2(self.selected_file['path'], new_path)
            messagebox.showinfo("Успіх", f"Файл дубльовано: {new_name}")
            self.refresh_textures()

        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося дублювати файл: {e}")

    def open_texture(self):
        """Відкрити текстуру в зовнішньому редакторі"""
        if not self.selected_file:
            messagebox.showwarning("Попередження", "Оберіть файл для відкриття")
            return

        try:
            import subprocess
            import platform

            if platform.system() == 'Windows':
                os.startfile(self.selected_file['path'])
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', self.selected_file['path']])
            else:  # Linux
                subprocess.run(['xdg-open', self.selected_file['path']])

        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося відкрити файл: {e}")

    def preview_texture(self):
        """Переглянути текстуру в окремому вікні"""
        if not self.selected_file:
            messagebox.showwarning("Попередження", "Оберіть файл для перегляду")
            return

        # Створити вікно попереднього перегляду
        PreviewWindow(self.root, self.selected_file, self.format_handler)


# Допоміжні класи
class OptimizationDialog:
    """Діалог налаштувань оптимізації"""

    def __init__(self, parent, file_data):
        self.result = None

        # Створити діалогове вікно
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Налаштування оптимізації")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Центрувати вікно
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))

        self.setup_ui(file_data)

        # Чекати закриття діалогу
        self.dialog.wait_window()

    def setup_ui(self, file_data):
        """Налаштування UI діалогу"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self.dialog,
            text=f"Оптимізація: {file_data['name']}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=20)

        # Налаштування якості
        quality_frame = ctk.CTkFrame(self.dialog)
        quality_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(quality_frame, text="Якість JPEG (%):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.quality_slider = ctk.CTkSlider(
            quality_frame,
            from_=10,
            to=100,
            number_of_steps=90
        )
        self.quality_slider.set(85)
        self.quality_slider.pack(fill="x", padx=10, pady=5)

        self.quality_label = ctk.CTkLabel(quality_frame, text="85%")
        self.quality_label.pack(padx=10, pady=(0, 10))

        self.quality_slider.configure(command=self.update_quality_label)

        # Максимальний розмір
        size_frame = ctk.CTkFrame(self.dialog)
        size_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(size_frame, text="Максимальний розмір:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.size_var = tk.StringVar(value="1024x1024")
        size_combo = ctk.CTkComboBox(
            size_frame,
            values=["Без обмежень", "512x512", "1024x1024", "2048x2048", "4096x4096"],
            variable=self.size_var
        )
        size_combo.pack(fill="x", padx=10, pady=(0, 10))

        # Кнопки
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(fill="x", padx=20, pady=20)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Скасувати",
            command=self.cancel
        )
        cancel_btn.pack(side="left", padx=10)

        ok_btn = ctk.CTkButton(
            button_frame,
            text="Оптимізувати",
            command=self.accept
        )
        ok_btn.pack(side="right", padx=10)

    def update_quality_label(self, value):
        """Оновити лейбл якості"""
        self.quality_label.configure(text=f"{int(value)}%")

    def accept(self):
        """Прийняти налаштування"""
        quality = int(self.quality_slider.get())

        size_text = self.size_var.get()
        if size_text == "Без обмежень":
            max_size = None
        else:
            size = int(size_text.split('x')[0])
            max_size = (size, size)

        self.result = {
            'quality': quality,
            'max_size': max_size
        }

        self.dialog.destroy()

    def cancel(self):
        """Скасувати"""
        self.result = None
        self.dialog.destroy()


class PreviewWindow:
    """Вікно попереднього перегляду"""

    def __init__(self, parent, file_data, format_handler):
        self.file_data = file_data
        self.format_handler = format_handler

        # Створити вікно
        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"Перегляд: {file_data['name']}")
        self.window.geometry("800x600")

        self.setup_ui()
        self.load_image()

    def setup_ui(self):
        """Налаштування UI"""
        # Заголовок
        header = ctk.CTkFrame(self.window)
        header.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            header,
            text=self.file_data['name'],
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)

        # Область зображення
        self.image_frame = ctk.CTkFrame(self.window)
        self.image_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.image_label = ctk.CTkLabel(
            self.image_frame,
            text="Завантаження..."
        )
        self.image_label.pack(expand=True)

    def load_image(self):
        """Завантажити зображення"""
        try:
            pil_image = self.format_handler.load_image_as_pil(self.file_data['path'])
            if pil_image:
                # Масштабувати для відображення
                max_size = (700, 500)
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)

                photo = ImageTk.PhotoImage(pil_image)
                self.image_label.configure(image=photo, text="")
            else:
                self.image_label.configure(text="Не вдалося завантажити зображення")
        except Exception as e:
            self.image_label.configure(text=f"Помилка: {e}")

def main():
    """Головна функція для тестування"""
    print("🎨 Запуск CustomTkinter Менеджера текстур")
    
    # Тестовий шлях до проєкту
    test_project_path = os.path.join(os.getcwd(), "test_project")
    
    try:
        app = TextureManagerCustomTkinter(test_project_path)
        app.run()
    except Exception as e:
        print(f"Помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
