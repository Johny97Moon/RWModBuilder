#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Покращений менеджер текстур для RimWorld Mod Builder v1.0.1 Alpha
Розширені функції: batch конвертація, drag & drop, zoom/pan, метадані, undo/redo
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import json
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from PIL import Image, ImageTk
import shutil

# Локальні імпорти
try:
    from core.image_formats import ImageFormatHandler
    from utils.simple_logger import get_logger_instance
except ImportError as e:
    print(f"Помилка імпорту: {e}")
    # Fallback для тестування
    class MockImageFormatHandler:
        def load_image_as_pil(self, path): return None
        def can_handle_format(self, path): return True
        def get_format_info(self, path): return {"native": True}
        def get_missing_dependencies(self): return []
    
    def get_logger_instance():
        class Logger:
            def get_logger(self): 
                class L:
                    def info(self, m): print(f"INFO: {m}")
                    def error(self, m): print(f"ERROR: {m}")
                    def warning(self, m): print(f"WARNING: {m}")
                    def debug(self, m): print(f"DEBUG: {m}")
                return L()
        return Logger()


@dataclass
class TextureMetadata:
    """Метадані текстури"""
    filename: str
    filepath: str
    format: str
    size: Tuple[int, int]
    file_size: int
    color_mode: str
    has_transparency: bool
    created_date: str
    modified_date: str
    dpi: Optional[Tuple[int, int]] = None
    compression: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TextureOperation:
    """Операція з текстурою для undo/redo"""
    operation_type: str  # "import", "delete", "convert", "rename"
    timestamp: str
    files_before: List[str]
    files_after: List[str]
    metadata: Dict[str, Any]


