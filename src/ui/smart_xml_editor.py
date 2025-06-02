#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Розумний XML редактор для RimWorld Mod Builder v1.0.1 Alpha
Автодоповнення, валідація в реальному часі, пропозиції значень
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import xml.etree.ElementTree as ET
import re
import os
import json
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

# Локальні імпорти
try:
    from utils.simple_logger import get_logger_instance
    from utils.xml_validator import XMLValidator
except ImportError as e:
    print(f"Помилка імпорту: {e}")
    # Fallback для тестування
    class MockXMLValidator:
        def validate_content(self, content): 
            return {"valid": True, "errors": [], "warnings": []}
    
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


class XMLSyntaxHighlighter:
    """Підсвічування синтаксису XML для tkinter Text widget"""

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.setup_tags()

    def setup_tags(self):
        """Налаштування тегів для підсвічування"""
        # XML теги
        self.text_widget.tag_configure("xml_tag", foreground="#569cd6", font=("Consolas", 11, "bold"))

        # XML атрибути
        self.text_widget.tag_configure("xml_attribute", foreground="#92c5f7")

        # Значення атрибутів (в лапках)
        self.text_widget.tag_configure("xml_value", foreground="#ce9178")

        # XML коментарі
        self.text_widget.tag_configure("xml_comment", foreground="#6a9955", font=("Consolas", 11, "italic"))

        # Числа
        self.text_widget.tag_configure("xml_number", foreground="#b5cea8")

        # XML декларація
        self.text_widget.tag_configure("xml_declaration", foreground="#c586c0")

        # Спеціальні символи
        self.text_widget.tag_configure("xml_special", foreground="#d4d4d4")

    def highlight_all(self):
        """Підсвічування всього тексту"""
        # Очищення попередніх тегів
        for tag in ["xml_tag", "xml_attribute", "xml_value", "xml_comment", "xml_number", "xml_declaration", "xml_special"]:
            self.text_widget.tag_remove(tag, "1.0", tk.END)

        content = self.text_widget.get("1.0", tk.END)

        # XML декларація
        self._highlight_pattern(r'<\?xml.*?\?>', "xml_declaration")

        # XML коментарі
        self._highlight_pattern(r'<!--.*?-->', "xml_comment")

        # XML теги (включаючи закриваючі)
        self._highlight_pattern(r'</?[a-zA-Z_][a-zA-Z0-9_.-]*', "xml_tag")

        # Спеціальні символи тегів
        self._highlight_pattern(r'[<>]', "xml_special")

        # XML атрибути
        self._highlight_pattern(r'\b[a-zA-Z_][a-zA-Z0-9_.-]*(?=\s*=)', "xml_attribute")

        # Значення атрибутів
        self._highlight_pattern(r'"[^"]*"', "xml_value")
        self._highlight_pattern(r"'[^']*'", "xml_value")

        # Числа
        self._highlight_pattern(r'\b\d+\.?\d*\b', "xml_number")

    def _highlight_pattern(self, pattern, tag):
        """Підсвічування за патерном"""
        content = self.text_widget.get("1.0", tk.END)

        for match in re.finditer(pattern, content, re.DOTALL):
            start_pos = self._get_position_from_index(match.start())
            end_pos = self._get_position_from_index(match.end())
            self.text_widget.tag_add(tag, start_pos, end_pos)

    def _get_position_from_index(self, index):
        """Конвертація індексу в позицію tkinter"""
        content = self.text_widget.get("1.0", tk.END)
        lines = content[:index].split('\n')
        line = len(lines)
        column = len(lines[-1]) if lines else 0
        return f"{line}.{column}"

    def highlight_line(self, line_number):
        """Підсвічування конкретного рядка"""
        start_pos = f"{line_number}.0"
        end_pos = f"{line_number}.end"
        line_content = self.text_widget.get(start_pos, end_pos)

        # Очищення тегів для цього рядка
        for tag in ["xml_tag", "xml_attribute", "xml_value", "xml_comment", "xml_number", "xml_declaration", "xml_special"]:
            self.text_widget.tag_remove(tag, start_pos, end_pos)

        # Підсвічування елементів рядка
        patterns = [
            (r'<\?xml.*?\?>', "xml_declaration"),
            (r'<!--.*?-->', "xml_comment"),
            (r'</?[a-zA-Z_][a-zA-Z0-9_.-]*', "xml_tag"),
            (r'[<>]', "xml_special"),
            (r'\b[a-zA-Z_][a-zA-Z0-9_.-]*(?=\s*=)', "xml_attribute"),
            (r'"[^"]*"', "xml_value"),
            (r"'[^']*'", "xml_value"),
            (r'\b\d+\.?\d*\b', "xml_number")
        ]

        for pattern, tag in patterns:
            for match in re.finditer(pattern, line_content):
                match_start = f"{line_number}.{match.start()}"
                match_end = f"{line_number}.{match.end()}"
                self.text_widget.tag_add(tag, match_start, match_end)


