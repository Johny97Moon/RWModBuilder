#!/usr/bin/env python3
"""
Спрощений XML валідатор для RimWorld Mod Builder
Валідація XML файлів без залежності від lxml
"""

import xml.etree.ElementTree as ET
import re
from pathlib import Path

class SimpleXMLValidator:
    """Спрощений валідатор XML для RimWorld модів"""
    
    def __init__(self):
        self.rimworld_tags = self.load_rimworld_tags()
        self.errors = []
        self.warnings = []
        
    def load_rimworld_tags(self):
        """Завантаження списку відомих RimWorld тегів"""
        return {
            # Основні теги
            'ModMetaData', 'Defs', 'ThingDef', 'RecipeDef', 'ResearchProjectDef',
            'PawnKindDef', 'TraitDef', 'FactionDef', 'BiomeDef', 'JobDef', 'WorkGiverDef',
            
            # Метадані мода
            'name', 'author', 'packageId', 'description', 'supportedVersions',
            'modDependencies', 'incompatibleWith', 'loadAfter', 'loadBefore',
            
            # ThingDef теги
            'defName', 'label', 'thingClass', 'category', 'tickerType', 'altitudeLayer',
            'passability', 'pathCost', 'useHitPoints', 'selectable', 'drawGUIOverlay',
            'rotatable', 'fillPercent', 'statBases', 'costList', 'graphicData',
            'researchPrerequisites', 'constructionSkillPrerequisite', 'designationCategory',
            'placingDraggableDimensions', 'terrainAffordanceNeeded', 'constructEffect',
            'repairEffect', 'filthLeaving', 'leaveResourcesWhenKilled', 'resourcesFractionWhenDeconstructed',
            
            # Статистики
            'MaxHitPoints', 'WorkToBuild', 'Flammability', 'Beauty', 'Mass', 'MarketValue',
            'DeteriorationRate', 'SellPriceFactor', 'Comfort', 'Nutrition', 'FoodPoisonChance',
            
            # Графіка
            'texPath', 'graphicClass', 'drawSize', 'color', 'colorTwo', 'drawRotated',
            'allowFlip', 'flipExtraRotation', 'shadowData', 'damageData',
            
            # Рецепти
            'jobString', 'workSpeedStat', 'workSkill', 'effectWorking', 'soundWorking',
            'workAmount', 'unfinishedThingDef', 'ingredients', 'products', 'recipeUsers',
            'researchPrerequisite', 'skillRequirements', 'workSkillLearnFactor',
            
            # Дослідження
            'baseCost', 'techLevel', 'prerequisites', 'researchViewX', 'researchViewY',
            'requiredResearchBuilding', 'requiredResearchFacilities', 'tab',
            
            # Загальні
            'li', 'count', 'filter', 'thingDefs', 'categories', 'stuffCategories'
        }
        
    def validate_xml_syntax(self, content):
        """Валідація синтаксису XML"""
        self.errors = []
        self.warnings = []
        
        try:
            ET.fromstring(content)
            return True
        except ET.ParseError as e:
            self.errors.append(f"Синтаксична помилка XML: {e}")
            return False
            
    def validate_rimworld_structure(self, content):
        """Валідація структури RimWorld мода"""
        try:
            root = ET.fromstring(content)
            
            # Перевірка кореневого елемента
            if root.tag == 'ModMetaData':
                self.validate_mod_metadata(root)
            elif root.tag == 'Defs':
                self.validate_defs_structure(root)
            else:
                self.warnings.append(f"Незвичний кореневий елемент: {root.tag}")
                
            # Перевірка невідомих тегів
            self.check_unknown_tags(root)
            
        except ET.ParseError:
            # Синтаксичні помилки вже перевірені
            pass
            
    def validate_mod_metadata(self, root):
        """Валідація метаданих мода (About.xml)"""
        required_tags = ['name', 'author', 'packageId', 'supportedVersions']
        
        for tag in required_tags:
            if root.find(tag) is None:
                self.errors.append(f"Відсутній обов'язковий тег: <{tag}>")
                
        # Перевірка packageId
        package_id_elem = root.find('packageId')
        if package_id_elem is not None:
            package_id = package_id_elem.text
            if not self.validate_package_id(package_id):
                self.errors.append(f"Неправильний формат packageId: {package_id}")
                
        # Перевірка supportedVersions
        supported_versions = root.find('supportedVersions')
        if supported_versions is not None:
            if len(supported_versions.findall('li')) == 0:
                self.warnings.append("supportedVersions не містить жодної версії")
                
    def validate_package_id(self, package_id):
        """Валідація формату packageId"""
        if not package_id:
            return False
            
        # packageId повинен бути у форматі author.modname
        pattern = r'^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$'
        return bool(re.match(pattern, package_id))
        
    def validate_defs_structure(self, root):
        """Валідація структури дефініцій"""
        def_count = 0
        
        for child in root:
            def_count += 1
            
            # Перевірка defName
            def_name_elem = child.find('defName')
            if def_name_elem is None:
                self.errors.append(f"Дефініція {child.tag} не має defName")
            elif not def_name_elem.text:
                self.errors.append(f"Порожній defName у дефініції {child.tag}")
                
            # Перевірка label для видимих об'єктів
            if child.tag in ['ThingDef', 'RecipeDef', 'ResearchProjectDef']:
                label_elem = child.find('label')
                if label_elem is None:
                    self.warnings.append(f"Дефініція {child.tag} не має label")
                    
        if def_count == 0:
            self.warnings.append("Файл Defs не містить жодної дефініції")
            
    def check_unknown_tags(self, element, path=""):
        """Перевірка невідомих тегів"""
        current_path = f"{path}/{element.tag}" if path else element.tag
        
        if element.tag not in self.rimworld_tags:
            # Ігноруємо деякі загальні теги
            if element.tag not in ['li', 'count'] and not element.tag.endswith('Def'):
                self.warnings.append(f"Невідомий тег: {current_path}")
                
        for child in element:
            self.check_unknown_tags(child, current_path)
            
    def validate_file(self, file_path):
        """Валідація XML файлу"""
        try:
            content = Path(file_path).read_text(encoding='utf-8')
            return self.validate_content(content)
        except Exception as e:
            self.errors = [f"Помилка читання файлу: {e}"]
            return False
            
    def validate_content(self, content):
        """Валідація вмісту XML"""
        # Перевірка синтаксису
        if not self.validate_xml_syntax(content):
            return False
            
        # Перевірка структури RimWorld
        self.validate_rimworld_structure(content)
        
        return len(self.errors) == 0
        
    def get_validation_report(self):
        """Отримання звіту валідації"""
        report = {
            'valid': len(self.errors) == 0,
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy(),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
        
        return report
        
    def format_report(self, report):
        """Форматування звіту для відображення"""
        lines = []
        
        if report['valid']:
            lines.append("✅ XML файл валідний!")
        else:
            lines.append("❌ XML файл містить помилки!")
            
        if report['errors']:
            lines.append("\n🔴 Помилки:")
            for i, error in enumerate(report['errors'], 1):
                lines.append(f"  {i}. {error}")
                
        if report['warnings']:
            lines.append("\n🟡 Попередження:")
            for i, warning in enumerate(report['warnings'], 1):
                lines.append(f"  {i}. {warning}")
                
        if not report['errors'] and not report['warnings']:
            lines.append("\n🎉 Файл не містить помилок або попереджень!")
            
        return "\n".join(lines)
        
    def quick_validate(self, content):
        """Швидка валідація для показу в реальному часі"""
        try:
            ET.fromstring(content)
            return True, "XML синтаксично правильний"
        except ET.ParseError as e:
            return False, f"XML помилка: {str(e)}"
        except Exception as e:
            return False, f"Помилка: {str(e)}"
