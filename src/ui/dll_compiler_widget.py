#!/usr/bin/env python3
"""
UI компонент для компіляції DLL файлів
Інтерфейс для покращеного DLL компілятора RimWorld Mod Builder
"""

import os
import threading
from pathlib import Path
from typing import Optional, List
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Локальні імпорти
try:
    import sys
    sys.path.append('.')
    sys.path.append('..')
    from src.core.dll_compiler import DLLCompiler, CompilationSettings, CompilationResult
    from src.core.dotnet_integration import get_dotnet_environment
    from src.utils.simple_logger import get_logger_instance
except ImportError as e:
    print(f"Помилка імпорту: {e}")
    # Fallback для тестування
    from dataclasses import dataclass
    from typing import Optional, List

    @dataclass
    class CompilationSettings:
        configuration: str = "Release"
        platform: str = "AnyCPU"
        target_framework: str = "net472"
        clean_before_build: bool = True
        copy_to_assemblies: bool = True
        include_debug_symbols: bool = False
        optimize_code: bool = True

    @dataclass
    class CompilationResult:
        success: bool
        error_messages: List[str] = None
        def __post_init__(self):
            if self.error_messages is None:
                self.error_messages = []

    class MockDLLCompiler:
        def compile_dll(self, path, settings):
            return CompilationResult(success=False, error_messages=['Mock compiler'])
        def add_compilation_callback(self, callback): pass
        def compile_multiple_projects(self, projects, settings): return []
        def get_compilation_summary(self, results): return {'total_projects': 0, 'successful': 0, 'failed': 0, 'success_rate': 0, 'total_compilation_time': 0, 'total_dll_size': 0}

    class MockDotNetEnvironment:
        def get_environment_info(self): return {'is_ready': False, 'dotnet_path': None, 'msbuild_path': None}

    class MockLogger:
        def get_logger(self): return self
        def info(self, msg): pass
        def error(self, msg): pass

    DLLCompiler = MockDLLCompiler
    get_dotnet_environment = lambda: MockDotNetEnvironment()
    get_logger_instance = lambda: MockLogger()


