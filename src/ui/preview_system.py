"""
Система попереднього перегляду для дефініцій RimWorld
"""

import os
import xml.etree.ElementTree as ET
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QFrame, QGroupBox, QTextEdit,
                             QTabWidget, QListWidget, QListWidgetItem,
                             QSplitter, QPushButton, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor, QPen
from PIL import Image, ImageDraw, ImageFont
import tempfile


class DefinitionPreview(QWidget):
    """Віджет попереднього перегляду дефініцій"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_definition = None
        self.init_ui()
        
    def init_ui(self):
        """Ініціалізація інтерфейсу"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        self.title_label = QLabel("Попередній перегляд")
        self.title_label.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(self.title_label)
        
        # Вкладки для різних типів попереднього перегляду
        self.tabs = QTabWidget()
        
        # Вкладка загальної інформації
        self.info_tab = self.create_info_tab()
        self.tabs.addTab(self.info_tab, "Інформація")
        
        # Вкладка візуального попереднього перегляду
        self.visual_tab = self.create_visual_tab()
        self.tabs.addTab(self.visual_tab, "Візуальний")
        
        # Вкладка статистик
        self.stats_tab = self.create_stats_tab()
        self.tabs.addTab(self.stats_tab, "Статистики")
        
        layout.addWidget(self.tabs)
        
    def create_info_tab(self):
        """Створення вкладки загальної інформації"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Основна інформація
        self.info_group = QGroupBox("Основна інформація")
        info_layout = QVBoxLayout()
        
        self.def_name_label = QLabel("DefName: -")
        self.label_label = QLabel("Label: -")
        self.description_label = QLabel("Description: -")
        self.type_label = QLabel("Тип: -")
        
        info_layout.addWidget(self.def_name_label)
        info_layout.addWidget(self.label_label)
        info_layout.addWidget(self.description_label)
        info_layout.addWidget(self.type_label)
        
        self.info_group.setLayout(info_layout)
        layout.addWidget(self.info_group)
        
        # Додаткова інформація
        self.additional_info = QTextEdit()
        self.additional_info.setMaximumHeight(200)
        self.additional_info.setFont(QFont("Consolas", 9))
        layout.addWidget(self.additional_info)
        
        layout.addStretch()
        return widget
        
    def create_visual_tab(self):
        """Створення вкладки візуального попереднього перегляду"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Область для зображення
        self.image_label = QLabel("Зображення недоступне")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        
        layout.addWidget(self.image_label)
        
        # Інформація про графіку
        self.graphics_info = QTextEdit()
        self.graphics_info.setMaximumHeight(150)
        self.graphics_info.setFont(QFont("Consolas", 9))
        layout.addWidget(self.graphics_info)
        
        layout.addStretch()
        return widget
        
    def create_stats_tab(self):
        """Створення вкладки статистик"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Список статистик
        self.stats_list = QListWidget()
        layout.addWidget(self.stats_list)
        
        return widget
        
    def preview_definition(self, xml_content: str, file_path: str = None):
        """Попередній перегляд дефініції"""
        try:
            root = ET.fromstring(xml_content)
            
            if root.tag == "Defs":
                # Якщо це файл з кількома дефініціями, беремо першу
                definitions = list(root)
                if definitions:
                    self.current_definition = definitions[0]
                else:
                    self.clear_preview()
                    return
            else:
                # Якщо це окрема дефініція
                self.current_definition = root
                
            self.update_preview(file_path)
            
        except ET.ParseError as e:
            self.show_error(f"Помилка парсингу XML: {e}")
            
    def update_preview(self, file_path: str = None):
        """Оновлення попереднього перегляду"""
        if not self.current_definition:
            return
            
        def_type = self.current_definition.tag
        
        # Оновлюємо загальну інформацію
        self.update_info_tab()
        
        # Оновлюємо візуальний перегляд
        self.update_visual_tab(file_path)
        
        # Оновлюємо статистики
        self.update_stats_tab()
        
        # Оновлюємо заголовок
        def_name = self.get_element_text("defName", "Невідомо")
        self.title_label.setText(f"Попередній перегляд: {def_name} ({def_type})")
        
    def update_info_tab(self):
        """Оновлення вкладки інформації"""
        def_name = self.get_element_text("defName", "-")
        label = self.get_element_text("label", "-")
        description = self.get_element_text("description", "-")
        def_type = self.current_definition.tag
        
        self.def_name_label.setText(f"DefName: {def_name}")
        self.label_label.setText(f"Label: {label}")
        self.description_label.setText(f"Description: {description}")
        self.type_label.setText(f"Тип: {def_type}")
        
        # Додаткова інформація залежно від типу
        additional_info = self.get_additional_info_by_type(def_type)
        self.additional_info.setPlainText(additional_info)
        
    def update_visual_tab(self, file_path: str = None):
        """Оновлення візуального попереднього перегляду"""
        def_type = self.current_definition.tag
        
        if def_type == "ThingDef":
            self.preview_thingdef_visual(file_path)
        elif def_type == "PawnKindDef":
            self.preview_pawnkind_visual()
        else:
            self.show_placeholder_image(def_type)
            
    def preview_thingdef_visual(self, file_path: str = None):
        """Візуальний попередній перегляд ThingDef"""
        graphic_data = self.current_definition.find("graphicData")
        
        if graphic_data is not None:
            tex_path = graphic_data.find("texPath")
            graphic_class = graphic_data.find("graphicClass")
            draw_size = graphic_data.find("drawSize")
            
            graphics_info = []
            
            if tex_path is not None and tex_path.text:
                graphics_info.append(f"Texture Path: {tex_path.text}")
                
                # Спробуємо знайти текстуру
                if file_path:
                    texture_path = self.find_texture_file(file_path, tex_path.text)
                    if texture_path:
                        self.load_texture_preview(texture_path)
                    else:
                        self.create_placeholder_texture(tex_path.text)
                else:
                    self.create_placeholder_texture(tex_path.text)
                    
            if graphic_class is not None and graphic_class.text:
                graphics_info.append(f"Graphic Class: {graphic_class.text}")
                
            if draw_size is not None and draw_size.text:
                graphics_info.append(f"Draw Size: {draw_size.text}")
                
            self.graphics_info.setPlainText("\n".join(graphics_info))
        else:
            self.show_placeholder_image("ThingDef")
            self.graphics_info.setPlainText("Графічні дані не знайдено")
            
    def preview_pawnkind_visual(self):
        """Візуальний попередній перегляд PawnKindDef"""
        # Створюємо заглушку для PawnKindDef
        self.create_pawnkind_placeholder()
        
        race = self.get_element_text("race", "Невідомо")
        combat_power = self.get_element_text("combatPower", "Невідомо")
        
        info = f"Race: {race}\nCombat Power: {combat_power}"
        self.graphics_info.setPlainText(info)
        
    def update_stats_tab(self):
        """Оновлення вкладки статистик"""
        self.stats_list.clear()
        
        def_type = self.current_definition.tag
        
        if def_type == "ThingDef":
            self.load_thingdef_stats()
        elif def_type == "RecipeDef":
            self.load_recipe_stats()
        elif def_type == "ResearchProjectDef":
            self.load_research_stats()
            
    def load_thingdef_stats(self):
        """Завантаження статистик ThingDef"""
        stat_bases = self.current_definition.find("statBases")
        if stat_bases is not None:
            for stat in stat_bases:
                if stat.text:
                    item = QListWidgetItem(f"{stat.tag}: {stat.text}")
                    self.stats_list.addItem(item)
                    
        # Додаємо інші важливі параметри
        cost_list = self.current_definition.find("costList")
        if cost_list is not None:
            cost_items = []
            for cost in cost_list:
                if cost.text:
                    cost_items.append(f"{cost.tag}: {cost.text}")
            if cost_items:
                item = QListWidgetItem(f"Cost: {', '.join(cost_items)}")
                self.stats_list.addItem(item)
                
    def load_recipe_stats(self):
        """Завантаження статистик RecipeDef"""
        work_amount = self.get_element_text("workAmount", "Невідомо")
        work_skill = self.get_element_text("workSkill", "Невідомо")
        
        self.stats_list.addItem(QListWidgetItem(f"Work Amount: {work_amount}"))
        self.stats_list.addItem(QListWidgetItem(f"Work Skill: {work_skill}"))
        
        # Інгредієнти
        ingredients = self.current_definition.find("ingredients")
        if ingredients is not None:
            for ingredient in ingredients:
                filter_elem = ingredient.find("filter")
                count_elem = ingredient.find("count")
                if filter_elem is not None and count_elem is not None:
                    thingdefs = filter_elem.find("thingDefs")
                    if thingdefs is not None:
                        for thingdef in thingdefs:
                            if thingdef.text:
                                item = QListWidgetItem(f"Ingredient: {thingdef.text} x{count_elem.text}")
                                self.stats_list.addItem(item)
                                
    def load_research_stats(self):
        """Завантаження статистик ResearchProjectDef"""
        base_cost = self.get_element_text("baseCost", "Невідомо")
        tech_level = self.get_element_text("techLevel", "Невідомо")
        
        self.stats_list.addItem(QListWidgetItem(f"Base Cost: {base_cost}"))
        self.stats_list.addItem(QListWidgetItem(f"Tech Level: {tech_level}"))
        
    def find_texture_file(self, mod_path: str, tex_path: str) -> str:
        """Пошук файлу текстури в моді"""
        # Шукаємо в папці Textures
        textures_dir = os.path.join(os.path.dirname(mod_path), "Textures")
        if not os.path.exists(textures_dir):
            return None
            
        # Можливі розширення
        extensions = [".png", ".jpg", ".jpeg"]
        
        for ext in extensions:
            full_path = os.path.join(textures_dir, tex_path + ext)
            if os.path.exists(full_path):
                return full_path
                
        return None
        
    def load_texture_preview(self, texture_path: str):
        """Завантаження попереднього перегляду текстури"""
        try:
            pixmap = QPixmap(texture_path)
            if not pixmap.isNull():
                # Масштабуємо зображення
                scaled_pixmap = pixmap.scaled(
                    200, 200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.show_placeholder_image("Texture")
        except Exception as e:
            self.show_placeholder_image(f"Error: {e}")
            
    def create_placeholder_texture(self, tex_path: str):
        """Створення заглушки для текстури"""
        # Створюємо просте зображення-заглушку
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor(200, 200, 200))
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(10, 10, 180, 180)
        
        # Додаємо текст
        painter.drawText(20, 100, f"Texture:\n{os.path.basename(tex_path)}")
        painter.end()
        
        self.image_label.setPixmap(pixmap)
        
    def create_pawnkind_placeholder(self):
        """Створення заглушки для PawnKindDef"""
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor(220, 220, 255))
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(50, 50, 150), 2))
        
        # Малюємо простий силует людини
        painter.drawEllipse(80, 30, 40, 40)  # Голова
        painter.drawLine(100, 70, 100, 140)  # Тіло
        painter.drawLine(100, 90, 70, 110)   # Ліва рука
        painter.drawLine(100, 90, 130, 110)  # Права рука
        painter.drawLine(100, 140, 80, 170)  # Ліва нога
        painter.drawLine(100, 140, 120, 170) # Права нога
        
        painter.drawText(20, 190, "PawnKind")
        painter.end()
        
        self.image_label.setPixmap(pixmap)
        
    def show_placeholder_image(self, def_type: str):
        """Показати заглушку для типу дефініції"""
        pixmap = QPixmap(200, 200)
        pixmap.fill(QColor(240, 240, 240))
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(10, 10, 180, 180)
        painter.drawText(20, 100, f"Preview for\n{def_type}\nnot available")
        painter.end()
        
        self.image_label.setPixmap(pixmap)
        
    def get_element_text(self, tag_name: str, default: str = "") -> str:
        """Отримання тексту елемента"""
        if not self.current_definition:
            return default
            
        element = self.current_definition.find(tag_name)
        if element is not None and element.text:
            return element.text.strip()
        return default
        
    def get_additional_info_by_type(self, def_type: str) -> str:
        """Отримання додаткової інформації залежно від типу"""
        info = []
        
        if def_type == "ThingDef":
            thing_class = self.get_element_text("thingClass")
            category = self.get_element_text("category")
            if thing_class:
                info.append(f"Thing Class: {thing_class}")
            if category:
                info.append(f"Category: {category}")
                
        elif def_type == "RecipeDef":
            work_amount = self.get_element_text("workAmount")
            work_skill = self.get_element_text("workSkill")
            if work_amount:
                info.append(f"Work Amount: {work_amount}")
            if work_skill:
                info.append(f"Work Skill: {work_skill}")
                
        elif def_type == "PawnKindDef":
            race = self.get_element_text("race")
            combat_power = self.get_element_text("combatPower")
            if race:
                info.append(f"Race: {race}")
            if combat_power:
                info.append(f"Combat Power: {combat_power}")
                
        return "\n".join(info) if info else "Додаткова інформація недоступна"
        
    def clear_preview(self):
        """Очищення попереднього перегляду"""
        self.current_definition = None
        self.title_label.setText("Попередній перегляд")
        
        self.def_name_label.setText("DefName: -")
        self.label_label.setText("Label: -")
        self.description_label.setText("Description: -")
        self.type_label.setText("Тип: -")
        
        self.additional_info.clear()
        self.graphics_info.clear()
        self.stats_list.clear()
        
        self.image_label.clear()
        self.image_label.setText("Зображення недоступне")
        
    def show_error(self, error_message: str):
        """Показати повідомлення про помилку"""
        self.clear_preview()
        self.title_label.setText("Помилка попереднього перегляду")
        self.additional_info.setPlainText(error_message)
