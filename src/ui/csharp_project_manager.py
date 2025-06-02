#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Менеджер C# проєктів для RimWorld Mod Builder v1.0.1 Alpha
UI для створення, редагування та компіляції C# модів
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import threading
from typing import Optional, Dict, Any

# Локальні імпорти
try:
    from core.dotnet_integration import get_dotnet_environment, CSharpCompiler, RimWorldModTemplate
    from utils.simple_logger import get_logger_instance
except ImportError as e:
    print(f"Помилка імпорту: {e}")
    # Fallback для тестування
    class MockDotNetEnvironment:
        def is_available(self): return False
        def get_environment_info(self): return {"is_ready": False, "dotnet_path": None}
    
    class MockCSharpCompiler:
        def __init__(self, env): pass
        def create_csharp_project(self, name, path): return path
        def compile_project(self, path, config): return False, "Mock compiler"
    
    class MockRimWorldModTemplate:
        def create_mod_structure(self, name, path, include_cs=True): return path
    
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


class DotNetStatusWidget(ctk.CTkFrame):
    """Віджет статусу .NET середовища"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.dotnet_env = get_dotnet_environment()
        self.logger = get_logger_instance().get_logger()
        
        self.setup_ui()
        self.update_status()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="🔧 Статус .NET середовища",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=(10, 5))
        
        # Статус
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(fill="x", padx=10, pady=5)
        
        # Кнопка оновлення
        self.refresh_button = ctk.CTkButton(
            self,
            text="🔄 Оновити",
            command=self.update_status,
            width=100
        )
        self.refresh_button.pack(pady=5)
    
    def update_status(self):
        """Оновлення статусу"""
        # Очищення попереднього статусу
        for widget in self.status_frame.winfo_children():
            widget.destroy()
        
        try:
            info = self.dotnet_env.get_environment_info()
            
            # Загальний статус
            status_color = "green" if info["is_ready"] else "red"
            status_text = "✅ Готовий" if info["is_ready"] else "❌ Недоступний"
            
            status_label = ctk.CTkLabel(
                self.status_frame,
                text=f"Статус: {status_text}",
                text_color=status_color,
                font=ctk.CTkFont(weight="bold")
            )
            status_label.pack(pady=2)
            
            # Деталі
            details = [
                ("dotnet CLI", "✅" if info["dotnet_available"] else "❌", info["dotnet_path"] or "Не знайдено"),
                ("MSBuild", "✅" if info["msbuild_available"] else "❌", "Доступний" if info["msbuild_available"] else "Не знайдено"),
                ("SDK версії", "📦", ", ".join(info["sdk_versions"]) if info["sdk_versions"] else "Не знайдено"),
                ("Framework", "🏗️", ", ".join(info["framework_versions"]) if info["framework_versions"] else "Не знайдено")
            ]
            
            for name, icon, value in details:
                detail_frame = ctk.CTkFrame(self.status_frame)
                detail_frame.pack(fill="x", padx=5, pady=1)
                
                name_label = ctk.CTkLabel(
                    detail_frame,
                    text=f"{icon} {name}:",
                    width=100,
                    anchor="w"
                )
                name_label.pack(side="left", padx=5)
                
                value_label = ctk.CTkLabel(
                    detail_frame,
                    text=value,
                    anchor="w",
                    font=ctk.CTkFont(size=10)
                )
                value_label.pack(side="left", fill="x", expand=True, padx=5)
            
        except Exception as e:
            error_label = ctk.CTkLabel(
                self.status_frame,
                text=f"❌ Помилка: {str(e)}",
                text_color="red"
            )
            error_label.pack(pady=5)


class CSharpProjectCreator(ctk.CTkFrame):
    """Створювач C# проєктів"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.dotnet_env = get_dotnet_environment()
        self.compiler = CSharpCompiler(self.dotnet_env)
        self.template = RimWorldModTemplate()
        self.logger = get_logger_instance().get_logger()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="🆕 Створення C# проєкту",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=10)
        
        # Форма створення
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Назва проєкту
        name_label = ctk.CTkLabel(form_frame, text="Назва проєкту:")
        name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="MyRimWorldMod")
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Шлях виводу
        path_label = ctk.CTkLabel(form_frame, text="Папка виводу:")
        path_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        path_frame = ctk.CTkFrame(form_frame)
        path_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.path_entry = ctk.CTkEntry(path_frame, placeholder_text="Оберіть папку...")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        browse_button = ctk.CTkButton(
            path_frame,
            text="📁",
            command=self.browse_output_path,
            width=40
        )
        browse_button.pack(side="right", padx=5, pady=5)
        
        # Опції
        options_frame = ctk.CTkFrame(form_frame)
        options_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        self.include_csharp_var = ctk.BooleanVar(value=True)
        csharp_checkbox = ctk.CTkCheckBox(
            options_frame,
            text="Включити C# код",
            variable=self.include_csharp_var
        )
        csharp_checkbox.pack(side="left", padx=5, pady=5)
        
        self.create_full_mod_var = ctk.BooleanVar(value=True)
        full_mod_checkbox = ctk.CTkCheckBox(
            options_frame,
            text="Повна структура мода",
            variable=self.create_full_mod_var
        )
        full_mod_checkbox.pack(side="left", padx=5, pady=5)
        
        # Налаштування сітки
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Кнопки дій
        actions_frame = ctk.CTkFrame(self)
        actions_frame.pack(fill="x", padx=10, pady=10)
        
        self.create_button = ctk.CTkButton(
            actions_frame,
            text="🚀 Створити проєкт",
            command=self.create_project,
            width=150
        )
        self.create_button.pack(side="left", padx=5)
        
        self.template_button = ctk.CTkButton(
            actions_frame,
            text="📋 Шаблони",
            command=self.show_templates,
            width=120
        )
        self.template_button.pack(side="left", padx=5)
        
        # Прогрес
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Готовий до створення проєкту"
        )
        self.progress_label.pack(pady=5)
    
    def browse_output_path(self):
        """Вибір папки виводу"""
        path = filedialog.askdirectory(title="Оберіть папку для проєкту")
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
    
    def create_project(self):
        """Створення проєкту"""
        name = self.name_entry.get().strip()
        output_path = self.path_entry.get().strip()
        
        if not name:
            messagebox.showerror("Помилка", "Введіть назву проєкту")
            return
        
        if not output_path:
            messagebox.showerror("Помилка", "Оберіть папку виводу")
            return
        
        if not os.path.exists(output_path):
            messagebox.showerror("Помилка", "Папка виводу не існує")
            return
        
        # Перевірка .NET середовища
        if self.include_csharp_var.get() and not self.dotnet_env.is_available():
            if not messagebox.askyesno(
                "Попередження", 
                ".NET середовище недоступне. Створити проєкт без C# коду?"
            ):
                return
            self.include_csharp_var.set(False)
        
        # Створення в окремому потоці
        self.create_button.configure(state="disabled")
        self.progress_label.configure(text="🔄 Створення проєкту...")
        
        def create_worker():
            try:
                if self.create_full_mod_var.get():
                    # Повна структура мода
                    project_path = self.template.create_mod_structure(
                        name, 
                        output_path, 
                        include_csharp=self.include_csharp_var.get()
                    )
                else:
                    # Тільки C# проєкт
                    project_path = self.compiler.create_csharp_project(name, output_path)
                
                self.after(0, lambda: self.creation_complete(project_path))
                
            except Exception as e:
                self.after(0, lambda: self.creation_error(str(e)))
        
        thread = threading.Thread(target=create_worker, daemon=True)
        thread.start()
    
    def creation_complete(self, project_path: str):
        """Завершення створення проєкту"""
        self.create_button.configure(state="normal")
        self.progress_label.configure(text="✅ Проєкт створено успішно")
        
        messagebox.showinfo(
            "Успіх", 
            f"Проєкт створено:\n{project_path}\n\nВідкрити папку?"
        )
        
        # Відкриття папки в провіднику
        if messagebox.askyesno("Відкрити папку", "Відкрити папку проєкту?"):
            try:
                os.startfile(project_path)
            except:
                pass
    
    def creation_error(self, error: str):
        """Помилка створення проєкту"""
        self.create_button.configure(state="normal")
        self.progress_label.configure(text="❌ Помилка створення")
        
        messagebox.showerror("Помилка створення", f"Не вдалося створити проєкт:\n{error}")
    
    def show_templates(self):
        """Показ шаблонів"""
        templates_window = ctk.CTkToplevel(self)
        templates_window.title("📋 Шаблони проєктів")
        templates_window.geometry("600x400")
        templates_window.transient(self)
        
        # Список шаблонів
        templates = [
            {
                "name": "Базовий мод",
                "description": "Простий мод з базовою структурою",
                "includes_cs": False
            },
            {
                "name": "Мод з C# кодом",
                "description": "Мод з C# проєктом та Harmony патчами",
                "includes_cs": True
            },
            {
                "name": "Мод з новими предметами",
                "description": "Шаблон для додавання нових предметів",
                "includes_cs": False
            },
            {
                "name": "Мод з новими дослідженнями",
                "description": "Шаблон для додавання досліджень",
                "includes_cs": False
            }
        ]
        
        templates_frame = ctk.CTkScrollableFrame(templates_window, label_text="Доступні шаблони")
        templates_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for template in templates:
            template_frame = ctk.CTkFrame(templates_frame)
            template_frame.pack(fill="x", padx=5, pady=5)
            
            name_label = ctk.CTkLabel(
                template_frame,
                text=template["name"],
                font=ctk.CTkFont(size=14, weight="bold")
            )
            name_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            desc_label = ctk.CTkLabel(
                template_frame,
                text=template["description"],
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            desc_label.pack(anchor="w", padx=10, pady=(0, 5))
            
            use_button = ctk.CTkButton(
                template_frame,
                text="Використати",
                command=lambda t=template: self.use_template(t, templates_window),
                width=100
            )
            use_button.pack(anchor="e", padx=10, pady=(0, 10))
    
    def use_template(self, template: Dict[str, Any], window: ctk.CTkToplevel):
        """Використання шаблону"""
        self.include_csharp_var.set(template["includes_cs"])
        self.create_full_mod_var.set(True)
        window.destroy()
        
        messagebox.showinfo("Шаблон", f"Обрано шаблон: {template['name']}")


class CSharpProjectManager(ctk.CTkFrame):
    """Головний менеджер C# проєктів"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Заголовок
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🔧 Менеджер C# проєктів",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=10)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Створення та управління C# модами для RimWorld",
            font=ctk.CTkFont(size=12)
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Основний контент
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Ліва панель - статус
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="y", padx=(0, 5))
        left_frame.configure(width=300)
        
        self.status_widget = DotNetStatusWidget(left_frame)
        self.status_widget.pack(fill="x", padx=5, pady=5)
        
        # Права панель - створення проєктів
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.project_creator = CSharpProjectCreator(right_frame)
        self.project_creator.pack(fill="both", expand=True, padx=5, pady=5)


if __name__ == "__main__":
    # Тестування менеджера C# проєктів
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("🔧 Менеджер C# проєктів - Тест")
    root.geometry("1000x700")
    
    manager = CSharpProjectManager(root)
    manager.pack(fill="both", expand=True, padx=10, pady=10)
    
    root.mainloop()
