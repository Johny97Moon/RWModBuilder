"""
Переглядач логів для RimWorld Mod Builder
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton, 
                             QHBoxLayout, QComboBox, QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LogViewerDialog(QDialog):
    """Діалог для перегляду логів програми"""
    
    def __init__(self, logger_instance, parent=None):
        super().__init__(parent)
        self.logger_instance = logger_instance
        self.init_ui()
        self.load_logs()
        
    def init_ui(self):
        """Ініціалізація інтерфейсу"""
        self.setWindowTitle("Логи програми")
        self.setModal(False)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Панель фільтрів
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Рівень:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["Всі", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self.filter_logs)
        filter_layout.addWidget(self.level_combo)
        
        filter_layout.addStretch()
        
        clear_button = QPushButton("Очистити логи")
        clear_button.clicked.connect(self.clear_logs)
        filter_layout.addWidget(clear_button)
        
        layout.addLayout(filter_layout)
        
        # Текстове поле для логів
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Оновити")
        refresh_button.clicked.connect(self.load_logs)
        buttons_layout.addWidget(refresh_button)
        
        buttons_layout.addStretch()
        
        close_button = QPushButton("Закрити")
        close_button.clicked.connect(self.close)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
        
    def load_logs(self):
        """Завантаження логів"""
        try:
            logs = self.logger_instance.get_logs()
            self.log_text.setPlainText('\n'.join(logs))
            # Прокручуємо до кінця
            self.log_text.moveCursor(self.log_text.textCursor().End)
        except Exception as e:
            self.log_text.setPlainText(f"Помилка завантаження логів: {e}")
            
    def filter_logs(self):
        """Фільтрація логів за рівнем"""
        level = self.level_combo.currentText()
        if level == "Всі":
            self.load_logs()
            return
            
        try:
            all_logs = self.logger_instance.get_logs()
            filtered_logs = [log for log in all_logs if level in log]
            self.log_text.setPlainText('\n'.join(filtered_logs))
        except Exception as e:
            self.log_text.setPlainText(f"Помилка фільтрації логів: {e}")
            
    def clear_logs(self):
        """Очищення логів"""
        try:
            self.logger_instance.clear_logs()
            self.log_text.clear()
        except Exception as e:
            self.log_text.setPlainText(f"Помилка очищення логів: {e}")
