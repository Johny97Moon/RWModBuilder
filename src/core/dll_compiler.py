#!/usr/bin/env python3
"""
Покращений DLL компілятор для RimWorld Mod Builder
Підтримує компіляцію C# проєктів в DLL файли для RimWorld модів
"""

import subprocess
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass

# Локальні імпорти
try:
    import sys
    sys.path.append('.')
    sys.path.append('..')
    from core.dotnet_integration import get_dotnet_environment
    from utils.simple_logger import get_logger_instance
    from utils.system_info_alternative import SystemInfoAlternative
except ImportError as e:
    print(f"Помилка імпорту: {e}")
    # Fallback для тестування
    class MockDotNetEnvironment:
        def is_available(self): return False
        def get_environment_info(self): return {"is_ready": False}
        def dotnet_path(self): return None
        def msbuild_path(self): return None

    class MockLogger:
        def info(self, msg): print(f"INFO: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def get_logger(self): return self

    class MockSystemInfo:
        def format_bytes(self, size): return f"{size} bytes"

    # Використання fallback класів
    DotNetEnvironment = MockDotNetEnvironment
    get_dotnet_environment = lambda: MockDotNetEnvironment()
    get_logger_instance = lambda: MockLogger()
    SystemInfoAlternative = MockSystemInfo


@dataclass
class CompilationSettings:
    """Налаштування компіляції DLL"""
    configuration: str = "Release"  # Release, Debug
    platform: str = "AnyCPU"  # AnyCPU, x86, x64
    target_framework: str = "net472"  # net472, net48
    output_path: Optional[str] = None
    clean_before_build: bool = True
    copy_to_assemblies: bool = True
    include_debug_symbols: bool = False
    optimize_code: bool = True
    treat_warnings_as_errors: bool = False
    verbosity: str = "minimal"  # quiet, minimal, normal, detailed, diagnostic


@dataclass
class CompilationResult:
    """Результат компіляції"""
    success: bool
    dll_path: Optional[str] = None
    output_messages: Optional[List[str]] = None
    error_messages: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    compilation_time: float = 0.0
    dll_size: int = 0

    def __post_init__(self):
        if self.output_messages is None:
            self.output_messages = []
        if self.error_messages is None:
            self.error_messages = []
        if self.warnings is None:
            self.warnings = []


class DLLCompiler:
    """Покращений компілятор DLL для RimWorld модів"""
    
    def __init__(self, dotnet_env=None):
        self.dotnet_env = dotnet_env or get_dotnet_environment()
        self.logger = get_logger_instance().get_logger()
        self.system_info = SystemInfoAlternative()
        self.compilation_callbacks: List[Callable] = []
        
    def add_compilation_callback(self, callback: Callable):
        """Додавання callback для відстеження прогресу компіляції"""
        self.compilation_callbacks.append(callback)
    
    def _notify_callbacks(self, message: str, progress: float = 0.0):
        """Сповіщення callbacks про прогрес"""
        for callback in self.compilation_callbacks:
            try:
                callback(message, progress)
            except Exception as e:
                self.logger.error(f"Помилка callback: {e}")
    
    def compile_dll(self, project_path: str, settings: Optional[CompilationSettings] = None) -> CompilationResult:
        """Компіляція C# проєкту в DLL"""
        if settings is None:
            settings = CompilationSettings()

        start_time = time.time()
        result = CompilationResult(success=False)
        # Ініціалізація списків
        result.output_messages = []
        result.error_messages = []
        result.warnings = []
        
        try:
            # Перевірка .NET середовища
            if not self.dotnet_env.is_available():
                result.error_messages.append("❌ .NET середовище недоступне")
                return result
            
            # Перевірка проєкту
            project_path_obj = Path(project_path)
            if not project_path_obj.exists():
                result.error_messages.append(f"❌ Проєкт не знайдено: {project_path}")
                return result

            # Визначення типу проєкту
            if project_path_obj.is_file() and project_path_obj.suffix == '.csproj':
                csproj_file = project_path_obj
                project_dir = project_path_obj.parent
            elif project_path_obj.is_dir():
                csproj_files = list(project_path_obj.glob("*.csproj"))
                if not csproj_files:
                    result.error_messages.append(f"❌ .csproj файл не знайдено в {project_path}")
                    return result
                csproj_file = csproj_files[0]
                project_dir = project_path_obj
            else:
                result.error_messages.append(f"❌ Невірний шлях проєкту: {project_path}")
                return result
            
            self._notify_callbacks("🔍 Аналіз проєкту...", 10)
            
            # Аналіз проєкту
            project_info = self._analyze_project(csproj_file)
            result.output_messages.append(f"📁 Проєкт: {project_info['name']}")
            result.output_messages.append(f"🎯 Target Framework: {project_info['target_framework']}")
            
            # Очищення якщо потрібно
            if settings.clean_before_build:
                self._notify_callbacks("🗑️ Очищення проєкту...", 20)
                self._clean_project(project_dir)
            
            # Підготовка команди компіляції
            self._notify_callbacks("⚙️ Підготовка компіляції...", 30)
            cmd = self._build_compilation_command(csproj_file, settings)
            
            # Компіляція
            self._notify_callbacks("🔨 Компіляція DLL...", 40)
            compilation_success, output, errors = self._execute_compilation(cmd, project_dir)
            
            # Обробка результатів
            result.output_messages.extend(output)
            result.error_messages.extend(errors)
            
            if compilation_success:
                self._notify_callbacks("✅ Пошук DLL файлу...", 80)
                
                # Пошук створеного DLL
                dll_path = self._find_compiled_dll(project_dir, project_info['name'], settings)
                
                if dll_path and dll_path.exists():
                    result.success = True
                    result.dll_path = str(dll_path)
                    result.dll_size = dll_path.stat().st_size
                    
                    # Копіювання в папку Assemblies якщо потрібно
                    if settings.copy_to_assemblies:
                        self._notify_callbacks("📦 Копіювання в Assemblies...", 90)
                        assemblies_path = self._copy_to_assemblies(dll_path, project_dir)
                        if assemblies_path:
                            result.output_messages.append(f"📦 DLL скопійовано в: {assemblies_path}")
                    
                    result.output_messages.append(f"✅ DLL створено: {dll_path}")
                    result.output_messages.append(f"📊 Розмір: {self._format_file_size(result.dll_size)}")
                    
                    self._notify_callbacks("🎉 Компіляція завершена успішно!", 100)
                else:
                    result.error_messages.append("❌ DLL файл не знайдено після компіляції")
            else:
                result.error_messages.append("❌ Компіляція завершилася з помилками")
            
        except Exception as e:
            result.error_messages.append(f"❌ Виняток під час компіляції: {e}")
            self.logger.error(f"Помилка компіляції: {e}")
        
        finally:
            result.compilation_time = time.time() - start_time
            
        return result
    
    def _analyze_project(self, csproj_file: Path) -> Dict:
        """Аналіз .csproj файлу"""
        project_info = {
            "name": csproj_file.stem,
            "target_framework": "net472",
            "output_type": "Library",
            "assembly_name": csproj_file.stem
        }
        
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(csproj_file)
            root = tree.getroot()
            
            # Пошук PropertyGroup
            for prop_group in root.findall(".//PropertyGroup"):
                for child in prop_group:
                    if child.tag == "TargetFramework" and child.text:
                        project_info["target_framework"] = child.text
                    elif child.tag == "OutputType" and child.text:
                        project_info["output_type"] = child.text
                    elif child.tag == "AssemblyName" and child.text:
                        project_info["assembly_name"] = child.text
                        
        except Exception as e:
            self.logger.warning(f"Не вдалося проаналізувати .csproj: {e}")
        
        return project_info
    
    def _clean_project(self, project_dir: Path):
        """Очищення проєкту"""
        clean_dirs = ["bin", "obj"]
        
        for clean_dir in clean_dirs:
            dir_path = project_dir / clean_dir
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    self.logger.info(f"🗑️ Очищено: {dir_path}")
                except Exception as e:
                    self.logger.warning(f"Не вдалося очистити {dir_path}: {e}")
    
    def _build_compilation_command(self, csproj_file: Path, settings: CompilationSettings) -> List[str]:
        """Побудова команди компіляції"""
        cmd: List[str] = []

        # Використання dotnet CLI або MSBuild
        if hasattr(self.dotnet_env, 'dotnet_path') and self.dotnet_env.dotnet_path:
            cmd = [str(self.dotnet_env.dotnet_path), "build"]
        elif hasattr(self.dotnet_env, 'msbuild_path') and self.dotnet_env.msbuild_path:
            cmd = [str(self.dotnet_env.msbuild_path)]
        else:
            raise Exception("Ні dotnet CLI, ні MSBuild недоступні")

        # Додавання параметрів
        cmd.append(str(csproj_file))
        cmd.extend([
            "--configuration", settings.configuration,
            "--verbosity", settings.verbosity
        ])

        # Додаткові параметри для dotnet CLI
        if len(cmd) > 0 and "dotnet" in str(cmd[0]):
            if settings.output_path:
                cmd.extend(["--output", settings.output_path])
        else:
            # Параметри для MSBuild
            cmd.extend([
                f"/p:Configuration={settings.configuration}",
                f"/p:Platform={settings.platform}",
                f"/verbosity:{settings.verbosity}"
            ])

            if settings.output_path:
                cmd.append(f"/p:OutputPath={settings.output_path}")

        return cmd
    
    def _execute_compilation(self, cmd: List[str], working_dir: Path) -> Tuple[bool, List[str], List[str]]:
        """Виконання команди компіляції"""
        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 хвилин timeout
            )
            
            output_lines = result.stdout.split('\n') if result.stdout else []
            error_lines = result.stderr.split('\n') if result.stderr else []
            
            # Фільтрація порожніх рядків
            output_lines = [line.strip() for line in output_lines if line.strip()]
            error_lines = [line.strip() for line in error_lines if line.strip()]
            
            success = result.returncode == 0
            
            return success, output_lines, error_lines
            
        except subprocess.TimeoutExpired:
            return False, [], ["❌ Timeout компіляції (5 хвилин)"]
        except Exception as e:
            return False, [], [f"❌ Помилка виконання: {e}"]
    
    def _find_compiled_dll(self, project_dir: Path, project_name: str, settings: CompilationSettings) -> Optional[Path]:
        """Пошук скомпільованого DLL файлу"""
        possible_paths = [
            project_dir / "bin" / settings.configuration / settings.target_framework / f"{project_name}.dll",
            project_dir / "bin" / settings.configuration / f"{project_name}.dll",
            project_dir / "bin" / f"{project_name}.dll",
        ]
        
        if settings.output_path:
            possible_paths.insert(0, Path(settings.output_path) / f"{project_name}.dll")
        
        for dll_path in possible_paths:
            if dll_path.exists():
                return dll_path
        
        # Пошук будь-якого .dll файлу в bin папці
        bin_dir = project_dir / "bin"
        if bin_dir.exists():
            for dll_file in bin_dir.rglob("*.dll"):
                if project_name.lower() in dll_file.name.lower():
                    return dll_file
        
        return None
    
    def _copy_to_assemblies(self, dll_path: Path, project_dir: Path) -> Optional[Path]:
        """Копіювання DLL в папку Assemblies мода"""
        # Пошук папки Assemblies
        assemblies_dir = None

        # Спочатку шукаємо в батьківських папках
        current_dir = project_dir
        for _ in range(5):  # Максимум 5 рівнів вгору
            assemblies_candidate = current_dir / "Assemblies"
            if assemblies_candidate.exists():
                assemblies_dir = assemblies_candidate
                break
            current_dir = current_dir.parent
            if current_dir == current_dir.parent:  # Досягли кореня
                break

        # Якщо не знайшли, створюємо поруч з Source
        if not assemblies_dir:
            if project_dir.name == "Source" or "Source" in str(project_dir):
                mod_root = project_dir.parent if project_dir.name == "Source" else project_dir.parent.parent
                assemblies_dir = mod_root / "Assemblies"
                assemblies_dir.mkdir(exist_ok=True)

        if assemblies_dir:
            target_path = assemblies_dir / dll_path.name
            try:
                shutil.copy2(dll_path, target_path)
                return target_path
            except Exception as e:
                self.logger.error(f"Помилка копіювання DLL: {e}")

        return None

    def get_project_dependencies(self, csproj_file: Path) -> List[str]:
        """Отримання залежностей проєкту"""
        dependencies = []

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(csproj_file)
            root = tree.getroot()

            # PackageReference
            for package_ref in root.findall(".//PackageReference"):
                include = package_ref.get("Include")
                version = package_ref.get("Version")
                if include:
                    dep_info = f"{include}"
                    if version:
                        dep_info += f" ({version})"
                    dependencies.append(dep_info)

            # Reference
            for ref in root.findall(".//Reference"):
                include = ref.get("Include")
                if include:
                    dependencies.append(include)

        except Exception as e:
            self.logger.warning(f"Не вдалося отримати залежності: {e}")

        return dependencies
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Форматування розміру файлу"""
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def compile_multiple_projects(self, project_paths: List[str], settings: Optional[CompilationSettings] = None) -> List[CompilationResult]:
        """Компіляція кількох проєктів"""
        if settings is None:
            settings = CompilationSettings()

        results = []

        for i, project_path in enumerate(project_paths):
            self._notify_callbacks(f"🔨 Компіляція проєкту {i+1}/{len(project_paths)}: {Path(project_path).name}",
                                 (i / len(project_paths)) * 100)

            result = self.compile_dll(project_path, settings)
            results.append(result)
            
            if not result.success:
                self.logger.error(f"Помилка компіляції {project_path}: {result.error_messages}")
        
        return results
    
    def get_compilation_summary(self, results: List[CompilationResult]) -> Dict:
        """Отримання зведення компіляції"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        total_size = sum(r.dll_size for r in successful)
        total_time = sum(r.compilation_time for r in results)
        
        return {
            "total_projects": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "total_dll_size": total_size,
            "total_compilation_time": total_time,
            "success_rate": (len(successful) / len(results)) * 100 if results else 0
        }


