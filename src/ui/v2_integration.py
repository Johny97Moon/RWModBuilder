#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Інтеграція компонентів RimWorld Mod Builder v1.0.1 Alpha
Об'єднання всіх нових функцій Priority 1
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import os
from typing import Optional

# Локальні імпорти
try:
    from ui.dependency_dialog import show_dependency_dialog
    from ui.enhanced_texture_manager import EnhancedTextureManager
    from ui.smart_xml_editor import SmartXMLEditor
    from core.dependency_manager import get_dependency_manager
    from utils.simple_logger import get_logger_instance
except ImportError as e:
    print(f"Помилка імпорту: {e}")
    # Fallback для тестування
    def show_dependency_dialog(parent=None):
        messagebox.showinfo("Заглушка", "Dependency Dialog")
        return None
    
    class EnhancedTextureManager(ctk.CTkFrame):
        def __init__(self, parent, project_path=None, **kwargs):
            super().__init__(parent, **kwargs)
            label = ctk.CTkLabel(self, text="Enhanced Texture Manager (Заглушка)")
            label.pack(pady=20)
    
    class SmartXMLEditor(ctk.CTkFrame):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            label = ctk.CTkLabel(self, text="Smart XML Editor (Заглушка)")
            label.pack(pady=20)
    
    def get_dependency_manager():
        class MockManager:
            def check_all_dependencies(self):
                return {"installed": [], "missing": [], "outdated": [], "optional_missing": [], "errors": []}
        return MockManager()
    
    def get_logger_instance():
        class Logger:
            def get_logger(self): 
                class L:
                    def info(self, m): print(f"INFO: {m}")
                    def error(self, m): print(f"ERROR: {m}")
                    def warning(self, m): print(f"WARNING: {m}")
                return L()
        return Logger()