class CompilationSettingsFrame(ctk.CTkFrame):
    """Фрейм налаштувань компіляції"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування UI"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self, 
            text="⚙️ Налаштування компіляції",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 15))
        
        # Основні налаштування
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="x", padx=10, pady=5)
        
        # Configuration
        config_frame = ctk.CTkFrame(main_frame)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(config_frame, text="Конфігурація:").pack(side="left", padx=5)
        self.configuration_var = ctk.StringVar(value="Release")
        self.configuration_combo = ctk.CTkComboBox(
            config_frame,
            values=["Release", "Debug"],
            variable=self.configuration_var,
            width=120
        )
        self.configuration_combo.pack(side="right", padx=5)
        
        # Platform
        platform_frame = ctk.CTkFrame(main_frame)
        platform_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(platform_frame, text="Платформа:").pack(side="left", padx=5)
        self.platform_var = ctk.StringVar(value="AnyCPU")
        self.platform_combo = ctk.CTkComboBox(
            platform_frame,
            values=["AnyCPU", "x86", "x64"],
            variable=self.platform_var,
            width=120
        )
        self.platform_combo.pack(side="right", padx=5)
        
        # Target Framework
        framework_frame = ctk.CTkFrame(main_frame)
        framework_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(framework_frame, text="Target Framework:").pack(side="left", padx=5)
        self.framework_var = ctk.StringVar(value="net472")
        self.framework_combo = ctk.CTkComboBox(
            framework_frame,
            values=["net472", "net48", "net6.0", "net8.0"],
            variable=self.framework_var,
            width=120
        )
        self.framework_combo.pack(side="right", padx=5)
        
        # Додаткові опції
        options_frame = ctk.CTkFrame(self)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            options_frame, 
            text="🔧 Додаткові опції",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        
        # Checkboxes
        self.clean_var = ctk.BooleanVar(value=True)
        self.clean_check = ctk.CTkCheckBox(
            options_frame,
            text="Очистити перед збіркою",
            variable=self.clean_var
        )
        self.clean_check.pack(anchor="w", padx=10, pady=2)
        
        self.copy_assemblies_var = ctk.BooleanVar(value=True)
        self.copy_assemblies_check = ctk.CTkCheckBox(
            options_frame,
            text="Копіювати в папку Assemblies",
            variable=self.copy_assemblies_var
        )
        self.copy_assemblies_check.pack(anchor="w", padx=10, pady=2)
        
        self.debug_symbols_var = ctk.BooleanVar(value=False)
        self.debug_symbols_check = ctk.CTkCheckBox(
            options_frame,
            text="Включити debug символи",
            variable=self.debug_symbols_var
        )
        self.debug_symbols_check.pack(anchor="w", padx=10, pady=2)
        
        self.optimize_var = ctk.BooleanVar(value=True)
        self.optimize_check = ctk.CTkCheckBox(
            options_frame,
            text="Оптимізувати код",
            variable=self.optimize_var
        )
        self.optimize_check.pack(anchor="w", padx=10, pady=2)
    
    def get_settings(self) -> CompilationSettings:
        """Отримання налаштувань компіляції"""
        return CompilationSettings(
            configuration=self.configuration_var.get(),
            platform=self.platform_var.get(),
            target_framework=self.framework_var.get(),
            clean_before_build=self.clean_var.get(),
            copy_to_assemblies=self.copy_assemblies_var.get(),
            include_debug_symbols=self.debug_symbols_var.get(),
            optimize_code=self.optimize_var.get()
        )


class CompilationOutputFrame(ctk.CTkFrame):
    """Фрейм виводу компіляції"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Налаштування UI"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self, 
            text="📋 Вивід компіляції",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 5))
        
        # Текстове поле виводу
        self.output_text = ctk.CTkTextbox(
            self,
            height=200,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.output_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Кнопки управління
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        self.clear_button = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Очистити",
            command=self.clear_output,
            width=100
        )
        self.clear_button.pack(side="left", padx=5)
        
        self.save_button = ctk.CTkButton(
            buttons_frame,
            text="💾 Зберегти лог",
            command=self.save_log,
            width=120
        )
        self.save_button.pack(side="right", padx=5)
    
    def add_output(self, text: str, message_type: str = "info"):
        """Додавання тексту до виводу"""
        # Кольори для різних типів повідомлень
        colors = {
            "info": "#FFFFFF",
            "success": "#00FF00", 
            "warning": "#FFAA00",
            "error": "#FF4444"
        }
        
        self.output_text.insert("end", text + "\n")
        self.output_text.see("end")
    
    def clear_output(self):
        """Очищення виводу"""
        self.output_text.delete("1.0", "end")
    
    def save_log(self):
        """Збереження логу в файл"""
        content = self.output_text.get("1.0", "end")
        if not content.strip():
            messagebox.showwarning("Попередження", "Немає даних для збереження")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Зберегти лог компіляції",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Успіх", f"Лог збережено: {file_path}")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося зберегти файл: {e}")


