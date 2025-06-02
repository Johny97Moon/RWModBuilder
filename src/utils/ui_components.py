#!/usr/bin/env python3
"""
Утилітні UI компоненти для уникнення дублювання коду
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import Optional, Callable, Dict, Any


class BaseDialog:
    """Базовий клас для діалогових вікон"""
    
    def __init__(self, parent, title: str, size: str = "600x500"):
        self.parent = parent
        self.result = None
        
        # Створення діалогу
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(size)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Центрування діалогу
        self._center_dialog()
        
        # Обробка закриття
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
    def _center_dialog(self):
        """Центрування діалогу відносно батьківського вікна"""
        self.dialog.geometry(f"+{self.parent.winfo_x() + 50}+{self.parent.winfo_y() + 50}")
    
    def create_header(self, text: str, font_size: int = 20) -> ctk.CTkLabel:
        """Створення заголовка діалогу"""
        header_label = ctk.CTkLabel(
            self.dialog,
            text=text,
            font=ctk.CTkFont(size=font_size, weight="bold")
        )
        header_label.pack(pady=20)
        return header_label
    
    def create_form_frame(self) -> ctk.CTkFrame:
        """Створення основної форми"""
        form_frame = ctk.CTkFrame(self.dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        return form_frame
    
    def create_button_frame(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        """Створення панелі кнопок"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        return button_frame
    
    def add_cancel_button(self, parent: ctk.CTkFrame) -> ctk.CTkButton:
        """Додавання кнопки скасування"""
        cancel_btn = ctk.CTkButton(
            parent, 
            text="Скасувати", 
            command=self.on_cancel
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        return cancel_btn
    
    def add_ok_button(self, parent: ctk.CTkFrame, text: str = "OK", command: Optional[Callable] = None) -> ctk.CTkButton:
        """Додавання кнопки OK"""
        ok_btn = ctk.CTkButton(
            parent, 
            text=text, 
            command=command or self.on_ok
        )
        ok_btn.pack(side="right")
        return ok_btn
    
    def on_cancel(self):
        """Обробка скасування"""
        self.result = None
        self.dialog.destroy()
    
    def on_ok(self):
        """Обробка підтвердження (переозначити в підкласах)"""
        self.dialog.destroy()
    
    def show(self):
        """Показ діалогу та очікування результату"""
        self.dialog.wait_window()
        return self.result


class ScrollableTextEditor:
    """Текстовий редактор з CustomTkinter повзунками та підсвічуванням синтаксису"""

    @staticmethod
    def create(parent, **kwargs) -> tuple[tk.Text, ctk.CTkFrame]:
        """
        Створення текстового редактора з CustomTkinter повзунками

        Returns:
            tuple: (text_widget, container_frame)
        """
        # Налаштування за замовчуванням
        defaults = {
            "font": ("Consolas", 11),
            "bg": "#1e1e1e",
            "fg": "#d4d4d4",
            "insertbackground": "white",
            "selectbackground": "#264f78",
            "selectforeground": "white",
            "tabs": "    ",  # 4 пробіли для табуляції
            "undo": True,
            "maxundo": 50,
            "wrap": tk.NONE  # Для горизонтального повзунка
        }
        defaults.update(kwargs)

        # Контейнер для редактора з повзунками (CustomTkinter Frame)
        container = ctk.CTkFrame(parent)

        # Текстовий редактор
        text_widget = tk.Text(container, **defaults)

        # CustomTkinter повзунки (такі ж як у "Файли проєкту")
        v_scrollbar = ctk.CTkScrollbar(container, command=text_widget.yview)
        text_widget.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ctk.CTkScrollbar(container, command=text_widget.xview, orientation="horizontal")
        text_widget.configure(xscrollcommand=h_scrollbar.set)

        # Розміщення елементів
        text_widget.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Налаштування розтягування
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        return text_widget, container


class FormField:
    """Утилітний клас для створення полів форми"""
    
    @staticmethod
    def create_text_field(parent: ctk.CTkFrame, label: str, placeholder: str = "", **kwargs) -> ctk.CTkEntry:
        """Створення текстового поля з підписом"""
        # Підпис
        ctk.CTkLabel(
            parent, 
            text=label, 
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        # Поле вводу
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, **kwargs)
        entry.pack(fill="x", padx=20, pady=(0, 10))
        
        return entry
    
    @staticmethod
    def create_path_browser(parent: ctk.CTkFrame, label: str, placeholder: str = "Виберіть папку", 
                           browse_command: Optional[Callable] = None) -> tuple[ctk.CTkEntry, ctk.CTkButton]:
        """Створення поля з кнопкою огляду"""
        # Підпис
        ctk.CTkLabel(
            parent, 
            text=label, 
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        # Контейнер для поля та кнопки
        path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        path_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Поле вводу
        entry = ctk.CTkEntry(path_frame, placeholder_text=placeholder)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Кнопка огляду
        browse_btn = ctk.CTkButton(
            path_frame, 
            text="Огляд", 
            command=browse_command,
            width=80
        )
        browse_btn.pack(side="right")
        
        return entry, browse_btn
    
    @staticmethod
    def create_radio_group(parent: ctk.CTkFrame, label: str, options: list, 
                          default_value: str = None) -> tuple[ctk.StringVar, list]:
        """Створення групи радіо кнопок"""
        # Підпис
        ctk.CTkLabel(
            parent, 
            text=label, 
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        # Змінна для зберігання вибору
        var = ctk.StringVar(value=default_value or options[0][0] if options else "")
        
        # Контейнер для радіо кнопок
        radio_frame = ctk.CTkFrame(parent, fg_color="transparent")
        radio_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # Створення радіо кнопок
        radio_buttons = []
        for value, text in options:
            radio_btn = ctk.CTkRadioButton(
                radio_frame,
                text=text,
                variable=var,
                value=value
            )
            radio_btn.pack(anchor="w", padx=10, pady=2)
            radio_buttons.append(radio_btn)
        
        return var, radio_buttons


class ValidationUtils:
    """Утиліти для валідації"""
    
    @staticmethod
    def create_result_dict() -> Dict[str, Any]:
        """Створення стандартного словника результатів валідації"""
        return {
            "valid": True,
            "errors": [],
            "warnings": []
        }
    
    @staticmethod
    def validate_required_field(value: str, field_name: str) -> Optional[str]:
        """Валідація обов'язкового поля"""
        if not value or not value.strip():
            return f"Поле '{field_name}' є обов'язковим"
        return None
    
    @staticmethod
    def validate_identifier(value: str, field_name: str) -> Optional[str]:
        """Валідація ідентифікатора (назва класу, змінної тощо)"""
        if not value.isidentifier():
            return f"'{field_name}' містить недопустимі символи"
        return None
    
    @staticmethod
    def validate_namespace(value: str) -> Optional[str]:
        """Валідація namespace"""
        if not all(part.isidentifier() for part in value.split('.')):
            return "Namespace містить недопустимі символи"
        return None


class ErrorHandler:
    """Централізована обробка помилок"""
    
    @staticmethod
    def show_error(title: str, message: str):
        """Показ помилки"""
        messagebox.showerror(title, message)
    
    @staticmethod
    def show_warning(title: str, message: str):
        """Показ попередження"""
        messagebox.showwarning(title, message)
    
    @staticmethod
    def show_info(title: str, message: str):
        """Показ інформації"""
        messagebox.showinfo(title, message)
    
    @staticmethod
    def handle_file_operation(operation: Callable, error_message: str = "Помилка файлової операції"):
        """Обробка файлових операцій з автоматичною обробкою помилок"""
        try:
            return operation()
        except FileNotFoundError:
            ErrorHandler.show_error("Помилка", "Файл не знайдено")
        except PermissionError:
            ErrorHandler.show_error("Помилка", "Недостатньо прав доступу")
        except Exception as e:
            ErrorHandler.show_error("Помилка", f"{error_message}: {e}")
        return None


# Приклад використання
if __name__ == "__main__":
    # Тестування компонентів
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("UI Components Test")
    root.geometry("800x600")
    
    # Тест ScrollableTextEditor
    text_editor, container = ScrollableTextEditor.create(root)
    container.pack(fill="both", expand=True, padx=10, pady=10)
    
    text_editor.insert("1.0", "Тест текстового редактора з повзунками\n" * 50)
    
    root.mainloop()
