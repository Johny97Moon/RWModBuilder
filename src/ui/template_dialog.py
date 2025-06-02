"""
Діалог для вибору та створення шаблонів дефініцій
"""

import os
import re
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QPushButton, QTextEdit, QLabel, QSplitter,
                             QMessageBox, QInputDialog, QListWidgetItem, QWidget,
                             QLineEdit, QComboBox, QGroupBox, QTreeWidget,
                             QTreeWidgetItem, QTabWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from jinja2 import Template


class TemplateDialog(QDialog):
    """Діалог для роботи з шаблонами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.templates_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
        self.selected_template = None
        self.template_name = None
        self.template_categories = self._get_template_categories()

        self.init_ui()
        self.load_templates()

    def _get_template_categories(self):
        """Отримати категорії шаблонів"""
        return {
            "Основні": ["about_template.xml", "thingdef_template.xml", "recipedef_template.xml"],
            "Дослідження": ["researchprojectdef_template.xml"],
            "Персонажі": ["pawnkinddef_template.xml", "traitdef_template.xml", "factiondef_template.xml"],
            "Світ": ["biomedef_template.xml"],
            "Робота": ["jobdef_template.xml", "workgiverdef_template.xml"],
            "Всі": []  # Буде заповнено автоматично
        }

    def init_ui(self):
        """Ініціалізація інтерфейсу"""
        self.setWindowTitle("Шаблони дефініцій")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Панель пошуку та фільтрів
        search_layout = QHBoxLayout()

        # Пошук
        search_layout.addWidget(QLabel("Пошук:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Введіть назву шаблону...")
        self.search_edit.textChanged.connect(self.filter_templates)
        search_layout.addWidget(self.search_edit)

        # Категорії
        search_layout.addWidget(QLabel("Категорія:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(list(self.template_categories.keys()))
        self.category_combo.currentTextChanged.connect(self.filter_templates)
        search_layout.addWidget(self.category_combo)

        layout.addLayout(search_layout)

        # Сплітер для розділення списку та попереднього перегляду
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Ліва панель - список шаблонів
        left_panel = QVBoxLayout()

        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(300)

        left_panel.addWidget(QLabel("Доступні шаблони:"))

        self.templates_list = QListWidget()
        self.templates_list.itemClicked.connect(self.on_template_selected)
        left_panel.addWidget(self.templates_list)

        # Кнопки управління шаблонами
        buttons_layout = QHBoxLayout()

        self.new_button = QPushButton("Новий")
        self.new_button.clicked.connect(self.create_new_template)

        self.edit_button = QPushButton("Редагувати")
        self.edit_button.clicked.connect(self.edit_template)
        self.edit_button.setEnabled(False)

        self.delete_button = QPushButton("Видалити")
        self.delete_button.clicked.connect(self.delete_template)
        self.delete_button.setEnabled(False)

        buttons_layout.addWidget(self.new_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)

        left_panel.addLayout(buttons_layout)

        # Права панель - попередній перегляд
        right_panel = QVBoxLayout()

        right_widget = QWidget()
        right_widget.setLayout(right_panel)

        right_panel.addWidget(QLabel("Попередній перегляд:"))

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        right_panel.addWidget(self.preview_text)

        # Додаємо віджети до сплітера
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 500])

        layout.addWidget(splitter)

        # Кнопки діалогу
        dialog_buttons = QHBoxLayout()

        self.use_button = QPushButton("Використати")
        self.use_button.clicked.connect(self.accept)
        self.use_button.setEnabled(False)

        self.cancel_button = QPushButton("Скасувати")
        self.cancel_button.clicked.connect(self.reject)

        dialog_buttons.addStretch()
        dialog_buttons.addWidget(self.use_button)
        dialog_buttons.addWidget(self.cancel_button)

        layout.addLayout(dialog_buttons)

    def load_templates(self):
        """Завантаження списку шаблонів"""
        self.templates_list.clear()

        if not os.path.exists(self.templates_dir):
            return

        # Розширені описи шаблонів
        template_descriptions = {
            "about_template.xml": "About.xml - Метадані мода",
            "thingdef_template.xml": "ThingDef - Предмети та будівлі",
            "recipedef_template.xml": "RecipeDef - Рецепти крафту",
            "researchprojectdef_template.xml": "ResearchProjectDef - Дослідження",
            "pawnkinddef_template.xml": "PawnKindDef - Типи персонажів",
            "traitdef_template.xml": "TraitDef - Риси характеру",
            "factiondef_template.xml": "FactionDef - Фракції",
            "biomedef_template.xml": "BiomeDef - Біоми світу",
            "jobdef_template.xml": "JobDef - Завдання для персонажів",
            "workgiverdef_template.xml": "WorkGiverDef - Постачальники роботи"
        }

        # Заповнюємо категорію "Всі"
        all_templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.xml'):
                all_templates.append(filename)
        self.template_categories["Всі"] = all_templates

        # Додаємо шаблони до списку
        for filename in sorted(all_templates):
            display_name = template_descriptions.get(filename, filename)
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, filename)
            self.templates_list.addItem(item)

    def filter_templates(self):
        """Фільтрація шаблонів за пошуком та категорією"""
        search_text = self.search_edit.text().lower()
        selected_category = self.category_combo.currentText()

        # Отримуємо список файлів для вибраної категорії
        if selected_category in self.template_categories:
            category_files = self.template_categories[selected_category]
            if not category_files:  # Якщо категорія "Всі" порожня, заповнюємо її
                category_files = []
                for filename in os.listdir(self.templates_dir):
                    if filename.endswith('.xml'):
                        category_files.append(filename)
        else:
            category_files = []

        # Фільтруємо елементи списку
        for i in range(self.templates_list.count()):
            item = self.templates_list.item(i)
            filename = item.data(Qt.ItemDataRole.UserRole)
            display_name = item.text().lower()

            # Перевіряємо відповідність пошуку та категорії
            matches_search = search_text in display_name or search_text in filename.lower()
            matches_category = filename in category_files or selected_category == "Всі"

            item.setHidden(not (matches_search and matches_category))

    def on_template_selected(self, item):
        """Обробка вибору шаблону"""
        filename = item.data(Qt.ItemDataRole.UserRole)
        template_path = os.path.join(self.templates_dir, filename)

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.preview_text.setPlainText(content)
                self.selected_template = filename
                self.use_button.setEnabled(True)
                self.edit_button.setEnabled(True)
                self.delete_button.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити шаблон: {e}")

    def create_new_template(self):
        """Створення нового шаблону"""
        name, ok = QInputDialog.getText(
            self, "Новий шаблон",
            "Введіть назву шаблону (без розширення):"
        )

        if ok and name:
            filename = f"{name}.xml"
            template_path = os.path.join(self.templates_dir, filename)

            if os.path.exists(template_path):
                QMessageBox.warning(self, "Увага", "Шаблон з такою назвою вже існує")
                return

            # Створюємо базовий шаблон
            basic_template = '''<?xml version="1.0" encoding="utf-8"?>
<Defs>
    <!-- Ваш шаблон тут -->
</Defs>'''

            try:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(basic_template)

                self.load_templates()
                QMessageBox.information(self, "Успіх", f"Шаблон '{filename}' створено")
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося створити шаблон: {e}")

    def edit_template(self):
        """Редагування шаблону"""
        if not self.selected_template:
            return

        # Тут можна відкрити редактор або передати файл до головного редактора
        QMessageBox.information(
            self, "Редагування",
            f"Шаблон '{self.selected_template}' буде відкрито в редакторі"
        )

    def delete_template(self):
        """Видалення шаблону"""
        if not self.selected_template:
            return

        reply = QMessageBox.question(
            self, "Підтвердження",
            f"Ви впевнені, що хочете видалити шаблон '{self.selected_template}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            template_path = os.path.join(self.templates_dir, self.selected_template)
            try:
                os.remove(template_path)
                self.load_templates()
                self.preview_text.clear()
                self.selected_template = None
                self.use_button.setEnabled(False)
                self.edit_button.setEnabled(False)
                self.delete_button.setEnabled(False)
                QMessageBox.information(self, "Успіх", "Шаблон видалено")
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося видалити шаблон: {e}")

    def get_selected_template(self):
        """Отримання вибраного шаблону"""
        if self.selected_template:
            template_path = os.path.join(self.templates_dir, self.selected_template)
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return None
        return None

    def get_template_name(self):
        """Отримання назви вибраного шаблону"""
        return self.selected_template
