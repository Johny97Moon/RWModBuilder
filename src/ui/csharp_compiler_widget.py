#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Віджет компілятора C# для RimWorld Mod Builder v2.0.1
UI для компіляції, тестування та налагодження C# проєктів
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import threading
import subprocess
from typing import Optional, List, Tuple
import time

# Локальні імпорти
try:
    from core.dotnet_integration import get_dotnet_environment, CSharpCompiler
    from utils.simple_logger import get_logger_instance
except ImportError as e:
    print(f"Помилка імпорту: {e}")
    # Fallback для тестування
    class MockDotNetEnvironment:
        def is_available(self): return False
        def get_environment_info(self): return {"is_ready": False}
    
    class MockCSharpCompiler:
        def __init__(self, env): pass
        def compile_project(self, path, config): return False, "Mock compiler"
    
    def get_dotnet_environment(): return MockDotNetEnvironment()
    def get_logger_instance():
        class Logger:
            def get_logger(self): 
                class L:
                    def info(self, m): print(f"INFO: {m}")
                    def error(self, m): print(f"ERROR: {m}")
                    def warning(self, m): print(f"WARNING: {m}")
                return L()
        return Logger()


class CompilationOutputWidget(ctk.CTkFrame):
    """Віджет виводу компіляції"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Заголовок
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=5, pady=5)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📋 Вивід компіляції",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(side="left", padx=10, pady=5)
        
        # Кнопки управління
        buttons_frame = ctk.CTkFrame(header_frame)
        buttons_frame.pack(side="right", padx=10, pady=5)
        
        self.clear_button = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Очистити",
            command=self.clear_output,
            width=80
        )
        self.clear_button.pack(side="left", padx=2)
        
        self.copy_button = ctk.CTkButton(
            buttons_frame,
            text="📋 Копіювати",
            command=self.copy_output,
            width=80
        )
        self.copy_button.pack(side="left", padx=2)
        
        # Текстове поле виводу
        self.output_text = ctk.CTkTextbox(
            self,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Початковий текст
        self.add_output("Готовий до компіляції...\n", "info")
    
    def add_output(self, text: str, level: str = "info"):
        """Додавання тексту до виводу"""
        timestamp = time.strftime("%H:%M:%S")
        
        # Кольори для різних рівнів
        colors = {
            "info": "#FFFFFF",
            "success": "#00FF00", 
            "warning": "#FFAA00",
            "error": "#FF4444",
            "debug": "#AAAAAA"
        }
        
        color = colors.get(level, "#FFFFFF")
        
        # Додавання тексту
        self.output_text.insert("end", f"[{timestamp}] {text}")
        self.output_text.see("end")
        
        # Автопрокрутка
        self.output_text.update()
    
    def clear_output(self):
        """Очищення виводу"""
        self.output_text.delete("1.0", "end")
        self.add_output("Вивід очищено.\n", "info")
    
    def copy_output(self):
        """Копіювання виводу в буфер обміну"""
        try:
            content = self.output_text.get("1.0", "end-1c")
            self.clipboard_clear()
            self.clipboard_append(content)
            self.add_output("Вивід скопійовано в буфер обміну.\n", "success")
        except Exception as e:
            self.add_output(f"Помилка копіювання: {e}\n", "error")


class ProjectSelectorWidget(ctk.CTkFrame):
    """Віджет вибору проєкту"""
    
    def __init__(self, parent, on_project_selected=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_project_selected = on_project_selected
        self.current_project = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="📁 Вибір проєкту",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=(10, 5))
        
        # Поле шляху
        path_frame = ctk.CTkFrame(self)
        path_frame.pack(fill="x", padx=10, pady=5)
        
        self.path_entry = ctk.CTkEntry(
            path_frame,
            placeholder_text="Шлях до .csproj файлу..."
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        browse_button = ctk.CTkButton(
            path_frame,
            text="📁",
            command=self.browse_project,
            width=40
        )
        browse_button.pack(side="right", padx=5, pady=5)
        
        # Інформація про проєкт
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(fill="x", padx=10, pady=5)
        
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="Проєкт не обрано",
            font=ctk.CTkFont(size=12)
        )
        self.info_label.pack(pady=10)
    
    def browse_project(self):
        """Вибір проєкту"""
        file_path = filedialog.askopenfilename(
            title="Оберіть .csproj файл",
            filetypes=[
                ("C# Project files", "*.csproj"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.set_project(file_path)
    
    def set_project(self, project_path: str):
        """Встановлення поточного проєкту"""
        if not os.path.exists(project_path):
            messagebox.showerror("Помилка", "Файл проєкту не існує")
            return
        
        self.current_project = project_path
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, project_path)
        
        # Оновлення інформації
        project_name = os.path.splitext(os.path.basename(project_path))[0]
        project_dir = os.path.dirname(project_path)
        
        info_text = f"📦 Проєкт: {project_name}\n📁 Папка: {project_dir}"
        self.info_label.configure(text=info_text)
        
        # Виклик callback
        if self.on_project_selected:
            self.on_project_selected(project_path)
    
    def get_project_path(self) -> Optional[str]:
        """Отримання шляху поточного проєкту"""
        return self.current_project


class CompilationSettingsWidget(ctk.CTkFrame):
    """Віджет налаштувань компіляції"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="⚙️ Налаштування компіляції",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=(10, 5))
        
        # Конфігурація
        config_frame = ctk.CTkFrame(self)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        config_label = ctk.CTkLabel(config_frame, text="Конфігурація:")
        config_label.pack(side="left", padx=5, pady=5)
        
        self.config_var = ctk.StringVar(value="Release")
        self.config_menu = ctk.CTkOptionMenu(
            config_frame,
            variable=self.config_var,
            values=["Debug", "Release"]
        )
        self.config_menu.pack(side="right", padx=5, pady=5)
        
        # Платформа
        platform_frame = ctk.CTkFrame(self)
        platform_frame.pack(fill="x", padx=10, pady=5)
        
        platform_label = ctk.CTkLabel(platform_frame, text="Платформа:")
        platform_label.pack(side="left", padx=5, pady=5)
        
        self.platform_var = ctk.StringVar(value="AnyCPU")
        self.platform_menu = ctk.CTkOptionMenu(
            platform_frame,
            variable=self.platform_var,
            values=["AnyCPU", "x86", "x64"]
        )
        self.platform_menu.pack(side="right", padx=5, pady=5)
        
        # Додаткові опції
        options_frame = ctk.CTkFrame(self)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        self.verbose_var = ctk.BooleanVar(value=False)
        verbose_checkbox = ctk.CTkCheckBox(
            options_frame,
            text="Детальний вивід",
            variable=self.verbose_var
        )
        verbose_checkbox.pack(side="left", padx=5, pady=5)
        
        self.clean_var = ctk.BooleanVar(value=True)
        clean_checkbox = ctk.CTkCheckBox(
            options_frame,
            text="Очистити перед збіркою",
            variable=self.clean_var
        )
        clean_checkbox.pack(side="left", padx=5, pady=5)
    
    def get_settings(self) -> dict:
        """Отримання налаштувань компіляції"""
        return {
            "configuration": self.config_var.get(),
            "platform": self.platform_var.get(),
            "verbose": self.verbose_var.get(),
            "clean": self.clean_var.get()
        }


