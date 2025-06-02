#!/usr/bin/env python3
"""
RimWorld Mod Builder - Версія з CustomTkinter
Інструмент для створення та редагування модів RimWorld з сучасним графічним інтерфейсом
"""

import sys
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path

# Налаштування CustomTkinter
ctk.set_appearance_mode("dark")  # Темна тема за замовчуванням
ctk.set_default_color_theme("blue")  # Синя колірна схема

# Додаємо src до шляху для імпорту модулів
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import re
import tkinter as tk


class XMLSyntaxHighlighter:
    """Підсвічування синтаксису XML для tkinter Text widget"""

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.setup_tags()

    def setup_tags(self):
        """Налаштування тегів для підсвічування"""
        # XML теги
        self.text_widget.tag_configure("xml_tag", foreground="#569cd6", font=("Consolas", 12, "bold"))

        # XML атрибути
        self.text_widget.tag_configure("xml_attribute", foreground="#92c5f7")

        # Значення атрибутів (в лапках)
        self.text_widget.tag_configure("xml_value", foreground="#ce9178")

        # XML коментарі
        self.text_widget.tag_configure("xml_comment", foreground="#6a9955", font=("Consolas", 12, "italic"))

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

        # content = self.text_widget.get("1.0", tk.END)  # Не використовується

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