class DragDropFrame(ctk.CTkFrame):
    """Фрейм з підтримкою drag & drop"""
    
    def __init__(self, parent, drop_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.drop_callback = drop_callback
        self.setup_drag_drop()
    
    def setup_drag_drop(self):
        """Налаштування drag & drop"""
        try:
            # Реєстрація для drag & drop
            self.drop_target_register(tk.DND_FILES)
            self.dnd_bind('<<Drop>>', self.on_drop)
            self.dnd_bind('<<DragEnter>>', self.on_drag_enter)
            self.dnd_bind('<<DragLeave>>', self.on_drag_leave)
        except:
            # Fallback якщо tkinterdnd2 не доступний
            self.bind("<Button-1>", self.on_click_fallback)
    
    def on_drop(self, event):
        """Обробка drop події"""
        if self.drop_callback and hasattr(event, 'data'):
            files = event.data.split()
            self.drop_callback(files)
    
    def on_drag_enter(self, event):
        """Обробка входу в зону drop"""
        self.configure(border_color="green", border_width=2)
    
    def on_drag_leave(self, event):
        """Обробка виходу з зони drop"""
        self.configure(border_color="gray", border_width=1)
    
    def on_click_fallback(self, event):
        """Fallback для відсутності drag & drop"""
        if self.drop_callback:
            files = filedialog.askopenfilenames(
                title="Оберіть файли для імпорту",
                filetypes=[
                    ("Зображення", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp *.psd *.svg"),
                    ("Всі файли", "*.*")
                ]
            )
            if files:
                self.drop_callback(list(files))


class ZoomPanCanvas(ctk.CTkCanvas):
    """Canvas з підтримкою zoom та pan"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.scale = 1.0
        self.min_scale = 0.1
        self.max_scale = 10.0
        self.image_id = None
        self.original_image = None
        self.current_image = None
        
        self.bind("<MouseWheel>", self.on_zoom)
        self.bind("<Button-1>", self.on_pan_start)
        self.bind("<B1-Motion>", self.on_pan_move)
        self.bind("<ButtonRelease-1>", self.on_pan_end)
        
        self.pan_start_x = 0
        self.pan_start_y = 0
    
    def set_image(self, pil_image: Image.Image):
        """Встановлення зображення"""
        self.original_image = pil_image
        self.scale = 1.0
        self.update_image()
    
    def update_image(self):
        """Оновлення відображення зображення"""
        if not self.original_image:
            return
        
        # Масштабування
        new_size = (
            int(self.original_image.width * self.scale),
            int(self.original_image.height * self.scale)
        )
        
        if new_size[0] > 0 and new_size[1] > 0:
            self.current_image = self.original_image.resize(new_size, Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(self.current_image)
            
            # Оновлення canvas
            self.delete("all")
            self.image_id = self.create_image(
                self.winfo_width() // 2,
                self.winfo_height() // 2,
                image=self.photo
            )
            
            # Оновлення scroll region
            self.configure(scrollregion=self.bbox("all"))
    
    def on_zoom(self, event):
        """Обробка zoom"""
        if not self.original_image:
            return
        
        # Визначення напрямку zoom
        if event.delta > 0:
            factor = 1.1
        else:
            factor = 0.9
        
        new_scale = self.scale * factor
        
        # Обмеження масштабу
        if self.min_scale <= new_scale <= self.max_scale:
            self.scale = new_scale
            self.update_image()
    
    def on_pan_start(self, event):
        """Початок pan"""
        self.pan_start_x = event.x
        self.pan_start_y = event.y
    
    def on_pan_move(self, event):
        """Рух pan"""
        if self.image_id:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.move(self.image_id, dx, dy)
            self.pan_start_x = event.x
            self.pan_start_y = event.y
    
    def on_pan_end(self, event):
        """Кінець pan"""
        pass
    
    def reset_view(self):
        """Скидання виду"""
        self.scale = 1.0
        self.update_image()
    
    def fit_to_window(self):
        """Підгонка під розмір вікна"""
        if not self.original_image:
            return
        
        canvas_width = self.winfo_width()
        canvas_height = self.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            scale_x = canvas_width / self.original_image.width
            scale_y = canvas_height / self.original_image.height
            self.scale = min(scale_x, scale_y) * 0.9  # 90% від розміру
            
            if self.scale < self.min_scale:
                self.scale = self.min_scale
            elif self.scale > self.max_scale:
                self.scale = self.max_scale
            
            self.update_image()


class BatchConversionDialog(ctk.CTkToplevel):
    """Діалог batch конвертації"""
    
    def __init__(self, parent, files: List[str], **kwargs):
        super().__init__(parent, **kwargs)
        
        self.files = files
        self.conversion_results = []
        
        self.title("🔄 Batch конвертація")
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Заголовок
        header_label = ctk.CTkLabel(
            self,
            text=f"🔄 Конвертація {len(self.files)} файлів",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header_label.pack(pady=10)
        
        # Налаштування конвертації
        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        # Формат виводу
        format_label = ctk.CTkLabel(settings_frame, text="Формат виводу:")
        format_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.output_format = ctk.CTkOptionMenu(
            settings_frame,
            values=["PNG", "JPEG", "WEBP", "TIFF"],
            width=100
        )
        self.output_format.set("PNG")
        self.output_format.grid(row=0, column=1, padx=5, pady=5)
        
        # Якість (для JPEG/WEBP)
        quality_label = ctk.CTkLabel(settings_frame, text="Якість:")
        quality_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        self.quality_slider = ctk.CTkSlider(
            settings_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            width=150
        )
        self.quality_slider.set(95)
        self.quality_slider.grid(row=0, column=3, padx=5, pady=5)
        
        self.quality_value = ctk.CTkLabel(settings_frame, text="95%")
        self.quality_value.grid(row=0, column=4, padx=5, pady=5)
        
        self.quality_slider.configure(command=self.update_quality_label)
        
        # Прогрес
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_label = ctk.CTkLabel(progress_frame, text="Готовий до конвертації")
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        # Список файлів
        files_frame = ctk.CTkFrame(self)
        files_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.files_list = ctk.CTkScrollableFrame(files_frame, label_text="Файли для конвертації")
        self.files_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        for file_path in self.files:
            file_label = ctk.CTkLabel(
                self.files_list,
                text=os.path.basename(file_path),
                anchor="w"
            )
            file_label.pack(fill="x", padx=5, pady=2)
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        self.convert_button = ctk.CTkButton(
            buttons_frame,
            text="🔄 Конвертувати",
            command=self.start_conversion,
            width=120
        )
        self.convert_button.pack(side="left", padx=5)
        
        self.cancel_button = ctk.CTkButton(
            buttons_frame,
            text="❌ Скасувати",
            command=self.destroy,
            width=120
        )
        self.cancel_button.pack(side="right", padx=5)
    
    def update_quality_label(self, value):
        """Оновлення лейбла якості"""
        self.quality_value.configure(text=f"{int(value)}%")
    
    def start_conversion(self):
        """Початок конвертації"""
        def conversion_worker():
            try:
                output_format = self.output_format.get().lower()
                quality = int(self.quality_slider.get())
                
                for i, file_path in enumerate(self.files):
                    # Оновлення прогресу
                    progress = (i / len(self.files)) * 100
                    filename = os.path.basename(file_path)
                    
                    self.after(0, lambda p=progress, f=filename: self.update_progress(p, f"Конвертація {f}..."))
                    
                    # Конвертація файлу
                    success = self.convert_file(file_path, output_format, quality)
                    self.conversion_results.append({
                        "file": file_path,
                        "success": success
                    })
                
                # Завершення
                self.after(0, lambda: self.conversion_complete())
                
            except Exception as e:
                self.after(0, lambda: self.conversion_error(str(e)))
        
        # Запуск в окремому потоці
        self.convert_button.configure(state="disabled")
        thread = threading.Thread(target=conversion_worker, daemon=True)
        thread.start()
    
    def convert_file(self, file_path: str, output_format: str, quality: int) -> bool:
        """Конвертація одного файлу"""
        try:
            # Завантаження зображення
            image = Image.open(file_path)
            
            # Генерація нового імені
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_dir = os.path.dirname(file_path)
            output_path = os.path.join(output_dir, f"{base_name}_converted.{output_format}")
            
            # Конвертація
            if output_format in ["jpeg", "jpg"]:
                # Конвертація в RGB для JPEG
                if image.mode in ("RGBA", "LA", "P"):
                    rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                    if image.mode == "P":
                        image = image.convert("RGBA")
                    rgb_image.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                    image = rgb_image
                
                image.save(output_path, format="JPEG", quality=quality, optimize=True)
            
            elif output_format == "webp":
                image.save(output_path, format="WEBP", quality=quality, optimize=True)
            
            else:
                image.save(output_path, format=output_format.upper())
            
            return True
            
        except Exception as e:
            print(f"Помилка конвертації {file_path}: {e}")
            return False
    
    def update_progress(self, progress: float, message: str):
        """Оновлення прогресу"""
        self.progress_bar.set(progress / 100.0)
        self.progress_label.configure(text=message)
    
    def conversion_complete(self):
        """Завершення конвертації"""
        successful = sum(1 for r in self.conversion_results if r["success"])
        total = len(self.conversion_results)
        
        self.progress_bar.set(1.0)
        self.progress_label.configure(text=f"✅ Завершено: {successful}/{total} файлів")
        
        messagebox.showinfo(
            "Конвертація завершена",
            f"Успішно конвертовано {successful} з {total} файлів"
        )
        
        self.convert_button.configure(state="normal", text="✅ Завершено")
    
    def conversion_error(self, error_message: str):
        """Помилка конвертації"""
        self.progress_label.configure(text=f"❌ Помилка: {error_message}")
        messagebox.showerror("Помилка конвертації", error_message)
        self.convert_button.configure(state="normal")


class EnhancedTextureManager(ctk.CTkFrame):
    """Покращений менеджер текстур"""
    
    def __init__(self, parent, project_path: Optional[str] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.project_path = project_path
        self.textures_path = os.path.join(project_path, "Textures") if project_path else None
        self.format_handler = ImageFormatHandler() if 'ImageFormatHandler' in globals() else MockImageFormatHandler()
        self.logger = get_logger_instance().get_logger()
        
        # Стан
        self.current_files = []
        self.selected_file = None
        self.operation_history = []  # Для undo/redo
        self.history_index = -1
        
        # Кеш метаданих
        self.metadata_cache = {}
        
        self.setup_ui()
        self.refresh_files()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Заголовок
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🎨 Покращений менеджер текстур",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=5)
        
        # Панель інструментів
        toolbar_frame = ctk.CTkFrame(self)
        toolbar_frame.pack(fill="x", padx=5, pady=5)
        
        # Кнопки дій
        self.refresh_button = ctk.CTkButton(
            toolbar_frame,
            text="🔄",
            command=self.refresh_files,
            width=40
        )
        self.refresh_button.pack(side="left", padx=2)
        
        self.import_button = ctk.CTkButton(
            toolbar_frame,
            text="📥 Імпорт",
            command=self.import_files,
            width=80
        )
        self.import_button.pack(side="left", padx=2)
        
        self.batch_convert_button = ctk.CTkButton(
            toolbar_frame,
            text="🔄 Batch",
            command=self.batch_convert,
            width=80
        )
        self.batch_convert_button.pack(side="left", padx=2)
        
        # Undo/Redo
        self.undo_button = ctk.CTkButton(
            toolbar_frame,
            text="↶",
            command=self.undo,
            width=40,
            state="disabled"
        )
        self.undo_button.pack(side="left", padx=2)
        
        self.redo_button = ctk.CTkButton(
            toolbar_frame,
            text="↷",
            command=self.redo,
            width=40,
            state="disabled"
        )
        self.redo_button.pack(side="left", padx=2)
        
        # Основний контент
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Ліва панель - список файлів
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Drag & Drop зона
        self.drop_zone = DragDropFrame(
            left_frame,
            drop_callback=self.on_files_dropped,
            height=100
        )
        self.drop_zone.pack(fill="x", padx=5, pady=5)
        
        drop_label = ctk.CTkLabel(
            self.drop_zone,
            text="📁 Перетягніть файли сюди або натисніть для вибору",
            font=ctk.CTkFont(size=12)
        )
        drop_label.pack(expand=True)
        
        # Список файлів
        self.files_list = ctk.CTkScrollableFrame(left_frame, label_text="📋 Файли текстур")
        self.files_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Права панель - попередній перегляд
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="both", padx=(5, 0))
        right_frame.configure(width=400)
        
        # Попередній перегляд
        preview_label = ctk.CTkLabel(
            right_frame,
            text="👁️ Попередній перегляд",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        preview_label.pack(pady=5)
        
        # Canvas для зображення
        self.preview_canvas = ZoomPanCanvas(
            right_frame,
            width=350,
            height=300,
            bg="gray20"
        )
        self.preview_canvas.pack(padx=5, pady=5)
        
        # Кнопки керування переглядом
        view_controls = ctk.CTkFrame(right_frame)
        view_controls.pack(fill="x", padx=5, pady=5)
        
        self.reset_view_button = ctk.CTkButton(
            view_controls,
            text="🔄 Скинути",
            command=self.preview_canvas.reset_view,
            width=80
        )
        self.reset_view_button.pack(side="left", padx=2)
        
        self.fit_view_button = ctk.CTkButton(
            view_controls,
            text="📐 Підігнати",
            command=self.preview_canvas.fit_to_window,
            width=80
        )
        self.fit_view_button.pack(side="left", padx=2)
        
        # Метадані
        self.metadata_frame = ctk.CTkScrollableFrame(
            right_frame,
            label_text="📊 Метадані",
            height=200
        )
        self.metadata_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    def refresh_files(self):
        """Оновлення списку файлів"""
        if not self.textures_path or not os.path.exists(self.textures_path):
            return

        # Очищення списку
        for widget in self.files_list.winfo_children():
            widget.destroy()

        self.current_files = []

        # Сканування файлів
        supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp', '.psd', '.svg']

        for root, _, files in os.walk(self.textures_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in supported_formats):
                    file_path = os.path.join(root, file)
                    self.current_files.append(file_path)

        # Створення віджетів файлів
        for file_path in self.current_files:
            self.create_file_widget(file_path)

        self.logger.info(f"📁 Знайдено {len(self.current_files)} файлів текстур")
    
    def create_file_widget(self, file_path: str):
        """Створення віджета файлу"""
        file_frame = ctk.CTkFrame(self.files_list)
        file_frame.pack(fill="x", padx=2, pady=1)

        # Іконка формату
        ext = os.path.splitext(file_path)[1].lower()
        format_icon = self.get_format_icon(ext)

        icon_label = ctk.CTkLabel(
            file_frame,
            text=format_icon,
            width=30,
            font=ctk.CTkFont(size=12)
        )
        icon_label.pack(side="left", padx=5)

        # Назва файлу
        filename = os.path.basename(file_path)
        name_label = ctk.CTkLabel(
            file_frame,
            text=filename,
            anchor="w",
            font=ctk.CTkFont(size=11)
        )
        name_label.pack(side="left", fill="x", expand=True, padx=5)

        # Розмір файлу
        try:
            file_size = os.path.getsize(file_path)
            size_text = self.format_file_size(file_size)
            size_label = ctk.CTkLabel(
                file_frame,
                text=size_text,
                width=60,
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            size_label.pack(side="right", padx=5)
        except:
            pass

        # Клік для вибору
        def on_select():
            self.select_file(file_path)

        file_frame.bind("<Button-1>", lambda _: on_select())
        icon_label.bind("<Button-1>", lambda _: on_select())
        name_label.bind("<Button-1>", lambda _: on_select())

    def get_format_icon(self, ext: str) -> str:
        """Отримання іконки формату"""
        icons = {
            '.png': '🖼️',
            '.jpg': '📷',
            '.jpeg': '📷',
            '.bmp': '🎨',
            '.gif': '🎬',
            '.tiff': '📄',
            '.webp': '🌐',
            '.psd': '🎭',
            '.svg': '📐'
        }
        return icons.get(ext, '📁')

    def format_file_size(self, size_bytes: int) -> str:
        """Форматування розміру файлу"""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f}MB"

    def select_file(self, file_path: str):
        """Вибір файлу"""
        self.selected_file = file_path
        self.load_preview(file_path)
        self.load_metadata(file_path)
        self.logger.debug(f"Вибрано файл: {os.path.basename(file_path)}")

    def load_preview(self, file_path: str):
        """Завантаження попереднього перегляду"""
        try:
            image = self.format_handler.load_image_as_pil(file_path)
            if image:
                # Конвертація в RGB якщо потрібно
                if image.mode in ('RGBA', 'LA', 'P'):
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    if image.mode in ('RGBA', 'LA'):
                        rgb_image.paste(image, mask=image.split()[-1] if len(image.split()) > 3 else None)
                        image = rgb_image

                self.preview_canvas.set_image(image)
                self.preview_canvas.fit_to_window()
            else:
                self.preview_canvas.delete("all")
                self.preview_canvas.create_text(
                    175, 150,
                    text="❌ Не вдалося завантажити",
                    fill="red",
                    font=("Arial", 12)
                )
        except Exception as e:
            self.logger.error(f"Помилка завантаження попереднього перегляду: {e}")
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                175, 150,
                text=f"❌ Помилка: {str(e)}",
                fill="red",
                font=("Arial", 10)
            )

    def load_metadata(self, file_path: str):
        """Завантаження метаданих"""
        # Очищення попередніх метаданих
        for widget in self.metadata_frame.winfo_children():
            widget.destroy()

        try:
            # Отримання метаданих
            metadata = self.get_file_metadata(file_path)

            # Відображення метаданих
            for key, value in metadata.to_dict().items():
                if value is not None:
                    self.create_metadata_row(key, value)

        except Exception as e:
            self.logger.error(f"Помилка завантаження метаданих: {e}")
            error_label = ctk.CTkLabel(
                self.metadata_frame,
                text=f"❌ Помилка: {str(e)}",
                text_color="red"
            )
            error_label.pack(pady=5)

    def get_file_metadata(self, file_path: str) -> TextureMetadata:
        """Отримання метаданих файлу"""
        # Перевірка кешу
        if file_path in self.metadata_cache:
            return self.metadata_cache[file_path]

        # Базова інформація про файл
        stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        file_format = os.path.splitext(filename)[1][1:].upper()

        # Спроба завантаження зображення для отримання розміру
        try:
            image = self.format_handler.load_image_as_pil(file_path)
            if image:
                size = image.size
                color_mode = image.mode
                has_transparency = image.mode in ('RGBA', 'LA') or 'transparency' in image.info
                dpi = image.info.get('dpi')
            else:
                size = (0, 0)
                color_mode = "Unknown"
                has_transparency = False
                dpi = None
        except:
            size = (0, 0)
            color_mode = "Unknown"
            has_transparency = False
            dpi = None

        metadata = TextureMetadata(
            filename=filename,
            filepath=file_path,
            format=file_format,
            size=size,
            file_size=stat.st_size,
            color_mode=color_mode,
            has_transparency=has_transparency,
            created_date=datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
            modified_date=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            dpi=dpi
        )

        # Кешування
        self.metadata_cache[file_path] = metadata
        return metadata

    def create_metadata_row(self, key: str, value: Any):
        """Створення рядка метаданих"""
        row_frame = ctk.CTkFrame(self.metadata_frame)
        row_frame.pack(fill="x", padx=2, pady=1)

        # Назва поля
        key_label = ctk.CTkLabel(
            row_frame,
            text=f"{self.translate_metadata_key(key)}:",
            width=100,
            anchor="w",
            font=ctk.CTkFont(size=10, weight="bold")
        )
        key_label.pack(side="left", padx=5)

        # Значення
        value_text = str(value)
        if key == "size" and isinstance(value, tuple):
            value_text = f"{value[0]} × {value[1]}"
        elif key == "file_size":
            value_text = self.format_file_size(value)

        value_label = ctk.CTkLabel(
            row_frame,
            text=value_text,
            anchor="w",
            font=ctk.CTkFont(size=10)
        )
        value_label.pack(side="left", fill="x", expand=True, padx=5)

    def translate_metadata_key(self, key: str) -> str:
        """Переклад ключів метаданих"""
        translations = {
            "filename": "Файл",
            "format": "Формат",
            "size": "Розмір",
            "file_size": "Розмір файлу",
            "color_mode": "Колірний режим",
            "has_transparency": "Прозорість",
            "created_date": "Створено",
            "modified_date": "Змінено",
            "dpi": "DPI"
        }
        return translations.get(key, key.title())

    def import_files(self):
        """Імпорт файлів"""
        files = filedialog.askopenfilenames(
            title="Оберіть файли для імпорту",
            filetypes=[
                ("Зображення", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp *.psd *.svg"),
                ("Всі файли", "*.*")
            ]
        )
        if files:
            self.on_files_dropped(list(files))

    def batch_convert(self):
        """Batch конвертація"""
        if not self.current_files:
            messagebox.showwarning("Попередження", "Немає файлів для конвертації")
            return

        _ = BatchConversionDialog(self, self.current_files)

    def on_files_dropped(self, files: List[str]):
        """Обробка dropped файлів"""
        if not self.textures_path:
            messagebox.showerror("Помилка", "Проєкт не відкрито")
            return

        # Створення папки Textures якщо не існує
        os.makedirs(self.textures_path, exist_ok=True)

        imported_files = []
        errors = []

        for file_path in files:
            try:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(self.textures_path, filename)

                    # Копіювання файлу
                    shutil.copy2(file_path, dest_path)
                    imported_files.append(filename)

            except Exception as e:
                errors.append(f"{os.path.basename(file_path)}: {str(e)}")

        # Результат
        if imported_files:
            self.add_operation_to_history("import", [], imported_files)
            self.refresh_files()
            messagebox.showinfo(
                "Імпорт завершено",
                f"Імпортовано {len(imported_files)} файлів"
            )

        if errors:
            messagebox.showerror(
                "Помилки імпорту",
                f"Помилки:\n" + "\n".join(errors[:5])  # Показати перші 5 помилок
            )

    def add_operation_to_history(self, operation_type: str, files_before: List[str], files_after: List[str]):
        """Додавання операції до історії"""
        operation = TextureOperation(
            operation_type=operation_type,
            timestamp=datetime.now().isoformat(),
            files_before=files_before,
            files_after=files_after,
            metadata={}
        )

        # Видалення операцій після поточної позиції
        self.operation_history = self.operation_history[:self.history_index + 1]

        # Додавання нової операції
        self.operation_history.append(operation)
        self.history_index = len(self.operation_history) - 1

        # Оновлення кнопок
        self.update_undo_redo_buttons()

    def update_undo_redo_buttons(self):
        """Оновлення стану кнопок undo/redo"""
        can_undo = self.history_index >= 0
        can_redo = self.history_index < len(self.operation_history) - 1

        self.undo_button.configure(state="normal" if can_undo else "disabled")
        self.redo_button.configure(state="normal" if can_redo else "disabled")

    def undo(self):
        """Скасування операції"""
        if self.history_index >= 0:
            operation = self.operation_history[self.history_index]
            self.reverse_operation(operation)
            self.history_index -= 1
            self.update_undo_redo_buttons()
            self.refresh_files()

    def redo(self):
        """Повторення операції"""
        if self.history_index < len(self.operation_history) - 1:
            self.history_index += 1
            operation = self.operation_history[self.history_index]
            self.apply_operation(operation)
            self.update_undo_redo_buttons()
            self.refresh_files()

    def reverse_operation(self, operation: TextureOperation):
        """Скасування операції"""
        if operation.operation_type == "import" and self.textures_path:
            # Видалення імпортованих файлів
            for filename in operation.files_after:
                file_path = os.path.join(self.textures_path, filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        self.logger.error(f"Помилка видалення {filename}: {e}")

    def apply_operation(self, operation: TextureOperation):
        """Застосування операції"""
        # Для redo операцій імпорту потрібно було б зберігати оригінальні файли
        # Це спрощена реалізація
        _ = operation  # Заглушка для unused parameter


if __name__ == "__main__":
    # Тестування покращеного менеджера текстур
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("Тест покращеного менеджера текстур")
    root.geometry("1200x800")
    
    manager = EnhancedTextureManager(root, project_path="./test_project")
    manager.pack(fill="both", expand=True, padx=10, pady=10)
    
    root.mainloop()