class CSharpCompilerWidget(ctk.CTkFrame):
    """Головний віджет компілятора C#"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.dotnet_env = get_dotnet_environment()
        self.compiler = CSharpCompiler(self.dotnet_env)
        self.logger = get_logger_instance().get_logger()
        
        self.current_project = None
        self.compilation_thread = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Заголовок
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔨 Компілятор C#",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Основний контент
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Ліва панель - налаштування
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="y", padx=(0, 5))
        left_frame.configure(width=350)
        
        # Вибір проєкту
        self.project_selector = ProjectSelectorWidget(
            left_frame,
            on_project_selected=self.on_project_selected
        )
        self.project_selector.pack(fill="x", padx=5, pady=5)
        
        # Налаштування компіляції
        self.compilation_settings = CompilationSettingsWidget(left_frame)
        self.compilation_settings.pack(fill="x", padx=5, pady=5)
        
        # Кнопки дій
        actions_frame = ctk.CTkFrame(left_frame)
        actions_frame.pack(fill="x", padx=5, pady=10)
        
        self.compile_button = ctk.CTkButton(
            actions_frame,
            text="🔨 Компілювати",
            command=self.compile_project,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.compile_button.pack(fill="x", padx=5, pady=5)
        
        self.clean_button = ctk.CTkButton(
            actions_frame,
            text="🗑️ Очистити",
            command=self.clean_project,
            height=30
        )
        self.clean_button.pack(fill="x", padx=5, pady=2)
        
        self.rebuild_button = ctk.CTkButton(
            actions_frame,
            text="🔄 Перезібрати",
            command=self.rebuild_project,
            height=30
        )
        self.rebuild_button.pack(fill="x", padx=5, pady=2)
        
        # Права панель - вивід
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.output_widget = CompilationOutputWidget(right_frame)
        self.output_widget.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Перевірка доступності .NET
        self.check_dotnet_availability()
    
    def check_dotnet_availability(self):
        """Перевірка доступності .NET"""
        if not self.dotnet_env.is_available():
            self.output_widget.add_output(
                "❌ .NET середовище недоступне. Компіляція неможлива.\n",
                "error"
            )
            self.compile_button.configure(state="disabled")
            self.clean_button.configure(state="disabled")
            self.rebuild_button.configure(state="disabled")
        else:
            self.output_widget.add_output(
                "✅ .NET середовище готове до роботи.\n",
                "success"
            )
    
    def on_project_selected(self, project_path: str):
        """Обробка вибору проєкту"""
        self.current_project = project_path
        self.output_widget.add_output(
            f"📁 Обрано проєкт: {os.path.basename(project_path)}\n",
            "info"
        )
    
    def compile_project(self):
        """Компіляція проєкту"""
        if not self.current_project:
            messagebox.showerror("Помилка", "Оберіть проєкт для компіляції")
            return
        
        if self.compilation_thread and self.compilation_thread.is_alive():
            messagebox.showwarning("Попередження", "Компіляція вже виконується")
            return
        
        settings = self.compilation_settings.get_settings()
        
        # Блокування кнопок
        self.set_buttons_state(False)
        
        self.output_widget.add_output(
            f"🔨 Початок компіляції проєкту: {os.path.basename(self.current_project)}\n",
            "info"
        )
        
        # Запуск компіляції в окремому потоці
        self.compilation_thread = threading.Thread(
            target=self._compile_worker,
            args=(self.current_project, settings),
            daemon=True
        )
        self.compilation_thread.start()
    
    def _compile_worker(self, project_path: str, settings: dict):
        """Робочий потік компіляції"""
        try:
            # Очищення якщо потрібно
            if settings["clean"]:
                self.after(0, lambda: self.output_widget.add_output(
                    "🗑️ Очищення проєкту...\n", "info"
                ))
                self._clean_project_sync(project_path)
            
            # Компіляція
            self.after(0, lambda: self.output_widget.add_output(
                f"⚙️ Конфігурація: {settings['configuration']}, Платформа: {settings['platform']}\n",
                "info"
            ))
            
            success, message = self.compiler.compile_project(
                project_path,
                settings["configuration"]
            )
            
            if success:
                self.after(0, lambda: self.compilation_success(message))
            else:
                self.after(0, lambda: self.compilation_error(message))
                
        except Exception as e:
            self.after(0, lambda: self.compilation_error(f"Виняток: {str(e)}"))
    
    def compilation_success(self, message: str):
        """Успішна компіляція"""
        self.output_widget.add_output(f"✅ {message}\n", "success")
        self.output_widget.add_output("🎉 Компіляція завершена успішно!\n", "success")
        self.set_buttons_state(True)
        
        # Показ результату
        if self.current_project:
            project_dir = os.path.dirname(self.current_project)
            bin_dir = os.path.join(project_dir, "bin")
            if os.path.exists(bin_dir):
                self.output_widget.add_output(f"📁 Результат у папці: {bin_dir}\n", "info")
    
    def compilation_error(self, error: str):
        """Помилка компіляції"""
        self.output_widget.add_output(f"❌ {error}\n", "error")
        self.output_widget.add_output("💥 Компіляція завершена з помилками!\n", "error")
        self.set_buttons_state(True)
    
    def clean_project(self):
        """Очищення проєкту"""
        if not self.current_project:
            messagebox.showerror("Помилка", "Оберіть проєкт для очищення")
            return
        
        self.output_widget.add_output("🗑️ Очищення проєкту...\n", "info")
        
        try:
            self._clean_project_sync(self.current_project)
            self.output_widget.add_output("✅ Проєкт очищено успішно!\n", "success")
        except Exception as e:
            self.output_widget.add_output(f"❌ Помилка очищення: {e}\n", "error")
    
    def _clean_project_sync(self, project_path: str):
        """Синхронне очищення проєкту"""
        project_dir = os.path.dirname(project_path)
        
        # Видалення папок bin та obj
        for folder in ["bin", "obj"]:
            folder_path = os.path.join(project_dir, folder)
            if os.path.exists(folder_path):
                import shutil
                shutil.rmtree(folder_path)
    
    def rebuild_project(self):
        """Перезбірка проєкту"""
        if not self.current_project:
            messagebox.showerror("Помилка", "Оберіть проєкт для перезбірки")
            return
        
        self.output_widget.add_output("🔄 Перезбірка проєкту...\n", "info")
        
        # Спочатку очищення, потім компіляція
        try:
            self._clean_project_sync(self.current_project)
            self.compile_project()
        except Exception as e:
            self.output_widget.add_output(f"❌ Помилка перезбірки: {e}\n", "error")
    
    def set_buttons_state(self, enabled: bool):
        """Встановлення стану кнопок"""
        state = "normal" if enabled else "disabled"
        self.compile_button.configure(state=state)
        self.clean_button.configure(state=state)
        self.rebuild_button.configure(state=state)


if __name__ == "__main__":
    # Тестування віджета компілятора
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("🔨 Компілятор C# - Тест")
    root.geometry("1200x800")
    
    compiler_widget = CSharpCompilerWidget(root)
    compiler_widget.pack(fill="both", expand=True, padx=10, pady=10)
    
    root.mainloop()
