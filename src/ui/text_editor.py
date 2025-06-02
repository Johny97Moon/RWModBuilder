"""
Текстовий редактор з підсвіткою синтаксису для XML та C#
"""

import os
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QMessageBox, QPlainTextEdit, QCompleter,
                             QDialog, QLineEdit, QPushButton, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QStringListModel
from PyQt6.QtGui import (QFont, QSyntaxHighlighter, QTextCharFormat,
                         QColor, QTextDocument, QTextCursor, QFontDatabase)

# Імпорти для профілювання (з try/except для сумісності)
try:
    from utils.performance import profile, cached
except ImportError:
    # Заглушки якщо модуль недоступний
    def profile(func):
        return func
    def cached(func):
        return func


class XmlSyntaxHighlighter(QSyntaxHighlighter):
    """Підсвітка синтаксису для XML"""

    def __init__(self, document):
        super().__init__(document)
        self.setup_highlighting_rules()

    def setup_highlighting_rules(self):
        """Налаштування правил підсвітки"""
        self.highlighting_rules = []

        # XML теги
        xml_element_format = QTextCharFormat()
        xml_element_format.setForeground(QColor(128, 128, 255))
        xml_element_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((
            re.compile(r'<[!?/]?\b[A-Za-z_][A-Za-z0-9_.-]*(?:\s|>|/>)'),
            xml_element_format
        ))

        # XML атрибути
        xml_attribute_format = QTextCharFormat()
        xml_attribute_format.setForeground(QColor(255, 128, 0))
        self.highlighting_rules.append((
            re.compile(r'\b[A-Za-z_][A-Za-z0-9_.-]*(?=\s*=)'),
            xml_attribute_format
        ))

        # Значення атрибутів
        xml_value_format = QTextCharFormat()
        xml_value_format.setForeground(QColor(0, 255, 0))
        self.highlighting_rules.append((
            re.compile(r'"[^"]*"'),
            xml_value_format
        ))

        # XML коментарі
        xml_comment_format = QTextCharFormat()
        xml_comment_format.setForeground(QColor(128, 128, 128))
        xml_comment_format.setFontItalic(True)
        self.highlighting_rules.append((
            re.compile(r'<!--.*-->'),
            xml_comment_format
        ))

        # Числа
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(255, 255, 0))
        self.highlighting_rules.append((
            re.compile(r'\b\d+\.?\d*\b'),
            number_format
        ))

    def highlightBlock(self, text):
        """Підсвітка блоку тексту"""
        for pattern, format_obj in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, format_obj)


