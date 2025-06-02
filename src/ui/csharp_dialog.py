#!/usr/bin/env python3
"""
Діалог для створення C# файлів з шаблонів
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path

class CSharpTemplateDialog:
    """Діалог для створення C# файлів з шаблонів"""
    
    def __init__(self, parent, project_path):
        self.parent = parent
        self.project_path = project_path
        self.result = None
        
        # Створення діалогу
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Створити C# файл")
        self.dialog.geometry("600x500")
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
            text="Створення C# файлу",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Основна форма
        form_frame = ctk.CTkFrame(self.dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Тип шаблону
        ctk.CTkLabel(form_frame, text="Тип класу:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.template_var = ctk.StringVar(value="ThingComp")
        template_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        template_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        templates = [
            ("ThingComp", "Компонент предмета"),
            ("JobDriver", "Драйвер роботи"),
            ("Hediff", "Ефект здоров'я"),
            ("MapComponent", "Компонент карти"),
            ("GameComponent", "Компонент гри"),
            ("DefOf", "Статичні посилання")
        ]
        
        for i, (template_name, description) in enumerate(templates):
            radio = ctk.CTkRadioButton(
                template_frame,
                text=f"{template_name} - {description}",
                variable=self.template_var,
                value=template_name
            )
            radio.pack(anchor="w", pady=2)
        
        # Назва класу
        ctk.CTkLabel(form_frame, text="Назва класу:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(10, 5))
        self.class_name_entry = ctk.CTkEntry(form_frame, placeholder_text="MyCustomClass")
        self.class_name_entry.pack(fill="x", padx=20, pady=(0, 10))
        
        # Namespace
        ctk.CTkLabel(form_frame, text="Namespace:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(0, 5))
        self.namespace_entry = ctk.CTkEntry(form_frame, placeholder_text="MyMod")
        self.namespace_entry.pack(fill="x", padx=20, pady=(0, 10))
        
        # Шлях файлу
        ctk.CTkLabel(form_frame, text="Шлях файлу:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(0, 5))
        
        path_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.file_path_entry = ctk.CTkEntry(path_frame, placeholder_text="Source/MyMod/MyCustomClass.cs")
        self.file_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(path_frame, text="Огляд", command=self.browse_path, width=80)
        browse_btn.pack(side="right")
        
        # Кнопки
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        cancel_btn = ctk.CTkButton(button_frame, text="Скасувати", command=self.dialog.destroy)
        cancel_btn.pack(side="right", padx=(10, 0))
        
        create_btn = ctk.CTkButton(button_frame, text="Створити", command=self.create_file)
        create_btn.pack(side="right")
        
        # Автозаповнення
        self.class_name_entry.bind("<KeyRelease>", self.update_file_path)
        self.namespace_entry.bind("<KeyRelease>", self.update_file_path)
        
        # Початкові значення
        project_name = Path(self.project_path).name
        self.namespace_entry.insert(0, project_name)
        self.class_name_entry.focus()
        
    def browse_path(self):
        """Вибір шляху для файлу"""
        # Простий діалог для введення шляху
        dialog = ctk.CTkInputDialog(
            text="Введіть шлях файлу відносно проєкту:",
            title="Шлях файлу"
        )
        path = dialog.get_input()
        
        if path:
            self.file_path_entry.delete(0, "end")
            self.file_path_entry.insert(0, path)
            
    def update_file_path(self, event=None):
        """Автоматичне оновлення шляху файлу"""
        class_name = self.class_name_entry.get().strip()
        namespace = self.namespace_entry.get().strip()
        
        if class_name and namespace:
            file_path = f"Source/{namespace}/{class_name}.cs"
            
            # Оновлюємо тільки якщо поле порожнє або містить автогенерований шлях
            current_path = self.file_path_entry.get()
            if not current_path or current_path.startswith("Source/"):
                self.file_path_entry.delete(0, "end")
                self.file_path_entry.insert(0, file_path)
                
    def create_file(self):
        """Створення C# файлу"""
        template_name = self.template_var.get()
        class_name = self.class_name_entry.get().strip()
        namespace = self.namespace_entry.get().strip()
        file_path = self.file_path_entry.get().strip()
        
        # Валідація
        if not class_name:
            messagebox.showerror("Помилка", "Введіть назву класу")
            return
            
        if not namespace:
            messagebox.showerror("Помилка", "Введіть namespace")
            return
            
        if not file_path:
            messagebox.showerror("Помилка", "Введіть шлях файлу")
            return
            
        # Перевірка валідності назви класу
        if not class_name.isidentifier():
            messagebox.showerror("Помилка", "Назва класу містить недопустимі символи")
            return
            
        # Перевірка валідності namespace
        if not all(part.isidentifier() for part in namespace.split('.')):
            messagebox.showerror("Помилка", "Namespace містить недопустимі символи")
            return
            
        try:
            from src.core.csharp_manager import CSharpManager
            
            csharp_manager = CSharpManager(self.project_path)
            full_file_path = Path(self.project_path) / file_path
            
            # Створення файлу
            csharp_manager.create_csharp_file(
                template_name=template_name,
                class_name=class_name,
                namespace=namespace,
                file_path=full_file_path
            )
            
            self.result = {
                'file_path': full_file_path,
                'class_name': class_name,
                'namespace': namespace,
                'template': template_name
            }
            
            messagebox.showinfo("Успіх", f"C# файл створено:\n{file_path}")
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося створити файл:\n{str(e)}")


def show_csharp_dialog(parent, project_path):
    """Функція для показу діалогу створення C# файлу"""
    dialog = CSharpTemplateDialog(parent, project_path)
    parent.wait_window(dialog.dialog)
    return dialog.result
