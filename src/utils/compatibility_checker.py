"""
Система перевірки сумісності модів RimWorld
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict
import re


class CompatibilityChecker:
    """Перевірка сумісності модів RimWorld"""
    
    def __init__(self):
        self.rimworld_versions = ["1.0", "1.1", "1.2", "1.3", "1.4", "1.5"]
        self.deprecated_tags = self._load_deprecated_tags()
        self.version_changes = self._load_version_changes()
        
    def _load_deprecated_tags(self) -> Dict[str, Dict]:
        """Завантаження списку застарілих тегів"""
        return {
            "1.3": {
                "deprecated": [
                    "tickerType",  # Замінено на компоненти
                    "useHitPoints",  # Тепер автоматично
                ],
                "removed": [
                    "drawGUIOverlay",  # Видалено в 1.3
                ]
            },
            "1.4": {
                "deprecated": [
                    "socialPropernessMatters",  # Застаріло в 1.4
                ],
                "removed": [
                    "race.intelligence",  # Замінено на intelligence
                ]
            },
            "1.5": {
                "deprecated": [
                    "defaultOutfitTags",  # Застаріло в 1.5
                ],
                "removed": [
                    "race.hasGenders",  # Видалено в 1.5
                ]
            }
        }
        
    def _load_version_changes(self) -> Dict[str, Dict]:
        """Завантаження змін між версіями"""
        return {
            "1.3": {
                "new_features": [
                    "Ideology DLC support",
                    "Мемы та ідеології",
                    "Нові компоненти для ThingDef"
                ],
                "breaking_changes": [
                    "Зміна системи тікерів",
                    "Нова система компонентів"
                ]
            },
            "1.4": {
                "new_features": [
                    "Biotech DLC support", 
                    "Генетика та ксеноморфи",
                    "Механоїди"
                ],
                "breaking_changes": [
                    "Зміна системи рас",
                    "Нові типи пешок"
                ]
            },
            "1.5": {
                "new_features": [
                    "Anomaly DLC support",
                    "Аномальні події",
                    "Нові типи дослідження"
                ],
                "breaking_changes": [
                    "Зміна системи статей",
                    "Оновлення AI"
                ]
            }
        }
        
    def check_mod_compatibility(self, mod_path: str) -> Dict:
        """Перевірка сумісності мода"""
        result = {
            "compatible": True,
            "warnings": [],
            "errors": [],
            "suggestions": [],
            "supported_versions": [],
            "deprecated_features": [],
            "missing_dependencies": []
        }
        
        try:
            # Перевіряємо About.xml
            about_path = os.path.join(mod_path, "About", "About.xml")
            if os.path.exists(about_path):
                self._check_about_xml(about_path, result)
            else:
                result["errors"].append("Відсутній файл About/About.xml")
                result["compatible"] = False
                
            # Перевіряємо дефініції
            defs_path = os.path.join(mod_path, "Defs")
            if os.path.exists(defs_path):
                self._check_definitions(defs_path, result)
                
            # Перевіряємо патчі
            patches_path = os.path.join(mod_path, "Patches")
            if os.path.exists(patches_path):
                self._check_patches(patches_path, result)
                
        except Exception as e:
            result["errors"].append(f"Помилка перевірки сумісності: {e}")
            result["compatible"] = False
            
        return result
        
    def _check_about_xml(self, about_path: str, result: Dict):
        """Перевірка файлу About.xml"""
        try:
            tree = ET.parse(about_path)
            root = tree.getroot()
            
            # Перевіряємо підтримувані версії
            supported_versions = root.find("supportedVersions")
            if supported_versions is not None:
                versions = []
                for version_elem in supported_versions:
                    if version_elem.tag == "li" and version_elem.text:
                        versions.append(version_elem.text.strip())
                        
                result["supported_versions"] = versions
                
                # Перевіряємо актуальність версій
                latest_version = self.rimworld_versions[-1]
                if latest_version not in versions:
                    result["warnings"].append(
                        f"Мод не підтримує останню версію RimWorld ({latest_version})"
                    )
                    
                # Перевіряємо застарілі версії
                old_versions = [v for v in versions if v in ["1.0", "1.1"]]
                if old_versions:
                    result["warnings"].append(
                        f"Мод підтримує застарілі версії: {', '.join(old_versions)}"
                    )
            else:
                result["errors"].append("Відсутній тег supportedVersions в About.xml")
                result["compatible"] = False
                
            # Перевіряємо залежності
            dependencies = root.find("modDependencies")
            if dependencies is not None:
                self._check_dependencies(dependencies, result)
                
            # Перевіряємо порядок завантаження
            load_after = root.find("loadAfter")
            if load_after is not None:
                self._check_load_order(load_after, result, "loadAfter")
                
            load_before = root.find("loadBefore")
            if load_before is not None:
                self._check_load_order(load_before, result, "loadBefore")
                
        except ET.ParseError as e:
            result["errors"].append(f"Помилка парсингу About.xml: {e}")
            result["compatible"] = False
            
    def _check_dependencies(self, dependencies_elem: ET.Element, result: Dict):
        """Перевірка залежностей мода"""
        for dep in dependencies_elem:
            if dep.tag == "li":
                package_id = dep.find("packageId")
                # display_name = dep.find("displayName")  # Поки не використовується

                if package_id is not None and package_id.text:
                    # Перевіряємо формат packageId
                    if not self._is_valid_package_id(package_id.text):
                        result["warnings"].append(
                            f"Невалідний packageId залежності: {package_id.text}"
                        )
                        
                    # Перевіряємо відомі моди
                    if self._is_known_problematic_mod(package_id.text):
                        result["warnings"].append(
                            f"Залежність від проблематичного мода: {package_id.text}"
                        )
                        
    def _check_load_order(self, load_order_elem: ET.Element, result: Dict, order_type: str):
        """Перевірка порядку завантаження"""
        for item in load_order_elem:
            if item.tag == "li" and item.text:
                package_id = item.text.strip()
                
                if not self._is_valid_package_id(package_id):
                    result["warnings"].append(
                        f"Невалідний packageId в {order_type}: {package_id}"
                    )
                    
    def _check_definitions(self, defs_path: str, result: Dict):
        """Перевірка файлів дефініцій"""
        for root, _, files in os.walk(defs_path):
            for file in files:
                if file.endswith('.xml'):
                    file_path = os.path.join(root, file)
                    self._check_definition_file(file_path, result)
                    
    def _check_definition_file(self, file_path: str, result: Dict):
        """Перевірка окремого файлу дефініції"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            if root.tag == "Defs":
                for def_elem in root:
                    self._check_definition_element(def_elem, result, file_path)
                    
        except ET.ParseError as e:
            result["warnings"].append(f"Помилка парсингу {file_path}: {e}")
            
    def _check_definition_element(self, def_elem: ET.Element, result: Dict, file_path: str):
        """Перевірка окремого елемента дефініції"""
        _ = file_path  # Заглушка для unused parameter
        def_type = def_elem.tag
        
        # Перевіряємо застарілі теги
        for version_str, version_data in self.deprecated_tags.items():
            deprecated_tags = version_data.get("deprecated", [])
            removed_tags = version_data.get("removed", [])
            
            for child in def_elem.iter():
                if child.tag in deprecated_tags:
                    result["deprecated_features"].append(
                        f"Застарілий тег '{child.tag}' в {def_type} (з версії {version_str})"
                    )
                    
                if child.tag in removed_tags:
                    result["errors"].append(
                        f"Видалений тег '{child.tag}' в {def_type} (з версії {version_str})"
                    )
                    result["compatible"] = False
                    
        # Перевіряємо специфічні правила для типів дефініцій
        if def_type == "ThingDef":
            self._check_thingdef_compatibility(def_elem, result)
        elif def_type == "PawnKindDef":
            self._check_pawnkinddef_compatibility(def_elem, result)
            
    def _check_thingdef_compatibility(self, thingdef_elem: ET.Element, result: Dict):
        """Перевірка сумісності ThingDef"""
        # Перевіряємо наявність обов'язкових тегів для нових версій
        thing_class = thingdef_elem.find("thingClass")
        if thing_class is not None and thing_class.text:
            # Перевіряємо відомі проблематичні класи
            if "Building_" in thing_class.text and thingdef_elem.find("building") is None:
                result["warnings"].append(
                    "ThingDef з Building_ класом без тегу <building>"
                )
                
        # Перевіряємо графічні дані
        graphic_data = thingdef_elem.find("graphicData")
        if graphic_data is not None:
            tex_path = graphic_data.find("texPath")
            if tex_path is not None and tex_path.text:
                # Перевіряємо формат шляху до текстури
                if not self._is_valid_texture_path(tex_path.text):
                    result["warnings"].append(
                        f"Можливо невалідний шлях до текстури: {tex_path.text}"
                    )
                    
    def _check_pawnkinddef_compatibility(self, pawnkind_elem: ET.Element, result: Dict):
        """Перевірка сумісності PawnKindDef"""
        # Перевіряємо расу
        race = pawnkind_elem.find("race")
        if race is not None and race.text:
            if not self._is_valid_def_reference(race.text):
                result["warnings"].append(
                    f"Можливо невалідне посилання на расу: {race.text}"
                )
                
    def _check_patches(self, patches_path: str, result: Dict):
        """Перевірка патчів"""
        for root, _, files in os.walk(patches_path):
            for file in files:
                if file.endswith('.xml'):
                    file_path = os.path.join(root, file)
                    self._check_patch_file(file_path, result)
                    
    def _check_patch_file(self, file_path: str, result: Dict):
        """Перевірка файлу патчу"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            if root.tag == "Patch":
                # Перевіряємо операції патчу
                for operation in root:
                    if operation.tag == "Operation":
                        self._check_patch_operation(operation, result, file_path)
                        
        except ET.ParseError as e:
            result["warnings"].append(f"Помилка парсингу патчу {file_path}: {e}")
            
    def _check_patch_operation(self, operation: ET.Element, result: Dict, file_path: str):
        """Перевірка операції патчу"""
        class_attr = operation.get("Class")
        if class_attr:
            # Перевіряємо відомі проблематичні операції
            if "PatchOperationReplace" in class_attr:
                result["suggestions"].append(
                    f"Використання PatchOperationReplace в {file_path} може викликати конфлікти"
                )
                
    def _is_valid_package_id(self, package_id: str) -> bool:
        """Перевірка валідності packageId"""
        if not package_id:
            return False
        # packageId має бути у форматі author.modname
        return bool(re.match(r'^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+', package_id))
        
    def _is_valid_texture_path(self, tex_path: str) -> bool:
        """Перевірка валідності шляху до текстури"""
        if not tex_path:
            return False
        # Перевіряємо базові правила для шляхів
        return not tex_path.startswith('/') and not tex_path.endswith('/')
        
    def _is_valid_def_reference(self, def_ref: str) -> bool:
        """Перевірка валідності посилання на дефініцію"""
        if not def_ref:
            return False
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', def_ref))
        
    def _is_known_problematic_mod(self, package_id: str) -> bool:
        """Перевірка чи є мод відомо проблематичним"""
        problematic_mods = [
            "example.problematicmod",  # Приклад
        ]
        return package_id.lower() in [mod.lower() for mod in problematic_mods]
        
    def get_compatibility_report(self, mod_path: str) -> str:
        """Отримання текстового звіту про сумісність"""
        result = self.check_mod_compatibility(mod_path)
        
        report = []
        report.append("=== ЗВІТ ПРО СУМІСНІСТЬ МОДА ===\n")
        
        if result["compatible"]:
            report.append("✅ Мод сумісний з RimWorld")
        else:
            report.append("❌ Мод має проблеми сумісності")
            
        if result["supported_versions"]:
            report.append(f"📋 Підтримувані версії: {', '.join(result['supported_versions'])}")
            
        if result["errors"]:
            report.append("\n🚨 КРИТИЧНІ ПОМИЛКИ:")
            for error in result["errors"]:
                report.append(f"  • {error}")
                
        if result["warnings"]:
            report.append("\n⚠️ ПОПЕРЕДЖЕННЯ:")
            for warning in result["warnings"]:
                report.append(f"  • {warning}")
                
        if result["deprecated_features"]:
            report.append("\n📅 ЗАСТАРІЛІ ФУНКЦІЇ:")
            for deprecated in result["deprecated_features"]:
                report.append(f"  • {deprecated}")
                
        if result["suggestions"]:
            report.append("\n💡 РЕКОМЕНДАЦІЇ:")
            for suggestion in result["suggestions"]:
                report.append(f"  • {suggestion}")
                
        return "\n".join(report)