@dataclass
class AutoCompleteItem:
    """Елемент автодоповнення"""
    text: str
    type: str  # "tag", "attribute", "value"
    description: str
    insert_text: str
    category: str = ""


@dataclass
class ValidationResult:
    """Результат валідації"""
    line: int
    column: int
    type: str  # "error", "warning", "info"
    message: str
    suggestion: Optional[str] = None


class RimWorldXMLDatabase:
    """База даних RimWorld XML тегів та атрибутів"""
    
    def __init__(self):
        self.tags = self._load_rimworld_tags()
        self.attributes = self._load_rimworld_attributes()
        self.values = self._load_rimworld_values()
    
    def _load_rimworld_tags(self) -> Dict[str, Dict]:
        """Завантаження RimWorld тегів"""
        return {
            # Основні теги
            "Defs": {
                "description": "Кореневий елемент для дефініцій",
                "children": ["ThingDef", "RecipeDef", "ResearchProjectDef", "JobDef"],
                "attributes": []
            },
            "ThingDef": {
                "description": "Дефініція предмета/об'єкта",
                "children": ["defName", "label", "description", "thingClass", "category", "graphicData", "statBases", "costList"],
                "attributes": ["ParentName", "Name", "Abstract"]
            },
            "RecipeDef": {
                "description": "Дефініція рецепта",
                "children": ["defName", "label", "description", "jobString", "workAmount", "ingredients", "products"],
                "attributes": ["ParentName", "Name"]
            },
            "ResearchProjectDef": {
                "description": "Дефініція дослідження",
                "children": ["defName", "label", "description", "baseCost", "techLevel", "prerequisites"],
                "attributes": ["ParentName", "Name"]
            },
            
            # Вкладені теги
            "defName": {
                "description": "Унікальний ідентифікатор дефініції",
                "children": [],
                "attributes": [],
                "value_type": "string"
            },
            "label": {
                "description": "Відображувана назва",
                "children": [],
                "attributes": [],
                "value_type": "string"
            },
            "description": {
                "description": "Опис об'єкта",
                "children": [],
                "attributes": [],
                "value_type": "string"
            },
            "thingClass": {
                "description": "Клас об'єкта в коді",
                "children": [],
                "attributes": [],
                "value_type": "class"
            },
            "category": {
                "description": "Категорія об'єкта",
                "children": [],
                "attributes": [],
                "value_type": "enum"
            },
            "graphicData": {
                "description": "Дані графіки",
                "children": ["texPath", "graphicClass", "drawSize"],
                "attributes": []
            },
            "texPath": {
                "description": "Шлях до текстури",
                "children": [],
                "attributes": [],
                "value_type": "path"
            },
            "statBases": {
                "description": "Базові характеристики",
                "children": ["li"],
                "attributes": []
            },
            "li": {
                "description": "Елемент списку",
                "children": [],
                "attributes": ["Class"],
                "value_type": "varies"
            }
        }
    
    def _load_rimworld_attributes(self) -> Dict[str, Dict]:
        """Завантаження RimWorld атрибутів"""
        return {
            "ParentName": {
                "description": "Батьківська дефініція для наслідування",
                "values": ["BaseThing", "BaseWeapon", "BaseApparel"]
            },
            "Name": {
                "description": "Ім'я для посилання в інших дефініціях",
                "values": []
            },
            "Abstract": {
                "description": "Чи є дефініція абстрактною",
                "values": ["True", "False"]
            },
            "Class": {
                "description": "Клас для елемента списку",
                "values": ["StatModifier", "ThingDefCountClass", "IngredientCount"]
            }
        }
    
    def _load_rimworld_values(self) -> Dict[str, List[str]]:
        """Завантаження можливих значень"""
        return {
            "category": [
                "Building", "Item", "Pawn", "Plant", "Projectile", 
                "Ethereal", "Mote", "Gas", "Filth"
            ],
            "thingClass": [
                "Building", "Building_Door", "Building_Bed", "Building_Storage",
                "ThingWithComps", "Apparel", "Weapon", "Plant"
            ],
            "techLevel": [
                "Animal", "Neolithic", "Medieval", "Industrial", 
                "Spacer", "Ultra", "Archotech"
            ],
            "graphicClass": [
                "Graphic_Single", "Graphic_Multi", "Graphic_Random", 
                "Graphic_Appearances", "Graphic_StackCount"
            ]
        }
    
    def get_tag_suggestions(self, parent_tag: Optional[str] = None) -> List[AutoCompleteItem]:
        """Отримання пропозицій тегів"""
        suggestions = []
        
        if parent_tag and parent_tag in self.tags:
            # Дочірні теги
            for child in self.tags[parent_tag]["children"]:
                if child in self.tags:
                    suggestions.append(AutoCompleteItem(
                        text=child,
                        type="tag",
                        description=self.tags[child]["description"],
                        insert_text=f"<{child}></{child}>",
                        category="child"
                    ))
        else:
            # Всі доступні теги
            for tag, info in self.tags.items():
                suggestions.append(AutoCompleteItem(
                    text=tag,
                    type="tag",
                    description=info["description"],
                    insert_text=f"<{tag}></{tag}>",
                    category="all"
                ))
        
        return suggestions
    
    def get_attribute_suggestions(self, tag: str) -> List[AutoCompleteItem]:
        """Отримання пропозицій атрибутів"""
        suggestions = []
        
        if tag in self.tags:
            for attr in self.tags[tag]["attributes"]:
                if attr in self.attributes:
                    suggestions.append(AutoCompleteItem(
                        text=attr,
                        type="attribute",
                        description=self.attributes[attr]["description"],
                        insert_text=f'{attr}=""',
                        category="attribute"
                    ))
        
        return suggestions
    
    def get_value_suggestions(self, tag: str, attribute: Optional[str] = None) -> List[AutoCompleteItem]:
        """Отримання пропозицій значень"""
        suggestions = []
        
        # Пропозиції для атрибутів
        if attribute and attribute in self.attributes:
            for value in self.attributes[attribute]["values"]:
                suggestions.append(AutoCompleteItem(
                    text=value,
                    type="value",
                    description=f"Значення для {attribute}",
                    insert_text=value,
                    category="attribute_value"
                ))
        
        # Пропозиції для вмісту тегів
        if tag in self.tags:
            value_type = self.tags[tag].get("value_type")
            if value_type and value_type in self.values:
                for value in self.values[value_type]:
                    suggestions.append(AutoCompleteItem(
                        text=value,
                        type="value",
                        description=f"Значення для {tag}",
                        insert_text=value,
                        category="tag_value"
                    ))
        
        return suggestions