# Функції для зворотної сумісності
def compile_csharp_project(project_path: str, configuration: str = "Release") -> Tuple[bool, str]:
    """Проста функція компіляції для зворотної сумісності"""
    compiler = DLLCompiler()
    settings = CompilationSettings(configuration=configuration)
    result = compiler.compile_dll(project_path, settings)
    
    if result.success:
        return True, f"✅ DLL створено: {result.dll_path}"
    else:
        error_msg = "\n".join(result.error_messages) if result.error_messages else "Невідома помилка"
        return False, f"❌ Помилка компіляції: {error_msg}"


# Тестування модуля
if __name__ == "__main__":
    print("🔨 Тест DLL Compiler")
    
    # Створення компілятора
    compiler = DLLCompiler()
    
    # Додавання callback для відстеження прогресу
    def progress_callback(message: str, progress: float):
        print(f"[{progress:5.1f}%] {message}")
    
    compiler.add_compilation_callback(progress_callback)
    
    # Перевірка .NET середовища
    env_info = compiler.dotnet_env.get_environment_info()
    print(f"\n🔧 .NET середовище:")
    print(f"  Готовий: {env_info['is_ready']}")
    print(f"  dotnet CLI: {env_info['dotnet_path']}")
    print(f"  MSBuild: {env_info['msbuild_path']}")
    
    if env_info['is_ready']:
        print("\n✅ DLL Compiler готовий до використання!")
        
        # Приклад налаштувань
        settings = CompilationSettings(
            configuration="Release",
            platform="AnyCPU",
            clean_before_build=True,
            copy_to_assemblies=True
        )
        print(f"\n⚙️ Налаштування компіляції: {settings}")
    else:
        print("\n⚠️ .NET середовище недоступне. Встановіть .NET SDK для компіляції DLL.")
    
    print("\n🎯 Функції DLL Compiler:")
    print("  • Компіляція C# проєктів в DLL")
    print("  • Автоматичне копіювання в папку Assemblies")
    print("  • Підтримка різних конфігурацій (Debug/Release)")
    print("  • Детальне логування та звітність")
    print("  • Пакетна компіляція кількох проєктів")
    print("  • Callbacks для відстеження прогресу")
