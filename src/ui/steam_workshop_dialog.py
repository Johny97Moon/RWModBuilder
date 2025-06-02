#!/usr/bin/env python3
"""
Діалог для підготовки мода до Steam Workshop
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading

class SteamWorkshopDialog:
    """Діалог для роботи з Steam Workshop"""
    
    def __init__(self, parent, project_path):
        self.parent = parent
        self.project_path = project_path
        self.result = None
        
        # Створення діалогу
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Steam Workshop")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Центрування діалогу
        self.dialog.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")
        
        self.setup_dialog()
        
    def setup_dialog(self):
        """Налаштування діалогу"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self.dialog,
            text="Підготовка до Steam Workshop",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Основна область
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Вкладки
        self.setup_tabs(main_frame)
        
    def setup_tabs(self, parent):
        """Налаштування вкладок"""
        # Створення вкладок
        self.tabview = ctk.CTkTabview(parent)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Вкладка підготовки
        self.setup_prepare_tab()
        
        # Вкладка валідації
        self.setup_validation_tab()
        
        # Вкладка рекомендацій
        self.setup_guidelines_tab()
        
    def setup_prepare_tab(self):
        """Вкладка підготовки мода"""
        prepare_tab = self.tabview.add("Підготовка")
        
        # Опис
        desc_label = ctk.CTkLabel(
            prepare_tab,
            text="Підготуйте ваш мод для публікації в Steam Workshop",
            font=ctk.CTkFont(size=14)
        )
        desc_label.pack(pady=10)
        
        # Опції експорту
        options_frame = ctk.CTkFrame(prepare_tab)
        options_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            options_frame,
            text="Опції експорту:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Чекбокси
        self.create_preview_var = ctk.BooleanVar(value=True)
        preview_check = ctk.CTkCheckBox(
            options_frame,
            text="Створити Preview.png (якщо відсутній)",
            variable=self.create_preview_var
        )
        preview_check.pack(anchor="w", padx=20, pady=2)
        
        self.validate_mod_var = ctk.BooleanVar(value=True)
        validate_check = ctk.CTkCheckBox(
            options_frame,
            text="Валідувати мод перед експортом",
            variable=self.validate_mod_var
        )
        validate_check.pack(anchor="w", padx=20, pady=2)
        
        self.optimize_images_var = ctk.BooleanVar(value=False)
        optimize_check = ctk.CTkCheckBox(
            options_frame,
            text="Оптимізувати зображення",
            variable=self.optimize_images_var
        )
        optimize_check.pack(anchor="w", padx=20, pady=(2, 10))
        
        # Шлях експорту
        path_frame = ctk.CTkFrame(prepare_tab)
        path_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            path_frame,
            text="Папка для експорту:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        path_input_frame = ctk.CTkFrame(path_frame, fg_color="transparent")
        path_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.export_path_entry = ctk.CTkEntry(
            path_input_frame,
            placeholder_text="Виберіть папку для експорту..."
        )
        self.export_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            path_input_frame,
            text="Огляд",
            command=self.browse_export_path,
            width=80
        )
        browse_btn.pack(side="right")
        
        # Кнопки дій
        actions_frame = ctk.CTkFrame(prepare_tab)
        actions_frame.pack(fill="x", padx=10, pady=10)
        
        # Підготовка для Workshop
        workshop_btn = ctk.CTkButton(
            actions_frame,
            text="🚀 Підготувати для Workshop",
            command=self.prepare_for_workshop,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        workshop_btn.pack(fill="x", padx=10, pady=10)
        
        # Локальне тестування
        local_btn = ctk.CTkButton(
            actions_frame,
            text="📁 Експорт для локального тестування",
            command=self.export_for_local_testing,
            height=35
        )
        local_btn.pack(fill="x", padx=10, pady=(0, 10))
        
        # Прогрес
        self.progress_label = ctk.CTkLabel(prepare_tab, text="")
        self.progress_label.pack(pady=5)
        
    def setup_validation_tab(self):
        """Вкладка валідації"""
        validation_tab = self.tabview.add("Валідація")
        
        # Опис
        desc_label = ctk.CTkLabel(
            validation_tab,
            text="Перевірка мода на відповідність вимогам Steam Workshop",
            font=ctk.CTkFont(size=14)
        )
        desc_label.pack(pady=10)
        
        # Кнопка валідації
        validate_btn = ctk.CTkButton(
            validation_tab,
            text="🔍 Перевірити мод",
            command=self.validate_mod,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        validate_btn.pack(pady=10)
        
        # Результати валідації
        self.validation_results = ctk.CTkTextbox(validation_tab)
        self.validation_results.pack(fill="both", expand=True, padx=10, pady=10)
        
    def setup_guidelines_tab(self):
        """Вкладка рекомендацій"""
        guidelines_tab = self.tabview.add("Рекомендації")
        
        # Рекомендації
        guidelines_text = """Steam Workshop рекомендації:

🖼️ Preview зображення:
• Мінімальний розмір: 512x512 пікселів
• Рекомендований розмір: 1024x1024 пікселів
• Формат: PNG або JPG
• Показуйте ключові особливості мода

📝 Опис мода:
• Використовуйте зрозумілу мову
• Опишіть що робить мод
• Вкажіть інструкції з встановлення
• Використовуйте BBCode для форматування

🏷️ Теги:
• Максимум 5 релевантних тегів
• Приклади: Gameplay, Items, Buildings, Quality of Life

🔧 Сумісність:
• Вказуйте підтримувані версії RimWorld
• Згадуйте сумісність з іншими модами
• Попереджайте про можливі конфлікти

📋 Обов'язкові файли:
• About/About.xml з усіма полями
• Preview.png
• Правильний packageId (author.modname)

⚠️ Уникайте:
• Копірайт контенту
• Неприйнятного контенту
• Модів що ламають гру
• Дублювання існуючих модів"""

        guidelines_textbox = ctk.CTkTextbox(guidelines_tab)
        guidelines_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        guidelines_textbox.insert("1.0", guidelines_text)
        guidelines_textbox.configure(state="disabled")
        
    def browse_export_path(self):
        """Вибір папки для експорту"""
        folder = filedialog.askdirectory(
            title="Виберіть папку для експорту",
            initialdir=str(Path(self.project_path).parent)
        )
        
        if folder:
            self.export_path_entry.delete(0, "end")
            self.export_path_entry.insert(0, folder)
            
    def prepare_for_workshop(self):
        """Підготовка мода для Steam Workshop"""
        export_path = self.export_path_entry.get().strip()
        if not export_path:
            export_path = str(Path(self.project_path).parent / f"{Path(self.project_path).name}_Workshop")
            
        self.progress_label.configure(text="Підготовка мода...")
        
        # Запуск в окремому потоці
        thread = threading.Thread(
            target=self._prepare_workshop_thread,
            args=(export_path,)
        )
        thread.daemon = True
        thread.start()
        
    def _prepare_workshop_thread(self, export_path):
        """Підготовка в окремому потоці"""
        try:
            from src.core.steam_workshop import SteamWorkshopManager
            
            workshop_manager = SteamWorkshopManager(self.project_path)
            result = workshop_manager.prepare_for_workshop(export_path)
            
            # Оновлення UI в головному потоці
            self.dialog.after(0, self._on_workshop_prepared, result)
            
        except Exception as e:
            self.dialog.after(0, self._on_workshop_error, str(e))
            
    def _on_workshop_prepared(self, result):
        """Обробка результату підготовки"""
        if result['success']:
            self.progress_label.configure(text="✅ Мод підготовлено для Workshop!")
            
            # Показ результатів валідації
            validation = result.get('validation', {})
            if validation:
                self._show_validation_results(validation)
                
            messagebox.showinfo(
                "Успіх",
                f"Мод підготовлено для Steam Workshop!\n\nПапка: {result['output_path']}"
            )
        else:
            self.progress_label.configure(text="❌ Помилка підготовки")
            messagebox.showerror("Помилка", f"Не вдалося підготувати мод:\n{result['error']}")
            
    def _on_workshop_error(self, error):
        """Обробка помилки підготовки"""
        self.progress_label.configure(text="❌ Помилка підготовки")
        messagebox.showerror("Помилка", f"Помилка підготовки мода:\n{error}")
        
    def export_for_local_testing(self):
        """Експорт для локального тестування"""
        # Автоматичний пошук папки RimWorld
        try:
            from src.core.steam_workshop import SteamWorkshopManager
            workshop_manager = SteamWorkshopManager(self.project_path)
            rimworld_path = workshop_manager.detect_rimworld_path()
            
            if rimworld_path:
                mods_path = rimworld_path / "Mods"
                if mods_path.exists():
                    result = workshop_manager.export_for_local_testing(mods_path)
                    if result['success']:
                        messagebox.showinfo("Успіх", result['message'])
                    else:
                        messagebox.showerror("Помилка", result['error'])
                    return
                    
        except Exception as e:
            pass
            
        # Ручний вибір папки
        folder = filedialog.askdirectory(
            title="Виберіть папку Mods RimWorld",
            initialdir=str(Path.home())
        )
        
        if folder:
            try:
                from src.core.steam_workshop import SteamWorkshopManager
                workshop_manager = SteamWorkshopManager(self.project_path)
                result = workshop_manager.export_for_local_testing(folder)
                
                if result['success']:
                    messagebox.showinfo("Успіх", result['message'])
                else:
                    messagebox.showerror("Помилка", result['error'])
                    
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося експортувати мод:\n{str(e)}")
                
    def validate_mod(self):
        """Валідація мода"""
        try:
            from src.core.steam_workshop import SteamWorkshopManager
            
            workshop_manager = SteamWorkshopManager(self.project_path)
            validation = workshop_manager._validate_for_workshop(self.project_path)
            
            self._show_validation_results(validation)
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося валідувати мод:\n{str(e)}")
            
    def _show_validation_results(self, validation):
        """Показ результатів валідації"""
        self.validation_results.delete("1.0", "end")
        
        if validation['valid']:
            self.validation_results.insert("1.0", "✅ Мод готовий для Steam Workshop!\n\n")
        else:
            self.validation_results.insert("1.0", "❌ Знайдено проблеми:\n\n")
            
        if validation['issues']:
            self.validation_results.insert("end", "🚨 Критичні проблеми:\n")
            for issue in validation['issues']:
                self.validation_results.insert("end", f"  • {issue}\n")
            self.validation_results.insert("end", "\n")
            
        if validation['warnings']:
            self.validation_results.insert("end", "⚠️ Попередження:\n")
            for warning in validation['warnings']:
                self.validation_results.insert("end", f"  • {warning}\n")
            self.validation_results.insert("end", "\n")
            
        if validation['valid'] and not validation['warnings']:
            self.validation_results.insert("end", "Всі перевірки пройдено успішно!")


def show_steam_workshop_dialog(parent, project_path):
    """Функція для показу діалогу Steam Workshop"""
    dialog = SteamWorkshopDialog(parent, project_path)
    parent.wait_window(dialog.dialog)
    return dialog.result
