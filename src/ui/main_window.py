"""
Головне вікно програми RimWorld Mod Builder
"""

import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QToolBar, QStatusBar,
                             QFileDialog, QMessageBox, QTabWidget, QDialog,
                             QTextEdit, QPushButton)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QKeySequence, QAction, QFont

import sys
import os

# Додаємо шляхи для імпорту
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from ui.file_explorer import FileExplorer
from ui.text_editor import TextEditor
from ui.new_project_dialog import NewProjectDialog
from ui.template_dialog import TemplateDialog
from ui.texture_manager import TextureManager
from ui.settings_dialog import SettingsDialog
from ui.export_dialog import ExportDialog
from ui.preview_system import DefinitionPreview
from core.project_manager import ProjectManager
from utils.logger import get_logger_instance, LogViewerDialog, StatusBarLogger
from utils.compatibility_checker import CompatibilityChecker
from utils.performance import get_profiler, get_thread_pool, MemoryMonitor, profile


class MainWindow(QMainWindow):
    """Головне вікно програми"""

    def __init__(self):
        super().__init__()

        # Ініціалізуємо логування
        self.logger_instance = get_logger_instance()
        self.logger = self.logger_instance.get_logger()

        self.project_manager = ProjectManager()
        self.settings = QSettings()

        self.init_ui()
        self.create_menus()
        self.create_toolbars()
        self.create_status_bar()
        self.setup_logging()
        self.restore_settings()

        self.logger.info("Головне вікно ініціалізовано")

    def init_ui(self):
        """Ініціалізація інтерфейсу користувача"""
        self.setWindowTitle("RimWorld Mod Builder")
        self.setMinimumSize(1200, 800)

        # Центральний віджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основний макет
        main_layout = QHBoxLayout(central_widget)

        # Створюємо сплітер для розділення областей
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Файловий експлорер (ліва панель)
        self.file_explorer = FileExplorer()
        self.file_explorer.setMaximumWidth(300)
        self.file_explorer.setMinimumWidth(200)

        # Права панель з вкладками
        right_panel = QTabWidget()

        # Вкладка редактора
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        right_panel.addTab(self.editor_tabs, "Редактор")

        # Вкладка менеджера текстур
        self.texture_manager = TextureManager()
        right_panel.addTab(self.texture_manager, "Текстури")

        # Вкладка попереднього перегляду
        self.preview_system = DefinitionPreview()
        right_panel.addTab(self.preview_system, "Попередній перегляд")

        # Система перевірки сумісності
        self.compatibility_checker = CompatibilityChecker()

        # Система моніторингу продуктивності
        self.memory_monitor = MemoryMonitor()
        self.memory_monitor.memory_warning.connect(self.on_memory_warning)
        self.memory_monitor.memory_critical.connect(self.on_memory_critical)

        # Запускаємо пул потоків
        self.thread_pool = get_thread_pool()
        self.thread_pool.start()

        # Додаємо віджети до сплітера
        splitter.addWidget(self.file_explorer)
        splitter.addWidget(right_panel)

        # Встановлюємо пропорції сплітера
        splitter.setSizes([250, 950])

        main_layout.addWidget(splitter)

        # Підключаємо сигнали
        self.file_explorer.file_opened.connect(self.open_file_in_editor)

    def create_menus(self):
        """Створення меню"""
        menubar = self.menuBar()
        if not menubar:
            return

        # Меню "Файл"
        file_menu = menubar.addMenu("&Файл")
        if not file_menu:
            return

        # Новий проєкт
        new_project_action = QAction("&Новий проєкт мода", self)
        new_project_action.setShortcut(QKeySequence.StandardKey.New)
        new_project_action.setStatusTip("Створити новий проєкт мода")
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)

        # Відкрити проєкт
        open_project_action = QAction("&Відкрити проєкт", self)
        open_project_action.setShortcut(QKeySequence.StandardKey.Open)
        open_project_action.setStatusTip("Відкрити існуючий проєкт мода")
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)

        file_menu.addSeparator()

        # Зберегти
        save_action = QAction("&Зберегти", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip("Зберегти поточний файл")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # Шаблони
        templates_action = QAction("&Шаблони дефініцій", self)
        templates_action.setStatusTip("Відкрити діалог шаблонів")
        templates_action.triggered.connect(self.open_templates)
        file_menu.addAction(templates_action)

        file_menu.addSeparator()

        # Експорт мода
        export_action = QAction("&Експорт мода", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Експортувати мод для використання")
        export_action.triggered.connect(self.export_mod)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # Вихід
        exit_action = QAction("&Вихід", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Вийти з програми")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Редагування"
        edit_menu = menubar.addMenu("&Редагування")
        if edit_menu:
            # Скасувати
            undo_action = QAction("&Скасувати", self)
            undo_action.setShortcut(QKeySequence.StandardKey.Undo)
            undo_action.setStatusTip("Скасувати останню дію")
            undo_action.triggered.connect(self.undo_action)
            edit_menu.addAction(undo_action)

            # Повторити
            redo_action = QAction("&Повторити", self)
            redo_action.setShortcut(QKeySequence.StandardKey.Redo)
            redo_action.setStatusTip("Повторити скасовану дію")
            redo_action.triggered.connect(self.redo_action)
            edit_menu.addAction(redo_action)

            edit_menu.addSeparator()

            # Знайти та замінити
            find_replace_action = QAction("&Знайти та замінити", self)
            find_replace_action.setShortcut("Ctrl+H")
            find_replace_action.setStatusTip("Відкрити діалог пошуку та заміни")
            find_replace_action.triggered.connect(self.show_find_replace)
            edit_menu.addAction(find_replace_action)

        # Меню "Вигляд"
        view_menu = menubar.addMenu("&Вигляд")

        # Перегляд логів
        logs_action = QAction("&Логи програми", self)
        logs_action.setStatusTip("Переглянути логи програми")
        logs_action.triggered.connect(self.show_logs)
        view_menu.addAction(logs_action)

        # Меню "Інструменти"
        tools_menu = menubar.addMenu("&Інструменти")

        # Перевірка сумісності
        compatibility_action = QAction("&Перевірка сумісності", self)
        compatibility_action.setStatusTip("Перевірити сумісність мода з RimWorld")
        compatibility_action.triggered.connect(self.check_compatibility)
        tools_menu.addAction(compatibility_action)

        tools_menu.addSeparator()

        # Налаштування
        settings_action = QAction("&Налаштування", self)
        settings_action.setStatusTip("Відкрити налаштування програми")
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)

        tools_menu.addSeparator()

        # Статистика продуктивності
        performance_action = QAction("&Статистика продуктивності", self)
        performance_action.setStatusTip("Переглянути статистику продуктивності")
        performance_action.triggered.connect(self.show_performance_stats)
        tools_menu.addAction(performance_action)

        # Меню "C# Розробка"
        csharp_menu = menubar.addMenu("&C# Розробка")

        # Менеджер C# проєктів
        csharp_manager_action = QAction("&Менеджер C# проєктів", self)
        csharp_manager_action.setStatusTip("Відкрити менеджер C# проєктів")
        csharp_manager_action.triggered.connect(self.open_csharp_manager)
        csharp_menu.addAction(csharp_manager_action)

        # Компілятор C#
        csharp_compiler_action = QAction("&Компілятор C#", self)
        csharp_compiler_action.setStatusTip("Відкрити компілятор C# проєктів")
        csharp_compiler_action.triggered.connect(self.open_csharp_compiler)
        csharp_menu.addAction(csharp_compiler_action)

        csharp_menu.addSeparator()

        # Статус .NET середовища
        dotnet_status_action = QAction("&Статус .NET середовища", self)
        dotnet_status_action.setStatusTip("Перевірити статус .NET середовища")
        dotnet_status_action.triggered.connect(self.check_dotnet_status)
        csharp_menu.addAction(dotnet_status_action)

        # Меню "Допомога"
        help_menu = menubar.addMenu("&Допомога")

        # Про програму
        about_action = QAction("&Про програму", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbars(self):
        """Створення панелей інструментів"""
        toolbar = QToolBar("Основна панель")
        self.addToolBar(toolbar)

        # Кнопки швидкого доступу
        toolbar.addAction("Новий проєкт")
        toolbar.addAction("Відкрити")
        toolbar.addAction("Зберегти")
        toolbar.addSeparator()
        toolbar.addAction("Експорт мода")

    def create_status_bar(self):
        """Створення статусної панелі"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

    @profile
    def new_project(self):
        """Створення нового проєкту мода"""
        self.logger.info("Початок створення нового проєкту")

        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            project_path, mod_info = dialog.get_project_data()

            # Перевіряємо, що project_path не None
            if not project_path:
                QMessageBox.warning(
                    self, "Помилка",
                    "Не вказано шлях до проєкту"
                )
                return

            try:
                # Створюємо проєкт через менеджер
                if self.project_manager.create_new_project(project_path, mod_info):
                    # Відкриваємо проєкт у файловому експлорері
                    self.file_explorer.set_root_path(project_path)

                    # Оновлюємо менеджер текстур
                    self.texture_manager.set_project_path(project_path)

                    self.status_bar.showMessage(f"Створено новий проєкт: {mod_info['name']}")
                    self.logger.info(f"Проєкт '{mod_info['name']}' створено успішно в {project_path}")

                    # Відкриваємо About.xml для редагування
                    about_path = os.path.join(project_path, "About", "About.xml")
                    if os.path.exists(about_path):
                        self.open_file_in_editor(about_path)
                else:
                    self.logger.error("Не вдалося створити проєкт")
                    QMessageBox.critical(
                        self, "Помилка",
                        "Не вдалося створити проєкт. Перевірте права доступу до папки."
                    )
            except Exception as e:
                self.logger.error(f"Помилка створення проєкту: {e}")
                QMessageBox.critical(
                    self, "Помилка",
                    f"Помилка створення проєкту:\n{e}"
                )

    def open_project(self):
        """Відкриття існуючого проєкту"""
        folder = QFileDialog.getExistingDirectory(self, "Оберіть папку проєкту мода")
        if folder:
            self.file_explorer.set_root_path(folder)
            self.texture_manager.set_project_path(folder)
            self.status_bar.showMessage(f"Відкрито проєкт: {folder}")

    def save_file(self):
        """Збереження поточного файлу"""
        current_tab = self.editor_tabs.currentWidget()
        if isinstance(current_tab, TextEditor):
            current_tab.save_file()

    def open_templates(self):
        """Відкриття діалогу шаблонів"""
        dialog = TemplateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template_content = dialog.get_selected_template()
            template_name = dialog.get_template_name()

            if template_content and template_name:
                # Створюємо новий файл з шаблоном
                editor = TextEditor()
                editor.setPlainText(template_content)

                tab_name = f"Новий {template_name}"
                self.editor_tabs.addTab(editor, tab_name)
                self.editor_tabs.setCurrentWidget(editor)

    def export_mod(self):
        """Експорт мода"""
        if not self.project_manager.current_project_path:
            QMessageBox.warning(
                self, "Помилка",
                "Спочатку відкрийте або створіть проєкт мода"
            )
            return

        dialog = ExportDialog(self.project_manager, self)
        dialog.exec()

    def check_compatibility(self):
        """Перевірка сумісності мода"""
        if not self.project_manager.current_project_path:
            # Якщо проєкт не відкритий, пропонуємо вибрати папку
            folder = QFileDialog.getExistingDirectory(
                self, "Оберіть папку мода для перевірки сумісності"
            )
            if not folder:
                return
            mod_path = folder
        else:
            mod_path = self.project_manager.current_project_path

        try:
            self.logger.info(f"Початок перевірки сумісності для {mod_path}")

            # Виконуємо перевірку
            report = self.compatibility_checker.get_compatibility_report(mod_path)

            # Показуємо результат
            self.show_compatibility_report(report)

        except Exception as e:
            self.logger.error(f"Помилка перевірки сумісності: {e}")
            QMessageBox.critical(
                self, "Помилка",
                f"Помилка перевірки сумісності:\n{e}"
            )

    def show_compatibility_report(self, report: str):
        """Показати звіт про сумісність"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Звіт про сумісність мода")
        dialog.setModal(True)
        dialog.resize(600, 500)

        layout = QVBoxLayout(dialog)

        # Текстове поле для звіту
        report_text = QTextEdit()
        report_text.setReadOnly(True)
        report_text.setFont(QFont("Consolas", 10))
        report_text.setPlainText(report)
        layout.addWidget(report_text)

        # Кнопки
        buttons_layout = QHBoxLayout()

        save_button = QPushButton("Зберегти звіт")
        save_button.clicked.connect(lambda: self.save_compatibility_report(report))

        close_button = QPushButton("Закрити")
        close_button.clicked.connect(dialog.accept)

        buttons_layout.addWidget(save_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_button)

        layout.addLayout(buttons_layout)

        dialog.exec()

    def save_compatibility_report(self, report: str):
        """Зберегти звіт про сумісність"""
        from datetime import datetime

        filename, _ = QFileDialog.getSaveFileName(
            self, "Зберегти звіт про сумісність",
            f"compatibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text files (*.txt);;All files (*.*)"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)

                self.logger.info(f"Звіт про сумісність збережено: {filename}")
                QMessageBox.information(
                    self, "Успіх",
                    f"Звіт збережено у файл:\n{filename}"
                )
            except Exception as e:
                self.logger.error(f"Помилка збереження звіту: {e}")
                QMessageBox.critical(
                    self, "Помилка",
                    f"Не вдалося зберегти звіт:\n{e}"
                )

    def on_memory_warning(self, memory_mb: float):
        """Обробка попередження про пам'ять"""
        self.status_bar.showMessage(
            f"⚠️ Високе використання пам'яті: {memory_mb:.1f}MB", 10000
        )

    def on_memory_critical(self, memory_mb: float):
        """Обробка критичного використання пам'яті"""
        QMessageBox.warning(
            self, "Критичне використання пам'яті",
            f"Програма використовує {memory_mb:.1f}MB пам'яті.\n"
            "Рекомендується закрити деякі файли або перезапустити програму."
        )

    def show_performance_stats(self):
        """Показати статистику продуктивності"""
        profiler = get_profiler()

        dialog = QDialog(self)
        dialog.setWindowTitle("Статистика продуктивності")
        dialog.setModal(True)
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        # Вкладки для різних типів статистики
        tabs = QTabWidget()

        # Вкладка методів
        methods_tab = QWidget()
        methods_layout = QVBoxLayout(methods_tab)

        methods_text = QTextEdit()
        methods_text.setReadOnly(True)
        methods_text.setFont(QFont("Consolas", 10))

        # Топ методів за часом виконання
        top_methods = profiler.get_top_methods(20, 'total_time')
        methods_content = "=== ТОП МЕТОДІВ ЗА ЧАСОМ ВИКОНАННЯ ===\n\n"

        for method_data in top_methods:
            methods_content += f"Метод: {method_data['method']}\n"
            methods_content += f"  Викликів: {method_data['calls']}\n"
            methods_content += f"  Загальний час: {method_data['total_time']:.3f}s\n"
            methods_content += f"  Середній час: {method_data['avg_time']:.3f}s\n"
            methods_content += f"  Мін/Макс: {method_data['min_time']:.3f}s / {method_data['max_time']:.3f}s\n\n"

        methods_text.setPlainText(methods_content)
        methods_layout.addWidget(methods_text)
        tabs.addTab(methods_tab, "Методи")

        # Вкладка пам'яті
        memory_tab = QWidget()
        memory_layout = QVBoxLayout(memory_tab)

        memory_text = QTextEdit()
        memory_text.setReadOnly(True)
        memory_text.setFont(QFont("Consolas", 10))

        memory_info = self.memory_monitor.get_memory_info()
        memory_content = "=== ІНФОРМАЦІЯ ПРО ПАМ'ЯТЬ ===\n\n"

        if memory_info:
            memory_content += f"Фізична пам'ять (RSS): {memory_info.get('rss_mb', 0):.1f} MB\n"
            memory_content += f"Віртуальна пам'ять (VMS): {memory_info.get('vms_mb', 0):.1f} MB\n"
            memory_content += f"Відсоток від системної пам'яті: {memory_info.get('percent', 0):.1f}%\n"
            memory_content += f"Доступна системна пам'ять: {memory_info.get('available_mb', 0):.1f} MB\n"
        else:
            memory_content += "Інформація про пам'ять недоступна\n"

        memory_text.setPlainText(memory_content)
        memory_layout.addWidget(memory_text)
        tabs.addTab(memory_tab, "Пам'ять")

        layout.addWidget(tabs)

        # Кнопки
        buttons_layout = QHBoxLayout()

        reset_button = QPushButton("Скинути статистику")
        reset_button.clicked.connect(lambda: profiler.reset_stats())

        close_button = QPushButton("Закрити")
        close_button.clicked.connect(dialog.accept)

        buttons_layout.addWidget(reset_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_button)

        layout.addLayout(buttons_layout)

        dialog.exec()

    def setup_logging(self):
        """Налаштування логування"""
        # Ініціалізуємо логер для статусної панелі
        self.status_logger = StatusBarLogger(self.status_bar)

        # Підключаємо сигнали логування
        signal_emitter = self.logger_instance.get_signal_emitter()
        signal_emitter.log_message.connect(self.handle_log_message)

    def handle_log_message(self, level, message):
        """Обробка лог-повідомлень"""
        import logging

        # Показуємо важливі повідомлення в статусній панелі
        if level >= logging.WARNING:
            # Витягуємо тільки текст повідомлення без timestamp
            clean_message = message.split(" - ")[-1] if " - " in message else message
            self.status_logger.show_message(clean_message, level)

    def show_logs(self):
        """Показати діалог логів"""
        if not hasattr(self, 'log_dialog') or not self.log_dialog:
            self.log_dialog = LogViewerDialog(self.logger_instance, self)
        self.log_dialog.show()
        self.log_dialog.raise_()
        self.log_dialog.activateWindow()

    def open_settings(self):
        """Відкриття діалогу налаштувань"""
        try:
            dialog = SettingsDialog(self)
            # Перевіряємо наявність сигналу перед підключенням
            if hasattr(dialog, 'settings_changed'):
                dialog.settings_changed.connect(self.apply_settings)
            else:
                self.logger.warning("SettingsDialog не має сигналу settings_changed")
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Помилка відкриття налаштувань: {e}")
            QMessageBox.critical(
                self, "Помилка",
                f"Не вдалося відкрити налаштування:\n{e}"
            )

    def apply_settings(self):
        """Застосування налаштувань до інтерфейсу"""
        settings = QSettings()

        # Застосовуємо налаштування шрифту до всіх редакторів
        font_family = settings.value("editor/font_family", "Consolas")
        font_size = settings.value("editor/font_size", 11, int)
        editor_font = QFont(font_family, font_size)

        for i in range(self.editor_tabs.count()):
            widget = self.editor_tabs.widget(i)
            if isinstance(widget, TextEditor):
                widget.setFont(editor_font)

        # Застосовуємо налаштування інтерфейсу
        show_status_bar = settings.value("interface/show_status_bar", True, bool)
        self.status_bar.setVisible(show_status_bar)

        show_toolbar = settings.value("interface/show_toolbar", True, bool)
        for toolbar in self.findChildren(QToolBar):
            toolbar.setVisible(show_toolbar)

        # Оновлюємо розмір мініатюр в менеджері текстур
        thumbnail_size = settings.value("texture/thumbnail_size", 64, int)
        if hasattr(self.texture_manager, 'set_thumbnail_size'):
            self.texture_manager.set_thumbnail_size(thumbnail_size)

    @profile
    def open_file_in_editor(self, file_path):
        """Відкриття файлу в редакторі"""
        try:
            # Перевіряємо, чи файл існує
            if not os.path.exists(file_path):
                self.logger.error(f"Файл не існує: {file_path}")
                QMessageBox.warning(
                    self, "Файл не знайдено",
                    f"Файл не існує:\n{file_path}"
                )
                return

            # Перевіряємо, чи файл вже відкритий
            for i in range(self.editor_tabs.count()):
                tab = self.editor_tabs.widget(i)
                if isinstance(tab, TextEditor) and tab.file_path == file_path:
                    self.editor_tabs.setCurrentIndex(i)
                    return

            # Створюємо новий редактор
            editor = TextEditor(file_path)
            tab_name = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
            self.editor_tabs.addTab(editor, tab_name)
            self.editor_tabs.setCurrentWidget(editor)

            # Підключаємо сигнал зміни тексту для попереднього перегляду
            try:
                editor.content_changed.connect(lambda: self.update_preview(editor))
                # Оновлюємо попередній перегляд
                self.update_preview(editor)
            except Exception as e:
                self.logger.warning(f"Помилка підключення попереднього перегляду: {e}")

        except Exception as e:
            self.logger.error(f"Помилка відкриття файлу {file_path}: {e}")
            QMessageBox.critical(
                self, "Помилка",
                f"Не вдалося відкрити файл:\n{e}"
            )

    def update_preview(self, editor):
        """Оновлення попереднього перегляду"""
        if not isinstance(editor, TextEditor):
            return

        # Перевіряємо, чи це XML файл
        if editor.file_path and editor.file_path.lower().endswith('.xml'):
            try:
                xml_content = editor.toPlainText()
                if xml_content.strip():
                    self.preview_system.preview_definition(xml_content, editor.file_path)
                else:
                    self.preview_system.clear_preview()
            except Exception as e:
                self.logger.warning(f"Помилка оновлення попереднього перегляду: {e}")
                self.preview_system.show_error(str(e))

    def close_tab(self, index):
        """Закриття вкладки"""
        widget = self.editor_tabs.widget(index)
        if isinstance(widget, TextEditor) and widget.is_modified():
            reply = QMessageBox.question(
                self, "Зберегти зміни?",
                f"Файл {widget.file_path} був змінений. Зберегти зміни?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Save:
                widget.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.editor_tabs.removeTab(index)

    def restore_settings(self):
        """Відновлення налаштувань"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def undo_action(self):
        """Скасувати останню дію в поточному редакторі"""
        current_tab = self.editor_tabs.currentWidget()
        if isinstance(current_tab, TextEditor):
            current_tab.undo()
        else:
            self.status_bar.showMessage("Немає активного редактора для скасування дії", 3000)

    def redo_action(self):
        """Повторити скасовану дію в поточному редакторі"""
        current_tab = self.editor_tabs.currentWidget()
        if isinstance(current_tab, TextEditor):
            current_tab.redo()
        else:
            self.status_bar.showMessage("Немає активного редактора для повтору дії", 3000)

    def show_find_replace(self):
        """Показати діалог пошуку та заміни"""
        current_tab = self.editor_tabs.currentWidget()
        if isinstance(current_tab, TextEditor):
            try:
                from utils.find_replace_dialog import FindReplaceDialog
                dialog = FindReplaceDialog(current_tab, self)
                dialog.show()
            except ImportError as e:
                self.logger.error(f"Не вдалося імпортувати діалог пошуку: {e}")
                QMessageBox.warning(
                    self, "Помилка",
                    "Діалог пошуку та заміни недоступний"
                )
        else:
            self.status_bar.showMessage("Немає активного редактора для пошуку", 3000)

    def show_about(self):
        """Показати діалог про програму"""
        QMessageBox.about(
            self, "Про RimWorld Mod Builder",
            "<h3>RimWorld Mod Builder</h3>"
            "<p>Професійний інструмент для створення модів RimWorld</p>"
            "<p><b>Версія:</b> 1.0.0</p>"
            "<p><b>Автор:</b> RimWorld Mod Builder Team</p>"
            "<p><b>Опис:</b> Повнофункціональний редактор для створення, "
            "редагування та експорту модів для гри RimWorld.</p>"
            "<p><b>Функції:</b></p>"
            "<ul>"
            "<li>Створення та управління проєктами модів</li>"
            "<li>Редактор з підсвіткою синтаксису XML</li>"
            "<li>Менеджер текстур з підтримкою різних форматів</li>"
            "<li>Система шаблонів для швидкого створення дефініцій</li>"
            "<li>Перевірка сумісності з різними версіями RimWorld</li>"
            "<li>Експорт модів для Steam Workshop</li>"
            "</ul>"
            "<p>© 2024 RimWorld Mod Builder. Всі права захищені.</p>"
        )

    def closeEvent(self, event):
        """Обробка закриття програми"""
        # Зупиняємо пул потоків
        self.thread_pool.stop()
        # Зберігаємо налаштування
        self.settings.setValue("geometry", self.saveGeometry())

        # Перевіряємо незбережені файли
        for i in range(self.editor_tabs.count()):
            widget = self.editor_tabs.widget(i)
            if isinstance(widget, TextEditor) and widget.is_modified():
                reply = QMessageBox.question(
                    self, "Зберегти зміни?",
                    "Є незбережені зміни. Зберегти перед виходом?",
                    QMessageBox.StandardButton.Save |
                    QMessageBox.StandardButton.Discard |
                    QMessageBox.StandardButton.Cancel
                )

                if reply == QMessageBox.StandardButton.Save:
                    widget.save_file()
                elif reply == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return

        event.accept()

    def open_csharp_manager(self):
        """Відкриття менеджера C# проєктів"""
        try:
            # Імпорт CustomTkinter компонентів
            import customtkinter as ctk
            from ui.csharp_project_manager import CSharpProjectManager

            # Створення нового вікна CustomTkinter
            csharp_window = ctk.CTkToplevel()
            csharp_window.title("🔧 Менеджер C# проєктів")
            csharp_window.geometry("1000x700")

            # Встановлення іконки та властивостей
            csharp_window.transient(self)
            csharp_window.grab_set()

            # Створення менеджера
            manager = CSharpProjectManager(csharp_window)
            manager.pack(fill="both", expand=True, padx=10, pady=10)

            self.logger.info("Відкрито менеджер C# проєктів")

        except ImportError as e:
            self.logger.error(f"Помилка імпорту CustomTkinter: {e}")
            QMessageBox.critical(
                self, "Помилка",
                f"Не вдалося відкрити менеджер C# проєктів.\n"
                f"Переконайтеся, що CustomTkinter встановлено:\n{e}"
            )
        except Exception as e:
            self.logger.error(f"Помилка відкриття менеджера C#: {e}")
            QMessageBox.critical(
                self, "Помилка",
                f"Не вдалося відкрити менеджер C# проєктів:\n{e}"
            )

    def open_csharp_compiler(self):
        """Відкриття компілятора C#"""
        try:
            # Імпорт CustomTkinter компонентів
            import customtkinter as ctk
            from ui.csharp_compiler_widget import CSharpCompilerWidget

            # Створення нового вікна CustomTkinter
            compiler_window = ctk.CTkToplevel()
            compiler_window.title("🔨 Компілятор C#")
            compiler_window.geometry("1200x800")

            # Встановлення іконки та властивостей
            compiler_window.transient(self)
            compiler_window.grab_set()

            # Створення компілятора
            compiler = CSharpCompilerWidget(compiler_window)
            compiler.pack(fill="both", expand=True, padx=10, pady=10)

            self.logger.info("Відкрито компілятор C#")

        except ImportError as e:
            self.logger.error(f"Помилка імпорту CustomTkinter: {e}")
            QMessageBox.critical(
                self, "Помилка",
                f"Не вдалося відкрити компілятор C#.\n"
                f"Переконайтеся, що CustomTkinter встановлено:\n{e}"
            )
        except Exception as e:
            self.logger.error(f"Помилка відкриття компілятора C#: {e}")
            QMessageBox.critical(
                self, "Помилка",
                f"Не вдалося відкрити компілятор C#:\n{e}"
            )

    def check_dotnet_status(self):
        """Перевірка статусу .NET середовища"""
        try:
            from core.dotnet_integration import get_dotnet_environment

            dotnet_env = get_dotnet_environment()
            info = dotnet_env.get_environment_info()

            # Створення діалогу статусу
            dialog = QDialog(self)
            dialog.setWindowTitle("Статус .NET середовища")
            dialog.setModal(True)
            dialog.resize(600, 400)

            layout = QVBoxLayout(dialog)

            # Текстове поле для статусу
            status_text = QTextEdit()
            status_text.setReadOnly(True)
            status_text.setFont(QFont("Consolas", 10))

            # Формування тексту статусу
            status_content = "=== СТАТУС .NET СЕРЕДОВИЩА ===\n\n"

            if info["is_ready"]:
                status_content += "✅ .NET середовище готове до роботи\n\n"
            else:
                status_content += "❌ .NET середовище недоступне\n\n"

            status_content += f"dotnet CLI: {'✅ Доступний' if info['dotnet_available'] else '❌ Недоступний'}\n"
            if info["dotnet_path"]:
                status_content += f"  Шлях: {info['dotnet_path']}\n"

            status_content += f"MSBuild: {'✅ Доступний' if info['msbuild_available'] else '❌ Недоступний'}\n"
            if info["msbuild_path"]:
                status_content += f"  Шлях: {info['msbuild_path']}\n"

            status_content += f"\nSDK версії: {', '.join(info['sdk_versions']) if info['sdk_versions'] else 'Не знайдено'}\n"
            status_content += f"Framework версії: {', '.join(info['framework_versions']) if info['framework_versions'] else 'Не знайдено'}\n"

            if not info["is_ready"]:
                status_content += "\n=== РЕКОМЕНДАЦІЇ ===\n"
                status_content += "1. Встановіть Visual Studio або Visual Studio Build Tools\n"
                status_content += "2. Встановіть .NET Framework 4.7.2 або новіший\n"
                status_content += "3. Перезапустіть програму після встановлення\n"

            status_text.setPlainText(status_content)
            layout.addWidget(status_text)

            # Кнопка закриття
            close_button = QPushButton("Закрити")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)

            dialog.exec()

        except Exception as e:
            self.logger.error(f"Помилка перевірки .NET статусу: {e}")
            QMessageBox.critical(
                self, "Помилка",
                f"Не вдалося перевірити статус .NET середовища:\n{e}"
            )