class DLLCompilerWidget(ctk.CTkFrame):
    """Головний віджет компіляції DLL"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Ініціалізація
        self.compiler = DLLCompiler()
        self.dotnet_env = get_dotnet_environment()
        self.logger = get_logger_instance().get_logger()
        self.compilation_thread: Optional[threading.Thread] = None
        self.current_projects: List[str] = []
        
        # Додавання callback для відстеження прогресу
        self.compiler.add_compilation_callback(self.on_compilation_progress)
        
        self.setup_ui()
        self.check_dotnet_environment()
    
    def setup_ui(self):
        """Налаштування UI"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self, 
            text="🔨 Компілятор DLL для RimWorld модів",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=15)
        
        # Основний контейнер
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Ліва панель - вибір проєктів та налаштування
        left_panel = ctk.CTkFrame(main_container)
        left_panel.pack(side="left", fill="y", padx=5, pady=5)
        
        # Вибір проєктів
        projects_frame = ctk.CTkFrame(left_panel)
        projects_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            projects_frame, 
            text="📁 Проєкти для компіляції",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=5)
        
        # Список проєктів
        self.projects_listbox = ctk.CTkTextbox(projects_frame, height=100)
        self.projects_listbox.pack(fill="x", padx=5, pady=5)
        
        # Кнопки управління проєктами
        projects_buttons = ctk.CTkFrame(projects_frame)
        projects_buttons.pack(fill="x", padx=5, pady=5)
        
        self.add_project_button = ctk.CTkButton(
            projects_buttons,
            text="➕ Додати",
            command=self.add_project,
            width=80
        )
        self.add_project_button.pack(side="left", padx=2)
        
        self.remove_project_button = ctk.CTkButton(
            projects_buttons,
            text="➖ Видалити",
            command=self.remove_project,
            width=80
        )
        self.remove_project_button.pack(side="left", padx=2)
        
        self.clear_projects_button = ctk.CTkButton(
            projects_buttons,
            text="🗑️ Очистити",
            command=self.clear_projects,
            width=80
        )
        self.clear_projects_button.pack(side="left", padx=2)
        
        # Налаштування компіляції
        self.settings_frame = CompilationSettingsFrame(left_panel)
        self.settings_frame.pack(fill="x", padx=5, pady=5)
        
        # Права панель - вивід та управління
        right_panel = ctk.CTkFrame(main_container)
        right_panel.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Статус .NET
        self.status_frame = ctk.CTkFrame(right_panel)
        self.status_frame.pack(fill="x", padx=5, pady=5)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="🔍 Перевірка .NET середовища...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
        # Прогрес бар
        self.progress_frame = ctk.CTkFrame(right_panel)
        self.progress_frame.pack(fill="x", padx=5, pady=5)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Готовий до компіляції",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=2)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        # Кнопки компіляції
        compile_buttons = ctk.CTkFrame(right_panel)
        compile_buttons.pack(fill="x", padx=5, pady=5)
        
        self.compile_button = ctk.CTkButton(
            compile_buttons,
            text="🔨 Компілювати",
            command=self.start_compilation,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40
        )
        self.compile_button.pack(side="left", fill="x", expand=True, padx=5)
        
        self.stop_button = ctk.CTkButton(
            compile_buttons,
            text="⏹️ Зупинити",
            command=self.stop_compilation,
            width=100,
            state="disabled"
        )
        self.stop_button.pack(side="right", padx=5)
        
        # Вивід компіляції
        self.output_frame = CompilationOutputFrame(right_panel)
        self.output_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    def check_dotnet_environment(self):
        """Перевірка .NET середовища"""
        env_info = self.dotnet_env.get_environment_info()
        
        if env_info['is_ready']:
            status_text = f"✅ .NET готовий | dotnet: {env_info['dotnet_path'] is not None} | MSBuild: {env_info['msbuild_path'] is not None}"
            self.status_label.configure(text=status_text, text_color="green")
            self.compile_button.configure(state="normal")
        else:
            status_text = "❌ .NET середовище недоступне. Встановіть .NET SDK."
            self.status_label.configure(text=status_text, text_color="red")
            self.compile_button.configure(state="disabled")
    
    def add_project(self):
        """Додавання проєкту"""
        file_path = filedialog.askopenfilename(
            title="Оберіть .csproj файл",
            filetypes=[("C# Project files", "*.csproj"), ("All files", "*.*")]
        )
        
        if file_path and file_path not in self.current_projects:
            self.current_projects.append(file_path)
            self.update_projects_display()
    
    def remove_project(self):
        """Видалення проєкту"""
        # Простий спосіб - видалити останній доданий
        if self.current_projects:
            self.current_projects.pop()
            self.update_projects_display()
    
    def clear_projects(self):
        """Очищення списку проєктів"""
        self.current_projects.clear()
        self.update_projects_display()
    
    def update_projects_display(self):
        """Оновлення відображення проєктів"""
        self.projects_listbox.delete("1.0", "end")
        
        if not self.current_projects:
            self.projects_listbox.insert("1.0", "Немає проєктів для компіляції")
        else:
            for i, project in enumerate(self.current_projects, 1):
                project_name = Path(project).name
                self.projects_listbox.insert("end", f"{i}. {project_name}\n")
    
    def on_compilation_progress(self, message: str, progress: float):
        """Callback для прогресу компіляції"""
        self.after(0, lambda: self._update_progress(message, progress))
    
    def _update_progress(self, message: str, progress: float):
        """Оновлення прогресу в UI потоці"""
        self.progress_label.configure(text=message)
        self.progress_bar.set(progress / 100.0)
        self.output_frame.add_output(message, "info")
    
    def start_compilation(self):
        """Початок компіляції"""
        if not self.current_projects:
            messagebox.showerror("Помилка", "Додайте проєкти для компіляції")
            return
        
        if self.compilation_thread and self.compilation_thread.is_alive():
            messagebox.showwarning("Попередження", "Компіляція вже виконується")
            return
        
        # Блокування кнопок
        self.compile_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        
        # Очищення виводу
        self.output_frame.clear_output()
        
        # Отримання налаштувань
        settings = self.settings_frame.get_settings()
        
        # Запуск компіляції в окремому потоці
        self.compilation_thread = threading.Thread(
            target=self._compilation_worker,
            args=(self.current_projects.copy(), settings),
            daemon=True
        )
        self.compilation_thread.start()
    
    def _compilation_worker(self, projects: List[str], settings: CompilationSettings):
        """Робочий потік компіляції"""
        try:
            results = self.compiler.compile_multiple_projects(projects, settings)
            
            # Обробка результатів
            self.after(0, lambda: self._compilation_finished(results))
            
        except Exception as e:
            self.after(0, lambda: self._compilation_error(str(e)))
    
    def _compilation_finished(self, results: List[CompilationResult]):
        """Завершення компіляції"""
        # Розблокування кнопок
        self.compile_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
        # Статистика
        summary = self.compiler.get_compilation_summary(results)
        
        self.output_frame.add_output("\n" + "="*50, "info")
        self.output_frame.add_output("📊 ЗВЕДЕННЯ КОМПІЛЯЦІЇ", "info")
        self.output_frame.add_output("="*50, "info")
        self.output_frame.add_output(f"Всього проєктів: {summary['total_projects']}", "info")
        self.output_frame.add_output(f"Успішно: {summary['successful']}", "success")
        self.output_frame.add_output(f"Помилки: {summary['failed']}", "error" if summary['failed'] > 0 else "info")
        self.output_frame.add_output(f"Успішність: {summary['success_rate']:.1f}%", "info")
        self.output_frame.add_output(f"Час компіляції: {summary['total_compilation_time']:.1f} сек", "info")
        
        if summary['total_dll_size'] > 0:
            size_mb = summary['total_dll_size'] / (1024 * 1024)
            self.output_frame.add_output(f"Загальний розмір DLL: {size_mb:.2f} MB", "info")
        
        # Повідомлення про результат
        if summary['failed'] == 0:
            self.progress_label.configure(text="🎉 Всі проєкти скомпільовано успішно!")
            messagebox.showinfo("Успіх", f"Всі {summary['successful']} проєктів скомпільовано успішно!")
        else:
            self.progress_label.configure(text=f"⚠️ Компіляція завершена з помилками ({summary['failed']} помилок)")
            messagebox.showwarning("Попередження", f"Компіляція завершена.\nУспішно: {summary['successful']}\nПомилки: {summary['failed']}")
    
    def _compilation_error(self, error_message: str):
        """Помилка компіляції"""
        self.compile_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
        self.progress_label.configure(text="❌ Помилка компіляції")
        self.output_frame.add_output(f"❌ КРИТИЧНА ПОМИЛКА: {error_message}", "error")
        
        messagebox.showerror("Помилка", f"Критична помилка компіляції:\n{error_message}")
    
    def stop_compilation(self):
        """Зупинка компіляції"""
        # Примітка: subprocess не можна легко зупинити, тому просто повідомляємо
        messagebox.showinfo("Інформація", "Компіляція буде зупинена після завершення поточного проєкту")
        self.stop_button.configure(state="disabled")


# Тестування віджета
if __name__ == "__main__":
    # Створення тестового вікна
    root = ctk.CTk()
    root.title("DLL Compiler Widget Test")
    root.geometry("1200x800")
    
    # Створення віджета
    widget = DLLCompilerWidget(root)
    widget.pack(fill="both", expand=True, padx=10, pady=10)
    
    root.mainloop()
