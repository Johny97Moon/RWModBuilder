"""
Діалог створення нового проєкту мода
"""

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QComboBox, QPushButton,
                             QFileDialog, QMessageBox, QLabel)
from PyQt6.QtCore import Qt


class NewProjectDialog(QDialog):
    """Діалог для створення нового проєкту мода"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = None
        self.mod_info = {}
        self.init_ui()
        
    def init_ui(self):
        """Ініціалізація інтерфейсу"""
        self.setWindowTitle("Створити новий проєкт мода")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Форма з полями
        form_layout = QFormLayout()
        
        # Назва мода
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введіть назву мода")
        form_layout.addRow("Назва мода:", self.name_edit)
        
        # Автор
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Ваше ім'я")
        form_layout.addRow("Автор:", self.author_edit)
        
        # Package ID
        self.package_id_edit = QLineEdit()
        self.package_id_edit.setPlaceholderText("author.modname")
        form_layout.addRow("Package ID:", self.package_id_edit)
        
        # Версія RimWorld
        self.version_combo = QComboBox()
        self.version_combo.addItems(["1.5", "1.4", "1.3", "1.2", "1.1", "1.0"])
        form_layout.addRow("Версія RimWorld:", self.version_combo)
        
        # URL (опціонально)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://github.com/author/modname (опціонально)")
        form_layout.addRow("URL:", self.url_edit)
        
        # Опис
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Опис мода...")
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Опис:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Вибір папки проєкту
        folder_layout = QHBoxLayout()
        
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Оберіть папку для проєкту")
        self.folder_edit.setReadOnly(True)
        
        self.browse_button = QPushButton("Огляд...")
        self.browse_button.clicked.connect(self.browse_folder)
        
        folder_layout.addWidget(QLabel("Папка проєкту:"))
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(self.browse_button)
        
        layout.addLayout(folder_layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.create_button = QPushButton("Створити")
        self.create_button.clicked.connect(self.create_project)
        self.create_button.setEnabled(False)
        
        self.cancel_button = QPushButton("Скасувати")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.create_button)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        
        # Підключаємо сигнали для валідації
        self.name_edit.textChanged.connect(self.validate_form)
        self.author_edit.textChanged.connect(self.validate_form)
        self.package_id_edit.textChanged.connect(self.validate_form)
        self.folder_edit.textChanged.connect(self.validate_form)
        
        # Автоматичне заповнення Package ID
        self.name_edit.textChanged.connect(self.auto_fill_package_id)
        self.author_edit.textChanged.connect(self.auto_fill_package_id)
        
    def browse_folder(self):
        """Вибір папки для проєкту"""
        folder = QFileDialog.getExistingDirectory(
            self, "Оберіть папку для проєкту"
        )
        if folder:
            # Створюємо підпапку з назвою мода
            mod_name = self.name_edit.text().strip()
            if mod_name:
                # Очищаємо назву від недозволених символів
                safe_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_name = safe_name.replace(' ', '_')
                project_folder = os.path.join(folder, safe_name)
            else:
                project_folder = os.path.join(folder, "NewMod")
                
            self.folder_edit.setText(project_folder)
            
    def auto_fill_package_id(self):
        """Автоматичне заповнення Package ID"""
        if not self.package_id_edit.text():  # Тільки якщо поле порожнє
            author = self.author_edit.text().strip().lower()
            mod_name = self.name_edit.text().strip().lower()
            
            if author and mod_name:
                # Очищаємо від недозволених символів
                author = "".join(c for c in author if c.isalnum())
                mod_name = "".join(c for c in mod_name if c.isalnum())
                
                if author and mod_name:
                    package_id = f"{author}.{mod_name}"
                    self.package_id_edit.setText(package_id)
                    
    def validate_form(self):
        """Валідація форми"""
        name = self.name_edit.text().strip()
        author = self.author_edit.text().strip()
        package_id = self.package_id_edit.text().strip()
        folder = self.folder_edit.text().strip()
        
        # Перевіряємо обов'язкові поля
        valid = bool(name and author and package_id and folder)
        
        # Перевіряємо формат Package ID
        if package_id and '.' not in package_id:
            valid = False
            
        self.create_button.setEnabled(valid)
        
    def create_project(self):
        """Створення проєкту"""
        # Збираємо дані
        self.mod_info = {
            'name': self.name_edit.text().strip(),
            'author': self.author_edit.text().strip(),
            'package_id': self.package_id_edit.text().strip(),
            'version': self.version_combo.currentText(),
            'url': self.url_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip()
        }
        
        self.project_path = self.folder_edit.text().strip()
        
        # Перевіряємо, чи папка не існує
        if os.path.exists(self.project_path):
            reply = QMessageBox.question(
                self, "Папка існує",
                f"Папка '{self.project_path}' вже існує. Продовжити?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
                
        # Створюємо папку
        try:
            os.makedirs(self.project_path, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(
                self, "Помилка",
                f"Не вдалося створити папку проєкту:\n{e}"
            )
            return
            
        self.accept()
        
    def get_project_data(self):
        """Отримання даних проєкту"""
        return self.project_path, self.mod_info
