# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec файл для RimWorld Mod Builder v2.0.1
Створює автономний .exe файл з усіма залежностями
Оптимізовано для розміру <100MB та повної функціональності
"""

import os
import sys
from pathlib import Path
import site

# Додаємо src до шляху
current_dir = os.path.dirname(os.path.abspath('build_exe.spec'))
sys.path.insert(0, os.path.join(current_dir, 'src'))

# Базовий шлях проєкту
project_root = Path(current_dir)

print("🔧 Початок конфігурації PyInstaller для RimWorld Mod Builder v2.0.1")
print(f"📁 Корінь проєкту: {project_root}")

# Збір всіх Python файлів з src/
src_files = []
for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            src_files.append(os.path.join(root, file))

print(f"📦 Знайдено Python файлів: {len(src_files)}")

# Збір шаблонів XML
template_files = []
templates_dir = project_root / 'src' / 'templates'
if templates_dir.exists():
    for template_file in templates_dir.glob('*.xml'):
        template_files.append((str(template_file), 'src/templates'))

print(f"📋 Знайдено шаблонів XML: {len(template_files)}")

# Збір ресурсів CustomTkinter
ctk_data = []
try:
    import customtkinter
    ctk_path = Path(customtkinter.__file__).parent
    
    # Теми CustomTkinter
    themes_dir = ctk_path / 'assets' / 'themes'
    if themes_dir.exists():
        for theme_file in themes_dir.rglob('*'):
            if theme_file.is_file():
                rel_path = theme_file.relative_to(ctk_path)
                ctk_data.append((str(theme_file), f'customtkinter/{rel_path.parent}'))
    
    # Іконки та зображення CustomTkinter
    assets_dir = ctk_path / 'assets'
    if assets_dir.exists():
        for asset_file in assets_dir.rglob('*'):
            if asset_file.is_file() and asset_file.suffix in ['.png', '.ico', '.gif']:
                rel_path = asset_file.relative_to(ctk_path)
                ctk_data.append((str(asset_file), f'customtkinter/{rel_path.parent}'))
                
except ImportError:
    print("⚠️ CustomTkinter не знайдено")

print(f"🎨 CustomTkinter ресурсів: {len(ctk_data)}")

# Збір ресурсів Pillow (оптимізовано)
pillow_data = []
try:
    import PIL
    pil_path = Path(PIL.__file__).parent

    # Тільки критично важливі плагіни Pillow
    essential_plugins = [
        'JpegImagePlugin.py',
        'PngImagePlugin.py',
        'BmpImagePlugin.py',
        'TiffImagePlugin.py',
        'WebPImagePlugin.py',
        'IcoImagePlugin.py',
        'GifImagePlugin.py'
    ]

    for plugin_name in essential_plugins:
        plugin_file = pil_path / plugin_name
        if plugin_file.exists():
            pillow_data.append((str(plugin_file), 'PIL'))

    # Додаємо бінарні файли Pillow
    for binary_file in pil_path.glob('*.pyd'):
        pillow_data.append((str(binary_file), 'PIL'))
    for binary_file in pil_path.glob('*.dll'):
        pillow_data.append((str(binary_file), 'PIL'))

except ImportError:
    print("⚠️ Pillow не знайдено")

print(f"🖼️ Pillow ресурсів: {len(pillow_data)}")

# Збір всіх додаткових файлів
datas = template_files + ctk_data + pillow_data

# Додаткові файли проєкту
additional_files = [
    ('requirements.txt', '.'),
    ('README.md', '.'),
    ('RIMWORLD_MOD_BUILDER_GUIDE.md', '.'),
    ('DOTNET_INTEGRATION_GUIDE.md', '.'),
]

for src_file, dest_dir in additional_files:
    if os.path.exists(src_file):
        datas.append((src_file, dest_dir))

# Приховані імпорти
hiddenimports = [
    # Основні модулі проєкту
    'src.core.dotnet_integration',
    'src.core.template_manager',
    'src.core.project_manager',
    'src.core.csharp_manager',
    'src.core.steam_workshop',
    'src.core.dependency_manager',
    'src.core.mod_validator',
    'src.core.image_formats',
    
    # UI модулі
    'src.ui.texture_manager_customtkinter',
    'src.ui.csharp_project_manager',
    'src.ui.csharp_compiler_widget',
    'src.ui.csharp_dialog',
    'src.ui.definition_preview',
    'src.ui.steam_workshop_dialog',
    'src.ui.export_dialog',
    'src.ui.settings_dialog',
    'src.ui.template_dialog',
    'src.ui.smart_xml_editor',
    'src.ui.enhanced_texture_manager',
    'src.ui.dependency_dialog',
    'src.ui.new_project_dialog',
    'src.ui.preview_system',
    'src.ui.file_explorer',
    'src.ui.text_editor',
    'src.ui.log_viewer',
    'src.ui.v2_integration',
    
    # Утиліти
    'src.utils.simple_logger',
    'src.utils.xml_validator',
    'src.utils.xml_validator_simple',
    'src.utils.compatibility_checker',
    'src.utils.performance',
    
    # CustomTkinter та залежності
    'customtkinter',
    'customtkinter.windows',
    'customtkinter.windows.widgets',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.colorchooser',
    
    # Обробка зображень
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.ImageFilter',
    'PIL.ImageEnhance',
    'PIL.ImageOps',
    'PIL.ImageChops',
    'PIL.ImageStat',
    'PIL.ImageSequence',
    'PIL.ImageFile',
    'PIL.ImageMode',
    'PIL.ImagePalette',
    'PIL.ImageColor',
    'PIL.ImageGrab',
    'PIL.ImageShow',
    'PIL.ImageWin',
    'PIL.ImageQt',
    'PIL.ExifTags',
    'PIL.TiffTags',
    'PIL.JpegImagePlugin',
    'PIL.PngImagePlugin',
    'PIL.BmpImagePlugin',
    'PIL.TiffImagePlugin',
    'PIL.WebPImagePlugin',
    'PIL.IcoImagePlugin',
    'PIL.GifImagePlugin',
    
    # PSD підтримка
    'psd_tools',
    'psd_tools.api',
    'psd_tools.psd',
    'psd_tools.constants',
    
    # XML обробка
    'lxml',
    'lxml.etree',
    'lxml.html',
    'xml.etree.ElementTree',
    'xml.dom.minidom',
    
    # Системні модулі
    'subprocess',
    'threading',
    'multiprocessing',
    'queue',
    'tempfile',
    'shutil',
    'zipfile',
    'tarfile',
    'json',
    'configparser',
    'urllib.request',
    'urllib.parse',
    'urllib.error',
    'http.client',
    'socket',
    'ssl',
    
    # Логування та діагностика
    'logging',
    'logging.handlers',
    'traceback',
    'inspect',
    'gc',
    'psutil',
    
    # Кольори та форматування
    'colorama',
    'colorama.init',
    'colorama.ansi',
    'colorama.win32',
    
    # Дата та час
    'datetime',
    'time',
    'calendar',
    
    # Математика
    'math',
    'random',
    'statistics',
    
    # Регулярні вирази
    're',
    'fnmatch',
    'glob',
    
    # Файлова система
    'pathlib',
    'os.path',
    'stat',
    
    # Кодування
    'base64',
    'binascii',
    'codecs',
    'locale',
    
    # Мережа (для Steam Workshop)
    'requests',
    'urllib3',
    
    # Windows специфічні
    'winreg',
    'msvcrt',
    'winsound',
    
    # .NET інтеграція
    'ctypes',
    'ctypes.wintypes',
]

# Виключені модулі для зменшення розміру
excludes = [
    # Тестування
    'pytest',
    'unittest',
    'doctest',
    'test',
    'tests',
    
    # Розробка
    'pdb',
    'pydoc',
    'profile',
    'cProfile',
    'pstats',
    'timeit',
    
    # Jupyter/IPython
    'IPython',
    'jupyter',
    'notebook',
    'ipykernel',
    
    # Matplotlib (якщо не використовується)
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    
    # PyQt/PySide (використовуємо CustomTkinter)
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    
    # Інші GUI фреймворки
    'wx',
    'kivy',
    'pygame',
    
    # Веб фреймворки
    'flask',
    'django',
    'tornado',
    'fastapi',
    
    # Бази даних
    'sqlite3',
    'mysql',
    'postgresql',
    'pymongo',
    
    # Криптографія (якщо не потрібна)
    'cryptography',
    'hashlib',
    'hmac',
    
    # Компіляція
    'distutils',
    'setuptools',
    'pip',
    'wheel',
]

# Аналіз основного файлу
a = Analysis(
    ['main.py'],
    pathex=[str(project_root), str(project_root / 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Видалення дублікатів
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Створення виконуваного файлу
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RimWorldModBuilder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Стиснення UPX для зменшення розміру
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Без консольного вікна
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Можна додати іконку пізніше
    version_file=None,  # Можна додати інформацію про версію
)

# Додаткова інформація про збірку
print("🔧 Конфігурація PyInstaller для RimWorld Mod Builder v2.0.1")
print(f"📁 Проєкт: {project_root}")
print(f"📦 Шаблонів: {len(template_files)}")
print(f"🎨 CustomTkinter ресурсів: {len(ctk_data)}")
print(f"🖼️ Pillow ресурсів: {len(pillow_data)}")
print(f"📚 Прихованих імпортів: {len(hiddenimports)}")
print(f"🚫 Виключених модулів: {len(excludes)}")
print("✅ Конфігурація готова до збірки")
