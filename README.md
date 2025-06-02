# 🚀 RimWorld Mod Builder v1.0.1 Alpha

**Created with AI**

**Інструмент для створення модів RimWorld**

> ⚠️ **ALPHA ВЕРСІЯ** - Це тестова версія програми (Build 1.0.1 R26225). Функціональність може змінюватися, можливі обмеження та помилки. Використовуйте на власний ризик.

[![Версія](https://img.shields.io/badge/версія-1.0.1%20Alpha-orange.svg)](https://github.com/Johny97Moon/RWModBuilder)
[![Платформа](https://img.shields.io/badge/платформа-Windows%2010%2F11-green.svg)](https://github.com/Johny97Moon/RWModBuilder)
[![Розмір](https://img.shields.io/badge/розмір-17.7%20MB-brightgreen.svg)](https://github.com/Johny97Moon/RWModBuilder/releases)
[![Ліцензія](https://img.shields.io/badge/ліцензія-MIT-blue.svg)](LICENSE)

- **💻 Не потребує Python** - Автономний .exe файл
- **📏 Компактний розмір** - Всього 17.7 MB
- **🚀 Швидкий запуск** - Готовий за 10 секунд
- **🇺🇦 Українська мова** - Повна локалізація

## ✨ Особливості

> 🧪 **Alpha функціональність** - Деякі функції можуть працювати нестабільно або бути неповними

- 🎨 **Сучасний GUI** з темними/світлими темами
- 🖼️ **Розширений менеджер текстур** (16+ форматів)
- 📝 **Інтегрований редактор** з підсвічуванням синтаксису
- 🔧 **XML валідація** та шаблони
- 💻 **C# підтримка** з Harmony патчингом (Alpha)
- 🚀 **Steam Workshop** інтеграція (Alpha)
> ⚠️ **Увага:** Alpha версія може містити помилки. Рекомендується створювати резервні копії ваших модів.

### 🛠️ Для розробників

```bash
# Клонування
git clone https://github.com/Johny97Moon/RWModBuilder.git
cd RWModBuilder

# Встановлення залежностей
pip install -r requirements.txt

# Запуск з вихідного коду
python main.py

# Збірка власного .exe (якщо доступно)
pyinstaller --onefile --windowed main.py
```

## 📖 Повна документація

### 📚 Основна документація
- **👉 [Головний посібник](ReadMD/RIMWORLD_MOD_BUILDER_GUIDE.md)** - Повне керівництво користувача
- **🔨 [Компілятор DLL](ReadMD/DLL_COMPILER_GUIDE.md)** - Керівництво по компіляції C# модів
- **📊 [Звіт про готовність](ReadMD/PRODUCTION_READINESS_REPORT.md)** - Технічна документація

### 🎯 Що містить документація:
- Детальні інструкції встановлення та налаштування
- Керівництво користувача з прикладами
- Опис всіх функцій та можливостей
- Інструкції по створенню C# модів
- Усунення проблем та FAQ

## 🎯 Основні компоненти

### 🖼️ Менеджер текстур CustomTkinter
- Підтримка PSD, SVG, PNG, JPEG, TIFF, WebP та інших
- Автоматична конвертація в PNG для RimWorld
- Попередній перегляд з масштабуванням
- Батч-операції та оптимізація

### 📝 Текстовий редактор
- Підсвічування синтаксису XML/C#
- Автодоповнення RimWorld тегів
- Валідація в реальному часі
- Множинні вкладки

### 🔧 XML Шаблони
- ThingDef, BuildingDef, WeaponDef
- ApparelDef, RecipeDef, ResearchProjectDef
- FactionDef, PawnKindDef, BiomeDef

## 🛠️ Технології

- **GUI**: CustomTkinter 5.2+
- **Обробка зображень**: Pillow, psd-tools
- **XML**: lxml, ElementTree
- **Python**: 3.8+ (рекомендується 3.11+)

## 📋 Системні вимоги

### 💻 Для .exe файлу (користувачі)
- **Windows 10/11 x64** - Основна платформа
- **4GB RAM** (рекомендується 8GB)
- **500MB вільного місця** на диску
- **Visual C++ Redistributable** (зазвичай вже встановлений)

### 🛠️ Для розробки (розробники)
- **Python 3.8+** (рекомендується 3.11+)
- **Windows 10+** / macOS 10.14+ / Linux Ubuntu 18.04+
- **8GB RAM** для збірки .exe
- **2GB вільного місця** для середовища розробки

### 🔧 Опціонально для C# функцій
- **Visual Studio Community 2022** (безкоштовно)
- **.NET Framework 4.7.2+** для компіляції C# модів

## 🤝 Внесок у проєкт

> 🧪 **Alpha версія** - Ми особливо вітаємо звіти про помилки та пропозиції покращень!

1. Fork репозиторій з [GitHub](https://github.com/Johny97Moon/RWModBuilder)
2. Створіть feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit зміни (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Створіть [Pull Request](https://github.com/Johny97Moon/RWModBuilder/pulls)

### 🐛 Звіти про помилки
Будь ласка, створюйте [Issues](https://github.com/Johny97Moon/RWModBuilder/issues) для звітів про помилки з детальним описом проблеми.

## 📄 Ліцензія

Розповсюджується під ліцензією MIT. Дивіться `LICENSE` для деталей.

## 🎉 Подяки

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Tom Schimansky
- [Pillow](https://python-pillow.org/) - Python Imaging Library
- RimWorld Community - за підтримку та зворотний зв'язок

---

**📚 Для детальної інформації дивіться документацію в папці [ReadMD/](ReadMD/)**

## ⚠️ Важлива інформація про Alpha версію

**RimWorld Mod Builder v1.0.1 Alpha (Build 1.0.1 R26225)** - це тестова версія програми.

### 🧪 Що означає Alpha:
- **Функціональність може змінюватися** без попередження
- **Можливі помилки та нестабільна робота** деяких функцій
- **Регулярні оновлення** з виправленнями та покращеннями
- **Зворотний зв'язок користувачів** дуже важливий для розвитку

### 📞 Підтримка:
- **GitHub Issues:** [Звіти про помилки](https://github.com/Johny97Moon/RWModBuilder/issues)
- **GitHub Discussions:** [Обговорення та пропозиції](https://github.com/Johny97Moon/RWModBuilder/discussions)

---

*RimWorld Mod Builder v1.0.1 Alpha - Створюйте моди з легкістю!* 🚀