class LineNumberArea(QWidget):
    """Область для відображення номерів рядків"""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return self.editor.line_number_area_width()

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class FindReplaceDialog(QDialog):
    """Діалог пошуку та заміни"""

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.init_ui()

    def init_ui(self):
        """Ініціалізація інтерфейсу"""
        self.setWindowTitle("Пошук та заміна")
        self.setModal(False)
        self.resize(400, 200)

        layout = QVBoxLayout(self)

        # Поле пошуку
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Знайти:"))
        self.find_edit = QLineEdit()
        find_layout.addWidget(self.find_edit)
        layout.addLayout(find_layout)

        # Поле заміни
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Замінити:"))
        self.replace_edit = QLineEdit()
        replace_layout.addWidget(self.replace_edit)
        layout.addLayout(replace_layout)

        # Опції
        options_layout = QHBoxLayout()
        self.case_sensitive = QCheckBox("Враховувати регістр")
        self.regex_mode = QCheckBox("Регулярні вирази")
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.regex_mode)
        layout.addLayout(options_layout)

        # Кнопки
        buttons_layout = QHBoxLayout()

        self.find_button = QPushButton("Знайти")
        self.find_button.clicked.connect(self.find_text)

        self.replace_button = QPushButton("Замінити")
        self.replace_button.clicked.connect(self.replace_text)

        self.replace_all_button = QPushButton("Замінити все")
        self.replace_all_button.clicked.connect(self.replace_all)

        self.close_button = QPushButton("Закрити")
        self.close_button.clicked.connect(self.close)

        buttons_layout.addWidget(self.find_button)
        buttons_layout.addWidget(self.replace_button)
        buttons_layout.addWidget(self.replace_all_button)
        buttons_layout.addWidget(self.close_button)

        layout.addLayout(buttons_layout)

    def find_text(self):
        """Пошук тексту"""
        text = self.find_edit.text()
        if not text:
            return

        flags = QTextDocument.FindFlag(0)
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        if self.regex_mode.isChecked():
            # Використовуємо регулярні вирази
            cursor = self.editor.textCursor()
            regex = re.compile(text, 0 if self.case_sensitive.isChecked() else re.IGNORECASE)

            content = self.editor.toPlainText()
            start_pos = cursor.position()

            match = regex.search(content, start_pos)
            if not match:
                # Шукаємо з початку
                match = regex.search(content, 0)

            if match:
                cursor.setPosition(match.start())
                cursor.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
                self.editor.setTextCursor(cursor)
        else:
            # Звичайний пошук
            found = self.editor.find(text, flags)
            if not found:
                # Шукаємо з початку
                cursor = self.editor.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                self.editor.setTextCursor(cursor)
                self.editor.find(text, flags)

    def replace_text(self):
        """Заміна поточного знайденого тексту"""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(self.replace_edit.text())

    def replace_all(self):
        """Заміна всіх входжень"""
        find_text = self.find_edit.text()
        replace_text = self.replace_edit.text()

        if not find_text:
            return

        content = self.editor.toPlainText()

        if self.regex_mode.isChecked():
            flags = 0 if self.case_sensitive.isChecked() else re.IGNORECASE
            content = re.sub(find_text, replace_text, content, flags=flags)
        else:
            if not self.case_sensitive.isChecked():
                # Заміна без урахування регістру
                import re
                content = re.sub(re.escape(find_text), replace_text, content, flags=re.IGNORECASE)
            else:
                content = content.replace(find_text, replace_text)

        self.editor.setPlainText(content)


