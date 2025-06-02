"""
Діалог налаштувань програми
"""

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QCheckBox, QComboBox, QPushButton,
                             QFileDialog, QMessageBox, QLabel, QSpinBox,
                             QGroupBox, QTabWidget, QWidget)
from PyQt6.QtCore import Qt, QSettings, pyqtSignal


class SettingsDialog(QDialog):
    """Діалог налаштувань програми"""

    # Сигнал для повідомлення про зміну налаштувань
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Ініціалізація інтерфейсу"""
        self.setWindowTitle("Налаштування")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Створюємо вкладки
        tab_widget = QTabWidget()

        # Вкладка "Загальні"
        general_tab = self.create_general_tab()
        tab_widget.addTab(general_tab, "Загальні")

        # Вкладка "Редактор"
        editor_tab = self.create_editor_tab()
        tab_widget.addTab(editor_tab, "Редактор")

        # Вкладка "RimWorld"
        rimworld_tab = self.create_rimworld_tab()
        tab_widget.addTab(rimworld_tab, "RimWorld")

        layout.addWidget(tab_widget)

        # Кнопки
        buttons_layout = QHBoxLayout()

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_settings)

        self.cancel_button = QPushButton("Скасувати")
        self.cancel_button.clicked.connect(self.reject)

        self.apply_button = QPushButton("Застосувати")
        self.apply_button.clicked.connect(self.apply_settings)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.apply_button)

        layout.addLayout(buttons_layout)

    def create_general_tab(self):
        """Створення вкладки загальних налаштувань"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Група "Інтерфейс"
        interface_group = QGroupBox("Інтерфейс")
        interface_layout = QFormLayout(interface_group)

        # Тема
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Світла", "Темна", "Системна"])
        interface_layout.addRow("Тема:", self.theme_combo)

        # Мова
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Українська", "English"])
        interface_layout.addRow("Мова:", self.language_combo)

        # Автозбереження
        self.autosave_checkbox = QCheckBox("Увімкнути автозбереження")
        interface_layout.addRow(self.autosave_checkbox)

        # Інтервал автозбереження
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(1, 60)
        self.autosave_interval.setSuffix(" хв")
        interface_layout.addRow("Інтервал автозбереження:", self.autosave_interval)

        layout.addWidget(interface_group)

        # Група "Проєкти"
        projects_group = QGroupBox("Проєкти")
        projects_layout = QFormLayout(projects_group)

        # Папка проєктів за замовчуванням
        projects_folder_layout = QHBoxLayout()
        self.projects_folder_edit = QLineEdit()
        self.browse_projects_button = QPushButton("Огляд...")
        self.browse_projects_button.clicked.connect(self.browse_projects_folder)

        projects_folder_layout.addWidget(self.projects_folder_edit)
        projects_folder_layout.addWidget(self.browse_projects_button)

        projects_layout.addRow("Папка проєктів:", projects_folder_layout)

        # Відкривати останній проєкт
        self.open_last_project_checkbox = QCheckBox("Відкривати останній проєкт при запуску")
        projects_layout.addRow(self.open_last_project_checkbox)

        layout.addWidget(projects_group)
        layout.addStretch()

        return widget

    def create_editor_tab(self):
        """Створення вкладки налаштувань редактора"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Група "Шрифт"
        font_group = QGroupBox("Шрифт")
        font_layout = QFormLayout(font_group)

        # Назва шрифту
        self.font_family_combo = QComboBox()
        # Додаємо fallback шрифти для кращої сумісності
        available_fonts = self.get_available_fonts()
        self.font_family_combo.addItems(available_fonts)
        font_layout.addRow("Шрифт:", self.font_family_combo)

        # Розмір шрифту
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 24)
        font_layout.addRow("Розмір:", self.font_size_spinbox)

        layout.addWidget(font_group)

        # Група "Редагування"
        editing_group = QGroupBox("Редагування")
        editing_layout = QFormLayout(editing_group)

        # Розмір табуляції
        self.tab_size_spinbox = QSpinBox()
        self.tab_size_spinbox.setRange(2, 8)
        editing_layout.addRow("Розмір табуляції:", self.tab_size_spinbox)

        # Показувати номери рядків
        self.show_line_numbers_checkbox = QCheckBox("Показувати номери рядків")
        editing_layout.addRow(self.show_line_numbers_checkbox)

        # Підсвітка поточного рядка
        self.highlight_current_line_checkbox = QCheckBox("Підсвічувати поточний рядок")
        editing_layout.addRow(self.highlight_current_line_checkbox)

        # Автодоповнення
        self.auto_completion_checkbox = QCheckBox("Увімкнути автодоповнення")
        editing_layout.addRow(self.auto_completion_checkbox)

        layout.addWidget(editing_group)

        # Група "XML"
        xml_group = QGroupBox("XML")
        xml_layout = QFormLayout(xml_group)

        # Валідація в реальному часі
        self.realtime_validation_checkbox = QCheckBox("Валідація в реальному часі")
        xml_layout.addRow(self.realtime_validation_checkbox)

        # Автоформатування
        self.auto_format_checkbox = QCheckBox("Автоматичне форматування")
        xml_layout.addRow(self.auto_format_checkbox)

        layout.addWidget(xml_group)
        layout.addStretch()

        return widget

    def create_rimworld_tab(self):
        """Створення вкладки налаштувань RimWorld"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Група "Шляхи"
        paths_group = QGroupBox("Шляхи")
        paths_layout = QFormLayout(paths_group)

        # Папка гри
        game_folder_layout = QHBoxLayout()
        self.game_folder_edit = QLineEdit()
        self.browse_game_button = QPushButton("Огляд...")
        self.browse_game_button.clicked.connect(self.browse_game_folder)

        game_folder_layout.addWidget(self.game_folder_edit)
        game_folder_layout.addWidget(self.browse_game_button)

        paths_layout.addRow("Папка RimWorld:", game_folder_layout)

        # Папка модів
        mods_folder_layout = QHBoxLayout()
        self.mods_folder_edit = QLineEdit()
        self.browse_mods_button = QPushButton("Огляд...")
        self.browse_mods_button.clicked.connect(self.browse_mods_folder)

        mods_folder_layout.addWidget(self.mods_folder_edit)
        mods_folder_layout.addWidget(self.browse_mods_button)

        paths_layout.addRow("Папка модів:", mods_folder_layout)

        layout.addWidget(paths_group)

        # Група "Експорт"
        export_group = QGroupBox("Експорт")
        export_layout = QFormLayout(export_group)

        # Автоматично копіювати в папку модів
        self.auto_copy_checkbox = QCheckBox("Автоматично копіювати в папку модів")
        export_layout.addRow(self.auto_copy_checkbox)

        # Стискати текстури
        self.compress_textures_checkbox = QCheckBox("Стискати текстури при експорті")
        export_layout.addRow(self.compress_textures_checkbox)

        layout.addWidget(export_group)
        layout.addStretch()

        return widget

    def get_available_fonts(self):
        """Отримання списку доступних моноширинних шрифтів"""
        try:
            from PyQt6.QtGui import QFontDatabase

            # Пріоритетні шрифти для програмування
            preferred_fonts = [
                "Consolas",
                "Courier New",
                "Monaco",
                "Source Code Pro",
                "DejaVu Sans Mono",
                "Liberation Mono",
                "Ubuntu Mono",
                "Fira Code",
                "JetBrains Mono"
            ]

            # Fallback шрифти для Windows
            fallback_fonts = [
                "Lucida Console",
                "MS Gothic",
                "Courier",
                "monospace"  # Загальний моноширинний шрифт
            ]

            try:
                font_db = QFontDatabase()
                available_fonts = []

                # Перевіряємо пріоритетні шрифти
                for font in preferred_fonts:
                    try:
                        if font_db.hasFamily(font):
                            available_fonts.append(font)
                    except:
                        continue

                # Додаємо fallback шрифти якщо потрібно
                if len(available_fonts) < 3:
                    for font in fallback_fonts:
                        try:
                            if font_db.hasFamily(font) and font not in available_fonts:
                                available_fonts.append(font)
                        except:
                            continue

                # Якщо нічого не знайдено, додаємо системний моноширинний
                if not available_fonts:
                    available_fonts = ["monospace", "Courier New", "Courier"]

                return available_fonts

            except Exception as e:
                # Якщо QFontDatabase не працює, повертаємо базовий список
                print(f"Помилка QFontDatabase: {e}")
                return ["Courier New", "Consolas", "Monaco", "monospace"]

        except ImportError:
            # Якщо PyQt6 недоступний
            return ["Courier New", "Consolas", "Monaco"]

    def get_default_font(self):
        """Отримання шрифту за замовчуванням"""
        available_fonts = self.get_available_fonts()
        if available_fonts:
            return available_fonts[0]
        return "Courier New"  # Останній fallback

    def browse_projects_folder(self):
        """Вибір папки проєктів"""
        folder = QFileDialog.getExistingDirectory(self, "Оберіть папку для проєктів")
        if folder:
            self.projects_folder_edit.setText(folder)

    def browse_game_folder(self):
        """Вибір папки гри"""
        folder = QFileDialog.getExistingDirectory(self, "Оберіть папку RimWorld")
        if folder:
            self.game_folder_edit.setText(folder)

    def browse_mods_folder(self):
        """Вибір папки модів"""
        folder = QFileDialog.getExistingDirectory(self, "Оберіть папку модів")
        if folder:
            self.mods_folder_edit.setText(folder)

    def load_settings(self):
        """Завантаження налаштувань"""
        # Загальні
        self.theme_combo.setCurrentText(self.settings.value("theme", "Світла"))
        self.language_combo.setCurrentText(self.settings.value("language", "Українська"))
        self.autosave_checkbox.setChecked(self.settings.value("autosave", True, type=bool))
        self.autosave_interval.setValue(self.settings.value("autosave_interval", 5, type=int))

        # Проєкти
        default_projects_folder = os.path.join(os.path.expanduser("~"), "RimWorldMods")
        self.projects_folder_edit.setText(self.settings.value("projects_folder", default_projects_folder))
        self.open_last_project_checkbox.setChecked(self.settings.value("open_last_project", False, type=bool))

        # Редактор
        default_font = self.get_default_font()
        current_font = self.settings.value("font_family", default_font)
        # Перевіряємо, чи доступний збережений шрифт
        if current_font in [self.font_family_combo.itemText(i) for i in range(self.font_family_combo.count())]:
            self.font_family_combo.setCurrentText(current_font)
        else:
            self.font_family_combo.setCurrentText(default_font)
        self.font_size_spinbox.setValue(self.settings.value("font_size", 11, type=int))
        self.tab_size_spinbox.setValue(self.settings.value("tab_size", 4, type=int))
        self.show_line_numbers_checkbox.setChecked(self.settings.value("show_line_numbers", True, type=bool))
        self.highlight_current_line_checkbox.setChecked(self.settings.value("highlight_current_line", True, type=bool))
        self.auto_completion_checkbox.setChecked(self.settings.value("auto_completion", True, type=bool))
        self.realtime_validation_checkbox.setChecked(self.settings.value("realtime_validation", True, type=bool))
        self.auto_format_checkbox.setChecked(self.settings.value("auto_format", False, type=bool))

        # RimWorld
        self.game_folder_edit.setText(self.settings.value("game_folder", ""))
        self.mods_folder_edit.setText(self.settings.value("mods_folder", ""))
        self.auto_copy_checkbox.setChecked(self.settings.value("auto_copy", False, type=bool))
        self.compress_textures_checkbox.setChecked(self.settings.value("compress_textures", False, type=bool))

    def apply_settings(self):
        """Застосування налаштувань"""
        # Загальні
        self.settings.setValue("theme", self.theme_combo.currentText())
        self.settings.setValue("language", self.language_combo.currentText())
        self.settings.setValue("autosave", self.autosave_checkbox.isChecked())
        self.settings.setValue("autosave_interval", self.autosave_interval.value())

        # Проєкти
        self.settings.setValue("projects_folder", self.projects_folder_edit.text())
        self.settings.setValue("open_last_project", self.open_last_project_checkbox.isChecked())

        # Редактор
        self.settings.setValue("font_family", self.font_family_combo.currentText())
        self.settings.setValue("font_size", self.font_size_spinbox.value())
        self.settings.setValue("tab_size", self.tab_size_spinbox.value())
        self.settings.setValue("show_line_numbers", self.show_line_numbers_checkbox.isChecked())
        self.settings.setValue("highlight_current_line", self.highlight_current_line_checkbox.isChecked())
        self.settings.setValue("auto_completion", self.auto_completion_checkbox.isChecked())
        self.settings.setValue("realtime_validation", self.realtime_validation_checkbox.isChecked())
        self.settings.setValue("auto_format", self.auto_format_checkbox.isChecked())

        # RimWorld
        self.settings.setValue("game_folder", self.game_folder_edit.text())
        self.settings.setValue("mods_folder", self.mods_folder_edit.text())
        self.settings.setValue("auto_copy", self.auto_copy_checkbox.isChecked())
        self.settings.setValue("compress_textures", self.compress_textures_checkbox.isChecked())

        # Емітуємо сигнал про зміну налаштувань
        self.settings_changed.emit()

    def accept_settings(self):
        """Прийняття налаштувань"""
        self.apply_settings()
        self.accept()
