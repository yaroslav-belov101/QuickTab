<div align="center">

# QuickTab v0.5.0

</div>




# QuickTab - Универсальный голосовой информационный хаб

QuickTab - мощный инструмент для мгновенного получения важной информации через терминал, голосовые команды и графическую оболочку. Создан для тех, кто хочет получать данные без лишних кликов и переключения вкладок.

## Зачем нужен QuickTab?

Каждый день мы тратим время на:
- Проверку погоды в браузере
- Поиск курсов валют, расписания, новостей
- Переключение между множеством вкладок

QuickTab решает это **одной командой**, голосом или кликом.

## ✅ Реализованные функции

```
✓  Мультигород + конфигурация
✓  Голосовое управление  
✓  Красивый GUI интерфейс (CustomTkinter)
✓  Виджеты: погода, валюты, новости
✓  Вывод информации в приложении (без браузера)
✓  Изменяемый размер окна
✓  Дашборд с меню и настройками
✓  Окно поиска с фильтрами
```

## 🎤 Голосовое управление (в разработке)

```
"QuickTab, какая погода?"
"Погода на завтра"
"Курс доллара"
"Пробки в Краснодаре"
```

## 🖥️ Графическая оболочка

- Современный GUI на CustomTkinter с темной темой
- Красивый дизайн с цветными рамками и градиентами
- Простой интерфейс с чекбоксами для выбора информации
- Выбор тем новостей через выпадающее меню
- Отображение результатов прямо в приложении
- Изменяемый размер окна
- Правый дашборд с меню навигации
- Окно поиска с фильтрами и предложениями функций
- Нет необходимости в браузере - данные загружаются мгновенно

## Быстрый старт (кроссплатформенный)

```bash
# ШАГ 1: Скачай проект
git clone https://github.com/yaroslav-belov101/QuickTab.git
cd QuickTab

# ШАГ 2: Установи Python пакеты (1 команда)
pip install -r requirements.txt

# ШАГ 3: Браузерные драйверы (выбери свою ОС)
```

#### Windows (самый простой способ):
```cmd
pip install webdriver-manager
```
**Всё! Драйверы скачаются автоматически.**

#### Linux (Arch/Ubuntu/Fedora):
```bash
# Arch/Manjaro
sudo pacman -S geckodriver chromium

# Ubuntu/Debian  
sudo apt install firefox-geckodriver chromium-browser

# Fedora
sudo dnf install geckodriver chromium
```

#### Mac:
```bash
brew install geckodriver chromedriver
```

### Полная автоматизация (копипаст)
```bash
# Скопируй ВСЕ эти команды подряд:
pip install selenium beautifulsoup4 webdriver-manager
git clone https://github.com/yaroslav-belov101/QuickTab.git
cd QuickTab
python main.py
```

## ▶️ Запуск

```bash
cd QuickTab
python main.py
```

**Увидишь:**
```
🌡️ Температура:  +2°
☁️  Условия:      Облачно  
💨 Ветер:        4,1 м/с
💧 Влажность:    99%
🛑 Ctrl+C для выхода
```

## 🎉 Что происходит?

1. **🦊 Firefox** открывает твой обычный профиль с куками
2. Загружает Яндекс.Погода Белореченск 
3. **Парсит** температуру/ветер/влажность
4. **Обновляет** каждые 60 секунд
5. **Ctrl+C** → мгновенно закрывается

## ❓ Типичные проблемы и решения

| Проблема | Решение |
|----------|---------|
| `pip не найдена` | `python -m pip install -r requirements.txt` |
| `geckodriver не найден` | `pip install webdriver-manager` |
| `Firefox не запускается` | **Не проблема!** Автоматически Chromium |
| `Permission denied` | `sudo` только для драйверов |

## 💾 Резервная копия (на всякий случай)

**Если что-то сломалось:**
```bash
pip install selenium beautifulsoup4 webdriver-manager
python -c "
from selenium import webdriver
driver = webdriver.Chrome()
driver.get('https://yandex.ru/pogoda/ru/belorechensk')
print('✅ Selenium работает!')
driver.quit()
"
```

## Проверка установки

```bash
# Проверь драйверы
geckodriver --version
chromedriver --version
# или
python -c "from selenium import webdriver; print('OK!')"
```

***

## Технические особенности

- ✅ Graceful shutdown с signal_handler
- ✅ Защита от invalid session id
- ✅ Автокилл Firefox/geckodriver процессов  
- ✅ Regex парсинг (устойчив к редизайну сайтов)
- ✅ Автоопределение default-release профиля Firefox
- ✅ requirements.txt (готовый)

## Системные требования

```
✦ Arch Linux / Ubuntu / Debian / Windows
✦ Firefox (default-release профиль)
✦ Chromium/Chromium-based браузеры
✦ Python 3.8+
✦ 256MB RAM
✦ requirements.txt (в комплекте)
```

## Архитектура проекта

```
QuickTab/
├── main.py          # Терминал версия (погода)
├── gui.py           # Графическая оболочка (TODO)
├── voice.py         # Голосовое управление (TODO)  
├── config.py        # Конфигурация
├── requirements.txt # Зависимости
├── .env            # Переменные окружения
└── README.md       # Документация
```

## Почему QuickTab?

- **Firefox default** = ваши cookies, расширения, настройки
- **Regex парсинг** = работает при любых изменениях сайта
- **Fallback Chromium** = 100% стабильность
- **Модульность** = легко добавлять новые виджеты
- **Три интерфейса** = терминал + голос + GUI

## Roadmap

```
✅  Терминал + Погода 
🔄  Конфигурация городов
🎤  Голосовое управление  
🖥️  Графическая оболочка
⭐  Полный функционал (валюта, пробки, кино)
```

## Лицензия и автор

**Автор:** Yaroslav Belov (Belorechensk, Краснодарский край, RU)  
**Лицензия:** MIT  
**Год:** 2026

***

QuickTab - это не просто парсер погоды. Это **платформа для персонального информационного хаба** с голосом, графикой и терминалом в одном проекте! 🚀