class AutoCompletePopup(ctk.CTkToplevel):
    """Popup для автодоповнення"""
    
    def __init__(self, parent, suggestions: List[AutoCompleteItem], **kwargs):
        super().__init__(parent, **kwargs)
        
        self.suggestions = suggestions
        self.selected_index = 0
        self.callback = None
        
        self.title("")
        self.geometry("300x200")
        self.resizable(False, False)
        self.transient(parent)
        
        # Видалення декорацій вікна
        self.overrideredirect(True)
        
        self.setup_ui()
        self.update_selection()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Список пропозицій
        self.listbox = tk.Listbox(
            self,
            height=min(10, len(self.suggestions)),
            font=("Consolas", 10),
            bg="#2b2b2b",
            fg="white",
            selectbackground="#404040",
            selectforeground="white",
            borderwidth=1,
            relief="solid"
        )
        self.listbox.pack(fill="both", expand=True)
        
        # Заповнення списку
        for suggestion in self.suggestions:
            display_text = f"{suggestion.text} - {suggestion.description}"
            self.listbox.insert(tk.END, display_text)
        
        # Обробники подій
        self.listbox.bind("<Double-Button-1>", self.on_select)
        self.listbox.bind("<Return>", self.on_select)
        self.bind("<Key>", self.on_key)
        self.bind("<FocusOut>", self.on_focus_out)
        
        # Фокус на список
        self.listbox.focus_set()
    
    def update_selection(self):
        """Оновлення вибору"""
        self.listbox.selection_clear(0, tk.END)
        if 0 <= self.selected_index < len(self.suggestions):
            self.listbox.selection_set(self.selected_index)
            self.listbox.see(self.selected_index)
    
    def on_key(self, event):
        """Обробка клавіш"""
        if event.keysym == "Up":
            self.selected_index = max(0, self.selected_index - 1)
            self.update_selection()
        elif event.keysym == "Down":
            self.selected_index = min(len(self.suggestions) - 1, self.selected_index + 1)
            self.update_selection()
        elif event.keysym == "Return":
            self.on_select(event)
        elif event.keysym == "Escape":
            self.destroy()
    
    def on_select(self, event):
        """Вибір елемента"""
        if 0 <= self.selected_index < len(self.suggestions):
            suggestion = self.suggestions[self.selected_index]
            if self.callback:
                self.callback(suggestion)
        self.destroy()
    
    def on_focus_out(self, event):
        """Втрата фокусу"""
        self.destroy()
    
    def set_callback(self, callback):
        """Встановлення callback"""
        self.callback = callback


