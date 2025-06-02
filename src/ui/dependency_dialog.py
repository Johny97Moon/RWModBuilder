#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Діалог управління залежностями для RimWorld Mod Builder v2.0.1
CustomTkinter інтерфейс для DependencyManager
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
from typing import Dict, List, Optional, Callable

# Локальні імпорти
try:
    from core.dependency_manager import get_dependency_manager
    from utils.simple_logger import get_logger_instance
except ImportError as e:
    print(f"Помилка імпорту: {e}")
    # Fallback для тестування
    class MockDependencyManager:
        def check_all_dependencies(self):
            return {"installed": [], "missing": [], "outdated": [], "optional_missing": [], "errors": []}
        def get_installation_suggestions(self):
            return []
        def install_missing_dependencies(self, include_optional=False, progress_callback=None):
            return {"success": True, "installed": [], "failed": []}
    
    def get_dependency_manager():
        return MockDependencyManager()
    
    def get_logger_instance():
        class Logger:
            def get_logger(self): 
                class L:
                    def info(self, m): print(f"INFO: {m}")
                    def error(self, m): print(f"ERROR: {m}")
                    def warning(self, m): print(f"WARNING: {m}")
                return L()
        return Logger()


class DependencyStatusWidget(ctk.CTkFrame):
    """Віджет відображення статусу залежності"""
    
    def __init__(self, parent, dependency_info: Dict, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.dependency_info = dependency_info
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування інтерфейсу віджета"""
        # Іконка статусу
        status_color = self._get_status_color()
        status_text = self._get_status_text()
        
        self.status_label = ctk.CTkLabel(
            self, 
            text=status_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=status_color,
            width=30
        )
        self.status_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Назва залежності
        self.name_label = ctk.CTkLabel(
            self,
            text=self.dependency_info.get("name", "Невідома"),
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.name_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Версія
        version_text = self._get_version_text()
        self.version_label = ctk.CTkLabel(
            self,
            text=version_text,
            font=ctk.CTkFont(size=12)
        )
        self.version_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Опис
        description = self.dependency_info.get("description", "")
        if description:
            self.desc_label = ctk.CTkLabel(
                self,
                text=description,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            self.desc_label.grid(row=1, column=1, columnspan=2, padx=5, pady=(0, 5), sticky="w")
        
        # Кнопка дії (якщо потрібна)
        if self._needs_action():
            self.action_button = ctk.CTkButton(
                self,
                text=self._get_action_text(),
                command=self._perform_action,
                width=100,
                height=25
            )
            self.action_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")
    
    def _get_status_color(self) -> str:
        """Отримання кольору статусу"""
        if "version" in self.dependency_info:
            if self.dependency_info.get("version_ok", True):
                return "green"
            else:
                return "orange"
        else:
            return "red"
    
    def _get_status_text(self) -> str:
        """Отримання тексту статусу"""
        if "version" in self.dependency_info:
            if self.dependency_info.get("version_ok", True):
                return "✅"
            else:
                return "⚠️"
        else:
            return "❌"
    
    def _get_version_text(self) -> str:
        """Отримання тексту версії"""
        version = self.dependency_info.get("version")
        required = self.dependency_info.get("required")
        
        if version and required:
            return f"v{version} (потрібно {required})"
        elif required:
            return f"Не встановлено (потрібно {required})"
        else:
            return "Версія невідома"
    
    def _needs_action(self) -> bool:
        """Чи потрібна кнопка дії"""
        return "install_command" in self.dependency_info
    
    def _get_action_text(self) -> str:
        """Текст кнопки дії"""
        if "version" in self.dependency_info:
            return "Оновити"
        else:
            return "Встановити"
    
    def _perform_action(self):
        """Виконання дії"""
        # Тут буде логіка встановлення/оновлення
        messagebox.showinfo("Дія", f"Встановлення {self.dependency_info['name']}...")


class DependencyDialog(ctk.CTkToplevel):
    """Діалог управління залежностями"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.dependency_manager = get_dependency_manager()
        self.logger = get_logger_instance().get_logger()
        
        self.title("🔧 Управління залежностями - RimWorld Mod Builder")
        self.geometry("800x600")
        self.minsize(600, 400)
        
        # Центрування вікна
        if parent:
            self.transient(parent)
            self.grab_set()
        
        self.setup_ui()
        self.refresh_dependencies()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Заголовок
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(fill="x", padx=10, pady=10)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🔧 Управління залежностями",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=10)
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Перевірка та встановлення необхідних бібліотек",
            font=ctk.CTkFont(size=14)
        )
        self.subtitle_label.pack(pady=(0, 10))
        
        # Кнопки дій
        self.actions_frame = ctk.CTkFrame(self)
        self.actions_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.refresh_button = ctk.CTkButton(
            self.actions_frame,
            text="🔄 Оновити",
            command=self.refresh_dependencies,
            width=120
        )
        self.refresh_button.pack(side="left", padx=5, pady=5)
        
        self.install_critical_button = ctk.CTkButton(
            self.actions_frame,
            text="📦 Встановити обов'язкові",
            command=self.install_critical,
            width=180
        )
        self.install_critical_button.pack(side="left", padx=5, pady=5)
        
        self.install_all_button = ctk.CTkButton(
            self.actions_frame,
            text="🎯 Встановити все",
            command=self.install_all,
            width=140
        )
        self.install_all_button.pack(side="left", padx=5, pady=5)
        
        # Прогрес бар
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Готовий до роботи",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.set(0)
        
        # Основний контент
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Скролюваний фрейм для залежностей
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            label_text="📋 Статус залежностей"
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Статистика
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text="📊 Завантаження статистики...",
            font=ctk.CTkFont(size=12)
        )
        self.stats_label.pack(pady=5)
    
    def refresh_dependencies(self):
        """Оновлення списку залежностей"""
        self.progress_label.configure(text="🔍 Перевірка залежностей...")
        self.progress_bar.set(0.3)
        
        # Очищення попереднього контенту
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        def check_worker():
            try:
                # Перевірка залежностей
                status = self.dependency_manager.check_all_dependencies()
                
                # Оновлення UI в головному потоці
                self.after(0, lambda: self._update_dependencies_ui(status))
                
            except Exception as e:
                self.logger.error(f"Помилка перевірки залежностей: {e}")
                self.after(0, lambda: self._show_error(f"Помилка перевірки: {e}"))
        
        # Запуск в окремому потоці
        thread = threading.Thread(target=check_worker, daemon=True)
        thread.start()
    
    def _update_dependencies_ui(self, status: Dict):
        """Оновлення UI зі статусом залежностей"""
        try:
            # Встановлені залежності
            if status["installed"]:
                installed_label = ctk.CTkLabel(
                    self.scrollable_frame,
                    text="✅ Встановлені залежності",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="green"
                )
                installed_label.pack(anchor="w", padx=5, pady=(10, 5))
                
                for dep in status["installed"]:
                    widget = DependencyStatusWidget(self.scrollable_frame, dep)
                    widget.pack(fill="x", padx=5, pady=2)
            
            # Відсутні залежності
            if status["missing"]:
                missing_label = ctk.CTkLabel(
                    self.scrollable_frame,
                    text="❌ Відсутні залежності",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="red"
                )
                missing_label.pack(anchor="w", padx=5, pady=(10, 5))
                
                for dep in status["missing"]:
                    widget = DependencyStatusWidget(self.scrollable_frame, dep)
                    widget.pack(fill="x", padx=5, pady=2)
            
            # Застарілі залежності
            if status["outdated"]:
                outdated_label = ctk.CTkLabel(
                    self.scrollable_frame,
                    text="⚠️ Застарілі залежності",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="orange"
                )
                outdated_label.pack(anchor="w", padx=5, pady=(10, 5))
                
                for dep in status["outdated"]:
                    widget = DependencyStatusWidget(self.scrollable_frame, dep)
                    widget.pack(fill="x", padx=5, pady=2)
            
            # Опціональні залежності
            if status["optional_missing"]:
                optional_label = ctk.CTkLabel(
                    self.scrollable_frame,
                    text="🔧 Опціональні залежності",
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="blue"
                )
                optional_label.pack(anchor="w", padx=5, pady=(10, 5))
                
                for dep in status["optional_missing"]:
                    widget = DependencyStatusWidget(self.scrollable_frame, dep)
                    widget.pack(fill="x", padx=5, pady=2)
            
            # Оновлення статистики
            self._update_stats(status)
            
            # Завершення
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="✅ Перевірка завершена")
            
        except Exception as e:
            self.logger.error(f"Помилка оновлення UI: {e}")
            self._show_error(f"Помилка оновлення інтерфейсу: {e}")
    
    def _update_stats(self, status: Dict):
        """Оновлення статистики"""
        total = sum(len(status[key]) for key in status.keys())
        installed = len(status["installed"])
        missing = len(status["missing"])
        outdated = len(status["outdated"])
        optional = len(status["optional_missing"])
        
        stats_text = f"📊 Статистика: {installed} встановлено, {missing} відсутні, {outdated} застарілі, {optional} опціональні"
        self.stats_label.configure(text=stats_text)
    
    def _show_error(self, message: str):
        """Показ помилки"""
        self.progress_label.configure(text=f"❌ {message}")
        self.progress_bar.set(0)
        messagebox.showerror("Помилка", message)
    
    def install_critical(self):
        """Встановлення критичних залежностей"""
        self._install_dependencies(include_optional=False)
    
    def install_all(self):
        """Встановлення всіх залежностей"""
        self._install_dependencies(include_optional=True)
    
    def _install_dependencies(self, include_optional: bool = False):
        """Встановлення залежностей"""
        def progress_callback(progress: float, message: str):
            self.after(0, lambda: self._update_progress(progress, message))
        
        def install_worker():
            try:
                results = self.dependency_manager.install_missing_dependencies(
                    include_optional=include_optional,
                    progress_callback=progress_callback
                )
                
                self.after(0, lambda: self._installation_complete(results))
                
            except Exception as e:
                self.logger.error(f"Помилка встановлення: {e}")
                self.after(0, lambda: self._show_error(f"Помилка встановлення: {e}"))
        
        # Підтвердження
        action = "всіх" if include_optional else "обов'язкових"
        if messagebox.askyesno("Підтвердження", f"Встановити {action} залежності?"):
            thread = threading.Thread(target=install_worker, daemon=True)
            thread.start()
    
    def _update_progress(self, progress: float, message: str):
        """Оновлення прогресу"""
        self.progress_bar.set(progress / 100.0)
        self.progress_label.configure(text=message)
    
    def _installation_complete(self, results: Dict):
        """Завершення встановлення"""
        if results["success"]:
            installed = len(results["installed"])
            message = f"✅ Успішно встановлено {installed} залежностей"
            self.progress_label.configure(text=message)
            messagebox.showinfo("Успіх", message)
        else:
            failed = len(results["failed"])
            message = f"❌ Не вдалося встановити {failed} залежностей"
            self.progress_label.configure(text=message)
            messagebox.showerror("Помилка", message)
        
        # Оновлення списку
        self.refresh_dependencies()


def show_dependency_dialog(parent=None):
    """Показ діалогу залежностей"""
    dialog = DependencyDialog(parent)
    return dialog


if __name__ == "__main__":
    # Тестування діалогу
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.withdraw()  # Сховати головне вікно
    
    dialog = show_dependency_dialog()
    
    root.mainloop()
