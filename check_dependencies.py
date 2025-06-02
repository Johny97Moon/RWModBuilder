#!/usr/bin/env python3
"""
Скрипт для перевірки залежностей RimWorld Mod Builder
"""

import sys
import importlib.util

def check_dependency(name, import_name=None, optional=False):
    """Перевірка однієї залежності"""
    if import_name is None:
        import_name = name.replace('-', '_')
    
    try:
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            status = "❌ НЕ ВСТАНОВЛЕНО"
            if optional:
                status += " (опціональна)"
            return False, status
        
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'невідома версія')
        status = f"✅ {version}"
        return True, status
        
    except Exception as e:
        status = f"❌ ПОМИЛКА: {e}"
        if optional:
            status += " (опціональна)"
        return False, status

def main():
    """Головна функція перевірки"""
    print("🔍 Перевірка залежностей RimWorld Mod Builder")
    print("=" * 50)
    
    # Python версія
    print(f"🐍 Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Обов'язкові залежності
    print("\n📦 ОБОВ'ЯЗКОВІ ЗАЛЕЖНОСТІ:")
    required_deps = [
        ("customtkinter", "customtkinter"),
        ("Pillow", "PIL"),
        ("packaging", "packaging"),
    ]
    
    all_required_ok = True
    for name, import_name in required_deps:
        ok, status = check_dependency(name, import_name)
        print(f"  {name}: {status}")
        if not ok:
            all_required_ok = False
    
    # Рекомендовані залежності
    print("\n🎯 РЕКОМЕНДОВАНІ ЗАЛЕЖНОСТІ:")
    recommended_deps = [
        ("lxml", "lxml"),
        ("colorama", "colorama"),
        ("pytest", "pytest"),
    ]
    
    for name, import_name in recommended_deps:
        ok, status = check_dependency(name, import_name, optional=True)
        print(f"  {name}: {status}")
    
    # Опціональні залежності
    print("\n🔧 ОПЦІОНАЛЬНІ ЗАЛЕЖНОСТІ:")
    optional_deps = [
        ("psd-tools", "psd_tools"),
        ("cairosvg", "cairosvg"),
        ("imageio", "imageio"),
        ("psutil", "psutil"),
        ("requests", "requests"),
    ]
    
    for name, import_name in optional_deps:
        ok, status = check_dependency(name, import_name, optional=True)
        print(f"  {name}: {status}")
    
    # Системні модулі (стандартна бібліотека)
    print("\n🐍 СТАНДАРТНА БІБЛІОТЕКА PYTHON:")
    stdlib_modules = [
        "tkinter",
        "xml.etree.ElementTree",
        "json",
        "os",
        "sys",
        "pathlib",
        "threading",
        "subprocess",
    ]
    
    for module_name in stdlib_modules:
        ok, status = check_dependency(module_name, module_name)
        print(f"  {module_name}: {status}")
    
    # Підсумок
    print("\n" + "=" * 50)
    if all_required_ok:
        print("🎉 ВСІ ОБОВ'ЯЗКОВІ ЗАЛЕЖНОСТІ ВСТАНОВЛЕНІ!")
        print("✅ RimWorld Mod Builder готовий до запуску")
    else:
        print("⚠️ ДЕЯКІ ОБОВ'ЯЗКОВІ ЗАЛЕЖНОСТІ ВІДСУТНІ!")
        print("❌ Встановіть відсутні залежності перед запуском")
        print("\n💡 Команда для встановлення:")
        print("pip install -r requirements.txt")
    
    print("\n📚 Додаткова інформація:")
    print("  - Опціональні залежності покращують функціональність")
    print("  - psd-tools потрібен для підтримки PSD файлів")
    print("  - lxml покращує XML валідацію")
    print("  - Всі інші залежності додають додаткові можливості")

if __name__ == "__main__":
    main()
