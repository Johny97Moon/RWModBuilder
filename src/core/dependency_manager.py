#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Система управління залежностями для RimWorld Mod Builder v2.0.1
Автоматичне встановлення та перевірка сумісності залежностей
"""

import subprocess
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from packaging import version
import importlib.util

# Локальні імпорти
try:
    from utils.simple_logger import get_logger_instance
except ImportError:
    # Fallback logger
    class FallbackLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def debug(self, msg): print(f"DEBUG: {msg}")
    
    def get_logger_instance():
        class Logger:
            def get_logger(self): return FallbackLogger()
        return Logger()


@dataclass
class DependencyInfo:
    """Інформація про залежність"""
    name: str
    version_required: str
    version_installed: Optional[str]
    description: str
    install_command: str
    import_name: str
    is_optional: bool = False
    alternatives: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


class DependencyManager:
    """Менеджер залежностей для RimWorld Mod Builder"""
    
    def __init__(self):
        self.logger = get_logger_instance().get_logger()
        self.dependencies = self._define_dependencies()
        self.installation_callbacks: List[Callable] = []
        self.progress_callback: Optional[Callable] = None
        
    def _define_dependencies(self) -> Dict[str, DependencyInfo]:
        """Визначення всіх залежностей проєкту"""
        return {
            # Основні залежності
            "customtkinter": DependencyInfo(
                name="CustomTkinter",
                version_required=">=5.2.0",
                version_installed=None,
                description="Сучасний GUI фреймворк",
                install_command="pip install customtkinter>=5.2.0",
                import_name="customtkinter",
                is_optional=False
            ),
            
            "pillow": DependencyInfo(
                name="Pillow",
                version_required=">=10.0.0",
                version_installed=None,
                description="Обробка зображень",
                install_command="pip install Pillow>=10.0.0",
                import_name="PIL",
                is_optional=False
            ),
            
            "lxml": DependencyInfo(
                name="lxml",
                version_required=">=4.9.0",
                version_installed=None,
                description="XML обробка (опціонально, є альтернатива)",
                install_command="pip install lxml>=4.9.0",
                import_name="lxml",
                is_optional=True  # Змінено на опціональну
            ),
            
            # Додаткові залежності для розширеної функціональності
            "psd-tools": DependencyInfo(
                name="psd-tools",
                version_required=">=1.9.0",
                version_installed=None,
                description="Підтримка PSD файлів",
                install_command="pip install psd-tools>=1.9.0",
                import_name="psd_tools",
                is_optional=True
            ),
            
            "cairosvg": DependencyInfo(
                name="cairosvg",
                version_required=">=2.5.0",
                version_installed=None,
                description="Підтримка SVG файлів",
                install_command="pip install cairosvg>=2.5.0",
                import_name="cairosvg",
                is_optional=True
            ),
            
            "imageio": DependencyInfo(
                name="imageio",
                version_required=">=2.25.0",
                version_installed=None,
                description="Розширені формати зображень (HDR, EXR)",
                install_command="pip install imageio>=2.25.0",
                import_name="imageio",
                is_optional=True
            ),
            
            "pillow-heif": DependencyInfo(
                name="pillow-heif",
                version_required=">=0.10.0",
                version_installed=None,
                description="Підтримка HEIF/HEIC форматів",
                install_command="pip install pillow-heif>=0.10.0",
                import_name="pillow_heif",
                is_optional=True
            ),
            
            "psutil": DependencyInfo(
                name="psutil",
                version_required=">=5.9.0",
                version_installed=None,
                description="Моніторинг системних ресурсів",
                install_command="pip install psutil>=5.9.0",
                import_name="psutil",
                is_optional=True
            ),
            
            "packaging": DependencyInfo(
                name="packaging",
                version_required=">=21.0",
                version_installed=None,
                description="Робота з версіями пакетів",
                install_command="pip install packaging>=21.0",
                import_name="packaging",
                is_optional=False
            )
        }
    
    def check_all_dependencies(self) -> Dict[str, Dict]:
        """Перевірка всіх залежностей"""
        self.logger.info("🔍 Перевірка залежностей...")
        
        results = {
            "installed": [],
            "missing": [],
            "outdated": [],
            "optional_missing": [],
            "errors": []
        }
        
        for dep_key, dep_info in self.dependencies.items():
            try:
                status = self._check_single_dependency(dep_info)
                
                if status["installed"]:
                    if status["version_ok"]:
                        results["installed"].append({
                            "name": dep_info.name,
                            "version": status["version"],
                            "required": dep_info.version_required
                        })
                    else:
                        results["outdated"].append({
                            "name": dep_info.name,
                            "version": status["version"],
                            "required": dep_info.version_required,
                            "install_command": dep_info.install_command
                        })
                else:
                    if dep_info.is_optional:
                        results["optional_missing"].append({
                            "name": dep_info.name,
                            "description": dep_info.description,
                            "install_command": dep_info.install_command
                        })
                    else:
                        results["missing"].append({
                            "name": dep_info.name,
                            "description": dep_info.description,
                            "install_command": dep_info.install_command
                        })
                        
            except Exception as e:
                results["errors"].append({
                    "name": dep_info.name,
                    "error": str(e)
                })
                self.logger.error(f"Помилка перевірки {dep_info.name}: {e}")
        
        self._log_dependency_summary(results)
        return results
    
    def _check_single_dependency(self, dep_info: DependencyInfo) -> Dict:
        """Перевірка однієї залежності"""
        try:
            # Спроба імпорту
            spec = importlib.util.find_spec(dep_info.import_name)
            if spec is None:
                return {"installed": False, "version": None, "version_ok": False}
            
            # Отримання версії
            module = importlib.import_module(dep_info.import_name)
            installed_version = getattr(module, '__version__', None)
            
            if installed_version is None:
                # Спроба альтернативних способів отримання версії
                try:
                    import pkg_resources
                    installed_version = pkg_resources.get_distribution(dep_info.name.lower()).version
                except:
                    installed_version = "unknown"
            
            # Перевірка версії
            version_ok = self._check_version_compatibility(
                installed_version, dep_info.version_required
            )
            
            return {
                "installed": True,
                "version": installed_version,
                "version_ok": version_ok
            }
            
        except ImportError:
            return {"installed": False, "version": None, "version_ok": False}
        except Exception as e:
            self.logger.warning(f"Помилка перевірки {dep_info.name}: {e}")
            return {"installed": False, "version": None, "version_ok": False}
    
    def _check_version_compatibility(self, installed: str, required: str) -> bool:
        """Перевірка сумісності версій"""
        if installed == "unknown":
            return True  # Припускаємо сумісність якщо версія невідома
        
        try:
            # Парсинг вимог версії (>=, ==, >, <, тощо)
            if required.startswith(">="):
                return version.parse(installed) >= version.parse(required[2:])
            elif required.startswith("=="):
                return version.parse(installed) == version.parse(required[2:])
            elif required.startswith(">"):
                return version.parse(installed) > version.parse(required[1:])
            elif required.startswith("<="):
                return version.parse(installed) <= version.parse(required[2:])
            elif required.startswith("<"):
                return version.parse(installed) < version.parse(required[1:])
            else:
                # Якщо немає оператора, припускаємо >=
                return version.parse(installed) >= version.parse(required)
        except Exception as e:
            self.logger.warning(f"Помилка порівняння версій {installed} vs {required}: {e}")
            return True  # Припускаємо сумісність при помилці
    
    def _log_dependency_summary(self, results: Dict):
        """Логування підсумку перевірки залежностей"""
        total = len(self.dependencies)
        installed = len(results["installed"])
        missing = len(results["missing"])
        outdated = len(results["outdated"])
        optional_missing = len(results["optional_missing"])
        
        self.logger.info(f"📊 Підсумок залежностей:")
        self.logger.info(f"  ✅ Встановлено: {installed}/{total}")
        self.logger.info(f"  ❌ Відсутні: {missing}")
        self.logger.info(f"  ⚠️ Застарілі: {outdated}")
        self.logger.info(f"  🔧 Опціональні відсутні: {optional_missing}")
        
        if results["errors"]:
            self.logger.warning(f"  💥 Помилки: {len(results['errors'])}")
    
    def install_missing_dependencies(self, include_optional: bool = False, 
                                   progress_callback: Optional[Callable] = None) -> Dict:
        """Встановлення відсутніх залежностей"""
        self.progress_callback = progress_callback
        
        # Перевірка поточного стану
        status = self.check_all_dependencies()
        
        to_install = []
        to_install.extend(status["missing"])
        to_install.extend(status["outdated"])
        
        if include_optional:
            to_install.extend(status["optional_missing"])
        
        if not to_install:
            self.logger.info("✅ Всі необхідні залежності вже встановлені!")
            return {"success": True, "installed": [], "failed": []}
        
        self.logger.info(f"📦 Встановлення {len(to_install)} залежностей...")
        
        results = {
            "success": True,
            "installed": [],
            "failed": []
        }
        
        for i, dep in enumerate(to_install):
            if self.progress_callback:
                progress = (i / len(to_install)) * 100
                self.progress_callback(progress, f"Встановлення {dep['name']}...")
            
            success = self._install_single_dependency(dep["install_command"])
            
            if success:
                results["installed"].append(dep["name"])
                self.logger.info(f"✅ {dep['name']} встановлено успішно")
            else:
                results["failed"].append(dep["name"])
                results["success"] = False
                self.logger.error(f"❌ Не вдалося встановити {dep['name']}")
        
        if self.progress_callback:
            self.progress_callback(100, "Завершено!")
        
        return results
    
    def _install_single_dependency(self, install_command: str) -> bool:
        """Встановлення однієї залежності"""
        try:
            self.logger.debug(f"Виконання команди: {install_command}")
            
            # Розділення команди на частини
            cmd_parts = install_command.split()
            
            # Виконання команди
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=300  # 5 хвилин таймаут
            )
            
            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"Помилка встановлення: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Таймаут встановлення (5 хвилин)")
            return False
        except Exception as e:
            self.logger.error(f"Помилка виконання команди: {e}")
            return False
    
    def get_installation_suggestions(self) -> List[Dict]:
        """Отримання рекомендацій по встановленню"""
        status = self.check_all_dependencies()
        suggestions = []
        
        # Критичні залежності
        if status["missing"]:
            suggestions.append({
                "type": "critical",
                "title": "Критичні залежності відсутні",
                "description": f"Відсутні {len(status['missing'])} обов'язкових залежностей",
                "action": "install_critical",
                "dependencies": status["missing"]
            })
        
        # Застарілі версії
        if status["outdated"]:
            suggestions.append({
                "type": "warning",
                "title": "Застарілі версії",
                "description": f"{len(status['outdated'])} залежностей потребують оновлення",
                "action": "update_outdated",
                "dependencies": status["outdated"]
            })
        
        # Опціональні покращення
        if status["optional_missing"]:
            suggestions.append({
                "type": "info",
                "title": "Додаткові можливості",
                "description": f"Встановіть {len(status['optional_missing'])} опціональних залежностей для розширеної функціональності",
                "action": "install_optional",
                "dependencies": status["optional_missing"]
            })
        
        return suggestions
    
    def add_installation_callback(self, callback: Callable):
        """Додавання callback для відстеження встановлення"""
        self.installation_callbacks.append(callback)
    
    def install_async(self, include_optional: bool = False):
        """Асинхронне встановлення залежностей"""
        def install_worker():
            try:
                results = self.install_missing_dependencies(include_optional, self.progress_callback)
                for callback in self.installation_callbacks:
                    callback(results)
            except Exception as e:
                self.logger.error(f"Помилка асинхронного встановлення: {e}")
                for callback in self.installation_callbacks:
                    callback({"success": False, "error": str(e)})
        
        thread = threading.Thread(target=install_worker, daemon=True)
        thread.start()
        return thread


# Глобальний екземпляр менеджера залежностей
_dependency_manager = None

def get_dependency_manager() -> DependencyManager:
    """Отримання глобального екземпляра менеджера залежностей"""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager


if __name__ == "__main__":
    # Тестування менеджера залежностей
    manager = DependencyManager()
    
    print("🔍 Перевірка залежностей...")
    status = manager.check_all_dependencies()
    
    print("\n📊 Результати:")
    for category, items in status.items():
        if items:
            print(f"{category}: {len(items)} елементів")
    
    print("\n💡 Рекомендації:")
    suggestions = manager.get_installation_suggestions()
    for suggestion in suggestions:
        print(f"- {suggestion['title']}: {suggestion['description']}")
