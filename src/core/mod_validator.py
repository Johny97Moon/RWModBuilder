"""
Валідатор модів RimWorld
"""

import os
from typing import Dict, Any
from utils.xml_validator import XmlValidator


class ModValidator:
    """Валідатор для перевірки структури та змісту модів RimWorld"""

    def __init__(self):
        self.xml_validator = XmlValidator()

    def validate_mod_structure(self, mod_path: str) -> Dict[str, Any]:
        """Валідація структури мода"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': []
        }

        # Перевіряємо обов'язкові папки
        required_folders = ['About']
        for folder in required_folders:
            folder_path = os.path.join(mod_path, folder)
            if not os.path.exists(folder_path):
                result['errors'].append(f"Відсутня обов'язкова папка: {folder}")
                result['valid'] = False

        # Перевіряємо About.xml
        about_path = os.path.join(mod_path, 'About', 'About.xml')
        if os.path.exists(about_path):
            xml_result = self.xml_validator.validate_file(about_path)
            if not xml_result['valid']:
                result['errors'].extend(xml_result['errors'])
                result['valid'] = False
        else:
            result['errors'].append("Відсутній файл About.xml")
            result['valid'] = False

        return result

    def validate_definitions(self, mod_path: str) -> Dict[str, Any]:
        """Валідація дефініцій мода"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        defs_path = os.path.join(mod_path, 'Defs')
        if not os.path.exists(defs_path):
            result['warnings'].append("Папка Defs не знайдена")
            return result

        # Перевіряємо всі XML файли в папці Defs
        for root, _, files in os.walk(defs_path):
            for file in files:
                if file.endswith('.xml'):
                    file_path = os.path.join(root, file)
                    xml_result = self.xml_validator.validate_file(file_path)
                    if not xml_result['valid']:
                        result['errors'].extend([f"{file}: {error}" for error in xml_result['errors']])
                        result['valid'] = False

        return result
