"""
Діалог експорту модів RimWorld
"""

import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QRadioButton, QCheckBox, QPushButton, QLineEdit,
                             QFileDialog, QProgressBar, QLabel, QGroupBox,
                             QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


class ExportWorker(QThread):
    """Робочий потік для експорту мода"""
    
    progress_updated = pyqtSignal(int, str)
    export_finished = pyqtSignal(bool, str)
    
    def __init__(self, project_manager, export_path, export_type, steam_workshop):
        super().__init__()
        self.project_manager = project_manager
        self.export_path = export_path
        self.export_type = export_type
        self.steam_workshop = steam_workshop
        
    def run(self):
        """Виконання експорту в окремому потоці"""
        try:
            success = self.project_manager.export_mod(
                self.export_path,
                self.export_type,
                self.steam_workshop,
                self.progress_callback
            )
            
            if success:
                self.export_finished.emit(True, "Експорт завершено успішно!")
            else:
                self.export_finished.emit(False, "Помилка під час експорту")
                
        except Exception as e:
            self.export_finished.emit(False, f"Критична помилка: {e}")
            
    def progress_callback(self, progress, message):
        """Callback для оновлення прогресу"""
        self.progress_updated.emit(progress, message)


class ExportDialog(QDialog):
    """Діалог експорту модів"""
    
    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.export_worker = None
        self.init_ui()
        
    def init_ui(self):
        """Ініціалізація інтерфейсу"""
        self.setWindowTitle("Експорт мода")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Інформація про проєкт
        self.create_project_info_section(layout)
        
        # Налаштування експорту
        self.create_export_settings_section(layout)
        
        # Вибір шляху
        self.create_path_selection_section(layout)
        
        # Прогрес
        self.create_progress_section(layout)
        
        # Кнопки
        self.create_buttons_section(layout)
        
    def create_project_info_section(self, layout):
        """Створення секції інформації про проєкт"""
        info_group = QGroupBox("Інформація про проєкт")
        info_layout = QFormLayout()
        
        # Отримуємо інформацію про проєкт
        project_config = self.project_manager.project_config
        mod_info = project_config.get("mod_info", {})
        
        self.project_name_label = QLabel(mod_info.get("name", "Невідомий мод"))
        self.project_name_label.setFont(QFont("", 10, QFont.Weight.Bold))
        info_layout.addRow("Назва:", self.project_name_label)
        
        self.author_label = QLabel(mod_info.get("author", "Невідомий автор"))
        info_layout.addRow("Автор:", self.author_label)
        
        self.package_id_label = QLabel(mod_info.get("package_id", "невідомий.мод"))
        info_layout.addRow("Package ID:", self.package_id_label)
        
        self.version_label = QLabel(mod_info.get("version", "1.5"))
        info_layout.addRow("Версія RimWorld:", self.version_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
    def create_export_settings_section(self, layout):
        """Створення секції налаштувань експорту"""
        settings_group = QGroupBox("Налаштування експорту")
        settings_layout = QVBoxLayout()
        
        # Тип експорту
        export_type_layout = QVBoxLayout()
        export_type_layout.addWidget(QLabel("Тип експорту:"))
        
        self.folder_radio = QRadioButton("Папка (для локального тестування)")
        self.folder_radio.setChecked(True)
        export_type_layout.addWidget(self.folder_radio)
        
        self.zip_radio = QRadioButton("ZIP архів (для розповсюдження)")
        export_type_layout.addWidget(self.zip_radio)
        
        settings_layout.addLayout(export_type_layout)
        
        # Додаткові опції
        self.steam_workshop_check = QCheckBox("Підготувати для Steam Workshop")
        self.steam_workshop_check.setToolTip(
            "Створює необхідні файли для публікації в Steam Workshop:\n"
            "- PublishedFileId.txt\n"
            "- Preview.png (якщо відсутній)"
        )
        settings_layout.addWidget(self.steam_workshop_check)
        
        self.validate_before_export = QCheckBox("Валідувати проєкт перед експортом")
        self.validate_before_export.setChecked(True)
        self.validate_before_export.setToolTip(
            "Перевіряє проєкт на помилки перед експортом"
        )
        settings_layout.addWidget(self.validate_before_export)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
    def create_path_selection_section(self, layout):
        """Створення секції вибору шляху"""
        path_group = QGroupBox("Шлях експорту")
        path_layout = QHBoxLayout()
        
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setPlaceholderText("Оберіть папку для експорту...")
        self.export_path_edit.setReadOnly(True)
        
        self.browse_button = QPushButton("Огляд...")
        self.browse_button.clicked.connect(self.browse_export_path)
        
        path_layout.addWidget(self.export_path_edit)
        path_layout.addWidget(self.browse_button)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
    def create_progress_section(self, layout):
        """Створення секції прогресу"""
        self.progress_group = QGroupBox("Прогрес експорту")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        progress_layout.addWidget(self.progress_label)
        
        # Лог експорту
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setVisible(False)
        self.log_text.setFont(QFont("Consolas", 9))
        progress_layout.addWidget(self.log_text)
        
        self.progress_group.setLayout(progress_layout)
        self.progress_group.setVisible(False)
        layout.addWidget(self.progress_group)
        
    def create_buttons_section(self, layout):
        """Створення секції кнопок"""
        buttons_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Експортувати")
        self.export_button.clicked.connect(self.start_export)
        self.export_button.setDefault(True)
        
        self.cancel_button = QPushButton("Скасувати")
        self.cancel_button.clicked.connect(self.reject)
        
        self.close_button = QPushButton("Закрити")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setVisible(False)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.export_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.close_button)
        
        layout.addLayout(buttons_layout)
        
    def browse_export_path(self):
        """Вибір шляху для експорту"""
        path = QFileDialog.getExistingDirectory(
            self, "Оберіть папку для експорту"
        )
        if path:
            self.export_path_edit.setText(path)
            
    def start_export(self):
        """Початок експорту"""
        # Перевіряємо налаштування
        if not self.export_path_edit.text():
            QMessageBox.warning(
                self, "Помилка", 
                "Будь ласка, оберіть папку для експорту"
            )
            return
            
        if not os.path.exists(self.export_path_edit.text()):
            QMessageBox.warning(
                self, "Помилка", 
                "Обрана папка не існує"
            )
            return
            
        # Валідація проєкту
        if self.validate_before_export.isChecked():
            validation = self.project_manager.validate_project()
            if not validation["valid"]:
                reply = QMessageBox.question(
                    self, "Помилки валідації",
                    f"Проєкт містить помилки:\n\n" + 
                    "\n".join(validation["errors"]) + 
                    "\n\nПродовжити експорт?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
                    
        # Підготовка до експорту
        self.progress_group.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.log_text.setVisible(True)
        
        self.export_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        
        # Визначаємо параметри експорту
        export_type = "zip" if self.zip_radio.isChecked() else "folder"
        steam_workshop = self.steam_workshop_check.isChecked()
        export_path = self.export_path_edit.text()
        
        # Запускаємо експорт в окремому потоці
        self.export_worker = ExportWorker(
            self.project_manager, export_path, export_type, steam_workshop
        )
        self.export_worker.progress_updated.connect(self.update_progress)
        self.export_worker.export_finished.connect(self.export_completed)
        self.export_worker.start()
        
        self.log_text.append("Початок експорту...")
        
    def update_progress(self, progress, message):
        """Оновлення прогресу"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
        self.log_text.append(f"[{progress}%] {message}")
        
        # Прокручуємо лог до кінця
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        
    def export_completed(self, success, message):
        """Завершення експорту"""
        self.progress_bar.setValue(100 if success else 0)
        self.progress_label.setText(message)
        self.log_text.append(f"\n{'✅' if success else '❌'} {message}")
        
        if success:
            self.log_text.append(f"📁 Експорт збережено в: {self.export_path_edit.text()}")
            
        # Відновлюємо інтерфейс
        self.export_button.setVisible(False)
        self.cancel_button.setVisible(False)
        self.close_button.setVisible(True)
        
        self.browse_button.setEnabled(True)
        
        # Показуємо повідомлення
        if success:
            QMessageBox.information(self, "Успіх", message)
        else:
            QMessageBox.critical(self, "Помилка", message)
            
    def closeEvent(self, event):
        """Обробка закриття діалогу"""
        if self.export_worker and self.export_worker.isRunning():
            reply = QMessageBox.question(
                self, "Експорт в процесі",
                "Експорт ще не завершено. Скасувати?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.export_worker.terminate()
                self.export_worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
