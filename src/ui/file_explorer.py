"""
Файловий експлорер для перегляду структури проєкту мода
"""

import os
from PyQt6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
                             QMenu, QMessageBox, QInputDialog)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QAction


class FileExplorer(QWidget):
    """Віджет файлового експлорера"""

    # Сигнал для відкриття файлу
    file_opened = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_root = None
        self.init_ui()

    def init_ui(self):
        """Ініціалізація інтерфейсу"""
        layout = QVBoxLayout(self)

        # Створюємо дерево файлів
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Файли проєкту")

        # Підключаємо сигнали
        self.tree_widget.itemDoubleClicked.connect(self.on_double_click)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.tree_widget)

    def set_root_path(self, path):
        """Встановлення кореневої папки"""
        if os.path.exists(path):
            self.current_root = path
            self.refresh_tree()

    def apply_settings(self):
        """Застосування налаштувань файлового експлорера"""
        from PyQt6.QtCore import QSettings

        settings = QSettings()

        # Показувати приховані файли
        show_hidden = settings.value("file_explorer/show_hidden", False, bool)
        # Тут можна додати логіку для показу/приховування прихованих файлів

        # Оновлюємо дерево файлів
        self.refresh_tree()

    def refresh_tree(self):
        """Оновлення дерева файлів"""
        if not self.current_root:
            return

        self.tree_widget.clear()
        self.populate_tree(self.current_root, self.tree_widget.invisibleRootItem())
        self.tree_widget.expandAll()

    def populate_tree(self, path, parent_item):
        """Заповнення дерева файлів"""
        try:
            items = os.listdir(path)
            items.sort()

            # Спочатку додаємо папки
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    folder_item = QTreeWidgetItem(parent_item, [item])
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, item_path)
                    self.populate_tree(item_path, folder_item)

            # Потім додаємо файли
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    file_item = QTreeWidgetItem(parent_item, [item])
                    file_item.setData(0, Qt.ItemDataRole.UserRole, item_path)

        except PermissionError:
            # Ігноруємо папки без доступу
            pass

    def on_double_click(self, item):
        """Обробка подвійного кліку"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)

        if os.path.isfile(file_path):
            # Відкриваємо файл для редагування
            self.file_opened.emit(file_path)

    def show_context_menu(self, position):
        """Показати контекстне меню"""
        item = self.tree_widget.itemAt(position)
        if not item:
            return

        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        is_file = os.path.isfile(file_path)

        menu = QMenu(self)

        if is_file:
            # Меню для файлів
            open_action = QAction("Відкрити", self)
            open_action.triggered.connect(lambda: self.file_opened.emit(file_path))
            menu.addAction(open_action)

            menu.addSeparator()

            rename_action = QAction("Перейменувати", self)
            rename_action.triggered.connect(lambda: self.rename_item(file_path))
            menu.addAction(rename_action)

            delete_action = QAction("Видалити", self)
            delete_action.triggered.connect(lambda: self.delete_item(file_path))
            menu.addAction(delete_action)
        else:
            # Меню для папок
            new_file_action = QAction("Новий файл", self)
            new_file_action.triggered.connect(lambda: self.create_new_file(file_path))
            menu.addAction(new_file_action)

            new_folder_action = QAction("Нова папка", self)
            new_folder_action.triggered.connect(lambda: self.create_new_folder(file_path))
            menu.addAction(new_folder_action)

            menu.addSeparator()

            rename_action = QAction("Перейменувати", self)
            rename_action.triggered.connect(lambda: self.rename_item(file_path))
            menu.addAction(rename_action)

            delete_action = QAction("Видалити", self)
            delete_action.triggered.connect(lambda: self.delete_item(file_path))
            menu.addAction(delete_action)

        menu.exec(self.tree_widget.mapToGlobal(position))

    def create_new_file(self, parent_path):
        """Створення нового файлу"""
        name, ok = QInputDialog.getText(self, "Новий файл", "Введіть назву файлу:")
        if ok and name:
            file_path = os.path.join(parent_path, name)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                self.refresh_tree()
                self.file_opened.emit(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося створити файл: {e}")

    def create_new_folder(self, parent_path):
        """Створення нової папки"""
        name, ok = QInputDialog.getText(self, "Нова папка", "Введіть назву папки:")
        if ok and name:
            folder_path = os.path.join(parent_path, name)
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.refresh_tree()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося створити папку: {e}")

    def rename_item(self, item_path):
        """Перейменування файлу або папки"""
        old_name = os.path.basename(item_path)
        new_name, ok = QInputDialog.getText(
            self, "Перейменувати", "Введіть нову назву:", text=old_name
        )

        if ok and new_name and new_name != old_name:
            parent_dir = os.path.dirname(item_path)
            new_path = os.path.join(parent_dir, new_name)

            try:
                os.rename(item_path, new_path)
                self.refresh_tree()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося перейменувати: {e}")

    def delete_item(self, item_path):
        """Видалення файлу або папки"""
        item_name = os.path.basename(item_path)
        reply = QMessageBox.question(
            self, "Підтвердження видалення",
            f"Ви впевнені, що хочете видалити '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                else:
                    import shutil
                    shutil.rmtree(item_path)
                self.refresh_tree()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося видалити: {e}")

    def refresh(self):
        """Оновлення дерева файлів"""
        self.refresh_tree()