class V2IntegratedInterface(ctk.CTkFrame):
    """Інтегрований інтерфейс v2.0.1"""
    
    def __init__(self, parent, project_path: Optional[str] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.project_path = project_path
        self.logger = get_logger_instance().get_logger()
        self.dependency_manager = get_dependency_manager()
        
        # Компоненти
        self.texture_manager = None
        self.xml_editor = None
        self.dependency_dialog = None
        
        self.setup_ui()
        self.check_dependencies_on_startup()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Заголовок
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🚀 RimWorld Mod Builder v2.0.1",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=10)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Покращені інструменти для створення модів",
            font=ctk.CTkFont(size=14)
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Панель інструментів v2.0.1
        toolbar_frame = ctk.CTkFrame(self)
        toolbar_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Кнопки нових функцій
        self.dependency_button = ctk.CTkButton(
            toolbar_frame,
            text="🔧 Залежності",
            command=self.show_dependency_manager,
            width=120,
            height=35
        )
        self.dependency_button.pack(side="left", padx=5, pady=5)
        
        self.texture_button = ctk.CTkButton(
            toolbar_frame,
            text="🎨 Текстури+",
            command=self.show_enhanced_texture_manager,
            width=120,
            height=35
        )
        self.texture_button.pack(side="left", padx=5, pady=5)
        
        self.xml_button = ctk.CTkButton(
            toolbar_frame,
            text="📝 Smart XML",
            command=self.show_smart_xml_editor,
            width=120,
            height=35
        )
        self.xml_button.pack(side="left", padx=5, pady=5)
        
        # Статус залежностей
        self.status_frame = ctk.CTkFrame(toolbar_frame)
        self.status_frame.pack(side="right", padx=5, pady=5)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="🔍 Перевірка залежностей...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(padx=10, pady=5)
        
        # Основний контент
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Вкладки для компонентів
        self.tabview = ctk.CTkTabview(self.content_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Вкладка "Огляд"
        self.overview_tab = self.tabview.add("📋 Огляд")
        self.setup_overview_tab()
        
        # Вкладка "Покращений менеджер текстур"
        self.texture_tab = self.tabview.add("🎨 Текстури")
        self.setup_texture_tab()
        
        # Вкладка "Smart XML Editor"
        self.xml_tab = self.tabview.add("📝 XML")
        self.setup_xml_tab()
        
        # Встановлення активної вкладки
        self.tabview.set("📋 Огляд")
    
    def setup_overview_tab(self):
        """Налаштування вкладки огляду"""
        # Інформація про v2.0.1
        info_frame = ctk.CTkScrollableFrame(self.overview_tab, label_text="🚀 Нові функції v2.0.1")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        features = [
            {
                "title": "🔧 Менеджер залежностей",
                "description": "Автоматичне встановлення та перевірка залежностей (psd-tools, cairosvg, imageio)",
                "status": "✅ Готово"
            },
            {
                "title": "🎨 Покращений менеджер текстур",
                "description": "Batch конвертація, drag & drop, zoom/pan, метадані, undo/redo",
                "status": "✅ Готово"
            },
            {
                "title": "📝 Smart XML Editor",
                "description": "Автодоповнення RimWorld тегів, валідація в реальному часі, форматування",
                "status": "✅ Готово"
            },
            {
                "title": "🔍 Глобальний пошук",
                "description": "Пошук по всьому проєкту з фільтрами",
                "status": "🔄 В розробці"
            },
            {
                "title": "📊 Аналітика модів",
                "description": "Статистика, перевірка балансу, граф залежностей",
                "status": "🔄 В розробці"
            },
            {
                "title": "🎮 Інтеграція з RimWorld",
                "description": "Швидке тестування, синхронізація з Workshop",
                "status": "🔄 В розробці"
            }
        ]
        
        for feature in features:
            feature_frame = ctk.CTkFrame(info_frame)
            feature_frame.pack(fill="x", padx=5, pady=5)
            
            title_label = ctk.CTkLabel(
                feature_frame,
                text=feature["title"],
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            title_label.pack(fill="x", padx=10, pady=(10, 5))
            
            desc_label = ctk.CTkLabel(
                feature_frame,
                text=feature["description"],
                font=ctk.CTkFont(size=12),
                anchor="w",
                text_color="gray"
            )
            desc_label.pack(fill="x", padx=10, pady=(0, 5))
            
            status_label = ctk.CTkLabel(
                feature_frame,
                text=feature["status"],
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="e"
            )
            status_label.pack(fill="x", padx=10, pady=(0, 10))
        
        # Швидкі дії
        actions_frame = ctk.CTkFrame(self.overview_tab)
        actions_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        actions_label = ctk.CTkLabel(
            actions_frame,
            text="⚡ Швидкі дії",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        actions_label.pack(pady=10)
        
        buttons_frame = ctk.CTkFrame(actions_frame)
        buttons_frame.pack(pady=(0, 10))
        
        quick_check_button = ctk.CTkButton(
            buttons_frame,
            text="🔍 Перевірити залежності",
            command=self.quick_dependency_check,
            width=180
        )
        quick_check_button.pack(side="left", padx=5, pady=5)
        
        quick_install_button = ctk.CTkButton(
            buttons_frame,
            text="📦 Встановити все",
            command=self.quick_install_all,
            width=150
        )
        quick_install_button.pack(side="left", padx=5, pady=5)
        
        help_button = ctk.CTkButton(
            buttons_frame,
            text="❓ Довідка",
            command=self.show_help,
            width=100
        )
        help_button.pack(side="left", padx=5, pady=5)
    
    def setup_texture_tab(self):
        """Налаштування вкладки текстур"""
        if self.project_path:
            self.texture_manager = EnhancedTextureManager(
                self.texture_tab,
                project_path=self.project_path
            )
            self.texture_manager.pack(fill="both", expand=True)
        else:
            placeholder_label = ctk.CTkLabel(
                self.texture_tab,
                text="📁 Відкрийте проєкт для використання менеджера текстур",
                font=ctk.CTkFont(size=16)
            )
            placeholder_label.pack(expand=True)
    
    def setup_xml_tab(self):
        """Налаштування вкладки XML"""
        self.xml_editor = SmartXMLEditor(self.xml_tab)
        self.xml_editor.pack(fill="both", expand=True)
    
    def check_dependencies_on_startup(self):
        """Перевірка залежностей при запуску"""
        def check_worker():
            try:
                status = self.dependency_manager.check_all_dependencies()
                
                # Підрахунок статистики
                total = sum(len(status[key]) for key in ["installed", "missing", "outdated", "optional_missing"])
                installed = len(status["installed"])
                missing = len(status["missing"])
                
                # Оновлення UI в головному потоці
                if missing > 0:
                    status_text = f"❌ {missing} залежностей відсутні"
                    self.after(0, lambda: self.status_label.configure(text=status_text, text_color="red"))
                elif installed == total:
                    status_text = f"✅ Всі залежності встановлені ({installed})"
                    self.after(0, lambda: self.status_label.configure(text=status_text, text_color="green"))
                else:
                    status_text = f"⚠️ {installed}/{total} залежностей"
                    self.after(0, lambda: self.status_label.configure(text=status_text, text_color="orange"))
                
            except Exception as e:
                self.logger.error(f"Помилка перевірки залежностей: {e}")
                self.after(0, lambda: self.status_label.configure(text="❌ Помилка перевірки", text_color="red"))
        
        # Запуск в окремому потоці
        import threading
        thread = threading.Thread(target=check_worker, daemon=True)
        thread.start()
    
    def show_dependency_manager(self):
        """Показ менеджера залежностей"""
        try:
            self.dependency_dialog = show_dependency_dialog(self)
        except Exception as e:
            self.logger.error(f"Помилка відкриття менеджера залежностей: {e}")
            messagebox.showerror("Помилка", f"Не вдалося відкрити менеджер залежностей: {e}")
    
    def show_enhanced_texture_manager(self):
        """Показ покращеного менеджера текстур"""
        self.tabview.set("🎨 Текстури")
    
    def show_smart_xml_editor(self):
        """Показ Smart XML Editor"""
        self.tabview.set("📝 XML")
    
    def quick_dependency_check(self):
        """Швидка перевірка залежностей"""
        self.check_dependencies_on_startup()
        messagebox.showinfo("Перевірка залежностей", "Перевірка залежностей запущена. Дивіться статус в правому верхньому куті.")
    
    def quick_install_all(self):
        """Швидке встановлення всіх залежностей"""
        if messagebox.askyesno("Встановлення", "Встановити всі відсутні залежності (включно з опціональними)?"):
            try:
                def install_callback(results):
                    if results.get("success", False):
                        installed = len(results.get("installed", []))
                        messagebox.showinfo("Успіх", f"Успішно встановлено {installed} залежностей")
                        self.check_dependencies_on_startup()
                    else:
                        failed = len(results.get("failed", []))
                        messagebox.showerror("Помилка", f"Не вдалося встановити {failed} залежностей")
                
                self.dependency_manager.add_installation_callback(install_callback)
                self.dependency_manager.install_async(include_optional=True)
                
            except Exception as e:
                self.logger.error(f"Помилка встановлення: {e}")
                messagebox.showerror("Помилка", f"Не вдалося запустити встановлення: {e}")
    
    def show_help(self):
        """Показ довідки"""
        help_text = """
🚀 RimWorld Mod Builder v2.0.1 - Довідка

🔧 Менеджер залежностей:
- Автоматична перевірка та встановлення бібліотек
- Підтримка psd-tools, cairosvg, imageio та інших
- Інтелектуальні рекомендації

🎨 Покращений менеджер текстур:
- Drag & Drop підтримка
- Batch конвертація форматів
- Zoom/Pan попередній перегляд
- Метадані зображень
- Undo/Redo операції

📝 Smart XML Editor:
- Автодоповнення RimWorld тегів
- Валідація в реальному часі
- Автоматичне форматування
- Підсвітка синтаксису

⌨️ Горячі клавіші:
- Ctrl+Space: Автодоповнення
- Ctrl+S: Зберегти
- F5: Валідувати XML
- Ctrl+Shift+F: Форматувати XML

💡 Поради:
- Регулярно перевіряйте залежності
- Використовуйте автодоповнення для швидшого кодування
- Зберігайте резервні копії проєктів
        """
        
        messagebox.showinfo("Довідка v2.0.1", help_text)
    
    def set_project_path(self, project_path: str):
        """Встановлення шляху проєкту"""
        self.project_path = project_path
        
        # Оновлення менеджера текстур
        if hasattr(self, 'texture_tab'):
            # Очищення старого контенту
            for widget in self.texture_tab.winfo_children():
                widget.destroy()
            
            # Створення нового менеджера
            self.setup_texture_tab()
        
        self.logger.info(f"Проєкт встановлено: {project_path}")


def create_v2_interface(parent, project_path: Optional[str] = None) -> V2IntegratedInterface:
    """Створення інтегрованого інтерфейсу v2.0.1"""
    return V2IntegratedInterface(parent, project_path=project_path)


if __name__ == "__main__":
    # Тестування інтегрованого інтерфейсу
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("RimWorld Mod Builder v2.0.1 - Тест")
    root.geometry("1400x900")
    
    interface = create_v2_interface(root, project_path="./test_project")
    interface.pack(fill="both", expand=True, padx=10, pady=10)
    
    root.mainloop()