class SmartXMLEditor(ctk.CTkFrame):
    """Розумний XML редактор"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.logger = get_logger_instance().get_logger()
        self.xml_database = RimWorldXMLDatabase()
        self.validator = XMLValidator() if 'XMLValidator' in globals() else MockXMLValidator()
        
        # Стан редактора
        self.current_file = None
        self.is_modified = False
        self.auto_complete_popup = None
        self.validation_markers = []
        self.syntax_highlighter = None

        self.setup_ui()
        self.setup_bindings()
        self.setup_syntax_highlighting()
    
    def setup_ui(self):
        """Налаштування інтерфейсу"""
        # Панель інструментів
        toolbar_frame = ctk.CTkFrame(self)
        toolbar_frame.pack(fill="x", padx=5, pady=5)
        
        # Кнопки файлових операцій
        self.new_button = ctk.CTkButton(
            toolbar_frame,
            text="🆕 Новий",
            command=self.new_file,
            width=80
        )
        self.new_button.pack(side="left", padx=2)
        
        self.open_button = ctk.CTkButton(
            toolbar_frame,
            text="📂 Відкрити",
            command=self.open_file,
            width=80
        )
        self.open_button.pack(side="left", padx=2)
        
        self.save_button = ctk.CTkButton(
            toolbar_frame,
            text="💾 Зберегти",
            command=self.save_file,
            width=80
        )
        self.save_button.pack(side="left", padx=2)
        
        # Кнопки редагування
        self.format_button = ctk.CTkButton(
            toolbar_frame,
            text="🎨 Форматувати",
            command=self.format_xml,
            width=100
        )
        self.format_button.pack(side="left", padx=2)
        
        self.validate_button = ctk.CTkButton(
            toolbar_frame,
            text="✅ Валідувати",
            command=self.validate_xml,
            width=100
        )
        self.validate_button.pack(side="left", padx=2)
        
        # Основний редактор
        editor_frame = ctk.CTkFrame(self)
        editor_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Текстовий редактор з номерами рядків
        self.text_editor = tk.Text(
            editor_frame,
            wrap=tk.NONE,
            font=("Consolas", 11),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            selectbackground="#264f78",
            selectforeground="white",
            tabs="    ",  # 4 пробіли для табуляції
            undo=True,
            maxundo=50
        )
        
        # Скролбари
        v_scrollbar = ctk.CTkScrollbar(editor_frame, command=self.text_editor.yview)
        h_scrollbar = ctk.CTkScrollbar(editor_frame, command=self.text_editor.xview, orientation="horizontal")
        
        self.text_editor.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Розміщення
        self.text_editor.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)
        
        # Статус бар
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(fill="x", padx=5, pady=5)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Готовий",
            anchor="w"
        )
        self.status_label.pack(side="left", padx=5)
        
        self.position_label = ctk.CTkLabel(
            self.status_frame,
            text="Рядок: 1, Стовпець: 1",
            anchor="e"
        )
        self.position_label.pack(side="right", padx=5)
    
    def setup_bindings(self):
        """Налаштування обробників подій"""
        # Автодоповнення
        self.text_editor.bind("<KeyRelease>", self.on_key_release)
        self.text_editor.bind("<Button-1>", self.on_click)
        self.text_editor.bind("<Control-space>", self.trigger_autocomplete)
        
        # Валідація в реальному часі
        self.text_editor.bind("<<Modified>>", self.on_text_modified)
        
        # Оновлення позиції курсора
        self.text_editor.bind("<KeyRelease>", self.update_cursor_position, add="+")
        self.text_editor.bind("<Button-1>", self.update_cursor_position, add="+")
        
        # Горячі клавіші
        self.text_editor.bind("<Control-s>", lambda e: self.save_file())
        self.text_editor.bind("<Control-o>", lambda e: self.open_file())
        self.text_editor.bind("<Control-n>", lambda e: self.new_file())
        self.text_editor.bind("<F5>", lambda e: self.validate_xml())

    def setup_syntax_highlighting(self):
        """Налаштування підсвічування синтаксису"""
        self.syntax_highlighter = XMLSyntaxHighlighter(self.text_editor)

        # Підсвічування при зміні тексту
        self.text_editor.bind("<KeyRelease>", self.on_text_change_highlight, add="+")
        self.text_editor.bind("<<Modified>>", self.on_text_modified_highlight, add="+")

    def on_text_change_highlight(self, event):
        """Підсвічування при зміні тексту"""
        if self.syntax_highlighter:
            # Підсвічування поточного рядка для швидкості
            cursor_pos = self.text_editor.index(tk.INSERT)
            line_number = int(cursor_pos.split('.')[0])
            self.syntax_highlighter.highlight_line(line_number)

    def on_text_modified_highlight(self, event):
        """Підсвічування при модифікації тексту"""
        if self.syntax_highlighter:
            # Повне підсвічування з затримкою для продуктивності
            self.after(100, self.syntax_highlighter.highlight_all)
    
    def new_file(self):
        """Створення нового файлу"""
        if self.is_modified:
            if not messagebox.askyesno("Зберегти зміни?", "Файл змінено. Зберегти зміни?"):
                return
            self.save_file()
        
        self.text_editor.delete(1.0, tk.END)
        self.text_editor.insert(1.0, '<?xml version="1.0" encoding="utf-8"?>\n<Defs>\n\n</Defs>')
        self.current_file = None
        self.is_modified = False
        self.update_title()

        # Підсвічування нового контенту
        if self.syntax_highlighter:
            self.syntax_highlighter.highlight_all()
    
    def open_file(self):
        """Відкриття файлу"""
        file_path = filedialog.askopenfilename(
            title="Відкрити XML файл",
            filetypes=[("XML файли", "*.xml"), ("Всі файли", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.text_editor.delete(1.0, tk.END)
                self.text_editor.insert(1.0, content)
                self.current_file = file_path
                self.is_modified = False
                self.update_title()

                # Підсвічування завантаженого контенту
                if self.syntax_highlighter:
                    self.syntax_highlighter.highlight_all()

                self.logger.info(f"Відкрито файл: {file_path}")
                
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося відкрити файл: {e}")
    
    def save_file(self):
        """Збереження файлу"""
        if not self.current_file:
            self.save_file_as()
            return
        
        try:
            content = self.text_editor.get(1.0, tk.END)
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.is_modified = False
            self.update_title()
            self.status_label.configure(text="Файл збережено")
            
            self.logger.info(f"Збережено файл: {self.current_file}")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти файл: {e}")
    
    def save_file_as(self):
        """Збереження файлу як"""
        file_path = filedialog.asksaveasfilename(
            title="Зберегти XML файл",
            defaultextension=".xml",
            filetypes=[("XML файли", "*.xml"), ("Всі файли", "*.*")]
        )
        
        if file_path:
            self.current_file = file_path
            self.save_file()
    
    def update_title(self):
        """Оновлення заголовка"""
        title = "Smart XML Editor"
        if self.current_file:
            title += f" - {os.path.basename(self.current_file)}"
        if self.is_modified:
            title += " *"
        
        # Оновлення заголовка батьківського вікна
        if hasattr(self.master, 'title'):
            self.master.title(title)

    def on_key_release(self, event):
        """Обробка відпускання клавіш"""
        # Автодоповнення при введенні < або пробілу
        if event.char == '<':
            self.trigger_autocomplete_tags()
        elif event.char == ' ' and self.is_in_tag():
            self.trigger_autocomplete_attributes()
        elif event.char in ['"', "'"]:
            self.trigger_autocomplete_values()

    def on_click(self, _):
        """Обробка кліку"""
        self.close_autocomplete()
        self.update_cursor_position()

    def on_text_modified(self, _):
        """Обробка зміни тексту"""
        if self.text_editor.edit_modified():
            self.is_modified = True
            self.update_title()
            self.text_editor.edit_modified(False)

            # Валідація в реальному часі (з затримкою)
            self.after(500, self.validate_real_time)

    def update_cursor_position(self, _=None):
        """Оновлення позиції курсора"""
        cursor_pos = self.text_editor.index(tk.INSERT)
        line, column = cursor_pos.split('.')
        self.position_label.configure(text=f"Рядок: {line}, Стовпець: {int(column) + 1}")

    def is_in_tag(self) -> bool:
        """Перевірка чи курсор знаходиться в тезі"""
        cursor_pos = self.text_editor.index(tk.INSERT)
        line_start = cursor_pos.split('.')[0] + '.0'
        line_text = self.text_editor.get(line_start, cursor_pos)

        # Пошук останнього < та >
        last_open = line_text.rfind('<')
        last_close = line_text.rfind('>')

        return last_open > last_close

    def get_current_tag(self) -> Optional[str]:
        """Отримання поточного тега"""
        cursor_pos = self.text_editor.index(tk.INSERT)
        line_start = cursor_pos.split('.')[0] + '.0'
        line_text = self.text_editor.get(line_start, cursor_pos)

        # Пошук тега
        match = re.search(r'<(\w+)', line_text[::-1])
        if match:
            return match.group(1)[::-1]
        return None

    def get_parent_tag(self) -> Optional[str]:
        """Отримання батьківського тега"""
        cursor_pos = self.text_editor.index(tk.INSERT)
        content_before = self.text_editor.get(1.0, cursor_pos)

        # Стек тегів
        tag_stack = []
        for match in re.finditer(r'<(/?)(\w+)', content_before):
            is_closing = match.group(1) == '/'
            tag_name = match.group(2)

            if is_closing:
                if tag_stack and tag_stack[-1] == tag_name:
                    tag_stack.pop()
            else:
                tag_stack.append(tag_name)

        return tag_stack[-1] if tag_stack else None

    def trigger_autocomplete(self, _=None):
        """Запуск автодоповнення"""
        if self.is_in_tag():
            self.trigger_autocomplete_attributes()
        else:
            self.trigger_autocomplete_tags()

    def trigger_autocomplete_tags(self):
        """Автодоповнення тегів"""
        parent_tag = self.get_parent_tag()
        suggestions = self.xml_database.get_tag_suggestions(parent_tag)

        if suggestions:
            self.show_autocomplete_popup(suggestions)

    def trigger_autocomplete_attributes(self):
        """Автодоповнення атрибутів"""
        current_tag = self.get_current_tag()
        if current_tag:
            suggestions = self.xml_database.get_attribute_suggestions(current_tag)
            if suggestions:
                self.show_autocomplete_popup(suggestions)

    def trigger_autocomplete_values(self):
        """Автодоповнення значень"""
        current_tag = self.get_current_tag()
        # TODO: Визначити поточний атрибут
        suggestions = self.xml_database.get_value_suggestions(current_tag or "")

        if suggestions:
            self.show_autocomplete_popup(suggestions)

    def show_autocomplete_popup(self, suggestions: List[AutoCompleteItem]):
        """Показ popup автодоповнення"""
        self.close_autocomplete()

        if not suggestions:
            return

        # Позиція курсора
        cursor_pos = self.text_editor.index(tk.INSERT)
        try:
            bbox = self.text_editor.bbox(cursor_pos)
            if bbox is None:
                return  # Курсор не видимий
            x, y, _, _ = bbox
        except:
            return  # Курсор не видимий

        # Абсолютні координати
        abs_x = self.text_editor.winfo_rootx() + x
        abs_y = self.text_editor.winfo_rooty() + y + 20

        # Створення popup
        self.auto_complete_popup = AutoCompletePopup(self, suggestions)
        self.auto_complete_popup.geometry(f"+{abs_x}+{abs_y}")
        self.auto_complete_popup.set_callback(self.on_autocomplete_select)

    def close_autocomplete(self):
        """Закриття автодоповнення"""
        if self.auto_complete_popup:
            self.auto_complete_popup.destroy()
            self.auto_complete_popup = None

    def on_autocomplete_select(self, suggestion: AutoCompleteItem):
        """Вибір елемента автодоповнення"""
        cursor_pos = self.text_editor.index(tk.INSERT)

        if suggestion.type == "tag":
            # Вставка тега
            self.text_editor.insert(cursor_pos, suggestion.insert_text)
            # Позиціонування курсора між тегами
            if suggestion.insert_text.endswith(f"</{suggestion.text}>"):
                new_pos = f"{cursor_pos.split('.')[0]}.{int(cursor_pos.split('.')[1]) + len(suggestion.text) + 2}"
                self.text_editor.mark_set(tk.INSERT, new_pos)

        elif suggestion.type == "attribute":
            # Вставка атрибута
            self.text_editor.insert(cursor_pos, suggestion.insert_text)
            # Позиціонування курсора між лапками
            new_pos = f"{cursor_pos.split('.')[0]}.{int(cursor_pos.split('.')[1]) + len(suggestion.insert_text) - 1}"
            self.text_editor.mark_set(tk.INSERT, new_pos)

        elif suggestion.type == "value":
            # Вставка значення
            self.text_editor.insert(cursor_pos, suggestion.insert_text)

        self.text_editor.focus_set()

    def format_xml(self):
        """Форматування XML"""
        try:
            content = self.text_editor.get(1.0, tk.END)

            # Парсинг XML
            root = ET.fromstring(content)

            # Форматування
            self.indent_xml(root)
            formatted = ET.tostring(root, encoding='unicode')

            # Додавання XML декларації
            if not formatted.startswith('<?xml'):
                formatted = '<?xml version="1.0" encoding="utf-8"?>\n' + formatted

            # Оновлення тексту
            self.text_editor.delete(1.0, tk.END)
            self.text_editor.insert(1.0, formatted)

            # Підсвічування відформатованого контенту
            if self.syntax_highlighter:
                self.syntax_highlighter.highlight_all()

            self.status_label.configure(text="XML відформатовано")

        except ET.ParseError as e:
            messagebox.showerror("Помилка форматування", f"Некоректний XML: {e}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося відформатувати XML: {e}")

    def indent_xml(self, elem, level=0):
        """Додавання відступів до XML"""
        indent = "\n" + "  " * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self.indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent

    def validate_xml(self):
        """Валідація XML"""
        content = self.text_editor.get(1.0, tk.END)

        try:
            # Базова XML валідація
            ET.fromstring(content)

            # RimWorld специфічна валідація
            result = self.validator.validate_content(content)

            if result["valid"]:
                self.status_label.configure(text="✅ XML валідний")
                messagebox.showinfo("Валідація", "XML файл валідний!")
            else:
                errors = result.get("errors", [])
                warnings = result.get("warnings", [])

                message = "Знайдені проблеми:\n\n"
                if errors:
                    message += "Помилки:\n" + "\n".join(errors[:5]) + "\n\n"
                if warnings:
                    message += "Попередження:\n" + "\n".join(warnings[:5])

                messagebox.showwarning("Валідація", message)
                self.status_label.configure(text="⚠️ Знайдені проблеми")

        except ET.ParseError as e:
            messagebox.showerror("Помилка XML", f"Некоректний XML: {e}")
            self.status_label.configure(text="❌ Некоректний XML")
        except Exception as e:
            messagebox.showerror("Помилка валідації", f"Помилка валідації: {e}")

    def validate_real_time(self):
        """Валідація в реальному часі"""
        content = self.text_editor.get(1.0, tk.END)

        # Очищення попередніх маркерів
        self.clear_validation_markers()

        try:
            # Швидка перевірка XML
            ET.fromstring(content)
            self.status_label.configure(text="✅ XML синтаксично коректний")

        except ET.ParseError as e:
            # Показ помилки в статус барі
            self.status_label.configure(text=f"❌ XML помилка: {str(e)}")

            # Додавання маркера помилки
            self.add_validation_marker(1, 1, "error", str(e))

        except Exception:
            # Ігнорування інших помилок для real-time валідації
            pass

    def clear_validation_markers(self):
        """Очищення маркерів валідації"""
        for marker in self.validation_markers:
            try:
                self.text_editor.tag_delete(marker)
            except:
                pass
        self.validation_markers.clear()

    def add_validation_marker(self, line: int, column: int, type: str, message: str):
        """Додавання маркера валідації"""
        _ = message  # Заглушка для unused parameter
        tag_name = f"validation_{type}_{len(self.validation_markers)}"

        # Кольори для різних типів
        colors = {
            "error": "#ff6b6b",
            "warning": "#ffa500",
            "info": "#4dabf7"
        }

        # Конфігурація тега
        self.text_editor.tag_configure(
            tag_name,
            background=colors.get(type, "#ff6b6b"),
            foreground="white"
        )

        # Позиція маркера
        start_pos = f"{line}.{column}"
        end_pos = f"{line}.{column + 1}"

        # Додавання тега
        self.text_editor.tag_add(tag_name, start_pos, end_pos)

        self.validation_markers.append(tag_name)


if __name__ == "__main__":
    # Тестування Smart XML Editor
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Smart XML Editor - Тест")
    root.geometry("1000x700")

    editor = SmartXMLEditor(root)
    editor.pack(fill="both", expand=True, padx=10, pady=10)

    root.mainloop()