class RimWorldCompleter(QCompleter):
    """Автодоповнення для RimWorld XML тегів"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_completions()

    def setup_completions(self):
        """Налаштування списку автодоповнення"""
        rimworld_tags = [
            # Загальні теги
            "defName", "label", "description",

            # ThingDef теги
            "thingClass", "category", "altitudeLayer", "useHitPoints", "selectable",
            "pathCost", "passability", "fillPercent", "rotatable", "size",
            "designationCategory", "constructEffect", "repairEffect", "destroyEffect",

            # Графіка
            "graphicData", "texPath", "graphicClass", "drawSize", "color",

            # Статистики
            "statBases", "MaxHitPoints", "Beauty", "Mass", "Flammability", "MarketValue",
            "WorkToBuild", "WorkToMake", "DeteriorationRate",

            # Будівлі
            "building", "isInert", "isEdifice", "canPlaceOverImpassablePlant",
            "preventDeteriorationOnTop", "preventDeteriorationInside",

            # Рецепти
            "workAmount", "workSpeedStat", "workSkill", "workSkillLearnFactor",
            "ingredients", "products", "fixedIngredientFilter", "defaultIngredientFilter",
            "recipeUsers", "researchPrerequisite", "skillRequirements",

            # PawnKindDef
            "race", "defaultFactionType", "combatPower", "canArriveManhunter",
            "canBeSapper", "apparelTags", "weaponTags", "apparelMoney", "weaponMoney",

            # Дослідження
            "baseCost", "techLevel", "prerequisites", "requiredResearchBuilding",
            "requiredResearchFacilities", "tab", "researchViewX", "researchViewY",

            # Загальні значення
            "Item", "Building", "Pawn", "Plant", "Projectile",
            "Thing", "ThingWithComps", "Building_Storage", "Building_WorkTable",
            "Industrial", "Medieval", "Spacer", "Neolithic",
            "true", "false"
        ]

        model = QStringListModel(rimworld_tags)
        self.setModel(model)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)


class TextEditor(QPlainTextEdit):
    """Текстовий редактор з номерами рядків та підсвіткою синтаксису"""

    # Сигнал для повідомлення про зміни
    content_changed = pyqtSignal()

    def __init__(self, file_path=None):
        super().__init__()
        self.file_path = file_path
        self.modified = False
        self.find_dialog = None

        self.init_ui()
        self.setup_editor()
        self.setup_autocomplete()

        if file_path:
            self.load_file()

    def init_ui(self):
        """Ініціалізація інтерфейсу"""
        # Налаштування шрифту з fallback
        try:
            font = self.get_safe_font()
            self.setFont(font)
        except Exception as e:
            # Fallback до системного шрифту
            print(f"Помилка налаштування шрифту: {e}")
            font = QFont()  # Системний шрифт за замовчуванням
            self.setFont(font)

        # Область номерів рядків
        self.line_number_area = LineNumberArea(self)

        # Підключення сигналів
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self.on_text_changed)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def setup_editor(self):
        """Налаштування редактора"""
        # Встановлення табуляції
        self.setTabStopDistance(40)  # 4 пробіли

        # Підсвітка синтаксису
        if self.file_path and self.file_path.lower().endswith('.xml'):
            self.highlighter = XmlSyntaxHighlighter(self.document())

    def get_safe_font(self):
        """Отримання безпечного шрифту з fallback"""
        try:
            # Пріоритетні шрифти
            preferred_fonts = ["Consolas", "Courier New", "Monaco", "DejaVu Sans Mono"]

            try:
                font_db = QFontDatabase.families()

                for font_name in preferred_fonts:
                    try:
                        if font_name in font_db:
                            font = QFont(font_name, 11)
                            if font.exactMatch():
                                return font
                    except:
                        continue

            except Exception as e:
                print(f"Помилка QFontDatabase: {e}")

            # Fallback до системного моноширинного шрифту
            font = QFont()
            font.setFamily("monospace")
            font.setPointSize(11)
            font.setStyleHint(QFont.StyleHint.TypeWriter)
            return font

        except Exception as e:
            print(f"Критична помилка шрифту: {e}")
            # Останній fallback - системний шрифт
            return QFont()

    def setup_autocomplete(self):
        """Налаштування автодоповнення"""
        if self.file_path and self.file_path.lower().endswith('.xml'):
            self.completer = RimWorldCompleter(self)
            self.completer.setWidget(self)
            self.completer.activated.connect(self.insert_completion)

    def insert_completion(self, completion):
        """Вставка автодоповнення"""
        cursor = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        cursor.movePosition(QTextCursor.MoveOperation.Left)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfWord)
        cursor.insertText(completion[-extra:])
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        """Обробка натискання клавіш"""
        # Обробка автодоповнення
        if hasattr(self, 'completer') and self.completer.popup().isVisible():
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                event.ignore()
                return

        # Гарячі клавіші
        if event.key() == Qt.Key.Key_F and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.show_find_dialog()
            return
        elif event.key() == Qt.Key.Key_H and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.show_find_dialog(replace_mode=True)
            return

        # Звичайна обробка
        super().keyPressEvent(event)

        # Автодоповнення
        if hasattr(self, 'completer'):
            self.handle_autocomplete(event)

    def handle_autocomplete(self, _):
        """Обробка автодоповнення"""
        if not hasattr(self, 'completer') or not self.completer:
            return

        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        completion_prefix = cursor.selectedText()

        if len(completion_prefix) < 2:
            popup = self.completer.popup()
            if popup:
                popup.hide()
            return

        if completion_prefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completion_prefix)
            popup = self.completer.popup()
            model = self.completer.completionModel()
            if popup and model:
                popup.setCurrentIndex(model.index(0, 0))

        cr = self.cursorRect()
        popup = self.completer.popup()
        if popup:
            try:
                width = popup.sizeHintForColumn(0)
                scrollbar = popup.verticalScrollBar()
                if scrollbar:
                    width += scrollbar.sizeHint().width()
                cr.setWidth(width)
            except:
                cr.setWidth(200)  # fallback width
        self.completer.complete(cr)

    def show_find_dialog(self, replace_mode=False):
        """Показати діалог пошуку"""
        if not self.find_dialog:
            self.find_dialog = FindReplaceDialog(self, self.parent())

        if replace_mode:
            self.find_dialog.replace_edit.setVisible(True)
            self.find_dialog.replace_button.setVisible(True)
            self.find_dialog.replace_all_button.setVisible(True)
        else:
            self.find_dialog.replace_edit.setVisible(False)
            self.find_dialog.replace_button.setVisible(False)
            self.find_dialog.replace_all_button.setVisible(False)

        # Заповнюємо поле пошуку виділеним текстом
        cursor = self.textCursor()
        if cursor.hasSelection():
            self.find_dialog.find_edit.setText(cursor.selectedText())

        self.find_dialog.show()
        self.find_dialog.find_edit.setFocus()
        self.find_dialog.find_edit.selectAll()

    @profile
    def load_file(self):
        """Завантаження файлу"""
        if not self.file_path or not os.path.exists(self.file_path):
            return False

        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.setPlainText(content)
                self.modified = False
                return True
        except Exception as e:
            QMessageBox.critical(
                self, "Помилка",
                f"Не вдалося відкрити файл {self.file_path}:\n{e}"
            )
            return False

    @profile
    def save_file(self):
        """Збереження файлу"""
        if not self.file_path:
            return False

        try:
            with open(self.file_path, 'w', encoding='utf-8') as file:
                file.write(self.toPlainText())
                self.modified = False
                return True
        except Exception as e:
            QMessageBox.critical(
                self, "Помилка",
                f"Не вдалося зберегти файл {self.file_path}:\n{e}"
            )
            return False

    def is_modified(self):
        """Перевірка, чи був файл змінений"""
        return self.modified

    def undo(self):
        """Скасувати останню дію"""
        super().undo()

    def redo(self):
        """Повторити скасовану дію"""
        super().redo()

    def apply_settings(self):
        """Застосування налаштувань редактора"""
        from PyQt6.QtCore import QSettings
        from PyQt6.QtGui import QFont

        settings = QSettings()

        # Шрифт
        font_family = settings.value("editor/font_family", "Consolas")
        font_size = settings.value("editor/font_size", 11, int)
        self.setFont(QFont(font_family, font_size))

        # Табуляція
        tab_width = settings.value("editor/tab_width", 4, int)
        self.setTabStopDistance(tab_width * self.fontMetrics().horizontalAdvance(' '))

        # Перенос рядків
        word_wrap = settings.value("editor/word_wrap", False, bool)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth if word_wrap else QPlainTextEdit.LineWrapMode.NoWrap)

    def on_text_changed(self):
        """Обробка зміни тексту"""
        self.modified = True
        self.content_changed.emit()

    def line_number_area_width(self):
        """Обчислення ширини області номерів рядків"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1

        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """Оновлення ширини області номерів рядків"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Оновлення області номерів рядків"""
        if not hasattr(self, 'line_number_area') or not self.line_number_area:
            return

        if dy:
            self.line_number_area.scroll(0, dy)
        elif rect and hasattr(rect, 'y') and hasattr(rect, 'height'):
            self.line_number_area.update(0, rect.y(),
                                       self.line_number_area.width(),
                                       rect.height())

            if hasattr(rect, 'contains') and rect.contains(self.viewport().rect()):
                self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Обробка зміни розміру"""
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            cr.left(), cr.top(),
            self.line_number_area_width(),
            cr.height()
        )

    def line_number_area_paint_event(self, event):
        """Малювання номерів рядків"""
        from PyQt6.QtGui import QPainter

        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(240, 240, 240))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(120, 120, 120))
                painter.drawText(
                    0, int(top),
                    self.line_number_area.width(),
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number
                )

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        """Підсвітка поточного рядка"""
        try:
            extra_selections = []

            if not self.isReadOnly():
                # Використовуємо правильний тип ExtraSelection
                from PyQt6.QtWidgets import QTextEdit

                selection = QTextEdit.ExtraSelection()

                line_color = QColor(Qt.GlobalColor.yellow).lighter(160)
                selection.format.setBackground(line_color)
                selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
                selection.cursor = self.textCursor()
                selection.cursor.clearSelection()
                extra_selections.append(selection)

            self.setExtraSelections(extra_selections)
        except Exception as e:
            # Якщо підсвітка не працює, просто ігноруємо помилку
            print(f"Попередження: не вдалося підсвітити поточний рядок: {e}")
            pass
