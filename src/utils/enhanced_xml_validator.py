#!/usr/bin/env python3
"""
Покращений XML валідатор без залежності від lxml
Повна заміна lxml функціональності для RimWorld Mod Builder
"""

import xml.etree.ElementTree as ET
import xml.dom.minidom
import re
import io
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


class EnhancedXMLValidator:
    """Покращений XML валідатор без залежності від lxml"""
    
    def __init__(self):
        self.rimworld_tags = self.load_rimworld_tags()
        self.rimworld_attributes = self.load_rimworld_attributes()
        
    def load_rimworld_tags(self) -> Dict[str, List[str]]:
        """Завантаження відомих RimWorld XML тегів"""
        return {
            "Defs": ["ThingDef", "RecipeDef", "ResearchProjectDef", "JobDef", "WorkGiverDef"],
            "ThingDef": ["defName", "label", "description", "thingClass", "category", "statBases", "comps"],
            "RecipeDef": ["defName", "label", "description", "jobString", "workAmount", "ingredients", "products"],
            "ResearchProjectDef": ["defName", "label", "description", "baseCost", "techLevel", "prerequisites"],
            "statBases": ["MaxHitPoints", "Mass", "Beauty", "WorkToMake", "MarketValue"],
            "comps": ["CompProperties_Forbiddable", "CompProperties_Rottable", "CompProperties_Usable"],
            "ingredients": ["li"],
            "products": ["li"],
            "prerequisites": ["li"]
        }
    
    def load_rimworld_attributes(self) -> Dict[str, List[str]]:
        """Завантаження відомих RimWorld XML атрибутів"""
        return {
            "ThingDef": ["ParentName", "Name", "Abstract"],
            "RecipeDef": ["ParentName", "Name"],
            "li": ["Class"],
            "comp": ["Class"]
        }
    
    def validate_xml_syntax(self, content: str) -> Dict[str, Any]:
        """Валідація синтаксису XML"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        if not content.strip():
            result["valid"] = False
            result["errors"].append("XML файл порожній")
            return result
        
        try:
            # Перевірка базового синтаксису
            root = ET.fromstring(content)
            result["info"].append(f"XML синтаксично коректний. Кореневий елемент: <{root.tag}>")
            
            # Додаткові перевірки
            self._check_xml_declaration(content, result)
            self._check_encoding(content, result)
            self._check_well_formed(content, result)
            
        except ET.ParseError as e:
            result["valid"] = False
            result["errors"].append(f"XML синтаксична помилка: {e}")
            
            # Спроба надати більш детальну інформацію про помилку
            self._analyze_parse_error(content, str(e), result)
            
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Неочікувана помилка при парсингу XML: {e}")
        
        return result
    
    def validate_rimworld_structure(self, content: str) -> Dict[str, Any]:
        """Валідація структури RimWorld XML"""
        result = self.validate_xml_syntax(content)
        
        if not result["valid"]:
            return result
        
        try:
            root = ET.fromstring(content)
            
            # Перевірка кореневого елемента
            if root.tag not in ["Defs", "GameData", "LanguageData", "Patch"]:
                result["warnings"].append(f"Незвичний кореневий елемент: <{root.tag}>. Очікувалося: Defs, GameData, LanguageData або Patch")
            
            # Валідація структури Defs
            if root.tag == "Defs":
                self._validate_defs_structure(root, result)
            
            # Валідація структури Patch
            elif root.tag == "Patch":
                self._validate_patch_structure(root, result)
            
            # Перевірка загальних помилок
            self._check_common_issues(root, result)
            
        except Exception as e:
            result["errors"].append(f"Помилка валідації структури: {e}")
            result["valid"] = False
        
        return result
    
    def format_xml(self, content: str, indent: str = "  ") -> str:
        """Форматування XML з відступами (заміна lxml.etree.tostring)"""
        try:
            # Парсинг XML
            root = ET.fromstring(content)
            
            # Додавання відступів
            self._indent_xml(root, 0, indent)
            
            # Конвертація назад в строку
            rough_string = ET.tostring(root, encoding='unicode')
            
            # Додавання XML декларації якщо потрібно
            if not content.strip().startswith('<?xml'):
                rough_string = '<?xml version="1.0" encoding="utf-8"?>\n' + rough_string
            
            return rough_string
            
        except ET.ParseError as e:
            # Якщо не вдається парсити, повертаємо оригінал
            return content
        except Exception as e:
            return content
    
    def validate_def_structure(self, content: str, def_type: str = None) -> Dict[str, Any]:
        """Валідація структури конкретного типу Def"""
        result = self.validate_xml_syntax(content)
        
        if not result["valid"]:
            return result
        
        try:
            root = ET.fromstring(content)
            
            # Знаходження всіх Def елементів
            defs = []
            if root.tag.endswith("Def"):
                defs = [root]
            else:
                defs = [elem for elem in root if elem.tag.endswith("Def")]
            
            for def_elem in defs:
                self._validate_single_def(def_elem, result, def_type)
                
        except Exception as e:
            result["errors"].append(f"Помилка валідації Def структури: {e}")
            result["valid"] = False
        
        return result
    
    def _check_xml_declaration(self, content: str, result: Dict):
        """Перевірка XML декларації"""
        if not content.strip().startswith('<?xml'):
            result["warnings"].append("Відсутня XML декларація. Рекомендується додати: <?xml version=\"1.0\" encoding=\"utf-8\"?>")
        else:
            # Перевірка кодування
            if 'encoding=' not in content[:100]:
                result["warnings"].append("Не вказано кодування в XML декларації")
            elif 'utf-8' not in content[:100].lower():
                result["warnings"].append("Рекомендується використовувати UTF-8 кодування")
    
    def _check_encoding(self, content: str, result: Dict):
        """Перевірка кодування"""
        try:
            # Спроба декодувати як UTF-8
            content.encode('utf-8')
        except UnicodeEncodeError:
            result["warnings"].append("Файл містить символи, які можуть викликати проблеми з кодуванням")
    
    def _check_well_formed(self, content: str, result: Dict):
        """Перевірка правильності формування XML"""
        # Перевірка парних тегів
        open_tags = re.findall(r'<([^/!?][^>]*)>', content)
        close_tags = re.findall(r'</([^>]+)>', content)
        
        # Видалення самозакривних тегів
        self_closing = re.findall(r'<([^/!?][^>]*)/>', content)
        open_tags = [tag.split()[0] for tag in open_tags if tag.split()[0] not in [sc.split()[0] for sc in self_closing]]
        
        if len(open_tags) != len(close_tags):
            result["warnings"].append(f"Можлива невідповідність відкриваючих ({len(open_tags)}) та закриваючих ({len(close_tags)}) тегів")
    
    def _analyze_parse_error(self, content: str, error_msg: str, result: Dict):
        """Аналіз помилки парсингу для надання корисних порад"""
        lines = content.split('\n')
        
        # Пошук номера рядка в помилці
        line_match = re.search(r'line (\d+)', error_msg)
        if line_match:
            line_num = int(line_match.group(1))
            if line_num <= len(lines):
                problematic_line = lines[line_num - 1]
                result["info"].append(f"Проблемний рядок {line_num}: {problematic_line.strip()}")
                
                # Аналіз типових помилок
                if '<' in problematic_line and '>' not in problematic_line:
                    result["info"].append("Можлива причина: незакритий тег")
                elif '&' in problematic_line and ';' not in problematic_line:
                    result["info"].append("Можлива причина: неекранований символ &")
    
    def _validate_defs_structure(self, root: ET.Element, result: Dict):
        """Валідація структури Defs"""
        def_count = 0
        
        for child in root:
            if child.tag.endswith("Def"):
                def_count += 1
                self._validate_single_def(child, result)
            else:
                result["warnings"].append(f"Незвичний елемент в Defs: <{child.tag}>")
        
        if def_count == 0:
            result["warnings"].append("Defs не містить жодного Def елемента")
        else:
            result["info"].append(f"Знайдено {def_count} Def елементів")
    
    def _validate_patch_structure(self, root: ET.Element, result: Dict):
        """Валідація структури Patch"""
        operations = ["add", "replace", "remove", "insert", "move", "copy", "test"]
        operation_count = 0
        
        for child in root:
            if child.tag.lower() in operations:
                operation_count += 1
            else:
                result["warnings"].append(f"Незвичний елемент в Patch: <{child.tag}>")
        
        if operation_count == 0:
            result["warnings"].append("Patch не містить жодної операції")
        else:
            result["info"].append(f"Знайдено {operation_count} patch операцій")
    
    def _validate_single_def(self, def_elem: ET.Element, result: Dict, expected_type: str = None):
        """Валідація одного Def елемента"""
        def_type = def_elem.tag
        
        # Перевірка типу Def
        if expected_type and def_type != expected_type:
            result["warnings"].append(f"Очікувався {expected_type}, знайдено {def_type}")
        
        # Перевірка обов'язкових елементів
        def_name = def_elem.find('defName')
        if def_name is None:
            result["errors"].append(f"{def_type} не має обов'язкового елемента <defName>")
            result["valid"] = False
        elif not def_name.text or not def_name.text.strip():
            result["errors"].append(f"{def_type} має порожній <defName>")
            result["valid"] = False
        
        # Перевірка рекомендованих елементів
        if def_elem.find('label') is None:
            result["warnings"].append(f"{def_type} не має <label> (рекомендується)")
        
        if def_elem.find('description') is None:
            result["warnings"].append(f"{def_type} не має <description> (рекомендується)")
        
        # Перевірка специфічних для типу елементів
        if def_type in self.rimworld_tags:
            expected_children = self.rimworld_tags[def_type]
            for child in def_elem:
                if child.tag not in expected_children and child.tag not in ["defName", "label", "description"]:
                    result["info"].append(f"Незвичний елемент в {def_type}: <{child.tag}>")
    
    def _check_common_issues(self, root: ET.Element, result: Dict):
        """Перевірка загальних проблем"""
        # Перевірка порожніх елементів
        for elem in root.iter():
            if elem.text is None and len(elem) == 0 and elem.tag not in ["li"]:
                result["warnings"].append(f"Порожній елемент: <{elem.tag}>")
        
        # Перевірка дублікатів defName
        def_names = []
        for def_elem in root.iter():
            if def_elem.tag.endswith("Def"):
                def_name_elem = def_elem.find('defName')
                if def_name_elem is not None and def_name_elem.text:
                    if def_name_elem.text in def_names:
                        result["errors"].append(f"Дублікат defName: {def_name_elem.text}")
                        result["valid"] = False
                    else:
                        def_names.append(def_name_elem.text)
    
    def _indent_xml(self, elem: ET.Element, level: int = 0, indent: str = "  "):
        """Додавання відступів до XML елементів"""
        i = "\n" + level * indent
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + indent
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level + 1, indent)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def get_xml_statistics(self, content: str) -> Dict[str, Any]:
        """Отримання статистики XML файлу"""
        stats = {
            "total_elements": 0,
            "total_attributes": 0,
            "def_count": 0,
            "def_types": {},
            "file_size": len(content.encode('utf-8')),
            "line_count": len(content.split('\n'))
        }
        
        try:
            root = ET.fromstring(content)
            
            # Підрахунок елементів та атрибутів
            for elem in root.iter():
                stats["total_elements"] += 1
                stats["total_attributes"] += len(elem.attrib)
                
                # Підрахунок Def елементів
                if elem.tag.endswith("Def"):
                    stats["def_count"] += 1
                    def_type = elem.tag
                    stats["def_types"][def_type] = stats["def_types"].get(def_type, 0) + 1
                    
        except Exception:
            pass
        
        return stats


# Функція для зворотної сумісності
def validate_xml(content: str) -> Dict[str, Any]:
    """Функція для зворотної сумісності з lxml"""
    validator = EnhancedXMLValidator()
    return validator.validate_rimworld_structure(content)


def format_xml(content: str) -> str:
    """Функція для зворотної сумісності з lxml"""
    validator = EnhancedXMLValidator()
    return validator.format_xml(content)


# Тестування модуля
if __name__ == "__main__":
    # Тест валідатора
    test_xml = '''<?xml version="1.0" encoding="utf-8"?>
<Defs>
    <ThingDef ParentName="BaseThing">
        <defName>TestItem</defName>
        <label>Test Item</label>
        <description>A test item for validation</description>
        <thingClass>ThingWithComps</thingClass>
        <category>Item</category>
        <statBases>
            <MaxHitPoints>100</MaxHitPoints>
            <Mass>1.0</Mass>
        </statBases>
    </ThingDef>
</Defs>'''
    
    validator = EnhancedXMLValidator()
    result = validator.validate_rimworld_structure(test_xml)
    
    print("🔍 Тест Enhanced XML Validator")
    print(f"Валідний: {result['valid']}")
    print(f"Помилки: {result['errors']}")
    print(f"Попередження: {result['warnings']}")
    print(f"Інформація: {result['info']}")
    
    # Тест форматування
    formatted = validator.format_xml(test_xml)
    print("\n📝 Форматований XML:")
    print(formatted[:200] + "..." if len(formatted) > 200 else formatted)