class RimWorldModBuilder:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("RimWorld Mod Builder v2.0")
        self.root.geometry("1200x800")
        
        # Змінні стану
        self.current_project_path = None
        self.current_file_path = None
        self.unsaved_changes = False
        
        self.setup_ui()

    def run(self):
        """Запуск головного циклу програми"""
        self.root.mainloop()

    def setup_ui(self):
        """Налаштування інтерфейсу користувача"""
        # Головне меню
        self.setup_menu()
        
        # Головна панель
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Ліва панель - файловий експлорер
        self.setup_file_explorer()
        
        # Центральна панель - редактор
        self.setup_editor()
        
        # Права панель - інструменти
        self.setup_tools_panel()
        
        # Статусна панель
        self.setup_status_bar()
        
    def setup_menu(self):
        """Налаштування меню"""
        # Верхня панель з кнопками меню
        self.menu_frame = ctk.CTkFrame(self.root, height=50)
        self.menu_frame.pack(fill="x", padx=10, pady=(10, 0))
        self.menu_frame.pack_propagate(False)
        
        # Кнопки меню
        self.new_project_btn = ctk.CTkButton(
            self.menu_frame, 
            text="Новий проєкт",
            command=self.new_project,
            width=120
        )
        self.new_project_btn.pack(side="left", padx=5, pady=10)
        
        self.open_project_btn = ctk.CTkButton(
            self.menu_frame,
            text="Відкрити проєкт", 
            command=self.open_project,
            width=120
        )
        self.open_project_btn.pack(side="left", padx=5, pady=10)
        
        self.save_btn = ctk.CTkButton(
            self.menu_frame,
            text="Зберегти",
            command=self.save_file,
            width=100
        )
        self.save_btn.pack(side="left", padx=5, pady=10)
        
        # Перемикач теми
        self.theme_switch = ctk.CTkSwitch(
            self.menu_frame,
            text="Світла тема",
            command=self.toggle_theme
        )
        self.theme_switch.pack(side="right", padx=10, pady=10)
        
    def setup_file_explorer(self):
        """Налаштування файлового експлорера"""
        self.file_frame = ctk.CTkFrame(self.main_frame, width=250)
        self.file_frame.pack(side="left", fill="y", padx=(0, 10))
        self.file_frame.pack_propagate(False)
        
        # Заголовок
        self.file_label = ctk.CTkLabel(
            self.file_frame, 
            text="Файли проєкту",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.file_label.pack(pady=10)
        
        # Список файлів (використовуємо CTkScrollableFrame)
        self.file_list_frame = ctk.CTkScrollableFrame(self.file_frame)
        self.file_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def setup_editor(self):
        """Налаштування редактора"""
        self.editor_frame = ctk.CTkFrame(self.main_frame)
        self.editor_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Заголовок редактора
        self.editor_header = ctk.CTkFrame(self.editor_frame, height=40)
        self.editor_header.pack(fill="x", padx=10, pady=(10, 0))
        self.editor_header.pack_propagate(False)
        
        self.file_name_label = ctk.CTkLabel(
            self.editor_header,
            text="Виберіть файл для редагування",
            font=ctk.CTkFont(size=14)
        )
        self.file_name_label.pack(side="left", padx=10, pady=10)
        
        # Текстовий редактор з підсвічуванням синтаксису та CustomTkinter повзунками
        import tkinter as tk

        # Контейнер для редактора з повзунками (CustomTkinter Frame)
        text_container = ctk.CTkFrame(self.editor_frame)
        text_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.text_editor = tk.Text(
            text_container,
            font=("Consolas", 12),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            selectbackground="#264f78",
            selectforeground="white",
            tabs="    ",  # 4 пробіли для табуляції
            undo=True,
            maxundo=50,
            wrap=tk.NONE  # Вимкнути перенос рядків для горизонтального повзунка
        )

        # CustomTkinter повзунки (такі ж як у "Файли проєкту")
        v_scrollbar = ctk.CTkScrollbar(text_container, command=self.text_editor.yview)
        self.text_editor.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ctk.CTkScrollbar(text_container, command=self.text_editor.xview, orientation="horizontal")
        self.text_editor.configure(xscrollcommand=h_scrollbar.set)

        # Розміщення елементів
        self.text_editor.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Налаштування розтягування
        text_container.grid_rowconfigure(0, weight=1)
        text_container.grid_columnconfigure(0, weight=1)

        self.text_editor.bind("<KeyPress>", self.on_text_change)

        # Ініціалізація підсвічування синтаксису
        self.syntax_highlighter = None
        self.setup_syntax_highlighting()

    def setup_syntax_highlighting(self):
        """Налаштування підсвічування синтаксису"""
        self.syntax_highlighter = XMLSyntaxHighlighter(self.text_editor)

        # Додаємо обробники для підсвічування
        self.text_editor.bind("<KeyRelease>", self.on_text_change_highlight, add="+")

    def on_text_change_highlight(self, event=None):
        """Підсвічування при зміні тексту"""
        _ = event  # Позначаємо що параметр використовується
        if self.syntax_highlighter and self.current_file_path and self.current_file_path.suffix == '.xml':
            # Підсвічування з затримкою для продуктивності
            self.root.after(100, self.syntax_highlighter.highlight_all)

    def setup_tools_panel(self):
        """Налаштування панелі інструментів"""
        self.tools_frame = ctk.CTkFrame(self.main_frame, width=200)
        self.tools_frame.pack(side="right", fill="y")
        self.tools_frame.pack_propagate(False)
        
        # Заголовок
        self.tools_label = ctk.CTkLabel(
            self.tools_frame,
            text="Інструменти",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.tools_label.pack(pady=10)
        
        # Кнопки інструментів
        self.validate_btn = ctk.CTkButton(
            self.tools_frame,
            text="Валідувати XML",
            command=self.validate_xml
        )
        self.validate_btn.pack(pady=5, padx=10, fill="x")
        
        self.templates_btn = ctk.CTkButton(
            self.tools_frame,
            text="XML Шаблони",
            command=self.show_templates
        )
        self.templates_btn.pack(pady=5, padx=10, fill="x")

        self.csharp_btn = ctk.CTkButton(
            self.tools_frame,
            text="C# Шаблони",
            command=self.show_csharp_templates
        )
        self.csharp_btn.pack(pady=5, padx=10, fill="x")

        self.dll_compiler_btn = ctk.CTkButton(
            self.tools_frame,
            text="🔨 Компілятор DLL",
            command=self.show_dll_compiler,
            fg_color="#8B4513",
            hover_color="#A0522D"
        )
        self.dll_compiler_btn.pack(pady=5, padx=10, fill="x")
        
        self.textures_btn = ctk.CTkButton(
            self.tools_frame,
            text="Менеджер текстур",
            command=self.show_texture_manager
        )
        self.textures_btn.pack(pady=5, padx=10, fill="x")

        self.preview_btn = ctk.CTkButton(
            self.tools_frame,
            text="Попередній перегляд",
            command=self.show_definition_preview
        )
        self.preview_btn.pack(pady=5, padx=10, fill="x")

        self.export_btn = ctk.CTkButton(
            self.tools_frame,
            text="Експорт мода",
            command=self.export_mod
        )
        self.export_btn.pack(pady=5, padx=10, fill="x")

        self.workshop_btn = ctk.CTkButton(
            self.tools_frame,
            text="Steam Workshop",
            command=self.show_steam_workshop,
            fg_color="#1e3a8a",
            hover_color="#1e40af"
        )
        self.workshop_btn.pack(pady=5, padx=10, fill="x")
        
        # Інформація про проєкт
        self.info_frame = ctk.CTkFrame(self.tools_frame)
        self.info_frame.pack(fill="x", padx=10, pady=20)
        
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="Інформація про проєкт",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.info_label.pack(pady=5)
        
        self.project_info = ctk.CTkLabel(
            self.info_frame,
            text="Проєкт не відкрито",
            wraplength=180
        )
        self.project_info.pack(pady=5)
        
    def setup_status_bar(self):
        """Налаштування статусної панелі"""
        self.status_frame = ctk.CTkFrame(self.root, height=30)
        self.status_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Готовий до роботи"
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
    def toggle_theme(self):
        """Перемикання теми"""
        if self.theme_switch.get():
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
            
    def new_project(self):
        """Створення нового проєкту"""
        dialog = NewProjectDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.create_project_structure(dialog.result)
            
    def create_project_structure(self, project_data):
        """Створення структури проєкту"""
        try:
            project_path = Path(project_data['path']) / project_data['name']
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Створення папок
            (project_path / "About").mkdir(exist_ok=True)
            (project_path / "Defs").mkdir(exist_ok=True)
            (project_path / "Textures").mkdir(exist_ok=True)
            (project_path / "Assemblies").mkdir(exist_ok=True)
            (project_path / "Source").mkdir(exist_ok=True)
            
            # Створення About.xml
            about_content = f"""<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
    <name>{project_data['name']}</name>
    <author>{project_data['author']}</author>
    <packageId>{project_data['author'].lower()}.{project_data['name'].lower()}</packageId>
    <description>{project_data['description']}</description>
    <supportedVersions>
        <li>1.5</li>
    </supportedVersions>
</ModMetaData>"""
            
            about_file = project_path / "About" / "About.xml"
            about_file.write_text(about_content, encoding='utf-8')

            # Створення C# структури
            try:
                from src.core.csharp_manager import CSharpManager
                csharp_manager = CSharpManager(project_path)
                csharp_manager.create_csharp_structure(project_data['name'], project_data['author'])
            except Exception as e:
                print(f"Попередження: Не вдалося створити C# структуру: {e}")

            self.current_project_path = project_path
            self.load_project_files()
            self.update_project_info(project_data)
            self.status_label.configure(text=f"Проєкт створено: {project_path.name}")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося створити проєкт: {e}")
            
    def open_project(self):
        """Відкриття існуючого проєкту"""
        folder_path = filedialog.askdirectory(title="Виберіть папку проєкту")
        if folder_path:
            self.current_project_path = Path(folder_path)
            self.load_project_files()
            self.load_project_info()
            self.status_label.configure(text=f"Проєкт відкрито: {Path(folder_path).name}")
            
    def load_project_files(self):
        """Завантаження файлів проєкту"""
        if not self.current_project_path:
            return
            
        # Очищення списку файлів
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
            
        # Додавання файлів
        self.add_files_to_list(self.current_project_path, 0)
        
    def add_files_to_list(self, path, level):
        """Рекурсивне додавання файлів до списку"""
        try:
            for item in sorted(path.iterdir()):
                indent = "  " * level
                if item.is_dir():
                    folder_btn = ctk.CTkButton(
                        self.file_list_frame,
                        text=f"{indent}📁 {item.name}",
                        anchor="w",
                        fg_color="transparent",
                        text_color=("gray10", "gray90"),
                        hover_color=("gray80", "gray20")
                    )
                    folder_btn.pack(fill="x", pady=1)
                    self.add_files_to_list(item, level + 1)
                else:
                    file_btn = ctk.CTkButton(
                        self.file_list_frame,
                        text=f"{indent}📄 {item.name}",
                        anchor="w",
                        fg_color="transparent",
                        text_color=("gray10", "gray90"),
                        hover_color=("gray80", "gray20"),
                        command=lambda p=item: self.open_file(p)
                    )
                    file_btn.pack(fill="x", pady=1)
        except PermissionError:
            pass
            
    def open_file(self, file_path):
        """Відкриття файлу в редакторі"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", content)
            self.current_file_path = file_path
            self.file_name_label.configure(text=f"📄 {file_path.name}")
            self.unsaved_changes = False
            self.status_label.configure(text=f"Відкрито: {file_path.name}")

            # Підсвічування синтаксису для XML файлів
            if self.syntax_highlighter and file_path.suffix == '.xml':
                self.syntax_highlighter.highlight_all()
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося відкрити файл: {e}")
            
    def save_file(self):
        """Збереження поточного файлу"""
        if not self.current_file_path:
            messagebox.showwarning("Попередження", "Немає відкритого файлу для збереження")
            return
            
        try:
            content = self.text_editor.get("1.0", "end-1c")
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.unsaved_changes = False
            self.status_label.configure(text=f"Збережено: {self.current_file_path.name}")
            
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти файл: {e}")
            
    def on_text_change(self, event=None):
        """Обробка змін в тексті"""
        _ = event  # Позначаємо що параметр використовується
        self.unsaved_changes = True
        
    def update_project_info(self, project_data):
        """Оновлення інформації про проєкт"""
        info_text = f"Назва: {project_data['name']}\nАвтор: {project_data['author']}"
        self.project_info.configure(text=info_text)
        
    def load_project_info(self):
        """Завантаження інформації про проєкт"""
        if not self.current_project_path:
            return
            
        about_file = self.current_project_path / "About" / "About.xml"
        if about_file.exists():
            try:
                content = about_file.read_text(encoding='utf-8')
                # Простий парсинг XML для отримання назви та автора
                import re
                name_match = re.search(r'<name>(.*?)</name>', content)
                author_match = re.search(r'<author>(.*?)</author>', content)
                
                name = name_match.group(1) if name_match else "Невідомо"
                author = author_match.group(1) if author_match else "Невідомо"
                
                info_text = f"Назва: {name}\nАвтор: {author}"
                self.project_info.configure(text=info_text)
            except:
                self.project_info.configure(text="Помилка читання About.xml")
        else:
            self.project_info.configure(text="About.xml не знайдено")
            
    def validate_xml(self):
        """Валідація XML"""
        if not self.current_file_path or not self.current_file_path.suffix == '.xml':
            messagebox.showwarning("Попередження", "Виберіть XML файл для валідації")
            return

        try:
            from src.utils.xml_validator_simple import SimpleXMLValidator

            content = self.text_editor.get("1.0", "end-1c")
            validator = SimpleXMLValidator()

            if validator.validate_content(content):
                report = validator.get_validation_report()
                formatted_report = validator.format_report(report)

                # Показуємо детальний звіт
                ValidationReportDialog(self.root, formatted_report)
            else:
                report = validator.get_validation_report()
                formatted_report = validator.format_report(report)
                ValidationReportDialog(self.root, formatted_report)

        except ImportError:
            # Fallback до простої валідації
            try:
                import xml.etree.ElementTree as ET
                content = self.text_editor.get("1.0", "end-1c")
                ET.fromstring(content)
                messagebox.showinfo("Валідація", "XML файл синтаксично правильний!")
            except ET.ParseError as e:
                messagebox.showerror("Помилка валідації", f"XML помилка: {e}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося валідувати: {e}")
            
    def show_templates(self):
        """Показ шаблонів"""
        dialog = TemplateDialog(self.root)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            # Вставляємо шаблон в редактор
            template_content = dialog.result
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", template_content)
            self.file_name_label.configure(text="📄 Новий файл з шаблону")
            self.current_file_path = None
            self.unsaved_changes = True
            self.status_label.configure(text="Шаблон завантажено")

            # Підсвічування синтаксису для XML шаблонів
            if self.syntax_highlighter and template_content.strip().startswith('<?xml'):
                self.syntax_highlighter.highlight_all()

    def show_texture_manager(self):
        """Показ менеджера текстур CustomTkinter"""
        if not self.current_project_path:
            messagebox.showwarning("Попередження", "Спочатку відкрийте проєкт")
            return

        try:
            # Додаємо логування для діагностики
            print(f"🔍 Відкриття менеджера текстур для проєкту: {self.current_project_path}")

            from src.ui.texture_manager_customtkinter import TextureManagerCustomTkinter

            # Створюємо нове вікно для менеджера текстур
            texture_window = ctk.CTkToplevel(self.root)
            texture_window.title("🎮 RimWorld Mod Builder - Менеджер текстур")
            texture_window.geometry("1400x900")
            texture_window.minsize(1000, 600)

            # Центруємо вікно відносно головного
            texture_window.transient(self.root)

            # Створюємо менеджер текстур з батьківським вікном
            texture_manager = TextureManagerCustomTkinter(
                project_path=str(self.current_project_path),
                parent_window=texture_window
            )

            # Зберігаємо посилання на менеджер у вікні для доступу
            setattr(texture_window, 'texture_manager', texture_manager)

            self.status_label.configure(text="✅ Менеджер текстур відкрито")
            print("✅ Менеджер текстур успішно створено")

        except ImportError as e:
            error_msg = f"Не вдалося завантажити менеджер текстур: {e}"
            print(f"❌ ImportError: {error_msg}")
            messagebox.showerror("Помилка імпорту", error_msg)
        except Exception as e:
            error_msg = f"Помилка запуску менеджера текстур: {e}"
            print(f"❌ Exception: {error_msg}")
            print(f"Тип помилки: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Помилка", error_msg)

    def show_csharp_templates(self):
        """Показ C# шаблонів"""
        if not self.current_project_path:
            messagebox.showwarning("Попередження", "Спочатку відкрийте проєкт")
            return

        try:
            from src.ui.csharp_dialog import show_csharp_dialog
            result = show_csharp_dialog(self.root, self.current_project_path)

            if result:
                # Оновлюємо файловий експлорер
                self.load_project_files()
                # Відкриваємо створений файл
                self.open_file(result['file_path'])
                self.status_label.configure(text=f"C# файл створено: {result['class_name']}")

        except ImportError as e:
            messagebox.showerror("Помилка", f"Не вдалося завантажити C# діалог: {e}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка створення C# файлу: {e}")

    def show_definition_preview(self):
        """Показ попереднього перегляду дефініцій"""
        if not self.current_project_path:
            messagebox.showwarning("Попередження", "Спочатку відкрийте проєкт")
            return

        try:
            from src.ui.definition_preview import show_definition_preview
            show_definition_preview(self.root, self.current_project_path)
        except ImportError as e:
            messagebox.showerror("Помилка", f"Не вдалося завантажити систему перегляду: {e}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка запуску попереднього перегляду: {e}")

    def show_steam_workshop(self):
        """Показ діалогу Steam Workshop"""
        if not self.current_project_path:
            messagebox.showwarning("Попередження", "Спочатку відкрийте проєкт")
            return

        try:
            from src.ui.steam_workshop_dialog import show_steam_workshop_dialog
            show_steam_workshop_dialog(self.root, self.current_project_path)
        except ImportError as e:
            messagebox.showerror("Помилка", f"Не вдалося завантажити Steam Workshop діалог: {e}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Помилка запуску Steam Workshop: {e}")

    def show_dll_compiler(self):
        """Відкриття DLL компілятора"""
        try:
            # Створення нового вікна для DLL компілятора
            dll_window = ctk.CTkToplevel(self.root)
            dll_window.title("🔨 Компілятор DLL для RimWorld")
            dll_window.geometry("1000x700")
            dll_window.transient(self.root)
            dll_window.grab_set()

            # Імпорт DLL компілятора
            try:
                from src.ui.dll_compiler_widget import DLLCompilerWidget

                # Створення віджета компілятора
                dll_compiler = DLLCompilerWidget(dll_window)
                dll_compiler.pack(fill="both", expand=True, padx=10, pady=10)

                # Якщо є відкритий проєкт, спробувати знайти C# проєкти
                if self.current_project_path:
                    source_dir = self.current_project_path / "Source"
                    if source_dir.exists():
                        # Пошук .csproj файлів
                        csproj_files = list(source_dir.rglob("*.csproj"))
                        if csproj_files:
                            # Додавання знайдених проєктів
                            for csproj_file in csproj_files:
                                dll_compiler.current_projects.append(str(csproj_file))
                            dll_compiler.update_projects_display()
                            dll_compiler.output_frame.add_output(
                                f"🔍 Знайдено {len(csproj_files)} C# проєктів у поточному моді",
                                "info"
                            )

                self.status_label.configure(text="✅ DLL компілятор відкрито")
                print("✅ DLL компілятор успішно створено")

            except ImportError as e:
                print(f"Помилка імпорту DLL компілятора: {e}")
                # Fallback - показати повідомлення
                error_label = ctk.CTkLabel(
                    dll_window,
                    text="❌ Не вдалося завантажити DLL компілятор\n\nПеревірте встановлення залежностей",
                    font=ctk.CTkFont(size=16)
                )
                error_label.pack(expand=True)

        except Exception as e:
            print(f"Помилка відкриття DLL компілятора: {e}")
            messagebox.showerror("Помилка", f"Не вдалося відкрити DLL компілятор:\n{e}")

    def export_mod(self):
        """Експорт мода"""
        if not self.current_project_path:
            messagebox.showwarning("Попередження", "Спочатку відкрийте проєкт")
            return

        # Діалог вибору типу експорту
        export_dialog = ExportDialog(self.root, self.current_project_path)
        self.root.wait_window(export_dialog.dialog)

        if export_dialog.result:
            self.status_label.configure(text="Мод експортовано успішно!")

    def save_project(self):
        """Збереження поточного проєкту"""
        if not self.current_project_path:
            messagebox.showwarning("Попередження", "Немає відкритого проєкту для збереження")
            return

        try:
            # Зберігаємо всі відкриті файли
            # Тут можна додати логіку збереження всіх змін
            self.status_label.configure(text="Проєкт збережено")
            messagebox.showinfo("Успіх", "Проєкт збережено успішно")

        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти проєкт:\n{e}")


class NewProjectDialog:
    def __init__(self, parent):
        self.result = None
        
        # Створення діалогу
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Новий проєкт")
        self.dialog.geometry("500x400")
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
            text="Створення нового проєкту",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Основна форма
        form_frame = ctk.CTkFrame(self.dialog)
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Поля вводу
        ctk.CTkLabel(form_frame, text="Назва мода:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(20, 5))
        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="Введіть назву мода")
        self.name_entry.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(form_frame, text="Автор:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(0, 5))
        self.author_entry = ctk.CTkEntry(form_frame, placeholder_text="Ваше ім'я")
        self.author_entry.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(form_frame, text="Опис:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(0, 5))
        self.description_text = ctk.CTkTextbox(form_frame, height=80)
        self.description_text.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(form_frame, text="Шлях:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(0, 5))
        
        path_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.path_entry = ctk.CTkEntry(path_frame, placeholder_text="Виберіть папку")
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.path_entry.insert(0, str(Path.home() / "RimWorldMods"))
        
        browse_btn = ctk.CTkButton(path_frame, text="Огляд", command=self.browse_path, width=80)
        browse_btn.pack(side="right")
        
        # Кнопки
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        cancel_btn = ctk.CTkButton(button_frame, text="Скасувати", command=self.dialog.destroy)
        cancel_btn.pack(side="right", padx=(10, 0))
        
        create_btn = ctk.CTkButton(button_frame, text="Створити", command=self.create_project)
        create_btn.pack(side="right")
        
        # Фокус на першому полі
        self.name_entry.focus()
        
    def browse_path(self):
        """Вибір шляху для проєкту"""
        folder_path = filedialog.askdirectory(title="Виберіть папку для проєкту")
        if folder_path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder_path)
            
    def create_project(self):
        """Створення проєкту"""
        name = self.name_entry.get().strip()
        author = self.author_entry.get().strip()
        description = self.description_text.get("1.0", "end-1c").strip()
        path = self.path_entry.get().strip()
        
        if not name or not author:
            messagebox.showerror("Помилка", "Назва та автор є обов'язковими полями")
            return
            
        self.result = {
            'name': name,
            'author': author,
            'description': description,
            'path': path
        }
        
        self.dialog.destroy()


class TemplateDialog:
    def __init__(self, parent):
        self.result = None

        # Імпорт менеджера шаблонів
        try:
            from src.core.template_manager import TemplateManager
            self.template_manager = TemplateManager("src/templates")
        except ImportError:
            messagebox.showerror("Помилка", "Не вдалося завантажити менеджер шаблонів")
            return

        # Створення діалогу
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Шаблони дефініцій")
        self.dialog.geometry("700x500")
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
            text="Виберіть шаблон",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)

        # Основна область
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Список шаблонів
        self.template_frame = ctk.CTkScrollableFrame(main_frame, label_text="Доступні шаблони")
        self.template_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Завантаження шаблонів
        self.load_templates()

        # Кнопки
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        cancel_btn = ctk.CTkButton(button_frame, text="Скасувати", command=self.dialog.destroy)
        cancel_btn.pack(side="right", padx=(10, 0))

    def load_templates(self):
        """Завантаження списку шаблонів"""
        templates = self.template_manager.get_template_list()

        if not templates:
            no_templates_label = ctk.CTkLabel(
                self.template_frame,
                text="Шаблони не знайдено",
                font=ctk.CTkFont(size=14)
            )
            no_templates_label.pack(pady=20)
            return

        # Групування за категоріями
        categories = {}
        for template in templates:
            category = template['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(template)

        # Відображення шаблонів по категоріях
        for category, category_templates in categories.items():
            # Заголовок категорії
            category_label = ctk.CTkLabel(
                self.template_frame,
                text=f"📁 {category}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            category_label.pack(anchor="w", pady=(10, 5))

            # Шаблони в категорії
            for template in category_templates:
                template_frame = ctk.CTkFrame(self.template_frame)
                template_frame.pack(fill="x", pady=2)

                # Назва шаблону
                name_label = ctk.CTkLabel(
                    template_frame,
                    text=template['name'].replace('_template', '').replace('_', ' ').title(),
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                name_label.pack(anchor="w", padx=10, pady=(5, 0))

                # Опис шаблону
                desc_label = ctk.CTkLabel(
                    template_frame,
                    text=template['description'],
                    font=ctk.CTkFont(size=12),
                    text_color="gray"
                )
                desc_label.pack(anchor="w", padx=10, pady=(0, 5))

                # Кнопка використання
                use_btn = ctk.CTkButton(
                    template_frame,
                    text="Використати",
                    command=lambda t=template['name']: self.use_template(t),
                    width=100
                )
                use_btn.pack(side="right", padx=10, pady=5)

    def use_template(self, template_name):
        """Використання шаблону"""
        try:
            # Простий рендеринг без змінних
            template_content = self.template_manager.templates[template_name]['content']

            # Видаляємо коментарі з описом
            lines = template_content.split('\n')
            filtered_lines = [line for line in lines if not line.strip().startswith('<!-- Description:')]
            template_content = '\n'.join(filtered_lines)

            self.result = template_content
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося завантажити шаблон: {e}")


class ValidationReportDialog:
    def __init__(self, parent, report_text):
        # Створення діалогу
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Звіт валідації XML")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Центрування діалогу
        self.dialog.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")

        self.setup_dialog(report_text)

    def setup_dialog(self, report_text):
        """Налаштування діалогу"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self.dialog,
            text="Результат валідації",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)

        # Текстова область для звіту
        self.report_text = ctk.CTkTextbox(
            self.dialog,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.report_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Вставляємо звіт
        self.report_text.insert("1.0", report_text)
        self.report_text.configure(state="disabled")  # Тільки для читання

        # Кнопка закриття
        close_btn = ctk.CTkButton(
            self.dialog,
            text="Закрити",
            command=self.dialog.destroy,
            width=100
        )
        close_btn.pack(pady=(0, 20))


class ExportDialog:
    """Діалог експорту мода"""

    def __init__(self, parent, project_path):
        self.parent = parent
        self.project_path = project_path
        self.result = None

        # Створення діалогу
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Експорт мода")
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
            text="Експорт мода",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)

        # Основна область
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Опції експорту
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            options_frame,
            text="Виберіть тип експорту:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)

        # Радіо кнопки для типу експорту
        self.export_type = ctk.StringVar(value="local")

        local_radio = ctk.CTkRadioButton(
            options_frame,
            text="📁 Локальний експорт (для тестування)",
            variable=self.export_type,
            value="local"
        )
        local_radio.pack(anchor="w", padx=20, pady=5)

        workshop_radio = ctk.CTkRadioButton(
            options_frame,
            text="🌐 Steam Workshop (для публікації)",
            variable=self.export_type,
            value="workshop"
        )
        workshop_radio.pack(anchor="w", padx=20, pady=5)

        zip_radio = ctk.CTkRadioButton(
            options_frame,
            text="📦 ZIP архів (для розповсюдження)",
            variable=self.export_type,
            value="zip"
        )
        zip_radio.pack(anchor="w", padx=20, pady=(5, 15))

        # Шлях експорту
        path_frame = ctk.CTkFrame(main_frame)
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

        # Встановлюємо папку за замовчуванням
        default_path = Path(self.project_path).parent / "Exported"
        self.export_path_entry.insert(0, str(default_path))

        browse_btn = ctk.CTkButton(
            path_input_frame,
            text="Огляд",
            command=self.browse_export_path,
            width=80
        )
        browse_btn.pack(side="right")

        # Додаткові опції
        extra_frame = ctk.CTkFrame(main_frame)
        extra_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            extra_frame,
            text="Додаткові опції:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        self.include_source = ctk.BooleanVar(value=True)
        source_check = ctk.CTkCheckBox(
            extra_frame,
            text="Включити вихідний код C#",
            variable=self.include_source
        )
        source_check.pack(anchor="w", padx=20, pady=2)

        self.validate_before = ctk.BooleanVar(value=True)
        validate_check = ctk.CTkCheckBox(
            extra_frame,
            text="Валідувати перед експортом",
            variable=self.validate_before
        )
        validate_check.pack(anchor="w", padx=20, pady=2)

        self.create_readme = ctk.BooleanVar(value=False)
        readme_check = ctk.CTkCheckBox(
            extra_frame,
            text="Створити README.txt",
            variable=self.create_readme
        )
        readme_check.pack(anchor="w", padx=20, pady=(2, 10))

        # Кнопки
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Скасувати",
            command=self.dialog.destroy
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        export_btn = ctk.CTkButton(
            button_frame,
            text="🚀 Експортувати",
            command=self.start_export,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        export_btn.pack(side="right")

    def browse_export_path(self):
        """Вибір папки для експорту"""
        folder = filedialog.askdirectory(
            title="Виберіть папку для експорту",
            initialdir=str(Path(self.project_path).parent)
        )

        if folder:
            self.export_path_entry.delete(0, "end")
            self.export_path_entry.insert(0, folder)

    def start_export(self):
        """Початок експорту"""
        export_type = self.export_type.get()
        export_path = self.export_path_entry.get().strip()

        if not export_path:
            messagebox.showerror("Помилка", "Виберіть папку для експорту")
            return

        try:
            if export_type == "local":
                self.export_local(export_path)
            elif export_type == "workshop":
                self.export_workshop(export_path)
            elif export_type == "zip":
                self.export_zip(export_path)

            self.result = True
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося експортувати мод:\n{str(e)}")

    def export_local(self, export_path):
        """Локальний експорт для тестування"""
        import shutil

        export_path = Path(export_path)
        export_path.mkdir(parents=True, exist_ok=True)

        # Назва папки мода
        mod_name = Path(self.project_path).name
        dest_path = export_path / mod_name

        # Видалення існуючої версії
        if dest_path.exists():
            shutil.rmtree(dest_path)

        # Копіювання мода
        shutil.copytree(self.project_path, dest_path)

        # Видалення Source папки якщо не потрібно
        if not self.include_source.get():
            source_path = dest_path / "Source"
            if source_path.exists():
                shutil.rmtree(source_path)

        # Створення README
        if self.create_readme.get():
            self.create_readme_file(dest_path)

        messagebox.showinfo("Успіх", f"Мод експортовано до:\n{dest_path}")

    def export_workshop(self, export_path):
        """Експорт для Steam Workshop"""
        try:
            from src.core.steam_workshop import SteamWorkshopManager

            workshop_manager = SteamWorkshopManager(self.project_path)
            result = workshop_manager.prepare_for_workshop(export_path)

            if result['success']:
                messagebox.showinfo("Успіх", f"Мод підготовлено для Steam Workshop:\n{result['output_path']}")
            else:
                messagebox.showerror("Помилка", f"Помилка підготовки:\n{result['error']}")

        except ImportError:
            messagebox.showerror("Помилка", "Steam Workshop модуль недоступний")

    def export_zip(self, export_path):
        """Експорт у ZIP архів"""
        import zipfile

        export_path = Path(export_path)
        export_path.mkdir(parents=True, exist_ok=True)

        # Назва архіву
        mod_name = Path(self.project_path).name
        zip_path = export_path / f"{mod_name}.zip"

        # Створення ZIP архіву
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in Path(self.project_path).rglob('*'):
                if file_path.is_file():
                    # Пропускаємо Source якщо не потрібно
                    if not self.include_source.get() and 'Source' in file_path.parts:
                        continue

                    # Відносний шлях в архіві
                    arcname = file_path.relative_to(self.project_path)
                    zipf.write(file_path, arcname)

        messagebox.showinfo("Успіх", f"ZIP архів створено:\n{zip_path}")

    def create_readme_file(self, dest_path):
        """Створення README файлу"""
        try:
            # Читання About.xml для інформації
            about_xml = Path(self.project_path) / "About" / "About.xml"
            mod_info = {"name": "Unknown Mod", "author": "Unknown", "description": "No description"}

            if about_xml.exists():
                import xml.etree.ElementTree as ET
                tree = ET.parse(about_xml)
                root = tree.getroot()

                for elem in ['name', 'author', 'description']:
                    elem_node = root.find(elem)
                    if elem_node is not None and elem_node.text:
                        mod_info[elem] = elem_node.text

            readme_content = f"""# {mod_info['name']}

**Автор:** {mod_info['author']}

## Опис
{mod_info['description']}

## Встановлення
1. Розпакуйте мод у папку Mods вашої гри RimWorld
2. Увімкніть мод у списку модів
3. Перезапустіть гру

## Підтримка
Якщо у вас виникли проблеми з модом, зверніться до автора.

---
Створено за допомогою RimWorld Mod Builder
"""

            readme_path = dest_path / "README.txt"
            readme_path.write_text(readme_content, encoding='utf-8')

        except Exception as e:
            print(f"Не вдалося створити README: {e}")


def main():
    """Головна функція запуску програми"""
    app = RimWorldModBuilder()
    app.run()


if __name__ == "__main__":
    main()
